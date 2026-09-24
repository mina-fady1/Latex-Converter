"""AI-provider integrations and image preparation for LaTeX extraction."""

from __future__ import annotations

import base64
import io
import logging
import os
import random
import shutil
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter, sleep
from typing import Callable

from dotenv import load_dotenv, set_key
from google import genai
from google.genai import types as genai_types
from openai import OpenAI
from PIL import Image, ImageOps, UnidentifiedImageError


LOGGER = logging.getLogger(__name__)

ENV_PATH = Path(__file__).resolve().parent / ".env"
ENV_EXAMPLE_PATH = Path(__file__).resolve().parent / ".env.example"

MODEL_ENV_VARS: dict[str, tuple[str, ...]] = {
    "Gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI", "Gemini"),
    "Mistral": ("MISTRAL_API_KEY", "OPENROUTER_API_KEY", "MISTRAL", "Mistral"),
}

PRIMARY_ENV_KEYS: dict[str, str] = {
    "Gemini": "GEMINI_API_KEY",
    "Mistral": "MISTRAL_API_KEY",
}

# Gemini requests are deliberately bounded. The previous SDK silently retried for
# up to ten minutes, which made a short provider outage look like a stuck conversion.
GEMINI_TIMEOUT_SECONDS = 60

# Ordered by preference. When a model answers 503 "high demand" on every attempt,
# the next one in the chain is tried. All are listed as Stable at
# https://ai.google.dev/gemini-api/docs/models
GEMINI_MODEL_CHAIN: tuple[str, ...] = (
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
)
GEMINI_ATTEMPTS_PER_MODEL = 3
# Exponential backoff between tries on the same model: ~2s, ~4s (with jitter).
# A 503 is a capacity spike, so retrying within milliseconds just hits the same wall.
GEMINI_BACKOFF_BASE_SECONDS = 2.0
GEMINI_BACKOFF_MAX_SECONDS = 15.0
MAX_OUTPUT_TOKENS = 2048

# Equation images rarely need more than this resolution. Converting all input to
# JPEG gives the API an accurate, consistent MIME type and keeps camera screenshots
# from dominating the request time.
MAX_IMAGE_DIMENSION = 2048
MAX_IMAGE_BYTES = 2 * 1024 * 1024
MIN_JPEG_QUALITY = 70
INITIAL_JPEG_QUALITY = 92

ProgressCallback = Callable[[str], None]


@dataclass(frozen=True)
class PreparedImage:
    """A normalized image ready for an inline multimodal API request."""

    data: bytes
    mime_type: str
    source_size: tuple[int, int]
    prepared_size: tuple[int, int]
    source_bytes: int
    prepared_bytes: int


class AIModels:
    def __init__(self):
        self.models = {
            "Gemini": {
                "name": GEMINI_MODEL_CHAIN[0],
                "api_key": ""
            },
            "Mistral": {
                "name": "mistralai/mistral-small-3.1-24b-instruct:free",
                "api_key": ""
            }
        }
        self._gemini_client: genai.Client | None = None
        self._gemini_client_key: str | None = None
        self._mistral_client: OpenAI | None = None
        self._mistral_client_key: str | None = None
        self.load_api_keys()

    def save_api_keys(self):
        """Save API keys to the .env file."""
        try:
            if not ENV_PATH.exists():
                if ENV_EXAMPLE_PATH.exists():
                    shutil.copy(ENV_EXAMPLE_PATH, ENV_PATH)
                else:
                    ENV_PATH.touch()

            for model, data in self.models.items():
                env_key = PRIMARY_ENV_KEYS.get(model)
                if env_key:
                    val = data.get("api_key", "").strip()
                    set_key(str(ENV_PATH), env_key, val, quote_mode="never")
                    os.environ[env_key] = val
        except Exception as error:
            LOGGER.warning("Could not save API keys to .env: %s", error)

    def load_api_keys(self):
        """Load API keys from .env file or environment variables."""
        try:
            if ENV_PATH.exists():
                load_dotenv(dotenv_path=ENV_PATH, override=True)
            else:
                load_dotenv(override=True)

            for model, env_vars in MODEL_ENV_VARS.items():
                for var_name in env_vars:
                    val = os.getenv(var_name, "").strip()
                    if val:
                        self.models[model]["api_key"] = val
                        break

            # Backward compatibility: if not in .env, migrate non-empty key from legacy api_keys.txt
            legacy_file = Path(__file__).resolve().parent / "api_keys.txt"
            if legacy_file.exists():
                migrated = False
                try:
                    with open(legacy_file, "r", encoding="utf-8") as file:
                        for line in file:
                            if "=" not in line:
                                continue
                            m_name, k_val = line.strip().split("=", 1)
                            m_name = m_name.strip()
                            k_val = k_val.strip()
                            if m_name in self.models and k_val and not self.models[m_name]["api_key"]:
                                self.models[m_name]["api_key"] = k_val
                                migrated = True
                    if migrated:
                        self.save_api_keys()
                except Exception as leg_err:
                    LOGGER.debug("Could not read legacy api_keys.txt: %s", leg_err)
        except Exception as error:
            LOGGER.warning("Could not load API keys from .env: %s", error)

    def update_api_key(self, model: str, key: str):
        """Update a model key and discard any client created with the old key."""
        if model not in self.models:
            return

        cleaned_key = key.strip()
        self.models[model]["api_key"] = cleaned_key
        env_key = PRIMARY_ENV_KEYS.get(model)
        if env_key:
            os.environ[env_key] = cleaned_key

        if model == "Gemini":
            self._close_gemini_client()
        else:
            self._close_mistral_client()
        self.save_api_keys()

    def close(self):
        """Close persistent HTTP clients when the application exits."""
        self._close_gemini_client()
        self._close_mistral_client()

    def _close_gemini_client(self):
        if self._gemini_client is not None:
            try:
                self._gemini_client.close()
            except Exception as error:
                LOGGER.debug("Could not close Gemini client: %s", error)
        self._gemini_client = None
        self._gemini_client_key = None

    def _close_mistral_client(self):
        if self._mistral_client is not None:
            try:
                self._mistral_client.close()
            except Exception as error:
                LOGGER.debug("Could not close Mistral client: %s", error)
        self._mistral_client = None
        self._mistral_client_key = None

    def _get_gemini_client(self) -> genai.Client:
        """Return one reusable, bounded-timeout client for the current API key."""
        api_key = self.models["Gemini"]["api_key"]
        if not api_key:
            raise RuntimeError("Please set Gemini API key first")

        if self._gemini_client is None or self._gemini_client_key != api_key:
            self._close_gemini_client()
            self._gemini_client = genai.Client(
                api_key=api_key,
                http_options=genai_types.HttpOptions(
                    api_version="v1",
                    timeout=GEMINI_TIMEOUT_SECONDS * 1000,
                    # Retries are performed below so the UI can report them.
                    retry_options=genai_types.HttpRetryOptions(attempts=1),
                ),
            )
            self._gemini_client_key = api_key

        return self._gemini_client

    def _get_mistral_client(self) -> OpenAI:
        api_key = self.models["Mistral"]["api_key"]
        if not api_key:
            raise RuntimeError("Please set Mistral API key first")

        if self._mistral_client is None or self._mistral_client_key != api_key:
            self._close_mistral_client()
            self._mistral_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                timeout=GEMINI_TIMEOUT_SECONDS,
                max_retries=1,
            )
            self._mistral_client_key = api_key

        return self._mistral_client

    @staticmethod
    def _emit_progress(callback: ProgressCallback | None, message: str):
        if callback is not None:
            callback(message)

    @staticmethod
    def _clean_latex(text: str) -> str:
        latex_code = text.strip()
        fence = chr(96) * 3
        if latex_code.startswith(fence):
            latex_code = "\n".join(latex_code.splitlines()[1:-1]).strip()
        return latex_code.replace(f"{fence}latex", "").replace(fence, "").strip()

    @staticmethod
    def _is_retryable_gemini_error(error: Exception) -> bool:
        """Retry only transient HTTP and transport failures once."""
        status_code = getattr(error, "code", None)
        if status_code in {408, 429, 500, 502, 503, 504}:
            return True

        module_name = error.__class__.__module__
        return module_name.startswith("httpx") or module_name.startswith("httpcore")

    @staticmethod
    def _backoff_delay(attempt: int) -> float:
        """Exponential backoff with jitter so retries don't all land together."""
        delay = min(
            GEMINI_BACKOFF_MAX_SECONDS,
            GEMINI_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)),
        )
        return delay * random.uniform(0.75, 1.25)

    @staticmethod
    def _friendly_gemini_error(error: Exception | None) -> str:
        """Turn Google's raw JSON-ish error text into one readable sentence."""
        code = getattr(error, "code", None)
        if code == 503:
            return "Google reports the model is under high demand (HTTP 503)."
        if code == 429:
            return "Rate limit or quota reached (HTTP 429)."
        if code in {500, 502, 504, 408}:
            return f"Google's servers had a temporary problem (HTTP {code})."
        return str(error) if error is not None else "Unknown error."

    @staticmethod
    def _resize_to_limit(image: Image.Image) -> Image.Image:
        if max(image.size) <= MAX_IMAGE_DIMENSION:
            return image

        resized = image.copy()
        resized.thumbnail(
            (MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION),
            Image.Resampling.LANCZOS,
        )
        return resized

    @staticmethod
    def _encode_jpeg_with_size_limit(image: Image.Image) -> tuple[bytes, tuple[int, int]]:
        """Return a legible JPEG under the request-size cap where practical."""
        working_image = image
        quality = INITIAL_JPEG_QUALITY

        for _ in range(12):
            buffer = io.BytesIO()
            working_image.save(
                buffer,
                format="JPEG",
                quality=quality,
                optimize=True,
                subsampling=0,
            )
            data = buffer.getvalue()
            if len(data) <= MAX_IMAGE_BYTES:
                return data, working_image.size

            if quality > MIN_JPEG_QUALITY:
                quality = max(MIN_JPEG_QUALITY, quality - 6)
                continue

            # Quality reductions alone did not meet the cap. Scale only enough
            # to approach it, while retaining at least a 256px longest edge.
            scale = max(0.5, min(0.9, (MAX_IMAGE_BYTES / len(data)) ** 0.5 * 0.95))
            longest_side = max(working_image.size)
            if longest_side <= 256:
                return data, working_image.size
            new_size = (
                max(1, int(working_image.width * scale)),
                max(1, int(working_image.height * scale)),
            )
            working_image = working_image.resize(new_size, Image.Resampling.LANCZOS)
            quality = INITIAL_JPEG_QUALITY

        return data, working_image.size

    def _prepare_image(self, image_path: str) -> PreparedImage:
        """Normalize orientation, resolution, format, and size before upload."""
        path = Path(image_path)
        source_bytes = path.stat().st_size

        try:
            with Image.open(path) as source_image:
                source_image.load()
                transposed_image = ImageOps.exif_transpose(source_image)
                if (
                    transposed_image.mode in {"RGBA", "LA"}
                    or "transparency" in transposed_image.info
                ):
                    # JPEG has no alpha channel. Composite onto white so
                    # transparent equation screenshots remain readable.
                    background = Image.new("RGBA", transposed_image.size, "white")
                    background.alpha_composite(transposed_image.convert("RGBA"))
                    normalized_image = background.convert("RGB")
                else:
                    normalized_image = transposed_image.convert("RGB")
        except (FileNotFoundError, UnidentifiedImageError, OSError) as error:
            raise RuntimeError(f"Could not read input image: {error}") from error

        source_size = normalized_image.size
        normalized_image = self._resize_to_limit(normalized_image)
        image_data, prepared_size = self._encode_jpeg_with_size_limit(normalized_image)

        return PreparedImage(
            data=image_data,
            mime_type="image/jpeg",
            source_size=source_size,
            prepared_size=prepared_size,
            source_bytes=source_bytes,
            prepared_bytes=len(image_data),
        )

    @staticmethod
    def _image_summary(image: PreparedImage) -> str:
        return (
            f"{image.source_size[0]}×{image.source_size[1]} "
            f"({image.source_bytes / 1024:.0f} KB) → "
            f"{image.prepared_size[0]}×{image.prepared_size[1]} "
            f"({image.prepared_bytes / 1024:.0f} KB)"
        )

    @staticmethod
    def _gemini_prompt() -> str:
        return (
            "Transcribe only the visible text and mathematics in this image as one clean, "
            "valid AMS-LaTeX snippet compatible with MathJax. Preserve mathematical structure "
            "and line breaks, but do not invent missing content.\n"
            "STRICT RULES:\n"
            "1. Do not use document wrappers or structural commands such as \\documentclass, "
            "\\begin{document}, \\section, or \\begin{itemize}.\n"
            "2. Use \\begin{aligned} ... \\end{aligned} for genuinely multi-line mathematical layouts.\n"
            "3. Wrap ordinary visible prose in \\text{...}.\n"
            "4. Return raw LaTeX only: no Markdown, code fences, explanations, or commentary."
        )

    def use_gemini(
        self,
        image_path: str,
        progress_callback: ProgressCallback | None = None,
    ) -> tuple[str, dict[str, float | int | str]]:
        """Convert an image with Gemini and return LaTeX plus phase timings."""
        total_started = perf_counter()
        self._emit_progress(progress_callback, "Preparing image for Gemini…")
        prepare_started = perf_counter()
        image = self._prepare_image(image_path)
        prepare_seconds = perf_counter() - prepare_started
        self._emit_progress(
            progress_callback,
            f"Prepared image in {prepare_seconds:.1f}s ({self._image_summary(image)}).",
        )

        client = self._get_gemini_client()
        response = None
        used_model = ""
        total_attempts = 0
        last_error: Exception | None = None
        api_started = perf_counter()

        for model_name in GEMINI_MODEL_CHAIN:
            for attempt in range(1, GEMINI_ATTEMPTS_PER_MODEL + 1):
                total_attempts += 1
                self._emit_progress(
                    progress_callback,
                    f"Sending image to {model_name} "
                    f"(attempt {attempt}/{GEMINI_ATTEMPTS_PER_MODEL})…",
                )
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[
                            self._gemini_prompt(),
                            genai_types.Part.from_bytes(
                                data=image.data,
                                mime_type=image.mime_type,
                            ),
                        ],
                        config=genai_types.GenerateContentConfig(
                            candidate_count=1,
                            max_output_tokens=MAX_OUTPUT_TOKENS,
                            response_mime_type="text/plain",
                            # This request has no tools. Disable the SDK's default
                            # AFC loop and its direct-generate warning.
                            automatic_function_calling=genai_types.AutomaticFunctionCallingConfig(
                                disable=True,
                            ),
                            # Low thinking balances speed with difficult equation reading.
                            thinking_config=genai_types.ThinkingConfig(
                                thinking_level=genai_types.ThinkingLevel.LOW,
                            ),
                        ),
                    )
                    used_model = model_name
                    break
                except Exception as error:
                    last_error = error
                    LOGGER.warning(
                        "Gemini %s attempt %d/%d failed: %s",
                        model_name, attempt, GEMINI_ATTEMPTS_PER_MODEL, error,
                    )

                    # Auth errors, bad requests, blocked content, etc. will not be
                    # fixed by waiting or by switching models, so fail immediately.
                    if not self._is_retryable_gemini_error(error):
                        elapsed = perf_counter() - api_started
                        raise RuntimeError(
                            f"Gemini request failed on {model_name} after {elapsed:.1f}s: {error}"
                        ) from error

                    if attempt < GEMINI_ATTEMPTS_PER_MODEL:
                        delay = self._backoff_delay(attempt)
                        self._emit_progress(
                            progress_callback,
                            f"{model_name} is busy; retrying in {delay:.0f}s…",
                        )
                        sleep(delay)
                    else:
                        self._emit_progress(
                            progress_callback,
                            f"{model_name} is still busy; switching to the next model…",
                        )

            if response is not None:
                break

        if response is None:
            elapsed = perf_counter() - api_started
            raise RuntimeError(
                f"All Gemini models are busy after {total_attempts} attempts and {elapsed:.1f}s. "
                f"{self._friendly_gemini_error(last_error)} "
                "This is usually temporary on Google's side. Please try again in a minute or two, "
                "or switch to Mistral."
            ) from last_error

        attempt = total_attempts
        api_seconds = perf_counter() - api_started
        self._emit_progress(progress_callback, f"Gemini responded in {api_seconds:.1f}s; validating LaTeX…")
        parse_started = perf_counter()
        latex_code = self._clean_latex(response.text or "")
        parse_seconds = perf_counter() - parse_started
        if not latex_code:
            raise RuntimeError("Gemini returned an empty response. Please try a clearer image.")

        timings: dict[str, float | int | str] = {
            "provider": f"Gemini ({used_model})",
            "prepare_seconds": prepare_seconds,
            "api_seconds": api_seconds,
            "parse_seconds": parse_seconds,
            "total_seconds": perf_counter() - total_started,
            "attempts": attempt,
            "image_summary": self._image_summary(image),
        }
        LOGGER.info("Gemini conversion completed: %s", timings)
        return latex_code, timings

    def use_mistral(
        self,
        image_path: str,
        progress_callback: ProgressCallback | None = None,
    ) -> tuple[str, dict[str, float | int | str]]:
        """Convert an image with Mistral using the same normalized upload path."""
        total_started = perf_counter()
        self._emit_progress(progress_callback, "Preparing image for Mistral…")
        prepare_started = perf_counter()
        image = self._prepare_image(image_path)
        prepare_seconds = perf_counter() - prepare_started
        encoded_image = base64.b64encode(image.data).decode("ascii")

        self._emit_progress(progress_callback, "Sending image to Mistral (60s limit)…")
        api_started = perf_counter()
        completion = self._get_mistral_client().chat.completions.create(
            model=self.models["Mistral"]["name"],
            max_tokens=MAX_OUTPUT_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self._gemini_prompt()},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image.mime_type};base64,{encoded_image}"
                            },
                        },
                    ],
                }
            ],
        )
        api_seconds = perf_counter() - api_started
        parse_started = perf_counter()
        latex_code = self._clean_latex(completion.choices[0].message.content or "")
        parse_seconds = perf_counter() - parse_started
        if not latex_code:
            raise RuntimeError("Mistral returned an empty response. Please try a clearer image.")

        timings: dict[str, float | int | str] = {
            "provider": "Mistral",
            "prepare_seconds": prepare_seconds,
            "api_seconds": api_seconds,
            "parse_seconds": parse_seconds,
            "total_seconds": perf_counter() - total_started,
            "attempts": 1,
            "image_summary": self._image_summary(image),
        }
        LOGGER.info("Mistral conversion completed: %s", timings)
        return latex_code, timings