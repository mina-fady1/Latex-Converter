# LaTeX Equation Converter

A powerful desktop application that converts mathematical equation images to LaTeX code and generates SVG output using AI models.

## Features

- Convert images of mathematical equations to LaTeX code using AI
- Support for multiple AI models (Gemini, Mistral)
- Generate SVG output with customizable text colors
- User-friendly interface with dark mode support
- Customizable output directory
- Image preview functionality
- Secure API key management



## Requirements

- Python 3.8+
- Tkinter (included with Python)
- Required Python packages (installed via requirements.txt):
  - Pillow (PIL) - For image processing and previews
  - requests - For SVG generation
  - google-generativeai - For Gemini Vision API
  - openai - For OpenRouter/Mistral API integration

## Installation

1. Clone the repository:
```bash
git clone https://github.com/elewashy/latex-equation-converter.git
cd latex-equation-converter
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up API keys:
- Obtain API keys for the AI models you plan to use
- Use the "Set API Key" button in the application to configure them

## Usage

1. Run the application:
```bash
python latex_converter.py
```

2. Using the application:
   - Select your preferred AI model (Gemini or Mistral)
   - Configure your API key if not already set
   - Choose your desired output directory
   - Click "Select Image" to load your equation image
   - Click "Convert to LaTeX" to generate LaTeX code
   - Customize the SVG text color if desired
   - Click "Generate SVG" to create the final SVG output

## Project Structure

```
latex-equation-converter/
├── latex_converter.py    # Main application file
├── ai_models.py         # AI model integration
├── ui_styles.py        # UI styling configuration
├── requirements.txt    # Python dependencies
├── README.md          # Documentation
└── api_keys.txt       # API key storage (git-ignored)
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- LaTeX.codecogs.com for SVG generation
- Google's Gemini AI
- Mistral AI

