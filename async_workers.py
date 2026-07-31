import os
import sys
import subprocess
from PySide6.QtCore import QThread, Signal

class AIConversionWorker(QThread):
    """Async worker thread for AI model LaTeX conversion."""
    success_signal = Signal(str)
    error_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, ai_models, model_name: str, image_path: str):
        super().__init__()
        self.ai_models = ai_models
        self.model_name = model_name
        self.image_path = image_path

    def run(self):
        try:
            if self.model_name == "Gemini":
                latex_code = self.ai_models.use_gemini(self.image_path)
            else:
                latex_code = self.ai_models.use_mistral(self.image_path)
            self.success_signal.emit(latex_code)
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            self.finished_signal.emit()


class SVGGenerationWorker(QThread):
    """Async worker thread for local MathJax SVG rendering via Node.js."""
    success_signal = Signal(str)
    error_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, latex_code: str, hex_color: str, output_directory: str, image_path: str):
        super().__init__()
        self.latex_code = latex_code
        self.hex_color = hex_color
        self.output_directory = output_directory
        self.image_path = image_path

    def run(self):
        try:
            base_name = os.path.splitext(os.path.basename(self.image_path))[0]
            folder_name = os.path.join(self.output_directory, f"{base_name}_latex")
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)

            cleaned_latex = self.latex_code.strip()
            if cleaned_latex.startswith('{') and cleaned_latex.endswith('}'):
                cleaned_latex = cleaned_latex[1:-1].strip()

            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "render_mathjax.js")
            if not os.path.exists(script_path):
                self.error_signal.emit("render_mathjax.js script not found in application directory.")
                return

            cmd = ["node", script_path, "--latex", cleaned_latex, "--color", self.hex_color, "--display", "true"]

            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                creationflags=creationflags
            )

            if process.returncode != 0:
                error_msg = process.stderr.strip() if process.stderr else "Node.js MathJax rendering failed."
                if "node" in error_msg.lower() and ("not recognized" in error_msg.lower() or "not found" in error_msg.lower()):
                    self.error_signal.emit("Node.js is not installed or not found in system PATH. Please install Node.js.")
                else:
                    self.error_signal.emit(f"MathJax rendering failed: {error_msg}")
                return

            svg_content = process.stdout.strip()
            if not svg_content or "<svg" not in svg_content:
                self.error_signal.emit("MathJax returned invalid or empty SVG data.")
                return

            svg_file_path = os.path.join(folder_name, "equation.svg")
            with open(svg_file_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)

            self.success_signal.emit(folder_name)

        except FileNotFoundError:
            self.error_signal.emit("Node.js executable ('node') was not found on your system. Please install Node.js from https://nodejs.org/")
        except Exception as e:
            self.error_signal.emit(f"Failed to generate SVG: {str(e)}")
        finally:
            self.finished_signal.emit()
