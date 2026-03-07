# ============================================================
# ui/answer_screen.py — Écran de réponse avec timer visuel
# ============================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QFrame, QProgressBar)
from PyQt5.QtCore    import Qt, pyqtSignal, QTimer
from PyQt5.QtGui     import QFont, QPainter, QColor, QLinearGradient
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config  import (COLOR_GREEN, COLOR_ROUGE, COLOR_BLEU, COLOR_GRAY,
                     COLOR_WHITE, COLOR_CARD_BG)
from ui.styles  import STYLE_OPTION_BTN
from ui.widgets import TeamPanel, ProgressManche, SeparatorLine

TIMER_SECONDS = 15   # temps pour répondre


class TimerBar(QWidget):
    """Barre de timer animée qui diminue"""
    timeout = pyqtSignal()

    def __init__(self, seconds=TIMER_SECONDS, parent=None):
        super().__init__(parent)
        self._total    = seconds * 10   # en dixièmes de seconde
        self._current  = self._total
        self._running  = False
        self._color    = QColor(COLOR_GREEN)
        self.setFixedHeight(14)

        self._timer = QTimer(self)
        self._timer.setInterval(100)   # 100ms = 0.1s
        self._timer.timeout.connect(self._tick)

    def start(self):
        self._current = self._total
        self._running = True
        self._timer.start()
        self.update()

    def stop(self):
        self._running = False
        self._timer.stop()

    def reset(self):
        self.stop()
        self._current = self._total
        self.update()

    def _tick(self):
        if self._current > 0:
            self._current -= 1
            self.update()
        else:
            self.stop()
            self.timeout.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        ratio = self._current / self._total if self._total > 0 else 0

        # Fond
        painter.setBrush(QColor("#1a1a1a"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 7, 7)

        # Barre colorée
        if ratio > 0:
            fill_w = int(w * ratio)
            if ratio > 0.5:
                color = QColor(COLOR_GREEN)
            elif ratio > 0.25:
                color = QColor("#ffc107")
            else:
                color = QColor(COLOR_ROUGE)
            painter.setBrush(color)
            painter.drawRoundedRect(0, 0, fill_w, h, 7, 7)

    def remaining_seconds(self) -> int:
        return self._current // 10


class AnswerScreen(QWidget):
    """
    Écran de réponse :
    - Affiche la question + 4 options
    - Timer visuel dégressif
    - Indique quelle équipe répond
    - Émet le signal answer_selected(option_str)
    """

    answer_selected = pyqtSignal(str)   # option choisie
    timer_expired   = pyqtSignal()      # temps écoulé

    def __init__(self, parent=None):
        super().__init__(parent)
        self._answering_team = None
        self._options        = []
        self._enabled        = False
        self._setup_ui()

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # ── Panel équipe rouge ────────────────────────────
        self.team_rouge_panel = TeamPanel("Équipe Rouge", "rouge")
        self.team_rouge_panel.setFixedWidth(200)
        root.addWidget(self.team_rouge_panel)

        # ── Centre ───────────────────────────────────────
        center = QVBoxLayout()
        center.setSpacing(14)

        # Progression
        self.progress = ProgressManche(total=11)
        center.addWidget(self.progress)

        sep = SeparatorLine()
        center.addWidget(sep)

        # Bannière équipe qui répond
        self.team_banner = QLabel("Équipe Rouge répond !")
        self.team_banner.setFixedHeight(44)
        self.team_banner.setStyleSheet(f"""
            background-color: {COLOR_ROUGE};
            color: white;
            font-size: 16px;
            font-weight: 900;
            border-radius: 10px;
            letter-spacing: 1px;
        """)
        self.team_banner.setAlignment(Qt.AlignCenter)
        center.addWidget(self.team_banner)

        # Timer bar + label
        timer_row = QHBoxLayout()
        self.timer_bar = TimerBar(TIMER_SECONDS)
        self.timer_bar.timeout.connect(self.timer_expired)
        self.timer_lbl = QLabel(f"{TIMER_SECONDS}s")
        self.timer_lbl.setFixedWidth(36)
        self.timer_lbl.setStyleSheet(
            f"color:{COLOR_GREEN}; font-size:13px; font-weight:bold; background:transparent;"
        )
        self.timer_lbl.setAlignment(Qt.AlignCenter)

        # Mettre à jour le label chaque tick
        self.timer_bar._timer.timeout.connect(self._update_timer_label)

        timer_row.addWidget(self.timer_bar)
        timer_row.addWidget(self.timer_lbl)
        center.addLayout(timer_row)

        # Question
        q_frame = QFrame()
        q_frame.setStyleSheet("""
            QFrame {
                background-color: #111111;
                border: 2px solid #252525;
                border-radius: 16px;
            }
        """)
        q_lay = QVBoxLayout(q_frame)
        q_lay.setContentsMargins(28, 20, 28, 20)
        self.question_lbl = QLabel("Question ici...")
        self.question_lbl.setStyleSheet(
            "color:white; font-size:19px; font-weight:bold; "
            "background:transparent; line-height:1.5;"
        )
        self.question_lbl.setAlignment(Qt.AlignCenter)
        self.question_lbl.setWordWrap(True)
        q_lay.addWidget(self.question_lbl)
        center.addWidget(q_frame)

        # 4 boutons options (grille 2×2)
        self.option_btns = []
        grid_top = QHBoxLayout(); grid_top.setSpacing(12)
        grid_bot = QHBoxLayout(); grid_bot.setSpacing(12)
        labels = ["A", "B", "C", "D"]

        for i in range(4):
            btn = QPushButton(f"  {labels[i]})  Option {i+1}")
            btn.setFixedHeight(58)
            btn.setStyleSheet(STYLE_OPTION_BTN)
            btn.clicked.connect(lambda _, idx=i: self._on_option(idx))
            self.option_btns.append(btn)
            if i < 2:
                grid_top.addWidget(btn)
            else:
                grid_bot.addWidget(btn)

        center.addLayout(grid_top)
        center.addLayout(grid_bot)

        # Message statut
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(
            f"color:{COLOR_GRAY}; font-size:13px; background:transparent;"
        )
        self.status_lbl.setAlignment(Qt.AlignCenter)
        center.addWidget(self.status_lbl)
        center.addStretch()

        root.addLayout(center)

        # ── Panel équipe bleue ────────────────────────────
        self.team_bleu_panel = TeamPanel("Équipe Bleue", "bleu")
        self.team_bleu_panel.setFixedWidth(200)
        root.addWidget(self.team_bleu_panel)

    # ── API Publique ──────────────────────────────────────
    def load(self, question: dict, answering_color: str,
             manche: int, game_state, is_second_chance: bool = False):
        """Charge la question et active l'écran pour une équipe"""
        self._answering_team = answering_color
        self._options        = question.get("options", ["A", "B", "C", "D"])
        self._enabled        = True

        # Bannière équipe
        team = game_state.get_team(answering_color)
        color_hex = COLOR_ROUGE if answering_color == "rouge" else COLOR_BLEU
        prefix = "⚡ 2ème chance — " if is_second_chance else ""
        self.team_banner.setText(f"{prefix}{team.name} répond !")
        self.team_banner.setStyleSheet(f"""
            background-color: {color_hex};
            color: white;
            font-size: 16px;
            font-weight: 900;
            border-radius: 10px;
            letter-spacing: 1px;
        """)

        # Question
        self.question_lbl.setText(question.get("question", "..."))

        # Options
        labels = ["A", "B", "C", "D"]
        for i, btn in enumerate(self.option_btns):
            if i < len(self._options):
                btn.setText(f"  {labels[i]})  {self._options[i]}")
                btn.setEnabled(True)
                btn.setStyleSheet(STYLE_OPTION_BTN)
            else:
                btn.setVisible(False)

        # Progression
        self.progress.update_progress(manche)
        self.status_lbl.setText("")

        # Update panels
        self.team_rouge_panel.update_state(game_state.team_rouge)
        self.team_bleu_panel.update_state(game_state.team_bleu)

        # Timer
        self.timer_bar.start()
        self._update_timer_label()

    def disable_options(self):
        """Désactive les options après réponse"""
        self._enabled = False
        self.timer_bar.stop()
        for btn in self.option_btns:
            btn.setEnabled(False)

    def highlight_correct(self, correct_option: str):
        """Met en vert la bonne réponse"""
        labels = ["A", "B", "C", "D"]
        for i, btn in enumerate(self.option_btns):
            if i < len(self._options) and self._options[i] == correct_option:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba(0,200,80,0.3);
                        color: {COLOR_GREEN};
                        border: 2px solid {COLOR_GREEN};
                        border-radius: 12px;
                        font-size: 15px;
                        font-weight: bold;
                        padding: 16px 20px;
                    }}
                """)

    def highlight_wrong(self, wrong_option: str, correct_option: str):
        """Met en rouge la mauvaise réponse et vert la bonne"""
        for i, btn in enumerate(self.option_btns):
            if i < len(self._options):
                opt = self._options[i]
                if opt == wrong_option:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: rgba(220,30,30,0.3);
                            color: {COLOR_ROUGE};
                            border: 2px solid {COLOR_ROUGE};
                            border-radius: 12px;
                            font-size: 15px;
                            font-weight: bold;
                            padding: 16px 20px;
                        }}
                    """)
                elif opt == correct_option:
                    self.highlight_correct(correct_option)

    def show_status(self, msg: str, color: str = COLOR_GRAY):
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet(
            f"color:{color}; font-size:14px; font-weight:bold; background:transparent;"
        )

    def update_teams(self, game_state):
        self.team_rouge_panel.update_state(game_state.team_rouge)
        self.team_bleu_panel.update_state(game_state.team_bleu)

    # ── Interne ──────────────────────────────────────────
    def _on_option(self, idx: int):
        if not self._enabled:
            return
        self._enabled = False
        self.timer_bar.stop()
        for btn in self.option_btns:
            btn.setEnabled(False)
        chosen = self._options[idx] if idx < len(self._options) else ""
        self.answer_selected.emit(chosen)

    def _update_timer_label(self):
        secs = self.timer_bar.remaining_seconds()
        self.timer_lbl.setText(f"{secs}s")
        color = COLOR_GREEN if secs > 8 else ("#ffc107" if secs > 4 else COLOR_ROUGE)
        self.timer_lbl.setStyleSheet(
            f"color:{color}; font-size:13px; font-weight:bold; background:transparent;"
        )

    def force_answer(self, option_idx: int):
        """Déclenche une réponse depuis l'extérieur (agent IA)"""
        self._on_option(option_idx)
