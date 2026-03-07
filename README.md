# AHSAN KHOTA — Football Draft Quiz 🏆⚽

Application desktop PyQt5 — Quiz football avec draft de joueurs FIFA.

## Installation

```bash
# 1. Cloner / télécharger le projet
cd ahsan_khota

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Placer le fichier CSV dans data/
# Télécharger depuis : https://www.kaggle.com/datasets/stefanoleone992/ea-sports-fc-24-complete-player-dataset
# Renommer en : male_players.csv
# Placer dans  : data/male_players.csv

# 4. Lancer l'app
python main.py
```

## Tester les données seules

```bash
python game/data.py
```

## Structure du projet

```
ahsan_khota/
├── main.py              # Point d'entrée
├── config.py            # Configuration globale
├── requirements.txt     # Dépendances
├── game/
│   ├── player.py        # Classe Player (rating privé)
│   ├── data.py          # Chargement CSV FIFA
│   └── state.py         # Machine à états du jeu
├── ui/
│   ├── styles.py        # Styles QSS dark football
│   ├── widgets.py       # Widgets réutilisables
│   ├── intro_screen.py  # Écran d'accueil
│   └── buzz_screen.py   # Écran de buzz
├── assets/images/       # Cache images joueurs
└── data/
    └── male_players.csv # Dataset FIFA 24 (Kaggle)
```

## Touches de jeu

| Équipe | Touche Buzz |
|--------|-------------|
| 🔴 Équipe Rouge | Q |
| 🔵 Équipe Bleue | P |

## Phases de développement

- [x] **Phase 1** — Socle PyQt5 + Données FIFA
- [ ] Phase 2 — Logique du jeu complète
- [ ] Phase 3 — IA Questions (Groq) + Images (Pollinations)
- [ ] Phase 4 — Agent IA adversaire (Q-Learning)
- [ ] Phase 5 — Multijoueur en ligne (Supabase)
- [ ] Phase 6 — Polish + animations
