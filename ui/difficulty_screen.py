# ============================================================
# ui/difficulty_screen.py — Sélection difficulté IA
# ============================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel)
from PyQt5.QtCore    import Qt, pyqtSignal
from PyQt5.QtGui     import QPainter, QColor, QLinearGradient
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COLOR_GREEN, COLOR_GRAY, COLOR_ROUGE, COLOR_BLEU


class DifficultyScreen(QWidget):
    """
    Écran de sélection de difficulté pour le mode VS AGENT.
    Propose 3 niveaux : Facile / Moyen / Difficile.
    """

    difficulty_selected = pyqtSignal(str)    # "easy", "medium", "hard"
    back_pressed        = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected = "medium"
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setAutoFillBackground(False)
        self._setup_ui()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0a0a0a"))
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(0, 40, 80, 60))
        gradient.setColorAt(0.5, QColor(0, 0, 0, 0))
        gradient.setColorAt(1.0, QColor(0, 40, 80, 40))
        painter.fillRect(self.rect(), gradient)

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(60, 40, 60, 40)
        main.setSpacing(0)

        main.addStretch(2)

        # ── Icône robot ──────────────────────────────────
        icon = QLabel("🤖")
        icon.setStyleSheet("font-size: 60px; background: transparent;")
        icon.setAlignment(Qt.AlignCenter)
        main.addWidget(icon)

        main.addSpacing(10)

        # ── Titre ────────────────────────────────────────
        title = QLabel("MODE VS AGENT")
        title.setStyleSheet(f"""
            color: {COLOR_GREEN};
            font-size: 32px;
            font-weight: 900;
            letter-spacing: 5px;
            background: transparent;
        """)
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        main.addSpacing(6)

        subtitle = QLabel("Choisissez le niveau de difficulté de l'agent IA")
        subtitle.setStyleSheet(f"""
            color: {COLOR_GRAY};
            font-size: 13px;
            letter-spacing: 2px;
            background: transparent;
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        main.addWidget(subtitle)

        main.addStretch(1)

        # ── 3 boutons difficulté ─────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(20)
        cards_row.setContentsMargins(80, 0, 80, 0)

        self._diff_btns = {}
        difficulties = [
            ("easy", "🟢", "FACILE", (
                "Agent débutant\n"
                "• Choix quasi-aléatoires\n"
                "• Buzz lent (~3s)\n"
                "• 35% bonnes réponses"
            )),
            ("medium", "🟡", "MOYEN", (
                "Agent intermédiaire\n"
                "• Bon instinct\n"
                "• Buzz modéré (~1.8s)\n"
                "• 60% bonnes réponses"
            )),
            ("hard", "🔴", "DIFFICILE", (
                "Agent expert\n"
                "• Quasi-optimal\n"
                "• Buzz rapide (~0.8s)\n"
                "• 85% bonnes réponses"
            )),
        ]

        for key, icon_txt, label, desc in difficulties:
            btn = QPushButton(f"{icon_txt}\n\n{label}\n\n{desc}")
            btn.setFixedHeight(220)
            btn.setStyleSheet(self._card_style(False))
            btn.clicked.connect(lambda _, k=key: self._select(k))
            self._diff_btns[key] = btn
            cards_row.addWidget(btn)

        main.addLayout(cards_row)

        main.addStretch(1)

        # ── Boutons bas ──────────────────────────────────
        btns_row = QHBoxLayout()
        btns_row.setContentsMargins(120, 0, 120, 0)
        btns_row.setSpacing(20)

        back_btn = QPushButton("⬅   Retour")
        back_btn.setFixedHeight(52)
        back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.08);
                color: rgba(255,255,255,0.7);
                border: 2px solid rgba(255,255,255,0.15);
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.15);
                border-color: rgba(255,255,255,0.3);
                color: white;
            }
        """)
        back_btn.clicked.connect(self.back_pressed)
        btns_row.addWidget(back_btn)

        self.start_btn = QPushButton("🤖   LANCER VS AGENT !")
        self.start_btn.setFixedHeight(52)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00b844, stop:1 {COLOR_GREEN});
                color: #000000;
                border: none;
                border-radius: 12px;
                font-size: 16px;
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
        btns_row.addWidget(self.start_btn, stretch=2)

        main.addLayout(btns_row)

        main.addStretch(1)

        # Sélection par défaut
        self._select("medium")

    # ── Helpers ──────────────────────────────────────────
    def _card_style(self, selected: bool) -> str:
        if selected:
            return f"""
                QPushButton {{
                    background: rgba(0,200,100,0.15);
                    color: {COLOR_GREEN};
                    border: 3px solid {COLOR_GREEN};
                    border-radius: 16px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 14px;
                    line-height: 1.6;
                }}
            """
        return """
            QPushButton {
                background: rgba(255,255,255,0.05);
                color: rgba(255,255,255,0.6);
                border: 2px solid rgba(255,255,255,0.10);
                border-radius: 16px;
                font-size: 12px;
                font-weight: bold;
                padding: 14px;
                line-height: 1.6;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.10);
                border-color: rgba(255,255,255,0.25);
                color: white;
            }
        """

    def _select(self, key: str):
        self._selected = key
        for k, btn in self._diff_btns.items():
            btn.setStyleSheet(self._card_style(k == key))

    def _on_start(self):
        self.difficulty_selected.emit(self._selected)
