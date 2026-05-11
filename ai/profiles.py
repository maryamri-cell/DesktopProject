# ============================================================
# ai/profiles.py — Profils de difficulté pour l'IA
# ============================================================

EASY = {
    "name": "EASY",
    "base_reaction_ms": 3500,
    "jitter_ms": 1000,
    "accuracy": {
        "MCQ": 0.40,
        "IMAGE_GUESS": 0.25,
        "TRANSFER_TRIVIA": 0.30,
        "WHO_AM_I": 0.30,
    },
    "knowledge_domains": {
        "EUROPEAN_CLUBS": 0.40,
        "PREMIER_LEAGUE": 0.35,
        "INTERNATIONAL": 0.30,
        "HISTORICAL": 0.15,
        "LEGENDS": 0.20,
    },
    "buzz_aggressiveness": 0.3,
    "skip_tendency": 0.4,
    "pick_error_margin": 0.4, # Probabilité de se tromper sur la force d'un joueur
}

MEDIUM = {
    "name": "MEDIUM",
    "base_reaction_ms": 2500,
    "jitter_ms": 600,
    "accuracy": {
        "MCQ": 0.65,
        "IMAGE_GUESS": 0.50,
        "TRANSFER_TRIVIA": 0.55,
        "WHO_AM_I": 0.50,
    },
    "knowledge_domains": {
        "EUROPEAN_CLUBS": 0.70,
        "PREMIER_LEAGUE": 0.65,
        "INTERNATIONAL": 0.60,
        "HISTORICAL": 0.40,
        "LEGENDS": 0.50,
    },
    "buzz_aggressiveness": 0.6,
    "skip_tendency": 0.2,
    "pick_error_margin": 0.2,
}

HARD = {
    "name": "HARD",
    "base_reaction_ms": 1600,
    "jitter_ms": 300,
    "accuracy": {
        "MCQ": 0.88,
        "IMAGE_GUESS": 0.80,
        "TRANSFER_TRIVIA": 0.85,
        "WHO_AM_I": 0.80,
    },
    "knowledge_domains": {
        "EUROPEAN_CLUBS": 0.90,
        "PREMIER_LEAGUE": 0.90,
        "INTERNATIONAL": 0.85,
        "HISTORICAL": 0.65,
        "LEGENDS": 0.80,
    },
    "buzz_aggressiveness": 0.85,
    "skip_tendency": 0.05,
    "pick_error_margin": 0.08,
}

PROFILES = {
    "easy": EASY,
    "medium": MEDIUM,
    "hard": HARD,
}
