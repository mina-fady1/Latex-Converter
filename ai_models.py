import google.generativeai as genai
from openai import OpenAI
import base64
import os

class AIModels:
    def __init__(self):
        self.models = {
            "Gemini": {
                "name": "gemini-3.6-flash",
                "api_key": ""
            },
            "Mistral": {
                "name": "mistralai/mistral-small-3.1-24b-instruct:free",
                "api_key": ""
            }
        }
        self.load_api_keys()

    def save_api_keys(self):
        """Save API keys to a file"""
        try:
            with open('api_keys.txt', 'w') as f:
                for model, data in self.models.items():
                    f.write(f"{model}={data['api_key']}\n")
        except Exception as e:
            print(f"Error saving API keys: {e}")

    def load_api_keys(self):
        """Load API keys from file"""
        try:
            if not os.path.exists('api_keys.txt'):
                return
            with open('api_keys.txt', 'r') as f:
                for line in f:
                    if '=' in line:
                        model, key = line.strip().split('=')
                        if model in self.models:
                            self.models[model]['api_key'] = key
        except Exception as e:
            print(f"Error loading API keys: {e}")

    def update_api_key(self, model, key):
        """Update API key for a specific model"""
        if model in self.models:
            self.models[model]['api_key'] = key
            self.save_api_keys()

    def use_gemini(self, image_path):
        if not self.models["Gemini"]["api_key"]:
            raise Exception("Please set Gemini API key first")

        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

        genai.configure(api_key=self.models["Gemini"]["api_key"])
        model = genai.GenerativeModel(model_name=self.models["Gemini"]["name"])
        
        prompt = (
            "Extract the text and math from this image into a single, valid Standard, clean AMS-LaTeX snippet compatible with MathJax.\n"
            "STRICT RULES:\n"
            "1. DO NOT use document wrappers or structural commands (NO \\documentclass, NO \\begin{document}, NO \\section, NO \\subsection, NO \\begin{itemize}).\n"
            "2. Wrap all multi-line structures, titles, and text lists inside a single \\begin{aligned} ... \\end{aligned} block or standard AMS environments.\n"
            "3. Convert standard text, headings, bullet points, and words into plain text wrapped inside \\text{...}.\n"
            "4. Return ONLY raw LaTeX code. NO markdown formatting, NO code blocks (do not wrap in ``` or ```latex), and NO explanations or extra text."
        )
        
        response = model.generate_content(
            contents=[
                prompt, 
                {
                    "mime_type": "image/png",
                    "data": base64.b64decode(encoded_string)
                }
            ]
        )
        
        # Strip away markdown block delimiters if present
        latex_code = response.text.strip()
        if latex_code.startswith("```"):
            latex_code = "\n".join(latex_code.splitlines()[1:-1]).strip()
        latex_code = latex_code.replace("```latex", "").replace("```", "").strip()
        
        return latex_code

    def use_mistral(self, image_path):
        if not self.models["Mistral"]["api_key"]:
            raise Exception("Please set Mistral API key first")

        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.models["Mistral"]["api_key"],
        )
        
        prompt = (
            "Extract the text and math from this image into Standard, clean AMS-LaTeX compatible with MathJax.\n"
            "STRICT RULES:\n"
            "1. DO NOT use document tags (NO \\documentclass, NO \\begin{document}, NO \\begin{itemize}, NO \\section).\n"
            "2. Wrap multi-line layouts in \\begin{aligned} ... \\end{aligned} or standard AMS environments, and wrap plain text inside \\text{...}.\n"
            "3. Output ONLY pure LaTeX code. NO markdown, NO ``` block wrappers, NO commentary."
        )
        
        completion = client.chat.completions.create(
            extra_body={},
            model=self.models["Mistral"]["name"],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{encoded_string}"
                            }
                        }
                    ]
                }
            ]
        )
        
        # Clean up the response
        latex_code = completion.choices[0].message.content or ""
        latex_code = latex_code.strip()
        if latex_code.startswith("```"):
            latex_code = "\n".join(latex_code.splitlines()[1:-1]).strip()
        latex_code = latex_code.replace("```latex", "").replace("```", "").strip()
        
        return latex_code