# ============================================================
# ui/difficulty_screen.py — Sélection difficulté IA
# ============================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel)
from ui.widgets import ImageButton
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
        from PyQt5.QtGui import QPixmap
        painter = QPainter(self)
        bg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Gemini_Generated_Image_81bu7x81bu7x81bu.png")
        if os.path.exists(bg_path):
            pix = QPixmap(bg_path)
            painter.drawPixmap(self.rect(), pix)
            # Overlay sombre pour améliorer la lisibilité du texte par-dessus
            painter.fillRect(self.rect(), QColor(0, 0, 0, 150))
        else:
            painter.fillRect(self.rect(), QColor("#0a0a0a"))
            
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(0, 40, 80, 60))
        gradient.setColorAt(0.5, QColor(0, 0, 0, 0))
        gradient.setColorAt(1.0, QColor(0, 40, 80, 40))
        painter.fillRect(self.rect(), gradient)

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(60, 10, 60, 40)
        main.setSpacing(0)


        # ── Logo Ahsan Khota ─────────────────────────────
        logo_lbl = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Gemini_Generated_Image_w4q5buw4q5buw4q5-removebg-preview.png")
        if os.path.exists(logo_path):
            from PyQt5.QtGui import QPixmap
            pix = QPixmap(logo_path)
            logo_lbl.setPixmap(pix.scaled(600, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_lbl.setText("AHSAN KHOTA")
            logo_lbl.setStyleSheet("color: #ffd700; font-size: 32px; font-weight: 900; background: transparent; border: none;")
        
        logo_lbl.setStyleSheet("background: transparent; border: none;")
        logo_lbl.setAlignment(Qt.AlignCenter)
        main.addWidget(logo_lbl)

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
                "Débutant (Culture foot limitée)\n"
                "• Réactions lentes (~3.5s)\n"
                "• Hésite et skip souvent\n"
                "• ~40% de bonnes réponses"
            )),
            ("medium", "🟡", "MOYEN", (
                "Amateur (Bonne culture)\n"
                "• Réactions équilibrées (~2.5s)\n"
                "• Quelques erreurs stratégiques\n"
                "• ~65% de bonnes réponses"
            )),
            ("hard", "🔴", "DIFFICILE", (
                "Expert (Fan inconditionnel)\n"
                "• Réactions rapides (~1.6s)\n"
                "• Agressif sur le buzz\n"
                "• ~88% de bonnes réponses"
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

        btn_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Gemini_Generated_Image_i8tfvei8tfvei8tf-removebg-preview.png")
        if os.path.exists(btn_path):
            self.start_btn = ImageButton(btn_path)
            self.start_btn.setFixedHeight(120)
            self.start_btn.setStyleSheet("background: transparent; border: none;")
        else:
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
                    background: rgba(255, 215, 0, 0.15);
                    color: #ffd700;
                    border: 3px solid #ffd700;
                    border-radius: 16px;
                    font-size: 13px;
                    font-weight: bold;
                    padding: 14px;
                    line-height: 1.6;
                }}
            """
        return """
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.6);
                border: 2px solid rgba(255, 215, 0, 0.4);
                border-radius: 16px;
                font-size: 13px;
                font-weight: bold;
                padding: 14px;
                line-height: 1.6;
            }
            QPushButton:hover {
                background: rgba(255, 215, 0, 0.10);
                border-color: rgba(255, 215, 0, 0.8);
                color: white;
            }
        """

    def _select(self, key: str):
        self._selected = key
        for k, btn in self._diff_btns.items():
            btn.setStyleSheet(self._card_style(k == key))

    def _on_start(self):
        self.difficulty_selected.emit(self._selected)
