import customtkinter as ctk

# Color Palettes
THEMES = {
    "Blue": {
        "primary": "#0078d4",
        "hover": "#1084d8",
        "accent_text": "#00e5ff",
        "border": "#0078d4"
    },
    "Green": {
        "primary": "#2e7d32",
        "hover": "#388e3c",
        "accent_text": "#00e676",
        "border": "#2e7d32"
    },
    "Red": {
        "primary": "#c62828",
        "hover": "#d32f2f",
        "accent_text": "#ff5252",
        "border": "#c62828"
    },
    "Gold": {
        "primary": "#f9a825",
        "hover": "#fbc02d",
        "accent_text": "#ffd740",
        "border": "#f9a825"
    },
    "Purple": {
        "primary": "#6a1b9a",
        "hover": "#7b1fa2",
        "accent_text": "#e040fb",
        "border": "#6a1b9a"
    }
}

class ThemeManager:
    _current_theme = "Blue"

    @classmethod
    def set_theme(cls, theme_name):
        if theme_name in THEMES:
            cls._current_theme = theme_name
            
    @classmethod
    def get_color(cls, key):
        """Returns the color code for the given key from the current theme."""
        theme = THEMES.get(cls._current_theme, THEMES["Blue"])
        return theme.get(key, "#ffffff")
    
    @classmethod
    def get_theme_names(cls):
        return list(THEMES.keys())
