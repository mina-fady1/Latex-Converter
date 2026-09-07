# LaTeX Equation Converter & Vector Generator

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-Qt6-green.svg)
![Node.js](https://img.shields.io/badge/Node.js-18%2B-brightgreen.svg)
![MathJax](https://img.shields.io/badge/MathJax-v3-red.svg)
![License](https://img.shields.io/badge/License-MIT-purple.svg)

A high-performance desktop application built with **PySide6 (Qt for Python)**, **Google Gemini / Mistral AI (via OpenRouter)**, and a local **MathJax Node.js** renderer. It extracts complex math equations from images, converts them into standard AMS-LaTeX, and generates publication-grade SVG vector files—specifically optimized for seamless Microsoft PowerPoint vector shape conversion and editing.

---

## Key Features

- **AI-Powered Image-to-LaTeX Extraction**:
  - **Google Gemini**: Uses `gemini-3.6-flash` via the supported Google Gen AI SDK.
  - **Mistral AI**: Uses `mistralai/mistral-small-3.1-24b-instruct:free` via OpenRouter (OpenAI client format).
  - Automatically recognizes multi-line equations, matrices, integrals, fractions, summations, aligned systems, and Greek symbols.
  - Strict system prompting prevents document wrapper boilerplate (`\documentclass`, `\begin{document}`), delivering clean MathJax-compatible snippets.
  - Normalizes uploads to a bounded 2048px JPEG before transmission, reuses provider clients, and reports preparation, API, and parsing timings in the status line.
  - Gemini requests use a 60-second per-attempt limit and one visible retry for transient provider failures.
- **Fast, 100% Local & Offline MathJax Renderer**:
  - Subprocess execution (`render_mathjax.js`) utilizing local Node.js and MathJax v3.
  - Complete TeX package support (`amsmath`, `amssymb`, `cancel`, `textmacros`, `mhchem`, etc.).
  - Zero external HTTP dependencies for LaTeX-to-SVG rendering.
- **Optimized for Microsoft PowerPoint Vector Shapes**:
  - Renders with `fontCache: 'none'` to embed direct `<path>` and `<rect>` vector geometries rather than `<use>` references.
  - Converts sizing units from `ex` to standard `px` dimensions (16px base scale).
  - Explicitly injects zero-stroke attributes (`stroke="none" stroke-width="0" stroke-opacity="0"`) so converted PowerPoint shapes import with sharp, clean edges and no unwanted thick default borders.
  - Outputs standalone SVGs with standard XML declaration headers.
- **Cyberpunk Dark Theme UI**:
  - Custom radial gradient shader glow background anchored top-center.
  - Interactive **Drag & Drop** drop zone supporting `.png`, `.jpg`, and `.jpeg` images.
  - Live color picker with dynamic hex preview and real-time color badge.
  - Non-blocking asynchronous multithreading (`QThread`) keeping the UI responsive during AI extraction and SVG compilation.
  - Local API key persistence in `api_keys.txt`.

---

## Prerequisites

Ensure you have the following installed on your system:

1. **Python 3.10+** (with `pip`)
2. **Node.js 18+** (with `npm`) &mdash; *Required for local MathJax SVG rendering*

---

## Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/mina-fady1/Latex-Converter.git
   cd Latex-Converter
   ```

2. **Set Up a Python Virtual Environment**:
   ```bash
   python -m venv .venv

   # On Windows (PowerShell):
   .venv\Scripts\activate

   # On Windows (Command Prompt):
   .venv\Scripts\activate.bat

   # On macOS / Linux:
   source .venv/bin/activate
   ```

3. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Node.js MathJax Dependencies**:
   ```bash
   npm install
   ```

---

## Running the Application

Launch the application using either entry script:

```bash
python main_app.py
# or
python latex_converter.py
```

---

## How to Use

1. **Configure AI API Keys**:
   - Select your preferred model (**Gemini** or **Mistral**) in the top panel.
   - Click **Set API Key**.
     - For **Gemini**: Enter your API key from [Google AI Studio](https://aistudio.google.com/).
     - For **Mistral**: Enter your API key from [OpenRouter](https://openrouter.ai/).
   - Keys are securely stored locally in `api_keys.txt` (which is excluded from Git).
2. **Load an Equation Image**:
   - Drag and drop any `.png`, `.jpg`, or `.jpeg` file directly onto the drop zone, or click **Select Image** / drop zone to browse.
   - A sample test image is provided in the root directory (`Hard Math Equation.png`) and in `screenshots/test.jpeg`.
3. **Convert Image to LaTeX**:
   - Click **Convert to LaTeX**.
   - The AI worker extracts the equation and displays the editable AMS-LaTeX code in the central editor.
4. **Choose SVG Text Color & Generate**:
   - Click **Pick Color** to choose any custom accent color for the SVG math symbols (defaults to `#ff003c`).
   - Click **Generate SVG**.
   - The app compiles the SVG locally using MathJax, saves it to `{output_directory}/{image_name}_latex/equation.svg`, and opens the output folder automatically.

---

## Microsoft PowerPoint Vector Shape Guide

To convert your generated SVG into editable, high-resolution Microsoft PowerPoint shapes:

1. Drag and drop the generated `equation.svg` file directly onto your PowerPoint slide (or use **Insert -> Pictures -> This Device**).
2. Right-click the SVG on the slide and choose **Convert to Shape** (or select it and press `Ctrl + Shift + G` to ungroup).
3. PowerPoint will turn each math symbol and stroke into an individual native vector shape that you can resize without quality loss, recolor, animate, or re-arrange.
4. If an outline appears on older Office versions, select all shapes and set **Shape Format -> Shape Outline -> No Outline**.

---

## Project Structure

```
Latex-Converter/
├── latex_converter.py     # Main PySide6 application window and GUI logic
├── main_app.py            # Main application entry point
├── ai_models.py           # Gemini & Mistral (OpenRouter) API integrations
├── async_workers.py       # QThread background workers for AI calls & Node.js subprocess
├── ui_styles.py           # Cyberpunk dark theme stylesheet (QSS) & color palette
├── render_mathjax.js      # Local Node.js MathJax TeX-to-SVG rendering engine
├── package.json           # Node.js manifest & MathJax dependency
├── requirements.txt       # Python dependencies (PySide6, google-generativeai, openai, Pillow, requests)
├── api_keys.txt           # Local API key storage (auto-generated)
├── Hard Math Equation.png # Sample test image
├── screenshots/           # Test assets & sample images
├── .gitignore             # Git exclusion rules
└── README.md              # Project documentation
```

---

## Troubleshooting

- **"Node.js is not installed or not found in system PATH"**:
  - Download and install Node.js (LTS version recommended) from [nodejs.org](https://nodejs.org/).
  - Ensure `node` and `npm` are available in your system's `PATH`. Run `node -v` in your terminal to verify.
- **MathJax module missing**:
  - Run `npm install` inside the project root directory so `node_modules/mathjax` is installed.
- **API Key Errors**:
  - Verify that your Gemini key is active in Google AI Studio or your OpenRouter key has access to the Mistral model.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
