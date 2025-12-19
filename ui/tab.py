import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from tkinterdnd2 import DND_FILES

from ui.tile import ShortcutTile
from ui.dialogs import EditDialog
from utils.icon_utils import get_file_icon_path
from config import ICONS_DIR

class CategoryTab(ctk.CTkFrame):
    """Tab-Inhalt für eine Kategorie"""
    
    def __init__(self, master, category_data, settings, save_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.category_data = category_data
        self.settings = settings
        self.save_callback = save_callback
        self.tiles = []
        self.drag_data = {"item": None, "x": 0, "y": 0}
        
        self.configure(fg_color="transparent")
        
        # Drag & Drop
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self._on_drop)
        
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
        
        self.current_filter = ""
        self._render_tiles()
    
    def set_filter(self, query):
        self.current_filter = query.lower()
        self._render_tiles()
        
    def update_settings(self, new_settings):
        self.settings = new_settings
        self._render_tiles()

    def _render_tiles(self):
        # Alte Tiles entfernen
        for tile in self.tiles:
            tile.destroy()
        self.tiles.clear()
        
        # Alle Widgets im Grid entfernen
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        
        all_shortcuts = self.category_data.get("shortcuts", [])
        
        # Filter Logic
        if self.current_filter:
            shortcuts = [s for s in all_shortcuts if self.current_filter in s.get("name", "").lower()]
        else:
            shortcuts = all_shortcuts
            
        columns = self.settings.get("columns", 4)
        free_mode = self.settings.get("free_placement", False)
        tile_size = 116 # Approximate size (100 width + padding)
        
        updated = False
        
        if free_mode:
            self.grid_frame.configure(height=2000, width=2000)
        else:
            self.grid_frame.configure(height=0, width=0) # Auto height

        for i, shortcut in enumerate(shortcuts):
            # Versuchen Icon zu laden wenn gefehlt
            if shortcut.get("type") == "file" and not shortcut.get("image_path"):
                try:
                    icon_path = get_file_icon_path(shortcut["path"], str(ICONS_DIR))
                    if icon_path:
                        shortcut["image_path"] = icon_path
                        updated = True
                except Exception:
                    pass

            tile = ShortcutTile(
                self.grid_frame,
                shortcut,
                on_delete=self._delete_shortcut,
                on_edit=self._edit_shortcut,
                width=100,
                height=100
            )
            
            if free_mode:
                # Default Position berechnen falls nicht vorhanden
                if "x" not in shortcut or "y" not in shortcut:
                    row = i // columns
                    col = i % columns
                    shortcut["x"] = col * tile_size + 10
                    shortcut["y"] = row * tile_size + 10
                    updated = True
                
                tile.place(x=shortcut["x"], y=shortcut["y"])
                
                # Drag Bindings (nur im Free Mode)
                # Apply to tile and all children to ensure consistent drag behavior
                # and to "override" or intercept the default click behavior
                
                start_cmd = lambda e, s=shortcut, t=tile: self._start_drag(e, s, t)
                
                targets = [tile, tile.icon_label, tile.name_label, tile.type_label]
                for target in targets:
                    if target:
                        target.bind("<Button-1>", start_cmd)
                        target.bind("<B1-Motion>", self._drag)
                        target.bind("<ButtonRelease-1>", self._end_drag)

                # Warnung: tile.bind override könnte Kontextmenü (Rechtsklick) beeinträchtigen
                # ShortcutTile macht self.bind("<Button-3>", ...)
                # Grid/Place beeinflusst das nicht. Wir binden nur Left Click neu.
                
            else:
                row = i // columns
                col = i % columns
                tile.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
                
            self.tiles.append(tile)
            
        if updated:
            self.save_callback()
        
        # Leere Nachricht wenn keine Verknüpfungen
        if not shortcuts:
            empty_label = ctk.CTkLabel(
                self.grid_frame,
                text="Klicke auf '+ Hinzufügen' oder '📂 Dateien'\num Verknüpfungen hinzuzufügen",
                font=("Segoe UI", 14),
                text_color="#666666"
            )
            if free_mode:
                empty_label.place(x=50, y=50)
            else:
                empty_label.grid(row=0, column=0, columnspan=4, pady=50)
    
    def _start_drag(self, event, shortcut, tile):
        self.drag_data["item"] = tile
        self.drag_data["shortcut"] = shortcut
        self.drag_data["start_x"] = event.x_root
        self.drag_data["start_y"] = event.y_root
        # Store initial widget position to calculate offset in _drag
        self.drag_data["widget_start_x"] = tile.winfo_x()
        self.drag_data["widget_start_y"] = tile.winfo_y()
        self.drag_data["did_move"] = False
        tile.lift() # Nach oben holen

    def _drag(self, event):
        tile = self.drag_data.get("item")
        if tile:
            # Delta berechnen (Screen based to avoid jumping if mouse moves fast)
            dx = event.x_root - self.drag_data["start_x"]
            dy = event.y_root - self.drag_data["start_y"]
            
            # Check threshold for "Click vs Drag"
            if not self.drag_data["did_move"]:
                if abs(dx) > 3 or abs(dy) > 3:
                     self.drag_data["did_move"] = True

            if self.drag_data["did_move"]:
                new_x = self.drag_data["widget_start_x"] + dx
                new_y = self.drag_data["widget_start_y"] + dy
                
                # Begrenzungen (optional)
                new_x = max(0, new_x)
                new_y = max(0, new_y)
                
                tile.place(x=new_x, y=new_y)

    def _end_drag(self, event):
        tile = self.drag_data.get("item")
        shortcut = self.drag_data.get("shortcut")
        
        if tile and shortcut:
            if self.drag_data.get("did_move", False):
                # Es war ein Drag -> Speichern
                shortcut["x"] = tile.winfo_x()
                shortcut["y"] = tile.winfo_y()
                self.save_callback()
            # Wenn nicht bewegt (Klick), passiert nichts hier.
            # Der Launch wird jetzt durch Double-Click im ShortcutTile behandelt.
            
        self.drag_data["item"] = None
    
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
        
        # Extract Image Icon
        image_path = None
        try:
            image_path = get_file_icon_path(str(path), str(ICONS_DIR))
        except Exception:
            pass

        shortcut = {
            "name": name,
            "path": str(path),
            "type": "file",
            "icon": icon,
            "image_path": image_path
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
    
    def _on_drop(self, event):
        """Handler für Drag & Drop Events"""
        if event.data:
            # TkinterDnD liefert Pfade als String, getrennt durch Leerzeichen.
            # Pfade mit Leerzeichen sind in {} eingeschlossen.
            files = self.tk.splitlist(event.data)
            for file_path in files:
                self.add_shortcut_from_path(file_path)
    
    def _delete_shortcut(self, shortcut_data):
        if messagebox.askyesno("Löschen", f"'{shortcut_data['name']}' wirklich löschen?"):
            self.category_data["shortcuts"].remove(shortcut_data)
            self.save_callback()
            self._render_tiles()
    
    def _edit_shortcut(self, shortcut_data):
        EditDialog(self, shortcut_data, self.save_callback, self._render_tiles)
