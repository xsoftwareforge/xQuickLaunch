import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from utils.system_utils import check_autostart, set_autostart
from utils.theme_manager import ThemeManager

class EditDialog(ctk.CTkToplevel):
    """Dialog zum Bearbeiten einer Verknüpfung"""
    
    def __init__(self, master, shortcut_data, save_callback, refresh_callback):
        super().__init__(master)
        self.shortcut_data = shortcut_data
        self.save_callback = save_callback
        self.refresh_callback = refresh_callback
        
        self.title("Verknüpfung bearbeiten")
        self.geometry("420x400")
        self.configure(fg_color="#1a1a1a")
        self.resizable(False, False)
        
        # Zentrieren
        self.transient(master)
        self.wait_visibility()
        self.grab_set()
        
        # Name
        ctk.CTkLabel(self, text="Name:", font=("Segoe UI", 12)).pack(pady=(15, 5), padx=20, anchor="w")
        self.name_entry = ctk.CTkEntry(self, width=380, height=35)
        self.name_entry.insert(0, shortcut_data.get("name", ""))
        self.name_entry.pack(padx=20)
        
        # Pfad/URL
        ctk.CTkLabel(self, text="Pfad/URL:", font=("Segoe UI", 12)).pack(pady=(10, 5), padx=20, anchor="w")
        self.path_entry = ctk.CTkEntry(self, width=380, height=35)
        self.path_entry.insert(0, shortcut_data.get("path", ""))
        self.path_entry.pack(padx=20)
        
        # Emoji & Bild Container
        icon_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        icon_wrapper.pack(fill="x", padx=20, pady=10)
        
        # Spalte 1: Emoji
        left_frame = ctk.CTkFrame(icon_wrapper, fg_color="transparent")
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        
        ctk.CTkLabel(left_frame, text="Emoji:", font=("Segoe UI", 12)).pack(anchor="w", pady=(0, 5))
        self.emoji_entry = ctk.CTkEntry(left_frame, width=60, height=35)
        self.emoji_entry.insert(0, shortcut_data.get("icon", "📁"))
        self.emoji_entry.pack(anchor="w")
        
        # Spalte 2: Bild Datei
        right_frame = ctk.CTkFrame(icon_wrapper, fg_color="transparent")
        right_frame.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(right_frame, text="Bild-Datei (Optional):", font=("Segoe UI", 12)).pack(anchor="w", pady=(0, 5))
        
        img_row = ctk.CTkFrame(right_frame, fg_color="transparent")
        img_row.pack(fill="x")
        
        self.image_entry = ctk.CTkEntry(img_row, width=200, height=35)
        current_img = shortcut_data.get("image_path", "")
        if current_img:
             self.image_entry.insert(0, current_img)
        self.image_entry.pack(side="left", fill="x", expand=True)
        
        ctk.CTkButton(
            img_row, text="📂", width=50, height=35,
            fg_color="#3d3d3d", hover_color="#4d4d4d",
            command=self._browse_icon
        ).pack(side="left", padx=(5, 0))
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20, fill="x", padx=20)
        
        ctk.CTkButton(
            btn_frame, text="Abbrechen", width=140,
            fg_color="#3d3d3d", hover_color="#4d4d4d",
            command=self.destroy
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame, text="Speichern", width=140,
            fg_color="#0078d4", hover_color="#1084d8",
            command=self._save
        ).pack(side="right", padx=5)
    
    def _browse_icon(self):
        file_types = [
            ("Bilder", "*.png;*.jpg;*.jpeg;*.ico;*.gif"),
            ("Alle Dateien", "*.*")
        ]
        path = filedialog.askopenfilename(filetypes=file_types)
        if path:
            self.image_entry.delete(0, "end")
            self.image_entry.insert(0, path)

    def _save(self):
        new_path = self.path_entry.get()
        emoji_val = self.emoji_entry.get().strip() or "📁"
        image_val = self.image_entry.get().strip()
        
        import os
        
        self.shortcut_data["name"] = self.name_entry.get()
        self.shortcut_data["path"] = new_path
        self.shortcut_data["icon"] = emoji_val
        
        if image_val and os.path.exists(image_val):
            self.shortcut_data["image_path"] = image_val
        else:
            # If empty or invalid, remove existing image_path to fallback to Emoji
            if "image_path" in self.shortcut_data:
                del self.shortcut_data["image_path"]
        
        # Typ automatisch erkennen
        if self.path_entry.get().startswith(("http://", "https://")):
            self.shortcut_data["type"] = "url"
        else:
            self.shortcut_data["type"] = "file"
        
        self.save_callback()
        self.refresh_callback()
        self.destroy()


class AddDialog(ctk.CTkToplevel):
    """Dialog zum Hinzufügen einer neuen Verknüpfung"""
    
    def __init__(self, master, add_callback):
        super().__init__(master)
        self.add_callback = add_callback
        
        self.title("Neue Verknüpfung")
        self.geometry("420x420")
        self.configure(fg_color="#1a1a1a")
        self.resizable(False, False)
        
        self.transient(master)
        self.wait_visibility()
        self.grab_set()
        
        # Typ-Auswahl
        self.type_var = ctk.StringVar(value="file")
        
        type_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=10)
        type_frame.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkRadioButton(
            type_frame, text="📁 Datei/Ordner", variable=self.type_var,
            value="file", font=("Segoe UI", 12),
            command=self._update_ui
        ).pack(side="left", padx=20, pady=15)
        
        ctk.CTkRadioButton(
            type_frame, text="🌐 URL/Website", variable=self.type_var,
            value="url", font=("Segoe UI", 12),
            command=self._update_ui
        ).pack(side="left", padx=20, pady=15)
        
        # Name
        ctk.CTkLabel(self, text="Name:", font=("Segoe UI", 12)).pack(pady=(10, 5), padx=20, anchor="w")
        self.name_entry = ctk.CTkEntry(self, width=380, height=35, placeholder_text="z.B. Google Chrome")
        self.name_entry.pack(padx=20)
        
        # Pfad/URL
        self.path_label = ctk.CTkLabel(self, text="Pfad:", font=("Segoe UI", 12))
        self.path_label.pack(pady=(15, 5), padx=20, anchor="w")
        
        path_frame = ctk.CTkFrame(self, fg_color="transparent")
        path_frame.pack(fill="x", padx=20)
        
        self.path_entry = ctk.CTkEntry(path_frame, width=300, height=35, placeholder_text="C:\\Program Files\\...")
        self.path_entry.pack(side="left")
        
        self.browse_btn = ctk.CTkButton(
            path_frame, text="📂", width=60, height=35,
            fg_color="#3d3d3d", hover_color="#4d4d4d",
            command=self._browse
        )
        self.browse_btn.pack(side="left", padx=(10, 0))
        
        # Icon
        icon_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        icon_wrapper.pack(fill="x", padx=20, pady=10)
        
        # Spalte 1: Emoji
        left_frame = ctk.CTkFrame(icon_wrapper, fg_color="transparent")
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        
        ctk.CTkLabel(left_frame, text="Emoji:", font=("Segoe UI", 12)).pack(anchor="w", pady=(0, 5))
        self.emoji_entry = ctk.CTkEntry(left_frame, width=60, height=35)
        self.emoji_entry.insert(0, "📁")
        self.emoji_entry.pack(anchor="w")
        
        # Spalte 2: Bild Datei
        right_frame = ctk.CTkFrame(icon_wrapper, fg_color="transparent")
        right_frame.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(right_frame, text="Bild-Datei (Optional):", font=("Segoe UI", 12)).pack(anchor="w", pady=(0, 5))
        
        img_row = ctk.CTkFrame(right_frame, fg_color="transparent")
        img_row.pack(fill="x")
        
        self.image_entry = ctk.CTkEntry(img_row, width=200, height=35)
        self.image_entry.pack(side="left", fill="x", expand=True)
        
        ctk.CTkButton(
            img_row, text="📂", width=50, height=35,
            fg_color="#3d3d3d", hover_color="#4d4d4d",
            command=self._browse_icon
        ).pack(side="left", padx=(5, 0))
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20, fill="x", padx=20)
        
        ctk.CTkButton(
            btn_frame, text="Abbrechen", width=140,
            fg_color="#3d3d3d", hover_color="#4d4d4d",
            command=self.destroy
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame, text="Hinzufügen", width=140,
            fg_color="#0078d4", hover_color="#1084d8",
            command=self._add
        ).pack(side="right", padx=5)
    
    def _update_ui(self):
        if self.type_var.get() == "url":
            self.path_label.configure(text="URL:")
            self.path_entry.configure(placeholder_text="https://www.example.com")
            self.browse_btn.configure(state="disabled")
            self.emoji_entry.delete(0, "end")
            self.emoji_entry.insert(0, "🌐")
        else:
            self.path_label.configure(text="Pfad:")
            self.path_entry.configure(placeholder_text="C:\\Program Files\\...")
            self.browse_btn.configure(state="normal")
            self.emoji_entry.delete(0, "end")
            self.emoji_entry.insert(0, "📁")
    
    def _browse(self):
        path = filedialog.askopenfilename()
        if not path:
            path = filedialog.askdirectory()
        if path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)
            if not self.name_entry.get():
                self.name_entry.insert(0, Path(path).stem)

    def _browse_icon(self):
        file_types = [
            ("Bilder", "*.png;*.jpg;*.jpeg;*.ico;*.gif"),
            ("Alle Dateien", "*.*")
        ]
        path = filedialog.askopenfilename(filetypes=file_types)
        if path:
            self.image_entry.delete(0, "end")
            self.image_entry.insert(0, path)
    
    def _add(self):
        name = self.name_entry.get().strip()
        path = self.path_entry.get().strip()
        emoji_val = self.emoji_entry.get().strip() or "📁"
        image_val = self.image_entry.get().strip()
        
        shortcut_type = self.type_var.get()
        
        if not name or not path:
            messagebox.showwarning("Fehler", "Name und Pfad/URL sind erforderlich!")
            return
            
        import os
        image_path = None
        
        if image_val and os.path.exists(image_val):
            image_path = image_val

        self.add_callback(name, path, shortcut_type, emoji_val, image_path=image_path)
        self.destroy()


class AddCategoryDialog(ctk.CTkToplevel):
    """Dialog zum Hinzufügen einer neuen Kategorie"""
    
    def __init__(self, master, add_callback):
        super().__init__(master)
        self.add_callback = add_callback
        
        self.title("Neue Kategorie")
        self.geometry("350x150")
        self.configure(fg_color="#1a1a1a")
        self.resizable(False, False)
        
        self.transient(master)
        self.wait_visibility()
        self.grab_set()
        
        ctk.CTkLabel(self, text="Kategorie-Name:", font=("Segoe UI", 12)).pack(pady=(20, 5), padx=20, anchor="w")
        self.name_entry = ctk.CTkEntry(self, width=310, height=35, placeholder_text="z.B. Spiele")
        self.name_entry.pack(padx=20)
        self.name_entry.bind("<Return>", lambda e: self._add())
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20, fill="x", padx=20)
        
        ctk.CTkButton(
            btn_frame, text="Abbrechen", width=140,
            fg_color="#3d3d3d", hover_color="#4d4d4d",
            command=self.destroy
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame, text="Erstellen", width=140,
            fg_color="#0078d4", hover_color="#1084d8",
            command=self._add
        ).pack(side="right", padx=5)
    
    def _add(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Fehler", "Bitte einen Namen eingeben!")
            return
        self.add_callback(name)
        self.destroy()


class SettingsDialog(ctk.CTkToplevel):
    """Dialog für Einstellungen"""
    
    def __init__(self, master, current_settings, save_callback):
        super().__init__(master)
        self.settings = current_settings
        self.save_callback = save_callback
        
        self.title("Einstellungen")
        self.geometry("400x580") # Increased height
        self.configure(fg_color="#1a1a1a")
        self.resizable(False, False)
        
        self.transient(master)
        self.wait_visibility()
        self.grab_set()
        
        # Grid Einstellungen
        ctk.CTkLabel(self, text="Raster Einstellungen", font=("Segoe UI", 14, "bold")).pack(pady=(20, 10), padx=20, anchor="w")
        
        # Spaltenanzahl
        self.columns_var = ctk.IntVar(value=self.settings.get("columns", 5))
        
        col_frame = ctk.CTkFrame(self, fg_color="transparent")
        col_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(col_frame, text="Spalten:", font=("Segoe UI", 12)).pack(side="left")
        self.col_label = ctk.CTkLabel(col_frame, text=str(self.columns_var.get()), font=("Segoe UI", 12, "bold"))
        self.col_label.pack(side="right")
        
        self.col_slider = ctk.CTkSlider(
            self,
            from_=2,
            to=10,
            number_of_steps=8,
            variable=self.columns_var,
            command=self._update_col_label
        )
        self.col_slider.pack(fill="x", padx=20, pady=(0, 15))
        
        # Freie Platzierung
        ctk.CTkLabel(self, text="Modus", font=("Segoe UI", 14, "bold")).pack(pady=(10, 10), padx=20, anchor="w")
        
        self.free_placement_var = ctk.BooleanVar(value=self.settings.get("free_placement", False))
        
        self.fp_switch = ctk.CTkSwitch(
            self,
            text="Freie Platzierung (kein Raster)",
            variable=self.free_placement_var,
            font=("Segoe UI", 12)
        )
        self.fp_switch.pack(padx=20, pady=5, anchor="w")
        
        ctk.CTkLabel(
            self,
            text="Wenn aktiviert, können Icons frei verschoben werden.\n(Experimentell)",
            font=("Segoe UI", 10),
            text_color="gray"
        ).pack(padx=45, pady=0, anchor="w")

        # Themes (Akzentfarbe)
        ctk.CTkLabel(self, text="Design", font=("Segoe UI", 14, "bold")).pack(pady=(15, 10), padx=20, anchor="w")
        
        self.accent_var = ctk.StringVar(value=self.settings.get("accent_color", "Blue"))
        
        self.theme_combo = ctk.CTkComboBox(
            self,
            values=ThemeManager.get_theme_names(),
            variable=self.accent_var,
            width=200,
            state="readonly"
        )
        self.theme_combo.pack(padx=20, pady=5, anchor="w")
        
        ctk.CTkLabel(
            self,
            text="Hinweis: Neustart erforderlich für vollständige Änderung.",
            font=("Segoe UI", 10),
            text_color="gray"
        ).pack(padx=20, pady=0, anchor="w")

        # Always On Top für QuickLaunch
        ctk.CTkLabel(self, text="Fenster Verhalten", font=("Segoe UI", 14, "bold")).pack(pady=(15, 10), padx=20, anchor="w")
        
        self.always_on_top_var = ctk.BooleanVar(value=self.settings.get("quicklaunch_always_on_top", False))
        
        self.aot_switch = ctk.CTkSwitch(
            self,
            text="Immer im Vordergrund",
            variable=self.always_on_top_var,
            font=("Segoe UI", 12)
        )
        self.aot_switch.pack(padx=20, pady=5, anchor="w")
        
        # Autostart
        self.autostart_var = ctk.BooleanVar(value=check_autostart())
        
        self.as_switch = ctk.CTkSwitch(
            self,
            text="Mit Windows starten",
            variable=self.autostart_var,
            font=("Segoe UI", 12)
        )
        self.as_switch.pack(padx=20, pady=10, anchor="w")
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=20, fill="x", padx=20)
        
        ctk.CTkButton(
            btn_frame, text="Schließen", width=140,
            fg_color="#3d3d3d", hover_color="#4d4d4d",
            command=self.destroy
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame, text="Speichern", width=140,
            fg_color=ThemeManager.get_color("primary"), 
            hover_color=ThemeManager.get_color("hover"),
            command=self._save
        ).pack(side="right", padx=5)
        
    def _update_col_label(self, value):
        self.col_label.configure(text=str(int(value)))
        
    def _save(self):
        self.settings["columns"] = int(self.columns_var.get())
        self.settings["free_placement"] = self.free_placement_var.get()
        self.settings["quicklaunch_always_on_top"] = self.always_on_top_var.get()
        self.settings["accent_color"] = self.accent_var.get()
        
        # Apply Autostart immediately
        set_autostart(self.autostart_var.get())
        
        self.save_callback()
        self.destroy()
