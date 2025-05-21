import tkinter as tk
from tkinter import messagebox
import psutil
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

def get_frame(master):
    frame = tk.Frame(master, bg="#1e1e1e", padx=20, pady=20)

    tk.Label(frame, text="📊 CPU + Memory Averages", font=("Segoe UI", 14, "bold"),
             fg="white", bg="#1e1e1e").pack(pady=(0, 10))

    stats_label = tk.Label(frame, text="", fg="lime", bg="#1e1e1e", font=("Segoe UI", 11))
    stats_label.pack(pady=(5, 10))

    show_graph = tk.BooleanVar(value=True)
    per_core = tk.BooleanVar(value=False)

    toggle_frame = tk.Frame(frame, bg="#1e1e1e")
    toggle_frame.pack(pady=(0, 10))

    def redraw_immediate(*_):
        stats_label.config(text="Updating...")

    tk.Checkbutton(toggle_frame, text="📈 Show Graph", variable=show_graph,
                   bg="#1e1e1e", fg="white", selectcolor="#1e1e1e",
                   font=("Segoe UI", 10), command=redraw_immediate).pack(side="left", padx=5)
    tk.Checkbutton(toggle_frame, text="🧠 Per-Core CPU", variable=per_core,
                   bg="#1e1e1e", fg="white", selectcolor="#1e1e1e",
                   font=("Segoe UI", 10), command=redraw_immediate).pack(side="left", padx=5)

    # Graph setup
    fig, ax = plt.subplots(figsize=(4.5, 2.2), dpi=100)
    fig.patch.set_facecolor("#1e1e1e")  # ✅ Remove white background around graph
    ax.set_facecolor("#2d2d2d")
    ax.tick_params(colors="white", labelsize=9)
    ax.set_xlim(0, 60)
    ax.set_ylim(0, 100)
    ax.set_ylabel("%", color="white", fontsize=9)
    ax.grid(True, linestyle="--", color="#555", linewidth=0.3)
    for spine in ax.spines.values():
        spine.set_visible(False)

    mem_line, = ax.plot([], [], color="cyan", linewidth=1, label="RAM")
    cpu_line, = ax.plot([], [], color="lime", linewidth=1, label="CPU")

    overlay_lines = {
        "cpu_avg": None,
        "cpu_max": None,
        "mem_avg": None,
        "mem_max": None
    }

    ax.legend(loc="upper right", fontsize=8, facecolor="#2d2d2d", labelcolor="white")

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill="x", pady=(0, 10))

    cpu_data = []
    mem_data = []

    def update():
        cpu = psutil.cpu_percent(percpu=per_core.get())
        avg_cpu = sum(cpu) / len(cpu) if isinstance(cpu, list) else cpu
        mem = psutil.virtual_memory().percent

        cpu_data.append(avg_cpu)
        mem_data.append(mem)

        if len(cpu_data) > 60:
            cpu_data.pop(0)
            mem_data.pop(0)

        cpu_avg = sum(cpu_data) / len(cpu_data)
        mem_avg = sum(mem_data) / len(mem_data)
        cpu_max = max(cpu_data)
        mem_max = max(mem_data)

        stats_label.config(
            text=f"🧠 CPU Avg: {cpu_avg:.1f}% (Max: {cpu_max:.1f}%)   💾 RAM Avg: {mem_avg:.1f}% (Max: {mem_max:.1f}%)"
        )

        if show_graph.get():
            canvas_widget.pack(fill="x", pady=(0, 10))
            mem_line.set_data(range(len(mem_data)), mem_data)
            cpu_line.set_data(range(len(cpu_data)), cpu_data)

            # Remove old overlay lines
            for key, line in overlay_lines.items():
                if line:
                    try:
                        line.remove()
                    except:
                        pass
                    overlay_lines[key] = None

            # Add new overlay lines
            overlay_lines["cpu_avg"] = ax.axhline(cpu_avg, color="lime", linestyle="--", linewidth=0.8)
            overlay_lines["cpu_max"] = ax.axhline(cpu_max, color="green", linestyle=":", linewidth=0.8)
            overlay_lines["mem_avg"] = ax.axhline(mem_avg, color="cyan", linestyle="--", linewidth=0.8)
            overlay_lines["mem_max"] = ax.axhline(mem_max, color="blue", linestyle=":", linewidth=0.8)

            ax.set_xlim(0, max(60, len(cpu_data)))
            ymax = max(cpu_max, mem_max, 100)
            ax.set_ylim(0, ymax + 5)
            canvas.draw()
        else:
            canvas_widget.forget()

        frame.after(2000, update)

    def export_stats():
        try:
            os.makedirs("logs", exist_ok=True)
            filename = f"logs/resource_averages_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
            with open(filename, "w") as f:
                f.write("Second,CPU %,RAM %\n")
                for i in range(len(cpu_data)):
                    f.write(f"{i},{cpu_data[i]:.1f},{mem_data[i]:.1f}\n")
            messagebox.showinfo("Exported", f"Stats saved to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    tk.Button(frame, text="💾 Export Stats", command=export_stats,
              bg="#3a3a3a", fg="white", font=("Segoe UI", 10)).pack()

    update()
    return frame
