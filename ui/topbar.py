import customtkinter as ctk
import time
from datetime import datetime
import tkinter as tk
from utils.system_utils import get_system_stats
from utils.theme_manager import ThemeManager

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
        self.width = 350
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
        self._update_status()
        
    def _create_widgets(self):
        theme_border = ThemeManager.get_color("border")
        
        # Main Pill Frame (Metallic: Gunmetal Gray, Silver Border)
        self.frame = ctk.CTkFrame(
            self, 
            fg_color="#2b2b2b", # Gunmetal Gray
            corner_radius=8,    # Machined part look
            border_width=2,
            border_color=theme_border, # Dynamic Border
            width=self.width,
            height=self.height
        )
        self.frame.pack(fill="both", expand=True, padx=0, pady=0)
        # We allow pack to propagate slightly or manage inside manually
        # self.frame.pack_propagate(False) 
        
        # Layout container
        # Using Pack inside for clean vertical stacking
        
        # Info Frame (CPU | Time | RAM)
        self.info_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.info_frame.pack(side="top", pady=(5, 0), fill="x", padx=10)
        
        theme_accent = ThemeManager.get_color("accent_text")
        
        # CPU Label
        self.cpu_label = ctk.CTkLabel(
            self.info_frame,
            text="CPU 0%",
            font=("Segoe UI", 9, "bold"),
            text_color=theme_accent # Dynamic
        )
        self.cpu_label.pack(side="left")

        # Clock / Date
        self.time_label = ctk.CTkLabel(
            self.info_frame,
            text="--:--",
            font=("Segoe UI", 13, "bold"), # Standard Clean Font
            text_color="#f0f0f0"           # Off-White
        )
        self.time_label.pack(side="left", expand=True)
        
        # RAM Label
        self.ram_label = ctk.CTkLabel(
            self.info_frame,
            text="RAM 0%",
            font=("Segoe UI", 9, "bold"),
            text_color=theme_accent # Dynamic
        )
        self.ram_label.pack(side="right", padx=(0, 50))
        
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
        self.controls_frame.place(relx=0.96, rely=0.10, anchor="ne")
        
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
        self.cpu_label.bind("<Button-3>", self._show_context_menu)
        self.ram_label.bind("<Button-3>", self._show_context_menu)
        self.arrow_btn.bind("<Button-3>", self._show_context_menu)
        
        # Dragging Bindings
        self.frame.bind("<Button-1>", self._start_move)
        self.time_label.bind("<Button-1>", self._start_move)
        self.cpu_label.bind("<Button-1>", self._start_move)
        self.ram_label.bind("<Button-1>", self._start_move)
        
        self.frame.bind("<B1-Motion>", self._on_move)
        self.time_label.bind("<B1-Motion>", self._on_move)
        self.cpu_label.bind("<B1-Motion>", self._on_move)
        self.ram_label.bind("<B1-Motion>", self._on_move)

    def _start_move(self, event):
        self._x = event.x
        # self._y = event.y # We don't need Y for horizontal only

    def _on_move(self, event):
        deltax = event.x - self._x
        # deltay = event.y - self._y # Ignore vertical delta
        
        x = self.winfo_x() + deltax
        y = 0 # Fixed top
        
        self.geometry(f"+{x}+{y}")

    def _update_status(self):
        # Update Clock
        now = datetime.now()
        time_str = now.strftime("%H:%M") # Shorter format without date for space
        # Or keep date if it fits. previous was %H:%M | %d.%m.%Y
        # Let's try to keep it if possible, or cycle?
        # Let's stick to short time + date in tool tip? No tooltips yet.
        # Let's try full string.
        time_str = now.strftime("%H:%M  |  %d.%m.%Y")
        self.time_label.configure(text=time_str)
        
        # Update Stats
        cpu, ram = get_system_stats()
        self.cpu_label.configure(text=f"CPU {int(cpu)}%")
        self.ram_label.configure(text=f"RAM {int(ram)}%")
        
        theme_accent = ThemeManager.get_color("accent_text")
        
        # Color warning
        if cpu > 80:
             self.cpu_label.configure(text_color="#ff5555")
        else:
             self.cpu_label.configure(text_color=theme_accent)
             
        if ram > 80:
             self.ram_label.configure(text_color="#ff5555")
        else:
             self.ram_label.configure(text_color=theme_accent)

        self.after(1000, self._update_status)
        
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
