# ============================================================
# ui/widgets.py — Widgets réutilisables
# ============================================================

import sys, os
from PyQt5.QtWidgets import (QLabel, QFrame, QVBoxLayout,
                              QHBoxLayout, QWidget, QProgressBar, QPushButton, QGraphicsDropShadowEffect)
from PyQt5.QtCore    import Qt, QSize, QRect, QRectF, pyqtSignal, QPoint
from PyQt5.QtGui     import (
    QPixmap, QColor, QFont, QPainter, QBrush, 
    QLinearGradient, QPen, QRadialGradient, QImage, QPainterPath
)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COLOR_GREEN, COLOR_ROUGE, COLOR_BLEU, COLOR_JAUNE, COLOR_GRAY
from ui.styles import STYLE_JAUNE, STYLE_ROUGE_CARD, STYLE_PROGRESS
from game.image_loader import get_cached_path

class ExitButton(QPushButton):
    """Bouton pour quitter/recommencer en haut à droite"""
    def __init__(self, parent=None):
        super().__init__("✖  QUITTER", parent)
        self.setFixedSize(110, 34)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a1a1a;
                color: #888;
                border: 1px solid #333;
                border-radius: 17px;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ROUGE};
                color: white;
                border: 1px solid {COLOR_ROUGE};
            }}
        """)


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
    Supporte le drag & drop libre.
    """

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.color     = color
        self._players  = []   
        self._color_hex = COLOR_ROUGE if color == "rouge" else COLOR_BLEU
        self.setMinimumHeight(500)
        self.setMouseTracking(True)
        self._dragged_player = None
        self._last_mouse_pos = None
        self._player_rects = {} 

    def set_players(self, players: list):
        self._players = players
        self._init_positions_if_needed()
        self.update()

    def _init_positions_if_needed(self):
        """Initialise les positions par défaut basées sur les lignes si non définies"""
        if not self._players: return
        
        # S'il y a déjà des positions pour tout le monde, on ne fait rien
        if all(p.pitch_pos is not None for p in self._players):
            return

        rows = self._build_rows()
        n_rows = len(rows)
        for row_idx, row_players in enumerate(rows):
            y_ratio = 1.0 - (row_idx + 0.6) / (n_rows + 0.2)
            n = len(row_players)
            for col_idx, p in enumerate(row_players):
                if p.pitch_pos is None:
                    x_ratio = (col_idx + 1) / (n + 1)
                    p.pitch_pos = (x_ratio, y_ratio)

    def _build_rows(self) -> list:
        """Distribue les joueurs selon leur position dans les lignes"""
        if not self._players:
            return []
        gk   = [p for p in self._players if p.position in ["GK"]]
        defs = [p for p in self._players if p.position in ["CB","LB","RB","LWB","RWB","SW"]]
        mids = [p for p in self._players if p.position in ["CDM","CM","CAM","LM","RM","DM"]]
        atts = [p for p in self._players if p.position in ["ST","CF","LW","RW","LF","RF","SS"]]
        rest = [p for p in self._players if p not in gk + defs + mids + atts]
        atts += rest
        rows = []
        if gk:   rows.append(gk)
        if defs: rows.append(defs)
        if mids: rows.append(mids)
        if atts: rows.append(atts)
        return rows

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            for p, rect in self._player_rects.items():
                if rect.contains(pos):
                    self._dragged_player = p
                    self._last_mouse_pos = pos
                    self.setCursor(Qt.ClosedHandCursor)
                    break

    def mouseMoveEvent(self, event):
        if self._dragged_player:
            w, h = self.width(), self.height()
            x_ratio = event.pos().x() / w
            y_ratio = event.pos().y() / h
            x_ratio = max(0.05, min(0.95, x_ratio))
            y_ratio = max(0.05, min(0.95, y_ratio))
            self._dragged_player.pitch_pos = (x_ratio, y_ratio)
            self.update()
        else:
            pos = event.pos()
            on_player = False
            for rect in self._player_rects.values():
                if rect.contains(pos):
                    on_player = True
                    break
            self.setCursor(Qt.PointingHandCursor if on_player else Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if self._dragged_player:
            self._dragged_player = None
            self.setCursor(Qt.ArrowCursor)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        w, h = self.width(), self.height()

        # ── Terrain ──────────────────────────────────────
        from PyQt5.QtCore import QRect
        from PyQt5.QtGui import QLinearGradient, QPen, QBrush, QFont as QF
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor("#1a3a1a"))
        grad.setColorAt(0.5, QColor("#1e4a1e"))
        grad.setColorAt(1.0, QColor("#1a3a1a"))
        painter.fillRect(0, 0, w, h, grad)

        pen = QPen(QColor(255, 255, 255, 40), 1)
        painter.setPen(pen)
        pad = 10
        painter.drawRect(pad, pad, w - 2*pad, h - 2*pad)
        painter.drawLine(pad, h//2, w - pad, h//2)
        painter.drawEllipse(w//2 - 30, h//2 - 30, 60, 60)
        bw, bh = int(w*0.6), int(h*0.15)
        painter.drawRect((w-bw)//2, h-pad-bh, bw, bh)
        painter.drawRect((w-bw)//2, pad, bw, bh)

        if not self._players:
            return

        # ── Joueurs ─────────────────────────
        self._player_rects = {}
        for p in self._players:
            if p.pitch_pos is None: continue
            xr, yr = p.pitch_pos
            x, y = int(xr * w), int(yr * h)
            r = 16
            rect = QRect(x - r, y - r, r*2, r*2)
            self._player_rects[p] = rect
            
            # Dessin cercle
            is_dragged = (p == self._dragged_player)
            painter.setBrush(QBrush(QColor(self._color_hex).lighter(120 if is_dragged else 100)))
            pen = QPen(QColor(255, 255, 255, 180), 2)
            if is_dragged: pen.setColor(QColor(COLOR_JAUNE)); pen.setWidth(3)
            painter.setPen(pen)
            painter.drawEllipse(rect)

            # Texte Position
            painter.setFont(QF("Segoe UI", 7, QF.Bold))
            painter.setPen(QPen(Qt.white))
            painter.drawText(rect, Qt.AlignCenter, p.position[:3])

            # Nom dessiné avec fond
            painter.setFont(QF("Segoe UI", 7))
            name_text = p.name.split(".")[-1][:10]
            painter.setBrush(QBrush(QColor(0,0,0,100)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x - 30, y + r + 2, 60, 14, 4, 4)
            painter.setPen(QPen(Qt.white))
            painter.drawText(x - 30, y + r + 2, 60, 14, Qt.AlignCenter, name_text)


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

        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(8, 8, 8, 8)
        self._lay.setSpacing(5)

        # ── Nom équipe ────────────────────────────────────
        self.name_lbl = QLabel(self.team_name)
        self.name_lbl.setStyleSheet(
            f"color: {color_hex}; font-size: 14px; font-weight: 900; "
            f"background: transparent; border: none; letter-spacing: 1px;"
        )
        self.name_lbl.setAlignment(Qt.AlignCenter)
        self._lay.addWidget(self.name_lbl)

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
    def __init__(self, total: int = 18, parent=None):
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
        self.lbl.setText(f"Manche {manche + 1} / {self.total}")


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

class BenchSlot(QFrame):
    """Petit slot circulaire pour un remplaçant"""
    def __init__(self, color_hex, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.color_hex = color_hex
        self.player = None
        self.photo_lbl = QLabel(self)
        self.photo_lbl.setGeometry(0, 0, 40, 40)
        self.photo_lbl.setAlignment(Qt.AlignCenter)
        self.photo_lbl.setStyleSheet("background: transparent; border: none;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self.player:
            # Cercle pointillé style image 3
            pen = QPen(QColor(self.color_hex), 1.5, Qt.CustomDashLine)
            pen.setDashPattern([6, 6])
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(0, 0, 0, 40)))
            painter.drawEllipse(2, 2, self.width()-4, self.height()-4)
        else:
            # Cercle plein si joueur présent
            painter.setPen(QPen(QColor(self.color_hex), 2))
            painter.setBrush(QBrush(QColor(0,0,0,100)))
            painter.drawEllipse(2, 2, self.width()-4, self.height()-4)

    def set_player(self, player):
        self.player = player
        if not player:
            self.photo_lbl.clear()
            self.update()
            return
        
        if hasattr(player, 'photo_path') and player.photo_path and os.path.exists(player.photo_path):
            pix = QPixmap(player.photo_path)
            self.photo_lbl.setPixmap(pix.scaled(40, 40, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            self.photo_lbl.setText(player.position[:2])
            self.photo_lbl.setStyleSheet("color: white; font-weight: 800; font-size: 10px;")
        self.update()

class CombinedFormationPitch(QWidget):
    """Terrain de foot simplifié pour afficher les deux équipes"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._players_rouge = []
        self._players_bleu  = []
        self._player_rects = {}
        self._dragged_player = None # Ajouté pour éviter le crash dans paintEvent
        # Les événements souris sont maintenant gérés par le parent CombinedTeamPanel

    def set_players(self, players_rouge, players_bleu):
        self._players_rouge = [p for p in players_rouge if p.pitch_pos is not None]
        self._players_bleu  = [p for p in players_bleu if p.pitch_pos is not None]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Fond Gazon high-tech
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor("#0a1a0a"))
        grad.setColorAt(0.5, QColor("#0d240d"))
        grad.setColorAt(1.0, QColor("#0a1a0a"))
        painter.fillRect(0, 0, w, h, grad)

        # Lignes de terrain lumineuses (Style Stadium)
        pen = QPen(QColor(255, 255, 255, 60), 2)
        painter.setPen(pen)
        pad = 15
        painter.drawRoundedRect(pad, pad, w - 2*pad, h - 2*pad, 15, 15)
        painter.drawLine(pad, h//2, w - pad, h//2)
        painter.drawEllipse(w//2 - 40, h//2 - 40, 80, 80)
        
        # Surfaces de réparation
        box_w, box_h = int(w * 0.5), int(h * 0.15)
        # Haut
        painter.drawRect((w - box_w)//2, pad, box_w, box_h)
        # Bas
        painter.drawRect((w - box_w)//2, h - pad - box_h, box_w, box_h)
        
        # Petites surfaces
        sbox_w, sbox_h = int(w * 0.2), int(h * 0.05)
        # Haut
        painter.drawRect((w - sbox_w)//2, pad, sbox_w, sbox_h)
        # Bas
        painter.drawRect((w - sbox_w)//2, h - pad - sbox_h, sbox_w, sbox_h)

        # Joueurs
        self._player_rects = {}
        all_players = [(p, "#ff4444") for p in self._players_rouge] + [(p, "#00d4ff") for p in self._players_bleu]
        
        for p, color_hex in all_players:
            if p.pitch_pos is None: continue
            xr, yr = p.pitch_pos
            x, y = int(xr * w), int(yr * h)
            r = 22 # Un peu plus grand pour les images
            rect = QRect(x - r, y - r, r*2, r*2)
            self._player_rects[p] = rect
            
            is_dragged = (p == self._dragged_player)
            
            # Glow effect (Halo lumineux en fond)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(0,0,0,120)))
            painter.drawEllipse(rect)

            # Tentative de récupération auto si path manquant
            if not hasattr(p, 'photo_path') or not p.photo_path or not os.path.exists(p.photo_path):
                local_path = get_cached_path(p.player_id)
                if local_path:
                    p.photo_path = local_path
            
            # Dessiner l'image du joueur si elle existe
            photo_found = False
            if hasattr(p, 'photo_path') and p.photo_path and os.path.exists(p.photo_path):
                pix = QPixmap(p.photo_path)
                if not pix.isNull():
                    photo_found = True
                    # Masque circulaire
                    painter.save()
                    path = QPainterPath()
                    path.addEllipse(QRectF(rect))
                    painter.setClipPath(path)
                    # On utilise un ratio fixe pour être sûr de bien remplir
                    painter.drawPixmap(rect, pix.scaled(int(r*2.5), int(r*2.5), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                    painter.restore()

            if not photo_found:
                # Fallback : Cercle avec position
                painter.setBrush(QBrush(QColor(color_hex)))
                painter.drawEllipse(rect)
                painter.setFont(QFont("Segoe UI", 9, QFont.Black))
                painter.setPen(QPen(Qt.white))
                painter.drawText(rect, Qt.AlignCenter, p.position[:2])

            # Anneau de couleur d'équipe par-dessus
            ring_pen = QPen(QColor(color_hex), 3)
            painter.setPen(ring_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(rect)
            
            # Nom du joueur (Adaptatif)
            painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
            last_name = p.name.split()[-1].upper()
            fm = painter.fontMetrics()
            tw = fm.width(last_name) + 12
            
            # Fond semi-transparent adaptatif
            painter.setBrush(QBrush(QColor(0,0,0,180)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x - tw//2, y + r + 2, tw, 16, 4, 4)
            
            # Texte complet
            painter.setPen(QPen(Qt.white))
            painter.drawText(x - tw//2, y + r + 2, tw, 16, Qt.AlignCenter, last_name)

class CombinedTeamPanel(QFrame):
    """Panel latéral combiné style premium"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(580)
        self._dragged_player = None
        self._view_opponent = False
        self._local_color = None
        self.setMouseTracking(True)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            CombinedTeamPanel {
                background: rgba(10, 20, 40, 0.95);
                border-right: 2px solid rgba(0, 212, 255, 0.3);
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(15)

        # Équipe Bleue Header
        self.header_bleu = self._create_header("BLEU", "#00d4ff")
        layout.addWidget(self.header_bleu)

        # Toggle to view opponent (visual only)
        from PyQt5.QtWidgets import QPushButton
        self.view_toggle_btn = QPushButton("👁️ VOIR ADVERSAIRE")
        self.view_toggle_btn.setCheckable(True)
        self.view_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.view_toggle_btn.setFixedHeight(32)
        self.view_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                color: white;
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
                padding: 4px 15px;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.15);
                border-color: {COLOR_GREEN};
            }}
            QPushButton:checked {{
                background: {COLOR_GREEN};
                color: black;
            }}
        """)
        self.view_toggle_btn.toggled.connect(lambda on: self.toggle_view_opponent())
        layout.addWidget(self.view_toggle_btn, alignment=Qt.AlignCenter)

        # Terrain
        self.pitch = CombinedFormationPitch()
        self.pitch.setStyleSheet("border-radius: 15px; border: 1px solid rgba(255,255,255,0.05);")
        layout.addWidget(self.pitch, 1)

        # Équipe Rouge Header
        self.header_rouge = self._create_header("ROUGE", "#ff4444")
        layout.addWidget(self.header_rouge)

    def _create_header(self, team_name: str, color: str):
        frame = QFrame()
        frame.setFixedHeight(65)
        frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.1);
                border-left: 4px solid {color};
                border-radius: 8px;
            }}
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 2, 12, 2) # Marges minimales
        lay.setSpacing(0)

        top_row = QHBoxLayout()
        name_lbl = QLabel(f"ÉQUIPE {team_name}")
        name_lbl.setStyleSheet(f"color: {color}; font-weight: 900; font-size: 12px; letter-spacing: 2px;")
        score_lbl = QLabel("0 ⭐")
        score_lbl.setStyleSheet("color: #ffd700; font-weight: 900; font-size: 15px;")
        top_row.addWidget(name_lbl)
        top_row.addStretch()
        top_row.addWidget(score_lbl)
        lay.addLayout(top_row)

        bot_row = QHBoxLayout()
        cartons = CartonWidget()
        count_lbl = QLabel("0/11 JOUEURS")
        count_lbl.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 10px; font-weight: 700;")
        bot_row.addWidget(count_lbl)
        bot_row.addStretch()
        
        # 7 Slots de remplaçants
        bench_lay = QHBoxLayout()
        bench_lay.setSpacing(5)
        frame.bench_slots = []
        for _ in range(7):
            slot = BenchSlot(color)
            bench_lay.addWidget(slot)
            frame.bench_slots.append(slot)
        bot_row.addLayout(bench_lay)
        
        bot_row.addStretch()
        bot_row.addWidget(cartons)
        lay.addLayout(bot_row)

        # Attach labels to frame for updates
        frame.name_lbl = name_lbl
        frame.score_lbl = score_lbl
        frame.count_lbl = count_lbl
        frame.cartons = cartons
        return frame

    def update_state(self, game_state):
        if not game_state: return
        self._gs = game_state
        tb = game_state.team_bleu
        tr = game_state.team_rouge

        self.header_bleu.name_lbl.setText(tb.name.upper())
        self.header_bleu.count_lbl.setText(f"{len(tb.players)}/18 JOUEURS")
        self.header_bleu.cartons.update_cartons(tb.jaunes, tb.rouges)
        self.header_bleu.score_lbl.setText(f"{tb.total_rating_revealed} ⭐")
        # Update Bench Bleu
        bench_bleu = tb.formation.get("BENCH", [])
        for i, slot in enumerate(self.header_bleu.bench_slots):
            slot.set_player(bench_bleu[i] if i < len(bench_bleu) else None)

        self.header_rouge.name_lbl.setText(tr.name.upper())
        self.header_rouge.count_lbl.setText(f"{len(tr.players)}/18 JOUEURS")
        self.header_rouge.cartons.update_cartons(tr.jaunes, tr.rouges)
        self.header_rouge.score_lbl.setText(f"{tr.total_rating_revealed} ⭐")
        # Update Bench Rouge
        bench_rouge = tr.formation.get("BENCH", [])
        for i, slot in enumerate(self.header_rouge.bench_slots):
            slot.set_player(bench_rouge[i] if i < len(bench_rouge) else None)

        # Decide which players to show on pitch depending on current view
        local_color = getattr(self, "_local_color", None) or "rouge"
        
        if self._view_opponent:
            # show opponent only
            if local_color == "rouge":
                # local is rouge → show bleu (opponent)
                self.pitch.set_players([], tb.players)
            else:
                # local is bleu → show rouge (opponent)
                self.pitch.set_players(tr.players, [])
        else:
            # show local only
            if local_color == "rouge":
                self.pitch.set_players(tr.players, [])
            else:
                self.pitch.set_players([], tb.players)

    def set_local_color(self, color: str | None):
        """Inform the panel which side is local ("rouge" or "bleu").
        If None, falls back to showing both teams.
        """
        self._local_color = color
        self._view_opponent = False
        # Update header labels to reflect which is local (visual only)
        if color == "rouge":
            self.header_rouge.score_lbl.setStyleSheet("color: #ffd700; font-weight: 900; font-size: 15px;")
        elif color == "bleu":
            self.header_bleu.score_lbl.setStyleSheet("color: #ffd700; font-weight: 900; font-size: 15px;")

    def toggle_view_opponent(self):
        self._view_opponent = not getattr(self, "_view_opponent", False)
        if hasattr(self, 'view_toggle_btn'):
            self.view_toggle_btn.setText("👁️ VOIR MON ÉQUIPE" if self._view_opponent else "👁️ VOIR ADVERSAIRE")
        # Force redraw using current game state if available
        if hasattr(self, "_gs") and self._gs:
            self.update_state(self._gs)

    # ── Gestion Drag & Drop Globale ───────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            # 1. Vérifier le terrain
            pitch_pos = self.pitch.mapFromParent(pos)
            for p, rect in self.pitch._player_rects.items():
                if rect.contains(pitch_pos):
                    self._dragged_player = p
                    self.setCursor(Qt.ClosedHandCursor)
                    return
            # 2. Vérifier les bancs
            for header in [self.header_bleu, self.header_rouge]:
                h_pos = header.mapFromParent(pos)
                for slot in header.bench_slots:
                    s_pos = slot.mapFrom(header, h_pos)
                    if slot.rect().contains(s_pos) and slot.player:
                        self._dragged_player = slot.player
                        self.setCursor(Qt.ClosedHandCursor)
                        return

    def mouseMoveEvent(self, event):
        if self._dragged_player:
            # On met à jour la position visuelle dans le terrain pour le feedback
            pitch_pos = self.pitch.mapFromParent(event.pos())
            w, h = self.pitch.width(), self.pitch.height()
            xr = pitch_pos.x() / w
            yr = pitch_pos.y() / h
            self._dragged_player.pitch_pos = (xr, yr)
            self.pitch._dragged_player = self._dragged_player # Synchro pour le paintEvent
            self.pitch.update()

    def mouseReleaseEvent(self, event):
        if self._dragged_player:
            pos = event.pos()
            p = self._dragged_player
            self._dragged_player = None
            self.pitch._dragged_player = None # Reset synchro
            self.setCursor(Qt.ArrowCursor)

            # Vérifier si on lâche sur un banc
            for team_color, header in [("bleu", self.header_bleu), ("rouge", self.header_rouge)]:
                h_pos = header.mapFromParent(pos)
                if header.rect().contains(h_pos):
                    # Trouver le slot ou juste lacher dans le header
                    team = self._gs.get_team(team_color)
                    team.move_player(p, "BENCH")
                    self.update_state(self._gs)
                    return
            
            # Vérifier si on lâche sur le terrain
            pitch_pos = self.pitch.mapFromParent(pos)
            if self.pitch.rect().contains(pitch_pos):
                # On le garde sur le terrain (déjà mis à jour dans mouseMove)
                # Mais il faut s'assurer qu'il n'est plus marqué comme BENCH
                for team in [self._gs.team_bleu, self._gs.team_rouge]:
                    if p in team.players:
                        # Si il était sur le banc, on essaie de le remettre dans un slot
                        if p in team.formation["BENCH"]:
                            team.move_player(p, "FIELD") # FIELD est un alias pour trouver le 1er slot libre
                self.update_state(self._gs)
            else:
                # Hors zone : on ne change rien ou on reset
                self.update_state(self._gs)

class ImageButton(QPushButton):
    """Bouton utilisant une image avec effet de lumière lors de la sélection"""
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path.replace("\\", "/")
        self.selected = False
        self.setCursor(Qt.PointingHandCursor)
        self._pixmap = QPixmap(self.image_path) if os.path.exists(self.image_path) else None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        rect = self.rect()
        center = rect.center()
        
        if self.selected:
            glow = QRadialGradient(center, min(rect.width(), rect.height()) * 0.8)
            glow.setColorAt(0, QColor(255, 255, 255, 100))
            glow.setColorAt(0.5, QColor(255, 255, 255, 40))
            glow.setColorAt(1, QColor(255, 255, 255, 0))
            
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(rect.adjusted(-20, -20, 20, 20))
        
        if self._pixmap and not self._pixmap.isNull():
            pix_size = self._pixmap.size()
            pix_size.scale(rect.size(), Qt.KeepAspectRatio)
            target_rect = QRect(
                rect.center().x() - pix_size.width() // 2,
                rect.center().y() - pix_size.height() // 2,
                pix_size.width(),
                pix_size.height()
            )
            painter.drawPixmap(target_rect, self._pixmap)
        painter.end()

class TeamLineupPanel(QFrame):
    player_clicked = pyqtSignal(object)

    def __init__(self, team_color: str, parent=None):
        super().__init__(parent)
        self.team_color = team_color
        self._accent = "#ff4444" if team_color == "rouge" else "#00d4ff"
        self.is_interactive = False 

        self.setStyleSheet("background: transparent; border: none;")
        self.setMinimumWidth(400)

        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(22, 18, 22, 18)
        self._lay.setSpacing(6)

    def _clear_sub_layout(self, layout):
        if not layout: return
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                w = item.widget()
                w.setParent(None)
                w.deleteLater()
            elif item.layout():
                self._clear_sub_layout(item.layout())

    def load(self, team_state, score: int = None, is_winner: bool = False, show_ratings: bool = False, interactive: bool = False):
        self.is_interactive = interactive
        # 1. Nettoyage
        while self._lay.count():
            item = self._lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_sub_layout(item.layout())

        # 2. Titre
        title = QLabel(f"STARTING XI ({team_state.name.upper()})")
        title.setStyleSheet("color: white; font-size: 22px; font-weight: 900; letter-spacing: 2px; background: transparent;")
        self._lay.addWidget(title)

        if score is not None:
            prefix = "🏆 " if is_winner else "⭐ "
            s_lbl = QLabel(f"{prefix}{score}")
            s_lbl.setStyleSheet(f"color: {'#00e676' if is_winner else 'white'}; font-size: 24px; font-weight: 900; background: transparent;")
            self._lay.addWidget(s_lbl)

        # 3. Séparation Titulaires / Remplaçants
        # On s'assure d'avoir les 11 premiers (ceux qui ont un pitch_pos)
        starters = [p for p in team_state.players if p.pitch_pos is not None][:11]
        bench = [p for p in team_state.players if p not in starters]

        # Fonction interne pour créer une ligne de joueur
        def create_player_row(p, index=None):
            row = QFrame()
            row.setObjectName("playerRow")
            if self.is_interactive:
                row.setCursor(Qt.PointingHandCursor)
                # Utilisation d'un slot nommé pour éviter les problèmes de portée de lambda
                row.mousePressEvent = lambda e, player=p: self.player_clicked.emit(player)
                row.setStyleSheet("""
                    QFrame#playerRow { background: rgba(255,255,255,0.05); border-radius: 8px; }
                    QFrame#playerRow:hover { background: rgba(255,255,255,0.15); border: 1px solid white; }
                """)
            else:
                row.setStyleSheet("background: transparent; border: none;")

            rlay = QHBoxLayout(row)
            rlay.setContentsMargins(10, 5, 10, 5)
            
            if index:
                num = QLabel(f"{index:02d}")
                num.setStyleSheet("color: rgba(255,255,255,0.4); font-weight: 900; font-size: 14px; background: transparent;")
                num.setFixedWidth(25)
                rlay.addWidget(num)
            
            name_text = f"{p.name.upper()} <span style='font-size:11px; color:#aaa;'>({p.position})</span>"
            name = QLabel(name_text)
            name.setStyleSheet(f"color: {COLOR_GREEN}; font-size: 16px; font-weight: 800; background: transparent;")
            rlay.addWidget(name)
            
            if show_ratings:
                rlay.addStretch()
                rat = QLabel(f"⭐ {p.get_rating_force()}")
                rat.setStyleSheet("color: #ffd700; font-weight: 900; background: transparent;")
                rlay.addWidget(rat)
            else:
                rlay.addStretch()
            
            return row

        # Ajout titulaires
        for i, p in enumerate(starters, 1):
            self._lay.addWidget(create_player_row(p, i))

        # Ajout remplaçants
        if bench:
            self._lay.addSpacing(15)
            sub_title = QLabel("SUBSTITUTES")
            sub_title.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 13px; font-weight: 900; letter-spacing: 2px; background: transparent;")
            self._lay.addWidget(sub_title)
            for p in bench:
                self._lay.addWidget(create_player_row(p))

        self._lay.addStretch()

        self._lay.addStretch()

