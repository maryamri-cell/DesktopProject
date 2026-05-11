# ============================================================
# ui/intro_screen.py — Écran d'accueil, zéro rectangle gris
# ============================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QLineEdit, QFrame)
from PyQt5.QtCore    import Qt, pyqtSignal, QUrl, QTimer, QRect, QRectF
from PyQt5.QtGui     import QPixmap, QPainter, QColor, QLinearGradient, QRadialGradient, QImage, QBrush, QPen, QPainterPath
import cv2
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config     import COLOR_GREEN, COLOR_GRAY, COLOR_ROUGE, COLOR_BLEU
from game.state import GameMode

BG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "background.png"
)

VIDEO_PATH = r"c:\Users\admin\Downloads\ahsan_khotaVersionHouda\ahsan_khota\kling_20260507_VIDEO_Cinematic_1700_0 (online-video-cutter.com).mp4"


class PremiumButton(QPushButton):
    """Bouton personnalisé avec style eSports (stries diagonales, bordure néon)"""
    def __init__(self, text, icon_path=None, icon_emoji=None, color="#00d4ff", parent=None):
        super().__init__(text, parent)
        self.color = color
        self.icon_path = icon_path
        self.icon_emoji = icon_emoji
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(75)
        self.setMinimumWidth(260)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect().adjusted(2, 2, -2, -2)
        
        # 1. Fond avec dégradé sombre
        grad = QLinearGradient(0, 0, rect.width(), rect.height())
        grad.setColorAt(0, QColor(20, 30, 45))
        grad.setColorAt(1, QColor(10, 15, 25))
        painter.setBrush(QBrush(grad))
        
        # 2. Bordure néon
        pen = QPen(QColor(self.color), 2)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 10, 10)
        
        # 3. Stries diagonales (Pattern)
        painter.setPen(QPen(QColor(255, 255, 255, 15), 1))
        gap = 8
        for i in range(-rect.height(), rect.width(), gap):
            painter.drawLine(i, 0, i + rect.height(), rect.height())
            
        # 4. Icone
        icon_rect = QRect(15, 12, 50, 50)
        if self.icon_path and os.path.exists(self.icon_path):
            pix = QPixmap(self.icon_path).scaled(45, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(icon_rect.center().x() - 22, icon_rect.center().y() - 22, pix)
        elif self.icon_emoji:
            painter.setPen(QPen(Qt.white))
            font = painter.font()
            font.setPointSize(24)
            painter.setFont(font)
            painter.drawText(icon_rect, Qt.AlignCenter, self.icon_emoji)
            
        # 5. Texte
        painter.setPen(QPen(QColor("#00e676"), 1))
        font = painter.font()
        font.setPointSize(14)
        font.setWeight(900)
        painter.setFont(font)
        text_rect = rect.adjusted(70, 0, -10, 0)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self.text())
        
        painter.end()

class ImageButton(QPushButton):
    """Bouton utilisant une image avec effet de lumière néon et bordure lors de la sélection"""
    def __init__(self, image_path, color=QColor("#00d4ff"), parent=None):
        super().__init__(parent)
        self.image_path = image_path.replace("\\", "/")
        self.selected = False
        self.color = color
        self.setCursor(Qt.PointingHandCursor)
        self._pixmap = QPixmap(self.image_path) if os.path.exists(self.image_path) else None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        rect = self.rect()
        
        # 1. Dessiner l'effet de sélection (Halo lumineux uniquement)
        if self.selected:
            # Halo néon
            glow = QRadialGradient(rect.center(), max(rect.width(), rect.height()) * 0.7)
            glow_color = QColor(self.color)
            glow_color.setAlpha(120)
            glow.setColorAt(0, glow_color)
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(rect.adjusted(-30, -30, 30, 30))
        else:
            # Opacité réduite pour les boutons non sélectionnés
            painter.setOpacity(0.4)
        
        # 2. Dessiner l'image
        if self._pixmap and not self._pixmap.isNull():
            # Centrer l'image dans le bouton en gardant l'aspect ratio
            scaled_pix = self._pixmap.scaled(rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (rect.width() - scaled_pix.width()) // 2
            y = (rect.height() - scaled_pix.height()) // 2
            painter.drawPixmap(x, y, scaled_pix)
            
        painter.end()
        
class RulesOverlay(QWidget):
    """Fiche des règles avec effet glassmorphism"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(parent.size() if parent else QRect(0,0,1280,720).size())
        self._setup_ui()
        
    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignCenter)
        
        # Panneau central
        panel = QFrame()
        panel.setFixedSize(900, 580)
        panel.setStyleSheet("""
            QFrame {
                background: rgba(10, 15, 25, 0.98);
                border: 3px solid #ffd700;
                border-radius: 20px;
            }
            QLabel { border: none; background: transparent; }
        """)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(40, 30, 40, 30)
        lay.setSpacing(15)
        
        title = QLabel("📜  RÈGLES ET DÉROULEMENT DU JEU")
        title.setStyleSheet("color: #ffd700; font-size: 28px; font-weight: 900; letter-spacing: 2px; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)
        
        rules_text = """
        <div style='color: white; line-height: 1.6; font-size: 16px;'>
            <p><b style='color: #ffd700;'>1. LA TACHKILA :</b> Le but est de construire le meilleur 11 titulaire possible en remportant des manches.</p>
            <p><b style='color: #ffd700;'>2. LE BUZZER :</b> Une question footballistique s'affiche. Le plus rapide à buzzer obtient le droit de répondre en premier.</p>
            <p><b style='color: #ffd700;'>3. 2ÈME CHANCE & CARTONS :</b> Si vous donnez une mauvaise réponse ou laissez le temps s'écouler, la main passe à l'adversaire (2ème chance). Une mauvaise réponse équivaut à une faute. Une faute sans succès donne 1 Carton Jaune.</p>
            <p><b style='color: #ffd700;'>4. DRAFT DE JOUEURS :</b> Le gagnant de la question choisit un joueur parmi une liste générée (Or, Argent, Bronze, etc.) pour renforcer son équipe. Les statistiques FIFA du joueur s'ajoutent au score total.</p>
            <p><b style='color: #ffd700;'>5. ÉCHANGE TACTIQUE (ROUGE) :</b> L'accumulation de 2 Cartons Jaunes entraîne 1 Carton Rouge (-2 pts). À la fin du match, pour chaque rouge, l'adversaire lance une phase d'échange "Take & Give" : il vous vole un de vos meilleurs joueurs et vous refile un remplaçant !</p>
            <p><b style='color: #ffd700;'>6. VICTOIRE :</b> À la fin de toutes les manches et après les échanges, l'équipe avec le score FIFA global le plus élevé est couronnée championne !</p>
        </div>
        """
        content = QLabel(rules_text)
        content.setWordWrap(True)
        content.setStyleSheet("background: transparent;")
        lay.addWidget(content)
        
        close_btn = QPushButton("COMPRIS !")
        close_btn.setFixedSize(200, 45)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #00d4ff; color: black; border-radius: 10px; font-weight: 900;
            }
            QPushButton:hover { background: white; }
        """)
        close_btn.clicked.connect(self.hide)
        lay.addWidget(close_btn, 0, Qt.AlignCenter)
        
        main.addWidget(panel)
        
    def paintEvent(self, event):
        # Fond sombre pour isoler le popup
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 180))

class IntroScreen(QWidget):
    game_start = pyqtSignal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_mode = GameMode.VS_AI
        self._bg_pixmap     = QPixmap(BG_PATH) if os.path.exists(BG_PATH) else None
        self._video_pixmap  = None

        # ── Video Background (OpenCV) ─────────────────────
        if os.path.exists(VIDEO_PATH):
            print(f"[VIDEO] Loading with OpenCV: {VIDEO_PATH}")
            self.cap = cv2.VideoCapture(VIDEO_PATH)
            if self.cap.isOpened():
                fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
                self.video_timer = QTimer(self)
                self.video_timer.timeout.connect(self._next_video_frame)
                self.video_timer.start(int(1000 / fps))
            else:
                print("[VIDEO] OpenCV failed to open file.")
                self.cap = None
        else:
            print(f"[VIDEO] File not found: {VIDEO_PATH}")
            self.cap = None
        
        self._setup_ui()
        
        # Overlay des règles (caché par défaut)
        self.rules_overlay = RulesOverlay(self)
        self.rules_overlay.hide()

    def showEvent(self, event):
        super().showEvent(event)
        # Si c'est la première fois qu'on affiche l'écran, on lance le délai
        if not hasattr(self, "_ui_timer_started"):
            self._ui_timer_started = True
            QTimer.singleShot(3000, self._show_ui_content)

    def _show_ui_content(self):
        if hasattr(self, "ui_content"):
            self.ui_content.setVisible(True)
            self.ui_content.update() # Force refresh
            print("[UI] Content visible after 3s delay.")

    def _next_video_frame(self):
        if not self.cap: return
        ret, frame = self.cap.read()
        if ret:
            # Conversion BGR -> RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            # Utiliser .copy() pour éviter que les données ne soient supprimées avec 'frame'
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
            self._video_pixmap = QPixmap.fromImage(qimg)
            self.update() # Déclenche paintEvent
        else:
            # Fin de vidéo -> on arrête le timer mais on garde le dernier _video_pixmap
            self.video_timer.stop()
            if self.cap:
                self.cap.release()
                self.cap = None
            self.update()
            print("[VIDEO] reached end and frozen on last frame.")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "rules_overlay"):
            self.rules_overlay.setFixedSize(self.size())

    # ── Background dessiné directement ───────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Fond noir de base
        painter.fillRect(self.rect(), QColor("#0a0a0a"))

        # Priorité à la vidéo (OpenCV)
        target_pix = self._video_pixmap if self._video_pixmap else self._bg_pixmap

        if target_pix and not target_pix.isNull():
            scaled = target_pix.scaled(
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
        # Layout racine
        self.root_lay = QVBoxLayout(self)
        self.root_lay.setContentsMargins(0, 0, 0, 0)
        
        # Conteneur global UI (pour l'affichage différé)
        self.ui_wrapper = QWidget()
        self.ui_wrapper.setStyleSheet("background: transparent;")
        ui_lay = QVBoxLayout(self.ui_wrapper)
        ui_lay.setContentsMargins(0, 0, 0, 0)
        ui_lay.setSpacing(0)
        self.root_lay.addWidget(self.ui_wrapper)
        
        # ── Header : Bouton Règles ────────────────────────
        header = QHBoxLayout()
        header.setContentsMargins(0, 30, 40, 0)
        header.addStretch()
        
        self.rules_btn = QPushButton("RÈGLES  ?")
        self.rules_btn.setFixedSize(140, 40)
        self.rules_btn.setCursor(Qt.PointingHandCursor)
        self.rules_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 215, 0, 0.1);
                color: #ffd700; border: 1px solid rgba(255, 215, 0, 0.4);
                border-radius: 15px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: rgba(255, 215, 0, 0.2); border-color: #ffd700; }
        """)
        self.rules_btn.clicked.connect(lambda: self.rules_overlay.show())
        header.addWidget(self.rules_btn)
        ui_lay.addLayout(header)

        # Conteneur principal avec effet de verre
        container = QWidget()
        container.setObjectName("mainContainer")
        container.setStyleSheet("""
            #mainContainer { background: transparent; }
        """)
        ui_lay.addWidget(container)

        main = QVBoxLayout(container)
        main.setContentsMargins(40, 40, 40, 0)
        main.setSpacing(10)

        # ── UI : Tout en bas ────────────────────────────────
        main.addStretch(85) # Un peu plus de stretch en haut pour redescendre légèrement

        # (Champs de noms supprimés à la demande de l'utilisateur)
        self.team_name_rouge = "Équipe Rouge"
        self.team_name_bleu = "Équipe Bleue"

        # Choix Mode (Images fournies par l'utilisateur)
        mode_lay = QHBoxLayout()
        mode_lay.setSpacing(30)
        mode_lay.setAlignment(Qt.AlignCenter)
        
        self.mode_buttons = {}
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Bouton SOLO VS IA - Taille Équilibrée
        img1_path = os.path.join(base_path, "boutton1-removebg-preview.png")
        btn_solo = ImageButton(img1_path, color=QColor("#cd7f32")) # Bronze/Gold
        btn_solo.setFixedSize(450, 154) 
        btn_solo.clicked.connect(lambda: self._select_mode(GameMode.VS_AI))
        self.mode_buttons[GameMode.VS_AI] = btn_solo
        mode_lay.addWidget(btn_solo)
        
        # Bouton EN LIGNE - Taille Équilibrée
        img2_path = os.path.join(base_path, "boutton2-removebg-preview.png")
        btn_online = ImageButton(img2_path, color=QColor("#00d4ff")) # Cyan
        btn_online.setFixedSize(450, 154) 
        btn_online.clicked.connect(lambda: self._select_mode(GameMode.ONLINE))
        self.mode_buttons[GameMode.ONLINE] = btn_online
        mode_lay.addWidget(btn_online)
        
        main.addLayout(mode_lay)

        main.addSpacing(10)

        # Start Button (Image fournie)
        img_start_path = os.path.join(base_path, "Gemini_Generated_Image_i8tfvei8tfvei8tf-removebg-preview.png")
        self.start_btn = ImageButton(img_start_path)
        self.start_btn.setFixedSize(700, 160)
        self.start_btn.clicked.connect(self._on_start)
        main.addWidget(self.start_btn, 0, Qt.AlignCenter)

        main.addSpacing(10)
        main.addStretch(15) # Un peu moins de stretch en bas
        
        self.ui_content = self.ui_wrapper
        self.ui_content.setVisible(False)

        # Mode par défaut
        self._select_mode(GameMode.VS_AI)

    # ── Helpers ──────────────────────────────────────────
    def _mode_style(self, selected: bool) -> str:
        # On ne change plus le stylesheet complet mais on peut stocker l'état
        return ""

    def _select_mode(self, mode: GameMode):
        self._selected_mode = mode
        for m, btn in self.mode_buttons.items():
            btn.selected = (m == mode)
            btn.update()

    def _on_start(self):
        self.game_start.emit(
            self._selected_mode.value,
            self.team_name_rouge,
            self.team_name_bleu
        )

    def set_authenticated_user(self, profile: dict | None, history: list[dict] | None = None):
        if not profile:
            return

        nickname = profile.get("nickname") or profile.get("email", "Joueur")
        if self.team_name_rouge in ("", "Équipe Rouge"):
            self.team_name_rouge = nickname
