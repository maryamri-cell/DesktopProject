# ============================================================
# ai/agent.py — Agent IA Q-Learning pour Ahsan Khota
# ============================================================

import random
import pickle
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class QLearningAgent:
    """
    Agent IA adaptatif basé sur Q-Learning.
    Joue en tant qu'équipe bleue (adversaire automatique).

    3 niveaux de difficulté :
    - easy   : choix quasi-aléatoires, lent à buzzer
    - medium : bon instinct, vitesse modérée
    - hard   : quasi-optimal, buzz rapide
    """

    DIFFICULTIES = {
        "easy": {
            "epsilon": 0.60,
            "buzz_delay_ms": 3000,
            "answer_accuracy": 0.35,
            "rating_knowledge": 0.20,
        },
        "medium": {
            "epsilon": 0.30,
            "buzz_delay_ms": 1800,
            "answer_accuracy": 0.60,
            "rating_knowledge": 0.50,
        },
        "hard": {
            "epsilon": 0.05,
            "buzz_delay_ms": 800,
            "answer_accuracy": 0.85,
            "rating_knowledge": 0.90,
        },
    }

    def __init__(self, difficulty: str = "medium"):
        params = self.DIFFICULTIES.get(difficulty, self.DIFFICULTIES["medium"])
        self.difficulty        = difficulty
        self.epsilon           = params["epsilon"]
        self.buzz_delay_ms     = params["buzz_delay_ms"]
        self.answer_accuracy   = params["answer_accuracy"]
        self.rating_knowledge  = params["rating_knowledge"]

        # Q-Learning hyper-paramètres
        self.alpha   = 0.1    # taux d'apprentissage
        self.gamma   = 0.95   # facteur de discount
        self.q_table = {}     # {(state_key, action): q_value}

    # ─────────────────────────────────────────────────────
    # REPRÉSENTATION D'ÉTAT
    # ─────────────────────────────────────────────────────
    def _state_key(self, game_state) -> str:
        """Représentation simplifiée de l'état pour la Q-table."""
        gs = game_state
        my   = gs.team_bleu
        opp  = gs.team_rouge
        return (
            f"m{gs.manche}_"
            f"my{len(my.players)}_opp{len(opp.players)}_"
            f"myj{my.jaunes}_oppj{opp.jaunes}_"
            f"myr{my.rouges}_oppr{opp.rouges}"
        )

    # ─────────────────────────────────────────────────────
    # SÉLECTION D'ACTION (epsilon-greedy)
    # ─────────────────────────────────────────────────────
    def choose_action(self, state_key: str, available_actions: list) -> str:
        """Sélection epsilon-greedy dans la Q-table."""
        if random.random() < self.epsilon:
            return random.choice(available_actions)

        q_values = {
            a: self.q_table.get((state_key, a), 0.0)
            for a in available_actions
        }
        max_q = max(q_values.values())
        best  = [a for a, q in q_values.items() if q == max_q]
        return random.choice(best)

    # ─────────────────────────────────────────────────────
    # DÉCISIONS DE JEU
    # ─────────────────────────────────────────────────────
    def should_buzz(self, game_state) -> bool:
        """Décide si l'agent doit buzzer."""
        state = self._state_key(game_state)
        action = self.choose_action(state, ["buzz", "wait"])
        return action == "buzz"

    def choose_answer(self, question: dict) -> str:
        """Choisit une réponse parmi les 4 options."""
        correct = question.get("answer", "")
        options = question.get("options", [])

        if random.random() < self.answer_accuracy:
            return correct

        wrong = [o for o in options if o != correct]
        return random.choice(wrong) if wrong else correct

    def choose_player(self, player1, player2, game_state) -> int:
        """Choisit entre le joueur 0 ou 1."""
        if random.random() < self.rating_knowledge:
            r1 = player1.get_rating_force()
            r2 = player2.get_rating_force()
            return 0 if r1 >= r2 else 1
        return random.randint(0, 1)

    def choose_exchange_take(self, opponent_players: list, n: int) -> list:
        """Choisit N joueurs à prendre dans l'équipe adverse."""
        if not opponent_players:
            return []
        n = min(n, len(opponent_players))
        if random.random() < self.rating_knowledge:
            ranked = sorted(opponent_players,
                            key=lambda p: p.get_rating_force(), reverse=True)
            return ranked[:n]
        return random.sample(opponent_players, n)

    def choose_exchange_give(self, own_players: list, n: int) -> list:
        """Choisit N de ses propres joueurs à donner."""
        if not own_players:
            return []
        n = min(n, len(own_players))
        if random.random() < self.rating_knowledge:
            ranked = sorted(own_players,
                            key=lambda p: p.get_rating_force())
            return ranked[:n]
        return random.sample(own_players, n)

    # ─────────────────────────────────────────────────────
    # MISE À JOUR Q-TABLE
    # ─────────────────────────────────────────────────────
    def update(self, state: str, action: str, reward: float, next_state: str):
        """Mise à jour Q-Learning classique."""
        old_q = self.q_table.get((state, action), 0.0)
        next_actions = ["buzz", "wait", "answer", "pick0", "pick1"]
        next_q_vals  = [self.q_table.get((next_state, a), 0.0)
                        for a in next_actions]
        max_next_q   = max(next_q_vals) if next_q_vals else 0.0
        new_q = old_q + self.alpha * (reward + self.gamma * max_next_q - old_q)
        self.q_table[(state, action)] = new_q

    # ─────────────────────────────────────────────────────
    # SAUVEGARDE / CHARGEMENT
    # ─────────────────────────────────────────────────────
    def save(self, path: str = "ai/agent_trained.pkl"):
        """Sauvegarde la Q-table entraînée."""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "q_table":    self.q_table,
                "difficulty": self.difficulty,
                "epsilon":    self.epsilon,
            }, f)
        print(f"[AI] Agent sauvegardé → {path}  ({len(self.q_table)} entrées)")

    def load(self, path: str = "ai/agent_trained.pkl"):
        """Charge une Q-table pré-entraînée."""
        if not os.path.exists(path):
            print(f"[AI] Pas de fichier {path} — agent vierge")
            return
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.q_table = data.get("q_table", {})
        print(f"[AI] Agent chargé ← {path}  ({len(self.q_table)} entrées)")

    def __repr__(self):
        return (f"QLearningAgent(difficulty={self.difficulty}, "
                f"epsilon={self.epsilon:.2f}, "
                f"q_size={len(self.q_table)})")
