# ============================================================
# ui/pick_screen.py — Écran de choix du joueur (2 cartes)
# ============================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QFrame)
from PyQt5.QtCore    import Qt, pyqtSignal, QTimer
from PyQt5.QtGui     import QPixmap, QPainter, QColor, QLinearGradient
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config  import (COLOR_GREEN, COLOR_ROUGE, COLOR_BLEU,
                     COLOR_GRAY, COLOR_CARD_BG)
from ui.widgets import TeamPanel, ProgressManche, SeparatorLine
from game.image_loader import ImageLoader, load_pixmap


class BigPlayerCard(QFrame):
    """
    Grande carte joueur style FIFA :
    - Photo placeholder (⚽) ou vraie image (Phase 3)
    - Nom, club, nationalité, position, âge
    - Rating CACHÉ pendant la partie
    - Bouton "Choisir ce joueur" en bas
    """
    chosen = pyqtSignal(int)   # index 0 ou 1

    def __init__(self, player, index: int, chooser_color: str, parent=None):
        super().__init__(parent)
        self.player        = player
        self.index         = index
        self.chooser_color = chooser_color
        self._setup_ui()

    def _setup_ui(self):
        color = COLOR_ROUGE if self.chooser_color == "rouge" else COLOR_BLEU
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #131313;
                border: 2px solid #2a2a2a;
                border-radius: 20px;
            }}
        """)
        self.setFixedWidth(290)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # ── Badge position ────────────────────────────────
        pos_badge = QLabel(self.player.position)
        pos_badge.setFixedHeight(28)
        pos_badge.setStyleSheet(f"""
            background-color: {color};
            color: white;
            font-size: 12px;
            font-weight: 900;
            border-radius: 8px;
            letter-spacing: 2px;
            padding: 0 10px;
        """)
        pos_badge.setAlignment(Qt.AlignCenter)
        layout.addWidget(pos_badge)

        # ── Photo ────────────────────────────────────────
        self.photo_lbl = QLabel()
        self.photo_lbl.setFixedSize(160, 160)
        self.photo_lbl.setAlignment(Qt.AlignCenter)
        self.photo_lbl.setStyleSheet("""
            background-color: #1e1e1e;
            border: 3px solid #333333;
            border-radius: 80px;
            font-size: 64px;
        """)
        self.photo_lbl.setText("⚽")
        layout.addWidget(self.photo_lbl, alignment=Qt.AlignCenter)

        # ── Nom ──────────────────────────────────────────
        name_lbl = QLabel(self.player.name)
        name_lbl.setStyleSheet(
            "color: white; font-size: 18px; font-weight: 900; "
            "background: transparent; border: none;"
        )
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setWordWrap(True)
        layout.addWidget(name_lbl)

        # ── Club ─────────────────────────────────────────
        club_lbl = QLabel(f"🏟  {self.player.club}")
        club_lbl.setStyleSheet(
            f"color: {COLOR_GRAY}; font-size: 12px; "
            "background: transparent; border: none;"
        )
        club_lbl.setAlignment(Qt.AlignCenter)
        club_lbl.setWordWrap(True)
        layout.addWidget(club_lbl)

        # ── Nation + Age ──────────────────────────────────
        info_lbl = QLabel(f"🌍  {self.player.nation}   •   {self.player.age} ans")
        info_lbl.setStyleSheet(
            f"color: {COLOR_GRAY}; font-size: 11px; "
            "background: transparent; border: none;"
        )
        info_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_lbl)

        # ── Rating caché ─────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #2a2a2a; border: none; max-height: 1px;")
        layout.addWidget(sep)

        rating_lbl = QLabel("⭐  Rating FIFA :  [Caché]")
        rating_lbl.setStyleSheet(
            f"color: #555555; font-size: 12px; font-style: italic; "
            "background: transparent; border: none;"
        )
        rating_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(rating_lbl)

        layout.addStretch()

        # ── Bouton Choisir ───────────────────────────────
        self.choose_btn = QPushButton("✅   Choisir ce joueur")
        self.choose_btn.setFixedHeight(48)
        self.choose_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 900;
            }}
            QPushButton:hover {{
                background-color: {'#ff6666' if self.chooser_color == 'rouge' else '#6688ff'};
            }}
            QPushButton:pressed {{
                background-color: {'#cc0000' if self.chooser_color == 'rouge' else '#2244cc'};
            }}
            QPushButton:disabled {{
                background-color: #1a1a1a;
                color: #444444;
            }}
        """)
        self.choose_btn.clicked.connect(lambda: self.chosen.emit(self.index))
        layout.addWidget(self.choose_btn)

    def set_image(self, path: str):
        """Charge une image joueur (Phase 3 - Pollinations.ai)"""
        if os.path.exists(path):
            px = QPixmap(path).scaled(
                160, 160, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            # Masque circulaire
            self.photo_lbl.setPixmap(px)
            self.photo_lbl.setText("")

    def set_image_pixmap(self, px: QPixmap):
        """Charge une image joueur depuis un QPixmap déjà prêt."""
        self.photo_lbl.setPixmap(px.scaled(
            160, 160, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        ))
        self.photo_lbl.setText("")

    def disable(self):
        self.choose_btn.setEnabled(False)
        self.choose_btn.setText("❌  Non disponible")

    def mark_chosen(self):
        """Marque cette carte comme choisie (vert)"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #0d2a0d;
                border: 3px solid {COLOR_GREEN};
                border-radius: 20px;
            }}
        """)
        self.choose_btn.setText("✅  Choisi !")
        self.choose_btn.setEnabled(False)

    def mark_given(self):
        """Marque cette carte comme attribuée à l'adversaire (gris)"""
        self.setStyleSheet("""
            QFrame {
                background-color: #111111;
                border: 2px solid #222222;
                border-radius: 20px;
                opacity: 0.5;
            }
        """)
        self.choose_btn.setText("→  Donné à l'adversaire")
        self.choose_btn.setEnabled(False)


class PickScreen(QWidget):
    """
    Écran de choix du joueur :
    - Affiche 2 grandes cartes joueurs côte à côte
    - L'équipe gagnante clique sur sa carte
    - L'autre joueur va automatiquement à l'adversaire
    - Émet player_picked(index) : 0 ou 1
    """

    player_picked = pyqtSignal(int)   # 0 ou 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards   = []
        self._enabled = False
        self._img_loader = ImageLoader(self)
        self._img_loader.image_ready.connect(self._on_image_ready)
        self._setup_ui()

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # Panel rouge
        self.team_rouge_panel = TeamPanel("Équipe Rouge", "rouge")
        self.team_rouge_panel.setFixedWidth(190)
        root.addWidget(self.team_rouge_panel)

        # Centre
        center = QVBoxLayout()
        center.setSpacing(14)

        self.progress = ProgressManche(total=11)
        center.addWidget(self.progress)

        sep = SeparatorLine()
        center.addWidget(sep)

        # Bannière qui choisit
        self.chooser_banner = QLabel("Équipe Rouge choisit son joueur !")
        self.chooser_banner.setFixedHeight(44)
        self.chooser_banner.setStyleSheet(f"""
            background-color: {COLOR_ROUGE};
            color: white;
            font-size: 16px;
            font-weight: 900;
            border-radius: 10px;
        """)
        self.chooser_banner.setAlignment(Qt.AlignCenter)
        center.addWidget(self.chooser_banner)

        # Sous-titre
        self.sub_lbl = QLabel("Choisissez un joueur — le rating est caché !")
        self.sub_lbl.setStyleSheet(
            f"color: {COLOR_GRAY}; font-size: 12px; background: transparent;"
        )
        self.sub_lbl.setAlignment(Qt.AlignCenter)
        center.addWidget(self.sub_lbl)

        # Zone des 2 cartes
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(30)
        self.cards_layout.setAlignment(Qt.AlignCenter)
        center.addLayout(self.cards_layout)

        center.addStretch()

        # Message statut
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(
            f"color: {COLOR_GREEN}; font-size: 14px; font-weight: bold; background: transparent;"
        )
        self.status_lbl.setAlignment(Qt.AlignCenter)
        center.addWidget(self.status_lbl)

        root.addLayout(center)

        # Panel bleu
        self.team_bleu_panel = TeamPanel("Équipe Bleue", "bleu")
        self.team_bleu_panel.setFixedWidth(190)
        root.addWidget(self.team_bleu_panel)

    # ── API Publique ──────────────────────────────────────
    def load(self, player1, player2, chooser_color: str,
             manche: int, game_state):
        """Prépare l'écran avec 2 joueurs pour le choix"""
        self._enabled = True

        # Vider les anciennes cartes
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards = []

        # Bannière
        team = game_state.get_team(chooser_color)
        color_hex = COLOR_ROUGE if chooser_color == "rouge" else COLOR_BLEU
        self.chooser_banner.setText(f"⚽  {team.name} choisit son joueur !")
        self.chooser_banner.setStyleSheet(f"""
            background-color: {color_hex};
            color: white; font-size: 16px;
            font-weight: 900; border-radius: 10px;
        """)

        # Créer les 2 cartes
        for i, player in enumerate([player1, player2]):
            card = BigPlayerCard(player, i, chooser_color)
            card.chosen.connect(self._on_pick)
            self._cards.append(card)
            self.cards_layout.addWidget(card)
            # Charger l'image (cache ou async)
            px = load_pixmap(player.name, size=160)
            if px:
                card.set_image_pixmap(px)
            else:
                self._img_loader.request_image(player.name, player.club)

        # Progression
        self.progress.update_progress(manche)
        self.status_lbl.setText("")

        # Panels équipes
        self.team_rouge_panel.update_state(game_state.team_rouge)
        self.team_bleu_panel.update_state(game_state.team_bleu)

    def disable_pick(self):
        self._enabled = False
        for card in self._cards:
            card.choose_btn.setEnabled(False)

    def update_teams(self, game_state):
        self.team_rouge_panel.update_state(game_state.team_rouge)
        self.team_bleu_panel.update_state(game_state.team_bleu)

    # ── Interne ──────────────────────────────────────────
    def _on_pick(self, index: int):
        if not self._enabled:
            return
        self._enabled = False

        # Marquer visuellement
        for i, card in enumerate(self._cards):
            if i == index:
                card.mark_chosen()
            else:
                card.mark_given()

        other = game_state_other_name = "l'adversaire"
        self.status_lbl.setText(
            f"✅  Joueur {index + 1} choisi !  L'autre joueur va à {other}."
        )

        # Petit délai pour voir les cartes avant de passer
        QTimer.singleShot(1200, lambda: self.player_picked.emit(index))

    def force_pick(self, index: int):
        """Déclenche un choix depuis l'extérieur (agent IA)"""
        self._on_pick(index)

    def _on_image_ready(self, name: str, path: str):
        """Callback quand une image est téléchargée."""
        for card in self._cards:
            if card.player.name == name:
                card.set_image(path)
