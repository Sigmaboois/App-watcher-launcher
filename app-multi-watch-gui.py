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
        self.root.title("Multi App Watcher")
        self.root.geometry("600x400")

        self.pairs = []
        self.watching = False
        self.tray_icon = None
        self.already_launched = {}
        self.monitor_thread = None

        self.pair_listbox = tk.Listbox(root, width=70)
        self.pair_listbox.pack(pady=10)

        self.add_pair_btn = tk.Button(root, text="Add Watch-Launch Pair", command=self.add_pair_dialog)
        self.add_pair_btn.pack(pady=5)

        self.start_button = tk.Button(root, text="Start Watching", command=self.start_watching)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(root, text="Stop Watching", command=self.stop_watching, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.load_config()
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

    def add_pair_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("New Watch-Launch Pair")
        dialog.geometry("500x200")

        tk.Label(dialog, text="App to watch:").pack()
        watch_entry = tk.Entry(dialog, width=50)
        watch_entry.pack()

        def browse_watch():
            path = filedialog.askopenfilename(filetypes=[("Executable Files", "*.exe")])
            if path:
                watch_entry.delete(0, tk.END)
                watch_entry.insert(0, path)

        tk.Button(dialog, text="Browse", command=browse_watch).pack()

        tk.Label(dialog, text="App to launch:").pack()
        launch_entry = tk.Entry(dialog, width=50)
        launch_entry.pack()

        def browse_launch():
            path = filedialog.askopenfilename(filetypes=[("Executable Files", "*.exe")])
            if path:
                launch_entry.delete(0, tk.END)
                launch_entry.insert(0, path)

        tk.Button(dialog, text="Browse", command=browse_launch).pack()

        def save_pair():
            watch = watch_entry.get()
            launch = launch_entry.get()
            if watch and launch:
                self.pairs.append((watch, launch))
                self.pair_listbox.insert(tk.END, f"Watch: {os.path.basename(watch)} → Launch: {os.path.basename(launch)}")
                dialog.destroy()
                self.save_config()
            else:
                messagebox.showerror("Error", "Both paths must be selected.")

        tk.Button(dialog, text="Add Pair", command=save_pair).pack(pady=10)

    def start_watching(self):
        if not self.pairs:
            messagebox.showerror("No Pairs", "Please add at least one pair.")
            return

        self.watching = True
        self.already_launched = {os.path.basename(p[0]).lower(): False for p in self.pairs}
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
                for watch_path, launch_path in self.pairs:
                    proc_name = os.path.basename(watch_path).lower()
                    if proc_name in running:
                        if not self.already_launched.get(proc_name, False):
                            subprocess.Popen(launch_path)
                            self.already_launched[proc_name] = True
                    else:
                        self.already_launched[proc_name] = False
            time.sleep(2)

    def save_config(self):
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.pairs, f)

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    self.pairs = json.load(f)
                    for watch, launch in self.pairs:
                        self.pair_listbox.insert(tk.END, f"Watch: {os.path.basename(watch)} → Launch: {os.path.basename(launch)}")
            except Exception as e:
                print(f"Error loading config: {e}")

    def show_tray_icon(self):
        image = self.create_image()
        self.tray_icon = pystray.Icon("MultiAppWatcher", image, "Multi App Watcher", menu=pystray.Menu(
            pystray.MenuItem("Resume Watching", self.resume_watching),
            pystray.MenuItem("Pause Watching", self.pause_watching),
            pystray.MenuItem("Quit", self.quit_app)
        ))
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def create_image(self):
        image = Image.new("RGB", (64, 64), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 16, 48, 48), fill="blue")
        return image

    def pause_watching(self, *args):
        self.watching = False

    def resume_watching(self, *args):
        self.watching = True

    def quit_app(self, *args):
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
