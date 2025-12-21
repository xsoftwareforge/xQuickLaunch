import tkinter as tk
import os
import sys

print(f"Python Version: {sys.version}")
print(f"Platform: {sys.platform}")
print(f"TKDND_LIBRARY env var: {os.environ.get('TKDND_LIBRARY', 'Not Set')}")

root = tk.Tk()
print(f"Tcl Library: {root.tk.exprstring('$tcl_library')}")
print(f"Tk Library: {root.tk.exprstring('$tk_library')}")
print(f"Tcl Version: {root.tk.eval('info tclversion')}")
print(f"Tk Version: {root.tk.eval('package require Tk')}")

print("\n--- Attempting to load tkdnd ---")
try:
    # Try to add the path explicitly if set
    tkdnd_lib = os.environ.get('TKDND_LIBRARY')
    if tkdnd_lib:
        print(f"Adding to auto_path: {tkdnd_lib}")
        root.tk.eval(f'lappend auto_path {{{tkdnd_lib}}}')
    
    print("Files in auto_path:")
    print(root.tk.eval('set auto_path'))
    
    # Try to require the package
    version = root.tk.eval('package require tkdnd')
    print(f"SUCCESS: Loaded tkdnd version {version}")
except tk.TclError as e:
    print(f"FAILURE: TclError: {e}")
except Exception as e:
    print(f"FAILURE: Exception: {e}")

print("\n--- Font Info ---")
try:
    from tkinter import font
    print("Available font families:")
    print(font.families())
except Exception as e:
    print(f"Font Error: {e}")

root.destroy()
