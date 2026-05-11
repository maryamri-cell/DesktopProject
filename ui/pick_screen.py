# ============================================================
# ui/pick_screen.py — Écran de choix du joueur (2 cartes)
# ============================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QFrame)
from PyQt5.QtCore    import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui     import QPixmap, QPainter, QColor, QLinearGradient, QPainterPath
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config  import (COLOR_GREEN, COLOR_ROUGE, COLOR_BLEU,
                     COLOR_GRAY, COLOR_CARD_BG, TOTAL_MANCHES)
from ui.styles  import (STYLE_MASTERS_HEADER, STYLE_MANCHE_BAR, STYLE_BANNER_ROUGE, STYLE_BANNER_BLEU)
from ui.widgets import TeamPanel, CombinedTeamPanel, ProgressManche, SeparatorLine, ExitButton
from game.image_loader import ImageLoader, load_pixmap


class BigPlayerCard(QFrame):
    """
    Grande carte joueur avec un design codé "Premium" inspiré du template utilisateur.
    """
    chosen = pyqtSignal(int)

    def __init__(self, player, index: int, chooser_color: str, parent=None):
        super().__init__(parent)
        self.player        = player
        self.index         = index
        self.chooser_color = chooser_color
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedSize(300, 440)
        self.setCursor(Qt.PointingHandCursor)
        
        color_hex = "#ff4444" if self.chooser_color == "rouge" else "#00d4ff"
        
        # Design de la carte (Gradient + Bordure lumineuse)
        self.setStyleSheet(f"""
            BigPlayerCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e2a3a, stop:1 #080c14);
                border: 2px solid {color_hex}44;
                border-radius: 25px;
            }}
            BigPlayerCard:hover {{
                border: 2px solid {color_hex};
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #25364a, stop:1 #0d121d);
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 25, 20, 25)
        layout.setSpacing(15)

        # 1. NOM (TOUT EN HAUT - Style Titre)
        self.name_lbl = QLabel(self.player.name.upper())
        self.name_lbl.setAlignment(Qt.AlignCenter)
        self.name_lbl.setStyleSheet("""
            color: #ffd700; font-size: 20px; font-weight: 900; 
            letter-spacing: 2px; background: transparent;
        """)
        layout.addWidget(self.name_lbl)

        # 2. PHOTO (CONTENEUR AVEC ANNEAU ARGENTÉ)
        self.photo_cont = QFrame()
        self.photo_cont.setFixedSize(175, 175)
        self.photo_cont.setStyleSheet("""
            background: rgba(255,255,255,0.03);
            border: 4px solid qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:0.5 #a0a0a0, stop:1 #666666);
            border-radius: 87px;
        """)
        photo_lay = QVBoxLayout(self.photo_cont)
        photo_lay.setContentsMargins(5, 5, 5, 5)
        
        self.photo_lbl = QLabel("⚽")
        self.photo_lbl.setAlignment(Qt.AlignCenter)
        self.photo_lbl.setStyleSheet("background: transparent; border: none; font-size: 80px;")
        photo_lay.addWidget(self.photo_lbl)
        
        layout.addWidget(self.photo_cont, 0, Qt.AlignCenter)

        # 3. INFOS (CLUB & NATION)
        info_widget = QWidget()
        info_lay = QVBoxLayout(info_widget)
        info_lay.setSpacing(4)
        info_lay.setContentsMargins(0, 0, 0, 0)

        self.club_lbl = QLabel(self.player.club)
        self.club_lbl.setAlignment(Qt.AlignCenter)
        self.club_lbl.setStyleSheet("color: white; font-size: 14px; font-weight: 700; background: transparent;")
        info_lay.addWidget(self.club_lbl)

        self.nation_lbl = QLabel(f"{self.player.nation} • {self.player.position}")
        self.nation_lbl.setAlignment(Qt.AlignCenter)
        self.nation_lbl.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 11px; background: transparent;")
        info_lay.addWidget(self.nation_lbl)
        
        layout.addWidget(info_widget)

        layout.addStretch()

        # 4. ACTION (Zone clickable en bas - FRAME ARGENTÉ)
        self.action_lbl = QLabel("CHOISIR CE JOUEUR")
        self.action_lbl.setFixedHeight(48)
        self.action_lbl.setAlignment(Qt.AlignCenter)
        self.action_lbl.setStyleSheet("""
            color: black; font-weight: 900; font-size: 13px; letter-spacing: 2px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e0e0e0, stop:0.5 #bdbdbd, stop:1 #8d8d8d);
            border: 2px solid #ffffff;
            border-radius: 15px;
        """)
        
        layout.addWidget(self.action_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.chosen.emit(self.index)

    def set_image_pixmap(self, px: QPixmap):
        """Applique l'image du joueur avec un masque circulaire"""
        # Taille utile à l'intérieur de l'anneau (175 - 10px de marges)
        size = QSize(165, 165)
        scaled = px.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        
        out_img = QPixmap(size)
        out_img.fill(Qt.transparent)
        
        painter = QPainter(out_img)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, size.width(), size.height())
        painter.setClipPath(path)
        
        x = (size.width() - scaled.width()) // 2
        y = (size.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()
        
        self.photo_lbl.setPixmap(out_img)
        self.photo_lbl.setText("")

    def set_image(self, path: str):
        if os.path.exists(path):
            self.set_image_pixmap(QPixmap(path))

    def disable(self):
        self.setEnabled(False)
        self.action_lbl.setText("INDISPONIBLE")
        self.action_lbl.setStyleSheet("color: #666; background: #222; border: 1px solid #333; border-radius: 12px;")

    def mark_chosen(self):
        self.action_lbl.setText("✅ CHOISI")
        self.action_lbl.setStyleSheet("color: #00ff00; background: rgba(0,255,0,0.1); border: 2px solid #00ff00; border-radius: 12px;")
        self.setEnabled(False)

    def mark_given(self):
        """Marque cette carte comme attribuée à l'adversaire (sombre)"""
        self.setEnabled(False)
        self.action_lbl.setText("ATTRIBUÉ")
        self.action_lbl.setStyleSheet("color: #444; background: transparent; border: 1px solid #222; border-radius: 12px;")
        self.photo_cont.setStyleSheet("background: rgba(0,0,0,0.5); border: 2px solid #222; border-radius: 85px;")
        self.name_lbl.setStyleSheet("color: #444; font-size: 20px; font-weight: 900; background: transparent;")


class PickScreen(QWidget):
    """
    Écran de choix du joueur :
    - Affiche 2 grandes cartes joueurs côte à côte
    - L'équipe gagnante clique sur sa carte
    - L'autre joueur va automatiquement à l'adversaire
    - Émet player_picked(index) : 0 ou 1
    """

    player_picked  = pyqtSignal(int)   # 0 ou 1
    exit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards   = []
        self._enabled = False
        self._img_loader = ImageLoader(self)
        self._img_loader.image_ready.connect(self._on_image_ready)
        self._setup_ui()

    def _setup_ui(self):
        # ── Fond (Image Stade) ───────────────────────────
        self.bg_lbl = QLabel(self)
        self.bg_lbl.setScaledContents(True)
        bg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Gemini_Generated_Image_81bu7x81bu7x81bu.png")
        if os.path.exists(bg_path):
            self.bg_lbl.setPixmap(QPixmap(bg_path))
            
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar Equipes ──────────────────────────────
        self.team_panel = CombinedTeamPanel()
        # Largeur harmonisée avec les autres écrans (580px)
        main_layout.addWidget(self.team_panel)

        # ── Zone centrale (Transparente pour voir l'image de fond) ──
        center_widget = QWidget()
        center_widget.setStyleSheet("background: transparent;")
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(25, 15, 25, 25)
        center_layout.setSpacing(10)
        main_layout.addWidget(center_widget, 1)

        # Header (Logo à gauche, bouton Quitter à droite)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        
        # Logo (Déplacé vers la droite)
        header_row.addSpacing(160)  
        self.logo_lbl = QLabel()
        self.logo_lbl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.logo_lbl.setStyleSheet("background: transparent; border: none;")
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Gemini_Generated_Image_w4q5buw4q5buw4q5-removebg-preview.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            self.logo_lbl.setPixmap(pix.scaledToHeight(120, Qt.SmoothTransformation)) # Taille AnswerScreen
        header_row.addWidget(self.logo_lbl)
        
        header_row.addStretch(1)
        
        self.exit_btn = ExitButton()
        self.exit_btn.clicked.connect(self.exit_requested.emit)
        header_row.addWidget(self.exit_btn)
        center_layout.addLayout(header_row)

        center_layout.addStretch(1)

        # ── Bannière Qui Choisit ───────────────────────────
        banner_cont = QWidget()
        banner_lay = QVBoxLayout(banner_cont)
        banner_lay.setSpacing(10) 
        banner_lay.setAlignment(Qt.AlignCenter)
        
        # Logo supprimé d'ici car déplacé en haut (header_row)

        self.chooser_banner = QLabel("ÉQUIPE ROUGE CHOISIT !")
        self.chooser_banner.setFixedHeight(45)
        self.chooser_banner.setFixedWidth(400)
        self.chooser_banner.setAlignment(Qt.AlignCenter)
        self.chooser_banner.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0,255,136,0.5), stop:1 rgba(0,255,136,0.2));
                color: white; font-weight: 900; font-size: 16px; border: 2px solid #00ff88; border-radius: 22px; letter-spacing: 2px;
            }
        """)
        banner_lay.addWidget(self.chooser_banner, 0, Qt.AlignCenter)
        center_layout.addWidget(banner_cont)

        # ── Sous-titre SUPPRIMÉ ──────────────────────────
        # self.sub_lbl = QLabel("...") 

        center_layout.addStretch(1)

        # ── Glass Panel pour les cartes ───────────────────
        self.cards_panel = QFrame()
        self.cards_panel.setObjectName("cardsFrame")
        self.cards_panel.setStyleSheet("""
            #cardsFrame {
                background: transparent;
                border: none;
            }
        """)
        cards_lay = QVBoxLayout(self.cards_panel)
        cards_lay.setContentsMargins(40, 40, 40, 40)
        
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(40)
        self.cards_layout.setAlignment(Qt.AlignCenter)
        cards_lay.addLayout(self.cards_layout)
        
        center_layout.addWidget(self.cards_panel)
        center_layout.addStretch(2)

        # Status
        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("color: #00ff88; font-weight: 700; font-size: 14px;")
        center_layout.addWidget(self.status_lbl)

    def resizeEvent(self, event):
        self.bg_lbl.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)



    # ── API Publique ──────────────────────────────────────
    def load(self, player1, player2, chooser_color: str,
             manche: int, game_state, ai_mode: bool = False):
        """Prépare l'écran avec 2 joueurs pour le choix"""
        self._enabled = True
        self._ai_mode = ai_mode

        # Vider les anciennes cartes
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards = []

        # Bannière
        team = game_state.get_team(chooser_color)
        color_hex = COLOR_ROUGE if chooser_color == "rouge" else COLOR_BLEU
        if ai_mode:
            self.chooser_banner.setText(f"🤖  {team.name.upper()} CHOISIT...")
        else:
            self.chooser_banner.setText(f"⚽  {team.name.upper()} CHOISIT !")
        
        self.chooser_banner.setStyleSheet(STYLE_BANNER_ROUGE if chooser_color == "rouge" else STYLE_BANNER_BLEU)

        # Créer les 2 cartes (masquées si c'est l'IA)
        for i, player in enumerate([player1, player2]):
            if ai_mode:
                card = self._make_hidden_card(i, chooser_color)
                self._cards.append(card)
                self.cards_layout.addWidget(card)
            else:
                card = BigPlayerCard(player, i, chooser_color)
                card.chosen.connect(self._on_pick)
                # Charger l'image (cache ou async)
                px = load_pixmap(player.player_id, size=180)
                if px:
                    # On affiche le cache mais on demande quand même le path pour la persistence terrain
                    card.set_image_pixmap(px)
                    self._img_loader.request_image(player.player_id)
                else:
                    self._img_loader.request_image(player.player_id)
                self._cards.append(card)
                self.cards_layout.addWidget(card)

        # Manche (Affichage supprimé du UI)
        # self.manche_lbl.setText(f"Manche {manche + 1} / {TOTAL_MANCHES}")
        self.status_lbl.setText("")

        # Panels équipes
        self.team_panel.update_state(game_state)

    def set_spectator_mode(self, is_spectator: bool):
        """Désactive l'interaction si on n'est pas celui qui choisit"""
        self._enabled = not is_spectator
        if is_spectator:
            self.status_lbl.setText("L'autre joueur est en train de sélectionner son joueur.")
            for card in self._cards:
                if hasattr(card, "disable"):
                    card.disable()
                if hasattr(card, "action_lbl"):
                    card.action_lbl.setText("⏳ EN ATTENTE...")
        else:
            self.status_lbl.setText("")

    def disable_pick(self):
        self._enabled = False
        for card in self._cards:
            if hasattr(card, "disable"):
                card.disable()

    def update_teams(self, game_state):
        self.team_panel.update_state(game_state)

    # ── Interne ──────────────────────────────────────────
    def _make_hidden_card(self, index: int, chooser_color: str):
        """Crée une carte masquée quand c'est l'IA qui choisit."""
        color = COLOR_ROUGE if chooser_color == "rouge" else COLOR_BLEU
        card = QFrame()
        card.index = index
        card.player = None
        card.setFixedWidth(290)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #131313;
                border: 2px solid #2a2a2a;
                border-radius: 20px;
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 30, 20, 30)
        lay.setSpacing(16)

        icon = QLabel("🤖")
        icon.setStyleSheet("font-size: 64px; background: transparent; border: none;")
        icon.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon)

        lbl = QLabel(f"Joueur {index + 1}")
        lbl.setStyleSheet(
            "color: #555; font-size: 18px; font-weight: 900; "
            "background: transparent; border: none;"
        )
        lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl)

        hidden_lbl = QLabel("Informations masquées")
        hidden_lbl.setStyleSheet(
            "color: #333; font-size: 12px; font-style: italic; "
            "background: transparent; border: none;"
        )
        hidden_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(hidden_lbl)

        lay.addStretch()

        # Dummy button (non clickable) pour garder la même taille
        dummy_btn = QPushButton("🤖  L'IA choisit...")
        dummy_btn.setFixedHeight(48)
        dummy_btn.setEnabled(False)
        dummy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a1a1a;
                color: #444444;
                border: none; border-radius: 12px;
                font-size: 14px; font-weight: 900;
            }}
        """)
        lay.addWidget(dummy_btn)

        card.choose_btn = dummy_btn
        return card

    def _on_pick(self, index: int):
        if not self._enabled:
            return
        self._enabled = False

        if getattr(self, '_ai_mode', False):
            # Mode IA : pas de feedback visuel, transition rapide
            self.status_lbl.setText("🤖  L'IA a fait son choix.")
            QTimer.singleShot(800, lambda: self.player_picked.emit(index))
            return

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

    def _on_image_ready(self, pid: int, path: str):
        """Callback quand une image est téléchargée."""
        for card in self._cards:
            if hasattr(card, 'player') and card.player and card.player.player_id == pid:
                card.player.photo_path = path # Persistance de l'image
                card.set_image(path)
