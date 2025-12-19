import customtkinter as ctk
import json
from pathlib import Path

# Pfad zur Konfigurationsdatei
CONFIG_FILE = Path(__file__).parent / "config.json"
ICONS_DIR = Path(__file__).parent / "icons"

def setup_theme():
    """Initialisiert das Theme"""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

def load_config() -> dict:
    """Lädt die Konfiguration oder gibt Standardwerte zurück"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure all settings keys exist
                if "settings" not in data:
                    data["settings"] = {}
                
                defaults = {
                    "theme": "dark",
                    "columns": 5,
                    "tile_size": 100,
                    "free_placement": False,
                    "topbar_always_on_top": True,
                    "quicklaunch_always_on_top": False
                }
                
                for key, val in defaults.items():
                    if key not in data["settings"]:
                        data["settings"][key] = val
                        
                return data
        except Exception:
            pass
            
    return {
        "categories": [{"name": "Allgemein", "shortcuts": []}],
        "settings": {
            "theme": "dark", 
            "columns": 5, 
            "tile_size": 100,
            "free_placement": False,
            "topbar_always_on_top": True,
            "quicklaunch_always_on_top": False
        }
    }

def save_config(data: dict):
    """Speichert die Konfiguration"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
