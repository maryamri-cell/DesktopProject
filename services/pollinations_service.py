# ============================================================
# services/pollinations_service.py — Service d'images Pollinations.ai
# ============================================================

import requests
from urllib.parse import quote

class PollinationsService:
    """
    Simplement génère des URLs Pollinations.ai basées sur des prompts.
    Permet de générer des parties de joueurs (cheveux, yeux, barbe).
    """

    @staticmethod
    def get_image_url(prompt: str, width: int = 1024, height: int = 1024, seed: int = None) -> str:
        """
        Génère une URL d'image Pollinations.ai.
        """
        clean_prompt = quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width={width}&height={height}"
        if seed is not None:
            url += f"&seed={seed}"
        return url

    @staticmethod
    def get_player_part_prompt(player_name: str, part: str) -> str:
        """
        Construit un prompt optimisé pour une partie spécifique du corps d'un joueur.
        """
        parts_fr_to_en = {
            "cheveux": "hairstyle and hair details",
            "yeux": "eyes close up, high detail",
            "barbe": "beard and facial hair",
            "tatouage": "specific arm tattoos",
            "chaussures": "football boots",
            "visage": "face close up"
        }
        
        part_en = parts_fr_to_en.get(part.lower(), part)
        return f"Hyper-realistic close up of {player_name}'s {part_en}, professional photography, high resolution, soft lighting, 8k"

# Test rapide
if __name__ == "__main__":
    p = PollinationsService()
    url = p.get_image_url(p.get_player_part_prompt("Lionel Messi", "yeux"))
    print(f"URL de test: {url}")
