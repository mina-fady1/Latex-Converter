from tkinter import ttk

def configure_styles(style: ttk.Style):
    # Use clam theme for modern look
    style.theme_use('clam')
    
    # Main colors
    colors = {
        'bg_dark': '#111112',       # Deep black background
        'bg_light': '#1a1a1c',      # Slightly lighter black for elements
        'accent': '#ff003c',        # Strong red accent
        'accent_hover': '#ff335c',  # Lighter red for hover
        'text': '#e4e4e4',          # Light grey text
        'border': '#2c3e50'         # Border color
    }
    
    # Configure general styles
    style.configure(".", 
                   background=colors['bg_dark'],
                   foreground=colors['text'])
    
    # Window background
    style.configure("Main.TFrame",
                   background=colors['bg_dark'])
    
    # Title style
    style.configure("Title.TLabel",
                   font=('Helvetica', 22, 'bold'),
                   foreground=colors['accent'],
                   background=colors['bg_dark'],
                   padding=18)
    
    # Regular labels
    style.configure("TLabel",
                   font=('Helvetica', 12, 'bold'),
                   foreground=colors['text'],
                   background=colors['bg_dark'],
                   padding=6)
    
    # Frames
    style.configure("TFrame",
                   background=colors['bg_dark'])
    
    # LabelFrames
    style.configure("TLabelframe",
                   background=colors['bg_light'],
                   padding=18,
                   borderwidth=0,
                   relief='flat')
    
    style.configure("TLabelframe.Label",
                   font=('Helvetica', 13, 'bold'),
                   foreground=colors['accent'],
                   background=colors['bg_light'],
                   padding=(12, 6))
    
    # Buttons
    style.configure("Action.TButton",
                   font=('Helvetica', 13, 'bold'),
                   background=colors['accent'],
                   foreground='white',
                   padding=(22, 12),
                   borderwidth=0,
                   relief='flat',
                   width=16,
                   bordercolor=colors['accent'],
                   focusthickness=2,
                   focuscolor=colors['accent_hover'])
    
    style.map("Action.TButton",
              background=[('active', colors['accent_hover'])],
              relief=[('pressed', 'sunken')],
              foreground=[('active', 'white')])
    
    # Entry styling
    style.configure("TEntry",
                   fieldbackground=colors['bg_light'],
                   foreground=colors['text'],
                   insertcolor=colors['text'],
                   borderwidth=2,
                   relief='flat',
                   font=('Consolas', 11))
    style.map("TEntry",
              fieldbackground=[('focus', colors['bg_light'])],
              bordercolor=[('focus', colors['accent'])])
    
    return colors  # Return colors for use in text widgets, etc.
