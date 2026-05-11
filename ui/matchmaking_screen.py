# ============================================================
# ui/matchmaking_screen.py — Écran du matchmaking online
# ============================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QScrollArea, QFrame, QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt5.QtGui import QColor, QPixmap, QPainter, QPainterPath, QPen, QBrush, QLinearGradient
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import COLOR_GREEN, COLOR_BLEU, COLOR_ROUGE
from ui.styles import STYLE_MASTERS_HEADER, STYLE_GLASS_PANEL, STYLE_PREMIUM_CARD
from services.matchmaking_service import MatchmakingService

class MatchmakingScreen(QWidget):
    """
    Écran pour chercher un adversaire en ligne (matchmaking)
    """
    
    # Signaux
    match_found = pyqtSignal(str)  # Émet l'ID du match quand trouvé
    cancel_requested = pyqtSignal()

    def __init__(self, matchmaking_service: MatchmakingService, user_id: str, parent=None):
        super().__init__(parent)
        self.matchmaking_service = matchmaking_service
        self.user_id = user_id
        self.selected_opponent = None
        self.match_id = None
        self.no_players_lbl = None
        self.no_invitations_lbl = None
        self.invitations_layout = None
        self.scroll_area = None
        self.players_layout = None
        self.pending_invitations = []
        self._match_started = False  # Flag pour éviter les émissions multiples
        
        self._setup_ui()
        self._refresh_data()
        
        # Timer pour rafraîchir la liste et vérifier les invitations
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._on_timer_tick)
        self.refresh_timer.start(1000)  # Rafraîchir toutes les 1s
    
    def closeEvent(self, event):
        """Arrêter le timer quand on ferme l'écran"""
        if self.refresh_timer:
            self.refresh_timer.stop()
        super().closeEvent(event)

    def reset(self):
        """Réinitialise l'écran de matchmaking"""
        self._match_started = False
        if not self.refresh_timer.isActive():
            self.refresh_timer.start(2000)

    def _setup_ui(self):
        self.bg_lbl = QLabel(self)
        self.bg_lbl.setScaledContents(True)
        bg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "images", "stadium_bg.png")
        if os.path.exists(bg_path):
            self.bg_lbl.setPixmap(QPixmap(bg_path))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Overlay Global (Plus transparent pour mieux voir le stade)
        overlay = QWidget()
        overlay.setStyleSheet("background: rgba(5, 10, 25, 0.35);")
        outer = QVBoxLayout(overlay)
        outer.setContentsMargins(40, 10, 40, 20)
        outer.setSpacing(15)
        main_layout.addWidget(overlay)

        # Header Logo (Sans cadre, directement sur le fond)
        logo_lbl = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Gemini_Generated_Image_w4q5buw4q5buw4q5-removebg-preview.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            logo_lbl.setPixmap(pix.scaled(600, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_lbl.setText("AHSAN KHOTA")
            logo_lbl.setStyleSheet("color: #ffd700; font-size: 32px; font-weight: 900; background: transparent;")
        
        logo_lbl.setAlignment(Qt.AlignCenter)
        logo_lbl.setStyleSheet("background: transparent; border: none;")
        outer.addWidget(logo_lbl)

        # Main Body - Two Columns
        body_lay = QHBoxLayout()
        body_lay.setSpacing(30)

        # --- LEFT COLUMN: PLAYERS ---
        left_col = QFrame()
        left_col.setObjectName("left_panel")
        left_col.setStyleSheet(STYLE_GLASS_PANEL)
        left_lay = QVBoxLayout(left_col)
        left_lay.setContentsMargins(15, 15, 15, 15)

        jd_header = QLabel("🛡️ JOUEURS DISPONIBLES")
        jd_header.setStyleSheet("color: #00e676; font-size: 14px; font-weight: 900; letter-spacing: 2px; background: transparent; border: none;")
        left_lay.addWidget(jd_header)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        
        self.players_container = QWidget()
        self.players_container.setStyleSheet("background: transparent;")
        self.players_layout = QVBoxLayout(self.players_container)
        self.players_layout.setContentsMargins(0, 10, 0, 10)
        self.players_layout.setSpacing(15)
        self.players_layout.setAlignment(Qt.AlignTop)
        
        self.scroll_area.setWidget(self.players_container)
        left_lay.addWidget(self.scroll_area)
        body_lay.addWidget(left_col, 2)

        # --- RIGHT COLUMN: INVITATIONS ---
        right_col = QFrame()
        right_col.setObjectName("right_panel")
        right_col.setStyleSheet(STYLE_GLASS_PANEL)
        right_lay = QVBoxLayout(right_col)
        right_lay.setContentsMargins(15, 15, 15, 15)

        inv_header = QLabel("⚡ INVITATIONS REÇUES")
        inv_header.setStyleSheet("color: #ff4444; font-size: 14px; font-weight: 900; letter-spacing: 2px; background: transparent; border: none;")
        right_lay.addWidget(inv_header)

        self.invitations_scroll = QScrollArea()
        self.invitations_scroll.setWidgetResizable(True)
        self.invitations_scroll.setFrameShape(QScrollArea.NoFrame)
        self.invitations_scroll.setStyleSheet("background: transparent; border: none;")
        
        self.invitations_container = QWidget()
        self.invitations_container.setStyleSheet("background: transparent;")
        self.invitations_layout = QVBoxLayout(self.invitations_container)
        self.invitations_layout.setContentsMargins(0, 10, 0, 10)
        self.invitations_layout.setSpacing(15)
        self.invitations_layout.setAlignment(Qt.AlignTop)
        
        self.invitations_scroll.setWidget(self.invitations_container)
        right_lay.addWidget(self.invitations_scroll)
        body_lay.addWidget(right_col, 1)

        outer.addLayout(body_lay, 1)

        # Footer Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)
        
        self.refresh_btn = QPushButton("🔄  RAFRAÎCHIR")
        self.refresh_btn.setFixedHeight(50)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0, 230, 118, 0.1);
                color: #00e676; border: 2px solid #00e676; border-radius: 15px;
                font-weight: 900; font-size: 14px; letter-spacing: 2px;
            }
            QPushButton:hover { background: rgba(0, 230, 118, 0.25); }
        """)
        self.refresh_btn.clicked.connect(self._refresh_data)
        btn_row.addWidget(self.refresh_btn, 1)

        self.cancel_btn = QPushButton("⬅  RETOUR")
        self.cancel_btn.setFixedHeight(50)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 68, 68, 0.1);
                color: #ff4444; border: 2px solid #ff4444; border-radius: 15px;
                font-weight: 900; font-size: 14px; letter-spacing: 2px;
            }
            QPushButton:hover { background: rgba(255, 68, 68, 0.25); }
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(self.cancel_btn, 1)
        
        outer.addLayout(btn_row)

    def resizeEvent(self, event):
        self.bg_lbl.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def _refresh_data(self):
        """Rafraîchit les joueurs disponibles ET les invitations reçues"""
        # Vérifier d'abord si un match a été accepté
        self._check_accepted_matches()
        # Puis rafraîchir les joueurs et invitations
        self._refresh_players()
        self._refresh_invitations()

    def _on_timer_tick(self):
        """Tick du timer principal"""
        # Arrêter le timer si le match a commencé
        if self._match_started:
            if self.refresh_timer.isActive():
                self.refresh_timer.stop()
            return
        
        # Sinon, rafraîchir normalement
        try:
            self._refresh_data()
        except Exception as e:
            print(f"⚠️ Erreur lors du rafraîchissement: {e}")

    def _check_accepted_matches(self):
        """
        Vérifie si un de nos matchs a été accepté par l'autre joueur
        (exécuté une seule fois)
        """
        if self._match_started:
            return  # Déjà lancé, ne rien faire
        
        try:
            accepted_matches = self.matchmaking_service.get_accepted_matches(self.user_id)
            if accepted_matches:
                match_id = accepted_matches[0]["id"]
                print(f"✅ Match ACCEPTÉ détecté! ID: {match_id}")
                print(f"   Passage au jeu pour {self.user_id}")
                self._match_started = True  # Marquer comme lancé
                self.refresh_timer.stop()   # <--- ARRÊT IMMÉDIAT DU TIMER
                self.match_found.emit(match_id)
        except Exception as e:
            print(f"⚠️ Erreur vérification matches acceptés: {e}")

    def _refresh_players(self):
        """Récupère et affiche les joueurs disponibles"""
        try:
            # Si le match a démarré, ne pas rafraîchir
            if self._match_started:
                return

            players = self.matchmaking_service.get_available_players(self.user_id)
            
            # Nettoyer complètement le layout
            if self.players_layout is not None:
                while self.players_layout.count() > 0:
                    item = self.players_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
            else:
                return

            if not players:
                print("ℹ️ Aucun joueur, affichage message vide")
                no_players_lbl = QLabel("⏳ Aucun joueur disponible...\nRéessaie dans quelques secondes")
                no_players_lbl.setStyleSheet("""
                    color: rgba(255,255,255,0.45);
                    font-size: 13px;
                """)
                no_players_lbl.setAlignment(Qt.AlignCenter)
                
                self.players_layout.addWidget(no_players_lbl)
                self.players_layout.addStretch()
                return

            # Afficher les joueurs
            print(f"✅ Ajout de {len(players)} joueurs à l'affichage")
            for player in players:
                player_card = self._create_player_card(player)
                self.players_layout.addWidget(player_card)

            self.players_layout.addStretch()
        except Exception as e:
            print(f"❌ ERREUR rafraîchissement: {e}")
            import traceback
            traceback.print_exc()

    def _refresh_invitations(self):
        """Récupère et affiche les invitations en attente"""
        try:
            if self._match_started or self.invitations_layout is None:
                return
            
            self.pending_invitations = self.matchmaking_service.get_pending_invitations(self.user_id)
            print(f"📬 {len(self.pending_invitations)} invitations reçues")
            
            # Nettoyer le layout
            while self.invitations_layout.count() > 0:
                item = self.invitations_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            if not self.pending_invitations:
                # Créer un nouveau label au lieu de réutiliser l'ancien
                no_inv_lbl = QLabel("Aucune invitation en attente")
                no_inv_lbl.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 12px;")
                no_inv_lbl.setAlignment(Qt.AlignCenter)
                
                self.invitations_layout.addWidget(no_inv_lbl)
                self.invitations_layout.addStretch()
                return

            # Afficher les invitations
            for inv in self.pending_invitations:
                inv_card = self._create_invitation_card(inv)
                self.invitations_layout.addWidget(inv_card)

            self.invitations_layout.addStretch()
        except Exception as e:
            print(f"❌ ERREUR rafraîchissement invitations: {e}")
            import traceback
            traceback.print_exc()

    def _create_invitation_card(self, invitation):
        """Crée une carte d'invitation horizontale avec le style premium"""
        card = QFrame()
        card.setFixedHeight(100)
        card.setStyleSheet(STYLE_PREMIUM_CARD)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        # Avatar + Info
        player = invitation.get("player", {})
        nickname = player.get("nickname", "Joueur")
        avatar_name = player.get("avatar")

        avatar_lbl = QLabel()
        avatar_lbl.setFixedSize(65, 65)
        
        # Illustration basée sur l'ID de l'envoyeur
        from hashlib import md5
        h = int(md5(str(player.get("id")).encode()).hexdigest(), 16)
        avatar_idx = (h % 4) + 1
        avatar_file = f"avatar_{avatar_idx}.png"
        
        avatar_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "images", avatar_file)
            
        if os.path.exists(avatar_path):
            pix = QPixmap(avatar_path).scaled(65, 65, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            avatar_lbl.setPixmap(pix)
        else:
            avatar_lbl.setText("👤")
            avatar_lbl.setStyleSheet("font-size: 30px; color: white;")
        
        layout.addWidget(avatar_lbl)
        
        msg_lay = QVBoxLayout()
        msg_lay.setSpacing(2)
        nick_lbl = QLabel(nickname.upper())
        nick_lbl.setStyleSheet("color: #ffd700; font-weight: 900; font-size: 14px; background: transparent; border: none;")
        info_lbl = QLabel("TE DÉFIE EN DUEL ! ⚡")
        info_lbl.setStyleSheet("color: #ffaa66; font-weight: 800; font-size: 10px; letter-spacing: 1px; background: transparent; border: none;")
        msg_lay.addStretch()
        msg_lay.addWidget(nick_lbl)
        msg_lay.addWidget(info_lbl)
        msg_lay.addStretch()
        layout.addLayout(msg_lay, 1)

        # Boutons
        accept_btn = QPushButton("ACCEPTER")
        accept_btn.setFixedSize(100, 35)
        accept_btn.setCursor(Qt.PointingHandCursor)
        accept_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 230, 118, 0.15);
                color: #00ff88; border: 2.2px solid #00ff88; border-radius: 10px;
                font-weight: 900; font-size: 10px;
            }}
            QPushButton:hover {{ background: #00ff88; color: black; }}
        """)
        accept_btn.clicked.connect(lambda: self._accept_invitation(invitation["id"]))
        layout.addWidget(accept_btn)

        decline_btn = QPushButton("REFUSER")
        decline_btn.setFixedSize(90, 35)
        decline_btn.setCursor(Qt.PointingHandCursor)
        decline_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 68, 68, 0.1);
                color: #ff4444; border: 1.5px solid #ff4444; border-radius: 10px;
                font-weight: 800; font-size: 10px;
            }}
            QPushButton:hover {{ background: rgba(255, 68, 68, 0.2); }}
        """)
        decline_btn.clicked.connect(lambda: self._decline_invitation(invitation["id"]))
        layout.addWidget(decline_btn)

        return card

    def _accept_invitation(self, invitation_id: str):
        """Accepte une invitation"""
        try:
            match = self.matchmaking_service.accept_invitation(invitation_id)
            if not match or not match.get("id"):
                QMessageBox.warning(self, "Erreur", "Le match n'a pas pu être créé.")
                return
            # ✅ Stopper le timer AVANT d'émettre le signal pour éviter les doublons
            self._match_started = True
            if self.refresh_timer.isActive():
                self.refresh_timer.stop()
            self.match_found.emit(match["id"])
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible d'accepter: {e}")

    def _decline_invitation(self, invitation_id: str):
        """Rejette une invitation"""
        try:
            self.matchmaking_service.decline_invitation(invitation_id)
            QMessageBox.information(self, "Invitation refusée ❌", "")
            self._refresh_invitations()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de refuser: {e}")

    def _create_player_card(self, player_info):
        """Crée une carte de joueur horizontale pour la liste verticale"""
        card = QFrame()
        card.setFixedHeight(100)
        card.setStyleSheet(STYLE_PREMIUM_CARD)
        
        lay = QHBoxLayout(card)
        lay.setContentsMargins(15, 5, 15, 5)
        lay.setSpacing(15)

        # Avatar Diamond
        avatar_lbl = QLabel()
        avatar_lbl.setFixedSize(70, 70)
        
        status = player_info.get("online_status", "offline")
        color = QColor("#00e676") if status == "online" else QColor("#ff4444")
        
        # Peindre le cadre de l'avatar (Rectangle Arrondi au lieu de Diamant)
        def paint_avatar_frame(label, color_obj, player_id):
            pix = QPixmap(70, 70)
            pix.fill(Qt.transparent)
            painter = QPainter(pix)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Cadre rectangulaire arrondi
            rect = pix.rect().adjusted(2, 2, -2, -2)
            painter.setBrush(QBrush(QColor(20, 30, 50, 200)))
            painter.setPen(QPen(color_obj, 3))
            painter.drawRoundedRect(rect, 12, 12)
            
            # Sélection de l'avatar illustration (1-4) basée sur l'ID du joueur
            import hashlib
            h = int(hashlib.md5(str(player_id).encode()).hexdigest(), 16)
            avatar_idx = (h % 4) + 1
            avatar_file = f"avatar_{avatar_idx}.png"
            
            avatar_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "images", avatar_file)
            
            if os.path.exists(avatar_path):
                avatar_pix = QPixmap(avatar_path).scaled(55, 55, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                # Centrer l'avatar
                painter.drawPixmap(7, 7, avatar_pix)
            else:
                painter.setPen(QPen(Qt.white))
                painter.drawText(pix.rect(), Qt.AlignCenter, "👤")
            
            painter.end()
            label.setPixmap(pix)

        paint_avatar_frame(avatar_lbl, color, player_info.get("id"))
        lay.addWidget(avatar_lbl)

        # Info
        info_lay = QVBoxLayout()
        info_lay.setSpacing(2)
        nick_lbl = QLabel(player_info.get("nickname", "Joueur").upper())
        nick_lbl.setStyleSheet("color: #ffd700; font-size: 16px; font-weight: 900; background: transparent; border: none;")
        status_lbl = QLabel(f"● {status.upper()}")
        status_lbl.setStyleSheet(f"color: {color.name()}; font-size: 11px; font-weight: 700; background: transparent; border: none;")
        info_lay.addStretch()
        info_lay.addWidget(nick_lbl)
        info_lay.addWidget(status_lbl)
        info_lay.addStretch()
        lay.addLayout(info_lay, 1)

        # Button
        challenge_btn = QPushButton("DÉFIER")
        challenge_btn.setFixedSize(110, 40)
        challenge_btn.setCursor(Qt.PointingHandCursor)
        challenge_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 212, 255, 0.1);
                color: #00d4ff; border: 2px solid #00d4ff; border-radius: 12px;
                font-weight: 900; font-size: 12px;
            }}
            QPushButton:hover {{ background: #00d4ff; color: black; }}
        """)
        challenge_btn.clicked.connect(lambda: self._challenge_player(player_info))
        lay.addWidget(challenge_btn)

        return card

    def _challenge_player(self, player: dict):
        """Envoie une invitation de match"""
        print(f"🖱️ Clic sur DÉFIER pour {player.get('nickname')} ({player.get('id')})")
        try:
            invitation = self.matchmaking_service.send_invitation(
                self.user_id,
                player["id"]
            )
            
            if invitation.get("auto_accepted"):
                print(f"✅ Match auto-accepté (ID: {invitation['id']})")
                self._match_started = True
                self.refresh_timer.stop()
                self.match_found.emit(invitation["id"])
                return
            
            if invitation.get("already_sent"):
                QMessageBox.information(self, "Défi en cours ⏳", f"Tu as déjà défié {player['nickname']}.\nAttend qu'il accepte ou rafraîchis.")
                return

            QMessageBox.information(
                self,
                "Défi envoyé !",
                f"Ton défi à {player['nickname']} a été envoyé. ⚡\n\n"
                f"En attente de sa réponse..."
            )
            
            # Mettre à jour l'interface
            self._refresh_players()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible d'envoyer le défi: {e}")

    def _on_cancel(self):
        """Annuler le matchmaking"""
        self.refresh_timer.stop()
        self.cancel_requested.emit()

    def closeEvent(self, event):
        """Nettoyer les ressources avant fermeture"""
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
        super().closeEvent(event)

    def set_online_status(self, status: str):
        """Met à jour le statut en ligne"""
        self.matchmaking_service.set_online_status(self.user_id, status)
