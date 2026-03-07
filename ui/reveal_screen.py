# ============================================================
# ui/reveal_screen.py — Révélation finale des ratings + vainqueur
# ============================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QFrame, QScrollArea,
                              QGridLayout)
from PyQt5.QtCore    import Qt, pyqtSignal, QTimer, QPropertyAnimation, QRect
from PyQt5.QtGui     import QColor, QPainter, QLinearGradient, QFont
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config  import (COLOR_GREEN, COLOR_ROUGE, COLOR_BLEU,
                     COLOR_GRAY, COLOR_CARD_BG)
from ui.widgets import SeparatorLine


class RevealPlayerCard(QFrame):
    """Carte joueur avec animation de révélation du rating"""

    def __init__(self, player, team_color: str, delay_ms: int = 0, parent=None):
        super().__init__(parent)
        self.player     = player
        self.team_color = team_color
        self._revealed  = False
        color = COLOR_ROUGE if team_color == "rouge" else COLOR_BLEU
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #131313;
                border: 2px solid {color};
                border-radius: 14px;
            }}
        """)
        self.setFixedSize(155, 110)
        self._setup_ui(color)
        if delay_ms > 0:
            QTimer.singleShot(delay_ms, self.reveal)

    def _setup_ui(self, color):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(4)

        # Position badge
        pos = QLabel(self.player.position)
        pos.setFixedHeight(20)
        pos.setStyleSheet(f"""
            background: {color}; color: white;
            border-radius: 6px; font-size: 10px;
            font-weight: 800; letter-spacing: 1px;
        """)
        pos.setAlignment(Qt.AlignCenter)
        lay.addWidget(pos)

        # Nom
        name = QLabel(self.player.name)
        name.setStyleSheet(
            "color: white; font-size: 12px; font-weight: bold; "
            "background: transparent; border: none;"
        )
        name.setAlignment(Qt.AlignCenter)
        name.setWordWrap(True)
        lay.addWidget(name)

        # Club
        club = QLabel(self.player.club)
        club.setStyleSheet(
            f"color: {COLOR_GRAY}; font-size: 9px; "
            "background: transparent; border: none;"
        )
        club.setAlignment(Qt.AlignCenter)
        club.setWordWrap(True)
        lay.addWidget(club)

        # Rating (caché au départ)
        self.rating_lbl = QLabel("⭐  ???")
        self.rating_lbl.setStyleSheet(
            f"color: #444444; font-size: 14px; font-weight: 900; "
            "background: transparent; border: none;"
        )
        self.rating_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.rating_lbl)

    def reveal(self):
        """Révèle le rating avec un effet visuel"""
        if self._revealed:
            return
        self._revealed = True
        rating = self.player.get_rating_force()

        # Couleur selon le rating
        if rating >= 88:
            color = "#ffd700"    # Or — élite
        elif rating >= 83:
            color = COLOR_GREEN  # Vert — très bon
        elif rating >= 78:
            color = "#4488ff"    # Bleu — bon
        else:
            color = COLOR_GRAY   # Gris — moyen

        self.rating_lbl.setText(f"⭐  {rating}")
        self.rating_lbl.setStyleSheet(
            f"color: {color}; font-size: 16px; font-weight: 900; "
            "background: transparent; border: none;"
        )

        # Flash du bord
        team_color = COLOR_ROUGE if self.team_color == "rouge" else COLOR_BLEU
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(
                    {'220,30,30' if self.team_color == 'rouge' else '30,80,220'}, 0.15
                );
                border: 2px solid {color};
                border-radius: 14px;
            }}
        """)


class ScoreBanner(QFrame):
    """Bannière de score total d'une équipe avec animation"""

    def __init__(self, team_name: str, color: str, parent=None):
        super().__init__(parent)
        border = COLOR_ROUGE if color == "rouge" else COLOR_BLEU
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {'#1a0a0a' if color == 'rouge' else '#0a0a1a'};
                border: 3px solid {border};
                border-radius: 16px;
            }}
        """)
        self.setFixedHeight(90)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 10, 20, 10)
        lay.setSpacing(4)

        lbl = QLabel(team_name)
        lbl.setStyleSheet(
            f"color: {border}; font-size: 14px; font-weight: 900; "
            "background: transparent; border: none; letter-spacing: 2px;"
        )
        lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl)

        self.score_lbl = QLabel("⭐  Total : Calcul en cours...")
        self.score_lbl.setStyleSheet(
            f"color: {COLOR_GRAY}; font-size: 18px; font-weight: 900; "
            "background: transparent; border: none;"
        )
        self.score_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.score_lbl)

    def set_score(self, total: int, is_winner: bool = False):
        color = COLOR_GREEN if is_winner else "white"
        prefix = "🏆  " if is_winner else "⭐  "
        self.score_lbl.setText(f"{prefix}Total : {total}")
        self.score_lbl.setStyleSheet(
            f"color: {color}; font-size: 22px; font-weight: 900; "
            "background: transparent; border: none;"
        )
        if is_winner:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: #0d2a0d;
                    border: 3px solid {COLOR_GREEN};
                    border-radius: 16px;
                }}
            """)


class RevealScreen(QWidget):
    """
    Écran de révélation finale :
    1. Reveal progressif des cartes (une par une, avec délai)
    2. Apparition des totaux
    3. Animation vainqueur
    4. Bouton rejouer
    """

    play_again = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(30, 20, 30, 20)
        self._root.setSpacing(14)

        # Titre
        self.title_lbl = QLabel("🏆  RÉVÉLATION FINALE")
        self.title_lbl.setStyleSheet(
            f"color: {COLOR_GREEN}; font-size: 28px; font-weight: 900; "
            "background: transparent; letter-spacing: 4px;"
        )
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self._root.addWidget(self.title_lbl)

        self.sub_lbl = QLabel("Les ratings FIFA de tous les joueurs sont révélés !")
        self.sub_lbl.setStyleSheet(
            f"color: {COLOR_GRAY}; font-size: 13px; background: transparent;"
        )
        self.sub_lbl.setAlignment(Qt.AlignCenter)
        self._root.addWidget(self.sub_lbl)

        sep = SeparatorLine()
        self._root.addWidget(sep)

        # Scores en haut
        scores_row = QHBoxLayout()
        scores_row.setSpacing(20)
        self.banner_rouge = ScoreBanner("Équipe Rouge", "rouge")
        self.banner_bleu  = ScoreBanner("Équipe Bleue", "bleu")
        scores_row.addWidget(self.banner_rouge)
        scores_row.addWidget(self.banner_bleu)
        self._root.addLayout(scores_row)

        # Grilles de joueurs
        teams_row = QHBoxLayout()
        teams_row.setSpacing(20)

        # Équipe rouge (gauche)
        rouge_col = QVBoxLayout()
        rouge_title = QLabel("🔴  Équipe Rouge")
        rouge_title.setStyleSheet(
            f"color: {COLOR_ROUGE}; font-size: 15px; font-weight: 900; "
            "background: transparent;"
        )
        rouge_title.setAlignment(Qt.AlignCenter)
        rouge_col.addWidget(rouge_title)
        self.rouge_grid_widget = QWidget()
        self.rouge_grid_lay = QGridLayout(self.rouge_grid_widget)
        self.rouge_grid_lay.setSpacing(8)
        rouge_col.addWidget(self.rouge_grid_widget)
        rouge_col.addStretch()
        teams_row.addLayout(rouge_col)

        # Séparateur central VS
        vs_col = QVBoxLayout()
        vs_col.setAlignment(Qt.AlignCenter)
        self.vs_lbl = QLabel("VS")
        self.vs_lbl.setStyleSheet(
            f"color: {COLOR_GRAY}; font-size: 24px; font-weight: 900; "
            "background: transparent;"
        )
        self.vs_lbl.setAlignment(Qt.AlignCenter)
        vs_col.addWidget(self.vs_lbl)
        teams_row.addLayout(vs_col)

        # Équipe bleue (droite)
        bleu_col = QVBoxLayout()
        bleu_title = QLabel("🔵  Équipe Bleue")
        bleu_title.setStyleSheet(
            f"color: {COLOR_BLEU}; font-size: 15px; font-weight: 900; "
            "background: transparent;"
        )
        bleu_title.setAlignment(Qt.AlignCenter)
        bleu_col.addWidget(bleu_title)
        self.bleu_grid_widget = QWidget()
        self.bleu_grid_lay = QGridLayout(self.bleu_grid_widget)
        self.bleu_grid_lay.setSpacing(8)
        bleu_col.addWidget(self.bleu_grid_widget)
        bleu_col.addStretch()
        teams_row.addLayout(bleu_col)

        self._root.addLayout(teams_row)

        # Bannière vainqueur (cachée au départ)
        self.winner_banner = QLabel("")
        self.winner_banner.setFixedHeight(60)
        self.winner_banner.setStyleSheet(
            "background: transparent; border: none;"
        )
        self.winner_banner.setAlignment(Qt.AlignCenter)
        self.winner_banner.setVisible(False)
        self._root.addWidget(self.winner_banner)

        # Bouton rejouer
        self.replay_btn = QPushButton("🔄   Rejouer une partie !")
        self.replay_btn.setFixedHeight(52)
        self.replay_btn.setVisible(False)
        self.replay_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00b844, stop:1 {COLOR_GREEN});
                color: black;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 900;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{ background: #33dd77; }}
            QPushButton:pressed {{ background: #009938; }}
        """)
        self.replay_btn.clicked.connect(self.play_again)
        self._root.addWidget(self.replay_btn)

    # ── API Publique ──────────────────────────────────────
    def load(self, game_state):
        """Lance la révélation animée"""
        game_state.start_reveal()

        # Vider les grilles
        for lay in [self.rouge_grid_lay, self.bleu_grid_lay]:
            while lay.count():
                item = lay.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        self.winner_banner.setVisible(False)
        self.replay_btn.setVisible(False)

        # Reset scores
        self.banner_rouge.score_lbl.setText("⭐  Calcul en cours...")
        self.banner_bleu.score_lbl.setText("⭐  Calcul en cours...")

        # Créer les cartes avec délai progressif
        all_cards_count = len(game_state.team_rouge.players) + len(game_state.team_bleu.players)
        delay_step = max(200, 1800 // max(all_cards_count, 1))

        rouge_cards = []
        for i, player in enumerate(game_state.team_rouge.players):
            card = RevealPlayerCard(player, "rouge", delay_ms=(i + 1) * delay_step)
            row, col = divmod(i, 3)
            self.rouge_grid_lay.addWidget(card, row, col)
            rouge_cards.append(card)

        bleu_cards = []
        for i, player in enumerate(game_state.team_bleu.players):
            card = RevealPlayerCard(
                player, "bleu",
                delay_ms=(len(game_state.team_rouge.players) + i + 1) * delay_step
            )
            row, col = divmod(i, 3)
            self.bleu_grid_lay.addWidget(card, row, col)
            bleu_cards.append(card)

        # Afficher les scores après toutes les révélations
        total_delay = (all_cards_count + 2) * delay_step
        QTimer.singleShot(
            total_delay,
            lambda: self._show_scores(game_state)
        )

    def _show_scores(self, game_state):
        """Affiche les scores finaux et le vainqueur"""
        r_total = game_state.team_rouge.total_rating
        b_total = game_state.team_bleu.total_rating
        winner  = game_state.get_winner()

        self.banner_rouge.set_score(r_total, winner == "rouge")
        self.banner_bleu.set_score(b_total,  winner == "bleu")

        QTimer.singleShot(600, lambda: self._show_winner(game_state, winner))

    def _show_winner(self, game_state, winner: str):
        """Affiche la bannière vainqueur animée"""
        self.winner_banner.setVisible(True)
        self.replay_btn.setVisible(True)

        if winner == "rouge":
            name  = game_state.team_rouge.name
            color = COLOR_ROUGE
            emoji = "🏆🔴"
        elif winner == "bleu":
            name  = game_state.team_bleu.name
            color = COLOR_BLEU
            emoji = "🏆🔵"
        else:
            name  = "Égalité parfaite !"
            color = COLOR_GREEN
            emoji = "🤝"

        self.winner_banner.setText(
            f"{emoji}  VAINQUEUR :  {name.upper()}  {emoji}"
        )
        self.winner_banner.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 rgba(0,0,0,0), stop:0.2 {color}, stop:0.8 {color}, stop:1 rgba(0,0,0,0));
            color: white;
            font-size: 20px;
            font-weight: 900;
            border-radius: 14px;
            letter-spacing: 3px;
        """)

        # Clignotement du titre
        self._blink_count = 0
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(400)
        self._blink_timer.timeout.connect(
            lambda: self._blink_title(color)
        )
        self._blink_timer.start()

    def _blink_title(self, color: str):
        self._blink_count += 1
        if self._blink_count > 6:
            self._blink_timer.stop()
            self.title_lbl.setStyleSheet(
                f"color: {COLOR_GREEN}; font-size: 28px; font-weight: 900; "
                "background: transparent; letter-spacing: 4px;"
            )
            return
        c = color if self._blink_count % 2 == 0 else COLOR_GREEN
        self.title_lbl.setStyleSheet(
            f"color: {c}; font-size: 28px; font-weight: 900; "
            "background: transparent; letter-spacing: 4px;"
        )
