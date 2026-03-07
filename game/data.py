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

# Groupes de positions pour le jeu
POSITION_GROUPS = {
    "GK":  ["GK"],
    "DEF": ["CB", "LB", "RB", "LWB", "RWB"],
    "MID": ["CDM", "CM", "CAM", "LM", "RM"],
    "ATT": ["ST", "CF", "LW", "RW", "LF", "RF"],
}

# 11 positions pour une équipe complète (1 par manche)
MATCH_POSITIONS = [
    ("GK",  "Gardien (GK)"),
    ("DEF", "Défenseur (CB)"),
    ("DEF", "Défenseur (RB)"),
    ("DEF", "Défenseur (LB)"),
    ("MID", "Milieu Défensif (CDM)"),
    ("MID", "Milieu Central (CM)"),
    ("MID", "Milieu Central (CM)"),
    ("ATT", "Milieu Offensif (CAM)"),
    ("ATT", "Ailier Gauche (LW)"),
    ("ATT", "Ailier Droit (RW)"),
    ("ATT", "Attaquant (ST)"),
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
            "fifa_version", "short_name", "long_name",
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

    def get_pair(self, position_group: str) -> tuple[Player, Player]:
        """
        Retourne 2 joueurs aléatoires d'un groupe de position.
        Les ratings sont chargés mais CACHÉS dans la classe Player.
        """
        pool = self.players_by_group.get(position_group, [])

        if len(pool) < 2:
            # Fallback sur tous les joueurs si groupe vide
            pool = [p for players in self.players_by_group.values()
                    for p in players]

        selected = random.sample(pool, 2)
        return Player(selected[0]), Player(selected[1])

    def get_match_positions(self) -> list[tuple[str, str]]:
        """Retourne les 11 positions du match (mélangées légèrement)"""
        positions = MATCH_POSITIONS.copy()
        # Mélanger légèrement pour varier l'ordre (garder GK en premier)
        gk = positions[0]
        rest = positions[1:]
        random.shuffle(rest)
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
