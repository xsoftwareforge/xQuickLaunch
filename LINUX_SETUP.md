## Prerequisites

This application uses `tkinter`.

### Linux (Debian/Ubuntu/Mint)
Usually installed by default or with python. If missing:
```bash
sudo apt install python3-tk
```

### FreeBSD
FreeBSD does not include `tkinter` by default. You must install it manually.
Make sure to match your python version (e.g., `py311` for Python 3.11).

```bash
sudo pkg install py311-tkinter
# or for Python 3.9:
# sudo pkg install py39-tkinter
```

## Enable Drag & Drop Support

To enable Drag & Drop functionality on Linux and FreeBSD, you need to install the system-level `tk-dnd` library.

## Linux (Debian/Ubuntu/Mint)

1.  **Install the library**:
    ```bash
    sudo apt update
    sudo apt install tk-dnd
    ```

## FreeBSD

1.  **Install the library**:
    ```bash
    sudo pkg install tkdnd
    ```

## Troubleshooting

### "Platform not supported" (FreeBSD/Linux)

If you see `Drag & Drop not supported: Platform not supported.`, the python wrapper cannot find the installed `tkdnd` library.

**Fix:**
1.  Find where `tkdnd` is installed:
    ```bash
    pkg info -l tkdnd | grep libtkdnd
    # Example output: /usr/local/lib/tkdnd2.9/libtkdnd2.9.so
    ```
2.  Set the `TKDND_LIBRARY` environment variable to the **directory** containing that file.
    ```bash
    export TKDND_LIBRARY="/usr/local/lib/tkdnd2.9"
    python main.py
    ```

### Font Warning (FreeBSD)
`Preferred drawing method 'font_shapes' can not be used...`

This means CustomTkinter cannot load its font files.
**Fix:**
Ensure the font files in `customtkinter` package are readable, or try installing standard fonts:
```bash
sudo pkg install xorg-fonts-truetype
```
Also ensure your user has read permissions to the python site-packages if installed systematically.

If the application still says "Drag & Drop not supported", you may need to help the python library find the installed `tkdnd` library.

1.  Find where `tkdnd` was installed.
    -   Linux: Often `/usr/lib/tk-dnd2.8` or `/usr/share/tcltk/tkdnd2.8`
    -   FreeBSD: Often `/usr/local/lib/tkdnd`

2.  Ensure your `PYTHONPATH` or `TCL_LIBRARY` environment variables include this path, or just restart the application; often `tkinter` finds it automatically if installed via package manager.

## Note on `tkinterdnd2-universal`

We attempted to use `tkinterdnd2-universal` to automate this, but it currently has compatibility issues with newer Python versions (3.13+) found on some Windows systems. Sticking to the standard package + system install is the most stable method for now.
