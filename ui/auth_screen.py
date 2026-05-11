# ============================================================
# ui/auth_screen.py — Design FIFA Masters (images de référence)
# ============================================================

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QGridLayout,
    QMessageBox, QFrame, QGraphicsDropShadowEffect,
    QSizePolicy,
)
from PyQt5.QtCore  import Qt, pyqtSignal
from PyQt5.QtGui   import QPixmap, QColor, QFont, QPainter, QBrush, QLinearGradient, QPen

from config import COLOR_GREEN, COLOR_ROUGE, COLOR_BLEU


# ══════════════════════════════════════════════════════
#  Petit badge joueur (emoji + note) — bande du haut
# ══════════════════════════════════════════════════════
class _PlayerBadge(QWidget):
    def __init__(self, rating: str, emoji: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(62, 72)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)

        face = QLabel(emoji)
        face.setAlignment(Qt.AlignCenter)
        face.setStyleSheet("font-size: 28px; background: transparent;")
        lay.addWidget(face)

        note = QLabel(rating)
        note.setAlignment(Qt.AlignCenter)
        note.setFixedHeight(20)
        note.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #d4af37, stop:1 #8b6914);
            color: #1a1a1a;
            font-size: 11px;
            font-weight: 900;
            border-radius: 4px;
        """)
        lay.addWidget(note)
        self.setStyleSheet("background: transparent;")


# ══════════════════════════════════════════════════════
#  Coin FIFA doré (badge numéro)
# ══════════════════════════════════════════════════════
class _CornerBadge(QLabel):
    def __init__(self, number: str, parent=None):
        super().__init__(number, parent)
        self.setFixedSize(46, 46)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #f5d060, stop:1 #c5900a);
                color: #1a1100;
                font-size: 15px;
                font-weight: 900;
                border-radius: 8px;
                border: 2px solid #e8b800;
            }
        """)


# ══════════════════════════════════════════════════════
#  Champ de saisie FIFA (avec décoration ⭐⚽ à droite)
# ══════════════════════════════════════════════════════
class _FifaInput(QWidget):
    def __init__(self, placeholder: str, password: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.field = QLineEdit(self)
        self.field.setPlaceholderText(placeholder)
        self.field.setFixedHeight(52)
        if password:
            self.field.setEchoMode(QLineEdit.Password)
        self.field.setStyleSheet("""
            QLineEdit {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #1c2840, stop:1 #111a2c);
                color: rgba(255,255,255,0.90);
                border: 1.5px solid #1e3050;
                border-radius: 10px;
                padding: 0 95px 0 18px;
                font-size: 14px;
                selection-background-color: #0066cc;
            }
            QLineEdit:focus {
                border-color: #00c8ff;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #1e2e4a, stop:1 #141e32);
            }
            QLineEdit::placeholder {
                color: rgba(255,255,255,0.40);
            }
        """)

        # Décoration étoiles football (superposée à droite)
        self.deco = QLabel("⭐ ★ ⚽", self)
        self.deco.setAlignment(Qt.AlignCenter)
        self.deco.setStyleSheet("""
            color: #ffd700;
            font-size: 15px;
            background: transparent;
        """)

    def resizeEvent(self, e):
        self.field.setGeometry(0, 0, self.width(), self.height())
        self.deco.setGeometry(self.width() - 88, 4, 82, self.height() - 8)

    def text(self) -> str:
        return self.field.text()


# ══════════════════════════════════════════════════════
#  Écran d'authentification principal
# ══════════════════════════════════════════════════════
class AuthScreen(QWidget):
    auth_success     = pyqtSignal(dict)
    continue_offline = pyqtSignal()

    AVATARS = ["⚽", "🔥", "🦅", "🛡️", "👑", "🎯", "🚀", "🐆"]

    _DECO = [
        ("67", "😊"), ("?",  "❓"), ("72", "😄"), ("?", "❓"),
        ("85", "😎"), ("?",  "❓"), ("79", "🙂"), ("?", "❓"),
        ("85", "🏃"), ("81", "👤"),
    ]

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service    = auth_service
        self.selected_avatar = self.AVATARS[0]
        self.avatar_buttons  = {}
        self._login_active   = True
        self._setup_ui()

    # ──────────────────────────────────────────────────
    def _setup_ui(self):
        # Fond : image stade
        self.bg_lbl = QLabel(self)
        self.bg_lbl.setScaledContents(True)
        bg_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets", "images", "stadium_bg.png"
        )
        if os.path.exists(bg_path):
            self.bg_lbl.setPixmap(QPixmap(bg_path))

        # Layout principal (au-dessus du fond)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 1. HEADER carbon (image 3) ────────────────────────────
        root.addWidget(self._build_header())

        # ── 2. CARTE CENTRALE ─────────────────────────────────────
        card_row = QHBoxLayout()
        card_row.setContentsMargins(0, 20, 0, 20)
        card_row.addStretch(1)
        card_row.addWidget(self._build_card())
        card_row.addStretch(1)

        card_wrapper = QWidget()
        card_wrapper.setStyleSheet("background: transparent;")
        card_wrapper.setLayout(card_row)
        root.addWidget(card_wrapper, 1)

    # ──────────────────────────────────────────────────
    def _build_header(self) -> QWidget:
        container = QWidget()
        container.setFixedHeight(220)
        container.setStyleSheet("background: transparent;")

        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Barre 1 — LOGO (remplace le texte)
        bar1 = QLabel()
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "Gemini_Generated_Image_w4q5buw4q5buw4q5-removebg-preview.png"
        )
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            bar1.setPixmap(pix.scaledToHeight(180, Qt.SmoothTransformation))
        
        bar1.setAlignment(Qt.AlignCenter)
        bar1.setFixedHeight(200)
        bar1.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(bar1)

        return container

    # ──────────────────────────────────────────────────
    def _build_card(self) -> QFrame:
        """Carte centrale métal (image 2)"""
        card = QFrame()
        card.setFixedWidth(640)
        card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #3a4a5c, stop:0.25 #2c3a4c,
                    stop:0.6 #1e2a3a, stop:1 #141e2c);
                border: 2px solid #00d4ff;
                border-radius: 16px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setColor(QColor(0, 212, 255, 160))
        shadow.setOffset(0, 0)
        card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(32, 24, 32, 28)
        lay.setSpacing(14)

        # ── Onglets Log in / Sign up ──────────────────
        tab_frame = QFrame()
        tab_frame.setFixedHeight(48)
        tab_frame.setStyleSheet("""
            QFrame {
                background: #1a2030;
                border-radius: 10px;
                border: 1px solid #2a3a50;
            }
        """)
        tab_lay = QHBoxLayout(tab_frame)
        tab_lay.setContentsMargins(5, 5, 5, 5)
        tab_lay.setSpacing(6)

        self.btn_login  = QPushButton("Log in")
        self.btn_signup = QPushButton("Sign up")

        for btn in (self.btn_login, self.btn_signup):
            btn.setFixedHeight(36)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont("Arial", 12, QFont.Bold))

        self.btn_login.clicked.connect(lambda: self._switch_tab(True))
        self.btn_signup.clicked.connect(lambda: self._switch_tab(False))

        tab_lay.addWidget(self.btn_login)
        tab_lay.addWidget(self.btn_signup)

        lay.addWidget(tab_frame)

        # ── Zone de contenu (champs + bouton) ─────────
        self.content_area = QVBoxLayout()
        self.content_area.setSpacing(10)
        lay.addLayout(self.content_area)

        # ── Status label (persistant) ─────────────────
        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("""
            QLabel {
                color: #ff6b6b;
                font-size: 12px;
                background: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }
        """)
        self.status_lbl.setVisible(False)
        lay.addWidget(self.status_lbl)

        # Afficher le formulaire login par défaut
        self._switch_tab(True)
        return card

    # ──────────────────────────────────────────────────
    def _switch_tab(self, login: bool):
        self._login_active = login

        ACTIVE = """
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00c040, stop:1 #00e868);
                color: #0a1a0a;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 900;
            }
        """
        INACTIVE = """
            QPushButton {
                background: #2a3040;
                color: rgba(255,255,255,0.60);
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover { background: #333d50; color: white; }
        """
        self.btn_login.setStyleSheet( ACTIVE   if login else INACTIVE)
        self.btn_signup.setStyleSheet(INACTIVE if login else ACTIVE)

        # Vider le content_area
        while self.content_area.count():
            item = self.content_area.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        self.avatar_buttons.clear()

        if login:
            self._build_login_form()
        else:
            self._build_signup_form()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ──────────────────────────────────────────────────
    def _build_login_form(self):
        self.login_email = _FifaInput("Email")
        self.login_pass  = _FifaInput("Mot de passe", password=True)

        self.content_area.addWidget(self.login_email)
        self.content_area.addWidget(self.login_pass)

        btn = QPushButton("Se connecter")
        btn.setFixedHeight(52)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #0d47a1, stop:0.5 #1976d2, stop:1 #0d47a1);
                color: white;
                border: 1px solid #42a5f5;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 900;
                letter-spacing: 4px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #1565c0, stop:0.5 #2196f3, stop:1 #1565c0);
                border-color: #64b5f6;
            }
            QPushButton:pressed { background: #0d47a1; }
        """)
        btn.clicked.connect(self._handle_login)
        self.content_area.addWidget(btn)

    # ──────────────────────────────────────────────────
    def _build_signup_form(self):
        self.signup_email    = _FifaInput("Email")
        self.signup_pass     = _FifaInput("Mot de passe", password=True)
        self.signup_nickname = _FifaInput("Nickname de jeu")

        self.content_area.addWidget(self.signup_email)
        self.content_area.addWidget(self.signup_pass)
        self.content_area.addWidget(self.signup_nickname)

        btn = QPushButton("Créer mon compte")
        btn.setFixedHeight(52)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00a030, stop:0.5 #00c850, stop:1 #00a030);
                color: #031208;
                border: 1px solid #00e060;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 900;
                letter-spacing: 3px;
            }
            QPushButton:hover { background: #00d860; }
            QPushButton:pressed { background: #008828; }
        """)
        btn.clicked.connect(self._handle_signup)
        self.content_area.addWidget(btn)

    # ──────────────────────────────────────────────────
    def _av_style(self, selected: bool) -> str:
        if selected:
            return ("QPushButton { background: rgba(0,200,80,0.2); border: 2px solid #00c850; "
                    "border-radius: 8px; font-size: 20px; }")
        return ("QPushButton { background: #1c2535; border: 2px solid #2a3a50; "
                "border-radius: 8px; font-size: 20px; color: white; }"
                "QPushButton:hover { border-color: #4a6a90; }")

    def _select_avatar(self, avatar: str):
        self.selected_avatar = avatar
        for v, btn in self.avatar_buttons.items():
            btn.setStyleSheet(self._av_style(v == avatar))

    def _set_status(self, msg: str, ok: bool = False):
        color = "#00e676" if ok else "#ff6b6b"
        self.status_lbl.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 12px;
                background: transparent;
                border: none;
                padding: 0; margin: 0;
            }}
        """)
        self.status_lbl.setText(msg)
        self.status_lbl.setVisible(bool(msg))

    def _validate(self, email: str, password: str):
        if not email or "@" not in email:
            return "Email invalide."
        if len(password) < 6:
            return "Mot de passe trop court (min 6 caractères)."
        return None

    # ── Fond suit le resize ────────────────────────────
    def resizeEvent(self, event):
        self.bg_lbl.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    # ── Handlers backend (inchangés) ──────────────────
    def _handle_login(self):
        email    = self.login_email.text().strip()
        password = self.login_pass.text().strip()
        err = self._validate(email, password)
        if err:
            self._set_status(err); return
        try:
            profile = self.auth_service.login(email, password)
        except Exception as exc:
            self._set_status(str(exc)); return
        self._set_status("Connexion réussie ✔", ok=True)
        self.auth_success.emit(profile)

    def _handle_signup(self):
        email    = self.signup_email.text().strip()
        password = self.signup_pass.text().strip()
        nickname = self.signup_nickname.text().strip()
        err = self._validate(email, password)
        if err:
            self._set_status(err); return
        if not nickname:
            self._set_status("Le nickname est obligatoire."); return
        try:
            profile = self.auth_service.sign_up(email, password, nickname, self.selected_avatar)
        except Exception as exc:
            self._set_status(str(exc)); return
        QMessageBox.information(self, "Inscription réussie ✔",
                                "Compte créé avec succès. Vous êtes maintenant connecté.")
        self._set_status("Inscription réussie ✔", ok=True)
        self.auth_success.emit(profile)
