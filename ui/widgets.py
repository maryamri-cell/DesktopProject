# ============================================================
# ui/widgets.py — Widgets réutilisables
# ============================================================

from PyQt5.QtWidgets import (QLabel, QFrame, QVBoxLayout,
                              QHBoxLayout, QWidget, QProgressBar)
from PyQt5.QtCore    import Qt, QSize
from PyQt5.QtGui     import QFont, QPixmap, QPainter, QColor
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COLOR_GREEN, COLOR_ROUGE, COLOR_BLEU, COLOR_JAUNE, COLOR_GRAY
from ui.styles import STYLE_JAUNE, STYLE_ROUGE_CARD, STYLE_PROGRESS


class TitleLabel(QLabel):
    """Label titre vert Ahsan Khota"""
    def __init__(self, text: str, size: int = 48, parent=None):
        super().__init__(text, parent)
        font = QFont("Segoe UI", size, QFont.Black)
        self.setFont(font)
        self.setStyleSheet(f"color: {COLOR_GREEN}; background: transparent; letter-spacing: 3px;")
        self.setAlignment(Qt.AlignCenter)


class SubtitleLabel(QLabel):
    """Label sous-titre gris"""
    def __init__(self, text: str, size: int = 14, parent=None):
        super().__init__(text, parent)
        font = QFont("Segoe UI", size)
        self.setFont(font)
        self.setStyleSheet(f"color: {COLOR_GRAY}; background: transparent; letter-spacing: 2px;")
        self.setAlignment(Qt.AlignCenter)


class SeparatorLine(QFrame):
    """Ligne séparatrice verte"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(2)
        self.setStyleSheet(f"background-color: {COLOR_GREEN}; border: none;")


class CartonWidget(QWidget):
    """Affiche les cartons jaunes et rouges d'une équipe"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._jaunes = 0
        self._rouges = 0
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self._layout = layout
        self._update_display()

    def update_cartons(self, jaunes: int, rouges: int):
        self._jaunes = jaunes
        self._rouges = rouges
        self._update_display()

    def _update_display(self):
        # Supprimer anciens widgets
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Cartons jaunes
        for _ in range(self._jaunes):
            lbl = QLabel("🟡")
            lbl.setFixedSize(28, 28)
            lbl.setAlignment(Qt.AlignCenter)
            self._layout.addWidget(lbl)

        # Cartons rouges
        for _ in range(self._rouges):
            lbl = QLabel("🟥")
            lbl.setFixedSize(28, 28)
            lbl.setAlignment(Qt.AlignCenter)
            self._layout.addWidget(lbl)

        self._layout.addStretch()


class FormationPitch(QWidget):
    """
    Terrain de football miniature avec joueurs positionnés.
    Affiche chaque joueur comme un cercle coloré avec position + nom.
    Inspiré du style tachkila (analyse tactique).
    """

    # Ordre de ligne pour la formation 4-3-3 (du bas vers le haut)
    # Chaque élément = (position_tag, ligne_y_ratio)
    FORMATION_ROWS = [
        ["GK"],
        ["RB", "CB", "CB", "LB"],
        ["CDM", "CM", "CM"],
        ["RW", "ST", "LW"],
    ]

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.color     = color
        self._players  = []   # liste de Player
        self._color_hex = COLOR_ROUGE if color == "rouge" else COLOR_BLEU
        self.setMinimumHeight(300)

    def set_players(self, players: list):
        self._players = players
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        w = self.width()
        h = self.height()

        # ── Terrain ──────────────────────────────────────
        # Fond gazon
        from PyQt5.QtGui import QLinearGradient, QPen, QBrush, QFont as QF
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor("#1a3a1a"))
        grad.setColorAt(0.5, QColor("#1e4a1e"))
        grad.setColorAt(1.0, QColor("#1a3a1a"))
        painter.fillRect(0, 0, w, h, grad)

        # Lignes terrain
        pen = painter.pen()
        pen.setColor(QColor(255, 255, 255, 60))
        pen.setWidth(1)
        painter.setPen(pen)

        pad = 8
        # Rectangle extérieur
        painter.drawRect(pad, pad, w - 2*pad, h - 2*pad)
        # Ligne médiane
        painter.drawLine(pad, h//2, w - pad, h//2)
        # Cercle central
        painter.drawEllipse(w//2 - 20, h//2 - 20, 40, 40)
        # Surface de réparation (bas)
        bw = int(w * 0.55)
        bh = int(h * 0.12)
        painter.drawRect((w - bw)//2, h - pad - bh, bw, bh)
        # Surface de réparation (haut)
        painter.drawRect((w - bw)//2, pad, bw, bh)

        if not self._players:
            # Message vide
            pen.setColor(QColor(255, 255, 255, 40))
            painter.setPen(pen)
            font = QF("Segoe UI", 8)
            painter.setFont(font)
            painter.drawText(0, 0, w, h, Qt.AlignCenter, "En attente\ndes joueurs...")
            return

        # ── Positionner les joueurs ───────────────────────
        # Distribuer les joueurs sur les lignes de la formation
        rows = self._build_rows()
        n_rows = len(rows)

        for row_idx, row_players in enumerate(rows):
            if not row_players:
                continue
            # Position y : de bas (GK) vers haut (attaquants)
            y_ratio = 1.0 - (row_idx + 0.6) / (n_rows + 0.2)
            y = int(h * y_ratio)

            n = len(row_players)
            for col_idx, player in enumerate(row_players):
                # Position x : répartis uniformément
                x_ratio = (col_idx + 1) / (n + 1)
                x = int(w * x_ratio)
                self._draw_player(painter, x, y, player)

    def _build_rows(self) -> list:
        """Distribue les joueurs selon leur position dans les lignes"""
        if not self._players:
            return []

        # Groupes par type
        gk   = [p for p in self._players if p.position in ["GK"]]
        defs = [p for p in self._players if p.position in ["CB","LB","RB","LWB","RWB","SW"]]
        mids = [p for p in self._players if p.position in ["CDM","CM","CAM","LM","RM","DM"]]
        atts = [p for p in self._players if p.position in ["ST","CF","LW","RW","LF","RF","SS"]]
        # Reste non classé
        rest = [p for p in self._players
                if p not in gk + defs + mids + atts]

        # Ajouter le reste aux attaquants
        atts += rest

        rows = []
        if gk:   rows.append(gk)
        if defs: rows.append(defs)
        if mids: rows.append(mids)
        if atts: rows.append(atts)
        return rows

    def _draw_player(self, painter, x: int, y: int, player):
        """Dessine un joueur : cercle + position + nom"""
        from PyQt5.QtGui import QPen, QBrush, QFont as QF

        r = 14   # rayon du cercle

        # Cercle rempli
        painter.setBrush(QBrush(QColor(self._color_hex)))
        pen = painter.pen()
        pen.setColor(QColor(255, 255, 255, 180))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawEllipse(x - r, y - r, r*2, r*2)

        # Position (en blanc dans le cercle)
        font = QF("Segoe UI", 6, QF.Bold)
        painter.setFont(font)
        pen.setColor(QColor(255, 255, 255, 240))
        painter.setPen(pen)
        pos_short = player.position[:3] if player.position else "?"
        painter.drawText(x - r, y - r, r*2, r*2, Qt.AlignCenter, pos_short)

        # Nom sous le cercle (raccourci)
        short_name = player.name.split(".")[-1].strip() if "." in player.name else player.name
        if len(short_name) > 9:
            short_name = short_name[:8] + "."
        font2 = QF("Segoe UI", 6)
        painter.setFont(font2)
        # Ombre
        pen.setColor(QColor(0, 0, 0, 180))
        painter.setPen(pen)
        painter.drawText(x - 28, y + r + 1, 56, 14, Qt.AlignCenter, short_name)
        # Texte blanc
        pen.setColor(QColor(255, 255, 255, 230))
        painter.setPen(pen)
        painter.drawText(x - 28, y + r, 56, 14, Qt.AlignCenter, short_name)


class TeamPanel(QFrame):
    """
    Panel latéral avec :
    - Nom + cartons + score en haut
    - Tachkila (terrain + formation) en dessous
    """
    def __init__(self, team_name: str, color: str, parent=None):
        super().__init__(parent)
        self.team_name = team_name
        self.color     = color
        self._setup_ui()

    def _setup_ui(self):
        color_hex = COLOR_ROUGE if self.color == "rouge" else COLOR_BLEU
        bg = "#1a0505" if self.color == "rouge" else "#05051a"
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 2px solid {color_hex};
                border-radius: 14px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)

        # ── Nom équipe ────────────────────────────────────
        self.name_lbl = QLabel(self.team_name)
        self.name_lbl.setStyleSheet(
            f"color: {color_hex}; font-size: 14px; font-weight: 900; "
            f"background: transparent; border: none; letter-spacing: 1px;"
        )
        self.name_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.name_lbl)

        # ── Cartons + Score inline ────────────────────────
        info_row = QHBoxLayout()
        info_row.setSpacing(4)

        self.cartons = CartonWidget()
        info_row.addWidget(self.cartons, stretch=1)

        self.score_lbl = QLabel("⭐ ?")
        self.score_lbl.setStyleSheet(
            f"color: {COLOR_GREEN}; font-size: 12px; font-weight: bold; "
            f"background: transparent; border: none;"
        )
        self.score_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        info_row.addWidget(self.score_lbl)
        layout.addLayout(info_row)

        # ── Séparateur ────────────────────────────────────
        sep = SeparatorLine()
        layout.addWidget(sep)

        # ── Terrain tachkila ─────────────────────────────
        self.pitch = FormationPitch(self.color)
        layout.addWidget(self.pitch, stretch=1)

    def update_state(self, team_state):
        """Met à jour depuis un TeamState"""
        # Nom
        self.name_lbl.setText(team_state.name)

        # Cartons
        self.cartons.update_cartons(team_state.jaunes, team_state.rouges)

        # Score
        score = team_state.total_rating_revealed
        self.score_lbl.setText(f"⭐ {score}")

        # Terrain
        self.pitch.set_players(team_state.players)


class ProgressManche(QWidget):
    """Barre de progression des manches"""
    def __init__(self, total: int = 11, parent=None):
        super().__init__(parent)
        self.total = total
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.lbl = QLabel("Manche 0 / 11")
        self.lbl.setStyleSheet(
            f"color: {COLOR_GRAY}; font-size: 12px; background: transparent;"
        )
        self.lbl.setAlignment(Qt.AlignCenter)

        self.bar = QProgressBar()
        self.bar.setMaximum(total)
        self.bar.setValue(0)
        self.bar.setFixedHeight(10)
        self.bar.setTextVisible(False)
        self.bar.setStyleSheet(STYLE_PROGRESS)

        layout.addWidget(self.lbl)
        layout.addWidget(self.bar)

    def update_progress(self, manche: int):
        self.bar.setValue(manche)
        self.lbl.setText(f"Manche {manche} / {self.total}")


class PlayerCard(QFrame):
    """
    Carte joueur style FIFA (sans le rating).
    Affiche : nom, club, nationalité, position.
    """
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #333333;
                border-radius: 16px;
            }
        """)
        self.setFixedSize(200, 260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Photo placeholder (sera remplacée par image IA en Phase 3)
        self.photo_lbl = QLabel()
        self.photo_lbl.setFixedSize(120, 120)
        self.photo_lbl.setAlignment(Qt.AlignCenter)
        self.photo_lbl.setStyleSheet("""
            background-color: #2a2a2a;
            border: 2px solid #444444;
            border-radius: 60px;
            font-size: 40px;
        """)
        self.photo_lbl.setText("⚽")
        layout.addWidget(self.photo_lbl, alignment=Qt.AlignCenter)

        # Nom
        name_lbl = QLabel(self.player.name)
        name_lbl.setStyleSheet(
            "color: white; font-size: 14px; font-weight: 900; "
            "background: transparent; border: none;"
        )
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setWordWrap(True)
        layout.addWidget(name_lbl)

        # Club
        club_lbl = QLabel(self.player.club)
        club_lbl.setStyleSheet(
            f"color: {COLOR_GRAY}; font-size: 11px; "
            "background: transparent; border: none;"
        )
        club_lbl.setAlignment(Qt.AlignCenter)
        club_lbl.setWordWrap(True)
        layout.addWidget(club_lbl)

        # Nation + Position
        info_lbl = QLabel(f"{self.player.nation} • {self.player.position}")
        info_lbl.setStyleSheet(
            f"color: {COLOR_GRAY}; font-size: 10px; "
            "background: transparent; border: none;"
        )
        info_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_lbl)

        # Rating caché
        rating_lbl = QLabel("⭐ Score FIFA: [Caché]")
        rating_lbl.setStyleSheet(
            f"color: {COLOR_GREEN}; font-size: 11px; font-weight: bold; "
            "background: transparent; border: none;"
        )
        rating_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(rating_lbl)

    def set_image(self, image_path: str):
        """Définit la photo du joueur (Phase 3)"""
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path).scaled(
                120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.photo_lbl.setPixmap(pixmap)
            self.photo_lbl.setText("")
