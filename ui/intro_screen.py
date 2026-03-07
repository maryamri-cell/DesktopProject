# ============================================================
# ui/intro_screen.py — Écran d'accueil, zéro rectangle gris
# ============================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QLineEdit)
from PyQt5.QtCore    import Qt, pyqtSignal
from PyQt5.QtGui     import QPixmap, QPainter, QColor, QLinearGradient
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config     import COLOR_GREEN, COLOR_GRAY, COLOR_ROUGE, COLOR_BLEU
from game.state import GameMode

BG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "background.png"
)


class IntroScreen(QWidget):
    game_start = pyqtSignal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_mode = GameMode.LOCAL
        self._bg_pixmap     = QPixmap(BG_PATH) if os.path.exists(BG_PATH) else None

        # ── CRITIQUE : rendre le widget transparent ───────
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setAutoFillBackground(False)

        self._setup_ui()

    # ── Background dessiné directement ───────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Fond noir de base
        painter.fillRect(self.rect(), QColor("#0a0a0a"))

        # Image de fond
        if self._bg_pixmap and not self._bg_pixmap.isNull():
            scaled = self._bg_pixmap.scaled(
                self.width(), self.height(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            x = (self.width()  - scaled.width())  // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        # Overlay gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.00, QColor(0, 0, 0, 90))
        gradient.setColorAt(0.35, QColor(0, 0, 0, 40))
        gradient.setColorAt(0.60, QColor(0, 0, 0, 140))
        gradient.setColorAt(1.00, QColor(0, 0, 0, 220))
        painter.fillRect(self.rect(), gradient)

    # ── UI : TOUT dans un seul layout, zéro QWidget fils ──
    def _setup_ui(self):
        # Layout racine directement sur self — pas de QWidget intermédiaire
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 28, 0, 24)
        main.setSpacing(0)

        # ── Badge haut ────────────────────────────────────
        badge = QLabel("⚽   FOOTBALL DRAFT QUIZ")
        badge.setStyleSheet(f"""
            color: {COLOR_GREEN};
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 5px;
            background: transparent;
            border: none;
        """)
        badge.setAlignment(Qt.AlignCenter)
        badge.setAttribute(Qt.WA_TransparentForMouseEvents)
        main.addWidget(badge)

        main.addStretch(3)

        # ── Inputs équipes ────────────────────────────────
        hint = QLabel("ENTREZ LES NOMS DES ÉQUIPES")
        hint.setStyleSheet("""
            color: rgba(255,255,255,0.55);
            font-size: 11px;
            letter-spacing: 4px;
            background: transparent;
            border: none;
        """)
        hint.setAlignment(Qt.AlignCenter)
        main.addWidget(hint)

        main.addSpacing(14)

        # Row inputs
        row_w = QWidget(self)
        row_w.setAttribute(Qt.WA_TranslucentBackground)
        row_w.setAutoFillBackground(False)
        row_w.setStyleSheet("background: transparent; border: none;")
        row = QHBoxLayout(row_w)
        row.setContentsMargins(160, 0, 160, 0)
        row.setSpacing(18)

        # Équipe rouge
        rcol = QVBoxLayout()
        rcol.setSpacing(6)
        rlbl = QLabel("🔴  ÉQUIPE ROUGE")
        rlbl.setStyleSheet(f"""
            color: {COLOR_ROUGE};
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 2px;
            background: transparent;
            border: none;
        """)
        rlbl.setAlignment(Qt.AlignCenter)
        self.input_rouge = QLineEdit("Équipe Rouge")
        self.input_rouge.setFixedHeight(50)
        self.input_rouge.setAlignment(Qt.AlignCenter)
        self.input_rouge.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(180,30,30,0.30);
                color: white;
                border: 2px solid {COLOR_ROUGE};
                border-radius: 12px;
                padding: 0 18px;
                font-size: 15px;
                font-weight: bold;
            }}
            QLineEdit:focus {{
                background: rgba(220,60,60,0.40);
                border-color: #ff9999;
            }}
        """)
        rcol.addWidget(rlbl)
        rcol.addWidget(self.input_rouge)
        row.addLayout(rcol)

        # VS
        vs = QLabel("VS")
        vs.setStyleSheet(f"""
            color: {COLOR_GREEN};
            font-size: 26px;
            font-weight: 900;
            background: transparent;
            border: none;
        """)
        vs.setAlignment(Qt.AlignCenter)
        vs.setFixedWidth(54)
        row.addWidget(vs)

        # Équipe bleue
        bcol = QVBoxLayout()
        bcol.setSpacing(6)
        blbl = QLabel("🔵  ÉQUIPE BLEUE")
        blbl.setStyleSheet(f"""
            color: {COLOR_BLEU};
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 2px;
            background: transparent;
            border: none;
        """)
        blbl.setAlignment(Qt.AlignCenter)
        self.input_bleu = QLineEdit("Équipe Bleue")
        self.input_bleu.setFixedHeight(50)
        self.input_bleu.setAlignment(Qt.AlignCenter)
        self.input_bleu.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(30,80,200,0.30);
                color: white;
                border: 2px solid {COLOR_BLEU};
                border-radius: 12px;
                padding: 0 18px;
                font-size: 15px;
                font-weight: bold;
            }}
            QLineEdit:focus {{
                background: rgba(50,100,230,0.40);
                border-color: #99aaff;
            }}
        """)
        bcol.addWidget(blbl)
        bcol.addWidget(self.input_bleu)
        row.addLayout(bcol)

        main.addWidget(row_w)
        main.addStretch(1)

        # ── Mode hint ─────────────────────────────────────
        mode_hint = QLabel("CHOISISSEZ VOTRE MODE DE JEU")
        mode_hint.setStyleSheet("""
            color: rgba(255,255,255,0.50);
            font-size: 10px;
            letter-spacing: 4px;
            background: transparent;
            border: none;
        """)
        mode_hint.setAlignment(Qt.AlignCenter)
        main.addWidget(mode_hint)

        main.addSpacing(10)

        # ── 3 boutons modes ───────────────────────────────
        modes_w = QWidget(self)
        modes_w.setAttribute(Qt.WA_TranslucentBackground)
        modes_w.setAutoFillBackground(False)
        modes_w.setStyleSheet("background: transparent; border: none;")
        modes_row = QHBoxLayout(modes_w)
        modes_row.setContentsMargins(50, 0, 50, 0)
        modes_row.setSpacing(14)

        self.mode_buttons = {}
        modes = [
            (GameMode.LOCAL,  "⚽", "LOCAL",    "2 Joueurs · Même PC\nTouches  Q  et  P"),
            (GameMode.VS_AI,  "🤖", "VS AGENT", "1 Joueur · Contre l'IA\nAgent adaptatif"),
            (GameMode.ONLINE, "🌐", "EN LIGNE",  "2 Joueurs · Distance\nMultijoueur Supabase"),
        ]
        for mode, icon, label, desc in modes:
            btn = QPushButton(f"{icon}\n{label}\n{desc}")
            btn.setFixedHeight(105)
            btn.setStyleSheet(self._mode_style(False))
            btn.clicked.connect(lambda _, m=mode: self._select_mode(m))
            self.mode_buttons[mode] = btn
            modes_row.addWidget(btn)

        main.addWidget(modes_w)
        main.addSpacing(14)

        # ── Bouton START ──────────────────────────────────
        start_w = QWidget(self)
        start_w.setAttribute(Qt.WA_TranslucentBackground)
        start_w.setAutoFillBackground(False)
        start_w.setStyleSheet("background: transparent; border: none;")
        start_lay = QHBoxLayout(start_w)
        start_lay.setContentsMargins(50, 0, 50, 0)

        self.start_btn = QPushButton("🚀   LANCER LE MATCH !")
        self.start_btn.setFixedHeight(62)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00b844, stop:1 {COLOR_GREEN});
                color: #000000;
                border: none;
                border-radius: 14px;
                font-size: 18px;
                font-weight: 900;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #33d068, stop:1 #55ff99);
            }}
            QPushButton:pressed {{
                background: #009938;
            }}
        """)
        self.start_btn.clicked.connect(self._on_start)
        start_lay.addWidget(self.start_btn)
        main.addWidget(start_w)

        main.addSpacing(10)

        # ── Info touches ──────────────────────────────────
        keys = QLabel("⌨️   Buzz : touche  Q  (rouge)   ·   P  (bleue)")
        keys.setStyleSheet("""
            color: rgba(255,255,255,0.35);
            font-size: 11px;
            background: transparent;
            border: none;
        """)
        keys.setAlignment(Qt.AlignCenter)
        main.addWidget(keys)

        # Mode par défaut
        self._select_mode(GameMode.LOCAL)

    # ── Helpers ──────────────────────────────────────────
    def _mode_style(self, selected: bool) -> str:
        if selected:
            return f"""
                QPushButton {{
                    background: rgba(0,200,100,0.22);
                    color: {COLOR_GREEN};
                    border: 2px solid {COLOR_GREEN};
                    border-radius: 14px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 8px;
                    line-height: 1.7;
                }}
            """
        return """
            QPushButton {
                background: rgba(255,255,255,0.07);
                color: rgba(255,255,255,0.65);
                border: 2px solid rgba(255,255,255,0.12);
                border-radius: 14px;
                font-size: 12px;
                font-weight: bold;
                padding: 8px;
                line-height: 1.7;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.13);
                border-color: rgba(255,255,255,0.30);
                color: white;
            }
        """

    def _select_mode(self, mode: GameMode):
        self._selected_mode = mode
        for m, btn in self.mode_buttons.items():
            btn.setStyleSheet(self._mode_style(m == mode))

    def _on_start(self):
        nom_rouge = self.input_rouge.text().strip() or "Équipe Rouge"
        nom_bleu  = self.input_bleu.text().strip()  or "Équipe Bleue"
        self.game_start.emit(self._selected_mode.value, nom_rouge, nom_bleu)
