#!/usr/bin/env python3
# ============================================================
# main.py — Contrôleur principal Ahsan Khota — Phase 2
# ============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PyQt5.QtCore    import Qt, QTimer

from config          import APP_TITLE, APP_WIDTH, APP_HEIGHT, TOTAL_MANCHES
from ui.styles       import STYLE_APP
from ui.intro_screen   import IntroScreen
from ui.buzz_screen    import BuzzScreen
from ui.answer_screen  import AnswerScreen
from ui.pick_screen    import PickScreen
from ui.exchange_screen import ExchangeScreen
from ui.reveal_screen  import RevealScreen
from ui.difficulty_screen import DifficultyScreen
from game.data  import GameData
from game.state import GameState, GameMode, Phase, TeamState
from game.questions_static import get_questions
from ai.agent       import QLearningAgent
from ai.integration import AIPlayer

# ── Index des écrans dans le QStackedWidget ───────────────
IDX_INTRO      = 0
IDX_BUZZ       = 1
IDX_ANSWER     = 2
IDX_PICK       = 3
IDX_EXCHANGE   = 4
IDX_REVEAL     = 5
IDX_DIFFICULTY = 6


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
        self.game_data  = None
        self.game_state = None
        self.questions  = []
        self._current_question = {}
        self.ai_player  = None          # AIPlayer (mode VS_AI uniquement)
        self._pending_start = None      # tuple en attente pour VS_AI

        self._load_data()
        self._setup_window()
        self._setup_screens()
        self._connect_signals()

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

        self.intro_screen    = IntroScreen()
        self.buzz_screen     = BuzzScreen()
        self.answer_screen   = AnswerScreen()
        self.pick_screen     = PickScreen()
        self.exchange_screen = ExchangeScreen()
        self.reveal_screen   = RevealScreen()
        self.difficulty_screen = DifficultyScreen()

        self.stack.addWidget(self.intro_screen)      # 0
        self.stack.addWidget(self.buzz_screen)       # 1
        self.stack.addWidget(self.answer_screen)     # 2
        self.stack.addWidget(self.pick_screen)       # 3
        self.stack.addWidget(self.exchange_screen)   # 4
        self.stack.addWidget(self.reveal_screen)     # 5
        self.stack.addWidget(self.difficulty_screen) # 6

        self.stack.setCurrentIndex(IDX_INTRO)

    def _connect_signals(self):
        # Intro → démarrage
        self.intro_screen.game_start.connect(self._on_game_start)

        # Buzz → réponse
        self.buzz_screen.buzzed.connect(self._on_buzzed)

        # Réponse → résultat
        self.answer_screen.answer_selected.connect(self._on_answer_selected)
        self.answer_screen.timer_expired.connect(self._on_timer_expired)

        # Pick → joueur choisi
        self.pick_screen.player_picked.connect(self._on_player_picked)

        # Échange → terminé
        self.exchange_screen.exchanges_done.connect(self._on_exchanges_done)

        # Reveal → rejouer
        self.reveal_screen.play_again.connect(self._back_to_intro)

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

    def _back_to_intro(self):
        self.game_state = None
        if self.ai_player:
            self.ai_player.cancel_all()
            self.ai_player = None
        self._pending_start = None
        self._show(IDX_INTRO)

    # ─────────────────────────────────────────────────────
    # DÉMARRAGE D'UNE PARTIE
    # ─────────────────────────────────────────────────────
    def _on_game_start(self, mode_str: str, nom_rouge: str, nom_bleu: str):
        mode = GameMode(mode_str)

        # Mode VS_AI → écran de difficulté d'abord
        if mode == GameMode.VS_AI:
            self._pending_start = (mode_str, nom_rouge, nom_bleu)
            self._show(IDX_DIFFICULTY)
            return

        self._do_start(mode_str, nom_rouge, nom_bleu)

    def _on_difficulty_selected(self, difficulty: str):
        """Callback difficulté IA choisie — créer l'agent et lancer"""
        mode_str, nom_rouge, nom_bleu = self._pending_start
        self._pending_start = None

        agent = QLearningAgent(difficulty=difficulty)
        # Charger Q-table pré-entraînée si disponible
        import os
        trained_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "ai", "agent_trained.pkl"
        )
        agent.load(trained_path)

        self.ai_player = AIPlayer(agent, parent=self)
        self.ai_player.buzz_action.connect(self._on_ai_buzz)
        self.ai_player.answer_action.connect(self._on_ai_answer)
        self.ai_player.pick_action.connect(self._on_ai_pick)

        nom_bleu = f"🤖 Agent ({difficulty.capitalize()})"
        print(f"[AI] Agent créé : {agent}")
        self._do_start(mode_str, nom_rouge, nom_bleu)

    def _do_start(self, mode_str: str, nom_rouge: str, nom_bleu: str):
        """Lance effectivement la partie"""
        mode = GameMode(mode_str)

        self.game_state = GameState(mode=mode)
        self.game_state.team_rouge.name = nom_rouge
        self.game_state.team_bleu.name  = nom_bleu
        self.game_state.match_positions = self.game_data.get_match_positions()
        self.questions = self._build_questions()

        print(f"\n{'='*50}")
        print(f"[GAME START] {nom_rouge} vs {nom_bleu} ({mode.value})")
        print(f"[GAME START] {len(self.questions)} questions prêtes")
        print(f"{'='*50}")

        self._start_manche()

    # ─────────────────────────────────────────────────────
    # MANCHE
    # ─────────────────────────────────────────────────────
    def _start_manche(self):
        """Prépare et affiche la manche courante"""
        gs = self.game_state
        manche = gs.manche

        # Récupérer question
        self._current_question = self.questions[manche % len(self.questions)]

        # Position + paire de joueurs
        pos_group, pos_label = gs.current_position()
        p1, p2 = self.game_data.get_pair(pos_group)
        gs.current_players = (p1, p2)

        print(f"\n[Manche {manche+1}/11] {pos_label} | "
              f"Q: {self._current_question['question'][:50]}...")

        # Charger l'écran buzz
        self.buzz_screen.load_question(
            question     = self._current_question,
            manche       = manche,
            position_label = pos_label,
            game_state   = gs
        )
        self._show(IDX_BUZZ)

        # Mode VS_AI : l'agent décide s'il buzze
        if self.ai_player:
            self.ai_player.request_buzz(gs)

    # ─────────────────────────────────────────────────────
    # BUZZ
    # ─────────────────────────────────────────────────────
    def _on_buzzed(self, color: str):
        gs = self.game_state
        # Annuler le buzz IA en attente (l'humain a pu buzzer avant)
        if self.ai_player:
            self.ai_player.cancel_buzz()
        gs.on_buzz(color)
        print(f"[BUZZ] {color} a buzzé")

        # Afficher l'écran de réponse (première chance)
        self.answer_screen.load(
            question       = self._current_question,
            answering_color = color,
            manche         = gs.manche,
            game_state     = gs,
            is_second_chance = False
        )
        self._show(IDX_ANSWER)

        # Mode VS_AI : si c'est l'agent qui répond, il choisit automatiquement
        if self.ai_player and color == "bleu":
            self.ai_player.request_answer(self._current_question)

    # ─────────────────────────────────────────────────────
    # RÉPONSE
    # ─────────────────────────────────────────────────────
    def _on_answer_selected(self, chosen: str):
        gs           = self.game_state
        correct      = self._current_question.get("answer", "")
        is_correct   = (chosen.strip() == correct.strip())
        answering    = gs.buzzer

        self.answer_screen.disable_options()

        if is_correct:
            # ✅ Bonne réponse
            self.answer_screen.highlight_correct(correct)
            self.answer_screen.show_status(
                f"✅  Bonne réponse ! {gs.get_team(answering).name} choisit son joueur.",
                color="#00e676"
            )
            gs.on_correct_answer()
            print(f"[ANSWER] ✅ Correct — {gs.get_team(answering).name} choisit")
            QTimer.singleShot(1200, self._go_to_pick)

        elif gs.phase == Phase.ANSWER_A:
            # ❌ Mauvaise réponse — première équipe
            self.answer_screen.highlight_wrong(chosen, correct)
            got_red = gs.on_wrong_answer_first()
            team    = gs.get_team(answering)

            msg = f"❌  Mauvaise réponse — Carton jaune pour {team.name} !"
            if got_red:
                msg += f"  🟥 CARTON ROUGE !"
            self.answer_screen.show_status(msg, color=COLOR_ROUGE_STR)
            self.answer_screen.update_teams(gs)
            print(f"[ANSWER] ❌ Faux — carton jaune pour {team.name} (rouge: {got_red})")

            # Donner la 2ème chance à l'adversaire
            other = "bleu" if answering == "rouge" else "rouge"
            QTimer.singleShot(1500, lambda: self._second_chance(other))

        else:
            # ❌ Mauvaise réponse — deuxième équipe
            self.answer_screen.highlight_wrong(chosen, correct)
            self.answer_screen.show_status(
                "❌  Mauvaise réponse — Question annulée, aucun joueur attribué.",
                color=COLOR_ROUGE_STR
            )
            gs.on_wrong_answer_second()
            print(f"[ANSWER] ❌ 2ème faux — question annulée")
            QTimer.singleShot(1800, self._after_manche)

    def _on_timer_expired(self):
        """Temps écoulé — traiter comme mauvaise réponse"""
        gs = self.game_state
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
            QTimer.singleShot(1500, self._after_manche)

    def _second_chance(self, other_color: str):
        """Affiche la 2ème chance pour l'équipe adverse"""
        gs = self.game_state
        gs.buzzer = other_color   # Mettre à jour qui répond
        self.answer_screen.load(
            question        = self._current_question,
            answering_color = other_color,
            manche          = gs.manche,
            game_state      = gs,
            is_second_chance = True
        )
        self._show(IDX_ANSWER)

        # Mode VS_AI : si c'est l'agent qui a la 2ème chance
        if self.ai_player and other_color == "bleu":
            self.ai_player.request_answer(self._current_question)

    # ─────────────────────────────────────────────────────
    # PICK
    # ─────────────────────────────────────────────────────
    def _go_to_pick(self):
        gs = self.game_state
        p1, p2 = gs.current_players
        chooser = gs.winner_manche

        self.pick_screen.load(
            player1       = p1,
            player2       = p2,
            chooser_color = chooser,
            manche        = gs.manche,
            game_state    = gs
        )
        self._show(IDX_PICK)

        # Mode VS_AI : si c'est l'agent qui choisit
        if self.ai_player and chooser == "bleu":
            self.ai_player.request_pick(p1, p2, gs)

    def _on_player_picked(self, index: int):
        gs = self.game_state
        gs.on_pick_player(index)
        print(f"[PICK] Joueur {index+1} choisi — "
              f"Rouge: {len(gs.team_rouge.players)} joueurs | "
              f"Bleu: {len(gs.team_bleu.players)} joueurs")
        self._after_manche()

    # ─────────────────────────────────────────────────────
    # APRÈS CHAQUE MANCHE
    # ─────────────────────────────────────────────────────
    def _after_manche(self):
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

    # ─────────────────────────────────────────────────────
    # ÉCHANGE
    # ─────────────────────────────────────────────────────
    def _on_exchanges_done(self):
        print("[EXCHANGE] Échanges terminés — révélation")
        self._start_reveal()

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
                for p in taken:
                    if p in penalized.players:
                        penalized.players.remove(p)
                        adversary.players.append(p)
                for p in given:
                    if p in adversary.players:
                        adversary.players.remove(p)
                        penalized.players.append(p)
                print(f"[AI EXCHANGE] IA prend {[p.name for p in taken]}, "
                      f"donne {[p.name for p in given]}")

        # 2) Échanges humains (bleu pénalisé, humain est adversaire)
        if gs.team_bleu.rouges > 0:
            queue = ["bleu"] * gs.team_bleu.rouges
            self.exchange_screen.load(gs, exchange_queue=queue)
            self._show(IDX_EXCHANGE)
        else:
            self._start_reveal()

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

    # ─────────────────────────────────────────────────────
    # RÉVÉLATION
    # ─────────────────────────────────────────────────────
    def _start_reveal(self):
        self.reveal_screen.load(self.game_state)
        self._show(IDX_REVEAL)

    # ─────────────────────────────────────────────────────
    # QUESTIONS STATIQUES (Phase 1 — remplacées par Groq en Phase 3)
    # ─────────────────────────────────────────────────────
    def _build_questions(self) -> list[dict]:
        return get_questions(n=TOTAL_MANCHES, shuffle=True)


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
