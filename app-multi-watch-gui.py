import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import psutil
import subprocess
import time
import threading
import sys
import pystray
from PIL import Image, ImageDraw

CONFIG_FILE = "app_pairs.json"

class AppWatcher:
    def __init__(self, root):
        self.root = root
        self.root.title("App Launcher Watcher")
        self.app_pairs = []
        self.load_pairs()
        self.watching = False
        self.watcher_thread = None

        # GUI widgets
        self.listbox = tk.Listbox(root, width=60)
        self.listbox.pack(pady=10)

        btn_frame = tk.Frame(root)
        btn_frame.pack()

        self.add_btn = tk.Button(btn_frame, text="Add Pair", command=self.add_pair)
        self.add_btn.grid(row=0, column=0, padx=5)

        self.remove_btn = tk.Button(btn_frame, text="Remove Selected", command=self.remove_selected)
        self.remove_btn.grid(row=0, column=1, padx=5)

        self.toggle_btn = tk.Button(root, text="Start Watching", command=self.toggle_watch)
        self.toggle_btn.pack(pady=10)

        self.status_label = tk.Label(root, text="Status: Not Watching")
        self.status_label.pack()

        # System tray setup
        self.tray_icon = self.create_tray_icon()

    def create_tray_icon(self):
        # Create a simple circle icon
        img = Image.new('RGB', (64, 64), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.ellipse((16, 16, 48, 48), fill=(0, 122, 255))
        return pystray.Icon("AppWatcher", img, "AppWatcher", menu=pystray.Menu(
            pystray.MenuItem("Show", self.show_window),
            pystray.MenuItem("Exit", self.exit_app)
        ))

    def show_window(self, icon=None, item=None):
        self.root.after(0, self.root.deiconify)

    def exit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()

    def load_pairs(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                self.app_pairs = json.load(f)

    def save_pairs(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.app_pairs, f, indent=4)

    def add_pair(self):
        trigger_path = filedialog.askopenfilename(title="Select Trigger App")
        if not trigger_path:
            return
        launch_path = filedialog.askopenfilename(title="Select App to Launch")
        if not launch_path:
            return

        pair = {"trigger": trigger_path, "launch": launch_path}
        self.app_pairs.append(pair)
        self.save_pairs()
        self.update_listbox()

    def remove_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            return
        index = selection[0]
        del self.app_pairs[index]
        self.save_pairs()
        self.update_listbox()

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for pair in self.app_pairs:
            self.listbox.insert(tk.END, f"Watch: {os.path.basename(pair['trigger'])} → {os.path.basename(pair['launch'])}")

    def toggle_watch(self):
        if self.watching:
            self.stop_watching()
        else:
            self.start_watching()

    def start_watching(self):
        self.watching = True
        self.toggle_btn.config(text="Stop Watching")
        self.status_label.config(text="Status: Watching")
        self.watcher_thread = threading.Thread(target=self.watch_loop, daemon=True)
        self.watcher_thread.start()

    def stop_watching(self):
        self.watching = False
        self.toggle_btn.config(text="Start Watching")
        self.status_label.config(text="Status: Not Watching")

    def is_process_running(self, path):
        for proc in psutil.process_iter(['exe']):
            try:
                if proc.info['exe'] and os.path.normcase(proc.info['exe']) == os.path.normcase(path):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def watch_loop(self):
        while self.watching:
            for pair in self.app_pairs:
                if self.is_process_running(pair["trigger"]):
                    if not self.is_process_running(pair["launch"]):
                        subprocess.Popen(pair["launch"])
            time.sleep(3)

    def run_tray(self):
        self.root.withdraw()
        self.tray_icon.run()

def run_gui():
    root = tk.Tk()
    app = AppWatcher(root)
    app.update_listbox()

    # Check if "--silent" flag is passed
    if "--silent" in sys.argv:
        app.start_watching()
        threading.Thread(target=app.run_tray, daemon=True).start()
    else:
        def on_close():
            if messagebox.askokcancel("Quit", "Do you want to quit the AppWatcher?"):
                if app.tray_icon:
                    app.tray_icon.stop()
                root.destroy()
        root.protocol("WM_DELETE_WINDOW", on_close)
        root.mainloop()

if __name__ == "__main__":
    run_gui()
