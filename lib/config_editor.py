import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil
import re
from datetime import datetime
from difflib import unified_diff

def get_frame(master):
    frame = tk.Frame(master, bg="#1e1e1e", padx=10, pady=10)
    current_file = {"path": None, "original": ""}
    theme = {"dark": True}

    LIGHT = {
        "bg": "#f0f0f0",
        "fg": "#000000",
        "text_bg": "#ffffff",
        "text_fg": "#000000",
        "insert": "#000000",
        "highlight": "#cceeff",
        "comment": "#888888",
        "keyword": "#0000cc",
        "quote": "#990000",
        "status": "#e0e0e0",
    }

    DARK = {
        "bg": "#1e1e1e",
        "fg": "#ffffff",
        "text_bg": "#252526",
        "text_fg": "#ffffff",
        "insert": "#ffffff",
        "highlight": "#444444",
        "comment": "#888888",
        "keyword": "#1ec6ff",
        "quote": "#ffa500",
        "status": "#2d2d2d",
    }

    def get_colors():
        return DARK if theme["dark"] else LIGHT

    def highlight_syntax(event=None):
        c = get_colors()
        text.tag_remove("keyword", "1.0", "end")
        text.tag_remove("comment", "1.0", "end")
        text.tag_remove("quote", "1.0", "end")
        for i, line in enumerate(text.get("1.0", "end-1c").split("\n"), 1):
            if "//" in line:
                start = line.index("//")
                text.tag_add("comment", f"{i}.{start}", f"{i}.end")
            for match in re.finditer(r'"[^"]+"', line):
                text.tag_add("quote", f"{i}.{match.start()}", f"{i}.{match.end()}")
            for kw in ("set", "bind", "exec", "map_rotate"):
                for match in re.finditer(rf"\b{kw}\b", line):
                    text.tag_add("keyword", f"{i}.{match.start()}", f"{i}.{match.end()}")
        text.tag_config("keyword", foreground=c["keyword"])
        text.tag_config("comment", foreground=c["comment"])
        text.tag_config("quote", foreground=c["quote"])

    tk.Label(frame, text="📝 Config Editor", font=("Segoe UI", 14, "bold"),
             fg=get_colors()["fg"], bg=get_colors()["bg"]).pack(pady=(0, 10))

    text_frame = tk.Frame(frame, bg=get_colors()["bg"])
    text_frame.pack(fill="both", expand=True)

    v_scroll = tk.Scrollbar(text_frame)
    v_scroll.pack(side="right", fill="y")

    h_scroll = tk.Scrollbar(text_frame, orient="horizontal")
    h_scroll.pack(side="bottom", fill="x")

    text = tk.Text(
        text_frame,
        bg=get_colors()["text_bg"], fg=get_colors()["text_fg"], insertbackground=get_colors()["insert"],
        font=("Consolas", 10), undo=True, wrap="none",
        yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set
    )
    text.pack(side="left", fill="both", expand=True)
    v_scroll.config(command=text.yview)
    h_scroll.config(command=text.xview)

    text.bind("<KeyRelease>", highlight_syntax)
    text.bind("<Control-z>", lambda e: text.edit_undo())
    text.bind("<Control-y>", lambda e: text.edit_redo())

    # === Search & Replace ===
    search_frame = tk.Frame(frame, bg=get_colors()["bg"])
    search_frame.pack(fill="x", pady=(5, 5))

    tk.Label(search_frame, text="Find:", bg=get_colors()["bg"], fg=get_colors()["fg"]).pack(side="left", padx=(3, 0))
    search_var = tk.StringVar()
    tk.Entry(search_frame, textvariable=search_var, width=20,
             font=("Segoe UI", 10), bg="#2b2b2b", fg="white", insertbackground="white").pack(side="left", padx=3)

    tk.Label(search_frame, text="Replace:", bg=get_colors()["bg"], fg=get_colors()["fg"]).pack(side="left", padx=(10, 0))
    replace_var = tk.StringVar()
    tk.Entry(search_frame, textvariable=replace_var, width=20,
             font=("Segoe UI", 10), bg="#2b2b2b", fg="white", insertbackground="white").pack(side="left", padx=3)

    def search_text():
        text.tag_remove("highlight", "1.0", "end")
        term = search_var.get()
        if not term:
            return
        start = "1.0"
        while True:
            pos = text.search(term, start, stopindex="end")
            if not pos:
                break
            end_pos = f"{pos}+{len(term)}c"
            text.tag_add("highlight", pos, end_pos)
            start = end_pos
        text.tag_config("highlight", background=get_colors()["highlight"], foreground="yellow")

    def replace_text():
        term = search_var.get()
        repl = replace_var.get()
        content = text.get("1.0", "end").replace(term, repl)
        text.delete("1.0", "end")
        text.insert("1.0", content)
        text.tag_remove("highlight", "1.0", "end")
        update_status()

    # === File Operations ===
    def open_cfg():
        path = filedialog.askopenfilename(filetypes=[("Config Files", "*.cfg")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            current_file["path"] = path
            current_file["original"] = content
            text.delete("1.0", "end")
            text.insert("1.0", content)
            highlight_syntax()
            update_status()

    def save_cfg():
        if not current_file["path"]:
            return save_as()
        diff_and_confirm()

    def save_as():
        path = filedialog.asksaveasfilename(defaultextension=".cfg", filetypes=[("Config Files", "*.cfg")])
        if path:
            current_file["path"] = path
            do_save()

    def do_save():
        content = text.get("1.0", "end")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        os.makedirs("cfg_backups", exist_ok=True)
        backup_name = f"{os.path.basename(current_file['path']).replace('.cfg', '')}_{timestamp}.cfg"
        if os.path.exists(current_file["path"]):
            shutil.copy(current_file["path"], os.path.join("cfg_backups", backup_name))
        with open(current_file["path"], "w", encoding="utf-8") as f:
            f.write(content)
        current_file["original"] = content
        update_status()
        messagebox.showinfo("Saved", f"Saved to {current_file['path']}\nBackup: {backup_name}")

    def diff_and_confirm():
        original_lines = current_file["original"].splitlines(keepends=True)
        new_lines = text.get("1.0", "end").splitlines(keepends=True)
        diff = list(unified_diff(original_lines, new_lines, fromfile='original', tofile='current'))
        if not diff:
            do_save()
            return
        confirm = messagebox.askyesno("Review Changes", "Changes detected. View diff before saving?")
        if confirm:
            diff_win = tk.Toplevel()
            diff_win.title("Diff Preview")
            diff_text = tk.Text(diff_win, bg="black", fg="white", font=("Consolas", 10))
            diff_text.pack(fill="both", expand=True)
            diff_text.insert("1.0", "".join(diff))
            diff_text.config(state="disabled")
        else:
            do_save()

    def toggle_theme():
        theme["dark"] = not theme["dark"]
        frame.destroy()
        new_frame = get_frame(master)
        new_frame.pack(fill="both", expand=True)

    # === Toolbar ===
    toolbar = tk.Frame(frame, bg=get_colors()["bg"])
    toolbar.pack(fill="x", pady=(5, 5))

    tk.Button(toolbar, text="📂 Open", bg="#3a3a3a", fg="white", font=("Segoe UI", 10), command=open_cfg).pack(side="left", padx=5)
    tk.Button(toolbar, text="💾 Save", bg="#3a3a3a", fg="white", font=("Segoe UI", 10), command=save_cfg).pack(side="left", padx=5)
    tk.Button(toolbar, text="📝 Save As", bg="#3a3a3a", fg="white", font=("Segoe UI", 10), command=save_as).pack(side="left", padx=5)
    tk.Button(toolbar, text="🔎 Find", bg="#3a3a3a", fg="white", font=("Segoe UI", 10), command=search_text).pack(side="left", padx=5)
    tk.Button(toolbar, text="♻ Replace", bg="#3a3a3a", fg="white", font=("Segoe UI", 10), command=replace_text).pack(side="left", padx=5)
    tk.Button(toolbar, text="🌗 Toggle Theme", bg="#3a3a3a", fg="white", font=("Segoe UI", 10), command=toggle_theme).pack(side="left", padx=5)

    # === Status Bar ===
    status_var = tk.StringVar()
    status_bar = tk.Label(frame, textvariable=status_var, anchor="w",
                          font=("Segoe UI", 9), bg=get_colors()["status"], fg="gray")
    status_bar.pack(fill="x", side="bottom", pady=(5, 0))

    def update_status():
        status = current_file["path"] or "No file loaded"
        modified = "(modified)" if text.get("1.0", "end") != current_file["original"] else ""
        status_var.set(f"{status} {modified}")

    def warn_unsaved_close():
        current = text.get("1.0", "end")
        if current != current_file["original"]:
            if not messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Close anyway?"):
                return
        frame.destroy()

    frame.protocol = warn_unsaved_close
    return frame
