from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QFrame)
from PyQt5.QtCore    import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui     import QPixmap, QFont, QFontDatabase, QIcon
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COLOR_GREEN, COLOR_ROUGE, COLOR_BLEU
from ui.widgets import ExitButton, TeamLineupPanel

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class ExchangeScreen(QWidget):
    """
    Écran final unifié (Échange → Révélation → Score)
    avec background 'backgroundexchangetfinal.png'
    et design Starting XI.
    """
    exchanges_done = pyqtSignal()
    play_again     = pyqtSignal()
    exit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._game_state     = None
        self._exchange_queue = []
        self._phase          = "EXCHANGE_TAKE"
        self._reveal_timer   = None
        self._reveal_index   = 0
        self._selected_player = None 
        self._player_to_take = None # Joueur de l'adversaire qu'on prend
        self._setup_ui()

    # ── Construction ──────────────────────────────────────
    def _setup_ui(self):
        # Fond (backgroundexchangetfinal.png)
        self.bg_lbl = QLabel(self)
        self.bg_lbl.setScaledContents(True)
        bg_path = os.path.join(BASE, "backgroundexchangetfinal.png")
        if os.path.exists(bg_path):
            self.bg_lbl.setPixmap(QPixmap(bg_path))

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── Header ───────────────────────────────────────
        header_container = QWidget()
        header_container.setFixedHeight(140)
        header_main = QHBoxLayout(header_container)
        header_main.setContentsMargins(40, 10, 40, 0)

        # Spacer pour équilibrer
        header_main.addSpacing(110)
        header_main.addStretch()

        logo_lbl = QLabel()
        logo_path = os.path.join(BASE, "Gemini_Generated_Image_w4q5buw4q5buw4q5-removebg-preview.png")
        if os.path.exists(logo_path):
            logo_lbl.setPixmap(QPixmap(logo_path).scaledToHeight(110, Qt.SmoothTransformation))
        logo_lbl.setStyleSheet("background: transparent; border: none;")
        logo_lbl.setAlignment(Qt.AlignCenter)
        header_main.addWidget(logo_lbl)

        header_main.addStretch()

        self.exit_btn = ExitButton()
        self.exit_btn.clicked.connect(self.exit_requested.emit)
        header_main.addWidget(self.exit_btn)
        
        header_container.setStyleSheet("background: transparent; border: none;")
        main_lay.addWidget(header_container)

        # ── Contenu central ──────────────────────────────
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        # Spacer gauche (Joueur Bleu) - Translation vers le centre
        content.addStretch(40)

        # Panneau Bleu
        self.panel_bleu = TeamLineupPanel("bleu")
        content.addWidget(self.panel_bleu, 3)

        # Zone centrale (VS + winner info + button)
        mid_container = QWidget()
        mid_container.setStyleSheet("background: transparent; border: none;")
        mid_container.setFixedWidth(600) # Élargi pour éviter les coupures de texte
        mid = QVBoxLayout(mid_container)
        mid.setAlignment(Qt.AlignCenter)
        mid.setSpacing(15)

        self.vs_lbl = QLabel("VS")
        self.vs_lbl.setAlignment(Qt.AlignCenter)
        self.vs_lbl.setStyleSheet(
            "color: white; font-size: 110px; font-weight: 900; "
            "background: transparent; border: none; font-style: italic;"
        )
        mid.addWidget(self.vs_lbl)

        # Scores totaux (affichés en phase RESULT)
        self.total_scores_lbl = QLabel("")
        self.total_scores_lbl.setAlignment(Qt.AlignCenter)
        self.total_scores_lbl.setStyleSheet(
            "color: #ffd700; font-size: 42px; font-weight: 900; "
            "background: transparent; letter-spacing: 4px;"
        )
        mid.addWidget(self.total_scores_lbl)

        self.phase_lbl = QLabel("")
        self.phase_lbl.setAlignment(Qt.AlignCenter)
        self.phase_lbl.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 22px; font-weight: 900; letter-spacing: 4px;")
        mid.addWidget(self.phase_lbl)

        self.winner_lbl = QLabel("")
        self.winner_lbl.setAlignment(Qt.AlignCenter)
        self.winner_lbl.setWordWrap(True)
        self.winner_lbl.setStyleSheet("color: white; font-size: 32px; font-weight: 900; letter-spacing: 4px;")
        mid.addWidget(self.winner_lbl)

        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet(
            "color: rgba(255,255,255,0.7); font-size: 13px; "
            "background: transparent; border: none;"
        )
        mid.addWidget(self.status_lbl)

        mid.addSpacing(30) # Espace supplémentaire avant les boutons
        self.action_btn = QPushButton("CONFIRMER")
        self.action_btn.setFixedSize(240, 50)
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.clicked.connect(self._on_action)
        mid.addWidget(self.action_btn, 0, Qt.AlignCenter)

        # Bouton Rejouer avec Image
        self.replay_img_btn = QPushButton()
        self.replay_img_btn.setFixedSize(250, 210)
        self.replay_img_btn.setCursor(Qt.PointingHandCursor)
        self.replay_img_btn.setStyleSheet("background: transparent; border: none;")
        
        replay_path = os.path.join(BASE, "Gemini_Generated_Image_8m8qbt8m8qbt8m8q-removebg-preview.png")
        if os.path.exists(replay_path):
            self.replay_img_btn.setIcon(QIcon(replay_path))
            self.replay_img_btn.setIconSize(QSize(250, 210))
        self.replay_img_btn.clicked.connect(self.play_again.emit)
        self.replay_img_btn.setVisible(False)
        mid.addWidget(self.replay_img_btn, 0, Qt.AlignCenter)
        self.action_btn.clicked.connect(self._on_action)
        mid.addWidget(self.action_btn, 0, Qt.AlignCenter)

        content.addWidget(mid_container, 3)

        # Panneau Rouge
        self.panel_rouge = TeamLineupPanel("rouge")
        content.addWidget(self.panel_rouge, 3)

        # Spacer droite (Joueur Rouge) - Translation vers le centre
        content.addStretch(40)

        main_lay.addLayout(content, 1)

        # Connexions pour l'interaction
        self.panel_bleu.player_clicked.connect(self._on_player_clicked)
        self.panel_rouge.player_clicked.connect(self._on_player_clicked)

    def _style_btn_gold(self):
        self.action_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #ffd700, stop:1 #c5850a);
                color: black; border-radius: 14px;
                font-weight: 900; font-size: 14px; letter-spacing: 2px;
            }
            QPushButton:hover  { background: #ffea00; }
            QPushButton:disabled { background: #333; color: #666; }
        """)

    def _style_btn_green(self):
        self.action_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00e676, stop:1 #00c853);
                color: black; border-radius: 14px;
                font-weight: 900; font-size: 14px; letter-spacing: 2px;
            }
            QPushButton:hover { background: #00ff88; }
        """)

    def resizeEvent(self, event):
        self.bg_lbl.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    # ══════════════════════════════════════════════════════
    # API PUBLIQUE
    # ══════════════════════════════════════════════════════
    def load(self, game_state, exchange_queue=None):
        self._game_state = game_state

        # Rafraîchir les panneaux (sans score encore)
        self.panel_bleu.load(game_state.team_bleu)
        self.panel_rouge.load(game_state.team_rouge)

        # File d'échanges
        if exchange_queue is not None:
            self._exchange_queue = list(exchange_queue)
        else:
            self._exchange_queue = []
            for color in ["rouge", "bleu"]:
                team = game_state.get_team(color)
                for _ in range(team.rouges):
                    self._exchange_queue.append(color)

        if self._exchange_queue:
            self._start_exchange_phase()
        else:
            self._start_reveal_phase()

    # ══════════════════════════════════════════════════════
    # PHASE 1 — ÉCHANGE
    # ══════════════════════════════════════════════════════
    def _start_exchange_phase(self):
        self._phase = "EXCHANGE_TAKE"
        self._selected_player = None
        self._player_to_take = None
        self.phase_lbl.setText("⚡  PHASE D'ÉCHANGE")

        if not self._exchange_queue:
            self._start_tactical_phase()
            return

        color_penalized = self._exchange_queue[0]
        adv_color = "bleu" if color_penalized == "rouge" else "rouge"
        adversary = self._game_state.get_team(adv_color)
        penalized = self._game_state.get_team(color_penalized)

        self.winner_lbl.setText(
            f"🔴 Carton rouge pour {penalized.name} !\n{adversary.name} : Choisissez un joueur à PRENDRE"
        )
        self.status_lbl.setText(f"Cliquez sur un joueur de {penalized.name}")
        self.action_btn.setText("PASSER L'ÉCHANGE")
        self._style_btn_gold()
        self.action_btn.setEnabled(True)

        # Activer l'interactivité sur le panneau de la victime
        self.panel_bleu.load(self._game_state.team_bleu, interactive=(color_penalized=="bleu"))
        self.panel_rouge.load(self._game_state.team_rouge, interactive=(color_penalized=="rouge"))

    def _on_player_clicked(self, player):
        if self._phase == "EXCHANGE_TAKE":
            # On vérifie qu'on clique bien sur un joueur de l'équipe pénalisée
            color_penalized = self._exchange_queue[0]
            team_penalized = self._game_state.get_team(color_penalized)
            
            if player in team_penalized.players:
                self._player_to_take = player
                self._start_exchange_give_phase()

        elif self._phase == "EXCHANGE_GIVE":
            # On vérifie qu'on clique sur un joueur de sa propre équipe (l'adversaire de la victime)
            color_penalized = self._exchange_queue[0]
            adv_color = "bleu" if color_penalized == "rouge" else "rouge"
            team_adversary = self._game_state.get_team(adv_color)

            if player in team_adversary.players:
                self._complete_exchange(self._player_to_take, player)

        elif self._phase == "TACTICAL":
            # Logique de swap (Titulaires <-> Remplaçants)
            if self._selected_player is None:
                self._selected_player = player
                self.status_lbl.setText(f"Sélectionné : {player.name}. Cliquez sur un autre pour swapper.")
            else:
                if self._selected_player == player:
                    self._selected_player = None
                    self.status_lbl.setText("Désélectionné.")
                else:
                    team_p1 = self._find_team_of_player(self._selected_player)
                    team_p2 = self._find_team_of_player(player)
                    if team_p1 and team_p1 == team_p2:
                        self._swap_players(team_p1, self._selected_player, player)
                        self._selected_player = None
                    else:
                        self._selected_player = player
                        self.status_lbl.setText(f"Nouveau joueur : {player.name}")

    def _start_exchange_give_phase(self):
        self._phase = "EXCHANGE_GIVE"
        color_penalized = self._exchange_queue[0]
        adv_color = "bleu" if color_penalized == "rouge" else "rouge"
        adversary = self._game_state.get_team(adv_color)

        self.winner_lbl.setText(
            f"🔄 Échange (2/2)\n{adversary.name} : Choisissez un joueur à DONNER"
        )
        self.status_lbl.setText(f"Cliquez sur un de VOS joueurs pour l'envoyer en face")
        
        # Activer l'interactivité sur le panneau de l'adversaire (celui qui donne)
        self.panel_bleu.load(self._game_state.team_bleu, interactive=(adv_color=="bleu"))
        self.panel_rouge.load(self._game_state.team_rouge, interactive=(adv_color=="rouge"))

    def _complete_exchange(self, taken_p, given_p):
        color_penalized = self._exchange_queue.pop(0)
        penalized = self._game_state.get_team(color_penalized)
        adv_color = "bleu" if color_penalized == "rouge" else "rouge"
        adversary = self._game_state.get_team(adv_color)

        # 1. Transfert : Penalized -> Adversary
        penalized.players.remove(taken_p)
        for pos, p in penalized.formation.items():
            if p == taken_p: penalized.formation[pos] = None; break
        adversary.players.append(taken_p)
        taken_p.pitch_pos = None # Va sur le banc
        adversary.formation["BENCH"].append(taken_p)

        # 2. Transfert : Adversary -> Penalized
        adversary.players.remove(given_p)
        for pos, p in adversary.formation.items():
            if p == given_p: adversary.formation[pos] = None; break
        penalized.players.append(given_p)
        given_p.pitch_pos = None # Va sur le banc
        penalized.formation["BENCH"].append(given_p)

        print(f"🔄 [EXCHANGE] {taken_p.name} ↔️ {given_p.name}")

        if self._exchange_queue:
            self._start_exchange_phase()
        else:
            self._start_tactical_phase()

    def _start_tactical_phase(self):
        self._phase = "TACTICAL"
        self._selected_player = None
        self.phase_lbl.setText("⚽  OPTIMISATION TACTIQUE")
        self.winner_lbl.setText("Préparez votre 11 final !\nCliquez sur 2 joueurs d'une équipe pour les intervertir")
        self.status_lbl.setText("Mode tactique actif")
        self.action_btn.setText("CONFIRMER TACHKILA")
        self._style_btn_green()
        self.action_btn.setVisible(True)
        self.action_btn.setEnabled(True)

        # Les deux panneaux sont interactifs
        self.panel_bleu.load(self._game_state.team_bleu, interactive=True)
        self.panel_rouge.load(self._game_state.team_rouge, interactive=True)

    def _swap_players(self, team, p1, p2):
        # Trouver les slots
        pos1 = None
        for k, v in team.formation.items():
            if v == p1: pos1 = k; break
        if not pos1 and p1 in team.formation["BENCH"]: pos1 = "BENCH"

        pos2 = None
        for k, v in team.formation.items():
            if v == p2: pos2 = k; break
        if not pos2 and p2 in team.formation["BENCH"]: pos2 = "BENCH"

        if not pos1 or not pos2: return

        # Effectuer le swap
        if pos1 == "BENCH":
            team.formation["BENCH"].remove(p1)
            team.formation[pos2] = p1
            p1.pitch_pos = (0.5, 0.5) # Temporaire, sera recalculé au load
        else:
            team.formation[pos1] = p2
        
        if pos2 == "BENCH":
            team.formation["BENCH"].remove(p2)
            team.formation[pos1] = p2
            p2.pitch_pos = (0.5, 0.5)
        else:
            team.formation[pos2] = p1
        
        # Gérer les bench proprement
        if pos1 == "BENCH": team.formation["BENCH"].append(p2); p2.pitch_pos = None
        if pos2 == "BENCH": team.formation["BENCH"].append(p1); p1.pitch_pos = None

        # Rafraîchir
        self.panel_bleu.load(self._game_state.team_bleu, interactive=True)
        self.panel_rouge.load(self._game_state.team_rouge, interactive=True)

    # ══════════════════════════════════════════════════════
    # PHASE 2 — RÉVÉLATION
    # ══════════════════════════════════════════════════════
    def _start_reveal_phase(self):
        self._phase = "REVEAL"
        # self.phase_lbl.setText("⭐  RÉVÉLATION DES RATINGS") # Supprimé
        self.phase_lbl.setText("RÉVÉLATION DES NOTES")
        self.status_lbl.setText("")
        self.action_btn.setVisible(False)

        self._game_state.start_reveal()

        # Mise à jour immédiate des panneaux (ratings révélés)
        self.panel_bleu.load(self._game_state.team_bleu, show_ratings=True)
        self.panel_rouge.load(self._game_state.team_rouge, show_ratings=True)

        QTimer.singleShot(1200, self._show_final_result)

    # ══════════════════════════════════════════════════════
    # PHASE 3 — RÉSULTAT FINAL
    # ══════════════════════════════════════════════════════
    def _show_final_result(self):
        self._phase = "RESULT"
        gs = self._game_state
        winner_color = gs.get_winner()

        r_total = gs.team_rouge.total_rating
        b_total = gs.team_bleu.total_rating

        # Recharger panneaux avec scores
        self.panel_bleu.load(gs.team_bleu,  score=b_total, is_winner=(winner_color == "bleu"), show_ratings=True)
        self.panel_rouge.load(gs.team_rouge, score=r_total, is_winner=(winner_color == "rouge"), show_ratings=True)
        self.total_scores_lbl.setText(f"{b_total} - {r_total}")

        if winner_color == "egalite":
            self.phase_lbl.setText("")
            self.winner_lbl.setText("ÉGALITÉ PARFAITE !")
            self.winner_lbl.setStyleSheet("color: white; font-size: 38px; font-weight: 900; letter-spacing: 4px;")
        else:
            win_name = gs.get_team(winner_color).name.upper()
            self.phase_lbl.setText("THE WINNER IS")
            self.winner_lbl.setText(win_name)
            color = COLOR_ROUGE if winner_color == "rouge" else COLOR_BLEU
            self.winner_lbl.setStyleSheet(f"color: {color}; font-size: 42px; font-weight: 900; letter-spacing: 6px;")
            
        self.action_btn.setVisible(False)
        self.replay_img_btn.setVisible(True)

    # ══════════════════════════════════════════════════════
    # BOUTON ACTION
    # ══════════════════════════════════════════════════════
    def _on_action(self):
        if self._phase in ["EXCHANGE_TAKE", "EXCHANGE_GIVE"]:
            # On passe simplement à la phase suivante (tactique ou prochaine queue)
            if self._exchange_queue:
                self._start_exchange_phase()
            else:
                self._start_tactical_phase()
        elif self._phase == "TACTICAL":
            self._start_reveal_phase()
        elif self._phase == "RESULT":
            self.play_again.emit()
