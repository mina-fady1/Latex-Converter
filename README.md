# LaTeX Equation Converter & Vector Generator

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-Qt6-green.svg)
![Node.js](https://img.shields.io/badge/Node.js-18%2B-brightgreen.svg)
![MathJax](https://img.shields.io/badge/MathJax-v3%2Fv4-red.svg)
![License](https://img.shields.io/badge/License-MIT-purple.svg)

A high-performance desktop application built with **PySide6 (Qt for Python)**, **Google Gemini / Mistral AI**, and a local **MathJax Node.js** renderer. It extracts math equations from images, converts them into standard AMS-LaTeX, and generates publication-grade SVG vector files—optimized for seamless Microsoft PowerPoint vector shape editing.

---

## Key Features

- **AI-Powered Image-to-LaTeX Extraction**:
  - Leverages **Gemini 3.6 Flash** and **Mistral Small** vision models.
  - Automatically handles multi-line expressions, matrices, integrals, fractions, and Greek symbols.
- **Fast, Local, Offline MathJax Renderer**:
  - Uses local **Node.js** execution (`render_mathjax.js`) via Python subprocesses.
  - Complete TeX extension support (`amsmath`, `amssymb`, `cancel`, `textmacros`, `mhchem`, etc.).
  - Zero external HTTP network dependencies for rendering.
- **Microsoft PowerPoint Vector Compatibility**:
  - Configured with `fontCache: 'none'` to embed direct, standalone `<path>` vector shapes instead of `<use>` symbol references.
  - Automatically tags elements with zero-stroke properties (`stroke="none" stroke-width="0" stroke-opacity="0"`).
  - Ungroups in PowerPoint into 100% sharp, editable Microsoft Office Drawing Objects with crisp lines.
- **Cyberpunk Dark Theme UI**:
  - Custom radial gradient shader glow background anchored top-center.
  - Interactive **Drag & Drop** image zone supporting PNG, JPG, and JPEG formats.
  - Live SVG text color picker with hex preview.
  - Non-blocking asynchronous multithreading (`QThread`) for smooth UI performance.

---

## Prerequisites

Ensure you have the following installed on your host system:

1. **Python 3.10+** (with `pip`)
2. **Node.js 18+** (with `npm`) - *Required for local MathJax rendering*

---

## Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/elewashy/latex-equation-converter.git
   cd latex-equation-converter
   ```

2. **Set Up Python Virtual Environment**:
   ```bash
   python -m venv .venv
   # On Windows (PowerShell / Command Prompt):
   .venv\Scripts\activate
   # On macOS / Linux:
   source .venv/bin/activate
   ```

3. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Node.js MathJax Dependency**:
   ```bash
   npm install
   ```

---

## Running the Application

Launch the application using either entry point:

```bash
python latex_converter.py
# or
python main_app.py
```

---

## How to Use

1. **Set AI API Key**:
   - Click **Set API Key** in the top control panel.
   - Enter your **Gemini** or **Mistral (OpenRouter)** API key. Keys are securely stored locally in `api_keys.txt`.
2. **Load Equation Image**:
   - Drag and drop any `.png`, `.jpg`, or `.jpeg` file onto the central drop zone, or click **Select Image**.
3. **Convert Image to LaTeX**:
   - Click **Convert to LaTeX**. The AI will extract the equation and display clean AMS-LaTeX in the text editor.
4. **Choose SVG Text Color & Generate**:
   - Pick a custom accent color using **Pick Color**.
   - Click **Generate SVG**. The app will render the SVG locally via MathJax and save it in `{output_directory}/{image_name}_latex/equation.svg`.

---

## Microsoft PowerPoint Vector Shape Guide

To convert your generated SVG into editable, sharp PowerPoint vector shapes:

1. Drag and drop the generated `equation.svg` onto any PowerPoint slide.
2. Right-click the SVG and select **Convert to Shape** (or press `Ctrl + Shift + G` to **Ungroup**).
3. If an older shape appears thick, select the converted object in PowerPoint and set **Shape Format -> Shape Outline -> No Outline**.

---

## Project Structure

```
LaTeX Converter/
├── latex_converter.py     # Main PySide6 Application Window & GUI
├── main_app.py            # Entry point script
├── ai_models.py           # Gemini & Mistral LLM API Integrations
├── async_workers.py       # QThread workers for AI and Node.js MathJax subprocess
├── ui_styles.py           # Cyberpunk QSS Theme System & Color Palette
├── render_mathjax.js      # Local Node.js MathJax TeX-to-SVG rendering CLI
├── package.json           # Node.js manifest (MathJax dependency)
├── requirements.txt       # Python dependencies (PySide6, google-generativeai, openai, Pillow)
├── .gitignore             # Git exclusion rules
└── README.md              # Project documentation
```

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
