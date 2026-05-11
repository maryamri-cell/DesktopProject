# ============================================================
# ui/answer_screen.py — Écran de réponse avec timer visuel
# ============================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QFrame, QProgressBar)
from PyQt5.QtCore    import Qt, pyqtSignal, QTimer
from PyQt5.QtGui     import QFont, QPainter, QColor, QLinearGradient, QPixmap
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config  import (COLOR_GREEN, COLOR_ROUGE, COLOR_BLEU, COLOR_GRAY,
                     COLOR_WHITE, COLOR_CARD_BG, TOTAL_MANCHES)
from ui.styles  import (STYLE_OPTION_BTN, STYLE_MASTERS_HEADER, STYLE_MANCHE_BAR,
                     STYLE_BANNER_ROUGE, STYLE_BANNER_BLEU, STYLE_QUESTION_BOX,
                     STYLE_OPTION_MASTERS)
from ui.widgets import TeamPanel, CombinedTeamPanel, ProgressManche, SeparatorLine, ExitButton
import requests
from PyQt5.QtGui import QPixmap

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
    exit_requested  = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._answering_team = None
        self._options        = []
        self._enabled        = False
        self._ai_mode        = False
        self._setup_ui()

    def _setup_ui(self):
        # ── Fond (Image Stade) ───────────────────────────
        self.bg_lbl = QLabel(self)
        self.bg_lbl.setScaledContents(True)
        bg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "images", "stadium_bg.png")
        if os.path.exists(bg_path):
            self.bg_lbl.setPixmap(QPixmap(bg_path))
            
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar Equipes ──────────────────────────────
        self.team_panel = CombinedTeamPanel()
        self.team_panel.setFixedWidth(580)
        main_layout.addWidget(self.team_panel)

        # ── Zone centrale (FOND PERSO) ───────────────────
        center_widget = QWidget()
        center_widget.setObjectName("centerWidget")
        bg_center_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Gemini_Generated_Image_81bu7x81bu7x81bu.png")
        if os.path.exists(bg_center_path):
             bg_url = bg_center_path.replace("\\", "/")
             center_widget.setStyleSheet(f"""
                #centerWidget {{
                    border-image: url('{bg_url}');
                }}
            """)
        
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(25, 10, 25, 10) # Réduit le bas
        center_layout.setSpacing(5) # Plus compact
        main_layout.addWidget(center_widget, 1)

        # ── 1. Header Row (Logo + Manche + Quitter) ──────
        header_row = QHBoxLayout()
        header_row.addStretch(6) # Décalage plus fort à droite
        
        # Logo (Superposé directement)
        self.logo_lbl = QLabel()
        self.logo_lbl.setStyleSheet("background: transparent; border: none;")
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Gemini_Generated_Image_w4q5buw4q5buw4q5-removebg-preview.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            self.logo_lbl.setPixmap(pix.scaledToHeight(120, Qt.SmoothTransformation))
        header_row.addWidget(self.logo_lbl)
        
        header_row.addStretch(1)
        
        # Manche Info (Déplacé à côté du bouton Quitter)
        self.manche_card = QFrame()
        self.manche_card.setFixedHeight(35)
        self.manche_card.setFixedWidth(260)
        self.manche_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #D4AF37, stop:0.5 #F2E394, stop:1 #D4AF37);
                border: 2px solid #A67C00;
                border-radius: 8px;
            }
        """)
        manche_lay = QHBoxLayout(self.manche_card)
        manche_lay.setContentsMargins(10, 0, 10, 0)
        self.manche_lbl = QLabel("MANCHE 1 / 18")
        self.manche_lbl.setAlignment(Qt.AlignCenter)
        self.manche_lbl.setStyleSheet("color: #3e2723; font-weight: 900; font-size: 13px; letter-spacing: 1px; background: transparent; border: none;")
        manche_lay.addWidget(self.manche_lbl)
        header_row.addWidget(self.manche_card)

        self.exit_btn = ExitButton()
        self.exit_btn.clicked.connect(self.exit_requested.emit)
        header_row.addWidget(self.exit_btn)
        
        center_layout.addLayout(header_row)

        center_layout.addSpacing(5)

        # ── Bannière Qui Répond (Superposée directement) ──
        banner_cont = QWidget()
        banner_cont.setStyleSheet("background: transparent; border: none;")
        banner_lay = QHBoxLayout(banner_cont)
        banner_lay.setContentsMargins(0, 0, 0, 0)
        self.team_banner = QLabel("JOUEUR 1 RÉPOND !")
        self.team_banner.setFixedHeight(45)
        self.team_banner.setFixedWidth(400)
        self.team_banner.setAlignment(Qt.AlignCenter)
        self.team_banner.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0,0,180,0.6), stop:1 rgba(0,0,180,0.2));
                color: white; font-weight: 900; font-size: 16px; border: 2px solid #00d4ff; border-radius: 22px; letter-spacing: 2px;
            }
        """)
        banner_lay.addWidget(self.team_banner)
        center_layout.addWidget(banner_cont)

        # ── Timer ────────────────────────────────────────
        timer_cont = QFrame()
        timer_cont.setFixedHeight(35)
        timer_cont.setStyleSheet("background: rgba(0,0,0,0.3); border-radius: 17px; border: 1px solid rgba(255,255,255,0.1);")
        timer_lay = QHBoxLayout(timer_cont)
        timer_lay.setContentsMargins(15, 0, 15, 0)

        self.timer_bar = TimerBar(TIMER_SECONDS)
        self.timer_bar.timeout.connect(self.timer_expired)
        self.timer_lbl = QLabel(f"{TIMER_SECONDS}s")
        self.timer_lbl.setFixedWidth(40)
        self.timer_lbl.setStyleSheet("color: #00ff88; font-weight: 900; font-size: 14px; background: transparent; border: none;")
        
        self.timer_bar._timer.timeout.connect(self._update_timer_label)
        timer_lay.addWidget(self.timer_bar, 1)
        timer_lay.addWidget(self.timer_lbl)
        center_layout.addWidget(timer_cont)
        center_layout.addSpacing(10)

        # ── Question Glass Panel ─────────────────────────
        self.question_container = QFrame()
        self.question_container.setObjectName("questionFrame")
        self.question_container.setStyleSheet("""
            #questionFrame {
                background: rgba(15, 25, 45, 0.7);
                border: 2.5px solid rgba(0, 212, 255, 0.4);
                border-radius: 25px;
            }
        """)
        q_lay = QVBoxLayout(self.question_container)
        q_lay.setContentsMargins(30, 20, 30, 20)

        self.image_lbl = QLabel()
        self.image_lbl.setFixedHeight(180)
        self.image_lbl.setAlignment(Qt.AlignCenter)
        self.image_lbl.setStyleSheet("border: 2px solid rgba(0, 212, 255, 0.2); border-radius: 15px; background: #000;")
        self.image_lbl.setVisible(False)
        q_lay.addWidget(self.image_lbl)

        self.question_lbl = QLabel("Question...")
        self.question_lbl.setAlignment(Qt.AlignCenter)
        self.question_lbl.setWordWrap(True)
        self.question_lbl.setStyleSheet("color: white; font-size: 20px; font-weight: 800; background: transparent; border: none;")
        q_lay.addWidget(self.question_lbl)
        
        center_layout.addStretch(2) # Centrage haut
        center_layout.addWidget(self.question_container)
        center_layout.addStretch(1) # Espace entre question et options

        # ── Options (Superposées directement) ───────────
        self.options_container = QWidget()
        self.options_container.setStyleSheet("background: transparent; border: none;")
        self.options_grid_lay = QVBoxLayout(self.options_container)
        self.options_grid_lay.setContentsMargins(10, 0, 10, 0)
        self.options_grid_lay.setSpacing(15)
        self.option_btns = []
        
        row1 = QHBoxLayout(); row1.setSpacing(15)
        row2 = QHBoxLayout(); row2.setSpacing(15)
        
        for i in range(4):
            btn = QPushButton()
            btn.setFixedHeight(58)
            from ui.styles import STYLE_OPTION_MASTERS
            btn.setStyleSheet(STYLE_OPTION_MASTERS)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, idx=i: self._on_option(idx))
            self.option_btns.append(btn)
            if i < 2: row1.addWidget(btn)
            else: row2.addWidget(btn)
            
        self.options_grid_lay.addLayout(row1)
        self.options_grid_lay.addLayout(row2)
        center_layout.addWidget(self.options_container)
        center_layout.addStretch(2) # Centrage bas

        # Status (Invisible si vide)
        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("color: white; font-weight: 700; font-size: 14px; background: transparent;")
        center_layout.addWidget(self.status_lbl)
        center_layout.addStretch(1) # Ajout d'un stretch final pour pousser tout vers le haut



    def resizeEvent(self, event):
        self.bg_lbl.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)



    # ── API Publique ──────────────────────────────────────
    def load(self, question: dict, answering_color: str,
             manche: int, game_state, is_second_chance: bool = False,
             ai_mode: bool = False):
        """Charge la question et active l'écran pour une équipe"""
        self._answering_team = answering_color
        self._options        = question.get("options", ["A", "B", "C", "D"])
        self._enabled        = True
        self._ai_mode        = ai_mode

        # Récupérer le type de question depuis l'état
        from game.state import QuestionType
        q_type = game_state.get_question_type()

        # Visibilité par défaut
        self.image_lbl.setVisible(False)
        self.options_container.setVisible(True)

        # Manche text
        self.manche_lbl.setText(f"Manche {manche + 1} / {TOTAL_MANCHES}")

        # Configuration selon le type
        if q_type == QuestionType.IMAGE_GUESS:
            self.image_lbl.setVisible(True)
            self.image_lbl.setText("Chargement image...")
            # Chargement asynchrone pour ne pas figer l'interface
            url = question.get("image_url")
            QTimer.singleShot(10, lambda: self._load_image(url))
            self.question_lbl.setText("Qui est ce joueur ? (Indice visuel)")
        elif q_type == QuestionType.REORDERING:
            # Pour l'instant on garde MCQ mais on pourrait adapter
            self.question_lbl.setText(question.get("question", ""))
        elif q_type == QuestionType.TRANSFER:
            self.question_lbl.setText(f"📜 PARCOURS : {question.get('question', '')}")
        elif q_type == QuestionType.WHO_AM_I:
            q_text = question.get('question', 'Qui suis-je ?')
            # Remplacer les \\n littéraux par de vrais sauts de ligne
            q_text = q_text.replace('\\n', '\n')
            self.question_lbl.setText(f"❓ {q_text}")
        else:
            self.question_lbl.setText(question.get("question", "..."))

        # Bannière équipe
        team = game_state.get_team(answering_color)
        prefix = "⚡ 2ème chance — " if is_second_chance else ""
        if ai_mode:
            self.team_banner.setText(f"{prefix}🤖 {team.name} réfléchit...")
        else:
            self.team_banner.setText(f"{prefix}{team.name} RÉPOND !")
        
        self.team_banner.setStyleSheet(STYLE_BANNER_ROUGE if answering_color == "rouge" else STYLE_BANNER_BLEU)

        # Options
        labels = ["A", "B", "C", "D"]
        for i, btn in enumerate(self.option_btns):
            btn.setVisible(True)
            if i < len(self._options):
                btn.setText(f"  {labels[i]})  {self._options[i]}")
                # En mode IA, les boutons sont visibles mais désactivés pour l'humain
                btn.setEnabled(not ai_mode)
                btn.setStyleSheet(STYLE_OPTION_MASTERS)
            else:
                btn.setVisible(False)

        self.status_lbl.setText("")

        # Update panels
        self.team_panel.update_state(game_state)

        # Timer
        self.timer_bar.start()
        self._update_timer_label()


    def _load_image(self, url: str):
        """Charge l'image depuis l'URL de manière non-bloquante via un worker minimal"""
        if not url: return
        
        # Pour éviter le freeze UI, on utilise un thread local rapide
        from PyQt5.QtCore import QThread, pyqtSignal
        
        class ImageWorker(QThread):
            finished = pyqtSignal(bytes)
            def run(self):
                try:
                    import requests
                    r = requests.get(url, timeout=5)
                    self.finished.emit(r.content)
                except:
                    self.finished.emit(b"")
        
        self._image_worker = ImageWorker(self)
        self._image_worker.finished.connect(self._on_image_loaded)
        self._image_worker.start()

    def _on_image_loaded(self, data: bytes):
        if not data:
            self.image_lbl.setText("Erreur de chargement")
            return
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            self.image_lbl.setPixmap(pixmap.scaled(self.image_lbl.width(), self.image_lbl.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.image_lbl.setText("Format invalide")

    def disable_options(self):
        """Désactive les options après réponse"""
        self._enabled = False
        self.timer_bar.stop()
        for btn in self.option_btns:
            btn.setEnabled(False)

    def enable_options(self):
        """Réactive les options pour 2ème chance"""
        self._enabled = True
        self.timer_bar.start()
        for btn in self.option_btns:
            btn.setEnabled(True)

    def highlight_correct(self, correct_option: str):
        """Met en vert la bonne réponse (masqué en mode IA)"""
        if self._ai_mode:
            return
        labels = ["A", "B", "C", "D"]
        for i, btn in enumerate(self.option_btns):
            if i < len(self._options) and self._options[i] == correct_option:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #005522, stop:1 #003311);
                        color: #00ff88;
                        border: 2px solid #00ff88;
                        border-radius: 20px;
                        font-size: 15px;
                        font-weight: bold;
                        padding: 15px 25px;
                        text-align: left;
                    }}
                """)

    def highlight_wrong(self, wrong_option: str, correct_option: str, show_correct: bool = True):
        """Met en rouge la mauvaise réponse et vert la bonne (masqué en mode IA)"""
        if self._ai_mode:
            return
        for i, btn in enumerate(self.option_btns):
            if i < len(self._options):
                opt = self._options[i]
                if opt == wrong_option:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #550000, stop:1 #330000);
                            color: #ff6666;
                            border: 2px solid #ff6666;
                            border-radius: 20px;
                            font-size: 15px;
                            font-weight: bold;
                            padding: 15px 25px;
                            text-align: left;
                        }}
                    """)
                elif opt == correct_option and show_correct:
                    self.highlight_correct(correct_option)

    def show_status(self, msg: str, color: str = COLOR_GRAY):
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet(
            f"color:{color}; font-size:14px; font-weight:bold; background:transparent;"
        )

    def update_teams(self, game_state):
        self.team_panel.update_state(game_state)

    # ── Interne ──────────────────────────────────────────
    def _on_option(self, idx: int):
        # Double-check: si les boutons sont désactivés, ignorer
        if not self._enabled or not self.option_btns[idx].isEnabled():
            print(f"[DEBUG] Click ignoré: _enabled={self._enabled}, btn.isEnabled()={self.option_btns[idx].isEnabled()}")
            return
        
        self._enabled = False
        self.timer_bar.stop()
        for btn in self.option_btns:
            btn.setEnabled(False)
        chosen = self._options[idx] if idx < len(self._options) else ""
        print(f"[DEBUG] Réponse envoyée: {chosen}")
        self.answer_selected.emit(chosen)



    def _update_timer_label(self):
        secs = self.timer_bar.remaining_seconds()
        self.timer_lbl.setText(f"{secs}s")
        color = "#00ff88" if secs > 8 else ("#ffc107" if secs > 4 else "#ff4444")
        self.timer_lbl.setStyleSheet(
            f"color:{color}; font-size:15px; font-weight:bold; background:transparent;"
        )

    def show_opponent_answer(self, opponent_answer: str, opponent_name: str, opponent_color: str):
        """
        Affiche la réponse de l'autre joueur
        Mode ONLINE uniquement
        """
        opponent_color_hex = COLOR_ROUGE if opponent_color == "rouge" else COLOR_BLEU
        self.status_lbl.setText(
            f"⚔️  {opponent_name} a répondu: {opponent_answer}"
        )
        self.status_lbl.setStyleSheet(f"""
            color: {opponent_color_hex};
            font-size: 14px;
            font-weight: bold;
            background-color: rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 8px 12px;
        """)

    def force_answer(self, option_idx: int):
        """Déclenche une réponse depuis l'extérieur (agent IA)"""
        self._on_option(option_idx)
