# ============================================================
# config.py — Configuration globale Ahsan Khota
# ============================================================

import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# --- Chemins ---
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
DATA_DIR       = os.path.join(BASE_DIR, "data")
ASSETS_DIR     = os.path.join(BASE_DIR, "assets")
IMAGES_DIR     = os.path.join(ASSETS_DIR, "images")
CSV_PATH       = os.path.join(DATA_DIR, "male_players.csv")

# --- Données FIFA ---
FIFA_VERSION   = 24.0
TOP_PLAYERS    = 500       # charger le top N joueurs par rating

# --- Jeu ---
TOTAL_MANCHES  = 18        # nombre de questions réussies par partie (6 DEF + 6 MID + 4 ATT + 2 GK)
MAX_JAUNES     = 2         # cartons jaunes avant carton rouge (2 jaunes = 1 rouge)

# --- Touches Buzz (clavier) ---
BUZZ_KEY_ROUGE = "Q"       # équipe rouge — côté gauche clavier
BUZZ_KEY_BLEU  = "P"       # équipe bleue  — côté droit clavier

# --- APIs ---
GROQ_API_KEY       = os.getenv("GROQ_API_KEY", "")
SUPABASE_URL       = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY  = os.getenv("SUPABASE_ANON_KEY", "")
MISTRAL_API_KEY    = os.getenv("MISTRAL_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
# Fallback conservé pour compatibilité avec l'ancien nom de variable
SUPABASE_KEY       = os.getenv("SUPABASE_KEY", SUPABASE_ANON_KEY)

# --- UI ---
APP_TITLE      = "AHSAN KHOTA — Football Draft Quiz"
APP_WIDTH      = 1280
APP_HEIGHT     = 800

# --- Couleurs (QSS) ---
COLOR_BG       = "#0a0a0a"
COLOR_GREEN    = "#00e676"
COLOR_ROUGE    = "#ff4444"
COLOR_BLEU     = "#4488ff"
COLOR_JAUNE    = "#ffc107"
COLOR_GRAY     = "#888888"
COLOR_WHITE    = "#ffffff"
COLOR_CARD_BG  = "#1a1a1a"
COLOR_BORDER   = "#2a2a2a"
