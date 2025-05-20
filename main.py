import os
import tkinter as tk
from lib.manager import HMWServerManager

if __name__ == "__main__":
    os.makedirs("cfg", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    root = tk.Tk()
    app = HMWServerManager(root)
    root.mainloop()
