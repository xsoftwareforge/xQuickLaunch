import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
from tkinterdnd2 import TkinterDnD
import pystray
from PIL import Image, ImageDraw
import threading
import sys

from config import load_config, save_config, setup_theme, ICONS_DIR
from ui.tab import CategoryTab
# ... (imports unchanged)

class QuickLaunchApp(ctk.CTk, TkinterDnD.DnDWrapper):
    """Hauptanwendung"""
    
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        
        setup_theme()

        self.title("QuickLaunch - Schnellstart")
        self.geometry("700x500")
        self.minsize(500, 400)
        self.configure(fg_color="#1a1a1a")
        
        # Daten laden
        self.config_data = load_config()
        self.category_tabs = {}
        
        # Always on Top für Hauptfenster
        self.attributes("-topmost", self.config_data["settings"].get("quicklaunch_always_on_top", False))
        
        # Protokoll für Schließen-Button ändern
        self.protocol("WM_DELETE_WINDOW", self._on_close_window)
        
        self.tray_icon = None
        self._setup_tray_icon()
        
        self._create_ui()
        
        # Topbar initialisieren
        from ui.topbar import Topbar
        self.topbar = Topbar(self)
    
    # ... (Create UI method unchanged) ...

    # --- System Tray Logic ---
    def _create_tray_image(self):
        # Create a simple icon if none exists
        image = Image.new('RGB', (64, 64), color = (0, 0, 0))
        d = ImageDraw.Draw(image)
        d.rectangle((16, 16, 48, 48), fill=(0, 229, 255)) # Cyan box
        d.text((22, 20), "QL", fill=(255, 255, 255))
        return image

    def _setup_tray_icon(self):
        def _run_tray():
            image = self._create_tray_image()
            menu = pystray.Menu(
                pystray.MenuItem("Anzeigen", self._restore_from_tray, default=True),
                pystray.MenuItem("Beenden", self.quit_app)
            )
            self.tray_icon = pystray.Icon("QuickLaunch", image, "QuickLaunch Bar", menu)
            self.tray_icon.run()

        # Run tray in separate thread to not block tkinter
        self.tray_thread = threading.Thread(target=_run_tray, daemon=True)
        self.tray_thread.start()

    def _restore_from_tray(self, icon=None, item=None):
        """Restores the Topbar and potentially the main window"""
        self.after(0, self.topbar.deiconify)
        # Main window stays hidden unless explicitly toggled, or we can show it too
        # self.after(0, self.deiconify) 

    def minimize_to_tray(self):
        """Hides both windows"""
        self.withdraw()
        self.topbar.withdraw()
        
    def quit_app(self, icon=None, item=None):
        """Beendet die gesamte Anwendung inkl. Tray"""
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()
        sys.exit(0)

    # --- Window Management ---
    
    def _on_close_window(self):
        """Wird beim Klick auf X des Hauptfensters aufgerufen. Versteckt das Fenster nur."""
        self.withdraw()
        if hasattr(self, 'topbar'):
            self.topbar.arrow_btn.configure(text="▼")
    # ... rest unchanged
    
    def _create_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="#0f0f0f", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header,
            text="⚡ QuickLaunch",
            font=("Segoe UI", 20, "bold"),
            text_color="#ffffff"
        )
        title_label.pack(side="left", padx=20, pady=15)
        
        # Header Buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)
        
        # Dateien hinzufügen Button
        self.add_files_btn = ctk.CTkButton(
            btn_frame,
            text="📂 Dateien",
            width=90,
            height=32,
            font=("Segoe UI", 12),
            fg_color="#2d7d32",
            hover_color="#388e3c",
            command=self._add_files
        )
        self.add_files_btn.pack(side="left", padx=5)
        
        self.settings_btn = ctk.CTkButton(
            btn_frame,
            text="⚙️",
            width=40,
            height=32,
            font=("Segoe UI", 16),
            fg_color="#3d3d3d",
            hover_color="#4d4d4d",
            command=self._show_settings_dialog
        )
        self.settings_btn.pack(side="right", padx=5)
        
        self.add_btn = ctk.CTkButton(
            btn_frame,
            text="+ Hinzufügen",
            width=110,
            height=32,
            font=("Segoe UI", 12),
            fg_color="#0078d4",
            hover_color="#1084d8",
            command=self._show_add_dialog
        )
        self.add_btn.pack(side="left", padx=5)
        
        self.add_cat_btn = ctk.CTkButton(
            btn_frame,
            text="+ Kategorie",
            width=100,
            height=32,
            font=("Segoe UI", 12),
            fg_color="#3d3d3d",
            hover_color="#4d4d4d",
            command=self._show_add_category_dialog
        )
        self.add_cat_btn.pack(side="left", padx=5)
        
        # Tabview für Kategorien
        self.tabview = ctk.CTkTabview(
            self,
            fg_color="#1a1a1a",
            segmented_button_fg_color="#2b2b2b",
            segmented_button_selected_color="#0078d4",
            segmented_button_selected_hover_color="#1084d8",
            segmented_button_unselected_color="#2b2b2b",
            segmented_button_unselected_hover_color="#3d3d3d"
        )
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(10, 15))
        
        self._create_tabs()
        
        # Status Bar
        status_bar = ctk.CTkFrame(self, fg_color="#0f0f0f", height=30)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            status_bar,
            text="📂 Dateien Button zum Hinzufügen | Rechtsklick für Optionen",
            font=("Segoe UI", 10),
            text_color="#666666"
        )
        self.status_label.pack(side="left", padx=15, pady=5)
    
    def _create_tabs(self):
        for cat in self.config_data["categories"]:
            tab = self.tabview.add(cat["name"])
            category_tab = CategoryTab(tab, cat, self.config_data.get("settings", {}), self._save_config)
            category_tab.pack(fill="both", expand=True)
            self.category_tabs[cat["name"]] = category_tab
    
    def _save_config(self):
        """Wrapper um config.save_config"""
        save_config(self.config_data)
    
    def _add_files(self):
        """Öffnet Datei-Dialog zum Hinzufügen mehrerer Dateien"""
        files = filedialog.askopenfilenames(
            title="Dateien auswählen",
            filetypes=[
                ("Alle Dateien", "*.*"),
                ("Programme", "*.exe;*.msi"),
                ("Verknüpfungen", "*.lnk"),
                ("Dokumente", "*.pdf;*.doc;*.docx;*.txt"),
            ]
        )
        
        current_tab = self.tabview.get()
        if files and current_tab in self.category_tabs:
            for file_path in files:
                self.category_tabs[current_tab].add_shortcut_from_path(file_path)
    
    def _show_add_dialog(self):
        AddDialog(self, self._add_shortcut)
    
    def _show_settings_dialog(self):
        if "settings" not in self.config_data:
             self.config_data["settings"] = {"columns": 5, "free_placement": False}
        SettingsDialog(self, self.config_data["settings"], self._on_settings_saved)

    def _on_settings_saved(self):
        self._save_config()
        # Settings anwenden
        self.attributes("-topmost", self.config_data["settings"].get("quicklaunch_always_on_top", False))
        
        # Refresh all tabs to apply new grid/placement settings
        for tab_name, tab in self.category_tabs.items():
            tab.update_settings(self.config_data["settings"])

    def _show_add_category_dialog(self):
        AddCategoryDialog(self, self._add_category)
    
    def _add_shortcut(self, name, path, shortcut_type, icon):
        current_tab = self.tabview.get()
        
        image_path = None
        if shortcut_type == "file":
            try:
                image_path = get_file_icon_path(path, str(ICONS_DIR))
            except Exception:
                pass

        shortcut = {
            "name": name,
            "path": path,
            "type": shortcut_type,
            "icon": icon,
            "image_path": image_path
        }
        
        # Finde die aktuelle Kategorie
        for cat in self.config_data["categories"]:
            if cat["name"] == current_tab:
                cat["shortcuts"].append(shortcut)
                break
        
        self._save_config()
        self.category_tabs[current_tab]._render_tiles()
    
    def _add_category(self, name):
        # Prüfen ob Kategorie existiert
        for cat in self.config_data["categories"]:
            if cat["name"].lower() == name.lower():
                messagebox.showwarning("Fehler", "Diese Kategorie existiert bereits!")
                return
        
        new_cat = {"name": name, "shortcuts": []}
        self.config_data["categories"].append(new_cat)
        self._save_config()
        
        # Tab hinzufügen
        tab = self.tabview.add(name)
        category_tab = CategoryTab(tab, new_cat, self.config_data.get("settings", {}), self._save_config)
        category_tab.pack(fill="both", expand=True)
        self.category_tabs[name] = category_tab
        
        # Zum neuen Tab wechseln
        self.tabview.set(name)
        
    # --- Neue Methoden für Topbar & Window Management ---
    
    def _on_close_window(self):
        """Wird beim Klick auf X aufgerufen. Versteckt das Fenster nur."""
        self.withdraw()
        if hasattr(self, 'topbar'):
            self.topbar.arrow_btn.configure(text="▼")
            
    def toggle_quicklaunch_window(self) -> bool:
        """Zeigt oder Versteckt das Hauptfenster. Gibt Status zurück (True=Sichtbar)."""
        if self.state() == "withdrawn":
            self.deiconify()
            return True
        else:
            self.withdraw()
            return False
            
    def update_setting(self, key, value):
        """Aktualisiert eine Einstellung und speichert."""
        self.config_data["settings"][key] = value
        self._save_config()
        
    def quit_app(self):
        """Beendet die gesamte Anwendung."""
        self.destroy()

def main():
    app = QuickLaunchApp()
    app.mainloop()

if __name__ == "__main__":
    main()
