# ============================================================
# ai/integration.py — Intégration ComputerOpponent dans PyQt5
# ============================================================

import random
import sys
import os

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.agent import ComputerOpponent


class AIPlayer(QObject):
    """
    Pont entre ComputerOpponent (logique pure) et l'interface PyQt5.
    Gère les timers pour simuler la réflexion humaine.
    """

    # Signaux
    buzz_action     = pyqtSignal()           # L'IA veut buzzer
    skip_action     = pyqtSignal()           # L'IA veut skip
    answer_action   = pyqtSignal(str)        # L'IA a choisi une réponse
    pick_action     = pyqtSignal(int)        # L'IA a choisi joueur 0 ou 1
    reaction_emit   = pyqtSignal(str)        # Signal émotionnel (optionnel)

    def __init__(self, agent: ComputerOpponent, parent=None, seed: int | None = None):
        super().__init__(parent)
        self.agent = agent
        self.rng = random.Random(seed if seed is not None else 0)

        # Timer Buzz / Skip
        self._think_timer = QTimer(self)
        self._think_timer.setSingleShot(True)
        self._think_timer.timeout.connect(self._on_think_finished)

        # Timer Réponse
        self._answer_timer = QTimer(self)
        self._answer_timer.setSingleShot(True)
        self._answer_timer.timeout.connect(self._emit_answer)
        self._pending_answer = ""

        # Timer Pick
        self._pick_timer = QTimer(self)
        self._pick_timer.setSingleShot(True)
        self._pick_timer.timeout.connect(self._emit_pick)
        self._pending_pick = 0
        
        self._pending_action = "WAIT" # BUZZ, SKIP, or WAIT

    # ─────────────────────────────────────────────────────
    # RÉFLEXION INITIALE (BUZZ / SKIP)
    # ─────────────────────────────────────────────────────
    
    def request_buzz(self, game_state):
        """Phase de buzz : l'IA réfléchit si elle buzz ou skip."""
        self._pending_action = self.agent.decide_action(game_state)
        
        if self._pending_action == "WAIT":
            return # Ne fait rien ce round (sauf si l'humain buzz)

        # Calculer le délai basé sur le type de question
        q_type = game_state.get_question_type().name if hasattr(game_state, "get_question_type") else "MCQ"
        delay = self.agent.get_buzz_delay(q_type)
        
        # On lance un timer de réflexion
        self._think_timer.start(delay)

    def _on_think_finished(self):
        """Appelé quand le délai de réflexion est écoulé."""
        if self._pending_action == "SKIP":
            self.skip_action.emit()
            self.reaction_emit.emit("HESITATING")
        elif self._pending_action == "BUZZ":
            self.buzz_action.emit()
            self.reaction_emit.emit("CONFIDENT" if self.agent.confidence_modifier > 1.1 else "NEUTRAL")

    def cancel_buzz(self):
        """Annule la réflexion (l'humain a buzzé)."""
        self._think_timer.stop()

    # ─────────────────────────────────────────────────────
    # RÉPONSE
    # ─────────────────────────────────────────────────────
    
    def request_answer(self, question: dict):
        """L'IA doit choisir une option parmi celles affichées."""
        self._pending_answer = self.agent.choose_answer(question)
        
        # Délai de "lecture" des options : augmenté pour laisser l'humain voir
        # les propositions s'afficher (min 1.8s)
        delay = self.rng.randint(1800, 3500)
        self._answer_timer.start(delay)

    def cancel_answer(self):
        self._answer_timer.stop()

    def _emit_answer(self):
        self.answer_action.emit(self._pending_answer)
        # Émettre une réaction basée sur le momentum après avoir répondu
        if self.agent.confidence_modifier > 1.2:
            self.reaction_emit.emit("CONFIDENT")
        elif self.agent.confidence_modifier < 0.8:
            self.reaction_emit.emit("FRUSTRATED")

    # ─────────────────────────────────────────────────────
    # PICK (CARTES)
    # ─────────────────────────────────────────────────────
    
    def request_pick(self, player1, player2, game_state):
        """L'IA choisit un joueur."""
        self._pending_pick = self.agent.choose_player(player1, player2, game_state)
        
        # Délai d'analyse des cartes
        delay = self.rng.randint(1000, 3000)
        self._pick_timer.start(delay)

    def cancel_pick(self):
        self._pick_timer.stop()

    def _emit_pick(self):
        self.pick_action.emit(self._pending_pick)

    # ─────────────────────────────────────────────────────
    # UTILS
    # ─────────────────────────────────────────────────────
    
    def cancel_all(self):
        self._think_timer.stop()
        self._answer_timer.stop()
        self._pick_timer.stop()
