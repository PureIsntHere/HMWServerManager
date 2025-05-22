import tkinter as tk
import socket
import asyncio
import threading


def get_frame(master):
    frame = tk.Frame(master, bg="#1e1e1e", padx=20, pady=20)

    tk.Label(
        frame,
        text="📡 Port Availability Scanner",
        font=("Segoe UI", 14, "bold"),
        fg="white",
        bg="#1e1e1e",
    ).pack(pady=(0, 10))

    tk.Label(
        frame,
        text="Enter ports to scan (e.g. 27016-27020 or 27016,27018):",
        font=("Segoe UI", 10),
        fg="#bbbbbb",
        bg="#1e1e1e",
    ).pack(anchor="w")

    entry = tk.Entry(
        frame, font=("Segoe UI", 10), bg="#2b2b2b", fg="white", insertbackground="white"
    )
    entry.insert(0, "27016-27020")
    entry.pack(fill="x", pady=(0, 5))

    host_var = tk.StringVar(value="127.0.0.1")
    host_frame = tk.Frame(frame, bg="#1e1e1e")
    host_frame.pack(anchor="w", pady=(5, 10))

    tk.Label(host_frame, text="Host:", bg="#1e1e1e", fg="white").pack(
        side="left", padx=(0, 5)
    )
    host_menu = tk.OptionMenu(host_frame, host_var, "127.0.0.1", "0.0.0.0", "localhost")
    host_menu.config(
        bg="#2b2b2b", fg="white", font=("Segoe UI", 10), highlightthickness=0
    )
    host_menu["menu"].config(bg="#2b2b2b", fg="white")
    host_menu.pack(side="left")

    result_box = tk.Text(
        frame, height=12, bg="#252526", fg="white", font=("Consolas", 10), wrap="none"
    )
    result_box.pack(fill="both", expand=True)

    def parse_ports(raw):
        ports = set()
        parts = raw.split(",")
        for part in parts:
            part = part.strip()
            if "-" in part:
                try:
                    start, end = map(int, part.split("-"))
                    ports.update(range(start, end + 1))
                except:
                    raise ValueError(f"Invalid range format: {part}")
            else:
                if part:
                    ports.add(int(part))
        return sorted(p for p in ports if 1 <= p <= 65535)

    async def scan_port(loop, host, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setblocking(False)
            await loop.sock_connect(sock, (host, port))
            sock.close()
            return port, False  # False = in use
        except:
            return port, True  # True = available

    async def scan_all_ports(host, ports):
        loop = asyncio.get_event_loop()
        tasks = [scan_port(loop, host, port) for port in ports]
        results = await asyncio.gather(*tasks)
        return results

    def start_async_scan():
        result_box.delete("1.0", "end")
        raw = entry.get().strip()
        try:
            ports = parse_ports(raw)
            if not ports:
                result_box.insert("end", "[ERROR] No valid ports to scan.\n")
                return

            result_box.insert(
                "end", f"🔎 Scanning {len(ports)} port(s) on {host_var.get()}...\n\n"
            )

            async def runner():
                results = await scan_all_ports(host_var.get(), ports)
                for port, is_free in results:
                    if is_free:
                        result_box.insert(
                            "end", f"[🟢 FREE] Port {port} is available\n"
                        )
                    else:
                        result_box.insert(
                            "end", f"[🔴 IN USE] Port {port} is occupied\n"
                        )

            threading.Thread(target=lambda: asyncio.run(runner())).start()

        except Exception as e:
            result_box.insert("end", f"[ERROR] {e}\n")

    def suggest_ports():
        entry.delete(0, "end")
        entry.insert(0, "27016-27020")

    def scan_all_from_manager():
        if hasattr(master.master, "tabs"):
            used = set()
            for tab in master.master.tabs:
                try:
                    used.add(str(tab.server_port.get()))
                except:
                    continue
            if used:
                entry.delete(0, "end")
                entry.insert(0, ",".join(sorted(used)))
            else:
                result_box.insert("end", "[WARN] No ports detected from tabs.\n")
        else:
            result_box.insert("end", "[ERROR] Server tabs unavailable in context.\n")

    control_frame = tk.Frame(frame, bg="#1e1e1e")
    control_frame.pack(fill="x", pady=(10, 0))

    tk.Button(
        control_frame,
        text="🔍 Scan",
        font=("Segoe UI", 10),
        bg="#3a3a3a",
        fg="white",
        command=start_async_scan,
    ).pack(side="left", padx=(0, 5))
    tk.Button(
        control_frame,
        text="💡 Suggest",
        font=("Segoe UI", 10),
        bg="#3a3a3a",
        fg="white",
        command=suggest_ports,
    ).pack(side="left", padx=(0, 5))
    tk.Button(
        control_frame,
        text="🧠 From Tabs",
        font=("Segoe UI", 10),
        bg="#3a3a3a",
        fg="white",
        command=scan_all_from_manager,
    ).pack(side="left")

    return frame
