# ============================================================
# ui/round_selection_screen.py — Choix de la manche de départ
# ============================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COLOR_GREEN, COLOR_BLEU, COLOR_ROUGE

class RoundSelectionScreen(QWidget):
    """
    Écran pour choisir par quelle manche commencer la partie.
    """
    
    # Signal émis quand l'utilisateur a choisi une manche (index 0 à 5)
    round_selected = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_waiting_mode = False
        self._setup_ui()
        
    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(20)
        self.setStyleSheet("background: #0a0a0a;")
        
        # ── Titre ────────────────────────────────────────
        self.title = QLabel("🎯 SÉLECTION DE LA MANCHE")
        self.title.setStyleSheet(f"color: {COLOR_GREEN}; font-size: 28px; font-weight: 900; letter-spacing: 2px;")
        self.title.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.title)
        
        self.subtitle = QLabel("Par quelle position souhaitez-vous commencer le match ?")
        self.subtitle.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 16px;")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.subtitle)
        
        self.main_layout.addSpacing(30)
        
        # ── Boutons de manches ───────────────────────────
        self.button_frame = QFrame()
        grid = QGridLayout(self.button_frame)
        grid.setSpacing(15)
        
        rounds_info = [
            (0,  "Round 1 (Défenseurs)", "5 joueurs : Questions de football", "#4CAF50"),
            (5,  "Round 2 (Milieux)", "6 joueurs : Images IA & Événements", "#FF9800"),
            (11, "Round 3 (Attaquants)", "3 joueurs : Historique de transferts", "#F44336"),
            (14, "Final (Gardien)", "1 joueur : Qui suis-je ? (Indices)", COLOR_BLEU)
        ]
        
        for idx, (r_idx, r_name, r_pos, color) in enumerate(rounds_info):
            btn = QPushButton(f"{r_name}\n\n{r_pos}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(30, 30, 30, 0.8);
                    border: 2px solid {color};
                    border-radius: 12px;
                    color: white;
                    padding: 20px;
                    font-size: 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {color};
                    color: black;
                }}
            """)
            btn.setMinimumHeight(120)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, i=r_idx: self._on_round_click(i))
            
            row = idx // 2
            col = idx % 2
            grid.addWidget(btn, row, col)
            
        self.main_layout.addWidget(self.button_frame)
        self.main_layout.addStretch()
        
    def _on_round_click(self, round_index: int):
        if not self.is_waiting_mode:
            self.round_selected.emit(round_index)
        
    def set_waiting_mode(self, is_waiting: bool):
        """Met l'écran en mode attente (pour le Joueur 1)"""
        self.is_waiting_mode = is_waiting
        if is_waiting:
            self.title.setText("⏳ EN ATTENTE DE L'ADVERSAIRE")
            self.title.setStyleSheet(f"color: {COLOR_ROUGE}; font-size: 28px; font-weight: 900; letter-spacing: 2px;")
            self.subtitle.setText("L'adversaire est en train de choisir la manche de départ ...")
            self.button_frame.setVisible(False)
        else:
            self.title.setText("🎯 SÉLECTION DE LA MANCHE")
            self.title.setStyleSheet(f"color: {COLOR_GREEN}; font-size: 28px; font-weight: 900; letter-spacing: 2px;")
            self.subtitle.setText("Par quelle position souhaitez-vous commencer le match ?\n\n(C'est vous qui avez accepté l'invitation, vous choisissez !)")
            self.button_frame.setVisible(True)
