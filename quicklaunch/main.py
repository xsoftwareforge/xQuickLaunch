#!/usr/bin/env python3
"""
QuickLaunch - Schnellstart-Leiste für Windows/Linux
Eine moderne Desktop-App zum Verwalten von Verknüpfungen
"""

import customtkinter as ctk
import json
import os
import subprocess
import sys
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk

# Pfad zur Konfigurationsdatei
CONFIG_FILE = Path(__file__).parent / "config.json"

# CustomTkinter Einstellungen
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ShortcutTile(ctk.CTkFrame):
    """Einzelne Kachel für eine Verknüpfung"""
    
    def __init__(self, master, shortcut_data, on_delete, on_edit, **kwargs):
        super().__init__(master, **kwargs)
        self.shortcut_data = shortcut_data
        self.on_delete = on_delete
        self.on_edit = on_edit
        
        self.configure(
            fg_color="#2b2b2b",
            corner_radius=12,
            border_width=1,
            border_color="#3d3d3d"
        )
        
        # Hover-Effekte
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Button-3>", self._show_context_menu)
        
        # Icon
        icon_text = shortcut_data.get("icon", "📁")
        self.icon_label = ctk.CTkLabel(
            self,
            text=icon_text,
            font=("Segoe UI Emoji", 32),
            text_color="#ffffff"
        )
        self.icon_label.pack(pady=(15, 5))
        self.icon_label.bind("<Button-1>", self._on_click)
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
        self.name_label.bind("<Button-1>", self._on_click)
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
        self.configure(fg_color="#3d3d3d", border_color="#0078d4")
    
    def _on_leave(self, event):
        self.configure(fg_color="#2b2b2b", border_color="#3d3d3d")
    
    def _on_click(self, event):
        path = self.shortcut_data.get("path", "")
        shortcut_type = self.shortcut_data.get("type", "file")
        
        try:
            if shortcut_type == "url":
                webbrowser.open(path)
            else:
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin":
                    subprocess.run(["open", path])
                else:
                    subprocess.run(["xdg-open", path])
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
        except:
            self.clipboard_clear()
            self.clipboard_append(self.shortcut_data.get("path", ""))


class CategoryTab(ctk.CTkFrame):
    """Tab-Inhalt für eine Kategorie"""
    
    def __init__(self, master, category_data, save_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.category_data = category_data
        self.save_callback = save_callback
        self.tiles = []
        
        self.configure(fg_color="transparent")
        
        # Scrollbarer Bereich
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color="#3d3d3d",
            scrollbar_button_hover_color="#4d4d4d"
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Grid-Container
        self.grid_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True)
        
        self._render_tiles()
    
    def _render_tiles(self):
        # Alte Tiles entfernen
        for tile in self.tiles:
            tile.destroy()
        self.tiles.clear()
        
        # Alle Widgets im Grid entfernen
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        
        shortcuts = self.category_data.get("shortcuts", [])
        columns = 4
        
        for i, shortcut in enumerate(shortcuts):
            row = i // columns
            col = i % columns
            
            tile = ShortcutTile(
                self.grid_frame,
                shortcut,
                on_delete=self._delete_shortcut,
                on_edit=self._edit_shortcut,
                width=100,
                height=100
            )
            tile.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            self.tiles.append(tile)
        
        # Leere Nachricht wenn keine Verknüpfungen
        if not shortcuts:
            empty_label = ctk.CTkLabel(
                self.grid_frame,
                text="Klicke auf '+ Hinzufügen' oder '📂 Dateien'\num Verknüpfungen hinzuzufügen",
                font=("Segoe UI", 14),
                text_color="#666666"
            )
            empty_label.grid(row=0, column=0, columnspan=4, pady=50)
    
    def add_shortcut_from_path(self, file_path):
        """Fügt eine Verknüpfung basierend auf einem Dateipfad hinzu"""
        path = Path(file_path)
        name = path.stem if path.is_file() else path.name
        
        # Icon basierend auf Dateityp
        suffix = path.suffix.lower()
        if suffix in ['.exe', '.msi']:
            icon = "⚙️"
        elif suffix in ['.lnk']:
            icon = "🔗"
        elif path.is_dir():
            icon = "📁"
        elif suffix in ['.txt', '.doc', '.docx', '.pdf']:
            icon = "📄"
        elif suffix in ['.jpg', '.png', '.gif', '.bmp', '.jpeg']:
            icon = "🖼️"
        elif suffix in ['.mp3', '.wav', '.flac', '.ogg']:
            icon = "🎵"
        elif suffix in ['.mp4', '.avi', '.mkv', '.mov']:
            icon = "🎬"
        elif suffix in ['.zip', '.rar', '.7z']:
            icon = "📦"
        elif suffix in ['.py', '.js', '.html', '.css']:
            icon = "💻"
        else:
            icon = "📄"
        
        shortcut = {
            "name": name,
            "path": str(path),
            "type": "file",
            "icon": icon
        }
        
        self.category_data["shortcuts"].append(shortcut)
        self.save_callback()
        self._render_tiles()
    
    def add_url(self, name, url, icon="🌐"):
        """Fügt eine URL-Verknüpfung hinzu"""
        shortcut = {
            "name": name,
            "path": url,
            "type": "url",
            "icon": icon
        }
        self.category_data["shortcuts"].append(shortcut)
        self.save_callback()
        self._render_tiles()
    
    def _delete_shortcut(self, shortcut_data):
        if messagebox.askyesno("Löschen", f"'{shortcut_data['name']}' wirklich löschen?"):
            self.category_data["shortcuts"].remove(shortcut_data)
            self.save_callback()
            self._render_tiles()
    
    def _edit_shortcut(self, shortcut_data):
        EditDialog(self, shortcut_data, self.save_callback, self._render_tiles)


class EditDialog(ctk.CTkToplevel):
    """Dialog zum Bearbeiten einer Verknüpfung"""
    
    def __init__(self, master, shortcut_data, save_callback, refresh_callback):
        super().__init__(master)
        self.shortcut_data = shortcut_data
        self.save_callback = save_callback
        self.refresh_callback = refresh_callback
        
        self.title("Verknüpfung bearbeiten")
        self.geometry("400x300")
        self.configure(fg_color="#1a1a1a")
        self.resizable(False, False)
        
        # Zentrieren
        self.transient(master)
        self.grab_set()
        
        # Name
        ctk.CTkLabel(self, text="Name:", font=("Segoe UI", 12)).pack(pady=(20, 5), padx=20, anchor="w")
        self.name_entry = ctk.CTkEntry(self, width=360, height=35)
        self.name_entry.insert(0, shortcut_data.get("name", ""))
        self.name_entry.pack(padx=20)
        
        # Pfad/URL
        ctk.CTkLabel(self, text="Pfad/URL:", font=("Segoe UI", 12)).pack(pady=(15, 5), padx=20, anchor="w")
        self.path_entry = ctk.CTkEntry(self, width=360, height=35)
        self.path_entry.insert(0, shortcut_data.get("path", ""))
        self.path_entry.pack(padx=20)
        
        # Icon
        ctk.CTkLabel(self, text="Icon (Emoji):", font=("Segoe UI", 12)).pack(pady=(15, 5), padx=20, anchor="w")
        self.icon_entry = ctk.CTkEntry(self, width=100, height=35)
        self.icon_entry.insert(0, shortcut_data.get("icon", "📁"))
        self.icon_entry.pack(padx=20, anchor="w")
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20, fill="x", padx=20)
        
        ctk.CTkButton(
            btn_frame, text="Abbrechen", width=100,
            fg_color="#3d3d3d", hover_color="#4d4d4d",
            command=self.destroy
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame, text="Speichern", width=100,
            fg_color="#0078d4", hover_color="#1084d8",
            command=self._save
        ).pack(side="right", padx=5)
    
    def _save(self):
        self.shortcut_data["name"] = self.name_entry.get()
        self.shortcut_data["path"] = self.path_entry.get()
        self.shortcut_data["icon"] = self.icon_entry.get() or "📁"
        
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
        self.geometry("420x380")
        self.configure(fg_color="#1a1a1a")
        self.resizable(False, False)
        
        self.transient(master)
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
            path_frame, text="📂", width=40, height=35,
            fg_color="#3d3d3d", hover_color="#4d4d4d",
            command=self._browse
        )
        self.browse_btn.pack(side="left", padx=(10, 0))
        
        # Icon
        ctk.CTkLabel(self, text="Icon (Emoji):", font=("Segoe UI", 12)).pack(pady=(15, 5), padx=20, anchor="w")
        self.icon_entry = ctk.CTkEntry(self, width=100, height=35)
        self.icon_entry.insert(0, "📁")
        self.icon_entry.pack(padx=20, anchor="w")
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20, fill="x", padx=20)
        
        ctk.CTkButton(
            btn_frame, text="Abbrechen", width=100,
            fg_color="#3d3d3d", hover_color="#4d4d4d",
            command=self.destroy
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame, text="Hinzufügen", width=100,
            fg_color="#0078d4", hover_color="#1084d8",
            command=self._add
        ).pack(side="right", padx=5)
    
    def _update_ui(self):
        if self.type_var.get() == "url":
            self.path_label.configure(text="URL:")
            self.path_entry.configure(placeholder_text="https://www.example.com")
            self.browse_btn.configure(state="disabled")
            self.icon_entry.delete(0, "end")
            self.icon_entry.insert(0, "🌐")
        else:
            self.path_label.configure(text="Pfad:")
            self.path_entry.configure(placeholder_text="C:\\Program Files\\...")
            self.browse_btn.configure(state="normal")
            self.icon_entry.delete(0, "end")
            self.icon_entry.insert(0, "📁")
    
    def _browse(self):
        path = filedialog.askopenfilename()
        if not path:
            path = filedialog.askdirectory()
        if path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)
            if not self.name_entry.get():
                self.name_entry.insert(0, Path(path).stem)
    
    def _add(self):
        name = self.name_entry.get().strip()
        path = self.path_entry.get().strip()
        icon = self.icon_entry.get().strip() or "📁"
        shortcut_type = self.type_var.get()
        
        if not name or not path:
            messagebox.showwarning("Fehler", "Name und Pfad/URL sind erforderlich!")
            return
        
        self.add_callback(name, path, shortcut_type, icon)
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
        self.grab_set()
        
        ctk.CTkLabel(self, text="Kategorie-Name:", font=("Segoe UI", 12)).pack(pady=(20, 5), padx=20, anchor="w")
        self.name_entry = ctk.CTkEntry(self, width=310, height=35, placeholder_text="z.B. Spiele")
        self.name_entry.pack(padx=20)
        self.name_entry.bind("<Return>", lambda e: self._add())
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20, fill="x", padx=20)
        
        ctk.CTkButton(
            btn_frame, text="Abbrechen", width=100,
            fg_color="#3d3d3d", hover_color="#4d4d4d",
            command=self.destroy
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame, text="Erstellen", width=100,
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


class QuickLaunchApp(ctk.CTk):
    """Hauptanwendung"""
    
    def __init__(self):
        super().__init__()
        
        self.title("QuickLaunch - Schnellstart")
        self.geometry("700x500")
        self.minsize(500, 400)
        self.configure(fg_color="#1a1a1a")
        
        # Daten laden
        self.config_data = self._load_config()
        self.category_tabs = {}
        
        self._create_ui()
    
    def _load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {
            "categories": [{"name": "Allgemein", "shortcuts": []}],
            "settings": {"theme": "dark", "columns": 4, "tile_size": 100}
        }
    
    def _save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config_data, f, indent=2, ensure_ascii=False)
    
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
            category_tab = CategoryTab(tab, cat, self._save_config)
            category_tab.pack(fill="both", expand=True)
            self.category_tabs[cat["name"]] = category_tab
    
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
    
    def _show_add_category_dialog(self):
        AddCategoryDialog(self, self._add_category)
    
    def _add_shortcut(self, name, path, shortcut_type, icon):
        current_tab = self.tabview.get()
        shortcut = {
            "name": name,
            "path": path,
            "type": shortcut_type,
            "icon": icon
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
        category_tab = CategoryTab(tab, new_cat, self._save_config)
        category_tab.pack(fill="both", expand=True)
        self.category_tabs[name] = category_tab
        
        # Zum neuen Tab wechseln
        self.tabview.set(name)


def main():
    app = QuickLaunchApp()
    app.mainloop()


if __name__ == "__main__":
    main()
