# =============================
# CUSTOM THEME CONFIGURATION
# =============================
custom_theme = {
    "window_bg": "#00775D",             # Main window background
    "text_color": "#FFFFFF",            # Default text color
    "label_color": "#FFFFFF",           # Label text color
    "button_bg": "#009EB3",             # Button background
    "button_hover": "#44B8DB",          # Button hover background, usually brighter than background
    "button_pressed": "#056E97",        # Button pressed background, usually darker than background
    "button_hover_border": "#8BE4FF",   # Button hover border
    "button_pressed_border": "#045369", # Button pressed border
    "button_text": "#FFFFFF",           # Button text color
    "button_border": "#FFFFFF",         # Button border color
    "border_radius": "8px",               # Button roundness
    "font_family": "Calibri",             # Font type
    "font_size": "14px",                  # Font size
    "font_style": "italic"
}

class Themes():
    def __init__(self):
        self.default = ""
        
        self.heap = """
            /* ==============================
            Heap Theme - PyQt6
            Industrial greyscale, smog + scrap aesthetic
            Fonts: OCR A Extended (or fallback to Bahnschrift/Consolas)
            ============================== */

            QWidget {
                background-color: #1c1c1c;       /* dark steel */
                color: #e0e0e0;                  /* pale grey text */
                font-family: "OCR A Extended", "Bahnschrift SemiBold", "Consolas", monospace;
                font-size: 14px;
            }

            QPushButton {
                background-color: #2b2b2b;
                color: #f0f0f0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 1px;             /* stamped industrial spacing */
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border: 1px solid #888;
            }
            QPushButton:pressed {
                background-color: #262626;
                border: 1px solid #aaa;
            }

            QLabel {
                color: #d6d6d6;
                font-family: "OCR A Extended", "Bahnschrift SemiBold", "Consolas", monospace;
            }
            QLabel[warning="true"] {
                color: #d17f21;                  /* rust orange */
                font-weight: bold;
                letter-spacing: 2px;
            }

            QLineEdit {
                background-color: #2a2a2a;
                border: 1px solid #555;
                color: #f0f0f0;
                padding: 4px;
                border-radius: 3px;
                font-family: "OCR A Extended", "Consolas", monospace;
            }
            QLineEdit:focus {
                border: 1px solid #d17f21;
            }

            QTabBar::tab {
                background: #2b2b2b;
                color: #ccc;
                padding: 6px 12px;
                border: 1px solid #444;
                border-bottom: none;
                font-family: "OCR A Extended", "Bahnschrift SemiBold", monospace;
                letter-spacing: 1px;
            }
            QTabBar::tab:selected {
                background: #3a3a3a;
                color: #fff;
                border-top: 2px solid #d17f21;
            }
            QTabBar::tab:hover {
                background: #333;
            }
        """

        self.night = """
            /* ==============================
            Night Theme - PyQt6
            Starry night, soft moonlight, subtle glow
            Font recommendation: "Segoe UI", "Inter", or serif for headings
            ============================== */

            /* Base window */
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #041029, stop:0.5 #091633, stop:1 #0f1b3a);
                color: #E6F0FF; /* starlight text */
                font-family: "Segoe UI", "Inter", Arial, sans-serif;
                font-size: 12px;
            }

            /* Group boxes / Frames */
            QGroupBox {
                margin-top: 12px;
                border: 1px solid rgba(230,240,255,0.08);
                border-radius: 10px;
                background: rgba(255,255,255,0.02);
                padding: 8px;
                font-weight: 600;
            }

            /* Titles */
            QGroupBox:title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #DCE9FF;
                font-size: 13px;
            }

            /* Buttons */
            QPushButton {
                border-radius: 8px;
                padding: 6px 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 rgba(110,140,255,0.12), stop:1 rgba(70,100,200,0.06));
                border: 1px solid rgba(200,220,255,0.09);
                color: #E9F3FF;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 rgba(150,175,255,0.18), stop:1 rgba(100,130,230,0.09));
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 rgba(90,115,220,0.22), stop:1 rgba(60,90,190,0.12));
            }

            /* Primary / accent buttons */
            QPushButton.primary {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #7FB3FF, stop:1 #A0E0FF);
                color: #052037;
                border: 1px solid rgba(255,255,255,0.12);
                font-weight: 700;
            }

            /* Tab widget */
            QTabWidget::pane {
                border: 0;
                background: transparent;
            }
            QTabBar::tab {
                background: transparent;
                padding: 8px 10px;
                margin: 2px;
                border-radius: 8px;
                color: #CFE7FF;
            }
            QTabBar::tab:selected {
                background: rgba(150,180,255,0.08);
                color: #EAF6FF;
                font-weight: 700;
            }

            /* Labels and headers */
            QLabel {
                color: #E6F0FF;
                background: transparent;
            }

            QLabel.header {
                font-size: 14px;
                font-weight: 700;
                color: #F2FBFF;
            }

            /* Line edits / text fields */
            QLineEdit, QTextEdit, QPlainTextEdit {
                border: 1px solid rgba(200,220,255,0.06);
                border-radius: 8px;
                background: rgba(255,255,255,0.01);
                padding: 6px;
                selection-background-color: rgba(160,210,255,0.25);
                color: #EAF6FF;
            }

            /* ComboBoxes */
            QComboBox {
                border: 1px solid rgba(200,220,255,0.06);
                border-radius: 8px;
                padding: 4px 8px;
                background: rgba(255,255,255,0.01);
                color: #E6F0FF;
            }
            QComboBox::drop-down { border: none; }

            /* Checkboxes & Radio */
            QCheckBox, QRadioButton {
                color: #DCEEFF;
                background: transparent;
            }

            /* Tooltips */
            QToolTip {
                background-color: #081428;
                color: #E6F0FF;
                border: 1px solid rgba(200,220,255,0.06);
                padding: 6px;
                border-radius: 6px;
            }

            /* Scrollbars */
            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 12px 0 12px 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(180,205,255,0.08);
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line, QScrollBar::sub-line { height: 0; }

            /* Menus */
            QMenuBar { background: transparent; color: #DDEFFF; }
            QMenu { background: #071028; color: #E6F0FF; border: 1px solid rgba(200,220,255,0.05); }

            /* Status bar */
            QStatusBar {
                background: transparent;
                color: #CFE8FF;
            }

            /* Small decorative "star" accent - use on small labels/buttons via .star */
            .star {
                background: qradialgradient(cx:0.5, cy:0.3, radius:1.0,
                                            fx:0.5, fy:0.3,
                                            stop:0 #FFFFFF, stop:0.08 rgba(255,255,255,0.9),
                                            stop:1 rgba(255,255,255,0.02));
                border-radius: 6px;
                padding: 4px;
                color: #001226;
                font-weight: 700;
            }
        """     

        self.celestia =  """
            /* ==============================
            Celestia Depths Theme - PyQt6
            Inspired by the deep sea, submerged ruins, and astral magic.
            Font: sans-serif (for a clear, astral aesthetic)
            ============================== */

            /* Base widget background */
            QWidget {
                background-color: #0D1B2A;      /* Deep ocean blue */
                color: #A2D5F2;                /* Glowing aqua text */
                font-family: "Verdana", "Geneva", "Tahoma", sans-serif;
                font-size: 14px;
            }

            /* Buttons */
            QPushButton {
                background-color: #1B263B;      /* Darker sea floor */
                color: #F0F4F8;                /* Starlight white */
                border: 2px solid #415A77;      /* Watery blue border */
                border-radius: 8px;             /* Rounded, bubble-like */
                padding: 6px 12px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #415A77;      /* Lighter water */
                border: 2px solid #FF6B6B;      /* Glowing coral */
            }
            QPushButton:pressed {
                background-color: #0D1B2A;      /* Deepest ocean */
                border: 2px solid #E05050;      /* Deeper coral */
                color: #A2D5F2;
            }

            /* Labels */
            QLabel {
                color: #FF6B6B;                /* Vibrant coral */
                background-color: transparent; /* No background */
                font-size: 15px;
                font-weight: bold;
            }

            /* Line edits (text boxes) */
            QLineEdit {
                background-color: #1B263B;      /* Dark sea floor inlay */
                color: #A2D5F2;
                border: 1px solid #415A77;      /* Watery outline */
                border-radius: 6px;
                padding: 4px;
            }
            QLineEdit:focus {
                border: 2px solid #FF6B6B;      /* Focused coral glow */
                background-color: #2A3B52;
            }

            /* Tabs */
            QTabBar::tab {
                font-size: 11px; /* Smaller font for tabs */
            }

            /* ComboBox */
            QComboBox {
                background-color: #1B263B;
                color: #A2D5F2;
                border: 1px solid #415A77;
                border-radius: 6px;
                padding: 4px;
            }
            QComboBox:hover {
                background-color: #415A77;
            }
            QComboBox::drop-down {
                border: none;
            }

            /* Scrollbars */
            QScrollBar:vertical {
                background: #0D1B2A;           /* Deep ocean */
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #415A77;           /* Watery handle */
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #FF6B6B;           /* Glowing coral handle */
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
            }

            /* Progress Bar (Mana) */
            QProgressBar {
                border: 2px solid #415A77;
                border-radius: 8px;
                text-align: center;
                color: #FFFFFF;
                background-color: #1B263B;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #FF6B6B;      /* Solid coral chunk */
                border-radius: 6px;
            }
        """

        self.mooshu = """
            /* ==============================
            Jade Palace Theme - PyQt6 (Mooshu)
            Inspired by imperial red lacquer, jade, and gold accents.
            Font: cursive (for a calligraphic, elegant feel)
            ============================== */

            /* Base widget background */
            QWidget {
                background-color: #2A3D2F;      /* Deep jade green */
                color: #EAE0C8;                /* Aged parchment text */
                font-family: "Lucida Handwriting", "Brush Script MT", cursive;
                font-size: 16px;
            }

            /* Buttons */
            QPushButton {
                background-color: #982B2B;      /* Imperial red lacquer */
                color: #FFFFFF;                /* Clean white text */
                border: 2px solid #C9A86B;      /* Muted gold border */
                border-radius: 8px;             /* Smoother, rounded corners */
                padding: 6px 14px;
                font-size: 17px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #B04A4A;      /* Lighter, glowing red */
                border: 2px solid #FFD700;      /* Bright, shining gold */
            }
            QPushButton:pressed {
                background-color: #782222;      /* Deeper lacquer red */
                border: 2px solid #B8860B;      /* Darker gold */
                color: #EAE0C8;
            }

            /* Labels */
            QLabel {
                color: #FFD700;                /* Imperial gold */
                background-color: transparent;
                font-size: 16px;
                font-weight: bold;
            }

            /* Line edits (text boxes) */
            QLineEdit {
                background-color: #29332B;      /* Dark jade slate */
                color: #EAE0C8;
                border: 1px solid #556B5A;      /* Jade outline */
                border-radius: 6px;
                padding: 4px;
            }
            QLineEdit:focus {
                border: 2px solid #FFD700;      /* Focused gold glow */
                background-color: #333F36;
            }

            /* Tabs and Frames */
            QTabBar::tab {
                background: #4A5D53;
                color: #EAE0C8;
                padding: 8px;
                font-size: 11px; /* Smaller font for tabs */
                border: 1px solid #556B5A;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background: #2A3D2F; /* Match main background */
                color: #FFD700; /* Gold for selected tab */
            }
            QTabWidget::pane {
                border: 1px solid #556B5A;
                border-top: none;
            }

            /* ComboBox */
            QComboBox {
                background-color: #29332B;
                color: #EAE0C8;
                border: 1px solid #556B5A;
                border-radius: 6px;
                padding: 4px;
            }
            QComboBox:hover {
                background-color: #333F36;
            }
            QComboBox::drop-down {
                border: none;
            }

            /* Scrollbars */
            QScrollBar:vertical {
                background: #2A3D2F;           /* Deep jade green */
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #556B5A;           /* Jade handle */
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #FFD700;           /* Gold handle on hover */
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
            }

            /* Progress Bar */
            QProgressBar {
                border: 2px solid #C9A86B;      /* Gold border */
                border-radius: 8px;
                text-align: center;
                color: #1A1411;                /* Darkest brown for legibility */
                background-color: #29332B;      /* Dark Jade */
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #556B5A;      /* Solid Jade chunk */
                border-radius: 6px;
            }
        """     

        self.custom_theme = self.build_stylesheet(custom_theme)

    def build_stylesheet(self, custom_theme):
        return f"""
        QWidget {{
            background-color: {custom_theme['window_bg']};
            color: {custom_theme['text_color']};
            font-family: {custom_theme['font_family']};
            font-size: {custom_theme['font_size']};
            font-style: {custom_theme['font_style']};
        }}

        QLabel {{
            color: {custom_theme['label_color']};
        }}

        QPushButton {{
            background-color: {custom_theme['button_bg']};
            color: {custom_theme['button_text']};
            border-radius: {custom_theme['border_radius']};
            padding: 6px 12px;
            border: 2px solid {custom_theme['button_border']};
        }}
        QPushButton:hover {{
            background-color: {custom_theme['button_hover']};
            border: 2px solid {custom_theme['button_hover_border']};
        }}
        QPushButton:pressed {{
            background-color: {custom_theme['button_pressed']};
            border: 2px solid {custom_theme['button_pressed_border']};
        }}
        """