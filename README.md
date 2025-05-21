# 🛠 HMW Server Manager

A server manager for HMW Servers. Easily manage multiple dedicated servers with integrated logging, tabbed instances, memory/CPU monitoring, and persistent configuration.

---

## 📸 Features

- 🎛 **Tabbed interface** – run and manage multiple servers in parallel
- 🧠 **Memory and CPU graphs** – real-time usage per server tab
- 📁 **Integrated logs** – live output and per-tab export
- ⚙️ **Auto-save sessions** – restores all tabs on restart
- 🔁 **Restart All** – instantly restart all active servers
- 📂 **Open Logs Folder** – jump to log directory from the UI

---

## 📦 Requirements

- Python 3.10+
- `psutil`
- `matplotlib`
- `mplcursors`

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🚀 Getting Started

1. Clone the repository:

```bash
git clone https://github.com/PureIsntHere/HMWServerManager.git
cd hmw-server-manager
```

2. Launch the manager:

```bash
python main.py
```

3. In the GUI, create a new server tab and configure:
   - Path to `hmw-mod.exe`
   - Path to `server-default.cfg`
   - Unique server port (e.g. 27016, 27017...)

---

## 📂 Project Structure

```
HMWServerManager/
├── main.py                 # Entry point
├── lib/
│   ├── manager.py          # Main window + tab logic
│   └── server_tab.py       # Per-tab server + graph UI
├── cfg/                    # Auto-saved session config
├── logs/                   # Server log exports
└── requirements.txt        # Python dependencies
```

---


![image](https://github.com/user-attachments/assets/51fd2b4f-641b-453f-b56f-25bbb3666d0f)


---

## 💡 Notes

- Each server must run on a **unique port**
- server configs must reside in the same folder as `hmw-mod.exe`
---
