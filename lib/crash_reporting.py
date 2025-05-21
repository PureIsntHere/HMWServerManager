import tkinter as tk
import os
import subprocess

def get_frame(master):
    frame = tk.Frame(master, bg="#1e1e1e", padx=20, pady=20)

    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    selected_file = tk.StringVar()

    tk.Label(frame, text="🧯 Crash Logs Viewer", font=("Segoe UI", 14, "bold"),
             fg="white", bg="#1e1e1e").pack(pady=(0, 10))

    search_entry = tk.Entry(frame, font=("Segoe UI", 10), bg="#2b2b2b", fg="white", insertbackground="white")
    search_entry.pack(fill="x", pady=(0, 5))

    listbox = tk.Listbox(frame, height=8, bg="#2b2b2b", fg="white", font=("Consolas", 10))
    listbox.pack(fill="x", pady=(0, 5))

    log_display = tk.Text(frame, height=14, bg="#252526", fg="white", font=("Consolas", 10), wrap="none")
    log_display.pack(fill="both", expand=True)

    def refresh_list():
        listbox.delete(0, "end")
        for file in sorted(os.listdir(log_dir)):
            if file.endswith(".log"):
                listbox.insert("end", file)

    def load_selected():
        log_display.delete("1.0", "end")
        sel = listbox.curselection()
        if not sel:
            return
        fname = listbox.get(sel[0])
        selected_file.set(fname)
        path = os.path.join(log_dir, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            log_display.insert("1.0", content)
        except Exception as e:
            log_display.insert("1.0", f"[ERROR] {e}")

    def search_logs():
        keyword = search_entry.get().lower()
        log_display.tag_remove("highlight", "1.0", "end")
        if not keyword:
            return
        start = "1.0"
        while True:
            pos = log_display.search(keyword, start, stopindex="end", nocase=True)
            if not pos:
                break
            end_pos = f"{pos}+{len(keyword)}c"
            log_display.tag_add("highlight", pos, end_pos)
            start = end_pos
        log_display.tag_config("highlight", background="#444444", foreground="yellow")

    def open_in_folder():
        if not selected_file.get():
            return
        path = os.path.join(log_dir, selected_file.get())
        if os.path.exists(path):
            subprocess.Popen(f'explorer /select,"{os.path.abspath(path)}"')

    def delete_log():
        if not selected_file.get():
            return
        path = os.path.join(log_dir, selected_file.get())
        if os.path.exists(path):
            os.remove(path)
            refresh_list()
            log_display.delete("1.0", "end")

    listbox.bind("<<ListboxSelect>>", lambda e: load_selected())

    button_frame = tk.Frame(frame, bg="#1e1e1e")
    button_frame.pack(fill="x", pady=(6, 0))

    tk.Button(button_frame, text="🔍 Search", command=search_logs, bg="#3a3a3a", fg="white", font=("Segoe UI", 10)).pack(side="left", padx=4)
    tk.Button(button_frame, text="📁 Open Location", command=open_in_folder, bg="#3a3a3a", fg="white", font=("Segoe UI", 10)).pack(side="left", padx=4)
    tk.Button(button_frame, text="🗑 Delete", command=delete_log, bg="#aa3333", fg="white", font=("Segoe UI", 10)).pack(side="left", padx=4)
    tk.Button(button_frame, text="🔄 Refresh", command=refresh_list, bg="#3a3a3a", fg="white", font=("Segoe UI", 10)).pack(side="left", padx=4)

    refresh_list()
    return frame