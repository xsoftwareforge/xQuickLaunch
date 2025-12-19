import customtkinter as ctk
import time
from datetime import datetime
import tkinter as tk

class Topbar(ctk.CTkToplevel):
    def __init__(self, app_controller):
        super().__init__()
        
        self.app_controller = app_controller
        self.config_data = app_controller.config_data
        
        self.title("QuickLaunch Bar")
        
    def __init__(self, app_controller):
        super().__init__()
        
        self.app_controller = app_controller
        self.config_data = app_controller.config_data
        
        self.title("QuickLaunch Bar")
        
        # Dimensions (Increased height for better spacing)
        self.width = 300
        self.height = 55
        
        # Calculate position (Centered at top)
        screen_width = self.winfo_screenwidth()
        x_pos = (screen_width - self.width) // 2
        y_pos = 0
        
        self.geometry(f"{self.width}x{self.height}+{x_pos}+{y_pos}")
        self.overrideredirect(True) # Frameless
        
        # Transparency Setup
        # Using a distinct color key for transparency
        self.transparent_color = "#000001"
        self.configure(fg_color=self.transparent_color)
        self.attributes("-transparentcolor", self.transparent_color)
        
        self.attributes("-topmost", self.config_data["settings"].get("topbar_always_on_top", True))
        
        self._create_widgets()
        self._setup_context_menu()
        self._update_clock()
        
    def _create_widgets(self):
        # Main Pill Frame (Metallic: Gunmetal Gray, Silver Border)
        self.frame = ctk.CTkFrame(
            self, 
            fg_color="#2b2b2b", # Gunmetal Gray
            corner_radius=8,    # Machined part look
            border_width=2,
            border_color="#a0a0a0", # Silver/Aluminum
            width=self.width,
            height=self.height
        )
        self.frame.pack(fill="both", expand=True, padx=0, pady=0)
        # We allow pack to propagate slightly or manage inside manually
        # self.frame.pack_propagate(False) 
        
        # Layout container
        # Using Pack inside for clean vertical stacking
        
        # Clock / Date
        self.time_label = ctk.CTkLabel(
            self.frame,
            text="--:--",
            font=("Segoe UI", 13, "bold"), # Standard Clean Font
            text_color="#f0f0f0"           # Off-White
        )
        self.time_label.pack(side="top", pady=(5, 0))
        
        # Separator Line (Groove look)
        self.separator = ctk.CTkFrame(
            self.frame,
            height=2,
            fg_color="#1a1a1a", # Darker groove
            width=self.width - 60
        )
        self.separator.pack(side="top", pady=(2, 2))
        
        # Toggle Arrow Button
        self.arrow_btn = ctk.CTkLabel(
            self.frame,
            text="▼", # Initial state
            font=("Segoe UI", 10, "bold"),
            text_color="#cccccc", # Silver Arrow
            cursor="hand2"
        )
        self.arrow_btn.pack(side="top", pady=(0, 5))
        self.arrow_btn.bind("<Button-1>", self._toggle_quicklaunch)
        
        # Controls Frame (Absolute positioning for precise placement)
        # Placed at top-right of the frame
        self.controls_frame = ctk.CTkFrame(
            self.frame,
            fg_color="transparent",
            width=40,
            height=20
        )
        self.controls_frame.place(relx=0.95, rely=0.15, anchor="ne")
        
        # Close Button
        self.close_btn = ctk.CTkLabel(
            self.controls_frame,
            text="✕",
            font=("Segoe UI", 10, "bold"),
            text_color="#888888",
            cursor="hand2"
        )
        self.close_btn.pack(side="right", padx=2)
        self.close_btn.bind("<Button-1>", lambda e: self.app_controller.quit_app())
        self.close_btn.bind("<Enter>", lambda e: self.close_btn.configure(text_color="#ff5555"))
        self.close_btn.bind("<Leave>", lambda e: self.close_btn.configure(text_color="#888888"))
        
        # Minimize Button
        self.min_btn = ctk.CTkLabel(
            self.controls_frame,
            text="─",
            font=("Segoe UI", 10, "bold"),
            text_color="#888888",
            cursor="hand2"
        )
        self.min_btn.pack(side="right", padx=2)
        self.min_btn.bind("<Button-1>", lambda e: self.app_controller.minimize_to_tray())
        self.min_btn.bind("<Enter>", lambda e: self.min_btn.configure(text_color="#ffffff"))
        self.min_btn.bind("<Leave>", lambda e: self.min_btn.configure(text_color="#888888"))
    
    def _setup_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="#ffffff")
        
        self.always_on_top_var = tk.BooleanVar(value=self.config_data["settings"].get("topbar_always_on_top", True))
        self.context_menu.add_checkbutton(
            label="Immer im Vordergrund",
            variable=self.always_on_top_var,
            command=self._toggle_always_on_top
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Beenden", command=self.app_controller.quit_app)
        
        # Bind context menu to frame and labels
        self.frame.bind("<Button-3>", self._show_context_menu)
        self.time_label.bind("<Button-3>", self._show_context_menu)
        self.arrow_btn.bind("<Button-3>", self._show_context_menu)
        
        # Dragging Bindings
        self.frame.bind("<Button-1>", self._start_move)
        self.time_label.bind("<Button-1>", self._start_move)
        
        self.frame.bind("<B1-Motion>", self._on_move)
        self.time_label.bind("<B1-Motion>", self._on_move)

    def _start_move(self, event):
        self._x = event.x
        # self._y = event.y # We don't need Y for horizontal only

    def _on_move(self, event):
        deltax = event.x - self._x
        # deltay = event.y - self._y # Ignore vertical delta
        
        x = self.winfo_x() + deltax
        y = 0 # Fixed top
        
        self.geometry(f"+{x}+{y}")

    def _update_clock(self):
        now = datetime.now()
        time_str = now.strftime("%H:%M  |  %d.%m.%Y")
        self.time_label.configure(text=time_str)
        self.after(1000, self._update_clock)
        
    def _toggle_quicklaunch(self, event=None):
        is_visible = self.app_controller.toggle_quicklaunch_window()
        self.arrow_btn.configure(text="▲" if is_visible else "▼")

    def _show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
            
    def _toggle_always_on_top(self):
        state = self.always_on_top_var.get()
        self.attributes("-topmost", state)
        self.app_controller.update_setting("topbar_always_on_top", state)
