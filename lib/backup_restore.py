import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil
from datetime import datetime

def get_frame(master):
    frame = tk.Frame(master, bg="#1e1e1e", padx=20, pady=20)

    tk.Label(frame, text="🗃 Backup & Restore Configs", font=("Segoe UI", 14, "bold"),
             fg="white", bg="#1e1e1e").pack(pady=(0, 10))

    os.makedirs("cfg_backups", exist_ok=True)

    backup_listbox = tk.Listbox(frame, bg="#252526", fg="white", font=("Consolas", 10), height=10)
    backup_listbox.pack(fill="x", pady=(0, 10), expand=False)

    def refresh_list():
        backup_listbox.delete(0, "end")
        for file in sorted(os.listdir("cfg_backups")):
            if file.endswith(".cfg"):
                backup_listbox.insert("end", file)

    def backup_file():
        files = filedialog.askopenfilenames(filetypes=[("CFG Files", "*.cfg")])
        if not files:
            return
        for path in files:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            name = os.path.basename(path).replace(".cfg", "")
            dest = f"cfg_backups/{name}_{timestamp}.cfg"
            shutil.copy2(path, dest)
        messagebox.showinfo("Backup Complete", "Config(s) backed up.")
        refresh_list()

    def restore_file():
        sel = backup_listbox.curselection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a backup to restore.")
            return
        selected = backup_listbox.get(sel[0])
        source = os.path.join("cfg_backups", selected)
        dest = filedialog.asksaveasfilename(defaultextension=".cfg")
        if dest:
            shutil.copy2(source, dest)
            messagebox.showinfo("Restored", f"Config restored to:{dest}")

    def delete_backup():
        sel = backup_listbox.curselection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a backup to delete.")
            return
        selected = backup_listbox.get(sel[0])
        os.remove(os.path.join("cfg_backups", selected))
        refresh_list()
        messagebox.showinfo("Deleted", f"{selected} deleted.")

    tk.Button(frame, text="📥 Backup Config(s)", command=backup_file,
              bg="#3a3a3a", fg="white", font=("Segoe UI", 10)).pack(pady=2, fill="x")

    tk.Button(frame, text="📤 Restore Selected", command=restore_file,
              bg="#3a3a3a", fg="white", font=("Segoe UI", 10)).pack(pady=2, fill="x")

    tk.Button(frame, text="🗑 Delete Selected", command=delete_backup,
              bg="#aa3333", fg="white", font=("Segoe UI", 10)).pack(pady=(2, 6), fill="x")

    refresh_list()
    return frame