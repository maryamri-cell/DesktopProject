# ============================================================
# ui/buzz_screen.py — Écran de buzz + question
# ============================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QFrame)
from PyQt5.QtCore    import Qt, pyqtSignal, QTimer
from PyQt5.QtGui     import QKeyEvent
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config      import COLOR_GREEN, COLOR_ROUGE, COLOR_BLEU, COLOR_GRAY, BUZZ_KEY_ROUGE, BUZZ_KEY_BLEU
from ui.styles   import STYLE_BUZZ_ROUGE, STYLE_BUZZ_BLEU
from ui.widgets  import TeamPanel, ProgressManche, SeparatorLine, SubtitleLabel


class BuzzScreen(QWidget):
    """
    Écran principal du jeu :
    - Affiche la question + position à gagner
    - 2 boutons BUZZ (Q pour rouge, P pour bleu)
    - Panels latéraux avec état des équipes
    """

    # Signal émis quand une équipe buzze : "rouge" ou "bleu"
    buzzed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buzz_enabled = False
        self._setup_ui()
        self.setFocusPolicy(Qt.StrongFocus)

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # ── Panel équipe rouge (gauche) ───────────────────
        self.team_rouge_panel = TeamPanel("Équipe Rouge", "rouge")
        self.team_rouge_panel.setFixedWidth(220)
        root.addWidget(self.team_rouge_panel)

        # ── Centre ───────────────────────────────────────
        center = QVBoxLayout()
        center.setSpacing(16)

        # Barre de progression
        self.progress = ProgressManche(total=11)
        center.addWidget(self.progress)

        sep1 = SeparatorLine()
        center.addWidget(sep1)

        # Position à gagner
        self.position_lbl = QLabel("🎯 Position : Attaquant (ST)")
        self.position_lbl.setStyleSheet(
            f"color: {COLOR_GREEN}; font-size: 14px; font-weight: bold; "
            f"background: transparent; letter-spacing: 1px;"
        )
        self.position_lbl.setAlignment(Qt.AlignCenter)
        center.addWidget(self.position_lbl)

        # Box question
        question_frame = QFrame()
        question_frame.setStyleSheet("""
            QFrame {
                background-color: #111111;
                border: 2px solid #2a2a2a;
                border-radius: 16px;
            }
        """)
        q_layout = QVBoxLayout(question_frame)
        q_layout.setContentsMargins(30, 24, 30, 24)

        self.question_lbl = QLabel("Chargement de la question...")
        self.question_lbl.setStyleSheet(
            "color: white; font-size: 20px; font-weight: bold; "
            "background: transparent; line-height: 1.5;"
        )
        self.question_lbl.setAlignment(Qt.AlignCenter)
        self.question_lbl.setWordWrap(True)
        q_layout.addWidget(self.question_lbl)
        center.addWidget(question_frame)

        # Boutons BUZZ
        buzz_layout = QHBoxLayout()
        buzz_layout.setSpacing(40)

        self.buzz_rouge_btn = QPushButton(f"🔔  BUZZ\n[Touche {BUZZ_KEY_ROUGE}]")
        self.buzz_rouge_btn.setFixedSize(200, 100)
        self.buzz_rouge_btn.setStyleSheet(STYLE_BUZZ_ROUGE)
        self.buzz_rouge_btn.clicked.connect(lambda: self._on_buzz("rouge"))

        self.buzz_bleu_btn = QPushButton(f"🔔  BUZZ\n[Touche {BUZZ_KEY_BLEU}]")
        self.buzz_bleu_btn.setFixedSize(200, 100)
        self.buzz_bleu_btn.setStyleSheet(STYLE_BUZZ_BLEU)
        self.buzz_bleu_btn.clicked.connect(lambda: self._on_buzz("bleu"))

        buzz_layout.addStretch()
        buzz_layout.addWidget(self.buzz_rouge_btn)
        buzz_layout.addWidget(self.buzz_bleu_btn)
        buzz_layout.addStretch()
        center.addLayout(buzz_layout)

        # Message d'état
        self.status_lbl = QLabel("Appuyez sur Q ou P pour buzzer !")
        self.status_lbl.setStyleSheet(
            f"color: {COLOR_GRAY}; font-size: 13px; background: transparent;"
        )
        self.status_lbl.setAlignment(Qt.AlignCenter)
        center.addWidget(self.status_lbl)
        center.addStretch()

        root.addLayout(center)

        # ── Panel équipe bleue (droite) ───────────────────
        self.team_bleu_panel = TeamPanel("Équipe Bleue", "bleu")
        self.team_bleu_panel.setFixedWidth(220)
        root.addWidget(self.team_bleu_panel)

    # ── API Publique ──────────────────────────────────────
    def load_question(self, question: dict, manche: int,
                      position_label: str, game_state):
        """Charge une nouvelle question dans l'écran"""
        self.question_lbl.setText(question.get("question", "..."))
        self.position_lbl.setText(f"🎯 Position à gagner : {position_label}")
        self.progress.update_progress(manche)
        self.status_lbl.setText("Appuyez sur Q ou P pour buzzer !")
        self._buzz_enabled = True
        self._enable_buzz_buttons(True)
        self._update_teams(game_state)
        self.setFocus()

    def disable_buzz(self):
        """Désactive les boutons buzz (équipe a buzzé)"""
        self._buzz_enabled = False
        self._enable_buzz_buttons(False)

    def update_teams(self, game_state):
        self._update_teams(game_state)

    def show_buzzed(self, color: str):
        """Affiche visuellement quelle équipe a buzzé"""
        name = "Équipe Rouge" if color == "rouge" else "Équipe Bleue"
        self.status_lbl.setText(f"🔔 {name} a buzzé ! Elle répond...")
        self.status_lbl.setStyleSheet(
            f"color: {COLOR_ROUGE if color == 'rouge' else COLOR_BLEU}; "
            f"font-size: 15px; font-weight: bold; background: transparent;"
        )

    # ── Clavier ──────────────────────────────────────────
    def keyPressEvent(self, event: QKeyEvent):
        if not self._buzz_enabled:
            return
        key = event.text().upper()
        if key == BUZZ_KEY_ROUGE:
            self._on_buzz("rouge")
        elif key == BUZZ_KEY_BLEU:
            self._on_buzz("bleu")

    # ── Interne ──────────────────────────────────────────
    def _on_buzz(self, color: str):
        if not self._buzz_enabled:
            return
        self._buzz_enabled = False
        self._enable_buzz_buttons(False)
        self.show_buzzed(color)
        self.buzzed.emit(color)

    def _enable_buzz_buttons(self, enabled: bool):
        self.buzz_rouge_btn.setEnabled(enabled)
        self.buzz_bleu_btn.setEnabled(enabled)

    def _update_teams(self, game_state):
        if game_state:
            self.team_rouge_panel.update_state(game_state.team_rouge)
            self.team_bleu_panel.update_state(game_state.team_bleu)

    def force_buzz(self, color: str):
        """Déclenche un buzz depuis l'extérieur (agent IA)"""
        self._on_buzz(color)
