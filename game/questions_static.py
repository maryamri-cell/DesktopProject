# ============================================================
# game/questions_static.py — Banque de 50+ questions football
# Fallback si Groq API hors ligne (Phase 3)
# ============================================================

QUESTIONS_STATIC = [
    # ─────────────────────────────────────────────────────
    # FACILE (easy)
    # ─────────────────────────────────────────────────────
    {
        "question": "Combien de fois le Brésil a-t-il remporté la Coupe du Monde ?",
        "options": ["3", "4", "5", "6"],
        "answer": "5",
        "difficulty": "easy"
    },
    {
        "question": "Quel joueur détient le record de Ballons d'Or ?",
        "options": ["Cristiano Ronaldo", "Messi", "Zidane", "Ronaldinho"],
        "answer": "Messi",
        "difficulty": "easy"
    },
    {
        "question": "Dans quel pays joue le club Real Madrid ?",
        "options": ["Portugal", "France", "Espagne", "Italie"],
        "answer": "Espagne",
        "difficulty": "easy"
    },
    {
        "question": "Quelle nation a remporté la Coupe du Monde 2022 ?",
        "options": ["France", "Brésil", "Angleterre", "Argentine"],
        "answer": "Argentine",
        "difficulty": "easy"
    },
    {
        "question": "Combien de joueurs composent une équipe sur le terrain ?",
        "options": ["10", "11", "12", "9"],
        "answer": "11",
        "difficulty": "easy"
    },
    {
        "question": "Quel pays a organisé la Coupe du Monde 1998 ?",
        "options": ["Allemagne", "Italie", "France", "Espagne"],
        "answer": "France",
        "difficulty": "easy"
    },
    {
        "question": "De quelle couleur est le carton d'expulsion au football ?",
        "options": ["Jaune", "Rouge", "Vert", "Bleu"],
        "answer": "Rouge",
        "difficulty": "easy"
    },
    {
        "question": "Quelle est la durée réglementaire d'un match de football ?",
        "options": ["80 minutes", "90 minutes", "100 minutes", "120 minutes"],
        "answer": "90 minutes",
        "difficulty": "easy"
    },
    {
        "question": "Quel trophée est remis au vainqueur de la Coupe du Monde ?",
        "options": ["Ballon d'Or", "Trophée Jules Rimet", "Coupe Henri Delaunay", "Trophée FIFA"],
        "answer": "Trophée FIFA",
        "difficulty": "easy"
    },
    {
        "question": "Dans quel sport Pelé est-il une légende ?",
        "options": ["Basketball", "Tennis", "Football", "Rugby"],
        "answer": "Football",
        "difficulty": "easy"
    },
    {
        "question": "Quel pays a remporté la première Coupe du Monde en 1930 ?",
        "options": ["Brésil", "Argentine", "Uruguay", "Italie"],
        "answer": "Uruguay",
        "difficulty": "easy"
    },
    {
        "question": "Combien de remplacements sont autorisés dans un match officiel FIFA ?",
        "options": ["3", "4", "5", "6"],
        "answer": "5",
        "difficulty": "easy"
    },
    {
        "question": "Quelle est la position du joueur qui garde les buts ?",
        "options": ["Défenseur", "Milieu", "Attaquant", "Gardien"],
        "answer": "Gardien",
        "difficulty": "easy"
    },
    {
        "question": "Quel continent organise la Copa América ?",
        "options": ["Europe", "Afrique", "Amérique du Sud", "Asie"],
        "answer": "Amérique du Sud",
        "difficulty": "easy"
    },
    {
        "question": "De quel pays est originaire Cristiano Ronaldo ?",
        "options": ["Espagne", "Brésil", "Portugal", "France"],
        "answer": "Portugal",
        "difficulty": "easy"
    },
    {
        "question": "Quel club joue au stade Santiago Bernabéu ?",
        "options": ["FC Barcelone", "Atletico Madrid", "Real Madrid", "Séville FC"],
        "answer": "Real Madrid",
        "difficulty": "easy"
    },
    {
        "question": "Quelle compétition oppose les meilleurs clubs européens chaque année ?",
        "options": ["Copa América", "Ligue des Champions", "Coupe du Monde", "Europa League"],
        "answer": "Ligue des Champions",
        "difficulty": "easy"
    },

    # ─────────────────────────────────────────────────────
    # MOYEN (medium)
    # ─────────────────────────────────────────────────────
    {
        "question": "Quel stade est surnommé 'Theatre of Dreams' ?",
        "options": ["Anfield", "Wembley", "Old Trafford", "Camp Nou"],
        "answer": "Old Trafford",
        "difficulty": "medium"
    },
    {
        "question": "Qui est le meilleur buteur de l'histoire de la Ligue des Champions ?",
        "options": ["Messi", "Raul", "Benzema", "Cristiano Ronaldo"],
        "answer": "Cristiano Ronaldo",
        "difficulty": "medium"
    },
    {
        "question": "Quel club a remporté le plus de Ligues des Champions ?",
        "options": ["Bayern Munich", "Liverpool", "Real Madrid", "Barcelona"],
        "answer": "Real Madrid",
        "difficulty": "medium"
    },
    {
        "question": "Qui a marqué le 'But de la main de Dieu' en 1986 ?",
        "options": ["Pelé", "Zidane", "Maradona", "Ronaldo"],
        "answer": "Maradona",
        "difficulty": "medium"
    },
    {
        "question": "Quel pays a remporté l'Euro 2020 (joué en 2021) ?",
        "options": ["Angleterre", "Italie", "Espagne", "France"],
        "answer": "Italie",
        "difficulty": "medium"
    },
    {
        "question": "Quel joueur est surnommé 'El Fenómeno' ?",
        "options": ["Ronaldinho", "Ronaldo Nazário", "Cristiano Ronaldo", "Zidane"],
        "answer": "Ronaldo Nazário",
        "difficulty": "medium"
    },
    {
        "question": "Dans quel club Zinédine Zidane a-t-il terminé sa carrière de joueur ?",
        "options": ["Juventus", "Bordeaux", "Real Madrid", "Marseille"],
        "answer": "Real Madrid",
        "difficulty": "medium"
    },
    {
        "question": "Quel pays africain a atteint les quarts de finale de la Coupe du Monde 2022 ?",
        "options": ["Sénégal", "Ghana", "Maroc", "Cameroun"],
        "answer": "Maroc",
        "difficulty": "medium"
    },
    {
        "question": "Combien de Ballons d'Or Cristiano Ronaldo a-t-il remportés ?",
        "options": ["4", "5", "6", "7"],
        "answer": "5",
        "difficulty": "medium"
    },
    {
        "question": "Quel gardien a remporté le trophée Lev Yachine au Mondial 2022 ?",
        "options": ["Lloris", "Bounou", "E. Martínez", "Livakovic"],
        "answer": "E. Martínez",
        "difficulty": "medium"
    },
    {
        "question": "Quel club anglais est surnommé 'The Gunners' ?",
        "options": ["Chelsea", "Arsenal", "Tottenham", "Manchester United"],
        "answer": "Arsenal",
        "difficulty": "medium"
    },
    {
        "question": "Quel joueur français a inscrit un triplé en finale de Coupe du Monde 2022 ?",
        "options": ["Griezmann", "Mbappé", "Giroud", "Dembélé"],
        "answer": "Mbappé",
        "difficulty": "medium"
    },
    {
        "question": "Quel club a remporté la Premier League le plus de fois ?",
        "options": ["Liverpool", "Chelsea", "Manchester United", "Arsenal"],
        "answer": "Manchester United",
        "difficulty": "medium"
    },
    {
        "question": "Dans quel pays se trouve le stade Maracanã ?",
        "options": ["Argentine", "Mexique", "Brésil", "Colombie"],
        "answer": "Brésil",
        "difficulty": "medium"
    },
    {
        "question": "Quel joueur est connu pour sa célébration 'SIUUU' ?",
        "options": ["Messi", "Neymar", "Cristiano Ronaldo", "Mbappé"],
        "answer": "Cristiano Ronaldo",
        "difficulty": "medium"
    },
    {
        "question": "Quelle équipe nationale est surnommée 'La Roja' ?",
        "options": ["Portugal", "Chili", "Espagne", "Colombie"],
        "answer": "Espagne",
        "difficulty": "medium"
    },
    {
        "question": "Quel club italien a remporté le plus de titres de Serie A ?",
        "options": ["AC Milan", "Inter Milan", "Juventus", "AS Roma"],
        "answer": "Juventus",
        "difficulty": "medium"
    },
    {
        "question": "Qui a été le sélectionneur de la France lors de la victoire au Mondial 2018 ?",
        "options": ["Zidane", "Deschamps", "Blanc", "Domenech"],
        "answer": "Deschamps",
        "difficulty": "medium"
    },
    {
        "question": "Quel joueur brésilien a remporté le Ballon d'Or en 2007 ?",
        "options": ["Ronaldinho", "Kaká", "Rivaldo", "Ronaldo"],
        "answer": "Kaká",
        "difficulty": "medium"
    },
    {
        "question": "Combien d'étoiles figurent sur le maillot du Brésil (titres mondiaux) ?",
        "options": ["3", "4", "5", "6"],
        "answer": "5",
        "difficulty": "medium"
    },

    # ─────────────────────────────────────────────────────
    # DIFFICILE (hard)
    # ─────────────────────────────────────────────────────
    {
        "question": "En quelle année a été fondé le FC Barcelone ?",
        "options": ["1895", "1899", "1902", "1910"],
        "answer": "1899",
        "difficulty": "hard"
    },
    {
        "question": "Quel joueur détient le record de buts en une année civile (91 buts en 2012) ?",
        "options": ["Cristiano Ronaldo", "Pelé", "Messi", "Gerd Müller"],
        "answer": "Messi",
        "difficulty": "hard"
    },
    {
        "question": "Quel club a remporté la première édition de la Ligue des Champions en 1956 ?",
        "options": ["AC Milan", "Real Madrid", "Benfica", "Barcelona"],
        "answer": "Real Madrid",
        "difficulty": "hard"
    },
    {
        "question": "Combien de buts Pelé a-t-il officiellement marqués en carrière ?",
        "options": ["643", "757", "767", "1281"],
        "answer": "767",
        "difficulty": "hard"
    },
    {
        "question": "Quel pays a remporté la première CAN (Coupe d'Afrique des Nations) en 1957 ?",
        "options": ["Ghana", "Cameroun", "Égypte", "Nigeria"],
        "answer": "Égypte",
        "difficulty": "hard"
    },
    {
        "question": "Quel joueur a le plus de sélections en équipe de France ?",
        "options": ["Zidane", "Thuram", "Henry", "Hugo Lloris"],
        "answer": "Hugo Lloris",
        "difficulty": "hard"
    },
    {
        "question": "En quelle année le VAR a-t-il été utilisé pour la première fois en Coupe du Monde ?",
        "options": ["2014", "2016", "2018", "2022"],
        "answer": "2018",
        "difficulty": "hard"
    },
    {
        "question": "Quel club a réalisé le 'Triplé' (championnat, coupe, C1) en 2009 ?",
        "options": ["Real Madrid", "Manchester United", "FC Barcelone", "Bayern Munich"],
        "answer": "FC Barcelone",
        "difficulty": "hard"
    },
    {
        "question": "Quel est le plus grand stade de football au monde par capacité ?",
        "options": ["Camp Nou", "Wembley", "Rungrado May Day", "Maracanã"],
        "answer": "Rungrado May Day",
        "difficulty": "hard"
    },
    {
        "question": "Quel joueur africain a remporté le Ballon d'Or en 1995 ?",
        "options": ["Samuel Eto'o", "Didier Drogba", "George Weah", "Jay-Jay Okocha"],
        "answer": "George Weah",
        "difficulty": "hard"
    },
    {
        "question": "Combien de Coupes du Monde l'Allemagne a-t-elle remportées ?",
        "options": ["3", "4", "5", "2"],
        "answer": "4",
        "difficulty": "hard"
    },
    {
        "question": "Quel joueur a marqué le but le plus rapide en Coupe du Monde (11 secondes) ?",
        "options": ["Ronaldo", "Hakan Şükür", "Mbappé", "Klose"],
        "answer": "Hakan Şükür",
        "difficulty": "hard"
    },
    {
        "question": "Quel club espagnol est basé dans le Pays Basque et n'aligne que des joueurs basques ?",
        "options": ["Real Sociedad", "Athletic Bilbao", "Eibar", "Osasuna"],
        "answer": "Athletic Bilbao",
        "difficulty": "hard"
    },
    {
        "question": "En quelle année la règle du hors-jeu a-t-elle été introduite dans les lois du football ?",
        "options": ["1863", "1866", "1886", "1925"],
        "answer": "1866",
        "difficulty": "hard"
    },
    {
        "question": "Quel est le record de buts inscrits par un joueur en une seule édition de Coupe du Monde ?",
        "options": ["11", "13", "15", "9"],
        "answer": "13",
        "difficulty": "hard"
    },
    {
        "question": "Quel gardien italien a remporté le Ballon d'Or en 2006 ?",
        "options": ["Buffon", "Cannavaro", "Pirlo", "Totti"],
        "answer": "Cannavaro",
        "difficulty": "hard"
    },
]


def get_questions(n: int = 11, shuffle: bool = True) -> list[dict]:
    """
    Retourne N questions depuis la banque statique.
    Mélange les questions si shuffle=True.
    Garantit un mix de difficultés : ~40% easy, ~40% medium, ~20% hard.
    """
    import random

    easy   = [q for q in QUESTIONS_STATIC if q["difficulty"] == "easy"]
    medium = [q for q in QUESTIONS_STATIC if q["difficulty"] == "medium"]
    hard   = [q for q in QUESTIONS_STATIC if q["difficulty"] == "hard"]

    if shuffle:
        random.shuffle(easy)
        random.shuffle(medium)
        random.shuffle(hard)

    # Répartition pour N questions
    n_easy   = max(1, int(n * 0.4))
    n_hard   = max(1, int(n * 0.2))
    n_medium = n - n_easy - n_hard

    selected = easy[:n_easy] + medium[:n_medium] + hard[:n_hard]

    # Compléter si pas assez
    all_q = easy + medium + hard
    while len(selected) < n and all_q:
        q = all_q.pop()
        if q not in selected:
            selected.append(q)

    if shuffle:
        random.shuffle(selected)

    return selected[:n]


# ============================================================
# TEST
# ============================================================
if __name__ == "__main__":
    print(f"Total questions en banque : {len(QUESTIONS_STATIC)}")
    easy   = sum(1 for q in QUESTIONS_STATIC if q["difficulty"] == "easy")
    medium = sum(1 for q in QUESTIONS_STATIC if q["difficulty"] == "medium")
    hard   = sum(1 for q in QUESTIONS_STATIC if q["difficulty"] == "hard")
    print(f"  Easy: {easy} | Medium: {medium} | Hard: {hard}")

    print("\n--- 11 questions pour une partie ---")
    for i, q in enumerate(get_questions(11), 1):
        print(f"  {i:2d}. [{q['difficulty']:6s}] {q['question'][:60]}...")
