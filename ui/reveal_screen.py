# ============================================================
# ui/reveal_screen.py — Révélation finale des ratings + vainqueur
# ============================================================

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore    import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui     import QPixmap, QIcon
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COLOR_GREEN, COLOR_ROUGE, COLOR_BLEU
from ui.widgets import ExitButton, TeamLineupPanel

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))




class RevealScreen(QWidget):
    """
    Écran de révélation finale :
    1. Reveal progressif des cartes (une par une, avec délai)
    2. Apparition des totaux
    3. Animation vainqueur
    4. Bouton rejouer
    """

    play_again = pyqtSignal()
    exit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # Fond (backgroundexchangetfinal.png)
        self.bg_lbl = QLabel(self)
        self.bg_lbl.setScaledContents(True)
        bg_path = os.path.join(BASE, "backgroundexchangetfinal.png")
        if os.path.exists(bg_path):
            self.bg_lbl.setPixmap(QPixmap(bg_path))

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── Header ───────────────────────────────────────
        header_container = QWidget()
        header_container.setFixedHeight(120)
        header = QHBoxLayout(header_container)
        header.setContentsMargins(40, 20, 40, 0)

        # Spacer gauche pour équilibrer le bouton quitter
        header.addSpacing(110) 
        header.addStretch()

        logo_lbl = QLabel()
        logo_path = os.path.join(BASE, "Gemini_Generated_Image_w4q5buw4q5buw4q5-removebg-preview.png")
        if os.path.exists(logo_path):
            logo_lbl.setPixmap(QPixmap(logo_path).scaledToHeight(110, Qt.SmoothTransformation))
        logo_lbl.setStyleSheet("background: transparent; border: none;")
        logo_lbl.setAlignment(Qt.AlignCenter)
        header.addWidget(logo_lbl)

        header.addStretch()

        self.exit_btn = ExitButton()
        self.exit_btn.clicked.connect(self.exit_requested.emit)
        header.addWidget(self.exit_btn)
        
        header_container.setStyleSheet("background: transparent; border: none;")
        main_lay.addWidget(header_container)

        # ── Contenu central (Layout VS) ──────────────────
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        # Spacer gauche (Joueur Bleu) - Translation vers le centre
        content.addStretch(25)

        # Panneau Bleu
        self.panel_bleu = TeamLineupPanel("bleu")
        content.addWidget(self.panel_bleu, 3)

        # Zone centrale (VS + Scores)
        mid_container = QWidget()
        mid = QVBoxLayout(mid_container)
        mid.setAlignment(Qt.AlignCenter)
        mid.setSpacing(10)
        
        self.vs_lbl = QLabel("VS")
        self.vs_lbl.setStyleSheet(
            "color: white; font-size: 110px; font-weight: 900; "
            "background: transparent; border: none; font-style: italic;"
        )
        mid.addWidget(self.vs_lbl)

        # Affichage scores totaux comparés
        self.total_scores_lbl = QLabel("00 - 00")
        self.total_scores_lbl.setStyleSheet(
            "color: #ffd700; font-size: 48px; font-weight: 900; "
            "background: transparent; letter-spacing: 5px;"
        )
        self.total_scores_lbl.setAlignment(Qt.AlignCenter)
        mid.addWidget(self.total_scores_lbl)

        content.addWidget(mid_container, 3)

        # Panneau Rouge
        self.panel_rouge = TeamLineupPanel("rouge")
        content.addWidget(self.panel_rouge, 3)

        # Spacer droite (Joueur Rouge) - Translation vers le centre
        content.addStretch(25)

        main_lay.addLayout(content, 1)

        # ── Footer (Winner announcement) ─────────────────
        footer = QVBoxLayout()
        footer.setContentsMargins(0, 0, 0, 40)
        footer.setSpacing(10)
        footer.setAlignment(Qt.AlignCenter)

        self.winner_msg_lbl = QLabel("THE WINNER IS")
        self.winner_msg_lbl.setStyleSheet(
            "color: rgba(255, 255, 255, 0.7); font-size: 28px; font-weight: 900; "
            "letter-spacing: 8px; background: transparent;"
        )
        self.winner_msg_lbl.setAlignment(Qt.AlignCenter)
        footer.addWidget(self.winner_msg_lbl)

        self.winner_name_lbl = QLabel("")
        self.winner_name_lbl.setMinimumWidth(600) # Évite les coupures
        self.winner_name_lbl.setAlignment(Qt.AlignCenter)
        self.winner_name_lbl.setStyleSheet(
            "color: #ffd700; font-size: 38px; font-weight: 900; "
            "letter-spacing: 4px; background: transparent; "
            "text-transform: uppercase;"
        )
        footer.addWidget(self.winner_name_lbl)
        
        footer.addSpacing(30) # Espace avant le bouton rejouer

        self.replay_btn = QPushButton()
        self.replay_btn.setFixedSize(250, 210)
        self.replay_btn.setCursor(Qt.PointingHandCursor)
        self.replay_btn.setStyleSheet("background: transparent; border: none;")
        
        replay_img_path = os.path.join(BASE, "Gemini_Generated_Image_8m8qbt8m8qbt8m8q-removebg-preview.png")
        if os.path.exists(replay_img_path):
            self.replay_btn.setIcon(QIcon(replay_img_path))
            self.replay_btn.setIconSize(QSize(250, 210))
        else:
            self.replay_btn.setText("🔄 REJOUER")
            self.replay_btn.setStyleSheet("color: white; font-weight: bold; background: #333; border-radius: 10px;")

        self.replay_btn.clicked.connect(self.play_again.emit)
        self.replay_btn.setVisible(False)
        footer.addWidget(self.replay_btn, 0, Qt.AlignCenter)

        main_lay.addLayout(footer)

    def resizeEvent(self, event):
        self.bg_lbl.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def load(self, game_state):
        """Affiche les scores finaux et le vainqueur"""
        game_state.start_reveal()
        
        r_total = game_state.team_rouge.total_rating
        b_total = game_state.team_bleu.total_rating
        winner_color = game_state.get_winner()

        self.panel_bleu.load(game_state.team_bleu, score=b_total, is_winner=(winner_color == "bleu"), show_ratings=True)
        self.panel_rouge.load(game_state.team_rouge, score=r_total, is_winner=(winner_color == "rouge"), show_ratings=True)

        self.total_scores_lbl.setText(f"{b_total} - {r_total}")

        if winner_color == "egalite":
            self.winner_name_lbl.setText("DRAW MATCH !")
            self.winner_name_lbl.setStyleSheet("color: white; font-size: 54px; font-weight: 900; letter-spacing: 8px;")
        else:
            win_team = game_state.get_team(winner_color)
            self.winner_name_lbl.setText(win_team.name.upper())
            color = COLOR_ROUGE if winner_color == "rouge" else COLOR_BLEU
            self.winner_name_lbl.setStyleSheet(f"color: {color}; font-size: 42px; font-weight: 900; letter-spacing: 5px;")

        self.replay_btn.setVisible(True)
