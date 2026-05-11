# ============================================================
# ui/styles.py — Styles QSS dark football theme
# ============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (COLOR_BG, COLOR_GREEN, COLOR_ROUGE, COLOR_BLEU,
                    COLOR_JAUNE, COLOR_GRAY, COLOR_WHITE,
                    COLOR_CARD_BG, COLOR_BORDER)

# Style global de l'application
STYLE_APP = f"""
QMainWindow, QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_WHITE};
    font-family: 'Segoe UI', Arial, sans-serif;
    margin: 0px;
    padding: 0px;
    border: none;
}}

QMenuBar {{
    max-height: 0px;
    height: 0px;
    border: none;
    background: transparent;
    padding: 0px;
    margin: 0px;
}}

QStatusBar {{
    max-height: 0px;
    height: 0px;
    border: none;
    background: transparent;
    padding: 0px;
    margin: 0px;
}}

QStackedWidget {{
    border: none;
    margin: 0px;
    padding: 0px;
    background-color: {COLOR_BG};
}}

QLabel {{
    color: {COLOR_WHITE};
    background-color: transparent;
    border: none;
}}

QPushButton {{
    background-color: {COLOR_CARD_BG};
    color: {COLOR_WHITE};
    border: 2px solid {COLOR_BORDER};
    border-radius: 10px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: #2a2a2a;
    border-color: {COLOR_GREEN};
    color: {COLOR_GREEN};
}}

QPushButton:pressed {{
    background-color: {COLOR_GREEN};
    color: #000000;
}}

QPushButton:disabled {{
    background-color: #111111;
    color: #444444;
    border-color: #222222;
}}

QLineEdit {{
    background-color: {COLOR_CARD_BG};
    color: {COLOR_WHITE};
    border: 2px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 14px;
}}

QLineEdit:focus {{
    border-color: {COLOR_GREEN};
}}

QFrame {{
    background-color: {COLOR_CARD_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
}}

QScrollArea {{
    background-color: transparent;
    border: none;
}}
"""

# Bouton BUZZ rouge
STYLE_BUZZ_ROUGE = f"""
QPushButton {{
    background-color: {COLOR_ROUGE};
    color: white;
    border: none;
    border-radius: 16px;
    font-size: 22px;
    font-weight: 900;
    letter-spacing: 2px;
    padding: 20px 40px;
}}
QPushButton:hover {{
    background-color: #ff6666;
    color: white;
}}
QPushButton:pressed {{
    background-color: #cc0000;
}}
QPushButton:disabled {{
    background-color: #4a1a1a;
    color: #884444;
}}
"""

# Bouton BUZZ bleu
STYLE_BUZZ_BLEU = f"""
QPushButton {{
    background-color: {COLOR_BLEU};
    color: white;
    border: none;
    border-radius: 16px;
    font-size: 22px;
    font-weight: 900;
    letter-spacing: 2px;
    padding: 20px 40px;
}}
QPushButton:hover {{
    background-color: #6699ff;
    color: white;
}}
QPushButton:pressed {{
    background-color: #2255cc;
}}
QPushButton:disabled {{
    background-color: #1a1a4a;
    color: #444488;
}}
"""

# Bouton vert (start, confirm)
STYLE_BTN_GREEN = f"""
QPushButton {{
    background-color: {COLOR_GREEN};
    color: #000000;
    border: none;
    border-radius: 12px;
    font-size: 16px;
    font-weight: 900;
    padding: 14px 36px;
}}
QPushButton:hover {{
    background-color: #33ffaa;
}}
QPushButton:pressed {{
    background-color: #00aa55;
}}
"""

# Carte joueur (pick screen)
STYLE_PLAYER_CARD = f"""
QPushButton {{
    background-color: {COLOR_CARD_BG};
    color: {COLOR_WHITE};
    border: 2px solid #333333;
    border-radius: 16px;
    font-size: 15px;
    font-weight: bold;
    padding: 20px;
    text-align: center;
}}
QPushButton:hover {{
    background-color: #1a2a1a;
    border-color: {COLOR_GREEN};
    color: {COLOR_GREEN};
}}
QPushButton:pressed {{
    background-color: #0a3a0a;
    border-color: {COLOR_GREEN};
}}
"""

# Option de réponse (answer screen)
STYLE_OPTION_BTN = f"""
QPushButton {{
    background-color: {COLOR_CARD_BG};
    color: {COLOR_WHITE};
    border: 2px solid {COLOR_BORDER};
    border-radius: 12px;
    font-size: 15px;
    font-weight: bold;
    padding: 16px 20px;
    text-align: left;
}}
QPushButton:hover {{
    background-color: #1a2a1a;
    border-color: {COLOR_GREEN};
}}
QPushButton:pressed {{
    background-color: {COLOR_GREEN};
    color: #000000;
}}
"""

# Carton jaune
STYLE_JAUNE = f"""
QLabel {{
    background-color: {COLOR_JAUNE};
    color: #000000;
    border-radius: 6px;
    font-weight: 900;
    font-size: 18px;
    padding: 4px 10px;
}}
"""

# Carton rouge
STYLE_ROUGE_CARD = f"""
QLabel {{
    background-color: {COLOR_ROUGE};
    color: white;
    border-radius: 6px;
    font-weight: 900;
    font-size: 18px;
    padding: 4px 10px;
}}
"""

# Titre principal
STYLE_TITLE = f"""
QLabel {{
    color: {COLOR_GREEN};
    font-size: 48px;
    font-weight: 900;
    letter-spacing: 4px;
    background-color: transparent;
}}
"""

# Sous-titre
STYLE_SUBTITLE = f"""
QLabel {{
    color: {COLOR_GRAY};
    font-size: 16px;
    letter-spacing: 2px;
    background-color: transparent;
}}
"""

# Barre de progression manche
STYLE_PROGRESS = f"""
QProgressBar {{
    background-color: #1a1a1a;
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    height: 12px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {COLOR_GREEN};
    border-radius: 6px;
}}
"""

# Panel équipe rouge
STYLE_TEAM_ROUGE = f"""
QFrame {{
    background-color: #1a0a0a;
    border: 2px solid {COLOR_ROUGE};
    border-radius: 14px;
}}
"""

# Panel équipe bleue
STYLE_TEAM_BLEU = f"""
QFrame {{
    background-color: #0a0a1a;
    border: 2px solid {COLOR_BLEU};
    border-radius: 14px;
}}
"""

# --- STYLES MASTERS DRAFT QUIZ ---
STYLE_MASTERS_HEADER = """
QLabel {
    color: #ffd700;
    font-size: 16px;
    font-weight: bold;
    background-color: rgba(20, 30, 40, 0.7);
    border-bottom: 1px solid #333;
    padding: 8px;
    letter-spacing: 2px;
}
"""

STYLE_MANCHE_BAR = """
QLabel {
    background-color: rgba(10, 20, 30, 0.8);
    color: #ddd;
    font-size: 13px;
    font-weight: bold;
    padding: 6px;
    border-top: 1px solid #444;
}
"""

STYLE_BANNER_ROUGE = f"""
QLabel {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4a0000, stop:1 #2a0000);
    color: white;
    font-size: 18px;
    font-weight: 900;
    border: 2px solid #660000;
    border-bottom-left-radius: 25px;
    border-bottom-right-radius: 25px;
    letter-spacing: 2px;
}}
"""

STYLE_BANNER_BLEU = f"""
QLabel {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #00004a, stop:1 #00002a);
    color: white;
    font-size: 18px;
    font-weight: 900;
    border: 2px solid #000066;
    border-bottom-left-radius: 25px;
    border-bottom-right-radius: 25px;
    letter-spacing: 2px;
}}
"""

STYLE_QUESTION_BOX = """
QLabel {
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.8, fx:0.5, fy:0.5, stop:0 #1a1a2a, stop:1 #000000);
    color: #ffffff;
    border: 2px solid #8b7355;
    border-radius: 25px;
    padding: 25px;
    font-size: 20px;
    font-weight: bold;
}
"""

STYLE_OPTION_MASTERS = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e272e, stop:1 #000000);
    color: #ffffff;
    border: 2px solid #485460;
    border-radius: 20px;
    font-size: 15px;
    font-weight: bold;
    padding: 15px 25px;
    text-align: left;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #485460, stop:1 #1e272e);
    border-color: #ffd700;
}
QPushButton:pressed {
    background-color: #ffd700;
    color: #000000;
}
"""

STYLE_GLASS_PANEL = """
    QFrame {
        background: rgba(10, 20, 40, 0.75);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 15px;
    }
"""

STYLE_PREMIUM_CARD = """
    QFrame {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1a2540, stop:1 #0d1525);
        border: 2px solid #00d4ff;
        border-radius: 16px;
    }
"""
