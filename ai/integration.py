# ============================================================
# ai/integration.py — Intégration agent IA dans le thread UI
# ============================================================

import random
import sys
import os

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.agent import QLearningAgent


class AIPlayer(QObject):
    """
    Pont entre le QLearningAgent et l'interface PyQt5.
    Utilise des QTimers pour simuler le temps de réflexion de l'IA.
    Chaque décision est retardée pour que le joueur humain voie l'IA "réfléchir".
    """

    # Signaux émis quand l'agent a pris une décision
    buzz_action     = pyqtSignal()           # l'IA veut buzzer
    answer_action   = pyqtSignal(str)        # l'IA a choisi une réponse
    pick_action     = pyqtSignal(int)        # l'IA a choisi joueur 0 ou 1

    def __init__(self, agent: QLearningAgent, parent=None):
        super().__init__(parent)
        self.agent = agent

        # Timer buzz annulable
        self._buzz_timer = QTimer(self)
        self._buzz_timer.setSingleShot(True)
        self._buzz_timer.timeout.connect(self._emit_buzz)

        # Timer réponse
        self._answer_timer = QTimer(self)
        self._answer_timer.setSingleShot(True)
        self._answer_timer.timeout.connect(self._emit_answer)
        self._pending_answer = ""

        # Timer pick
        self._pick_timer = QTimer(self)
        self._pick_timer.setSingleShot(True)
        self._pick_timer.timeout.connect(self._emit_pick)
        self._pending_pick = 0

    # ─────────────────────────────────────────────────────
    # BUZZ
    # ─────────────────────────────────────────────────────
    def request_buzz(self, game_state):
        """Demande à l'agent s'il veut buzzer (après un délai)."""
        if self.agent.should_buzz(game_state):
            delay = self.agent.buzz_delay_ms + random.randint(-400, 400)
            delay = max(300, delay)
            self._buzz_timer.start(delay)

    def cancel_buzz(self):
        """Annule le buzz en attente (l'humain a buzzé avant)."""
        self._buzz_timer.stop()

    def _emit_buzz(self):
        self.buzz_action.emit()

    # ─────────────────────────────────────────────────────
    # RÉPONSE
    # ─────────────────────────────────────────────────────
    def request_answer(self, question: dict):
        """L'agent doit répondre à une question."""
        self._pending_answer = self.agent.choose_answer(question)
        delay = random.randint(1200, 3000)
        self._answer_timer.start(delay)

    def cancel_answer(self):
        """Annule la réponse en attente."""
        self._answer_timer.stop()

    def _emit_answer(self):
        self.answer_action.emit(self._pending_answer)

    # ─────────────────────────────────────────────────────
    # PICK (choix de joueur)
    # ─────────────────────────────────────────────────────
    def request_pick(self, player1, player2, game_state):
        """L'agent doit choisir entre 2 joueurs."""
        self._pending_pick = self.agent.choose_player(player1, player2, game_state)
        delay = random.randint(800, 2000)
        self._pick_timer.start(delay)

    def cancel_pick(self):
        """Annule le pick en attente."""
        self._pick_timer.stop()

    def _emit_pick(self):
        self.pick_action.emit(self._pending_pick)

    # ─────────────────────────────────────────────────────
    # NETTOYAGE
    # ─────────────────────────────────────────────────────
    def cancel_all(self):
        """Annule toutes les actions en attente."""
        self._buzz_timer.stop()
        self._answer_timer.stop()
        self._pick_timer.stop()
