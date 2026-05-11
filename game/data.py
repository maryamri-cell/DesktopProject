# ============================================================
# game/data.py — Chargement et gestion des données FIFA
# ============================================================

import pandas as pd
import random
import os
import sys

# Ajouter le dossier racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CSV_PATH, FIFA_VERSION, TOP_PLAYERS
from game.player import Player


def _pair_metadata_distance(p1: dict, p2: dict) -> int:
    score = 0
    if p1.get("club_name") != p2.get("club_name"):
        score += 1
    if p1.get("nationality_name") != p2.get("nationality_name"):
        score += 1
    if p1.get("player_positions") != p2.get("player_positions"):
        score += 1
    if p1.get("age") != p2.get("age"):
        score += 1
    return score

# Groupes de positions pour le jeu
POSITION_GROUPS = {
    "GK":  ["GK"],
    "DEF": ["CB", "LB", "RB", "LWB", "RWB"],
    "MID": ["CDM", "CM", "CAM", "LM", "RM"],
    "ATT": ["ST", "CF", "LW", "RW", "LF", "RF"],
}

# 18 positions pour une équipe complète (6 DEF, 6 MID, 4 ATT, 2 GK)
MATCH_POSITIONS = [
    ("DEF", "Défenseur (CB)"), ("DEF", "Défenseur (CB)"), ("DEF", "Défenseur (CB)"),
    ("DEF", "Défenseur (LB)"), ("DEF", "Défenseur (RB)"), ("DEF", "Défenseur (CB)"),
    ("MID", "Milieu (CDM)"), ("MID", "Milieu (CM)"), ("MID", "Milieu (CM)"),
    ("MID", "Milieu (CAM)"), ("MID", "Milieu (LM)"), ("MID", "Milieu (RM)"),
    ("ATT", "Attaquant (LW)"), ("ATT", "Attaquant (RW)"), ("ATT", "Attaquant (ST)"),
    ("ATT", "Attaquant (ST)"),
    ("GK",  "Gardien (GK)"), ("GK",  "Gardien (GK)"),
]


class GameData:
    """
    Charge le CSV FIFA une seule fois au démarrage.
    Fournit des paires de joueurs pour chaque manche.
    """

    def __init__(self):
        self.players_by_group: dict[str, list[dict]] = {}
        self._load_csv()

    def _load_csv(self):
        """Charge et filtre le CSV FIFA 24"""
        print(f"[GameData] Chargement de {CSV_PATH} ...")

        if not os.path.exists(CSV_PATH):
            raise FileNotFoundError(
                f"Fichier CSV introuvable : {CSV_PATH}\n"
                f"Télécharge-le depuis Kaggle et place-le dans data/"
            )

        # Lire seulement les colonnes nécessaires
        cols_needed = [
            "player_id", "fifa_version", "short_name", "long_name",
            "overall", "player_positions", "club_name",
            "nationality_name", "age"
        ]

        df = pd.read_csv(CSV_PATH, usecols=cols_needed, low_memory=False)

        # Filtrer FIFA 24
        df24 = df[df["fifa_version"] == FIFA_VERSION].copy()

        # Prendre le top N joueurs par rating
        df24 = df24.nlargest(TOP_PLAYERS, "overall")

        # Nettoyer les valeurs manquantes
        df24 = df24.fillna({
            "short_name":        "Inconnu",
            "long_name":         "Inconnu",
            "overall":           70,
            "player_positions":  "CM",
            "club_name":         "Sans club",
            "nationality_name":  "Inconnu",
            "age":               25,
        })
        df24["overall"] = df24["overall"].astype(int)
        df24["age"]     = df24["age"].astype(int)

        # Grouper par type de position
        for group, positions in POSITION_GROUPS.items():
            mask = df24["player_positions"].apply(
                lambda p: any(pos in str(p).split(",")[0].strip()
                              for pos in positions)
            )
            self.players_by_group[group] = df24[mask].to_dict("records")

        total = sum(len(v) for v in self.players_by_group.values())
        print(f"[GameData] {total} joueurs chargés :")
        for group, players in self.players_by_group.items():
            print(f"  {group}: {len(players)} joueurs")

    def get_similar_pair(self, position_group: str, excluded_ids: set = None, 
                         rating_diff_max: int = 20, seed: int = None, is_legend: bool = False,
                         rarity_tier: str | None = None) -> tuple[Player, Player]:
        """
        Retourne 2 joueurs.
        Si is_legend=True, cherche des joueurs avec un rating très élevé (90+).
        """
        import random as rd
        local_random = rd.Random(seed if seed is not None else 0)

        excluded_ids = excluded_ids or set()
        pool = self.players_by_group.get(position_group, [])
        
        # Filtrer et TRIER par ID pour garantir le même point de départ avant le shuffle
        pool = [p for p in pool if p["player_id"] not in excluded_ids]
        pool.sort(key=lambda x: x["player_id"])

        if len(pool) < 2:
            return self.get_pair(position_group, excluded_ids, seed=seed)

        tier = (rarity_tier or ("ELITE" if is_legend else "COMMON")).upper()

        def in_tier(entry: dict, tier_name: str) -> bool:
            rating = int(entry.get("overall", 0))
            if tier_name == "COMMON":
                return 70 <= rating <= 80
            if tier_name == "HIGH":
                return 80 <= rating <= 90
            if tier_name == "ELITE":
                return rating > 90
            return True

        def pair_ok(p1: dict, p2: dict, require_common: bool = False) -> bool:
            if p1["player_id"] == p2["player_id"]:
                return False
            if abs(int(p1.get("overall", 0)) - int(p2.get("overall", 0))) < 5:
                return False
            if require_common and not (70 <= int(p2.get("overall", 0)) <= 80):
                return False
            return _pair_metadata_distance(p1, p2) >= 1

        if tier == "ELITE":
            elite_pool = [p for p in pool if in_tier(p, "ELITE")]
            common_pool = [p for p in pool if in_tier(p, "COMMON")]
            if not common_pool:
                common_pool = [p for p in pool if p not in elite_pool]
            best_pair = None
            best_score = -1
            for p1 in elite_pool:
                for p2 in common_pool:
                    if pair_ok(p1, p2, require_common=True):
                        score = abs(int(p1.get("overall", 0)) - int(p2.get("overall", 0))) * 10 + _pair_metadata_distance(p1, p2)
                        if score > best_score:
                            best_score = score
                            best_pair = (p1, p2)
            if best_pair:
                return Player(best_pair[0]), Player(best_pair[1])

        tier_pool = [p for p in pool if in_tier(p, tier)]
        if len(tier_pool) < 2:
            tier_pool = pool[:]

        ordered = tier_pool[:]
        local_random.shuffle(ordered)
        best_pair = None
        best_score = -1
        for i, p1 in enumerate(ordered):
            for p2 in ordered[i + 1:]:
                if pair_ok(p1, p2):
                    score = abs(int(p1.get("overall", 0)) - int(p2.get("overall", 0))) * 10 + _pair_metadata_distance(p1, p2)
                    if score > best_score:
                        best_score = score
                        best_pair = (p1, p2)
            if best_pair and best_score >= 50:
                break

        if best_pair:
            return Player(best_pair[0]), Player(best_pair[1])

        if len(pool) >= 2:
            p1_data, p2_data = pool[0], pool[1]
            if int(p1_data.get("overall", 0)) < int(p2_data.get("overall", 0)):
                return Player(p1_data), Player(p2_data)
            return Player(p2_data), Player(p1_data)

        fallback = self.players_by_group.get(position_group, []) or [p for players in self.players_by_group.values() for p in players]
        if len(fallback) < 2:
            raise RuntimeError(f"Pool de joueurs insuffisant pour le groupe {position_group}")
        fallback.sort(key=lambda x: x["player_id"])
        p1_data, p2_data = fallback[0], fallback[1]
        return Player(p1_data), Player(p2_data)

    def get_pair(self, position_group: str, excluded_ids: set = None, seed: int = None) -> tuple[Player, Player]:
        """
        Retourne 2 joueurs aléatoires de manière déterministe (fallback).
        """
        import random as rd
        local_random = rd.Random(seed if seed is not None else 0)

        excluded_ids = excluded_ids or set()
        pool = self.players_by_group.get(position_group, [])
        
        pool = [p for p in pool if p["player_id"] not in excluded_ids]
        pool.sort(key=lambda x: x["player_id"])

        if len(pool) < 2:
            pool = self.players_by_group.get(position_group, [])
            pool.sort(key=lambda x: x["player_id"])

        selected = local_random.sample(pool, min(len(pool), 2))
        if len(selected) < 2:
             all_pool = [p for players in self.players_by_group.values() for p in players]
             all_pool.sort(key=lambda x: x["player_id"])
             selected = local_random.sample(all_pool, 2)
             
        return Player(selected[0]), Player(selected[1])

    def get_match_positions(self, seed: int | None = None) -> list[tuple[str, str]]:
        """Retourne les 11 positions du match (mélangées légèrement)"""
        positions = MATCH_POSITIONS.copy()
        # Mélanger légèrement pour varier l'ordre (garder GK en premier)
        gk = positions[0]
        rest = positions[1:]
        local_random = random.Random(seed if seed is not None else 0)
        local_random.shuffle(rest)
        return [gk] + rest


# ============================================================
# TEST — exécuter directement pour tester
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("TEST GameData")
    print("=" * 50)

    data = GameData()

    print("\n--- Test get_pair() ---")
    for group in ["GK", "DEF", "MID", "ATT"]:
        p1, p2 = data.get_pair(group)
        print(f"\n[{group}]")
        print(f"  Joueur 1 : {p1.name} | {p1.club} | Rating: {p1.get_rating()}")
        print(f"  Joueur 2 : {p2.name} | {p2.club} | Rating: {p2.get_rating()}")

    print("\n--- Test reveal() ---")
    p1, p2 = data.get_pair("ATT")
    print(f"Avant révélation : {p1.name} → rating = {p1.get_rating()}")
    p1.reveal()
    print(f"Après révélation : {p1.name} → rating = {p1.get_rating()}")

    print("\n--- Test get_match_positions() ---")
    positions = data.get_match_positions()
    for i, (group, label) in enumerate(positions, 1):
        print(f"  Manche {i:2d} : {label}")

    print("\n✅ Tests OK !")
