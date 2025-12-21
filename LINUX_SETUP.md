# Linux & FreeBSD Setup Guide

To enable Drag & Drop functionality on Linux and FreeBSD, you need to install the system-level `tk-dnd` library. The Python `tkinterdnd2` package requires this underlying library to function.

## Linux (Debian/Ubuntu/Mint)

1.  **Install the library**:
    ```bash
    sudo apt update
    sudo apt install tk-dnd
    ```

## FreeBSD

1.  **Install the library**:
    ```bash
    sudo pkg install tk-dnd
    ```

## Troubleshooting

If the application still says "Drag & Drop not supported", you may need to help the python library find the installed `tkdnd` library.

1.  Find where `tkdnd` was installed.
    -   Linux: Often `/usr/lib/tk-dnd2.8` or `/usr/share/tcltk/tkdnd2.8`
    -   FreeBSD: Often `/usr/local/lib/tkdnd`

2.  Ensure your `PYTHONPATH` or `TCL_LIBRARY` environment variables include this path, or just restart the application; often `tkinter` finds it automatically if installed via package manager.

## Note on `tkinterdnd2-universal`

We attempted to use `tkinterdnd2-universal` to automate this, but it currently has compatibility issues with newer Python versions (3.13+) found on some Windows systems. Sticking to the standard package + system install is the most stable method for now.
