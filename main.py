#!/usr/bin/env python3
# ============================================================
# main.py — Contrôleur principal Ahsan Khota — Phase 2
# ============================================================

import sys, os, random, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import (QApplication, QMainWindow, QStackedWidget, QMessageBox, QInputDialog)
from PyQt5.QtCore    import Qt, QTimer, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist, QMediaContent

from config          import APP_TITLE, APP_WIDTH, APP_HEIGHT, TOTAL_MANCHES, COLOR_ROUGE, COLOR_BLEU
from ui.styles       import STYLE_APP
from ui.auth_screen    import AuthScreen
from ui.intro_screen   import IntroScreen
from ui.buzz_screen    import BuzzScreen
from ui.answer_screen  import AnswerScreen
from ui.pick_screen    import PickScreen
from ui.exchange_screen import ExchangeScreen
from ui.reveal_screen  import RevealScreen
from ui.difficulty_screen import DifficultyScreen
from ui.matchmaking_screen import MatchmakingScreen
from ui.round_selection_screen import RoundSelectionScreen
from game.data  import GameData
from game.state import GameState, GameMode, Phase, TeamState, QuestionType, RoundType
from game.deterministic import seed_from_parts
from game.questions_static import get_questions
from ai.agent       import ComputerOpponent
from ai.integration import AIPlayer
from services.supabase_service import SupabaseService
from services.matchmaking_service import MatchmakingService
from services.question_generator import DynamicQuestionGenerator
from services.pollinations_service import PollinationsService

# ── Index des écrans dans le QStackedWidget ───────────────
IDX_AUTH        = 0
IDX_INTRO       = 1
IDX_BUZZ        = 2
IDX_ANSWER      = 3
IDX_PICK        = 4
IDX_EXCHANGE    = 5
IDX_REVEAL      = 6
IDX_DIFFICULTY  = 7
IDX_ROUND_SELECT = 8   # ajouté statiquement dans _setup_screens
IDX_MATCHMAKING  = 9   # ajouté dynamiquement dans _show_matchmaking()


class AhsanKhotaApp(QMainWindow):
    """
    Contrôleur principal du jeu.
    Gère :
      - la navigation entre les 6 écrans
      - toute la logique de jeu (buzz → réponse → pick → échange → révélation)
      - l'état de la partie (GameState)
    """

    def __init__(self):
        super().__init__()
        self.supabase = SupabaseService()
        self.matchmaking = None  # Initialized after auth
        self.question_generator = None  # Initialized when needed
        self.current_profile = None
        self._score_saved = False
        self._lazy_pending_start = None
        self._is_guest = False

        self.game_data  = None
        self.game_state = None
        self.questions  = []
        self.question_generator = DynamicQuestionGenerator()
        self.pollinations = PollinationsService()
        self._current_question = {}
        self.ai_player  = None          # AIPlayer (mode VS_AI uniquement)
        self._pending_start = None      # tuple en attente pour VS_AI
        self._opponent_profile = None   # Profil de l'adversaire en ligne
        self._current_match_id = None   # ID du match actuel (ONLINE)
        self._answerer_color = None     # Qui doit répondre (rouge/bleu)
        self._last_opponent_answer_id = None # Tracer l'ID de la dernière réponse opponent pour éviter doublons
        self._poll_opponent_timer = None # Timer pour polling opponent answers
        self._opponent_buzz_timer = None # Timer pour polling opponent buzz
        self._buzz_timeout_timer = None # Timeout déterministe de buzz
        self._match_seed = None
        self._skip_pending_color = None
        self._skip_pending_color = None
        self._load_data()
        self._setup_window()
        self._setup_screens()
        self._init_audio()
        self._connect_signals()
        
    def _init_audio(self):
        # Initialiser le lecteur de musique et les playlists
        self.music_player = QMediaPlayer()
        
        # Musique des menus
        self.menu_playlist = QMediaPlaylist()
        menu_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Percussion Sport Drums by Infraction [No Copyright Music]  Football.mp3")
        if os.path.exists(menu_path):
            self.menu_playlist.addMedia(QMediaContent(QUrl.fromLocalFile(menu_path)))
        self.menu_playlist.setPlaybackMode(QMediaPlaylist.Loop)
        
        # Musique du match
        self.match_playlist = QMediaPlaylist()
        match_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sport-powerful-rock-moto-by-infraction-copyright-free-music-hard-race_eqUF8tgX.mp3")
        if os.path.exists(match_path):
            self.match_playlist.addMedia(QMediaContent(QUrl.fromLocalFile(match_path)))
        self.match_playlist.setPlaybackMode(QMediaPlaylist.Loop)
        
        # Lancer la musique des menus au démarrage
        self.music_player.setPlaylist(self.menu_playlist)
        self.music_player.setVolume(25)
        self.music_player.play()
        
        # Effet sonore du buzzer
        self.sfx_player = QMediaPlayer()
        sfx_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wrong-buzzer-sound-effect_gadUs3pk.mp3")
        if os.path.exists(sfx_path):
            self.sfx_player.setMedia(QMediaContent(QUrl.fromLocalFile(sfx_path)))
            self.sfx_player.setVolume(100)

    # ─────────────────────────────────────────────────────
    # INITIALISATION
    # ─────────────────────────────────────────────────────
    def _load_data(self):
        try:
            self.game_data = GameData()
        except FileNotFoundError as e:
            QMessageBox.critical(
                None, "Erreur — Données FIFA manquantes",
                f"Impossible de charger male_players.csv :\n\n{e}\n\n"
                f"Télécharge le fichier depuis Kaggle et place-le dans data/"
            )
            sys.exit(1)

    def _setup_window(self):
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(APP_WIDTH, APP_HEIGHT)
        self.resize(APP_WIDTH, APP_HEIGHT)
        self.setStyleSheet(STYLE_APP)

        # ── Supprimer tous les cadres indésirables ────────
        # Barre de menu (en haut)
        self.menuBar().setVisible(False)
        self.menuBar().setMaximumHeight(0)
        # Barre de statut (en bas)
        self.statusBar().setVisible(False)
        self.statusBar().setMaximumHeight(0)
        # Pas de barre d'outils
        self.setUnifiedTitleAndToolBarOnMac(False)

        # Style pour supprimer tout padding/margin résiduel
        self.setStyleSheet(STYLE_APP + """
            QMainWindow {
                margin: 0px;
                padding: 0px;
                border: none;
            }
            QMainWindow::separator {
                width: 0px;
                height: 0px;
            }
            QMenuBar {
                max-height: 0px;
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QStatusBar {
                max-height: 0px;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)

        # Centrer
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width()  - APP_WIDTH)  // 2,
            (screen.height() - APP_HEIGHT) // 2
        )

    def _setup_screens(self):
        self.stack = QStackedWidget()
        self.stack.setContentsMargins(0, 0, 0, 0)
        self.stack.setStyleSheet("QStackedWidget { border: none; margin: 0px; padding: 0px; }")
        self.setCentralWidget(self.stack)

        self.auth_screen     = AuthScreen(self.supabase)
        self.intro_screen    = IntroScreen()
        self.buzz_screen     = BuzzScreen()
        self.answer_screen   = AnswerScreen()
        self.pick_screen     = PickScreen()
        self.exchange_screen = ExchangeScreen()
        self.reveal_screen   = RevealScreen()
        self.difficulty_screen = DifficultyScreen()
        self.matchmaking_screen = None  # Created after auth
        self.round_selection_screen = RoundSelectionScreen()

        self.stack.addWidget(self.auth_screen)       # 0
        self.stack.addWidget(self.intro_screen)      # 1
        self.stack.addWidget(self.buzz_screen)       # 2
        self.stack.addWidget(self.answer_screen)     # 3
        self.stack.addWidget(self.pick_screen)       # 4
        self.stack.addWidget(self.exchange_screen)   # 5
        self.stack.addWidget(self.reveal_screen)     # 6
        self.stack.addWidget(self.difficulty_screen) # 7
        self.stack.addWidget(self.round_selection_screen) # index 8 (IDX_ROUND_SELECT)
        # matchmaking_screen ajouté dynamiquement dans _show_matchmaking() → index 9 (IDX_MATCHMAKING)

        self.stack.setCurrentIndex(IDX_INTRO)

    def _connect_signals(self):
        # Auth
        self.auth_screen.auth_success.connect(self._on_auth_success)
        self.auth_screen.continue_offline.connect(self._on_continue_offline)

        # Intro → démarrage
        self.intro_screen.game_start.connect(self._on_game_start)

        # Buzz → réponse
        self.buzz_screen.buzzed.connect(self._on_buzzed)

        # Réponse → résultat
        self.answer_screen.answer_selected.connect(self._on_answer_selected)
        self.answer_screen.timer_expired.connect(self._on_timer_expired)

        # Pick → joueur choisi
        self.pick_screen.player_picked.connect(self._on_player_picked)

        # Échange → signal legacy (gardé pour compatibilité AI)
        self.exchange_screen.exchanges_done.connect(self._on_exchanges_done)

        # Échange → rejouer (nouveau flux unifié)
        self.exchange_screen.play_again.connect(self._back_to_intro)

        # Boutons EXIT partout
        self.buzz_screen.exit_requested.connect(self._back_to_intro)
        self.answer_screen.exit_requested.connect(self._back_to_intro)
        self.pick_screen.exit_requested.connect(self._back_to_intro)
        self.exchange_screen.exit_requested.connect(self._back_to_intro)

        # Difficulté IA
        self.difficulty_screen.difficulty_selected.connect(self._on_difficulty_selected)
        self.difficulty_screen.back_pressed.connect(self._back_to_intro)

    # ─────────────────────────────────────────────────────
    # NAVIGATION
    # ─────────────────────────────────────────────────────
    def _show(self, idx: int):
        self.stack.setCurrentIndex(idx)
        if idx == IDX_BUZZ:
            self.buzz_screen.setFocus()

    def _show_round_select(self):
        """Affiche l'écran de sélection de manche (utilise setCurrentWidget pour éviter les problèmes d'index)"""
        self.stack.setCurrentWidget(self.round_selection_screen)

    def _back_to_intro(self):
        self.game_state = None
        self._cancel_buzz_timeout()
        if self.ai_player:
            self.ai_player.cancel_all()
            self.ai_player = None
        self._pending_start = None
        self._score_saved = False
        self._is_ingame = False
        self._current_match_id = None
        self._match_seed = None
        
        # Mark as offline if authenticated
        if self.current_profile and self.matchmaking:
            self.matchmaking.set_online_status(self.current_profile["id"], "offline")
            
        if hasattr(self, 'music_player') and self.music_player.playlist() != self.menu_playlist:
            self.music_player.setPlaylist(self.menu_playlist)
            self.music_player.play()
            
        self._show(IDX_INTRO)

    def _on_auth_success(self, profile: dict):
        self.current_profile = profile
        self._is_guest = False
        # Initialize matchmaking service for online mode
        if not self.matchmaking and self.supabase.is_ready:
            self.matchmaking = MatchmakingService(self.supabase.client)
        history = []
        if self.supabase.is_ready and profile.get("id"):
            try:
                history = self.supabase.get_score_history(profile["id"], limit=10)
            except Exception:
                history = []
        self.intro_screen.set_authenticated_user(profile, history)
        
        # Si on venait d'un clic "Play", on reprend
        if self._lazy_pending_start:
            params = self._lazy_pending_start
            self._lazy_pending_start = None
            self._on_game_start(*params)
        else:
            self._show(IDX_INTRO)

    def _on_continue_offline(self):
        self._is_guest = True
        self.current_profile = None
        self.intro_screen.set_authenticated_user(None)
        
        if self._lazy_pending_start:
            params = self._lazy_pending_start
            self._lazy_pending_start = None
            self._on_game_start(*params)
        else:
            self._show(IDX_INTRO)

    # ─────────────────────────────────────────────────────
    # DÉMARRAGE D'UNE PARTIE
    # ─────────────────────────────────────────────────────
    def _on_game_start(self, mode_str: str, nom_rouge: str, nom_bleu: str):
        # Lazy login check
        if not self.current_profile and not self._is_guest:
            self._lazy_pending_start = (mode_str, nom_rouge, nom_bleu)
            self._show(IDX_AUTH)
            return
        
        # Re-check online mode (requires auth, even if guest chose offline before)
        mode = GameMode(mode_str)
        if mode == GameMode.ONLINE and not self.current_profile:
            QMessageBox.warning(self, "Authentification requise", "Le mode en ligne nécessite un compte joueur.")
            self._is_guest = False # Reset to force login again
            self._lazy_pending_start = (mode_str, nom_rouge, nom_bleu)
            self._show(IDX_AUTH)
            return


        # Mode VS_AI → écran de difficulté d'abord
        if mode == GameMode.VS_AI:
            self._pending_start = (mode_str, nom_rouge, nom_bleu)
            self._show(IDX_DIFFICULTY)
            return

        # Mode ONLINE → écran de matchmaking
        if mode == GameMode.ONLINE:
            if not self.current_profile:
                QMessageBox.warning(self, "Erreur", "Vous devez être connecté pour jouer en ligne !")
                self._back_to_intro()
                return
            if not self.matchmaking:
                self.matchmaking = MatchmakingService(self.supabase.client)
            self.matchmaking.set_online_status(self.current_profile["id"], "online")
            self._show_matchmaking()
            return

        # Mode LOCAL / SOLO → démarrage automatique (Round 1)
        self._nom_rouge = nom_rouge
        self._nom_bleu = nom_bleu
        self._current_mode = mode_str
        self._current_match_id = None

        self._do_start(mode_str, nom_rouge, nom_bleu, match_id=None, round_start=0)


    def _on_difficulty_selected(self, difficulty: str):
        """Callback difficulté IA choisie — créer l'agent et lancer"""
        mode_str, nom_rouge, nom_bleu = self._pending_start
        self._pending_start = None

        ai_seed = seed_from_parts("ai", difficulty, mode_str, nom_rouge, nom_bleu)
        agent = ComputerOpponent(difficulty=difficulty, seed=ai_seed)
        self.ai_player = AIPlayer(agent, parent=self, seed=ai_seed)
        self.ai_player.buzz_action.connect(self._on_ai_buzz)
        self.ai_player.answer_action.connect(self._on_ai_answer)
        self.ai_player.pick_action.connect(self._on_ai_pick)

        nom_bleu = f"🤖 Agent ({difficulty.capitalize()})"
        print(f"[AI] Agent créé : {agent}")
        self._nom_rouge = nom_rouge
        self._nom_bleu = nom_bleu
        self._current_mode = mode_str
        self._current_match_id = None

        self._do_start(mode_str, nom_rouge, nom_bleu, match_id=None, round_start=0)

    def _show_matchmaking(self):
        """Affiche l'écran de matchmaking"""
        if not self.matchmaking_screen:
            self.matchmaking_screen = MatchmakingScreen(
                self.matchmaking,
                self.current_profile["id"]
            )
            self.matchmaking_screen.match_found.connect(self._on_match_found)
            self.matchmaking_screen.cancel_requested.connect(self._back_to_intro)
            self.stack.addWidget(self.matchmaking_screen)
        else:
            # Réinitialiser si on revient du jeu
            self.matchmaking_screen.reset()
        self._show(IDX_MATCHMAKING)

    def _on_match_found(self, match_id: str):
        """Appelé quand un match est accepté"""
        try:
            if hasattr(self, "_is_ingame") and self._is_ingame:
                print("⚠️ Signal match_found ignoré car la partie est déjà lancée.")
                return
            
            match_data = self.matchmaking.client.table("matches").select("*").eq("id", match_id).single().execute()
            match_info = match_data.data if match_data.data else {}
            
            opponent_id = match_info.get("player2_id") if match_info.get("player1_id") == self.current_profile["id"] else match_info.get("player1_id")
            self._opponent_profile = self.matchmaking.get_user_profile(opponent_id)
            
            # Charger les noms depuis le match (synchronisé BD)
            nom_rouge = match_info.get("player1_nickname")
            nom_bleu = match_info.get("player2_nickname")
            
            if not nom_rouge or not nom_bleu or nom_rouge == "Joueur 1" or nom_bleu == "Joueur 2":
                p1_prof = self.matchmaking.get_user_profile(match_info["player1_id"])
                p2_prof = self.matchmaking.get_user_profile(match_info["player2_id"])
                
                p1_name = p1_prof.get("nickname") if p1_prof else None
                if not p1_name and p1_prof: p1_name = p1_prof.get("email")
                nom_rouge = p1_name or "Joueur 1"
                
                p2_name = p2_prof.get("nickname") if p2_prof else None
                if not p2_name and p2_prof: p2_name = p2_prof.get("email")
                nom_bleu = p2_name or "Joueur 2"
                
                self.matchmaking.update_match_nicknames(match_id, nom_rouge, nom_bleu)
            
            self._is_ingame = True 
            self._nom_rouge = nom_rouge
            self._nom_bleu = nom_bleu
            self._current_match_id = match_id
            self._current_mode = "online"
            
            # Qui choisit la manche ? C'est le Player 2 (Celui qui a accepté l'invitation)
            is_player1 = (self.current_profile["id"] == match_info["player1_id"])
            
            try: self.round_selection_screen.round_selected.disconnect()
            except: pass
            
            # Marquer le match comme actif
            self.matchmaking.start_match(match_id)
            
            if is_player1:
                # Host : Pas de choix de manche, on commence direct
                self.matchmaking.init_match_state(match_id, round_number=1)
                self._do_start("online", self._nom_rouge, self._nom_bleu, match_id, round_start=0)
            else:
                # Acceptor : Attend que l'host initialise (ou on force le start à 0)
                self._do_start("online", self._nom_rouge, self._nom_bleu, match_id, round_start=0)
            
        except Exception as e:
            print(f"❌ Erreur on_match_found: {e}")
            self._is_ingame = False
            self._back_to_intro()

    def _on_online_round_selected(self, round_idx: int):
        """Player 2 a cliqué sur une manche"""
        # Il initialise l'état du match en base de données avec sa manche
        self.matchmaking.init_match_state(self._current_match_id, round_number=round_idx + 1)
        self._do_start("online", self._nom_rouge, self._nom_bleu, self._current_match_id, round_start=round_idx)

    def _wait_for_round_selection(self, match_id: str, retry_count: int):
        """Player 1 attend que Player 2 initialise le match state avec la manche choisi"""
        if not self._is_ingame: return # Annulé
        
        ms = self.matchmaking.get_match_state(match_id)
        if ms:
            start_num = ms.get("round_number", 1)
            print(f"✅ Player 2 a choisi la manche : {start_num}")
            self._do_start("online", self._nom_rouge, self._nom_bleu, match_id, round_start=start_num - 1)
        else:
            if retry_count < 120:
                QTimer.singleShot(1000, lambda: self._wait_for_round_selection(match_id, retry_count+1))
            else:
                QMessageBox.critical(self, "Erreur", "L'adversaire n'a pas sélectionné de manche.")
                self._is_ingame = False
                self._back_to_intro()

    def _do_start(self, mode_str: str, nom_rouge: str, nom_bleu: str, match_id: str = None, round_start: int = 0):
        """Lance effectivement la partie une fois la manche sélectionnée"""
        mode = GameMode(mode_str)
        self._score_saved = False
        self._current_match_id = match_id  # Stocker pour utiliser plus tard

        # Mode ONLINE : marquer le match comme actif
        if match_id and self.matchmaking:
            self.matchmaking.start_match(match_id)
            # L'état du match a déjà été initialisé par le P2 ou checké par P1.

        self._match_seed = seed_from_parts(
            mode_str,
            nom_rouge,
            nom_bleu,
            match_id or "local"
        )

        self.game_state = GameState(mode=mode)
        self.game_state.team_rouge.name = nom_rouge
        self.game_state.team_bleu.name  = nom_bleu
        self.game_state.manche = round_start
        self.game_state.question_index = round_start  # <--- CRITIQUE : Sync l'index de question avec la manche de départ
        self.game_state.init_rarity_plan(self._match_seed)
        
        # Synchroniser current_round selon la manche de départ (4 DEF, 3 MID, 3 ATT, 1 GK, puis banc)
        if round_start < 4:
            self.game_state.current_round = RoundType.DEFENDERS
        elif round_start < 7:
            self.game_state.current_round = RoundType.MIDFIELDERS
        elif round_start < 10:
            self.game_state.current_round = RoundType.ATTACKERS
        elif round_start == 10:
            self.game_state.current_round = RoundType.GOALKEEPER
        else:
            self.game_state.current_round = RoundType.BENCH

        # ── Synchronisation du HASARD ──────────────────────
        if match_id:
            self.game_state.legend_manche = self.game_state.rarity_plan.index("ELITE") if "ELITE" in self.game_state.rarity_plan else 0
            print(f"🎲 [DO_START] Match {match_id} | Seed: {self._match_seed} | Rarity: {self.game_state.current_rarity()}")
            
        self.game_state.match_positions = self.game_data.get_match_positions(seed=self._match_seed)
        
        # ── Synchronisation des Questions ──────────────────
        if mode == GameMode.ONLINE and match_id:
            self._sync_online_questions(match_id)
        else:
            # Mode LOCAL / Solo / AI
            from PyQt5.QtWidgets import QProgressDialog
            progress = QProgressDialog("Génération de vos questions uniques par l'IA Mistral...\nCela prendra quelques secondes.", None, 0, 0, self)
            progress.setWindowTitle("Veuillez patienter")
            progress.setWindowModality(Qt.WindowModal)
            progress.setCancelButton(None)
            progress.setStyleSheet("QLabel { color: white; font-size: 14px; font-weight: bold; } QProgressDialog { background-color: #1a2540; }")
            progress.show()
            QApplication.processEvents()
            
            self.questions = self._build_questions()
            
            progress.close()
            self._start_game_after_sync(nom_rouge, nom_bleu, match_id)

    def _sync_online_questions(self, match_id: str, retry_count: int = 0):
        """Récupère ou génère les questions de manière synchrone"""
        print(f"🔄 Synchronisation des questions (essai {retry_count+1})...")
        self.questions = self.matchmaking.get_match_questions(match_id)
        
        if self.questions:
            print(f"✅ {len(self.questions)} questions récupérées depuis la DB.")
            self._start_game_after_sync(self.game_state.team_rouge.name, self.game_state.team_bleu.name, match_id)
            return

        match_info = self.matchmaking.get_match_info(match_id)
        if not match_info: 
             QTimer.singleShot(1000, lambda: self._sync_online_questions(match_id, retry_count+1))
             return

        is_player1 = (self.current_profile["id"] == match_info["player1_id"])
        
        if is_player1:
            print(f"🆕 Player 1 : Génération des questions IA pour le match...")
            from PyQt5.QtWidgets import QProgressDialog
            progress = QProgressDialog("Génération de vos questions uniques par l'IA Mistral...\nCela prendra quelques secondes.", None, 0, 0, self)
            progress.setWindowTitle("Veuillez patienter")
            progress.setWindowModality(Qt.WindowModal)
            progress.setCancelButton(None)
            progress.setStyleSheet("QLabel { color: white; font-size: 14px; font-weight: bold; } QProgressDialog { background-color: #1a2540; }")
            progress.show()
            QApplication.processEvents()
            
            # P1 génère
            self.questions = self._build_questions()
            success = self.matchmaking.generate_match_questions(match_id, self.questions)
            
            progress.close()
            self._start_game_after_sync(self.game_state.team_rouge.name, self.game_state.team_bleu.name, match_id)
        else:
            # Player 2 : on attend P1
            if retry_count < 60:
                print(f"⌛ Player 2 [Match {match_id[:8]}] : En attente des questions de l'hôte...")
                QTimer.singleShot(1000, lambda: self._sync_online_questions(match_id, retry_count+1))
            else:
                QMessageBox.critical(self, "Erreur Sync", "Délai API dépassé...")
                self._is_ingame = False
                self._back_to_intro()

    def _start_game_after_sync(self, nom_rouge, nom_bleu, match_id):
        """Finalise le lancement après que les questions soient chargées"""
        print(f"\n{'='*50}")
        print(f"[GAME START] {nom_rouge} vs {nom_bleu}")
        print(f"[GAME START] {len(self.questions)} questions prêtes")
        if match_id:
            print(f"[MATCH ID] {match_id}")
        print(f"{'='*50}")

        if hasattr(self, 'music_player') and self.music_player.playlist() != self.match_playlist:
            self.music_player.setPlaylist(self.match_playlist)
            self.music_player.play()

        self._start_manche()

    # ─────────────────────────────────────────────────────
    # MANCHE
    # ─────────────────────────────────────────────────────
    def _start_manche(self):
        """Prépare et affiche la manche courante"""
        gs = self.game_state
        if not gs: return

        self._skip_pending_color = None
        self._cancel_buzz_timeout()

        # ── SÉCURITÉ : Génération dynamique si question manquante ──
        # (Cas où on a eu des questions annulées et qu'on dépasse le pool initial)
        if len(self.questions) <= gs.question_index:
            from PyQt5.QtWidgets import QProgressDialog
            progress = QProgressDialog("Génération d'une question de remplacement par l'IA...", None, 0, 0, self)
            progress.setWindowTitle("Veuillez patienter")
            progress.setWindowModality(Qt.WindowModal)
            progress.setCancelButton(None)
            progress.setStyleSheet("QLabel { color: white; font-size: 14px; font-weight: bold; } QProgressDialog { background-color: #1a2540; }")
            progress.show()
            QApplication.processEvents()

            if gs.mode == GameMode.ONLINE and self._current_match_id:
                # En ONLINE, on synchronise avec la BD
                try:
                    match_info = self.matchmaking.get_match_info(self._current_match_id)
                    is_player1 = (self.current_profile["id"] == match_info["player1_id"])
                    
                    if is_player1:
                        # Master génère et sauve
                        while len(self.questions) <= gs.question_index:
                            print(f"🆕 [MASTER] Génération d'une question supplémentaire (index {gs.question_index})...")
                            new_q = self._generate_single_question(gs.current_round, gs.manche)
                            self.questions.append(new_q)
                            self.matchmaking.save_single_question(self._current_match_id, gs.question_index + 1, new_q)
                    else:
                        # Slave récupère la question en BD
                        print(f"⏳ [SLAVE] Récupération de la question {gs.question_index + 1}...")
                        db_qs = self.matchmaking.get_match_questions(self._current_match_id)
                        if len(db_qs) > gs.question_index:
                            self.questions = db_qs
                        else:
                            print(f"⚠️ [SLAVE] Question {gs.question_index + 1} non trouvée en BD! Retentative dans 1s...")
                            progress.close()
                            QTimer.singleShot(1000, self._start_manche)
                            return
                except Exception as e:
                    print(f"❌ Erreur sync question: {e}")
            else:
                # Solo / AI / Local
                while len(self.questions) <= gs.question_index:
                    print(f"🆕 Génération question locale (index {gs.question_index})")
                    self.questions.append(self._generate_single_question(gs.current_round, gs.manche))
                    
            progress.close()

        # Si ONLINE, on rafraîchit la liste pour être sûr d'avoir ce que l'hôte a généré
        if gs.mode == GameMode.ONLINE and self._current_match_id:
            db_questions = self.matchmaking.get_match_questions(self._current_match_id)
            if len(db_questions) > len(self.questions):
                self.questions = db_questions

        # Récupérer la question actuelle via question_index
        self._current_question = self.questions[gs.question_index]

        # Position + paire de joueurs (DÉTERMINISTE via seed)
        pos_group, pos_label = gs.current_position()
        seed_int = seed_from_parts(self._match_seed, gs.question_index, gs.manche, pos_group)
        rarity_tier = gs.current_rarity()
        used_ids = {p.player_id for p in gs.team_rouge.players + gs.team_bleu.players}
        p1, p2 = self.game_data.get_similar_pair(
            pos_group,
            excluded_ids=used_ids,
            seed=seed_int,
            rarity_tier=rarity_tier,
        )
        gs.current_players = (p1, p2)
        
        # Si Round Image Guess, ajouter l'URL de l'image à la question
        if gs.get_question_type() == QuestionType.IMAGE_GUESS:
            image_rng = random.Random(seed_from_parts(self._match_seed, gs.question_index, "image"))
            # On génère une partie aléatoire du joueur 1 (ou 2)
            part = image_rng.choice(["cheveux", "yeux", "barbe", "visage"])
            prompt = self.pollinations.get_player_part_prompt(p1.name, part)
            
            # Seed déterministe pour l'image aussi
            img_seed = image_rng.randint(1, 10000)
            self._current_question["image_url"] = self.pollinations.get_image_url(prompt, seed=img_seed)
            
            # Définir les options réelles (Le joueur correct + 3 aléatoires)
            correct_name = p1.name
            
            # Chercher des distracteurs dans le même groupe de positions
            group_players = self.game_data.players_by_group.get(pos_group, [])
            distractors = []
            if len(group_players) > 10:
                others = [p["short_name"] for p in group_players if p["short_name"] != correct_name]
                distractors = image_rng.sample(others, min(3, len(others)))
            else:
                distractors = ["Mbappé", "Haaland", "Vinícius Jr."] # Fallback
            
            options = [correct_name] + distractors
            image_rng.shuffle(options)
            
            self._current_question["options"] = options
            self._current_question["answer"] = correct_name
            self._current_question["question"] = "Qui est ce joueur ?"

        # Reset seed - On évite le time.time() pour rester synchrone sur les images
        # random.seed(time.time()) # SUPPRIMÉ POUR DÉTERMINISME
        
        # SÉCURITÉ : Forcer la mise à jour (Optionnel, load_question le fait déjà)

        print(f"\n[Manche {gs.manche+1}/18] [Q:{gs.question_index+1}] {pos_label} | "
              f"Q: {self._current_question['question'][:50]}...")

        # Déterminer MA couleur en mode ONLINE ou VS_AGENT
        my_color = None
        if gs.mode == GameMode.ONLINE and self._current_match_id and self.current_profile:
            try:
                match_info = self.matchmaking.get_match_info(self._current_match_id)
                my_color = "rouge" if self.current_profile["id"] == match_info["player1_id"] else "bleu"
            except:
                pass
        elif gs.mode == GameMode.VS_AI:
            # En mode VS AI, le joueur humain est toujours rouge, l'IA est bleue
            # On ne veut afficher que le buzzer rouge pour le joueur
            my_color = "rouge"

        # Charger l'écran buzz
        self.buzz_screen.load_question(
            question     = self._current_question,
            manche       = gs.manche,
            position_label = pos_label,
            game_state   = gs,
            my_color     = my_color
        )
        # Ensure side panels default to local team view when online
        if my_color:
            for scr in (self.buzz_screen, self.pick_screen, self.answer_screen):
                try:
                    scr.team_panel.set_local_color(my_color)
                except Exception:
                    pass
        self._show(IDX_BUZZ)

        # Mode ONLINE: Polling pour détecter quand l'autre joueur buzze
        if gs.mode == GameMode.ONLINE and self._current_match_id:
            self._start_opponent_buzz_polling()

        self._start_buzz_timeout()

        # Mode VS_AI : l'agent décide s'il buzze
        if self.ai_player:
            self.ai_player.request_buzz(gs)

    def _start_opponent_buzz_polling(self):
        """En ONLINE: poll toutes les 300ms pour détecter buzz opponent"""
        if self._opponent_buzz_timer:
            self._opponent_buzz_timer.stop()
        
        self._opponent_buzz_timer = QTimer(self)
        self._opponent_buzz_timer.timeout.connect(
            lambda: self._check_if_opponent_buzzed()
        )
        self._opponent_buzz_timer.start(300)
    
    def _check_if_opponent_buzzed(self):
        """Check si l'autre joueur a buzzé cette manche"""
        gs = self.game_state
        try:
            match_state = self.matchmaking.get_match_state(self._current_match_id)

            if match_state and match_state.get("round_number", 0) > gs.question_index + 1 and gs.phase == Phase.BUZZ:
                print("✅ Round avancé côté serveur après skip/annulation, synchronisation locale.")
                self._cancel_buzz_timeout()
                gs.next_manche(success=False)
                self._start_manche()
                return

            if match_state and match_state.get("phase") in ("ANSWER_A", "ANSWER_B") and gs.phase == Phase.BUZZ:
                match_info = self.matchmaking.get_match_info(self._current_match_id)
                active_id = match_state.get("active_player_id")
                if match_info and active_id:
                    answering_color = "rouge" if active_id == match_info.get("player1_id") else "bleu"
                    if self.current_profile and active_id == self.current_profile.get("id"):
                        self._show_answer_screen(answering_color, is_second_chance=(match_state.get("phase") == "ANSWER_B"))
                    else:
                        self._show_spectator_screen(answering_color)
                    return

            buzzes = self.matchmaking.get_all_buzzes_for_round(
                self._current_match_id,
                gs.question_index + 1
            )
            
            # S'il y a un buzz et que c'est pas le mien
            if buzzes:
                for buzz in buzzes:
                    if buzz["player_id"] != self.current_profile["id"]:
                        # L'autre a buzzé!
                        if self._opponent_buzz_timer:
                            self._opponent_buzz_timer.stop()
                            self._opponent_buzz_timer = None
                        print(f"📢 L'AUTRE joueur a buzzé!")
                        
                        # Si MOI je suis pas en train de répondre
                        if not self._answerer_color:
                            # Je vois les choix grisés (spectateur)
                            match_info = self.matchmaking.get_match_info(self._current_match_id)
                            opponent_color = "bleu" if match_info and match_info.get("player1_id") == self.current_profile["id"] else "rouge"
                            if hasattr(self, 'sfx_player'):
                                self.sfx_player.stop()
                                self.sfx_player.play()
                            self._show_spectator_screen(opponent_color)
                        return
        except Exception as e:
            pass  # Continue polling

    # ─────────────────────────────────────────────────────
    # HELPER METHODS - ONLINE MODE
    # ─────────────────────────────────────────────────────
    def _get_opponent_id(self) -> str:
        """Récupère l'ID de l'adversaire en mode ONLINE"""
        if not (self._current_match_id and self.current_profile):
            return None
        try:
            match_info = self.matchmaking.get_match_info(self._current_match_id)
            if not match_info:
                return None
            player1_id = match_info["player1_id"]
            my_id = self.current_profile["id"]
            return match_info["player2_id"] if player1_id == my_id else player1_id
        except:
            return None

    def _show_answer_screen(self, answering_color: str, is_second_chance: bool = False):
        """Affiche l'écran de réponse avec BOUTONS ACTIVÉS"""
        gs = self.game_state
        self._cancel_buzz_timeout()
        is_ai_turn = bool(self.ai_player and answering_color == "bleu")
        
        chance_text = " (2ème chance)" if is_second_chance else ""
        print(f"📋 Écran de réponse{chance_text}: {answering_color} peut cliquer")
        
        self.answer_screen.load(
            question       = self._current_question,
            answering_color = answering_color,
            manche         = gs.manche,
            game_state     = gs,
            is_second_chance = is_second_chance,
            ai_mode        = is_ai_turn
        )
        self.answer_screen.enable_options()
        self._show(IDX_ANSWER)
        if is_ai_turn:
            self.ai_player.request_answer(self._current_question)

    def _show_spectator_screen(self, answering_color: str):
        """Affiche l'écran spectateur: BOUTONS GRISÉS + polling"""
        gs = self.game_state
        self._cancel_buzz_timeout()
        
        # Get opponent name
        try:
            match_info = self.matchmaking.get_match_info(self._current_match_id)
            opponent_nick = match_info.get("player1_nickname") if match_info and match_info["player2_id"] == self.current_profile["id"] else match_info.get("player2_nickname") if match_info else "l'adversaire"
        except:
            opponent_nick = "l'adversaire"
        
        print(f"⏳ Écran spectateur: En attente de {opponent_nick}...")
        
        # Load with grayed buttons
        self.answer_screen.load(
            question       = self._current_question,
            answering_color = answering_color,
            manche         = gs.manche,
            game_state     = gs,
            is_second_chance = False,
            ai_mode        = False
        )
        self.answer_screen.disable_options()
        
        # Show waiting banner
        self.answer_screen.show_status(f"⏳ En attente de {opponent_nick}...", color="#4488ff")
        self._show(IDX_ANSWER)
        
        # Start polling to detect opponent's answer
        self._poll_for_opponent_answer(gs.manche + 1, answering_color)

    def _poll_for_opponent_answer(self, round_number: int, answering_color: str):
        """Polling toutes les 300ms pour détecter la réponse de l'adversaire"""
        # S'assurer qu'on utilise question_index
        gs = self.game_state
        round_number = gs.question_index + 1
        
        if self._poll_opponent_timer:
            self._poll_opponent_timer.stop()
        
        self._poll_opponent_timer = QTimer(self)
        self._poll_opponent_timer.timeout.connect(
            lambda: self._check_opponent_answered(round_number, answering_color)
        )
        self._poll_opponent_timer.start(300)

    def _check_opponent_answered(self, round_number: int, answering_color: str):
        """Vérifie si l'adversaire a répondu (évite doublons)"""
        try:
            # SÉCURITÉ : Vérifier si le Master a déjà avancé au round suivant
            match_state = self.matchmaking.get_match_state(self._current_match_id)
            if match_state and match_state.get("round_number") > round_number:
                print(f"✅ [SLAVE] Master a déjà avancé au round {match_state.get('round_number')}")
                if self._poll_opponent_timer:
                    self._poll_opponent_timer.stop()
                    self._poll_opponent_timer = None
                self._after_manche() # Détectera success=False car winner_manche est None
                return

            answers = self.matchmaking.get_round_answers(self._current_match_id, round_number)
            
            # Check if opponent answered
            for answer in answers:
                if answer["player_id"] != self.current_profile["id"]:
                    # Opponent answered - mais CHECK si c'est UNE NOUVELLE réponse
                    if answer["id"] == self._last_opponent_answer_id:
                        # Déjà traité, ignorer
                        return
                    
                    # ✅ Nouvelle réponse!
                    self._last_opponent_answer_id = answer["id"]
                    
                    if self._poll_opponent_timer:
                        self._poll_opponent_timer.stop()
                        self._poll_opponent_timer = None
                    print(f"⚔️ {answering_color} a répondu: {answer['chosen_answer']}")
                    
                    try:
                        match_info = self.matchmaking.get_match_info(self._current_match_id)
                        opponent_nick = match_info.get("player1_nickname") if answer["player_id"] == match_info["player1_id"] else match_info.get("player2_nickname")
                    except:
                        opponent_nick = "Adversaire"
                    
                    self.answer_screen.show_opponent_answer(
                        answer['chosen_answer'],
                        opponent_nick,
                        answering_color
                    )
                    # Auto-advance after showing
                    QTimer.singleShot(2000, self._after_opponent_answered)
                    return
        except Exception as e:
            pass  # Continue polling on error

    def _after_opponent_answered(self):
        """Logique après que l'adversaire a répondu"""
        # STOP polling immédiatement
        if self._poll_opponent_timer:
            self._poll_opponent_timer.stop()
            self._poll_opponent_timer = None
        
        gs = self.game_state
        # Récupérer la réponse enregistrée
        answers = self.matchmaking.get_round_answers(self._current_match_id, gs.question_index + 1)
        
        # Trouver la réponse de l'adversaire
        opponent_answer = None
        for answer in answers:
            if answer["player_id"] != self.current_profile["id"]:
                opponent_answer = answer
                break
        
        if opponent_answer:
            opponent_color = "rouge" if opponent_answer["player_id"] == self.matchmaking.get_match_info(self._current_match_id)["player1_id"] else "bleu"
            
            if opponent_answer["is_correct"]:
                # ✅ L'adversaire a RÉUSSI → Afficher PICK aux deux joueurs
                print(f"✅ L'adversaire a réussi! Passage au PICK...")
                QTimer.singleShot(1000, self._go_to_pick)
            else:
                # Opponent échoue. Est-ce le premier échec du round ?
                my_answer = next((a for a in answers if a["player_id"] == self.current_profile["id"]), None)
                
                if not my_answer:
                    # Je n'ai pas encore répondu, donc c'est le 1er échec du round
                    print(f"❌ L'adversaire a échoué son essai → À mon tour!")
                    QTimer.singleShot(1500, lambda: self._show_second_chance_to_other(opponent_color))
                else:
                    # J'avais déjà répondu et échoué, et l'autre aussi → Question finie
                    print(f"❌ Les deux joueurs ont échoué → Question finie")
                    QTimer.singleShot(2000, lambda: self._after_manche(force_success=False))

    # ─────────────────────────────────────────────────────
    # BUZZ
    # ─────────────────────────────────────────────────────
    def _on_buzzed(self, color: str):
        gs = self.game_state
        self._cancel_buzz_timeout()
        if self.ai_player:
            self.ai_player.cancel_buzz()
        
        # STOP le buzz polling immédiatement
        if self._opponent_buzz_timer:
            self._opponent_buzz_timer.stop()
            self._opponent_buzz_timer = None
        
        print(f"[BUZZ] {color} a buzzé localement")
        
        if hasattr(self, 'sfx_player'):
            self.sfx_player.stop()
            self.sfx_player.play()

        if gs.mode == GameMode.ONLINE and self._current_match_id and self.current_profile:
            buzzer_id = self.current_profile["id"]
            
            # Enregistrer ce buzz IMMÉDIATEMENT
            try:
                self.matchmaking.register_buzz(
                    self._current_match_id,
                    buzzer_id,
                    gs.question_index + 1
                )
                print(f"📢 Buzz LOCAL enregistré sur Supabase")
            except Exception as e:
                print(f"❌ Erreur enregistrement buzz: {e}")
            
            # ✅ Attendre un court instant pour voir qui a buzzé en premier sur le serveur
            # pour une synchronisation parfaite à distance (Maroc <-> USA)
            QTimer.singleShot(400, lambda: self._resolve_buzzer_winner(color))
        
        else:
            # Mode LOCAL
            gs.on_buzz(color)
            self._answerer_color = color
            self._show_answer_screen(color, is_second_chance=False)


    def _resolve_buzzer_winner(self, my_color: str):
        """Vérifie dans Supabase qui a réellement buzzé en premier"""
        gs = self.game_state
        if not (gs.mode == GameMode.ONLINE and self._current_match_id):
            return

        try:
            first_buzz = self.matchmaking.get_first_buzz(self._current_match_id, gs.question_index + 1)
            if first_buzz:
                first_id = first_buzz["player_id"]
                my_id = self.current_profile["id"]

                if first_id == my_id:
                    # ✅ J'AI GAGNÉ LE BUZZ
                    print(f"🏆 J'ai gagné le buzz (confirmé serveur)")
                    gs.on_buzz(my_color)
                    self._answerer_color = my_color
                    self._show_answer_screen(my_color, is_second_chance=False)
                    # Informer le match_state du buzzer actif
                    self.matchmaking.update_match_phase(self._current_match_id, "ANSWER_A", active_player_id=my_id)
                else:
                    # ⏳ L'AUTRE A GAGNÉ
                    print(f"⏳ L'autre a buzzé avant moi (confirmé serveur)")
                    other_color = "bleu" if my_color == "rouge" else "rouge"
                    self._show_spectator_screen(other_color)
            else:
                # Fallback: si pas de buzz trouvé (devrait pas arriver), utiliser le mien
                gs.on_buzz(my_color)
                self._answerer_color = my_color
                self._show_answer_screen(my_color, is_second_chance=False)
        except Exception as e:
            print(f"❌ Erreur résolution buzzer: {e}")
            # Fallback local
            gs.on_buzz(my_color)
            self._answerer_color = my_color
            self._show_answer_screen(my_color, is_second_chance=False)

    def _start_buzz_polling(self, my_color: str):
        """Poll pour détecter si l'autre joueur a aussi buzzé (ONLINE mode)"""
        if self._opponent_buzz_timer:
            self._opponent_buzz_timer.stop()
        
        self._opponent_buzz_timer = QTimer(self)
        self._opponent_buzz_timer.timeout.connect(
            lambda: self._check_opponent_also_buzzed(my_color)
        )
        self._opponent_buzz_timer.start(500)
    
    def _check_opponent_also_buzzed(self, my_color: str):
        """Vérifie si l'autre joueur a aussi buzzé (pour info seulement)"""
        try:
            buzzes = self.matchmaking.get_all_buzzes_for_round(
                self._current_match_id,
                self.game_state.question_index + 1
            )
            
            # Si 2 buzzes trouvés, l'autre a aussi buzzé
            if buzzes and len(buzzes) >= 2:
                if self._opponent_buzz_timer:
                    self._opponent_buzz_timer.stop()
                    self._opponent_buzz_timer = None
                print(f"ℹ️ L'autre joueur a aussi buzzé")
                # Pas besoin de changer l'affichage
        except Exception as e:
            pass  # Continue polling

    # ─────────────────────────────────────────────────────
    # RÉPONSE
    # ─────────────────────────────────────────────────────
    def _on_answer_selected(self, chosen: str):
        gs           = self.game_state
        if not gs: return
        
        self._cancel_buzz_timeout()
        # Chercher la réponse correcte (support "answer" des questions statiques ET "correct_answer" de Supabase)
        correct      = self._current_question.get("answer") or self._current_question.get("correct_answer", "")
        is_correct   = (chosen.strip() == correct.strip())
        answering    = gs.buzzer
        is_ai        = bool(self.ai_player and answering == "bleu")

        self.answer_screen.disable_options()

        # Mode ONLINE: Enregistrer la réponse
        if gs.mode == GameMode.ONLINE and self._current_match_id and self.current_profile:
            try:
                score_gained = 10 if is_correct else 0
                saved = self.matchmaking.register_answer(
                    self._current_match_id,
                    self.current_profile["id"],
                    gs.question_index + 1,
                    chosen,
                    is_correct,
                    score_gained
                )
                if saved:
                    print(f"📝 Réponse enregistrée: {chosen} (correct: {is_correct})")
            except Exception as e:
                print(f"❌ Erreur enregistrement réponse: {e}")

        if is_correct:
            # ✅ BONNE RÉPONSE → MANCHE SUIVANTE
            self.answer_screen.highlight_correct(correct)
            msg = f"✅  Bonne réponse ! {gs.get_team(answering).name} choisit son joueur."
            self.answer_screen.show_status(msg, color="#00e676")
            gs.on_correct_answer()
            print(f"[ANSWER] ✅ Correct!")
            
            # Ensuite: Go to PICK (joueur choisit un joueur à attribuer)
            QTimer.singleShot(2000, self._go_to_pick)
        
        elif gs.phase == Phase.ANSWER_A or gs.phase == Phase.ANSWER_B:
            # ❌ MAUVAISE RÉPONSE → VÉRIFIER 2ème CHANCE
            # SI c'est la première erreur (ANSWER_A), on ne montre pas la bonne réponse (show_correct=False)
            show_corr = (gs.phase == Phase.ANSWER_B)
            self.answer_screen.highlight_wrong(chosen, correct, show_correct=show_corr)
            
            if gs.mode == GameMode.ONLINE and self._current_match_id:
                if gs.phase == Phase.ANSWER_A:
                    # Premier échec → donner la chance à l'autre
                    self._show_second_chance_to_other(answering)
                else:
                    # Deuxième échec (en ANSWER_B) → manche finie
                    print(f"❌ Deuxième échec → Question finie pour les deux")
                    self.answer_screen.show_status("❌  Mauvaise réponse — Question annulée.", color=COLOR_ROUGE_STR)
                    gs.on_wrong_answer_second()
                    # Mettre à jour phase en BD pour synchroniser la fin
                    self.matchmaking.update_match_phase(self._current_match_id, "BUZZ")
                    QTimer.singleShot(2000, self._after_manche)
            else:
                # Mode LOCAL/IA
                if gs.phase == Phase.ANSWER_A:
                    got_red = gs.on_wrong_answer_first()
                    team = gs.get_team(answering)
                    msg = f"❌  Mauvaise réponse — Carton jaune pour {team.name}!"
                    if got_red: msg += " 🟥 CARTON ROUGE!"
                    self.answer_screen.show_status(msg, color=COLOR_ROUGE_STR)
                    other = "bleu" if answering == "rouge" else "rouge"
                    QTimer.singleShot(1500, lambda: self._second_chance(other))
                else:
                    self.answer_screen.show_status("❌  Mauvaise réponse — Question annulée.", color=COLOR_ROUGE_STR)
                    gs.on_wrong_answer_second()
                    QTimer.singleShot(2000, lambda: self._after_manche(force_success=False))
        
        elif gs.phase == Phase.SECOND_CHANCE_A or gs.phase == Phase.SECOND_CHANCE_B:
            # ❌ ÉCHOUE À LA 2ème CHANCE
            self.answer_screen.highlight_wrong(chosen, correct)
            
            # En ONLINE: Si SECOND_CHANCE_A échoue → l'autre joueur peut répondre (ANSWER_B)
            # Si SECOND_CHANCE_B échoue → c'est fini
            if gs.mode == GameMode.ONLINE and self._current_match_id:
                if gs.phase == Phase.SECOND_CHANCE_A:
                    # SECOND_CHANCE_A échoue → Passer à ANSWER_B (l'autre peut répondre)
                    print(f"❌ Joueur 1 échoue 2ème chance → Joueur 2 peut répondre")
                    self.answer_screen.show_status(
                        "❌  Mauvaise réponse — L'autre joueur peut répondre!",
                        color=COLOR_ROUGE_STR
                    )
                    # Mettre à jour la phase en BD
                    self.matchmaking.update_match_phase(self._current_match_id, "ANSWER_B")
                    # Passer à l'écran spectateur en attente de réponse du joueur 2
                    other_color = "bleu" if answering == "rouge" else "rouge"
                    QTimer.singleShot(2000, lambda: self._show_spectator_screen(other_color))
                else:
                    # SECOND_CHANCE_B échoue → fin de la question
                    print(f"❌ Joueur 2 échoue aussi 2ème chance → Question finie")
                    self.answer_screen.show_status(
                        "❌  Mauvaise réponse — Question annulée.",
                        color=COLOR_ROUGE_STR
                    )
                    gs.on_wrong_answer_second()
                    QTimer.singleShot(2000, lambda: self._after_manche(force_success=False))
            else:
                # Mode LOCAL
                self.answer_screen.show_status(
                    "❌  Mauvaise réponse — Question annulée.",
                    color=COLOR_ROUGE_STR
                )
                gs.on_wrong_answer_second()
                QTimer.singleShot(2000, lambda: self._after_manche(force_success=False))

    def _show_second_chance_to_other(self, first_answerer_color: str):
        """Affiche la chance de répondre à l'AUTRE joueur"""
        # STOP les anciens timers immédiatement
        if self._poll_opponent_timer:
            self._poll_opponent_timer.stop()
            self._poll_opponent_timer = None
        if self._opponent_buzz_timer:
            self._opponent_buzz_timer.stop()
            self._opponent_buzz_timer = None
        
        gs = self.game_state
        
        # Le premier a échoué (donner carton jaune etc.)
        got_red = gs.on_wrong_answer_first()
        
        my_id = self.current_profile["id"]
        match_info = self.matchmaking.get_match_info(self._current_match_id)
        player1_id = match_info["player1_id"]
        
        # Qui est l'autre joueur ?
        first_answerer_id = player1_id if first_answerer_color == "rouge" else match_info["player2_id"]
        other_color = "bleu" if first_answerer_color == "rouge" else "rouge"
        
        print(f"[DEBUG] _show_second_chance_to_other: first_answerer={first_answerer_color}, other={other_color}")
        
        # Suis-je l'autre joueur ?
        if my_id != first_answerer_id:
            # C'EST À MON TOUR DE RÉPONDRE !
            print(f"🎯 C'est à TON tour de répondre (l'autre s'est trompé)!")
            gs.phase = Phase.ANSWER_B
            gs.buzzer = other_color # Indiquer que c'est moi qui répond maintenant
            
            # Réactiver les boutons
            self.answer_screen.load(
                question        = self._current_question,
                answering_color = other_color,
                manche          = gs.manche,
                game_state      = gs,
                is_second_chance = True, # Afficher le badge 2ème chance
                ai_mode         = False
            )
            self.answer_screen.enable_options()
            
            # Afficher le message
            msg = f"🎯  L'autre s'est trompé ! À ton tour !"
            self.answer_screen.show_status(msg, color="#ffc107")
            
            # Mettre à jour la phase en BD
            self.matchmaking.update_match_phase(self._current_match_id, "ANSWER_B", active_player_id=my_id)
        else:
            # J'AI ÉCHOUÉ → Je deviens spectateur
            print(f"⏳ J'ai échoué, attente de la réponse de l'autre...")
            self._show_spectator_screen(other_color)

    def _on_timer_expired(self):
        """Temps écoulé — traiter comme mauvaise réponse"""
        gs = self.game_state
        if not gs: return
        
        self.answer_screen.disable_options()

        if gs.phase == Phase.ANSWER_A:
            got_red = gs.on_wrong_answer_first()
            self.answer_screen.show_status(
                "⏱️  Temps écoulé ! Carton jaune.",
                color="#ffc107"
            )
            other = "bleu" if gs.buzzer == "rouge" else "rouge"
            QTimer.singleShot(1500, lambda: self._second_chance(other))
        else:
            self.answer_screen.show_status(
                "⏱️  Temps écoulé — Question annulée.",
                color="#ffc107"
            )
            gs.on_wrong_answer_second()
            QTimer.singleShot(1500, lambda: self._after_manche(force_success=False))

    def _second_chance(self, other_color: str):
        """Affiche la 2ème chance pour l'équipe adverse"""
        gs = self.game_state
        gs.buzzer = other_color   # Mettre à jour qui répond
        is_ai_turn = bool(self.ai_player and other_color == "bleu")
        self.answer_screen.load(
            question        = self._current_question,
            answering_color = other_color,
            manche          = gs.manche,
            game_state      = gs,
            is_second_chance = True,
            ai_mode         = is_ai_turn
        )
        self._show(IDX_ANSWER)

        # Mode VS_AI : si c'est l'agent qui a la 2ème chance
        if is_ai_turn:
            self.ai_player.request_answer(self._current_question)


    # ─────────────────────────────────────────────────────
    # PICK
    # ─────────────────────────────────────────────────────
    def _go_to_pick(self):
        gs = self.game_state
        if not gs or not hasattr(gs, 'current_players') or len(gs.current_players) < 2:
            print("[ERROR] Pas assez de joueurs pour le PICK")
            return
        p1, p2 = gs.current_players
        chooser = gs.winner_manche
        is_ai_turn = bool(self.ai_player and chooser == "bleu")

        # 🛑 STOP tous les timers de polling avant de continuer
        if self._poll_opponent_timer:
            self._poll_opponent_timer.stop()
            self._poll_opponent_timer = None
        if self._opponent_buzz_timer:
            self._opponent_buzz_timer.stop()
            self._opponent_buzz_timer = None

        # 📋 Mode ONLINE: Mettre à jour match_state pour signaler le PICK
        is_me_chooser = False
        if gs.mode == GameMode.ONLINE and self._current_match_id:
            self.matchmaking.update_match_phase(self._current_match_id, "PICK")
            # Vérifier si je suis le chooser
            try:
                match_info = self.matchmaking.get_match_info(self._current_match_id)
                my_id = self.current_profile["id"]
                is_me_chooser = (chooser == "rouge" and my_id == match_info["player1_id"]) or \
                               (chooser == "bleu" and my_id == match_info["player2_id"])
                
                # ✅ BLOQUER L'INTERFACE SI ON N'EST PAS LE CHOOSER
                self.pick_screen.set_spectator_mode(not is_me_chooser)
            except Exception as e:
                print(f"[DEBUG] Erreur chooser check: {e}")

        self.pick_screen.load(
            player1       = p1,
            player2       = p2,
            chooser_color = chooser,
            manche        = gs.manche,
            game_state    = gs,
            ai_mode       = is_ai_turn
        )
        self._show(IDX_PICK)

        # Mode VS_AI : si c'est l'agent qui choisit
        if is_ai_turn:
            self.ai_player.request_pick(p1, p2, gs)
        elif gs.mode == GameMode.ONLINE and not is_me_chooser:
            # Je suis spectateur → poll jusqu'à que le chooser fasse son choix
            self._poll_for_pick_completion()

    def _on_player_picked(self, index: int):
        gs = self.game_state
        # Reveal the two candidate players immediately for both sides
        p1, p2 = gs.current_players
        try:
            p1.reveal()
            p2.reveal()
        except Exception:
            pass

        # Apply the pick (placement) to the teams
        gs.on_pick_player(index)
        # Update UI to show revealed ratings
        try:
            self.pick_screen.update_teams(gs)
        except Exception:
            pass
        print(f"[PICK] Joueur {index+1} choisi — "
              f"Rouge: {len(gs.team_rouge.players)} joueurs | "
              f"Bleu: {len(gs.team_bleu.players)} joueurs")
        
        # Mode ONLINE: enregistrer le choix, puis attendre que spectateur l'applique aussi
        if gs.mode == GameMode.ONLINE and self._current_match_id:
            # 1. Enregistrer le pick index en BD
            self.matchmaking.store_pick_choice(self._current_match_id, index)
            # 2. Mettre à jour phase à "PICK_DONE" (signal au spectateur)
            self.matchmaking.update_match_phase(self._current_match_id, "BUZZ")
            # 3. ATTENDRE que spectateur ait appliqué le pick aussi!
            # → poll jusqu'à ce qu'on détecte que spectateur a avancé aussi ou timeout
            QTimer.singleShot(1500, self._wait_for_spectator_pick_readiness)
        else:
            # Local mode: go directly
            self._after_manche(force_success=True)
    
    def _wait_for_spectator_pick_readiness(self):
        """Attendre que spectateur soit prêt avant de passer à manche suivante"""
        # Petit délai pour laisser au spectateur le temps d'appliquer le pick
        QTimer.singleShot(1000, lambda: self._after_manche(force_success=True))

    def _poll_for_pick_completion(self):
        """Poll jusqu'à ce que le chooser finisse sa sélection"""
        if self._poll_opponent_timer:
            self._poll_opponent_timer.stop()
        
        self._poll_opponent_timer = QTimer(self)
        self._poll_opponent_timer.timeout.connect(self._check_pick_completed)
        self._poll_opponent_timer.start(300)
    
    def _check_pick_completed(self):
        """Vérifie si le chooser a fini de choisir"""
        try:
            match_state = self.matchmaking.get_match_state(self._current_match_id)
            if match_state and match_state.get("phase") == "BUZZ":
                # Le picker a choisi et la phase est revenue à BUZZ!
                if self._poll_opponent_timer:
                    self._poll_opponent_timer.stop()
                    self._poll_opponent_timer = None
                
                # ✅ APPLIQUER LE MÊME PICK AU SPECTATEUR AUSSI!
                gs = self.game_state
                pick_index = match_state.get("pick_index")
                if pick_index is not None:
                    # Reveal candidates then apply the pick so spectator sees ratings
                    try:
                        sp1, sp2 = gs.current_players
                        sp1.reveal(); sp2.reveal()
                    except Exception:
                        pass

                    gs.on_pick_player(pick_index)
                    try:
                        self.pick_screen.update_teams(gs)
                    except Exception:
                        pass
                    print(f"✅ Spectateur applique le pick: index {pick_index}")
                    print(f"   Rouge: {len(gs.team_rouge.players)} joueurs | Bleu: {len(gs.team_bleu.players)} joueurs")
                
                print(f"✅ Le joueur a fini de choisir, passage à la manche suivante")
                QTimer.singleShot(500, lambda: self._after_manche(force_success=True))
        except:
            pass  # Continue polling

    # ─────────────────────────────────────────────────────
    # APRÈS CHAQUE MANCHE
    # ─────────────────────────────────────────────────────
    def _after_manche(self, force_success: bool = None, sync_online: bool = True):
        gs = self.game_state
        if not gs: return

        self._skip_pending_color = None
        self._cancel_buzz_timeout()

        # ✅ Déterminer si la manche a été RÉUSSIE (quelqu'un a gagné) ou ANNULÉE
        # Si force_success est fourni, on l'utilise (cas du Slave qui suit le Master)
        if force_success is not None:
            success = force_success
        else:
            success = (gs.winner_manche is not None)
        
        if not success:
            print(f"❌ Manche ANNULÉE (aucun gagnant) — On reste sur le slot {gs.manche + 1}")
        else:
            print(f"✅ Manche RÉUSSIE — Passage au slot suivant")

        # ✅ Passer à l'état suivant (incrémente question_index TOUJOURS, manche SEULEMENT SI success)
        gs.next_manche(success=success)
        
        # 📋 Mode ONLINE: Synchronisation
        if sync_online and gs.mode == GameMode.ONLINE and self._current_match_id:
            try:
                match_info = self.matchmaking.get_match_info(self._current_match_id)
                is_player1 = (self.current_profile["id"] == match_info["player1_id"])
                
                if is_player1:
                    # Master (P1) : Générer et sauver la question SI BESOIN avant d'incrémenter le round en BD
                    while len(self.questions) <= gs.question_index:
                        print(f"🆕 [MASTER] Génération question supplémentaire pour index {gs.question_index}")
                        new_q = self._generate_single_question(gs.current_round, gs.manche)
                        self.questions.append(new_q)
                        self.matchmaking.save_single_question(self._current_match_id, gs.question_index + 1, new_q)
                    
                    # Maintenant on peut signaler le nouveau round
                    new_phase = gs.phase.name
                    self.matchmaking.update_match_round(self._current_match_id, gs.question_index + 1)
                    self.matchmaking.update_match_phase(self._current_match_id, new_phase)
                else:
                    # Slave (P2) : attend que le Master mette à jour l'état
                    print(f"⏳ [SLAVE] Attente de la question {gs.question_index + 1}...")
                    self._poll_for_next_round(gs.question_index + 1)
                    return
            except Exception as e:
                print(f"❌ Erreur sync after_manche: {e}")
        
        # Transition locale (Master ou Local/Solo/AI)
        if gs.phase == Phase.EXCHANGE:
            print("[EXCHANGE] Phase d'échanges (cartons rouges)")
            if self.ai_player:
                self._handle_ai_exchanges()
            else:
                self.exchange_screen.load(gs)
                self._show(IDX_EXCHANGE)
        elif gs.phase == Phase.REVEAL:
            print("[REVEAL] Révélation finale")
            self._start_reveal()
        else:
            # Prochaine manche standard
            self._start_manche()


    def _on_formation_done(self):
        """Redondant - à supprimer si besoin, gardé pour compatibilité court terme"""
        if self.game_state:
            self._start_manche()

    def _poll_for_next_round(self, next_round_num: int):
        """Poll jusqu'à ce que le master ait incrémenté le round_number"""
        if self._poll_opponent_timer:
            self._poll_opponent_timer.stop()
        
        self._poll_opponent_timer = QTimer(self)
        self._poll_opponent_timer.timeout.connect(lambda: self._check_round_ready(next_round_num))
        self._poll_opponent_timer.start(500)

    def _check_round_ready(self, next_round_num: int):
        try:
            match_state = self.matchmaking.get_match_state(self._current_match_id)
            if match_state and match_state.get("round_number") == next_round_num:
                if self._poll_opponent_timer:
                    self._poll_opponent_timer.stop()
                    self._poll_opponent_timer = None
                
                print(f"✅ [SLAVE] Manche {next_round_num} prête!")
                gs = self.game_state
                
                print(f"[STATE] Phase={gs.phase.name} | Manche={gs.manche}")

                if gs.phase == Phase.EXCHANGE:
                    print("[EXCHANGE] Début de la phase d'échange")
                    if self.ai_player:
                        self._handle_ai_exchanges()
                    else:
                        self.exchange_screen.load(gs)
                        self._show(IDX_EXCHANGE)
                elif gs.phase == Phase.REVEAL:
                    print("[REVEAL] Révélation finale")
                    self._start_reveal()
                else:
                    # Prochaine manche
                    self._start_manche()
        except Exception as e:
            print(f"❌ Erreur check_round_ready: {e}")

    # ─────────────────────────────────────────────────────
    # ÉCHANGE
    # ─────────────────────────────────────────────────────
    def _on_exchanges_done(self):
        """Legacy — utilisé uniquement par le flux AI via _handle_ai_exchanges"""
        print("[EXCHANGE] Échanges AI terminés — passage à la révélation")
        self.exchange_screen._start_reveal_phase()

    def _handle_ai_exchanges(self):
        """
        Gère les échanges en mode VS_AI :
        - Rouge pénalisé → l'IA (bleu) choisit automatiquement
        - Bleu pénalisé → l'humain (rouge) choisit via l'écran d'échange
        """
        gs = self.game_state
        agent = self.ai_player.agent

        # 1) Échanges automatiques (rouge pénalisé, IA est adversaire)
        for _ in range(gs.team_rouge.rouges):
            penalized = gs.team_rouge
            adversary = gs.team_bleu
            if penalized.players and adversary.players:
                taken = agent.choose_exchange_take(penalized.players, 1)
                given = agent.choose_exchange_give(adversary.players, 1)
                if taken and given:
                    taken_p = taken[0]
                    given_p = given[0]
                    
                    if taken_p in penalized.players and given_p in adversary.players:
                        # 1. Penalized -> Adversary
                        penalized.players.remove(taken_p)
                        if taken_p in penalized.formation.get("BENCH", []):
                            penalized.formation["BENCH"].remove(taken_p)
                        else:
                            for pos, p in penalized.formation.items():
                                if p == taken_p:
                                    penalized.formation[pos] = None
                                    break
                        adversary.players.append(taken_p)
                        taken_p.pitch_pos = None
                        adversary.formation["BENCH"].append(taken_p)
                        
                        # 2. Adversary -> Penalized
                        adversary.players.remove(given_p)
                        if given_p in adversary.formation.get("BENCH", []):
                            adversary.formation["BENCH"].remove(given_p)
                        else:
                            for pos, p in adversary.formation.items():
                                if p == given_p:
                                    adversary.formation[pos] = None
                                    break
                        penalized.players.append(given_p)
                        given_p.pitch_pos = None
                        penalized.formation["BENCH"].append(given_p)
                        
                        print(f"[AI EXCHANGE] IA prend {taken_p.name}, donne {given_p.name}")

        # 2) Échanges humains (bleu pénalisé, humain est adversaire)
        if gs.team_bleu.rouges > 0:
            queue = ["bleu"] * gs.team_bleu.rouges
            self.exchange_screen.load(gs, exchange_queue=queue)
            self._show(IDX_EXCHANGE)
        else:
            # Pas d'échanges humains — aller directement à l'écran final
            self._persist_match_history()
            self.exchange_screen.load(gs)
            self._show(IDX_EXCHANGE)

    # ─────────────────────────────────────────────────────
    # AGENT IA — Callbacks
    # ─────────────────────────────────────────────────────
    def _on_ai_buzz(self):
        """L'agent IA a décidé de buzzer"""
        if self.game_state and self.game_state.phase == Phase.BUZZ:
            self.buzz_screen.force_buzz("bleu")

    def _on_ai_answer(self, answer_text: str):
        """L'agent IA a choisi une réponse"""
        if not self.game_state:
            return
        if self.game_state.phase not in (Phase.ANSWER_A, Phase.ANSWER_B):
            return
        # Trouver l'index de l'option choisie
        for i, opt in enumerate(self.answer_screen._options):
            if opt == answer_text:
                self.answer_screen.force_answer(i)
                return

    def _on_ai_pick(self, index: int):
        """L'agent IA a choisi un joueur"""
        if self.game_state and self.game_state.phase == Phase.PICK:
            self.pick_screen.force_pick(index)

    def _on_ai_skip(self):
        """Skip désactivé — l'IA ne peut plus passer de question"""
        pass  # Fonctionnalité skip supprimée

    # ─────────────────────────────────────────────────────
    # RÉVÉLATION
    # ─────────────────────────────────────────────────────
    def _start_reveal(self):
        """Charge l'écran final unifié (échange + révélation + score)"""
        self._persist_match_history()
        self.exchange_screen.load(self.game_state)
        self._show(IDX_EXCHANGE)

    def _persist_match_history(self):
        if self._score_saved:
            return
        if not self.supabase.is_ready or not self.current_profile:
            return
        if not self.game_state or not self.current_profile.get("id"):
            return

        gs = self.game_state
        winner = gs.get_winner() or "egalite"

        try:
            self.supabase.save_match_score(
                user_id=self.current_profile["id"],
                mode=gs.mode.value,
                team_rouge_name=gs.team_rouge.name,
                team_bleu_name=gs.team_bleu.name,
                team_rouge_score=gs.team_rouge.total_rating,
                team_bleu_score=gs.team_bleu.total_rating,
                winner=winner,
            )
            self._score_saved = True
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Historique non sauvegarde",
                f"Impossible d'enregistrer le score dans Supabase:\n{exc}",
            )

    def _build_questions(self) -> list[dict]:
        """Génère dynamiquement les 18 questions du match via l'API Mistral"""
        print("[GAME] Génération de la liste des questions (API Mistral)...")
        if not self.question_generator:
            from services.question_generator import DynamicQuestionGenerator
            self.question_generator = DynamicQuestionGenerator()
            
        questions = self.question_generator.generate_full_match_questions()
        return questions

    def _generate_single_question(self, round_type: RoundType, manche_idx: int) -> dict:
        """Génère une seule question selon le round actuel via Mistral (fallback/remplacement dynamique)"""
        import random
        from game.questions_static import ROUND_1_DEFENSEURS, ROUND_2_MILIEUX, ROUND_3_ATTAQUANTS, ROUND_4_GARDIEN
        
        if not self.question_generator:
            from services.question_generator import DynamicQuestionGenerator
            self.question_generator = DynamicQuestionGenerator()
            
        try:
            if round_type == RoundType.DEFENDERS:
                themes = ["Coupe du Monde", "Ligue des Champions", "Ballon d'Or", "Légendes du foot"]
                q = self.question_generator.generate_trivia_question("medium", random.choice(themes))
                if q: return q
            elif round_type == RoundType.MIDFIELDERS:
                themes = ["Célébration mythique", "But en finale", "Exploit technique", "Moment insolite"]
                q = self.question_generator.generate_iconic_moment_question(random.choice(themes))
                if q: return q
            elif round_type == RoundType.ATTACKERS:
                players = ["Cristiano Ronaldo", "Zlatan Ibrahimović", "Neymar", "Luis Suarez", "Ronaldo R9", "Ronaldinho", "Thierry Henry"]
                q = self.question_generator.generate_transfer_question(random.choice(players))
                if q: return q
            else:
                themes = ["Vainqueur de la Coupe du Monde", "Légende du 20ème siècle", "Légende de Premier League"]
                q = self.question_generator.generate_who_am_i(random.choice(themes))
                if q: return q
        except Exception as e:
            print(f"❌ Erreur Mistral Single Question: {e}")
            
        # Fallback de secours statique
        seed_int = seed_from_parts(self._match_seed, round_type.value, manche_idx, self._current_match_id or "local")
        local_random = random.Random(seed_int)

        if round_type == RoundType.DEFENDERS:
            return local_random.choice(ROUND_1_DEFENSEURS)
        elif round_type == RoundType.MIDFIELDERS:
            return local_random.choice(ROUND_2_MILIEUX)
        elif round_type == RoundType.ATTACKERS:
            return local_random.choice(ROUND_3_ATTAQUANTS)
        else:
            return local_random.choice(ROUND_4_GARDIEN)

    def _start_buzz_timeout(self):
        # Désactivé pour empêcher le skip automatique de la question
        pass

    def _cancel_buzz_timeout(self):
        pass

    def _on_buzz_timeout(self):
        pass



# Constante manquante importée ici pour éviter import circulaire
COLOR_ROUGE_STR = "#ff4444"


# ─────────────────────────────────────────────────────────
# LANCEMENT
# ─────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Ahsan Khota")
    app.setStyle("Fusion")

    window = AhsanKhotaApp()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
