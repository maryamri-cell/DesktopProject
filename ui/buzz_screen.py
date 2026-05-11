# ============================================================
# ui/buzz_screen.py — Écran de buzz + question
# ============================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QFrame)
from PyQt5.QtCore    import Qt, pyqtSignal, QTimer
from PyQt5.QtGui     import QKeyEvent
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config      import COLOR_GREEN, COLOR_ROUGE, COLOR_BLEU, COLOR_GRAY, BUZZ_KEY_ROUGE, BUZZ_KEY_BLEU, TOTAL_MANCHES
from ui.styles   import (STYLE_BUZZ_ROUGE, STYLE_BUZZ_BLEU, STYLE_MASTERS_HEADER,
                     STYLE_MANCHE_BAR, STYLE_QUESTION_BOX)
from ui.widgets  import TeamPanel, CombinedTeamPanel, ProgressManche, SeparatorLine, SubtitleLabel, ExitButton, ImageButton
from PyQt5.QtGui     import QPixmap, QImage
import requests


class BuzzScreen(QWidget):
    """
    Écran principal du jeu :
    - Affiche la question + position à gagner
    - 2 boutons BUZZ (Q pour rouge, P pour bleu)
    - Panels latéraux avec état des équipes
    """

    # Signal émis quand une équipe buzze : "rouge" ou "bleu"
    buzzed = pyqtSignal(str)
    exit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buzz_enabled = False
        self._setup_ui()
        self.setFocusPolicy(Qt.StrongFocus)

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
        center_layout.setContentsMargins(25, 15, 25, 25)
        center_layout.setSpacing(10)
        main_layout.addWidget(center_widget, 1)

        # ── 1. Header Row (Logo + Manche + Quitter) ──────
        header_row = QHBoxLayout()
        header_row.addStretch(6) # Décalage encore plus prononcé à droite
        
        # Logo (Superposé directement)
        self.logo_lbl = QLabel()
        self.logo_lbl.setStyleSheet("background: transparent; border: none;")
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Gemini_Generated_Image_w4q5buw4q5buw4q5-removebg-preview.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            self.logo_lbl.setPixmap(pix.scaledToHeight(140, Qt.SmoothTransformation))
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

        center_layout.addStretch(2)

        # 🎯 Position Card (Plus large pour lisibilité)
        pos_card = QFrame()
        pos_card.setFixedHeight(70)
        pos_card.setFixedWidth(500)
        pos_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #D4AF37, stop:0.5 #F2E394, stop:1 #D4AF37);
                border: 2px solid #A67C00;
                border-radius: 20px;
            }
        """)
        pos_lay = QHBoxLayout(pos_card)
        self.position_lbl = QLabel("🎯 POSITION : ST")
        self.position_lbl.setAlignment(Qt.AlignCenter)
        self.position_lbl.setStyleSheet("""
            color: #3e2723; 
            font-weight: 900; 
            font-size: 20px; 
            background: transparent; 
            border: none;
            letter-spacing: 1.5px;
        """)
        pos_lay.addWidget(self.position_lbl)
        center_layout.addWidget(pos_card, 0, Qt.AlignCenter)

        # ── Question Glass Panel ─────────────────────────
        self.question_frame = QFrame()
        self.question_frame.setObjectName("questionFrame")
        self.question_frame.setStyleSheet("""
            #questionFrame {
                background: rgba(15, 25, 45, 0.85);
                border: 2.5px solid rgba(0, 212, 255, 0.5);
                border-radius: 25px;
            }
        """)
        q_layout = QVBoxLayout(self.question_frame)
        q_layout.setContentsMargins(40, 30, 40, 30)
        q_layout.setSpacing(20)

        self.image_lbl = QLabel()
        self.image_lbl.setFixedHeight(240)
        self.image_lbl.setAlignment(Qt.AlignCenter)
        self.image_lbl.setStyleSheet("border: 2px solid rgba(0, 212, 255, 0.3); border-radius: 15px; background: #000;")
        self.image_lbl.setVisible(False)
        q_layout.addWidget(self.image_lbl)

        self.question_lbl = QLabel("Chargement de la question...")
        self.question_lbl.setWordWrap(True)
        self.question_lbl.setAlignment(Qt.AlignCenter)
        self.question_lbl.setStyleSheet("color: white; font-size: 24px; font-weight: 800; background: transparent; border: none;")
        q_layout.addWidget(self.question_lbl)
        
        center_layout.addWidget(self.question_frame)
        center_layout.addStretch(2) # Stretch équilibré en bas

        # ── Buzz Prompt SUPPRIMÉ ────────────────────────

        # 5. Boutons BUZZ (AGRANDIS)
        buzz_layout = QHBoxLayout()
        buzz_layout.setSpacing(80)

        buzzer_img_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Gemini_Generated_Image_e8hupne8hupne8hu-removebg-preview.png")
        
        self.buzz_rouge_btn = ImageButton(buzzer_img_path)
        self.buzz_rouge_btn.setFixedSize(350, 350)
        self.buzz_rouge_btn.clicked.connect(lambda: self._on_buzz("rouge"))

        self.buzz_bleu_btn = ImageButton(buzzer_img_path)
        self.buzz_bleu_btn.setFixedSize(350, 350)
        self.buzz_bleu_btn.clicked.connect(lambda: self._on_buzz("bleu"))

        buzz_layout.addStretch()
        buzz_layout.addWidget(self.buzz_rouge_btn)
        buzz_layout.addWidget(self.buzz_bleu_btn)
        buzz_layout.addStretch()
        center_layout.addLayout(buzz_layout)

        # 6. Status (utilisé par load_question)
        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("color: white; font-weight: 700; font-size: 14px; background: transparent;")
        center_layout.addWidget(self.status_lbl)

    def resizeEvent(self, event):
        self.bg_lbl.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)



    # ── API Publique ──────────────────────────────────────
    def load_question(self, question: dict, manche: int,
                      position_label: str, game_state, my_color: str | None = None):
        """Charge une nouvelle question dans l'écran
        my_color: "rouge", "bleu" (ONLINE mode), ou None (LOCAL mode show both)
        """
        q_text = question.get("question", "...")
        # Remplacer les \n littéraux par de vrais sauts de ligne (pour WHO_AM_I)
        q_text = q_text.replace('\\n', '\n')
        self.question_lbl.setText(q_text)
        self.position_lbl.setText(f"🎯 Position à gagner : {position_label}")
        self.manche_lbl.setText(f"Manche {manche + 1} / {TOTAL_MANCHES}")
        self.status_lbl.setText("")
        self._buzz_enabled = True
        self._enable_buzz_buttons(True)
        self._update_teams(game_state)
        
        # Gestion de l'image (Pollinations)
        img_url = question.get("image_url")
        if img_url:
            self.image_lbl.setVisible(True)
            self.image_lbl.setText("Chargement image...")
            # Chargement simple (bloquant mais acceptable pour ce type de round spécialisé)
            try:
                # Utiliser un QTimer pour ne pas bloquer l'event loop immédiatement
                QTimer.singleShot(10, lambda: self._fetch_image(img_url))
            except Exception as e:
                print(f"Erreur init fetch: {e}")
        else:
            self.image_lbl.setVisible(False)

        # En ONLINE: afficher seulement LE BOUTON du joueur courant
        self.set_button_visibility(my_color)
        
        self.setFocus()

    def _fetch_image(self, url: str):
        """Télécharge et affiche l'image"""
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                image = QImage.fromData(resp.content)
                pixmap = QPixmap.fromImage(image)
                self.image_lbl.setPixmap(pixmap.scaled(self.image_lbl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.image_lbl.setText("Erreur image")
        except Exception as e:
            print(f"Erreur Pollinations: {e}")
            self.image_lbl.setText("Image non disponible")

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
    
    def set_button_visibility(self, my_color: str | None):
        """En ONLINE: affiche seulement LE BOUTON du joueur courant
        my_color: "rouge", "bleu", ou None (LOCAL show both)
        """
        if my_color == "rouge":
            # Je suis ROUGE → Afficher mon bouton, cacher BLEU
            self.buzz_rouge_btn.setVisible(True)
            self.buzz_bleu_btn.setVisible(False)
        elif my_color == "bleu":
            # Je suis BLEU → Cacher ROUGE, afficher mon bouton
            self.buzz_rouge_btn.setVisible(False)
            self.buzz_bleu_btn.setVisible(True)
        else:
            # LOCAL mode: afficher les deux
            self.buzz_rouge_btn.setVisible(True)
            self.buzz_bleu_btn.setVisible(True)

    def _update_teams(self, game_state):
        if game_state:
            self.team_panel.update_state(game_state)

    def force_buzz(self, color: str):
        """Déclenche un buzz depuis l'extérieur (agent IA)"""
        self._on_buzz(color)
