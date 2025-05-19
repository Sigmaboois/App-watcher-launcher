import os
import sys
import shutil
import win32com.client

def add_to_startup(app_name, target_path):
    startup_dir = os.path.join(os.environ["APPDATA"], "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
    shortcut_path = os.path.join(startup_dir, f"{app_name}.lnk")

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target_path
    shortcut.WorkingDirectory = os.path.dirname(target_path)
    shortcut.IconLocation = target_path
    shortcut.save()

# Example:
# Replace with the full path to your EXE or PY file
add_to_startup("AppWatcher", r"C:\Path\To\app_multi_watch_gui.exe")
