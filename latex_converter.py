import os
import sys
from PySide6.QtCore import Qt, Signal, QUrl, QSize, QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QRadioButton, QButtonGroup, QGroupBox,
    QPlainTextEdit, QFileDialog, QMessageBox, QColorDialog,
    QProgressBar, QFrame, QDialog, QLineEdit, QSizePolicy
)
from PySide6.QtGui import (
    QPainter, QRadialGradient, QColor, QBrush, QPixmap,
    QIcon, QDesktopServices, QFont, QDragEnterEvent, QDropEvent, QDragLeaveEvent
)
from PIL import Image

from ui_styles import get_cyberpunk_qss, COLORS
from ai_models import AIModels
from async_workers import AIConversionWorker, SVGGenerationWorker


class ShaderBackgroundWidget(QWidget):
    """Container widget overriding paintEvent to render a radial gradient glow anchored top-center."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Base background fill (#111112)
        painter.fillRect(self.rect(), QColor(COLORS['bg_dark']))

        # Top-center radial gradient glow
        center_x = self.width() / 2.0
        center_y = 0.0
        radius = max(self.width(), self.height()) * 0.70

        radial_grad = QRadialGradient(center_x, center_y, radius)
        # Deep cyberpunk red accent glow transitioning to dark background
        radial_grad.setColorAt(0.0, QColor(255, 0, 60, 85))
        radial_grad.setColorAt(0.35, QColor(255, 0, 60, 25))
        radial_grad.setColorAt(0.75, QColor(255, 0, 60, 5))
        radial_grad.setColorAt(1.0, QColor(17, 17, 18, 0))

        painter.fillRect(self.rect(), QBrush(radial_grad))
        painter.end()
        super().paintEvent(event)


class ImageDropZone(QFrame):
    """Native Drag & Drop interactive zone supporting PNG/JPG/JPEG."""
    image_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background: transparent; border: none;")

        self.text_label = QLabel("Drag & Drop Image Here\nor Click to Browse (.png, .jpg, .jpeg)")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; font-weight: bold; background: transparent; border: none;")

        layout.addWidget(self.preview_label)
        layout.addWidget(self.text_label)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                filepath = url.toLocalFile()
                if filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
                    event.acceptProposedAction()
                    self.setProperty("dragActive", True)
                    self.style().unpolish(self)
                    self.style().polish(self)
                    return
        event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent):
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)

        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                filepath = url.toLocalFile()
                if filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
                    event.acceptProposedAction()
                    self.image_selected.emit(filepath)
                    return

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Select Image", "", "Image files (*.png *.jpg *.jpeg)"
            )
            if filepath:
                self.image_selected.emit(filepath)

    def set_image_preview(self, filepath: str):
        pixmap = QPixmap(filepath)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                QSize(360, 320),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled)
            filename = os.path.basename(filepath)
            self.text_label.setText(f"Loaded: {filename}\n(Click or drop to replace)")
            self.text_label.setStyleSheet(f"color: {COLORS['accent']}; font-size: 12px; font-weight: bold; background: transparent; border: none;")


class ApiKeyDialog(QDialog):
    """Modal Dialog for setting and saving model API Keys."""
    def __init__(self, model_name: str, current_key: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Set API Key - {model_name}")
        self.setFixedSize(480, 210)
        self.model_name = model_name

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel(f"Enter API Key for {model_name}:")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")

        env_var_name = "GEMINI_API_KEY" if model_name == "Gemini" else "MISTRAL_API_KEY"
        hint = QLabel(f"Key is loaded from and saved to your local .env file ({env_var_name})")
        hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")

        self.key_input = QLineEdit(current_key)
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("Paste API key here...")

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("PrimaryButton")
        self.save_btn.clicked.connect(self.accept)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self.key_input)
        layout.addLayout(btn_layout)

    def get_api_key(self) -> str:
        return self.key_input.text().strip()


class LatexConverterApp(QMainWindow):
    """Main Application Window for PySide6 LaTeX Equation Converter."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LaTeX Equation Converter")
        self.resize(1100, 750)
        self.setMinimumSize(900, 600)

        # Initialize AI Models & Business State
        self.ai_models = AIModels()
        self.output_directory = os.getcwd()
        self.current_image_path = None
        self.selected_color = "#ff003c"  # Default Cyberpunk Red
        self.active_worker = None

        # Build UI Structure
        self.init_ui()

        # Check Node.js installation on startup
        self.verify_node_installed()

        # Start Maximized like Tkinter app
        self.showMaximized()

    def init_ui(self):
        # Central widget with custom shader paint event
        self.central_widget = ShaderBackgroundWidget()
        self.setCentralWidget(self.central_widget)

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # --- 1. Header ---
        header_label = QLabel("LaTeX Equation Converter")
        header_label.setObjectName("HeaderTitle")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)

        # --- 2. Controls Section (Side-by-side GroupBoxes) ---
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(16)

        # AI Model Selection Box
        model_box = QGroupBox("Select AI Model")
        model_layout = QHBoxLayout(model_box)
        model_layout.setContentsMargins(16, 16, 16, 16)

        self.gemini_radio = QRadioButton("Gemini")
        self.mistral_radio = QRadioButton("Mistral")
        self.gemini_radio.setChecked(True)

        self.model_button_group = QButtonGroup(self)
        self.model_button_group.addButton(self.gemini_radio)
        self.model_button_group.addButton(self.mistral_radio)

        api_key_btn = QPushButton("Set API Key")
        api_key_btn.clicked.connect(self.show_api_key_dialog)

        model_layout.addWidget(self.gemini_radio)
        model_layout.addWidget(self.mistral_radio)
        model_layout.addStretch()
        model_layout.addWidget(api_key_btn)

        # Output Directory Box
        dir_box = QGroupBox("Output Directory")
        dir_layout = QHBoxLayout(dir_box)
        dir_layout.setContentsMargins(16, 16, 16, 16)

        self.dir_label = QLabel(self.output_directory)
        self.dir_label.setStyleSheet("font-size: 12px;")
        self.dir_label.setToolTip(self.output_directory)

        change_dir_btn = QPushButton("Change Directory")
        change_dir_btn.clicked.connect(self.select_output_directory)

        dir_layout.addWidget(self.dir_label, stretch=1)
        dir_layout.addWidget(change_dir_btn)

        controls_layout.addWidget(model_box, stretch=1)
        controls_layout.addWidget(dir_box, stretch=1)
        main_layout.addLayout(controls_layout)

        # --- 3. Content Columns (50/50 Horizontal Split) ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left Column: Input Image Drop Zone
        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        image_group = QGroupBox("Input Image (Drag & Drop or Select)")
        image_box_layout = QVBoxLayout(image_group)
        image_box_layout.setContentsMargins(16, 20, 16, 16)

        self.drop_zone = ImageDropZone()
        self.drop_zone.image_selected.connect(self.on_image_selected)

        select_btn = QPushButton("Select Image")
        select_btn.clicked.connect(self.select_image_dialog)

        image_box_layout.addWidget(self.drop_zone, stretch=1)
        image_box_layout.addWidget(select_btn)
        left_col.addWidget(image_group)

        # Right Column: LaTeX Output & Actions
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        latex_group = QGroupBox("LaTeX Code")
        latex_box_layout = QVBoxLayout(latex_group)
        latex_box_layout.setContentsMargins(16, 16, 16, 16)
        latex_box_layout.setSpacing(12)

        # Color Selector Row
        color_layout = QHBoxLayout()
        color_layout.setSpacing(12)

        color_label = QLabel("SVG Text Color:")
        color_label.setStyleSheet("font-weight: bold;")

        self.pick_color_btn = QPushButton("Pick Color")
        self.pick_color_btn.clicked.connect(self.open_color_dialog)

        self.color_preview = QFrame()
        self.color_preview.setFixedSize(28, 28)
        self.color_preview.setStyleSheet(f"background-color: {self.selected_color}; border: 1px solid #ffffff; border-radius: 4px;")

        self.color_hex_label = QLabel(self.selected_color)
        self.color_hex_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-family: monospace;")

        color_layout.addWidget(color_label)
        color_layout.addWidget(self.pick_color_btn)
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_hex_label)
        color_layout.addStretch()

        latex_box_layout.addLayout(color_layout)

        # LaTeX Code Text Area
        self.latex_editor = QPlainTextEdit()
        self.latex_editor.setObjectName("MonospaceEditor")
        self.latex_editor.setPlaceholderText("Extracted LaTeX code will appear here after conversion...")

        latex_box_layout.addWidget(self.latex_editor, stretch=1)

        # Status Label & Progress Bar
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("StatusLabel")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        latex_box_layout.addWidget(self.status_label)
        latex_box_layout.addWidget(self.progress_bar)

        right_col.addWidget(latex_group, stretch=1)

        # Action Buttons
        self.convert_btn = QPushButton("Convert to LaTeX")
        self.convert_btn.setObjectName("PrimaryButton")
        self.convert_btn.clicked.connect(self.convert_to_latex)

        self.generate_btn = QPushButton("Generate SVG")
        self.generate_btn.setObjectName("SecondaryButton")
        self.generate_btn.clicked.connect(self.generate_svg)

        right_col.addWidget(self.convert_btn)
        right_col.addWidget(self.generate_btn)

        content_layout.addLayout(left_col, stretch=1)
        content_layout.addLayout(right_col, stretch=1)
        main_layout.addLayout(content_layout, stretch=1)

    # --- Event Handlers & Slot Methods ---
    def get_selected_model_name(self) -> str:
        return "Gemini" if self.gemini_radio.isChecked() else "Mistral"

    def select_image_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image files (*.png *.jpg *.jpeg)"
        )
        if filepath:
            self.on_image_selected(filepath)

    def on_image_selected(self, filepath: str):
        self.current_image_path = filepath
        self.drop_zone.set_image_preview(filepath)
        self.status_label.setText(f"Loaded image: {os.path.basename(filepath)}")

    def select_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.output_directory)
        if directory:
            self.output_directory = directory
            self.dir_label.setText(directory)
            self.dir_label.setToolTip(directory)

    def open_color_dialog(self):
        color = QColorDialog.getColor(QColor(self.selected_color), self, "Select SVG Text Color")
        if color.isValid():
            self.selected_color = color.name()
            self.color_preview.setStyleSheet(f"background-color: {self.selected_color}; border: 1px solid #ffffff; border-radius: 4px;")
            self.color_hex_label.setText(self.selected_color)

    def show_api_key_dialog(self):
        model_name = self.get_selected_model_name()
        current_key = self.ai_models.models[model_name]["api_key"]
        dialog = ApiKeyDialog(model_name, current_key, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_key = dialog.get_api_key()
            self.ai_models.update_api_key(model_name, new_key)
            QMessageBox.information(self, "Success", f"API Key for {model_name} updated successfully in .env.")

    def set_loading_state(self, is_loading: bool, message: str = ""):
        self.convert_btn.setEnabled(not is_loading)
        self.generate_btn.setEnabled(not is_loading)
        self.pick_color_btn.setEnabled(not is_loading)

        if is_loading:
            self.status_label.setText(message)
            self.progress_bar.setRange(0, 0)  # Indeterminate animation
        else:
            # Keep a final success/error message visible after the worker ends.
            self.status_label.setText(message or self.status_label.text() or "Ready")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

    # --- Non-blocking Async Conversion & SVG Generation ---
    def convert_to_latex(self):
        if not self.current_image_path:
            QMessageBox.warning(self, "Warning", "Please select an image first!")
            return

        model_name = self.get_selected_model_name()
        self.set_loading_state(True, f"Converting image with {model_name}...")

        self.active_worker = AIConversionWorker(self.ai_models, model_name, self.current_image_path)
        self.active_worker.success_signal.connect(self.on_conversion_success)
        self.active_worker.error_signal.connect(self.on_conversion_error)
        self.active_worker.progress_signal.connect(self.on_conversion_progress)
        self.active_worker.finished_signal.connect(lambda: self.set_loading_state(False))
        self.active_worker.start()

    def on_conversion_progress(self, message: str):
        self.status_label.setText(message)

    def on_conversion_success(self, latex_code: str, timings: dict):
        self.latex_editor.setPlainText(latex_code)
        provider = timings.get("provider", "AI")
        total = timings.get("total_seconds", 0.0)
        prepare = timings.get("prepare_seconds", 0.0)
        api = timings.get("api_seconds", 0.0)
        parse = timings.get("parse_seconds", 0.0)
        attempts = timings.get("attempts", 1)
        retry_note = f", {attempts} attempts" if attempts > 1 else ""
        self.status_label.setText(
            f"Conversion complete in {total:.1f}s "
            f"(prep {prepare:.1f}s, {provider} {api:.1f}s, parse {parse:.1f}s{retry_note})."
        )

    def on_conversion_error(self, error_msg: str):
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Critical)
        dialog.setWindowTitle("Conversion failed")
        dialog.setText("Could not convert the image.")
        dialog.setInformativeText(error_msg)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.exec()
        self.status_label.setText("Conversion failed — see the error message for details.")

    def closeEvent(self, event):
        """Release persistent AI HTTP connections during application shutdown."""
        self.ai_models.close()
        super().closeEvent(event)

    def check_node_installed(self) -> bool:
        """Verify if Node.js is installed on the host system."""
        try:
            import subprocess
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            res = subprocess.run(["node", "-v"], capture_output=True, text=True, creationflags=creationflags)
            return res.returncode == 0
        except Exception:
            return False

    def verify_node_installed(self) -> bool:
        if not self.check_node_installed():
            QMessageBox.critical(
                self,
                "Node.js Required",
                "Node.js is not installed or not found in your system PATH.\n\n"
                "MathJax rendering requires Node.js to generate SVGs locally and offline.\n"
                "Please download and install Node.js from https://nodejs.org/"
            )
            return False
        return True

    def generate_svg(self):
        if not self.verify_node_installed():
            return

        if not self.current_image_path:
            QMessageBox.warning(self, "Warning", "Please select an image first!")
            return

        latex_code = self.latex_editor.toPlainText().strip()
        if not latex_code:
            QMessageBox.warning(self, "Warning", "No LaTeX code to convert!")
            return

        self.set_loading_state(True, "Rendering SVG locally via MathJax...")

        self.active_worker = SVGGenerationWorker(
            latex_code, self.selected_color, self.output_directory, self.current_image_path
        )
        self.active_worker.success_signal.connect(self.on_svg_success)
        self.active_worker.error_signal.connect(self.on_svg_error)
        self.active_worker.finished_signal.connect(lambda: self.set_loading_state(False))
        self.active_worker.start()

    def on_svg_success(self, folder_name: str):
        self.status_label.setText("SVG generated successfully!")
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder_name))
        success_dialog = QMessageBox(self)
        success_dialog.setIcon(QMessageBox.Icon.Information)
        success_dialog.setWindowTitle("Success")
        success_dialog.setText(f"SVG saved in:\n{folder_name}")
        success_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        QTimer.singleShot(5000, success_dialog.accept)
        success_dialog.exec()

    def on_svg_error(self, error_msg: str):
        QMessageBox.critical(self, "Error", error_msg)
        self.status_label.setText("SVG generation failed.")


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(get_cyberpunk_qss())
    window = LatexConverterApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()