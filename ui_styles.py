"""
UI Style System for LaTeX Converter - Cyberpunk Dark Theme (PySide6 / QSS)
"""

COLORS = {
    'bg_dark': '#111112',       # Deep black background
    'bg_surface': '#1a1a1c',    # Slightly lighter surface/panel dark
    'accent': '#ff003c',        # Primary red accent
    'accent_hover': '#ff335c',  # Lighter red hover accent
    'accent_pressed': '#d90033',# Darker red for button press
    'text': '#e4e4e4',          # Primary light grey text
    'text_muted': '#8a8a93',    # Muted secondary text
    'border': '#2c3e50',        # Panel border color
    'border_focus': '#ff003c',  # Focus border color
    'success': '#00e676',       # Success status color
    'error': '#ff1744'          # Error status color
}

def get_cyberpunk_qss() -> str:
    """Returns the complete QSS stylesheet for PySide6 application."""
    return f"""
    /* Global Application Styling */
    QWidget {{
        color: {COLORS['text']};
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
        font-size: 13px;
    }}
    
    QMainWindow {{
        background-color: {COLORS['bg_dark']};
    }}
    
    /* Dialog Windows */
    QDialog {{
        background-color: {COLORS['bg_dark']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
    }}

    /* Titles and Header Labels */
    QLabel#HeaderTitle {{
        font-size: 26px;
        font-weight: bold;
        color: {COLORS['accent']};
        letter-spacing: 1px;
    }}
    
    QLabel#SectionTitle {{
        font-size: 14px;
        font-weight: bold;
        color: {COLORS['text']};
    }}
    
    QLabel#StatusLabel {{
        font-size: 12px;
        color: {COLORS['text_muted']};
    }}
    
    /* Group Boxes / Panels */
    QGroupBox {{
        background-color: {COLORS['bg_surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        margin-top: 14px;
        font-weight: bold;
        font-size: 13px;
        color: {COLORS['accent']};
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 14px;
        padding: 0 8px;
        background-color: {COLORS['bg_surface']};
        color: {COLORS['accent']};
    }}
    
    /* Buttons */
    QPushButton {{
        background-color: {COLORS['bg_surface']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: #242428;
        border-color: {COLORS['accent']};
        color: #ffffff;
    }}
    
    QPushButton:pressed {{
        background-color: #171719;
    }}

    QPushButton#PrimaryButton {{
        background-color: {COLORS['accent']};
        color: #ffffff;
        border: 1px solid {COLORS['accent']};
        border-radius: 10px;
        padding: 12px 20px;
        font-size: 14px;
        font-weight: bold;
    }}
    
    QPushButton#PrimaryButton:hover {{
        background-color: {COLORS['accent_hover']};
        border-color: {COLORS['accent_hover']};
        box-shadow: 0 0 10px {COLORS['accent_hover']};
    }}
    
    QPushButton#PrimaryButton:pressed {{
        background-color: {COLORS['accent_pressed']};
        border-color: {COLORS['accent_pressed']};
    }}

    QPushButton#SecondaryButton {{
        background-color: transparent;
        color: {COLORS['text']};
        border: 1px solid {COLORS['accent']};
        border-radius: 10px;
        padding: 10px 20px;
        font-size: 13px;
        font-weight: bold;
    }}
    
    QPushButton#SecondaryButton:hover {{
        background-color: rgba(255, 0, 60, 0.15);
        color: #ffffff;
        border-color: {COLORS['accent_hover']};
    }}
    
    QPushButton#SecondaryButton:pressed {{
        background-color: rgba(255, 0, 60, 0.25);
    }}
    
    QPushButton:disabled {{
        background-color: #222226;
        color: #666666;
        border-color: #333338;
    }}

    /* Radio Buttons */
    QRadioButton {{
        spacing: 8px;
        font-size: 13px;
        font-weight: bold;
        color: {COLORS['text']};
    }}
    
    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 9px;
        border: 2px solid {COLORS['border']};
        background-color: {COLORS['bg_dark']};
    }}
    
    QRadioButton::indicator:hover {{
        border-color: {COLORS['accent']};
    }}
    
    QRadioButton::indicator:checked {{
        border: 2px solid {COLORS['accent']};
        background-color: {COLORS['accent']};
    }}

    /* Text & Monospace Inputs */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {COLORS['bg_surface']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 10px;
        selection-background-color: {COLORS['accent']};
        selection-color: #ffffff;
    }}
    
    QPlainTextEdit#MonospaceEditor {{
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.4;
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {COLORS['accent']};
    }}

    /* Drop Zone Frame */
    QFrame#DropZone {{
        background-color: rgba(26, 26, 28, 0.7);
        border: 2px dashed {COLORS['border']};
        border-radius: 12px;
    }}

    QFrame#DropZone[dragActive="true"] {{
        border: 2px dashed {COLORS['accent']};
        background-color: rgba(255, 0, 60, 0.08);
    }}

    /* Progress Bar */
    QProgressBar {{
        background-color: {COLORS['bg_surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        text-align: center;
        color: {COLORS['text']};
        font-weight: bold;
        max-height: 12px;
    }}
    
    QProgressBar::chunk {{
        background-color: {COLORS['accent']};
        border-radius: 5px;
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: {COLORS['bg_dark']};
        width: 10px;
        margin: 0px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['border']};
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLORS['accent']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    """
