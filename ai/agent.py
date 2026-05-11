# ============================================================
# ai/agent.py — Adversaire de jeu (ComputerOpponent)
# ============================================================

import random
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.profiles import PROFILES

class ComputerOpponent:
    """
    Simule un adversaire humain déterministe et réaliste.
    Remplace l'ancien système de Q-Learning.
    """

    def __init__(self, difficulty: str = "medium", seed: int | None = None):
        self.difficulty = difficulty.lower()
        self.profile = PROFILES.get(self.difficulty, PROFILES["medium"])
        self.rng = random.Random(seed if seed is not None else 0)
        
        # État interne émotionnel (momentum)
        self.confidence_modifier = 1.0
        self._consecutive_successes = 0
        self._consecutive_failures = 0

    def reset_match_context(self):
        """Réinitialise le contexte émotionnel pour un nouveau match."""
        self.confidence_modifier = 1.0
        self._consecutive_successes = 0
        self._consecutive_failures = 0

    # ── Système de Buzz ───────────────────────────────────
    
    def decide_action(self, game_state) -> str:
        """
        Décide de l'action à entreprendre (BUZZ, SKIP, WAIT).
        """
        if self.should_skip(game_state):
            return "SKIP"
        
        if self.should_buzz(game_state):
            return "BUZZ"
            
        return "WAIT"

    def should_buzz(self, game_state) -> bool:
        """
        Décide si l'IA buzz en fonction de sa confiance.
        """
        threshold = 1.0 - (self.profile["buzz_aggressiveness"] * self.confidence_modifier)
        
        if self._is_losing(game_state):
            threshold *= 0.8
            
        return self.rng.random() > threshold

    def get_buzz_delay(self, question_type: str) -> int:
        """
        Calcule le délai de réaction (ms) de manière "humaine".
        """
        base = self.profile["base_reaction_ms"]
        jitter = self.profile["jitter_ms"]
        
        # Modificateurs par type de question
        type_mod = {
            "IMAGE_GUESS": 1.5,     # Plus long à reconnaître une image
            "WHO_AM_I": 1.3,        # Lecture du texte
            "MCQ": 0.8,             # Réponse rapide sur du texte simple
            "TRANSFER_TRIVIA": 1.1,
        }.get(question_type, 1.0)
        
        # Calcul final avec jitter non-linéaire
        delay = (base * type_mod) + self.rng.gauss(0, jitter / 2)
        
        # Momentum : si confiant, on réagit plus vite
        delay /= self.confidence_modifier
        
        return int(max(400, delay))

    # ── Système de Réponse ───────────────────────────────

    def choose_answer(self, question: dict) -> str:
        """
        Choisit une réponse en fonction de ses connaissances.
        """
        correct = question.get("answer", "")
        options = question.get("options", [])
        q_type = question.get("type", "MCQ")
        
        # Probabilité de succès
        success_rate = self.profile["accuracy"].get(q_type, 0.5)
        
        # Ajustement par momentum
        success_rate *= self.confidence_modifier
        
        if self.rng.random() < success_rate:
            self._on_success()
            return correct
        else:
            self._on_failure()
            wrong = [o for o in options if o != correct]
            return self.rng.choice(wrong) if wrong else correct

    # ── Système de Pick (Cartes) ─────────────────────────

    def choose_player(self, player1, player2, game_state) -> int:
        """
        Estime quel joueur est le meilleur sans lire le rating caché.
        Se base sur la réputation et le prestige du club.
        """
        est1 = self._estimate_player_strength(player1)
        est2 = self._estimate_player_strength(player2)
        
        # Si estimation proche, petite chance de doute
        if abs(est1 - est2) < 3:
            if self.rng.random() < 0.2:
                return 1 if est1 >= est2 else 0
        
        return 0 if est1 >= est2 else 1

    def _estimate_player_strength(self, player) -> float:
        """
        Simule l'évaluation subjective d'un joueur.
        Utilise la réputation internationale et le prestige du club.
        """
        # Baseline : la réputation internationale (1-5) donne une grosse indication
        rep = getattr(player, "reputation", 1)
        base_fame = 65 + (rep * 6) # 1->71, 2->77, 3->83, 4->89, 5->95
        
        # Le "perçu" du niveau global (simule la connaissance de la fiche du joueur)
        perceived_ovr = getattr(player, "overall_reputation", 75)
        
        error_margin = self.profile["pick_error_margin"]
        noise = self.rng.gauss(0, 20 * error_margin)
        
        # Simulation du prestige du club
        prestige_bonus = 0
        famous_clubs = ["Real Madrid", "Manchester City", "Barcelona", "Bayern München", "Liverpool", "PSG", "Arsenal", "Inter"]
        if player.club in famous_clubs:
            prestige_bonus = self.rng.uniform(1, 4)
            
        return (base_fame * 0.4 + perceived_ovr * 0.6) + noise + prestige_bonus

    # ── Système d'Échange (Cartons Rouges) ─────────────────
    
    def choose_exchange_take(self, opponent_players: list, count: int) -> list:
        """
        Choisit le(s) meilleur(s) joueur(s) de l'adversaire à lui voler (Take).
        L'IA sélectionne les joueurs avec les plus hautes statistiques estimées.
        """
        if not opponent_players:
            return []
        sorted_players = sorted(opponent_players, key=lambda p: self._estimate_player_strength(p), reverse=True)
        return sorted_players[:count]

    def choose_exchange_give(self, my_bench: list, count: int) -> list:
        """
        Choisit le(s) joueur(s) de son propre banc à donner à l'adversaire (Give).
        L'IA sélectionne ses joueurs les plus faibles.
        """
        if not my_bench:
            return []
        sorted_players = sorted(my_bench, key=lambda p: self._estimate_player_strength(p))
        return sorted_players[:count]

    # ── Système de Skip ───────────────────────────────────

    def should_skip(self, game_state) -> bool:
        """Parfois l'IA préfère passer si elle n'est pas confiante."""
        confidence = self._calculate_confidence(game_state)
        
        # Si confiance très basse, on a une chance de skip
        if confidence < 0.3:
            return self.rng.random() < self.profile["skip_tendency"]
        return False

    def should_accept_skip(self) -> bool:
        """Accepte le skip de l'adversaire si pas confiant."""
        return self.rng.random() < self.profile["skip_tendency"] * 1.5

    # ── Helpers Internes ──────────────────────────────────

    def _calculate_confidence(self, game_state) -> float:
        """Calcule un score de confiance interne [0, 1]."""
        # Pour l'instant, basé sur la difficulté de base + momentum
        base_conf = self.profile["accuracy"]["MCQ"] # Proxy pour la connaissance générale
        return min(1.0, base_conf * self.confidence_modifier)

    def _is_losing(self, game_state) -> bool:
        """Vérifie si l'IA est en train de perdre."""
        my_score = game_state.team_bleu.total_rating_revealed
        opp_score = game_state.team_rouge.total_rating_revealed
        return my_score < (opp_score - 10)

    def _on_success(self):
        self._consecutive_successes += 1
        self._consecutive_failures = 0
        self.confidence_modifier = min(1.3, 1.0 + (self._consecutive_successes * 0.05))

    def _on_failure(self):
        self._consecutive_failures += 1
        self._consecutive_successes = 0
        self.confidence_modifier = max(0.7, 1.0 - (self._consecutive_failures * 0.05))

    # Trigger de réaction émotionnelle (pour l'UI)
    def get_reaction(self, event_type: str) -> str:
        """Retourne un état émotionnel basé sur un événement."""
        if event_type == "wrong_answer":
            return "FRUSTRATED" if self.difficulty == "hard" else "DISAPPOINTED"
        if event_type == "correct_answer":
            return "CONFIDENT" if self._consecutive_successes > 1 else "EXCITED"
        if event_type == "lost_elite":
            return "ANGRY"
        return "NEUTRAL"

    def __repr__(self):
        return f"ComputerOpponent(difficulty={self.difficulty}, momentum={self.confidence_modifier:.2f})"
