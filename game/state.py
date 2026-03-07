# ============================================================
# game/state.py — Machine à états du jeu
# ============================================================

from enum import Enum, auto
from dataclasses import dataclass, field
from game.player import Player
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TOTAL_MANCHES, MAX_JAUNES


class Phase(Enum):
    """Phases possibles du jeu"""
    INTRO       = auto()   # écran d'accueil
    BUZZ        = auto()   # attente du buzz
    ANSWER_A    = auto()   # équipe A répond (a buzzé en premier)
    ANSWER_B    = auto()   # équipe B répond (deuxième chance)
    PICK        = auto()   # l'équipe gagnante choisit un joueur
    EXCHANGE    = auto()   # phase d'échange (cartons rouges)
    REVEAL      = auto()   # révélation finale des ratings
    FINISHED    = auto()   # fin de partie


class GameMode(Enum):
    LOCAL    = "local"       # 2 joueurs même PC
    VS_AI    = "vs_ai"       # 1 joueur vs agent IA
    ONLINE   = "online"      # multijoueur en ligne
    SOLO     = "solo"        # solo entraînement


@dataclass
class TeamState:
    """État d'une équipe"""
    name:         str
    color:        str          # ex: "rouge" ou "bleu"
    jaunes:       int  = 0
    rouges:       int  = 0
    players:      list = field(default_factory=list)   # liste de Player

    @property
    def total_rating(self) -> int:
        """Total des ratings FIFA (révélés ou pas)"""
        return sum(p.get_rating_force() for p in self.players)

    @property
    def total_rating_revealed(self) -> int | str:
        """Total affiché — seulement si tous révélés"""
        if all(p.revealed for p in self.players):
            return self.total_rating
        return "?"

    def add_jaune(self) -> bool:
        """Ajoute un carton jaune. Retourne True si carton rouge obtenu."""
        self.jaunes += 1
        if self.jaunes >= MAX_JAUNES:
            self.jaunes = 0
            self.rouges += 1
            return True   # carton rouge !
        return False

    def add_player(self, player: Player):
        self.players.append(player)

    def reveal_all(self):
        """Révèle tous les ratings de l'équipe"""
        for p in self.players:
            p.reveal()


@dataclass
class GameState:
    """
    État global de la partie.
    C'est la source de vérité — tout l'état du jeu est ici.
    """
    mode:           GameMode
    team_rouge:     TeamState = field(default_factory=lambda: TeamState("Équipe Rouge", "rouge"))
    team_bleu:      TeamState = field(default_factory=lambda: TeamState("Équipe Bleue", "bleu"))
    phase:          Phase     = Phase.BUZZ
    manche:         int       = 0          # 0 à TOTAL_MANCHES-1
    buzzer:         str | None = None      # "rouge" | "bleu" | None
    winner_manche:  str | None = None      # équipe ayant gagné la manche
    match_positions: list     = field(default_factory=list)
    current_question: dict    = field(default_factory=dict)
    current_players:  tuple   = field(default_factory=tuple)  # (Player, Player)
    exchange_done:    bool    = False

    # --------------------------------------------------------
    # Accès aux équipes
    # --------------------------------------------------------
    def get_team(self, color: str) -> TeamState:
        return self.team_rouge if color == "rouge" else self.team_bleu

    def get_other_team(self, color: str) -> TeamState:
        return self.team_bleu if color == "rouge" else self.team_rouge

    def current_position(self) -> tuple[str, str]:
        """Position de la manche courante (group, label)"""
        if self.manche < len(self.match_positions):
            return self.match_positions[self.manche]
        return ("ATT", "Attaquant (ST)")

    # --------------------------------------------------------
    # Transitions d'état
    # --------------------------------------------------------
    def on_buzz(self, color: str):
        """Une équipe a buzzé"""
        self.buzzer = color
        self.phase  = Phase.ANSWER_A

    def on_correct_answer(self) -> str:
        """Bonne réponse — retourne la couleur gagnante"""
        self.winner_manche = self.buzzer
        self.phase = Phase.PICK
        return self.winner_manche

    def on_wrong_answer_first(self) -> bool:
        """
        Mauvaise réponse de l'équipe qui a buzzé.
        Retourne True si carton rouge obtenu.
        """
        team = self.get_team(self.buzzer)
        got_red = team.add_jaune()
        self.phase = Phase.ANSWER_B   # l'autre équipe peut répondre
        return got_red

    def on_wrong_answer_second(self):
        """Mauvaise réponse de la deuxième équipe — question annulée"""
        # Pas de carton pour la 2e équipe
        self.next_manche()

    def on_pick_player(self, player_idx: int):
        """L'équipe gagnante choisit un joueur (0 ou 1)"""
        p1, p2 = self.current_players
        winner = self.get_team(self.winner_manche)
        loser  = self.get_other_team(self.winner_manche)

        if player_idx == 0:
            winner.add_player(p1)
            loser.add_player(p2)
        else:
            winner.add_player(p2)
            loser.add_player(p1)

        self.next_manche()

    def next_manche(self):
        """Passer à la manche suivante ou terminer"""
        self.manche        += 1
        self.buzzer         = None
        self.winner_manche  = None
        self.current_players = ()

        if self.manche >= TOTAL_MANCHES:
            # Vérifier si échanges nécessaires
            if self.team_rouge.rouges > 0 or self.team_bleu.rouges > 0:
                self.phase = Phase.EXCHANGE
            else:
                self.phase = Phase.REVEAL
        else:
            self.phase = Phase.BUZZ

    def start_reveal(self):
        """Révéler tous les ratings"""
        self.team_rouge.reveal_all()
        self.team_bleu.reveal_all()
        self.phase = Phase.REVEAL

    def get_winner(self) -> str | None:
        """Retourne 'rouge', 'bleu', ou 'egalite'"""
        if self.phase != Phase.REVEAL and self.phase != Phase.FINISHED:
            return None
        r = self.team_rouge.total_rating
        b = self.team_bleu.total_rating
        if r > b:   return "rouge"
        if b > r:   return "bleu"
        return "egalite"

    def progress(self) -> float:
        """Progression de 0.0 à 1.0"""
        return self.manche / TOTAL_MANCHES

    def __repr__(self):
        return (f"GameState(manche={self.manche}/{TOTAL_MANCHES}, "
                f"phase={self.phase.name}, buzzer={self.buzzer})")
