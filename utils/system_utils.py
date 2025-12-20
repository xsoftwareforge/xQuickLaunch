import psutil
import sys
import os
from pathlib import Path

# Conditional import for winreg
if sys.platform == 'win32':
    import winreg

def get_system_stats():
    """Returns a tuple (cpu_percent, ram_percent)"""
    try:
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        return cpu, ram
    except Exception:
        return 0, 0

def set_autostart(enable: bool, app_name="QuickLaunch"):
    """
    Sets or removes the autostart registry key for the current application.
    Works for both Python script and frozen executable.
    """
    if sys.platform != 'win32':
        return False

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    # Determine the path to the executable/script
    if getattr(sys, 'frozen', False):
        # If frozen (compiled exe), use the executable path
        app_path = f'"{sys.executable}"'
    else:
        # If running as script, use pythonw.exe + script path to avoid console window
        # Assuming we want to run main.py or app.py
        # Finding the main entry point (usually main.py relative to this file)
        # current file is utils/system_utils.py -> parent is utils -> parent is root
        root_dir = Path(__file__).parent.parent
        script_path = root_dir / "main.py"
        
        # Use pythonw.exe for no console
        python_exe = sys.executable.replace("python.exe", "pythonw.exe")
        app_path = f'"{python_exe}" "{script_path}"'

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        
        if enable:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass # Key didn't exist, which is fine
                
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Error setting autostart: {e}")
        return False

def check_autostart(app_name="QuickLaunch") -> bool:
    """Checks if autostart is currently enabled via registry"""
    if sys.platform != 'win32':
        return False

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, app_name)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False
