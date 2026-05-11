# ============================================================
# game/questions_static.py — Banque de questions structurée
# ============================================================

import random

ROUND_1_DEFENSEURS = [
    {
        "type": "standard",
        "question": "Quel pays a remporté le plus de Coupes du Monde ?",
        "options": ["Allemagne", "Brésil", "Italie", "Argentine"],
        "answer": "Brésil"
    },
    {
        "type": "standard",
        "question": "Quel joueur détient le record du nombre de Ballons d'Or ?",
        "options": ["Cristiano Ronaldo", "Lionel Messi", "Michel Platini", "Johan Cruyff"],
        "answer": "Lionel Messi"
    },
    {
        "type": "standard",
        "question": "Quel est le plus grand stade d'Europe en termes de capacité ?",
        "options": ["Wembley Stadium", "Santiago Bernabéu", "Camp Nou", "San Siro"],
        "answer": "Camp Nou"
    },
    {
        "type": "standard",
        "question": "Quelle équipe a remporté l'Euro 2004 à la surprise générale ?",
        "options": ["Portugal", "Grèce", "Danemark", "République Tchèque"],
        "answer": "Grèce"
    },
    {
        "type": "standard",
        "question": "Quel joueur a marqué le but le plus rapide de l'histoire de la Coupe du Monde ?",
        "options": ["Pelé", "Kylian Mbappé", "Hakan Şükür", "Ronaldo Nazário"],
        "answer": "Hakan Şükür"
    }
]

ROUND_2_MILIEUX = [
    {
        "type": "standard",
        "question": "Un joueur chauve avec un maillot bleu frappé du numéro 10 donne un coup de tête dans le torse d'un défenseur italien en maillot blanc lors d'une finale de Coupe du Monde. Qui est ce joueur ?",
        "options": ["Thierry Henry", "Zinédine Zidane", "Patrick Vieira", "Fabien Barthez"],
        "answer": "Zinédine Zidane"
    },
    {
        "type": "transfer",
        "question": "Malmö FF ➔ Ajax ➔ Juventus ➔ Inter Milan ➔ FC Barcelone ➔ AC Milan ➔ PSG ➔ Manchester United ➔ LA Galaxy ➔ AC Milan. \nQui suis-je ?",
        "options": ["Edinson Cavani", "Zlatan Ibrahimović", "Thiago Silva", "Henrik Larsson"],
        "answer": "Zlatan Ibrahimović"
    },
    {
        "type": "transfer",
        "question": "River Plate ➔ Corinthians ➔ West Ham ➔ Carlos Tevez ➔ Manchester United ➔ Manchester City ➔ Juventus ➔ Boca Juniors. \nQui suis-je ?",
        "options": ["Sergio Agüero", "Carlos Tevez", "Gonzalo Higuaín", "Angel Di Maria"],
        "answer": "Carlos Tevez"
    },
    {
        "type": "whoami",
        "question": "🔎 Indice 1 : J'ai remporté la Coupe du Monde 2018 avec l'équipe de France.\n🔎 Indice 2 : On me surnomme 'La Pioche'.\n🔎 Indice 3 : J'ai joué pour Manchester United et la Juventus.\n🔎 Indice 4 : Je suis connu pour mes frappes lointaines et mes célébrations originales.\n\nQui suis-je ?",
        "options": ["N'Golo Kanté", "Paul Pogba", "Blaise Matuidi", "Adrien Rabiot"],
        "answer": "Paul Pogba"
    },
    {
        "type": "whoami",
        "question": "🔎 Indice 1 : Je suis un milieu de terrain croate.\n🔎 Indice 2 : J'ai gagné le Ballon d'Or en 2018.\n🔎 Indice 3 : Je porte le numéro 10 au Real Madrid.\n🔎 Indice 4 : J'ai joué pour Tottenham avant de rejoindre l'Espagne.\n\nQui suis-je ?",
        "options": ["Ivan Rakitić", "Luka Modrić", "Mateo Kovačić", "Marcelo Brozović"],
        "answer": "Luka Modrić"
    },
    {
        "type": "standard",
        "question": "Un attaquant suédois marque un retourné acrobatique incroyable de plus de 30 mètres contre l'Angleterre, puis célèbre torse nu. Qui est ce joueur ?",
        "options": ["Henrik Larsson", "Freddie Ljungberg", "Zlatan Ibrahimović", "Alexander Isak"],
        "answer": "Zlatan Ibrahimović"
    }
]

ROUND_3_ATTAQUANTS = [
    {
        "type": "transfer",
        "question": "Sporting CP ➔ Manchester United ➔ Real Madrid ➔ Juventus ➔ Manchester United ➔ Al Nassr. \nQui suis-je ?",
        "options": ["Nani", "Ricardo Quaresma", "Cristiano Ronaldo", "Bruno Fernandes"],
        "answer": "Cristiano Ronaldo"
    },
    {
        "type": "transfer",
        "question": "Malmö FF ➔ Ajax ➔ Juventus ➔ Inter Milan ➔ FC Barcelone ➔ AC Milan ➔ PSG ➔ Manchester United ➔ LA Galaxy ➔ AC Milan. \nQui suis-je ?",
        "options": ["Edinson Cavani", "Zlatan Ibrahimović", "Thiago Silva", "Henrik Larsson"],
        "answer": "Zlatan Ibrahimović"
    },
    {
        "type": "transfer",
        "question": "Santos FC ➔ FC Barcelone ➔ Paris Saint-Germain ➔ Al Hilal. \nQui suis-je ?",
        "options": ["Ronaldinho", "Robinho", "Neymar", "Vinícius Júnior"],
        "answer": "Neymar"
    }
]

ROUND_4_GARDIEN = [
    {
        "type": "whoami",
        "question": "🔎 Indice 1 : Je suis le seul gardien de l'histoire à avoir remporté le Ballon d'Or.\n🔎 Indice 2 : J'ai passé toute ma carrière dans un seul club, le Dynamo Moscou.\n🔎 Indice 3 : Je portais toujours une tenue entièrement noire.\n🔎 Indice 4 : On me surnommait 'L'Araignée Noire'.\n\nQui suis-je ?",
        "options": ["Gordon Banks", "Lev Yachine", "Dino Zoff", "Sepp Maier"],
        "answer": "Lev Yachine"
    }
]

def get_questions(n: int = 1) -> list[dict]:
    """Fallback basique au cas où"""
    return ROUND_1_DEFENSEURS[:n]
