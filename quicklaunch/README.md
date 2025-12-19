# QuickLaunch - Schnellstart-Leiste

Eine moderne Desktop-Anwendung zum Verwalten von Verknüpfungen für Windows und Linux.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2+-green.svg)

## Features

- 🎨 **Modernes dunkles Design** (Windows 11 Style)
- 📁 **Drag & Drop** - Ziehe Dateien/Ordner direkt ins Fenster
- 🏷️ **Kategorien/Tabs** - Organisiere deine Verknüpfungen
- 🌐 **URLs & Programme** - Speichere Webseiten und lokale Programme
- 💾 **Persistente Speicherung** - Einstellungen werden automatisch gespeichert
- 🖱️ **Kontextmenü** - Rechtsklick für schnelle Aktionen

## Installation

### Voraussetzungen

- Python 3.8 oder höher
- pip (Python Package Manager)

### Schritte

1. **Python installieren** (falls noch nicht vorhanden)
   - Windows: [python.org/downloads](https://www.python.org/downloads/)
   - Linux: `sudo apt install python3 python3-pip`

2. **Abhängigkeiten installieren**
   ```bash
   cd quicklaunch
   pip install -r requirements.txt
   ```

3. **Optional: TkDND für besseres Drag & Drop (Linux)**
   ```bash
   # Ubuntu/Debian
   sudo apt install tkdnd
   
   # Fedora
   sudo dnf install tkdnd
   ```

## Starten

```bash
python main.py
```

Oder unter Linux:
```bash
python3 main.py
```

## Verwendung

### Verknüpfungen hinzufügen

1. **Per Drag & Drop**: Ziehe Dateien, Ordner oder .lnk-Dateien direkt ins Fenster
2. **Manuell**: Klicke auf "+ Hinzufügen" und wähle zwischen Datei/Ordner oder URL

### Kategorien verwalten

- Klicke auf "+ Kategorie" um eine neue Kategorie zu erstellen
- Nutze die Tabs oben um zwischen Kategorien zu wechseln

### Verknüpfungen bearbeiten

- **Öffnen**: Einfacher Linksklick auf eine Kachel
- **Bearbeiten/Löschen**: Rechtsklick für das Kontextmenü

## Konfiguration

Die Einstellungen werden in `config.json` gespeichert. Du kannst diese Datei manuell bearbeiten:

```json
{
  "categories": [
    {
      "name": "Allgemein",
      "shortcuts": [
        {
          "name": "Google",
          "path": "https://www.google.com",
          "type": "url",
          "icon": "🌐"
        }
      ]
    }
  ],
  "settings": {
    "theme": "dark",
    "columns": 4,
    "tile_size": 100
  }
}
```

## Tastenkürzel

| Aktion | Tastenkürzel |
|--------|-------------|
| Neues Element | + Button |
| Neue Kategorie | + Kategorie Button |
| Element öffnen | Linksklick |
| Kontextmenü | Rechtsklick |

## Fehlerbehebung

### "ModuleNotFoundError: No module named 'customtkinter'"
```bash
pip install customtkinter
```

### Drag & Drop funktioniert nicht (Linux)
Installiere TkDND:
```bash
sudo apt install python3-tk tkdnd
```

### Icons werden nicht korrekt angezeigt
Stelle sicher, dass du eine Schriftart mit Emoji-Support installiert hast:
- Windows: Segoe UI Emoji (Standard)
- Linux: `sudo apt install fonts-noto-color-emoji`

## Lizenz

MIT License - Frei verwendbar für private und kommerzielle Zwecke.
