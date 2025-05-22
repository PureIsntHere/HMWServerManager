import os
import shutil
import subprocess
import threading
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, scrolledtext

import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplcursors

LOG_DIR = "logs"
used_ports = set()

BG_COLOR = "#1e1e1e"
FG_COLOR = "#d4d4d4"
BTN_COLOR = "#3a3a3a"
ACCENT_COLOR = "#0db9d7"

class ServerTab:
    def __init__(self, manager, name, config=None):
        self.manager = manager
        self.name = name
        self.frame = tk.Frame(manager.notebook, bg=BG_COLOR)
        self.executable_path = tk.StringVar()
        self.config_path = tk.StringVar()
        self.server_port = tk.StringVar(value="27016")
        self.server_status = tk.StringVar(value="🔴 Offline")

        self.auto_restart = tk.BooleanVar(value=config.get("auto_restart", False) if config else False)
        self.process = None
        self.log_data = []
        self.manual_stop = False

        self.mem_data = []
        self.cpu_data = []
        self.mem_max_points = 60

        if config:
            self.executable_path.set(config.get("exe", ""))
            self.config_path.set(config.get("cfg", ""))
            self.server_port.set(config.get("port", "27016"))

        self.create_widgets()
        self.auto_refresh_status()
        self.update_resource_plots()
    def create_widgets(self):
        default_font = ("Segoe UI", 10)
        large_font = ("Segoe UI", 11)
        mono_font = ("Consolas", 11)

        main_pane = tk.PanedWindow(self.frame, bg=BG_COLOR, sashwidth=2, sashrelief=tk.RAISED)
        main_pane.pack(fill=tk.BOTH, expand=True)

        control_frame = tk.Frame(main_pane, bg=BG_COLOR, padx=10, pady=10)
        main_pane.add(control_frame, width=400)

        def label(text):
            return tk.Label(control_frame, text=text, bg=BG_COLOR, fg=FG_COLOR, anchor="w", font=default_font)

        def entry(var):
            return tk.Entry(control_frame, textvariable=var, bg=BTN_COLOR, fg=FG_COLOR,
                            insertbackground=FG_COLOR, relief=tk.FLAT, font=default_font)

        label("Server Executable:").pack(anchor="w")
        entry(self.executable_path).pack(fill="x")
        tk.Button(control_frame, text="Browse", command=self.browse_executable,
                  bg=ACCENT_COLOR, fg="white", relief=tk.FLAT, font=large_font).pack(pady=(0, 10), fill="x")

        label("Config File:").pack(anchor="w")
        entry(self.config_path).pack(fill="x")
        tk.Button(control_frame, text="Browse", command=self.browse_config,
                  bg=ACCENT_COLOR, fg="white", relief=tk.FLAT, font=large_font).pack(pady=(0, 10), fill="x")

        label("Server Port:").pack(anchor="w")
        entry(self.server_port).pack(fill="x", pady=(0, 10))

        tk.Button(control_frame, text="Start Server", command=self.start_server,
                  bg=ACCENT_COLOR, fg="white", relief=tk.FLAT, font=large_font).pack(fill="x", pady=(0, 5))

        tk.Button(control_frame, text="Stop Server", command=self.stop_server,
                  bg="#d9534f", fg="white", relief=tk.FLAT, font=large_font).pack(fill="x")

        tk.Button(control_frame, text="Export Log", command=self.export_log,
                  bg="#6c757d", fg="white", relief=tk.FLAT, font=large_font).pack(fill="x", pady=(10, 5))

        tk.Checkbutton(control_frame, text="Auto-Restart on Crash",
                       variable=self.auto_restart, bg=BG_COLOR,
                       fg=FG_COLOR, selectcolor=BTN_COLOR,
                       font=default_font).pack(anchor="w", pady=(5, 5))

        label("Status:").pack(anchor="w", pady=(10, 0))
        self.status_label = tk.Label(control_frame, textvariable=self.server_status,
                                     fg="red", bg=BG_COLOR, font=("Segoe UI", 11, "bold"))
        self.status_label.pack(anchor="w")
        label("Memory Usage (MB):").pack(anchor="w", pady=(5, 0))
        self.fig_mem, self.ax_mem = plt.subplots(figsize=(3.6, 1.6), dpi=100, facecolor=BG_COLOR)
        self.ax_mem.set_facecolor("#2d2d2d")
        self.ax_mem.tick_params(colors="white", labelsize=8)
        self.ax_mem.set_ylabel("MB", color="white", fontsize=8)
        self.ax_mem.set_xlim(0, self.mem_max_points)
        self.ax_mem.grid(True, linestyle="--", color="#555", linewidth=0.3)
        for spine in self.ax_mem.spines.values():
            spine.set_visible(False)
        self.mem_line, = self.ax_mem.plot([], [], color="cyan", linewidth=1)
        self.mem_max_line, = self.ax_mem.plot([], [], linestyle="--", color="orange", linewidth=0.8)
        self.mem_canvas = FigureCanvasTkAgg(self.fig_mem, master=control_frame)
        self.mem_canvas.get_tk_widget().pack(fill="x", pady=(0, 5))

        cursor = mplcursors.cursor(self.mem_line, hover=True)
        cursor.connect("add", lambda sel: sel.annotation.set_text(f"{self.mem_data[int(sel.index)]:.1f} MB"))

        label("CPU Usage (%):").pack(anchor="w", pady=(5, 0))
        self.fig_cpu, self.ax_cpu = plt.subplots(figsize=(3.6, 1.6), dpi=100, facecolor=BG_COLOR)
        self.ax_cpu.set_facecolor("#2d2d2d")
        self.ax_cpu.tick_params(colors="white", labelsize=8)
        self.ax_cpu.set_ylabel("%", color="white", fontsize=8)
        self.ax_cpu.set_xlim(0, self.mem_max_points)
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.grid(True, linestyle="--", color="#555", linewidth=0.3)
        for spine in self.ax_cpu.spines.values():
            spine.set_visible(False)
        self.cpu_line, = self.ax_cpu.plot([], [], color="lime", linewidth=1)
        self.cpu_canvas = FigureCanvasTkAgg(self.fig_cpu, master=control_frame)
        self.cpu_canvas.get_tk_widget().pack(fill="x", pady=(0, 5))

        log_frame = tk.Frame(main_pane, bg=BG_COLOR)
        main_pane.add(log_frame)

        self.log_output = scrolledtext.ScrolledText(log_frame,
                                                    bg="#252526", fg=FG_COLOR,
                                                    insertbackground=FG_COLOR,
                                                    font=mono_font, wrap="word")
        self.log_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_output.config(state="disabled")
    def update_resource_plots(self):
        if self.process and self.process.poll() is None:
            try:
                proc = psutil.Process(self.process.pid)
                mem = proc.memory_info().rss / 1024 / 1024
                cpu = proc.cpu_percent(interval=None)
                self.mem_data.append(mem)
                self.cpu_data.append(cpu)
                if len(self.mem_data) > self.mem_max_points:
                    self.mem_data.pop(0)
                    self.cpu_data.pop(0)
                x = range(len(self.mem_data))
                self.mem_line.set_data(x, self.mem_data)
                self.mem_max_line.set_data(x, [max(self.mem_data)] * len(self.mem_data))
                self.ax_mem.set_ylim(0, max(64, max(self.mem_data) * 1.25))
                self.mem_canvas.draw()
                self.cpu_line.set_data(x, self.cpu_data)
                self.cpu_canvas.draw()
            except Exception as e:
                import traceback
                self.log("[ERROR] Resource monitor:\n" + traceback.format_exc())
        self.frame.after(2000, self.update_resource_plots)

    def browse_executable(self):
        path = filedialog.askopenfilename(title="Select hmw-mod.exe", filetypes=[("Executable", "*.exe")])
        if path:
            self.executable_path.set(path)

    def browse_config(self):
        path = filedialog.askopenfilename(title="Select server config", filetypes=[("Config Files", "*.cfg")])
        if path:
            self.config_path.set(path)

    def set_status(self, status_text, color):
        self.server_status.set(status_text)
        self.status_label.config(fg=color)
        if "Online" in status_text:
            emoji = "🟢"
        elif "Timeout" in status_text:
            emoji = "🟠"
        elif "Stopped" in status_text:
            emoji = "⏹"
        elif "Crashed" in status_text:
            emoji = "🟠"
        else:
            emoji = "🔴"
        self.manager.notebook.tab(self.manager.tabs.index(self), text=f"{emoji} {self.name}")
    def auto_refresh_status(self):
        if self.process and self.process.poll() is not None:
            if self.manual_stop:
                self.set_status("⏹ Stopped", "gray")
            else:
                self.set_status("🟠 Crashed", "orange")
                if self.process.returncode not in (0, None):
                    crash_dir = os.path.join(LOG_DIR, "crashes")
                    os.makedirs(crash_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    crash_file = os.path.join(crash_dir, f"{self.name.replace(' ', '_')}_crash_{timestamp}.log")
                    with open(crash_file, "w", encoding="utf-8") as f:
                        f.write("\n".join(self.log_data))
                    self.log(f"[CRASH] Crash log saved to {crash_file}")
                if self.auto_restart.get():
                    self.log("[INFO] Server crashed. Restarting after delay.")
                    self.manager.root.after(3000, self.start_server)
            self.manual_stop = False
        self.frame.after(2000, self.auto_refresh_status)

    def stop_server(self):
        self.manual_stop = True
        self.auto_restart.set(False)

        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.log("[ACTION] Server manually stopped.")
            try:
                self.process.wait(timeout=5)  # wait up to 5 seconds
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.log("[WARN] Server didn't terminate cleanly. Force killed.")

        self.set_status("⏹ Stopped", "gray")
        self.process = None  # ✅ Prevent crash detection


    def log(self, message):
        timestamp = datetime.now().strftime("[%H:%M:%S] ")
        line = timestamp + message
        self.log_data.append(line)
        self.log_output.config(state="normal")
        self.log_output.insert(tk.END, line + "\n")
        self.log_output.see(tk.END)
        self.log_output.config(state="disabled")

    def export_log(self):
        os.makedirs(LOG_DIR, exist_ok=True)
        file_path = os.path.join(LOG_DIR, f"{self.name.replace(' ', '_')}.log")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.log_data))
        self.log(f"[INFO] Log exported to {file_path}")

    def start_server(self):
        exe = self.executable_path.get()
        cfg = self.config_path.get()
        port = self.server_port.get()

        if not os.path.isfile(exe) or not os.path.isfile(cfg):
            return

        if port in used_ports:
            self.log(f"[ERROR] Port {port} is already in use.")
            return

        used_ports.add(port)
        working_dir = os.path.dirname(exe)

        cmd = [
            exe,
            "-dedicated",
            "-memoryfix",
            "+exec", os.path.basename(cfg),
            "+set", "net_port", port,
            "+map_rotate"
        ]

        self.log(f"[CMD] {' '.join(cmd)}")
        self.set_status("🔄 Starting...", "gray")
        self.log(f"[INFO] Launching on port {port}...")

        def run():
            try:
                self.process = subprocess.Popen(
                    cmd,
                    cwd=working_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                for line in self.process.stdout:
                    line = line.strip()
                    self.log(line)
                    if "Server started!" in line:
                        self.set_status("🟢 Online", "green")
                used_ports.discard(port)
            except Exception as e:
                self.log(f"[ERROR] {e}")
                used_ports.discard(port)
                self.set_status("🟠 Crashed", "orange")

        threading.Thread(target=run, daemon=True).start()
