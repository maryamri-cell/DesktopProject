# ============================================================
# config.py — Configuration globale Ahsan Khota
# ============================================================

import os

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
TOTAL_MANCHES  = 11        # nombre de questions par partie
MAX_JAUNES     = 3         # cartons jaunes avant carton rouge

# --- Touches Buzz (clavier) ---
BUZZ_KEY_ROUGE = "Q"       # équipe rouge — côté gauche clavier
BUZZ_KEY_BLEU  = "P"       # équipe bleue  — côté droit clavier

# --- APIs (à remplir plus tard) ---
GROQ_API_KEY      = ""     # console.groq.com
SUPABASE_URL      = ""     # settings → API → Project URL
SUPABASE_KEY      = ""     # settings → API → Secret key

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
