# ============================================================
# game/state.py — Machine à états du jeu
# ============================================================

from enum import Enum, auto
from dataclasses import dataclass, field
from game.player import Player
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TOTAL_MANCHES, MAX_JAUNES
import random


STARTER_SLOTS = [
    # 4-3-3 strict starter order: defenders -> midfielders -> attackers -> goalkeeper
    "DEF1", "DEF2", "DEF3", "DEF4",
    "MID1", "MID2", "MID3",
    "ATT1", "ATT2", "ATT3",
    "GK",
]


class Phase(Enum):
    """Phases possibles du jeu"""
    INTRO           = auto()   # écran d'accueil
    BUZZ            = auto()   # attente du buzz
    ANSWER_A        = auto()   # équipe A répond (a buzzé en premier)
    SECOND_CHANCE_A = auto()   # équipe A deuxième tentative (après mauvaise réponse)
    ANSWER_B        = auto()   # équipe B répond (deuxième chance)
    SECOND_CHANCE_B = auto()   # équipe B deuxième tentative (après mauvaise réponse)
    PICK            = auto()   # l'équipe gagnante choisit un joueur
    EXCHANGE        = auto()   # phase d'échange (cartons rouges)
    REVEAL          = auto()   # révélation finale des ratings
    FINISHED        = auto()   # fin de partie


class GameMode(Enum):
    LOCAL    = "local"       # 2 joueurs même PC
    VS_AI    = "vs_ai"       # 1 joueur vs agent IA
    ONLINE   = "online"      # multijoueur en ligne
    SOLO     = "solo"        # solo entraînement


class RoundType(Enum):
    """Types de rounds dans le nouveau mode Online"""
    DEFENDERS      = "Défenseurs"   # Round 1: 5 défenseurs
    MIDFIELDERS    = "Milieux"      # Round 2: milieux
    ATTACKERS      = "Attaquants"   # Round 3: attaquants
    GOALKEEPER     = "Gardien"      # Final: gardien
    BENCH          = "Remplaçants"  # Rounds de banc

class QuestionType(Enum):
    """Types de questions possibles"""
    MCQ            = auto()         # QCM classique
    IMAGE_GUESS    = auto()         # Deviner via pollinations.ai
    REORDERING     = auto()         # Reclassement d'événements
    TRANSFER       = auto()         # Historique de transferts
    WHO_AM_I       = auto()         # Qui suis-je (indices progressifs)


@dataclass
class TeamState:
    """État d'une équipe"""
    name:         str
    color:        str          # ex: "rouge" ou "bleu"
    jaunes:       int  = 0
    rouges:       int  = 0
    players:      list = field(default_factory=list)   # liste de Player
    
    # Mapping position sur le terrain -> Player
    # Ex: {"GK": Player1, "CB1": Player2, "Bench": [Player3, ...]}
    formation:    dict = field(default_factory=lambda: {
        "DEF1": None, "DEF2": None, "DEF3": None, "DEF4": None,
        "MID1": None, "MID2": None, "MID3": None,
        "ATT1": None, "ATT2": None, "ATT3": None,
        "GK": None,
        "BENCH": []
    })

    @property
    def penalty(self) -> int:
        """Pénalité de points (cartons jaunes) : -2 points par jaune"""
        return self.jaunes * 2

    @property
    def total_rating(self) -> int:
        """Total des ratings FIFA (seulement les 11 titulaires) moins les pénalités"""
        total = 0
        for pos, player in self.formation.items():
            if pos != "BENCH" and player is not None:
                total += player.get_rating_force()
        return max(0, total - self.penalty)

    @property
    def total_rating_revealed(self) -> int | str:
        """Total affiché — seulement si tous révélés"""
        if not self.players: return 0
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

    def add_player(self, player: Player, preferred_pos: str = None, pos_group: str = None, within_index: int = None):
        """Ajoute un joueur et tente de le placer dans la formation"""
        self.players.append(player)
        
        # Mapping des positions par défaut pour le dessin sur le terrain
        # Rouge = Bas du terrain (Y: 0.55 -> 0.95)
        # Bleu  = Haut du terrain (Y: 0.05 -> 0.45)
        is_blue = (self.color == "bleu")
        
        # Standard Symmetrical Full-Pitch Coordinates (Bottom to Top)
        # These are used for the individual composition view.
        coords = {
            "DEF1": (0.12, 0.72), "DEF2": (0.37, 0.75), "DEF3": (0.63, 0.75), "DEF4": (0.88, 0.72),
            "MID1": (0.22, 0.50), "MID2": (0.50, 0.50), "MID3": (0.78, 0.50),
            "ATT1": (0.20, 0.25), "ATT2": (0.50, 0.20), "ATT3": (0.80, 0.25),
            "GK":   (0.50, 0.90)
        }
        
        target_slot = None
        if preferred_pos in (None, "", "FIELD"):
            # If caller provided the position group and within-phase index, honor
            # the exact starter/bench split for the 4-3-3 draft (4-3-3 starters)
            if pos_group == "DEF":
                # defenders phase: first 4 -> starters (DEF1..DEF4), remaining -> bench
                if within_index is not None and within_index < 4:
                    for slot in ("DEF1", "DEF2", "DEF3", "DEF4"):
                        if self.formation.get(slot) is None:
                            target_slot = slot
                            break
                else:
                    target_slot = "BENCH"
            elif pos_group == "MID":
                # midfielders: first 3 -> starters (MID1..MID3)
                if within_index is not None and within_index < 3:
                    for slot in ("MID1", "MID2", "MID3"):
                        if self.formation.get(slot) is None:
                            target_slot = slot
                            break
                else:
                    target_slot = "BENCH"
            elif pos_group == "ATT":
                # attackers: first 3 -> starters (ATT1..ATT3)
                if within_index is not None and within_index < 3:
                    for slot in ("ATT1", "ATT2", "ATT3"):
                        if self.formation.get(slot) is None:
                            target_slot = slot
                            break
                else:
                    target_slot = "BENCH"
            elif pos_group == "GK":
                # goalkeepers: first -> GK, second -> bench
                if within_index is not None and within_index == 0:
                    if self.formation.get("GK") is None:
                        target_slot = "GK"
                    else:
                        target_slot = "BENCH"
                else:
                    target_slot = "BENCH"
            else:
                # Fallback to global starter slots fill order
                for slot in STARTER_SLOTS:
                    if self.formation.get(slot) is None:
                        target_slot = slot
                        break
        elif preferred_pos and preferred_pos in self.formation and self.formation[preferred_pos] is None:
            target_slot = preferred_pos
        else:
            pos_prefix = preferred_pos[:3] if preferred_pos else ""
            for k in self.formation:
                if k.startswith(pos_prefix) and self.formation[k] is None:
                    target_slot = k
                    break
        
        if target_slot and target_slot != "BENCH":
            self.formation[target_slot] = player
            if target_slot in coords:
                player.pitch_pos = coords[target_slot]
        else:
            self.formation["BENCH"].append(player)
            player.pitch_pos = None

    def move_player(self, player: Player, target_pos: str):
        """Déplace un joueur vers une position cible (incluant BENCH et FIELD)"""
        # 1. Trouver où est le joueur actuellement
        current_pos = None
        if player in self.formation["BENCH"]:
            current_pos = "BENCH"
        else:
            for k, v in self.formation.items():
                if v == player:
                    current_pos = k
                    break
        
        if not current_pos: return False
        
        # 2. Gérer l'alias FIELD (trouver le 1er slot libre)
        if target_pos == "FIELD":
            # Respect strict starter order: try STARTER_SLOTS first
            for slot in STARTER_SLOTS:
                if self.formation.get(slot) is None:
                    target_pos = slot
                    break
            else:
                # Fallback: any non-bench empty slot
                for k, v in self.formation.items():
                    if k != "BENCH" and v is None:
                        target_pos = k
                        break
            if target_pos == "FIELD": # Toujours FIELD ? Aucun slot libre
                return False

        # 3. Gérer la destination
        if target_pos == "BENCH":
            if current_pos != "BENCH":
                self.formation[current_pos] = None
                self.formation["BENCH"].append(player)
                player.pitch_pos = None # Cacher du terrain
        else:
            # Swap ou simple move
            old_occupant = self.formation.get(target_pos)
            self.formation[target_pos] = player
            
            # Mettre à jour pitch_pos visuel (un peu arbitraire mais nécessaire pour pas qu'il disparaisse)
            if not player.pitch_pos:
                player.pitch_pos = (0.5, 0.5)

            if current_pos == "BENCH":
                self.formation["BENCH"].remove(player)
                if old_occupant: 
                    self.formation["BENCH"].append(old_occupant)
                    old_occupant.pitch_pos = None
            else:
                self.formation[current_pos] = old_occupant
                if old_occupant:
                    # L'ancien occupant prend la place (visuelle) du nouveau ? 
                    # On garde les pitch_pos tels quels si on swap sur le terrain
                    pass
        return True

    def reveal_all(self):
        """Révèle tous les ratings de l'équipe"""
        for p in self.players:
            p.reveal()


@dataclass
class GameState:
    """
    État global de la partie.
    """
    mode:           GameMode
    team_rouge:     TeamState = field(default_factory=lambda: TeamState("Équipe Rouge", "rouge"))
    team_bleu:      TeamState = field(default_factory=lambda: TeamState("Équipe Bleue", "bleu"))
    phase:          Phase     = Phase.BUZZ
    manche:         int       = 0          
    current_round:  RoundType = RoundType.DEFENDERS
    buzzer:         str | None = None      
    winner_manche:  str | None = None      
    match_positions: list     = field(default_factory=list)
    current_question: dict    = field(default_factory=dict)
    current_players:  tuple   = field(default_factory=tuple)  
    exchange_done:    bool    = False
    used_player_ids:  set     = field(default_factory=set) # Éviter les répétitions
    question_index:   int     = 0          # Index total des questions posées (pour synchro DB)
    legend_manche:    int     = 0
    rarity_plan:      list    = field(default_factory=list)
    current_rarity_index: int = 0

    # --------------------------------------------------------
    # Accès aux équipes
    # --------------------------------------------------------
    def get_team(self, color: str) -> TeamState:
        return self.team_rouge if color == "rouge" else self.team_bleu

    def get_other_team(self, color: str) -> TeamState:
        return self.team_bleu if color == "rouge" else self.team_rouge

    def init_rarity_plan(self, seed: int, total_slots: int = TOTAL_MANCHES):
        """Create a deterministic rarity order with exact slot counts."""
        rng = random.Random(seed)
        plan = (["COMMON"] * 14) + (["HIGH"] * 3) + (["ELITE"] * 1)
        rng.shuffle(plan)
        self.rarity_plan = plan[:total_slots]
        self.current_rarity_index = 0

    def current_rarity(self) -> str:
        if not self.rarity_plan:
            return "COMMON"
        if self.current_rarity_index >= len(self.rarity_plan):
            return self.rarity_plan[-1]
        return self.rarity_plan[self.current_rarity_index]

    def current_position_label(self) -> str:
        """Label de la position pour la manche actuelle."""
        m = self.manche
        if m < 6:
            return f"Défenseur {m + 1}"
        elif m < 12:
            return f"Milieu {m - 6 + 1}"
        elif m < 16:
            return f"Attaquant {m - 12 + 1}"
        elif m < 18:
            return f"Gardien {m - 16 + 1}"
        else:
            return f"Remplaçant {m - 18 + 1}"

    def current_position(self) -> tuple[str, str]:
        """Retourne (pos_group, pos_label) pour la manche actuelle"""
        label = self.current_position_label()
        m = self.manche
        if m < 6:
            return "DEF", label
        elif m < 12:
            return "MID", label
        elif m < 16:
            return "ATT", label
        elif m < 18:
            return "GK", label
        else:
            return "BENCH", label

    def get_question_type(self) -> QuestionType:
        """Détermine le type de question selon le round et la manche"""
        # Map manche index to question types using new 4-3-3 mapping
        m = self.manche
        if m < 6:
            return QuestionType.MCQ
        elif m < 12:
            # Seulement 1 question d'image (la première des milieux)
            return QuestionType.IMAGE_GUESS if m == 6 else QuestionType.MCQ
        elif m < 16:
            return QuestionType.TRANSFER
        elif m < 18:
            return QuestionType.WHO_AM_I
        else:
            # Bench rounds: default to MCQ
            return QuestionType.MCQ

    # --------------------------------------------------------
    # Transitions d'état
    # --------------------------------------------------------
    def on_buzz(self, color: str):
        self.buzzer = color
        self.phase  = Phase.ANSWER_A

    def on_correct_answer(self) -> str:
        self.winner_manche = self.buzzer
        self.phase = Phase.PICK
        return self.winner_manche

    def on_wrong_answer_first(self) -> bool:
        team = self.get_team(self.buzzer)
        got_red = team.add_jaune()
        self.phase = Phase.ANSWER_B   
        return got_red

    def on_wrong_answer_second(self):
        team = self.get_team(self.buzzer)
        got_red = team.add_jaune()
        return got_red

    def on_pick_player(self, player_idx: int):
        p1, p2 = self.current_players
        winner = self.get_team(self.winner_manche)
        loser  = self.get_other_team(self.winner_manche)

        # Placement déterministe: remplir d'abord les 11 titulaires, puis le banc.
        target_pos = "FIELD"

        # Determine pos_group and within-group index from current manche
        pos_group, _ = self.current_position()
        if self.manche < 6:
            within_index = self.manche
        elif self.manche < 12:
            within_index = self.manche - 6
        elif self.manche < 16:
            within_index = self.manche - 12
        elif self.manche < 18:
            within_index = self.manche - 16
        else:
            within_index = None

        if player_idx == 0:
            winner.add_player(p1, target_pos, pos_group=pos_group, within_index=within_index)
            loser.add_player(p2, target_pos, pos_group=pos_group, within_index=within_index)
        else:
            winner.add_player(p2, target_pos, pos_group=pos_group, within_index=within_index)
            loser.add_player(p1, target_pos, pos_group=pos_group, within_index=within_index)

    def next_manche(self, success: bool = True):
        """
        Passe à la manche suivante.
        Si success=False, on reste sur la même 'manche' (même slot joueur) 
        mais on incrémente question_index pour la synchro.
        """
        if success:
            self.manche += 1
            if self.rarity_plan and self.current_rarity_index < len(self.rarity_plan):
                self.current_rarity_index += 1
        
        self.question_index += 1
        self.buzzer         = None
        self.winner_manche  = None
        self.current_players = ()

        # Logique de changement de round (6 DEF, 6 MID, 4 ATT, 2 GK)
        if self.manche < 6:
            self.current_round = RoundType.DEFENDERS
        elif self.manche < 12:
            self.current_round = RoundType.MIDFIELDERS
        elif self.manche < 16:
            self.current_round = RoundType.ATTACKERS
        elif self.manche < 18:
            self.current_round = RoundType.GOALKEEPER
        else:
            if self.team_rouge.rouges > 0 or self.team_bleu.rouges > 0:
                self.phase = Phase.EXCHANGE
            else:
                self.phase = Phase.REVEAL
            return

        self.phase = Phase.BUZZ

    def start_reveal(self):
        self.team_rouge.reveal_all()
        self.team_bleu.reveal_all()
        self.phase = Phase.REVEAL

    def get_winner(self) -> str | None:
        if self.phase != Phase.REVEAL and self.phase != Phase.FINISHED:
            return None
        r = self.team_rouge.total_rating
        b = self.team_bleu.total_rating
        if r > b:   return "rouge"
        if b > r:   return "bleu"
        return "egalite"

    def progress(self) -> float:
        return self.manche / 18.0

    def __repr__(self):
        return (f"GameState(manche={self.manche+1}/18, round={self.current_round.value}, "
                f"phase={self.phase.name}, buzzer={self.buzzer})")
