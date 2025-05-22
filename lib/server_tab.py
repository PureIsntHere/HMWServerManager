import os
import re
import socket
import subprocess
import threading
import time
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
        self.rcon_password = ""
        self.failed_rcon_pings = 0
        self.rcon_warning_count = 0
        self.current_log_date = datetime.now().strftime("%Y-%m-%d")

        self.auto_restart = tk.BooleanVar(
            value=config.get("auto_restart", False) if config else False
        )
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
            self.parse_rcon_password(config.get("cfg", ""))

        self.create_widgets()
        self.auto_refresh_status()
        self.update_resource_plots()

    def get_daily_log_path(self):
        return os.path.join(
            LOG_DIR, f"{self.name.replace(' ', '_')}_{self.current_log_date}.log"
        )

    def parse_rcon_password(self, cfg_path):
        try:
            if not cfg_path or not os.path.isfile(cfg_path):
                return
            with open(cfg_path, "r", encoding="utf-8") as f:
                content = f.read()
            match = re.search(r'set\s+rcon_password\s+"([^"]+)"', content)
            if match:
                self.rcon_password = match.group(1)
        except Exception:
            self.rcon_password = ""

    def create_widgets(self):
        default_font = ("Segoe UI", 10)
        mono_font = ("Consolas", 11)

        main_pane = tk.PanedWindow(
            self.frame, bg=BG_COLOR, sashwidth=2, sashrelief=tk.RAISED
        )
        main_pane.pack(fill=tk.BOTH, expand=True)

        control_frame = tk.Frame(main_pane, bg=BG_COLOR, padx=10, pady=10)
        main_pane.add(control_frame, width=400)

        def label(text):
            return tk.Label(
                control_frame,
                text=text,
                bg=BG_COLOR,
                fg=FG_COLOR,
                anchor="w",
                font=default_font,
            )

        def entry(var):
            return tk.Entry(
                control_frame,
                textvariable=var,
                bg=BTN_COLOR,
                fg=FG_COLOR,
                insertbackground=FG_COLOR,
                relief=tk.FLAT,
                font=default_font,
            )

        label("Server Executable:").pack(anchor="w")
        entry(self.executable_path).pack(fill="x")
        tk.Button(
            control_frame,
            text="Browse",
            command=self.browse_executable,
            bg=ACCENT_COLOR,
            fg="white",
            relief=tk.FLAT,
        ).pack(pady=(0, 10), fill="x")

        label("Config File:").pack(anchor="w")
        entry(self.config_path).pack(fill="x")
        tk.Button(
            control_frame,
            text="Browse",
            command=self.browse_config,
            bg=ACCENT_COLOR,
            fg="white",
            relief=tk.FLAT,
        ).pack(pady=(0, 10), fill="x")

        label("Server Port:").pack(anchor="w")
        entry(self.server_port).pack(fill="x", pady=(0, 10))

        tk.Button(
            control_frame,
            text="Start Server",
            command=self.start_server,
            bg=ACCENT_COLOR,
            fg="white",
            relief=tk.FLAT,
        ).pack(fill="x", pady=(0, 5))
        tk.Button(
            control_frame,
            text="Stop Server",
            command=self.stop_server,
            bg="#d9534f",
            fg="white",
            relief=tk.FLAT,
        ).pack(fill="x")
        tk.Button(
            control_frame,
            text="Export Log",
            command=self.export_log,
            bg="#6c757d",
            fg="white",
            relief=tk.FLAT,
        ).pack(fill="x", pady=(10, 5))

        tk.Checkbutton(
            control_frame,
            text="Auto-Restart on Crash",
            variable=self.auto_restart,
            bg=BG_COLOR,
            fg=FG_COLOR,
            selectcolor=BTN_COLOR,
            font=default_font,
        ).pack(anchor="w", pady=(5, 5))

        label("Status:").pack(anchor="w", pady=(10, 0))
        self.status_label = tk.Label(
            control_frame,
            textvariable=self.server_status,
            fg="red",
            bg=BG_COLOR,
            font=("Segoe UI", 11, "bold"),
        )
        self.status_label.pack(anchor="w")
        # Memory Usage Graph
        self.fig_mem, self.ax_mem = plt.subplots(
            figsize=(3.6, 1.6), dpi=100, facecolor=BG_COLOR
        )
        self.ax_mem.set_facecolor("#2d2d2d")
        self.ax_mem.tick_params(colors="white", labelsize=8)
        self.ax_mem.set_ylabel("MB", color="white", fontsize=8)
        self.ax_mem.set_xlim(0, self.mem_max_points)
        self.ax_mem.grid(True, linestyle="--", color="#555", linewidth=0.3)
        for spine in self.ax_mem.spines.values():
            spine.set_visible(False)
        (self.mem_line,) = self.ax_mem.plot([], [], color="cyan", linewidth=1)
        (self.mem_max_line,) = self.ax_mem.plot(
            [], [], linestyle="--", color="orange", linewidth=0.8
        )
        self.mem_canvas = FigureCanvasTkAgg(self.fig_mem, master=control_frame)
        self.mem_canvas.get_tk_widget().pack(fill="x", pady=(0, 5))
        mplcursors.cursor(self.mem_line, hover=True)

        # CPU Usage Graph
        self.fig_cpu, self.ax_cpu = plt.subplots(
            figsize=(3.6, 1.6), dpi=100, facecolor=BG_COLOR
        )
        self.ax_cpu.set_facecolor("#2d2d2d")
        self.ax_cpu.tick_params(colors="white", labelsize=8)
        self.ax_cpu.set_ylabel("%", color="white", fontsize=8)
        self.ax_cpu.set_xlim(0, self.mem_max_points)
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.grid(True, linestyle="--", color="#555", linewidth=0.3)
        for spine in self.ax_cpu.spines.values():
            spine.set_visible(False)
        (self.cpu_line,) = self.ax_cpu.plot([], [], color="lime", linewidth=1)
        self.cpu_canvas = FigureCanvasTkAgg(self.fig_cpu, master=control_frame)
        self.cpu_canvas.get_tk_widget().pack(fill="x", pady=(0, 5))

        # Log Output + RCON Sender
        log_frame = tk.Frame(main_pane, bg=BG_COLOR)
        main_pane.add(log_frame)

        self.log_output = scrolledtext.ScrolledText(
            log_frame,
            bg="#252526",
            fg=FG_COLOR,
            insertbackground=FG_COLOR,
            font=("Consolas", 11),
            wrap="word",
        )
        self.log_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_output.config(state="disabled")

        rcon_frame = tk.Frame(log_frame, bg=BG_COLOR)
        rcon_frame.pack(fill="x", padx=5, pady=(0, 5))
        self.rcon_entry = tk.Entry(
            rcon_frame,
            font=("Consolas", 10),
            bg=BTN_COLOR,
            fg="white",
            insertbackground="white",
        )
        self.rcon_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(
            rcon_frame,
            text="Send RCON",
            command=self.send_custom_rcon,
            bg=ACCENT_COLOR,
            fg="white",
            font=("Segoe UI", 10),
        ).pack(side="right")

    def log(self, message):
        timestamp = datetime.now().strftime("[%H:%M:%S] ")
        line = timestamp + message

        # Rotate log file if date changed
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.current_log_date:
            self.current_log_date = today

        os.makedirs(LOG_DIR, exist_ok=True)
        with open(self.get_daily_log_path(), "a", encoding="utf-8") as f:
            f.write(line + "\n")

        self.log_data.append(line)
        if len(self.log_data) > 500:
            self.log_data.pop(0)

        self.log_output.config(state="normal")
        self.log_output.insert(tk.END, line + "\n")
        lines = int(self.log_output.index("end-1c").split(".")[0])
        if lines > 500:
            self.log_output.delete("1.0", "2.0")
        self.log_output.see(tk.END)
        self.log_output.config(state="disabled")

    def send_custom_rcon(self):
        command = self.rcon_entry.get().strip()
        if not command:
            self.log("[WARN] No RCON command entered.")
            return
        self.log(f"[RCON] Sending: {command}")
        result = self.send_rcon_command(command)
        self.log(f"[RCON] Response:\n{result}")

    def export_log(self):
        os.makedirs(LOG_DIR, exist_ok=True)
        file_path = os.path.join(
            LOG_DIR, f"{self.name.replace(' ', '_')}_manual_export.txt"
        )
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.log_data))
        self.log(f"[INFO] Log exported to {file_path}")

    def send_rcon_command(self, command):
        try:
            host = "127.0.0.1"
            port = int(self.server_port.get())
            password = self.rcon_password
            if not password:
                return "[ERROR] No RCON password set."

            packet = b"\xff\xff\xff\xff" + f"rcon {password} {command}\n".encode(
                "utf-8"
            )
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2.0)
            sock.sendto(packet, (host, port))

            response = b""
            while True:
                try:
                    part, _ = sock.recvfrom(4096)
                    response += part
                except socket.timeout:
                    break
            sock.close()

            if response.startswith(b"\xff\xff\xff\xffprint\n"):
                response = response[10:]
            return response.decode("utf-8", errors="ignore")
        except Exception as e:
            return f"[ERROR] {e}"

    def start_rcon_ping(self):
        def rcon_loop():
            self.failed_rcon_pings = 0
            self.rcon_warning_count = 0
            while self.process and self.process.poll() is None:
                ok = self.send_rcon_command("status")
                if "[ERROR]" in ok or not ok.strip():
                    self.failed_rcon_pings += 1
                    if self.failed_rcon_pings >= 3:
                        self.rcon_warning_count += 1
                        self.failed_rcon_pings = 0
                        self.set_status("🟠 Timeout (No RCON)", "orange")
                        self.log(
                            f"[WARN] RCON ping failed 3x. Server may be frozen. ({self.rcon_warning_count}/3)"
                        )

                        if self.rcon_warning_count >= 3:
                            self.log(
                                "[ERROR] RCON frozen warning hit 3x. Restarting server."
                            )
                            self.stop_server()
                            time.sleep(2)
                            self.start_server()
                            return
                else:
                    if self.rcon_warning_count > 0:
                        self.log("[INFO] RCON ping recovered.")
                    self.failed_rcon_pings = 0
                    self.rcon_warning_count = 0
                time.sleep(30)

        threading.Thread(target=rcon_loop, daemon=True).start()

    def start_server(self):
        exe = self.executable_path.get()
        cfg = self.config_path.get()
        port = self.server_port.get()

        if not os.path.isfile(exe) or not os.path.isfile(cfg):
            self.log("[ERROR] Executable or config path invalid.")
            return

        if port in used_ports:
            self.log(f"[ERROR] Port {port} is already in use.")
            return

        used_ports.add(port)
        self.parse_rcon_password(cfg)
        working_dir = os.path.dirname(exe)

        cmd = [
            exe,
            "-dedicated",
            "-memoryfix",
            "+exec",
            os.path.basename(cfg),
            "+set",
            "net_port",
            port,
            "+map_rotate",
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
                    text=True,
                )
                self.start_rcon_ping()
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

    def stop_server(self):
        self.manual_stop = True
        self.auto_restart.set(False)
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.log("[ACTION] Server manually stopped.")
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.log("[WARN] Server didn't terminate cleanly. Force killed.")
        self.set_status("⏹ Stopped", "gray")
        self.process = None

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
                self.log(f"[ERROR] Resource monitor: {e}")
        self.frame.after(2000, self.update_resource_plots)

    def auto_refresh_status(self):
        if self.process and self.process.poll() is not None:
            if self.manual_stop:
                self.set_status("⏹ Stopped", "gray")
            else:
                self.set_status("🟠 Crashed", "orange")
                if self.auto_restart.get():
                    self.log("[INFO] Server crashed. Restarting after delay.")
                    self.manager.root.after(3000, self.start_server)
            self.manual_stop = False
        self.frame.after(2000, self.auto_refresh_status)

    def browse_executable(self):
        path = filedialog.askopenfilename(
            title="Select hmw-mod.exe", filetypes=[("Executable", "*.exe")]
        )
        if path:
            self.executable_path.set(path)

    def browse_config(self):
        path = filedialog.askopenfilename(
            title="Select server config", filetypes=[("Config Files", "*.cfg")]
        )
        if path:
            self.config_path.set(path)
            self.parse_rcon_password(path)

    def set_status(self, status_text, color):
        self.server_status.set(status_text)
        self.status_label.config(fg=color)
        emoji = "🔴"
        if "Online" in status_text:
            emoji = "🟢"
        elif "Timeout" in status_text:
            emoji = "🟠"
        elif "Stopped" in status_text:
            emoji = "⏹"
        elif "Crashed" in status_text:
            emoji = "🟠"
        self.manager.notebook.tab(
            self.manager.tabs.index(self), text=f"{emoji} {self.name}"
        )
