import os
import json
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from lib.server_tab import ServerTab
from lib.features_tab import create_features_tab

# Theme Colors
BG_COLOR = "#1e1e1e"
FG_COLOR = "#d4d4d4"
BTN_COLOR = "#3a3a3a"
ACCENT_COLOR = "#0db9d7"

CONFIG_DIR = "cfg"
SESSION_FILE = os.path.join(CONFIG_DIR, "sessions.json")

class HMWServerManager:
    def __init__(self, root):
        self.root = root
        self.root.title("🛠 HMW Server Manager")
        self.root.configure(bg=BG_COLOR)
        self.root.geometry("1000x700")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=BTN_COLOR,
                        foreground=FG_COLOR,
                        font=("Segoe UI", 11),
                        padding=[12, 6])
        style.map("TNotebook.Tab",
                  background=[("selected", "#333333")],
                  foreground=[("selected", FG_COLOR)])

        topbar = tk.Frame(self.root, bg=BTN_COLOR, height=36, padx=10, pady=6)
        topbar.pack(fill="x", side="top")

        servers_btn = tk.Menubutton(
            topbar,
            text="📂 Servers",
            bg=BTN_COLOR,
            fg=FG_COLOR,
            activebackground="#444444",
            activeforeground=FG_COLOR,
            font=("Segoe UI", 11),
            relief="flat",
            highlightthickness=0,
            borderwidth=0
        )
        servers_btn.pack(side="left", padx=(0, 10))

        features_btn = tk.Menubutton(
            topbar,
            text="🧩 Features",
            bg=BTN_COLOR,
            fg=FG_COLOR,
            activebackground="#444444",
            activeforeground=FG_COLOR,
            font=("Segoe UI", 11),
            relief="flat",
            highlightthickness=0,
            borderwidth=0
        )
        features_btn.pack(side="left", padx=(0, 10))

        features_menu = tk.Menu(
            features_btn,
            tearoff=0,
            bg=BTN_COLOR,
            fg=FG_COLOR,
            activebackground="#444444",
            activeforeground=FG_COLOR,
            borderwidth=0
        )
        features_menu.add_command(label="📂 Open Features Tab", command=self.open_features_tab)
        features_btn.config(menu=features_menu)

        server_menu = tk.Menu(
            servers_btn,
            tearoff=0,
            bg=BTN_COLOR,
            fg=FG_COLOR,
            activebackground="#444444",
            activeforeground=FG_COLOR,
            borderwidth=0
        )
        server_menu.add_command(label="➕ Add New Server", command=self.add_server_tab)
        server_menu.add_command(label="✏️ Rename Current Tab", command=self.rename_current_tab)
        server_menu.add_command(label="❌ Close Current Tab", command=self.close_current_tab)
        servers_btn.config(menu=server_menu)

        tk.Button(
            topbar, text="🔁 Restart All", command=self.restart_all_servers,
            bg=ACCENT_COLOR, fg="white", font=("Segoe UI", 10), relief="flat"
        ).pack(side="right", padx=5)

        tk.Button(
            topbar, text="📁 Open Logs", command=self.open_logs_folder,
            bg=BTN_COLOR, fg=FG_COLOR, font=("Segoe UI", 10), relief="flat",
            activebackground="#444", activeforeground=FG_COLOR
        ).pack(side="right", padx=5)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.tabs = []
        self.load_sessions()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def add_server_tab(self, name=None, config=None):
        name = name or f"Server {len(self.tabs) + 1}"
        tab = ServerTab(self, name, config)
        self.tabs.append(tab)
        self.notebook.add(tab.frame, text=f"🖥 {name}")
        self.notebook.select(len(self.tabs) - 1)

    def rename_current_tab(self):
        index = self.notebook.index(self.notebook.select())
        name = simpledialog.askstring("Rename Server", "New name:", initialvalue=self.tabs[index].name)
        if name:
            self.tabs[index].name = name
            self.notebook.tab(index, text=f"🖥 {name}")

    def close_current_tab(self):
        index = self.notebook.index(self.notebook.select())
        if index >= 0:
            tab = self.tabs[index]
            if tab.process and tab.process.poll() is None:
                if not messagebox.askyesno("Close Server", "Server is running. Stop and close?"):
                    return
                tab.process.terminate()
            self.notebook.forget(index)
            self.tabs.pop(index)

    def save_sessions(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        session_data = []
        for tab in self.tabs:
            session_data.append({
                "name": tab.name,
                "exe": tab.executable_path.get(),
                "cfg": tab.config_path.get(),
                "port": tab.server_port.get(),
                "auto_restart": tab.auto_restart.get()
            })
        with open(SESSION_FILE, "w") as f:
            json.dump(session_data, f, indent=4)

    def load_sessions(self):
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r") as f:
                for tab_data in json.load(f):
                    self.add_server_tab(tab_data["name"], tab_data)

    def on_close(self):
        self.save_sessions()
        self.root.destroy()

    def restart_all_servers(self):
        for tab in self.tabs:
            if tab.process and tab.process.poll() is None:
                tab.stop_server()
            tab.start_server()

    def open_logs_folder(self):
        import subprocess
        import platform
        path = os.path.abspath("logs")
        os.makedirs(path, exist_ok=True)
        if platform.system() == "Windows":
            subprocess.Popen(f'explorer "{path}"')
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def open_features_tab(self):
        if not hasattr(self, "_features_tab_created"):
            features_tab = tk.Frame(self.notebook, bg=BG_COLOR)
            create_features_tab(features_tab)
            self.notebook.add(features_tab, text="🧩 Features")
            self._features_tab_created = True
            self.notebook.select(len(self.tabs))
