import tkinter as tk
from tkinter import ttk

from lib.resource_averages import get_frame as resource_avg_frame
from lib.crash_reporting import get_frame as crash_report_frame
from lib.backup_restore import get_frame as backup_restore_frame
from lib.config_editor import get_frame as config_editor_frame
from lib.port_scan import get_frame as port_scan_frame

def create_features_tab(notebook):
    container = ttk.Notebook(notebook)
    container.configure(style="TNotebook")
    container.pack(fill="both", expand=True)

    features = [
        ("📊 Averages", resource_avg_frame),
        ("🧯 Crash Logs", crash_report_frame),
        ("🗃 Backups", backup_restore_frame),
        ("📝 Config Editor", config_editor_frame),
        ("📡 Port Scan", port_scan_frame)
    ]

    for label, get_frame in features:
        try:
            frame = get_frame(container)
            container.add(frame, text=label)
        except Exception as e:
            err_frame = tk.Frame(container, bg="red")
            tk.Label(err_frame, text=f"Failed to load: {label}\n{e}", fg="white", bg="red").pack()
            container.add(err_frame, text=label)

    return container
