import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
from tkinterdnd2 import TkinterDnD
try:
    import pystray
except Exception:
    pystray = None
from PIL import Image, ImageDraw
import threading
import sys


from config import load_config, save_config, setup_theme, ICONS_DIR
from ui.tab import CategoryTab
from ui.dialogs import AddDialog, AddCategoryDialog, SettingsDialog
from utils.theme_manager import ThemeManager
from utils.icon_utils import get_file_icon_path

class QuickLaunchApp(ctk.CTk, TkinterDnD.DnDWrapper):
    """Hauptanwendung"""
    
    def __init__(self):
        super().__init__()
        
        # Support for FreeBSD/Linux Manual TkDND Path
        import os
        tkdnd_path = os.environ.get('TKDND_LIBRARY')
        if tkdnd_path:
            try:
                # Add the library path to Tcl's auto_path so 'package require tkdnd' can find it
                self.tk.eval(f'lappend auto_path {{{tkdnd_path}}}')
                print(f"Injected tkdnd path: {tkdnd_path}")
            except Exception as e:
                print(f"Warning: Failed to inject tkdnd path: {e}")

        try:
            # FreeBSD Fix: Override the internal _require function to manually load tkdnd
            # This avoids the strict platform check in tkinterdnd2
            import sys
            import os
            if sys.platform.startswith('freebsd'):
                def _require_freebsd(tkroot):
                    # Try env var first, then standard ports location
                    paths = [
                        os.environ.get('TKDND_LIBRARY'),
                        '/usr/local/lib/tkdnd2.8',
                        '/usr/local/lib/tkdnd2.9'
                    ]
                    found = False
                    for path in paths:
                        if path and os.path.exists(path):
                            print(f"FreeBSD: injecting auto_path {path}")
                            tkroot.tk.call('lappend', 'auto_path', path)
                            found = True
                            break
                    
                    if not found:
                        print("Warning: Could not find tkdnd library path. Set TKDND_LIBRARY env var.")
                        
                    return tkroot.tk.call('package', 'require', 'tkdnd')

                # Critical: We must patch the _require function on the class/module
                # Depending on how it's imported, it might be an instance method or static
                # In tkinterdnd2 source, _require is a static function that takes the widget
                TkinterDnD._require = _require_freebsd

            self.TkdndVersion = TkinterDnD._require(self)
            self.dnd_enabled = True

        except (RuntimeError, ImportError, Exception) as e:
            print(f"Drag & Drop not supported: {e}")
            self.dnd_enabled = False
        
        setup_theme()
        
        # Daten laden
        self.config_data = load_config()
        
        # Theme initialisieren
        current_theme = self.config_data.get("settings", {}).get("accent_color", "Blue")
        ThemeManager.set_theme(current_theme)

        self.title("QuickLaunch - Schnellstart")
        self.geometry("700x500")
        self.minsize(600, 400)
        self.configure(fg_color="#1a1a1a")
        
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
        
        # Use primary color for tray icon
        primary_color = ThemeManager.get_color("primary")
        # Convert hex to RGB for PIL
        h = primary_color.lstrip('#')
        rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        
        d.rectangle((16, 16, 48, 48), fill=rgb) 
        d.text((22, 20), "QL", fill=(255, 255, 255))
        return image

    def _setup_tray_icon(self):
        if pystray is None:
            return

        def _run_tray():
            image = self._create_tray_image()
            menu = pystray.Menu(
                pystray.MenuItem("Anzeigen", self._restore_from_tray, default=True),
                pystray.MenuItem("Beenden", self.quit_app)
            )
            try:
                self.tray_icon = pystray.Icon("QuickLaunch", image, "QuickLaunch Bar", menu)
                self.tray_icon.run()
            except Exception as e:
                print(f"Failed to initialize system tray icon: {e}")
                self.tray_icon = None

        # Run tray in separate thread to not block tkinter
        self.tray_thread = threading.Thread(target=_run_tray, daemon=True)
        self.tray_thread.start()

    def _restore_from_tray(self, icon=None, item=None):
        """Restores the Topbar and potentially the main window"""
        self.after(0, self.topbar.deiconify)
        # Main window stays hidden unless explicitly toggled, or we can show it too
        # self.after(0, self.deiconify) 

        self.withdraw()
        if self.tray_icon:
            self.topbar.withdraw()
            # If no tray icon, we should probably not hide the topbar completely or provide a way back, 
            # but for minimize logic, hiding window is standard. 
            # If no tray, maybe we just minimize to taskbar? 
            # But topbar is overrideredirect, so it doesn't have taskbar entry usually.
        else:
            # removing from screen without tray to bring it back is dangerous.
            # treating minimize as just hiding main window but keeping topbar if no tray?
            self.topbar.withdraw()
            # If we don't have tray, we rely on topbar being visible? 
            # Wait, if topbar is hidden, how do we get it back?
            # On Windows, we re-show from tray.
            # On Linux without tray, we might be stuck.
            # Let's just withdraw for now, user can kill app if stuck. 
            # Better: if no tray, maybe don't allow full minimize or just iconify?
            pass
        
    def quit_app(self, icon=None, item=None):
        """Beendet die gesamte Anwendung inkl. Tray"""
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.destroy()
        sys.exit(0)

    # --- Window Management ---
    
    def _on_close_window(self):
        """Wird beim Klick auf X des Hauptfensters aufgerufen. Versteckt das Fenster nur."""
        self.withdraw()
        if hasattr(self, 'topbar'):
            self.topbar.arrow_btn.configure(text="▼")
    
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
        
        # Search Bar
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self._on_search)
        
        self.search_entry = ctk.CTkEntry(
            header,
            width=200,
            height=32,
            placeholder_text="Suche...",
            textvariable=self.search_var,
            border_width=1,
            corner_radius=15,
            fg_color="#1a1a1a",
            border_color="#3d3d3d",
            text_color="white"
        )
        self.search_entry.pack(side="left", padx=20)

        # Header Buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)
        
        theme_primary = ThemeManager.get_color("primary")
        theme_hover = ThemeManager.get_color("hover")
        
        # Dateien hinzufügen Button
        self.add_files_btn = ctk.CTkButton(
            btn_frame,
            text="📂 Dateien",
            width=90,
            height=32,
            font=("Segoe UI", 12),
            fg_color=theme_primary, 
            hover_color=theme_hover,
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
            fg_color=theme_primary,
            hover_color=theme_hover,
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
    
    def _add_shortcut(self, name, path, shortcut_type, icon, image_path=None):
        current_tab = self.tabview.get()
        
        if not image_path and shortcut_type == "file":
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

    def _bind_tab_context_menu(self, tab_name):
        try:
            # Access the internal button for the tab
            # CTkTabview -> _segmented_button -> _buttons_dict (name -> CTkButton)
            btn = self.tabview._segmented_button._buttons_dict.get(tab_name)
            if btn:
                # Bind Right Click
                btn.bind("<Button-3>", lambda event, name=tab_name: self._show_tab_context_menu(event, name))
        except Exception as e:
            print(f"Failed to bind context menu to tab {tab_name}: {e}")

    def _show_tab_context_menu(self, event, tab_name):
        import tkinter as tk # Ensure tk is available
        menu = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white",
                       activebackground="#0078d4", activeforeground="white")
        
        # Umbenennen
        menu.add_command(label="✏️ Umbenennen", command=lambda: self._rename_category(tab_name))
        
        # Löschen (nur wenn mehr als 1 Tab)
        if len(self.category_tabs) > 1:
             menu.add_command(label="🗑️ Löschen", command=lambda: self._delete_category(tab_name))
             
        menu.tk_popup(event.x_root, event.y_root)
        
    def _rename_category(self, old_name):
        dialog = ctk.CTkInputDialog(text=f"Neuer Name für '{old_name}':", title="Kategorie umbenennen")
        # Center dialog roughly
        dialog.geometry(f"+{self.winfo_x()+200}+{self.winfo_y()+200}")
        new_name = dialog.get_input()
        
        if not new_name or new_name == old_name:
            return
            
        # Check duplicate
        for cat in self.config_data["categories"]:
            if cat["name"].lower() == new_name.lower():
                messagebox.showwarning("Fehler", "Dieser Name existiert bereits!")
                return
                
        # 1. Update Data
        category_data = None
        for cat in self.config_data["categories"]:
            if cat["name"] == old_name:
                cat["name"] = new_name
                category_data = cat
                break
        
        if not category_data:
            return

        # 2. Update UI (Re-create Tab)
        # We need to preserve the tab order? 
        # CTkTabview doesn't support renaming easily. We have to remove and add.
        # But removing an item from config list and re-appending changes order?
        # No, we updated the name in-place in the list, so order in `config_data` is preserved.
        # But `tabview` adds tabs at the end.
        
        # Full refresh strategy:
        # Rebuild all tabs to keep order? Or just Accept it moves to end?
        # User probably prefers order. Let's redraw all tabs.
        
        # Save current tab index/selection if possible?
        # Actually, let's just do a full redraw of tabs to be safe and simple
        
        current_selection = self.tabview.get()
        if current_selection == old_name:
            current_selection = new_name
            
        # Clear tabs
        # To avoid issues, let's remove them one by one or reconstruct the view?
        # CTkTabview has no `clear()`. We have to `delete(name)`.
        
        # Note: Deleting tabs might trigger events or be slow.
        # Let's try to just update the one tab if we didn't care about order, but we explicitly want renaming.
        # If we re-render everything, it is cleanest.
        
        # Temporarily suppress saves during mass update if needed? No, just save once at end.
        
        # Delete all tabs from UI
        # Removing from keys() while iterating is unsafe, make list
        for name in list(self.category_tabs.keys()):
            self.tabview.delete(name)
            
        self.category_tabs.clear()
        
        # Re-create all
        for cat in self.config_data["categories"]:
            self._create_single_tab(cat)
            
        if current_selection:
            try:
                self.tabview.set(current_selection)
            except:
                pass
                
        self._save_config()

    def _delete_category(self, tab_name):
        if messagebox.askyesno("Löschen", f"Kategorie '{tab_name}' und alle Verknüpfungen darin wirklich löschen?"):
             # Update Data
            self.config_data["categories"] = [c for c in self.config_data["categories"] if c["name"] != tab_name]
            
            # Update UI
            self.tabview.delete(tab_name)
            if tab_name in self.category_tabs:
                del self.category_tabs[tab_name]
                
            self._save_config()

    def _create_tabs(self):
        for cat in self.config_data["categories"]:
            self._create_single_tab(cat)

    def _create_single_tab(self, cat):
        name = cat["name"]
        tab = self.tabview.add(name)
        category_tab = CategoryTab(tab, cat, self.config_data.get("settings", {}), self._save_config)
        category_tab.pack(fill="both", expand=True)
        self.category_tabs[name] = category_tab
        
        # Bind Context Menu
        self._bind_tab_context_menu(name)

    def _on_search(self, *args):
        query = self.search_var.get().lower()
        
        # Determine the currently active tab
        current_tab_name = self.tabview.get()
        if current_tab_name in self.category_tabs:
            self.category_tabs[current_tab_name].set_filter(query)

def main():
    app = QuickLaunchApp()
    app.mainloop()

if __name__ == "__main__":
    main()
