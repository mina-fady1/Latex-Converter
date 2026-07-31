import os
import requests
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk, ImageDraw, ImageFilter
from urllib.parse import quote
import xml.etree.ElementTree as ET
import shutil
from ui_styles import configure_styles
from ai_models import AIModels

class LatexConverter:
    def __init__(self):
        self.window = TkinterDnD.Tk()
        self.window.title("LaTeX Equation Converter")
        # Start maximized
        self.window.state('zoomed')
        
        # Setup styling
        self.style = ttk.Style()
        self.colors = configure_styles(self.style)
        
        # --- Gradient background (shader-like) ---
        self.bg_canvas = tk.Canvas(self.window, highlightthickness=0, bd=0)
        self.bg_canvas.pack(fill="both", expand=True)
        self.gradient_img = self.create_gradient_image(1920, 1080, self.colors['bg_dark'], self.colors['accent'])
        self.gradient_photo = ImageTk.PhotoImage(self.gradient_img)
        self.bg_canvas.create_image(0, 0, anchor="nw", image=self.gradient_photo)
        self.window.bind('<Configure>', self._resize_gradient)
        
        # Main container frame (will be placed on top of canvas)
        self.main_container = ttk.Frame(self.bg_canvas, style="Main.TFrame", padding=20)
        self.bg_canvas.create_window(0, 0, anchor="nw", window=self.main_container, tags="main_frame")
        
        # Initialize AI models
        self.ai_models = AIModels()
        
        # Set default output directory
        self.output_directory = os.getcwd()
        
        # Create UI
        self.create_widgets()
        self._resize_gradient()
        
    def _resize_gradient(self, event=None):
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        if w < 100 or h < 100:
            return
        self.gradient_img = self.create_gradient_image(w, h, self.colors['bg_dark'], self.colors['accent'])
        self.gradient_photo = ImageTk.PhotoImage(self.gradient_img)
        self.bg_canvas.config(width=w, height=h)
        self.bg_canvas.create_image(0, 0, anchor="nw", image=self.gradient_photo)
        self.bg_canvas.coords("main_frame", 0, 0)
        self.bg_canvas.itemconfig("main_frame", width=w, height=h)

    def create_gradient_image(self, width, height, color1, color2):
        from PIL import Image, ImageDraw
        import random
        base = Image.new('RGB', (width, height), color1)
        # Vertical gradient
        top = Image.new('RGB', (width, height), color2)
        mask = Image.new('L', (width, height))
        for y in range(height):
            mask.putpixel((0, y), int(255 * y / height))
        mask = mask.resize((width, height))
        base.paste(top, (0, 0), mask)
        # Radial gradient overlay (shader effect)
        overlay = Image.new('RGBA', (width, height))
        draw = ImageDraw.Draw(overlay)
        max_radius = int(min(width, height) * 0.6)
        center = (width // 2, int(height * 0.4))
        for r in range(max_radius, 0, -8):
            alpha = int(80 * (1 - r / max_radius))
            fill = (255, 0, 60, alpha)
            draw.ellipse([
                center[0] - r, center[1] - r,
                center[0] + r, center[1] + r
            ], fill=fill)
        # Vignette
        vignette = Image.new('L', (width, height), 0)
        vdraw = ImageDraw.Draw(vignette)
        vdraw.ellipse([int(-0.2*width), int(-0.2*height), int(1.2*width), int(1.2*height)], fill=255)
        vignette = vignette.filter(ImageFilter.GaussianBlur(radius=int(0.2*min(width, height))))
        overlay.putalpha(vignette)
        base = base.convert('RGBA')
        base.alpha_composite(overlay)
        # Subtle noise
        noise = Image.effect_noise((width, height), 8)
        noise = noise.point(lambda x: 80 + x//8)
        noise = noise.convert('L')
        noise_img = Image.new('RGBA', (width, height), (0,0,0,0))
        noise_img.putalpha(noise)
        base.alpha_composite(noise_img)
        return base.convert('RGB')
        
    def create_widgets(self):
        # Main container
        main_container = self.main_container
        main_container.pack(fill="both", expand=True)
        
        # Title
        title = ttk.Label(main_container, text="LaTeX Equation Converter",
                         style="Title.TLabel")
        title.pack(pady=(0, 20))
        
        # Controls container for AI model and output directory
        controls_container = ttk.Frame(main_container)
        controls_container.pack(fill="x", padx=10, pady=(0, 20))
        
        # Model selection (left side)
        model_frame = ttk.LabelFrame(controls_container, text="Select AI Model", padding=15)
        model_frame.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        model_controls = ttk.Frame(model_frame)
        model_controls.pack(fill="x")
        
        self.model_var = tk.StringVar(value="Gemini")
        for model in self.ai_models.models.keys():
            ttk.Radiobutton(model_controls, text=model, variable=self.model_var,
                          value=model).pack(side="left", padx=20)
        
        # API Key button
        api_key_btn = ttk.Button(model_controls, text="Set API Key",
                               command=self.show_api_key_dialog,
                               style="Action.TButton")
        api_key_btn.pack(side="right", padx=20)
        
        # Output directory selection (right side)
        dir_frame = ttk.LabelFrame(controls_container, text="Output Directory", padding=15)
        dir_frame.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        dir_controls = ttk.Frame(dir_frame)
        dir_controls.pack(fill="x")
        
        self.dir_label = ttk.Label(dir_controls, text=self.output_directory)
        self.dir_label.pack(side="left", padx=20)
        
        dir_btn = ttk.Button(dir_controls, text="Change Directory",
                           command=self.select_output_directory,
                           style="Action.TButton")
        dir_btn.pack(side="right", padx=20)
        
        # Create columns container
        columns = ttk.Frame(main_container)
        columns.pack(fill="both", expand=True, padx=10)
        
        # Left column (Image)
        left_col = ttk.Frame(columns)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.setup_image_section(left_col)
        
        # Right column (LaTeX + Buttons)
        right_col = ttk.Frame(columns)
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        self.setup_latex_section(right_col)
        
    def setup_image_section(self, parent):
        img_frame = ttk.LabelFrame(parent, text="Input Image (Drag & Drop or Select)", padding=15)
        img_frame.pack(fill="both", expand=True)

        # Configure drop zone
        img_frame.drop_target_register(DND_FILES)
        img_frame.dnd_bind('<<Drop>>', self.handle_drop)
        
        self.img_label = ttk.Label(img_frame, text="Drop an image here or click 'Select Image'", anchor="center")
        self.img_label.pack(pady=20, fill="both", expand=True)
        
        # Also allow dropping on the label itself
        self.img_label.drop_target_register(DND_FILES)
        self.img_label.dnd_bind('<<Drop>>', self.handle_drop)
        
        select_btn = ttk.Button(img_frame, text="Select Image",
                              command=self.select_image,
                              style="Action.TButton")
        select_btn.pack(pady=10)
        
    def setup_latex_section(self, parent):
        # LaTeX output
        latex_frame = ttk.LabelFrame(parent, text="LaTeX Code", padding=15)
        latex_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Color selection with advanced color picker
        color_label_frame = ttk.LabelFrame(latex_frame, text="SVG Text Color")
        color_label_frame.pack(fill="x", pady=(0, 10))
        
        color_frame = ttk.Frame(color_label_frame)
        color_frame.pack(fill="x", padx=5, pady=5)
        
        self.color_var = tk.StringVar(value="#ff003c")  # Default: Red
        
        def open_advanced_color_picker():
            import colorsys
            dialog = tk.Toplevel(self.window)
            dialog.title("Pick SVG Color")
            dialog.geometry("550x440")
            dialog.configure(bg=self.colors['bg_dark'])
            dialog.transient(self.window)
            dialog.grab_set()

            # --- Style all dialog widgets for consistency ---
            def style_widget(widget):
                try:
                    widget.configure(bg=self.colors['bg_dark'])
                except:
                    pass
                for child in getattr(widget, 'winfo_children', lambda:[])():
                    style_widget(child)

            # HSV state
            hsv = [0.0, 1.0, 1.0]  # Default: red
            def hex_to_hsv(hex_color):
                hex_color = hex_color.lstrip('#')
                r, g, b = tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
                return list(colorsys.rgb_to_hsv(r, g, b))
            def hsv_to_hex(h, s, v):
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                return '#%02x%02x%02x' % (int(r*255), int(g*255), int(b*255))
            
            try:
                hsv = hex_to_hsv(self.color_var.get())
            except:
                pass

            # SV square
            sv_size = 240
            hue_height = 240
            hue_width = 40
            sv_canvas = tk.Canvas(dialog, width=sv_size, height=sv_size, highlightthickness=0, bd=0)
            sv_canvas.grid(row=0, column=0, padx=(24,12), pady=(24,12))
            # Hue bar
            hue_canvas = tk.Canvas(dialog, width=hue_width, height=hue_height, highlightthickness=0, bd=0)
            hue_canvas.grid(row=0, column=1, pady=(24,12))
            # Preview
            preview = tk.Label(dialog, width=12, height=2, bg=self.color_var.get(), relief="solid", bd=2)
            preview.grid(row=0, column=2, padx=(12,24), pady=(24,12))
            # Hex input
            hex_var = tk.StringVar(value=self.color_var.get())
            hex_entry = ttk.Entry(dialog, textvariable=hex_var, width=12, style="TEntry")
            hex_entry.grid(row=1, column=0, columnspan=2, pady=(0,16), padx=(24,0), sticky="w")

            # Draw hue bar
            from PIL import Image, ImageTk
            hue_img = Image.new('RGB', (1, hue_height))
            for y in range(hue_height):
                h = y / hue_height
                r, g, b = colorsys.hsv_to_rgb(h, 1, 1)
                hue_img.putpixel((0, y), (int(r*255), int(g*255), int(b*255)))
            hue_img = hue_img.resize((hue_width, hue_height))
            hue_photo = ImageTk.PhotoImage(hue_img)
            hue_canvas.create_image(0, 0, anchor="nw", image=hue_photo)
            hue_canvas.image = hue_photo

            # Draw SV square
            def update_sv_square():
                sv_img = Image.new('RGB', (sv_size, sv_size))
                for x in range(sv_size):
                    for y in range(sv_size):
                        s = x / (sv_size-1)
                        v = 1 - y / (sv_size-1)
                        r, g, b = colorsys.hsv_to_rgb(hsv[0], s, v)
                        sv_img.putpixel((x, y), (int(r*255), int(g*255), int(b*255)))
                sv_photo = ImageTk.PhotoImage(sv_img)
                sv_canvas.create_image(0, 0, anchor="nw", image=sv_photo)
                sv_canvas.image = sv_photo
            update_sv_square()

            # SV square click
            def on_sv_click(event):
                x, y = event.x, event.y
                if 0 <= x < sv_size and 0 <= y < sv_size:
                    hsv[1] = x / (sv_size-1)
                    hsv[2] = 1 - y / (sv_size-1)
                    hex_code = hsv_to_hex(*hsv)
                    hex_var.set(hex_code)
                    preview.configure(bg=hex_code)
            sv_canvas.bind('<Button-1>', on_sv_click)
            sv_canvas.bind('<B1-Motion>', on_sv_click)

            # Hue bar click
            def on_hue_click(event):
                y = event.y
                if 0 <= y < hue_height:
                    hsv[0] = y / hue_height
                    update_sv_square()
                    hex_code = hsv_to_hex(*hsv)
                    hex_var.set(hex_code)
                    preview.configure(bg=hex_code)
            hue_canvas.bind('<Button-1>', on_hue_click)
            hue_canvas.bind('<B1-Motion>', on_hue_click)

            # Hex input change
            def on_hex_change(*_):
                val = hex_var.get()
                if val.startswith('#') and len(val) == 7:
                    preview.configure(bg=val)
                    try:
                        h, s, v = hex_to_hsv(val)
                        hsv[0], hsv[1], hsv[2] = h, s, v
                        update_sv_square()
                    except:
                        pass
            hex_var.trace_add('write', on_hex_change)

            # Save button
            def save_color():
                self.color_var.set(hex_var.get())
                color_preview.configure(bg=hex_var.get())
                dialog.destroy()
            save_btn = ttk.Button(dialog, text="Save", command=save_color, style="Action.TButton")
            save_btn.grid(row=2, column=0, columnspan=2, pady=(0,18), padx=(24,0), sticky="w")
            # Cancel button
            cancel_btn = ttk.Button(dialog, text="Cancel", command=dialog.destroy, style="Action.TButton")
            cancel_btn.grid(row=2, column=2, pady=(0,18), padx=(0,24), sticky="e")

            # --- Style all dialog widgets for consistency ---
            style_widget(dialog)

            # Center the dialog on the main window
            dialog.update_idletasks()
            x = self.window.winfo_x() + (self.window.winfo_width() // 2) - (dialog.winfo_width() // 2)
            y = self.window.winfo_y() + (self.window.winfo_height() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")

            hex_entry.focus_set()

        pick_btn = ttk.Button(color_frame, text="Pick Color", command=open_advanced_color_picker, style="Action.TButton")
        pick_btn.pack(side="left", padx=(0, 10))
        
        color_preview = tk.Label(color_frame, width=3, height=1, bg=self.color_var.get(), relief="solid", bd=2)
        color_preview.pack(side="left")
        
        # Live update for color preview
        def update_color_preview(*_):
            color_preview.configure(bg=self.color_var.get())
        self.color_var.trace_add('write', update_color_preview)
        
        # LaTeX text box
        self.latex_text = tk.Text(latex_frame, height=8,
                                font=('Consolas', 11),
                                wrap='word',
                                bg=self.colors['bg_light'],
                                fg=self.colors['text'],
                                insertbackground=self.colors['text'],
                                selectbackground=self.colors['accent'],
                                selectforeground='white',
                                relief='flat',
                                padx=15,
                                pady=15)
        self.latex_text.pack(fill="both", expand=True, pady=10)
        
        # Action buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", pady=(0, 10))
        
        convert_btn = ttk.Button(btn_frame, text="Convert to LaTeX",
                               command=self.convert_to_latex,
                               style="Action.TButton")
        convert_btn.pack(fill="x", pady=5)
        
        generate_btn = ttk.Button(btn_frame, text="Generate SVG",
                                command=self.generate_svg,
                                style="Action.TButton")
        generate_btn.pack(fill="x", pady=5)
        
    def select_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        self.process_image(file_path)

    def handle_drop(self, event):
        file_path = event.data.strip()
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            self.process_image(file_path)
        else:
            messagebox.showwarning("Invalid File", "Please drop a valid image file (PNG, JPG, JPEG).")

    def process_image(self, file_path):
        if file_path:
            self.current_image_path = file_path
            img = Image.open(file_path)
            img.thumbnail((400, 400))
            photo = ImageTk.PhotoImage(img)
            self.img_label.configure(image=photo, text="", anchor="center")
            self.img_label.image = photo
            
    def convert_to_latex(self):
        if not hasattr(self, 'current_image_path'):
            messagebox.showwarning("Warning", "Please select an image first!")
            return
            
        try:
            selected_model = self.model_var.get()
            
            if selected_model == "Gemini":
                latex_code = self.ai_models.use_gemini(self.current_image_path)
            else:
                latex_code = self.ai_models.use_mistral(self.current_image_path)
            
            self.latex_text.delete(1.0, tk.END)
            self.latex_text.insert(tk.END, latex_code)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to convert image: {str(e)}")
        
    def select_output_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_directory = directory
            self.dir_label.configure(text=directory)
    
    def generate_svg(self):
        if not hasattr(self, 'current_image_path'):
            messagebox.showwarning("Warning", "Please select an image first!")
            return
            
        latex_code = self.latex_text.get(1.0, tk.END).strip()
        if not latex_code:
            messagebox.showwarning("Warning", "No LaTeX code to convert!")
            return
            
        try:
            # Create output folder
            base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
            folder_name = os.path.join(self.output_directory, f"{base_name}_latex")
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            
            # Add color to LaTeX code
            color = self.color_var.get()
            def hex_to_rgb_floats(hex_color):
                hex_color = hex_color.lstrip('#')
                r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                return r/255, g/255, b/255
            r, g, b = hex_to_rgb_floats(color)
            
            cleaned_latex = latex_code.strip()
            if cleaned_latex.startswith('{') and cleaned_latex.endswith('}'):
                cleaned_latex = cleaned_latex[1:-1].strip()
                
            colored_latex = f"\\color[rgb]{{{r:.3f},{g:.3f},{b:.3f}}} {cleaned_latex}"
            
            # FIXED: Properly URL encode latex string for CodeCogs
            encoded_latex = quote(colored_latex, safe='')
            svg_url = f"[https://latex.codecogs.com/svg.latex](https://latex.codecogs.com/svg.latex)?{encoded_latex}"
            
            response = requests.get(svg_url)
            # Verify valid response and ensure CodeCogs did not return an error page/SVG
            if response.status_code == 200 and not (b"Error" in response.content and b"svg" not in response.content):
                original_svg_path = os.path.join(folder_name, "equation.svg")
                with open(original_svg_path, 'wb') as f:
                    f.write(response.content)
                
                os.startfile(folder_name)
                messagebox.showinfo("Success", f"SVG images saved in '{folder_name}' folder!")
            else:
                messagebox.showerror("Error", "CodeCogs failed to render this LaTeX syntax.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save SVG: {str(e)}")

    def show_api_key_dialog(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Set API Key")
        dialog.geometry("400x200")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Configure dialog styling
        dialog.configure(bg=self.colors['bg_dark'])
        
        # Create and pack widgets
        content_frame = ttk.Frame(dialog, style="Main.TFrame", padding=20)
        content_frame.pack(fill="both", expand=True)
        
        selected_model = self.model_var.get()
        
        # Label
        ttk.Label(content_frame, 
                 text=f"Enter API Key for {selected_model}:",
                 style="TLabel").pack(pady=(0, 10))
        
        # Entry field
        api_key = tk.StringVar(value=self.ai_models.models[selected_model]["api_key"])
        entry = ttk.Entry(content_frame, textvariable=api_key, width=40, style="TEntry")
        entry.pack(pady=(0, 20))
        
        # Buttons frame
        btn_frame = ttk.Frame(content_frame)
        btn_frame.pack(fill="x")
        
        def save_key():
            self.ai_models.update_api_key(selected_model, api_key.get())
            dialog.destroy()
        
        # Save button
        save_btn = ttk.Button(btn_frame, text="Save",
                            command=save_key,
                            style="Action.TButton")
        save_btn.pack(side="left", padx=5)
        
        # Cancel button
        cancel_btn = ttk.Button(btn_frame, text="Cancel",
                              command=dialog.destroy,
                              style="Action.TButton")
        cancel_btn.pack(side="right", padx=5)
        
        # Center the dialog on the main window
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        entry.focus_set()

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = LatexConverter()
    app.run()