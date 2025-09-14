# Raid Utility Tools

A collection of utility tools designed to assist with different **Wizard101 raid instances**.  
Each tool provides quality-of-life features, shortcuts, and client utilities for more efficient raiding.

---

## 🛠️ Development Notes

This project took immense effort — the **UI framework** and the systems that run behind the scenes have been rewritten multiple times to ensure stability, usability, and performance.  

Countless hours went into refining the tools, experimenting with different designs, and improving the overall raid utility framework to make it as reliable and user-friendly as possible.

If you enjoy these tools and would like to support future development,  please consider [buying me a coffee](https://www.buymeacoffee.com/lxghtend). ☕  
Your support means a lot and helps keep this project alive!

---

### 🔹 **ds-tool**  
Utility tool for the **Voracious Void** raid.  
**Raid-specific features:**  
- Power Star utilities  
- Drums  

---

### 🔹 **az-tool**  
Utility tool for the **Crying Sky** raid.  
**Raid-specific features:**  
- Fishing utilities  
- Touchstone locations  
- Cacao Pod utilities
- Misfortune Tear utilities  
- Drums  

---

### 🔹 **pl-tool**
Utility tool for the **Cabal's Revenge** raid.  
**Raid-specific features:**
- Rope utilities
- Catapult utilities
- Cannon utilities

---

### 🔹 **lm-tool**  
Utility tool for the **Ghastly Conspiracy** raid.  
**Raid-specific features:**  
- Chest utilities  
- Tracy utilities  
- Cauldron utilities  

---

## 🧰 Additional Features (Included in All Tools)
- Client renaming
- Client hook management
- Client information  
- Raid specific teleports  
- General utilities    
- Preset themes
- Configurable themes 

---

## ⚙️ Configuration (`config.ini`)

Each tool supports a simple configuration file named **`config.ini`**.  
This file allows you to toggle common settings without modifying code.

Example:

```ini
[General]
always_on_top = True
enable_clients_tab = True
use_raid_theme = True

[Keybinds]
handle_xyz_sync = F3
toggle_speedhack = F4
toggle_freecam = F5
handle_freecam_teleport = F6
toggle_auto_dialogue = F7
```

---

## 🎨 Custom Theme Configuration

All tools support user-defined themes to customize the look and feel of the interface.  
Themes can be configured by editing the **`custom_theme`** dictionary inside the tool’s **`themes.py`** file.

Example (Default Custom Theme):

```python
# =============================
# CUSTOM THEME CONFIGURATION
# =============================
custom_theme = {
    "window_bg": "#00775D",             # Main window background
    "text_color": "#FFFFFF",            # Default text color
    "label_color": "#FFFFFF",           # Label text color
    "button_bg": "#009EB3",             # Button background
    "button_hover": "#44B8DB",          # Button hover background, usually brighter
    "button_pressed": "#056E97",        # Button pressed background, usually darker
    "button_hover_border": "#8BE4FF",   # Button hover border
    "button_pressed_border": "#045369", # Button pressed border
    "button_text": "#FFFFFF",           # Button text color
    "button_border": "#FFFFFF",         # Button border color
    "border_radius": "8px",             # Button roundness
    "font_family": "Calibri",           # Font type
    "font_size": "14px",                # Font size
    "font_style": "italic"              # Font style
}
```

---

## ⚙️ Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/lxghtend/raid-utility-tools.git
cd raid-utility-tools
pip install -r requirements.txt
```

---

## 🚀 Usage

Each tool can be run individually:

```bash
# Voracious Void Raid Tool
python ds-tool/main.py

# Crying Sky Raid Tool
python az-tool/main.py

# Cabal's Revenge Raid Tool
python pl-tool/main.py

# Ghastly Conspiracy Raid Tool
python lm-tool/main.py
```

---

## 📝 Requirements
- Python **3.11+**  
- Dependencies listed in `requirements.txt`

---

## 🤝 Credits
Built and maintained by **Lxghtend**  
- [GitHub](https://github.com/Lxghtend)  
- [Buy Me a Coffee](https://www.buymeacoffee.com/lxghtend)  

WorldsCollideTP built by **CIick**
- [Github](https://github.com/CIick)