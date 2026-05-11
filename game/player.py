# ============================================================
# game/player.py — Classe Player avec rating caché
# ============================================================


class Player:
    """
    Représente un joueur FIFA.
    Le rating est PRIVÉ — invisible jusqu'à la révélation finale.
    """

    def __init__(self, data: dict):
        # Informations visibles pendant le jeu
        self.name       = str(data.get("short_name", "Inconnu"))
        self.full_name  = str(data.get("long_name",  self.name))
        self.club       = str(data.get("club_name",  "Inconnu"))
        self.nation     = str(data.get("nationality_name", "Inconnu"))
        self.age        = int(data.get("age", 0))
        self.position   = str(data.get("player_positions", "??")).split(",")[0].strip()
        self.player_id  = int(data.get("player_id", 0))
        self.image_path = None   
        self.photo_path = None   # Chemin local vers la photo téléchargée
        self.pitch_pos  = None   # (x_ratio, y_ratio) pour le placement libre
        self.reputation = int(data.get("international_reputation", 1))
        self.overall_reputation = int(data.get("overall", 0)) # Used for "fame" proxy

        # Rating CACHÉ — attribut privé Python
        self.__rating   = int(data.get("overall", 0))
        self.revealed   = False  # False pendant tout le jeu

    def get_rating(self) -> int | str:
        """Retourne le rating UNIQUEMENT si révélé, sinon '?'"""
        if self.revealed:
            return self.__rating
        return "?"

    def reveal(self):
        """Appelé UNIQUEMENT à la fin du jeu (révélation finale)"""
        self.revealed = True

    def get_rating_force(self) -> int:
        """Usage interne uniquement (calcul score, agent IA) — jamais affiché"""
        return self.__rating

    def to_display_dict(self) -> dict:
        """Données affichables dans l'UI (sans le rating si caché)"""
        return {
            "name":     self.name,
            "club":     self.club,
            "nation":   self.nation,
            "age":      self.age,
            "position": self.position,
            "rating":   self.get_rating(),   # "?" si pas révélé
        }

    def __repr__(self):
        rating_str = str(self.__rating) if self.revealed else "?"
        return f"Player({self.name} | {self.club} | OVR:{rating_str})"
