import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import webbrowser
import sys
import os
import subprocess

from PIL import Image
from utils.theme_manager import ThemeManager

class ShortcutTile(ctk.CTkFrame):
    """Einzelne Kachel für eine Verknüpfung"""
    
    def __init__(self, master, shortcut_data, on_delete, on_edit, **kwargs):
        super().__init__(master, **kwargs)
        self.shortcut_data = shortcut_data
        self.on_delete = on_delete
        self.on_edit = on_edit
        
        self.configure(
            fg_color="#2b2b2b",
            corner_radius=4,
            border_width=1,
            border_color="#3d3d3d"
        )
        self.pack_propagate(False)
        
        # Hover-Effekte
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Double-Button-1>", self.launch)
        self.bind("<Button-3>", self._show_context_menu)
        
        # Icon
        self.icon_label = None
        image_path = shortcut_data.get("image_path")
        
        if image_path and os.path.exists(image_path):
            try:
                pil_img = Image.open(image_path)
                # Resize with high quality filter to prevent pixelation
                # We resize to a bit larger than target to keep detail, or exact target with Lanczos
                pil_img = pil_img.resize((64, 64), Image.Resampling.LANCZOS)
                
                # Skalierung für HighDPI handled by CTkImage, passing PIL image
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(40, 40))
                self.icon_label = ctk.CTkLabel(
                    self,
                    text="",
                    image=ctk_img
                )
            except Exception as e:
                print(f"Error loading image: {e}")
                
        if not self.icon_label:
            icon_text = shortcut_data.get("icon", "📁")
            self.icon_label = ctk.CTkLabel(
                self,
                text=icon_text,
                font=("Segoe UI Emoji", 32),
                text_color="#ffffff"
            )

        self.icon_label.pack(pady=(15, 5))
        self.icon_label.bind("<Double-Button-1>", self.launch)
        self.icon_label.bind("<Button-3>", self._show_context_menu)
        
        # Name
        name = shortcut_data.get("name", "Unbenannt")
        if len(name) > 12:
            name = name[:10] + "..."
        self.name_label = ctk.CTkLabel(
            self,
            text=name,
            font=("Segoe UI", 11),
            text_color="#cccccc"
        )
        self.name_label.pack(pady=(0, 10))
        self.name_label.bind("<Double-Button-1>", self.launch)
        self.name_label.bind("<Button-3>", self._show_context_menu)
        
        # Typ-Indikator
        type_icon = "🌐" if shortcut_data.get("type") == "url" else "📂"
        self.type_label = ctk.CTkLabel(
            self,
            text=type_icon,
            font=("Segoe UI Emoji", 10),
            text_color="#666666"
        )
        self.type_label.place(relx=0.9, rely=0.1, anchor="center")
    
    def _on_enter(self, event):
        theme_border = ThemeManager.get_color("border")
        self.configure(fg_color="#3d3d3d", border_color=theme_border)
    
    def _on_leave(self, event):
        self.configure(fg_color="#2b2b2b", border_color="#3d3d3d")
    
    def launch(self, event=None):
        """Startet die Verknüpfung"""
        path = self.shortcut_data.get("path", "")
        shortcut_type = self.shortcut_data.get("type", "file")
        
        try:
            if shortcut_type == "url":
                webbrowser.open(path)
            else:
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", path])
                else:
                    subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte nicht öffnen:\n{e}")
    
    def _show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white",
                       activebackground="#0078d4", activeforeground="white")
        menu.add_command(label="✏️ Bearbeiten", command=lambda: self.on_edit(self.shortcut_data))
        menu.add_command(label="🗑️ Löschen", command=lambda: self.on_delete(self.shortcut_data))
        menu.add_separator()
        menu.add_command(label="📋 Pfad kopieren", command=self._copy_path)
        menu.tk_popup(event.x_root, event.y_root)
    
    def _copy_path(self):
        try:
            import pyperclip
            pyperclip.copy(self.shortcut_data.get("path", ""))
        except ImportError:
            # Fallback if pyperclip is not installed
            self.clipboard_clear()
            self.clipboard_append(self.shortcut_data.get("path", ""))
            self.update() # Required to process clipboard event
        except Exception:
             # Generic fallback
            self.clipboard_clear()
            self.clipboard_append(self.shortcut_data.get("path", ""))
            self.update()
