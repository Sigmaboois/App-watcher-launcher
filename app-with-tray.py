import tkinter as tk
from tkinter import filedialog, messagebox
import psutil
import subprocess
import threading
import time
import os
import json
import pystray
from PIL import Image, ImageDraw

CONFIG_PATH = "watch_config.json"

class AppWatcher:
    def __init__(self, root):
        self.root = root
        self.root.title("App Watcher Launcher")
        self.root.geometry("500x350")

        self.watch_path = ""
        self.launch_path = ""
        self.already_launched = False
        self.watching = False
        self.monitor_thread = None
        self.tray_icon = None

        # GUI
        self.watch_label = tk.Label(root, text="App to watch for:")
        self.watch_label.pack(pady=5)

        self.watch_entry = tk.Entry(root, width=50)
        self.watch_entry.pack()

        self.watch_browse = tk.Button(root, text="Browse", command=self.select_watch_app)
        self.watch_browse.pack()

        self.launch_label = tk.Label(root, text="App to launch:")
        self.launch_label.pack(pady=5)

        self.launch_entry = tk.Entry(root, width=50)
        self.launch_entry.pack()

        self.launch_browse = tk.Button(root, text="Browse", command=self.select_launch_app)
        self.launch_browse.pack()

        self.start_button = tk.Button(root, text="Start Watching", command=self.start_watching)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(root, text="Stop Watching", command=self.stop_watching, state=tk.DISABLED)
        self.stop_button.pack()

        self.load_config()
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

    def select_watch_app(self):
        filepath = filedialog.askopenfilename(filetypes=[("Executable Files", "*.exe")])
        if filepath:
            self.watch_path = filepath
            self.watch_entry.delete(0, tk.END)
            self.watch_entry.insert(0, filepath)

    def select_launch_app(self):
        filepath = filedialog.askopenfilename(filetypes=[("Executable Files", "*.exe")])
        if filepath:
            self.launch_path = filepath
            self.launch_entry.delete(0, tk.END)
            self.launch_entry.insert(0, filepath)

    def start_watching(self):
        if not self.watch_entry.get() or not self.launch_entry.get():
            messagebox.showerror("Missing info", "Please select both apps.")
            return

        self.watch_path = self.watch_entry.get()
        self.launch_path = self.launch_entry.get()
        self.target_process_name = os.path.basename(self.watch_path)

        self.save_config()

        self.watching = True
        self.already_launched = False
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

        self.show_tray_icon()
        self.root.withdraw()

    def stop_watching(self):
        self.watching = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def monitor_loop(self):
        while True:
            if self.watching:
                running = [p.name().lower() for p in psutil.process_iter()]
                if self.target_process_name.lower() in running:
                    if not self.already_launched:
                        subprocess.Popen(self.launch_path)
                        self.already_launched = True
                else:
                    self.already_launched = False
            time.sleep(2)

    def save_config(self):
        config = {
            "watch_path": self.watch_path,
            "launch_path": self.launch_path
        }
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f)

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    config = json.load(f)
                    self.watch_path = config.get("watch_path", "")
                    self.launch_path = config.get("launch_path", "")
                    self.watch_entry.insert(0, self.watch_path)
                    self.launch_entry.insert(0, self.launch_path)
            except Exception as e:
                print(f"Failed to load config: {e}")

    def show_tray_icon(self):
        image = self.create_image()
        self.tray_icon = pystray.Icon("AppWatcher", image, "App Watcher", menu=pystray.Menu(
            pystray.MenuItem("Resume Watching", self.resume_watching),
            pystray.MenuItem("Pause Watching", self.pause_watching),
            pystray.MenuItem("Quit", self.quit_app)
        ))
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def create_image(self):
        # Generate a simple black-and-white icon
        image = Image.new("RGB", (64, 64), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 16, 48, 48), fill="black")
        return image

    def pause_watching(self, icon=None, item=None):
        self.watching = False

    def resume_watching(self, icon=None, item=None):
        self.watching = True

    def quit_app(self, icon=None, item=None):
        self.watching = False
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()

    def hide_window(self):
        self.root.withdraw()

if __name__ == "__main__":
    root = tk.Tk()
    app = AppWatcher(root)
    root.mainloop()
