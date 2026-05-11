# ============================================================
# services/question_generator.py — Génération dynamique de questions
# ============================================================

import requests
import json
import random
from typing import List, Dict, Any
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MISTRAL_API_KEY

class DynamicQuestionGenerator:
    """
    Génère des questions de football dynamiques avec Mistral via API Mistral
    """
    
    API_URL = "https://api.mistral.ai/v1/chat/completions"
    MODEL = "mistral-medium"
    
    def __init__(self):
        self.api_key = MISTRAL_API_KEY
        if not self.api_key:
            raise RuntimeError("MISTRAL_API_KEY non configurée")
    
    def _call_mistral(self, prompt: str, temperature: float = 0.7) -> Dict[str, Any] | None:
        """Helper pour appeler l'API Mistral"""
        try:
            response = requests.post(
                self.API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "random_seed": random.randint(1, 10**6) if "random_seed" not in prompt else None # Optionnel, géré plus haut
                },
                timeout=30
            )
            if response.status_code != 200:
                print(f"[ERROR] Mistral API: {response.status_code}")
                return None
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return self._parse_response(content)
        except Exception as e:
            print(f"[ERROR] API Call: {e}")
            return None
    
    def generate_batch(self, count: int = 11, difficulty: str = "mixed") -> List[Dict[str, Any]]:
        """
        Génère plusieurs questions
        
        Args:
            count: nombre de questions à générer
            difficulty: "easy", "medium", "hard", ou "mixed"
        
        Returns:
            Liste de questions
        """
        questions = []
        for i in range(count):
            if difficulty == "mixed":
                # Répartition : 1/3 facile, 1/3 moyen, 1/3 difficile
                if i < count // 3:
                    diff = "easy"
                elif i < 2 * count // 3:
                    diff = "medium"
                else:
                    diff = "hard"
            else:
                diff = difficulty
            
            q = self.generate_question(diff)
            if q:
                questions.append(q)
            else:
                print(f"[WARN] Impossible de générer question {i+1}")
        
        return questions
    
    def generate_trivia_question(self, difficulty: str = "medium", theme: str = "") -> Dict[str, Any] | None:
        """Génère une question de culture générale football (Round Défenseurs)"""
        prompt = self._build_prompt(difficulty, theme)
        return self._call_mistral(prompt)

    def generate_iconic_moment_question(self, theme: str = "") -> Dict[str, Any] | None:
        """Génère une question de description d'action iconique (Round Milieux)"""
        theme_str = f"L'action doit idéalement être liée à ce thème : {theme}." if theme else ""
        prompt = f"""Tu es un expert du football. Génère UNE question décrivant visuellement une action mythique de l'histoire du football, sans jamais nommer le joueur principal.
Exemple : "Un joueur chauve avec un maillot bleu frappé du numéro 10 donne un coup de tête dans le torse d'un défenseur italien lors d'une finale."
{theme_str}
CONSIGNES :
1. Propose 4 joueurs célèbres dans les "options".
2. La BONNE RÉPONSE doit être en 2ème position.
3. Ne réponds qu'avec le format JSON strict suivant :
{{
  "question": "La description de la scène... Qui est ce joueur ?",
  "options": ["Faux Joueur 1", "Bon Joueur", "Faux Joueur 2", "Faux Joueur 3"],
  "answer": "Bon Joueur"
}}"""
        return self._call_mistral(prompt)
    
    def generate_transfer_question(self, player_name: str) -> Dict[str, Any] | None:
        """Génère une question basée sur l'historique des transferts"""
        prompt = f"""Tu es un expert en mercato. Génère l'historique chronologique précis des clubs pour le joueur : {player_name}.
CONSIGNES :
1. Utilise les VRAIS NOMS des clubs (ex: Real Madrid, Juventus, Manchester United) et les VRAIES ANNÉES.
2. Ne jamais utiliser "Club A", "Club B", etc.
3. Pour les 'options', propose {player_name} et 3 autres VRAIS joueurs célèbres de la même époque.

Format JSON :
{{
  "question": "Quel joueur a connu ce parcours : [Nom Club (Années), Nom Club (Années)...] ?",
  "options": ["Nom Joueur 1", "{player_name}", "Nom Joueur 3", "Nom Joueur 4"],
  "answer": "{player_name}"
}}
RÈGLE : Mets la bonne réponse en 2e position. Réponds uniquement en JSON."""
        return self._call_mistral(prompt)

    def generate_reordering_question(self) -> Dict[str, Any] | None:
        """Génère une question de reclassement chronologique"""
        prompt = """Génère 4 événements historiques MAJEURS et RÉELS du football mondial (Coupes du Monde, finales de C1, transferts records).
CONSIGNES :
1. Les événements doivent être précis et datés.
2. Format JSON uniquement.

Format JSON :
{{
  "question": "Reclassez ces événements du plus ancien au plus récent :",
  "events": ["Description précise 1", "Description précise 2", "Description précise 3", "Description précise 4"],
  "correct_order": ["Événement le plus ancien", "...", "...", "Événement le plus récent"]
}}"""
        return self._call_mistral(prompt)

    def generate_who_am_i(self, theme: str = "") -> Dict[str, Any] | None:
        """Génère une question 'Qui suis-je' avec indices progressifs, format MCQ"""
        theme_str = f"Le gardien doit avoir cette caractéristique : {theme}." if theme else ""
        prompt = f"""Génère une question 'Qui suis-je' pour un gardien de but légendaire.
{theme_str}
CONSIGNES :
1. Donne 4 indices de plus en plus faciles sur le gardien mystère.
2. L'indice 1 doit être une anecdote ou un record précis. L'indice 4 doit être très reconnaissable.
3. Utilise de vrais noms.
4. Propose 4 noms de gardiens légendaires en options, dont la bonne réponse en 2ème position.

Format JSON OBLIGATOIRE :
{{
  "question": "Qui suis-je ?\\n\\n🔎 Indice 1 : [anecdote/record]\\n🔎 Indice 2 : [club/palmarès]\\n🔎 Indice 3 : [nationalité/époque]\\n🔎 Indice 4 : [fait très connu]",
  "options": ["Nom Gardien 1", "Nom Gardien CORRECT", "Nom Gardien 3", "Nom Gardien 4"],
  "answer": "Nom Gardien CORRECT"
}}

RÈGLE : La bonne réponse doit être en 2ème position dans les options. Réponds uniquement en JSON valide."""
        result = self._call_mistral(prompt)
        
        # Si le résultat a le vieux format (hints sans options), le convertir
        if result and "hints" in result and "options" not in result:
            hints = result["hints"]
            answer = result.get("answer", "Inconnu")
            # Construire le texte de question avec les indices
            hints_text = "\n".join([f"🔎 Indice {i+1} : {h}" for i, h in enumerate(hints)])
            question_text = f"Qui suis-je ?\n\n{hints_text}"
            
            # Créer des options avec de vrais noms de gardiens
            all_keepers = ["Buffon", "Casillas", "Neuer", "Yashin", "Schmeichel",
                           "Zoff", "Kahn", "Cech", "Van der Sar", "Oblak",
                           "Ter Stegen", "Courtois", "Lloris", "De Gea", "Alisson"]
            # Retirer la bonne réponse des distracteurs potentiels
            distractors = [k for k in all_keepers if k.lower() not in answer.lower() and answer.lower() not in k.lower()]
            import random
            chosen = random.sample(distractors, min(3, len(distractors)))
            
            options = [chosen[0] if len(chosen) > 0 else "Gardien A",
                       answer,
                       chosen[1] if len(chosen) > 1 else "Gardien C",
                       chosen[2] if len(chosen) > 2 else "Gardien D"]
            
            result = {
                "question": question_text,
                "options": options,
                "answer": answer
            }
        
        return result

    def generate_full_match_questions(self) -> list[dict]:
        """Génère les 18 questions du match en parallèle pour gagner du temps"""
        import concurrent.futures
        import random
        
        # On définit les tâches (18 manches)
        tasks = []
        # Round 1 (Défenseurs) : 6 questions Trivia avec thèmes uniques
        trivia_themes = ["Coupe du Monde", "Ligue des Champions", "Ballon d'Or et Records", "Premier League", "La Liga et Serie A", "Gardiens et Défenseurs de légende"]
        tasks.extend([(self.generate_trivia_question, "medium", t) for t in trivia_themes])
        
        # Round 2 (Milieux) : 6 questions Iconic Moment avec thèmes uniques
        iconic_themes = ["Une célébration mythique", "Un but exceptionnel en finale", "Un carton rouge ou coup de sang célèbre", "Un exploit technique individuel", "Un arrêt légendaire", "Un moment insolite ou drôle"]
        tasks.extend([(self.generate_iconic_moment_question, t) for t in iconic_themes])
        
        # Round 3 (Attaquants) : 4 questions Transfert
        players = ["Cristiano Ronaldo", "Zlatan Ibrahimović", "Neymar", "Luis Suarez", "Angel Di Maria", "Thierry Henry", "Ronaldinho", "David Beckham", "Karim Benzema", "Robert Lewandowski"]
        selected_players = random.sample(players, 4)
        tasks.extend([(self.generate_transfer_question, p) for p in selected_players])
        
        # Round 4 (Gardien) : 2 questions Who Am I avec thèmes
        whoami_themes = ["Gardien ayant gagné une Coupe du Monde au 21ème siècle", "Gardien légendaire du 20ème siècle (avant l'an 2000)"]
        tasks.extend([(self.generate_who_am_i, t) for t in whoami_themes])
        
        temp_results = [None] * 18
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_idx = {}
            for idx, task_info in enumerate(tasks):
                func = task_info[0]
                args = task_info[1:]
                future = executor.submit(func, *args)
                future_to_idx[future] = idx
            
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    res = future.result()
                    temp_results[idx] = res
                except Exception as e:
                    print(f"❌ Erreur génération Q{idx}: {e}")
                    
        # Remplacer les erreurs par des fallback
        from game.questions_static import ROUND_1_DEFENSEURS, ROUND_2_MILIEUX, ROUND_3_ATTAQUANTS, ROUND_4_GARDIEN
        final_list = []
        for i, q in enumerate(temp_results):
            if q is not None and "question" in q and "options" in q and len(q["options"]) >= 4:
                # S'assurer que la bonne réponse est présente dans la question locale
                final_list.append(q)
            else:
                # Fallback robuste
                if i < 6: final_list.append(random.choice(ROUND_1_DEFENSEURS))
                elif i < 12: final_list.append(random.choice(ROUND_2_MILIEUX))
                elif i < 16: final_list.append(random.choice(ROUND_3_ATTAQUANTS))
                else: final_list.append(random.choice(ROUND_4_GARDIEN))
                
        return final_list

    def _build_prompt(self, difficulty: str, theme: str = "") -> str:
        """
        Construit le prompt pour Mistral
        """
        difficulty_desc = {
            "easy": "simple et accessible à tous les fans de football",
            "medium": "modérée, pour les connaisseurs",
            "hard": "difficile, pour les experts du football"
        }
        
        theme_str = f"\nTHÈME OBLIGATOIRE : La question DOIT porter spécifiquement sur le sujet suivant : {theme}\n" if theme else ""
        
        prompt = f"""Tu es un expert du football. Génère UNE question de football {difficulty_desc.get(difficulty, 'modérée')} 
en format JSON avec cette structure exacte (valide JSON, pas de texte avant/après):
{theme_str}

{{
  "question": "La question en français?",
  "options": ["Option 1", "Option 2 (BONNE RÉPONSE)", "Option 3", "Option 4"],
  "answer": "Option 2 (BONNE RÉPONSE)"
}}

RÈGLES IMPORTANTES:
1. La 2e option doit TOUJOURS être la bonne réponse
2. Les mauvaises options doivent être plausibles mais clairement incorrectes
3. La question doit être sur le football (statistiques, histoire, records, joueurs, équipes)
4. Difficulté {difficulty}: {"Questions basiques (règles, équipes connues)" if difficulty == "easy" else "Questions intermédiaires (histoire récente, joueurs)" if difficulty == "medium" else "Questions pointues (records obscurs, faits précis)"}
5. Réponds UNIQUEMENT avec le JSON valide, rien d'autre

Génère la question maintenant:"""
        
        return prompt
    
    def _parse_response(self, content: str) -> Dict[str, Any] | None:
        """
        Parse la réponse JSON du modèle de manière robuste
        """
        try:
            # Nettoyer le contenu
            content = content.strip()
            
            # Extraire JSON si le texte contient du JSON entre accolades (cas général)
            if "{" in content and "}" in content:
                # S'il y a plusieurs blocs JSON (ex: explication + json),
                # on essaie de trouver celui qui contient "question"
                blocks = []
                temp_content = content
                while "{" in temp_content:
                    s = temp_content.find("{")
                    # Essayer de trouver le } correspondant équilibré
                    depth = 0
                    e = -1
                    for i in range(s, len(temp_content)):
                        if temp_content[i] == "{": depth += 1
                        elif temp_content[i] == "}":
                            depth -= 1
                            if depth == 0:
                                e = i + 1
                                break
                    if e != -1:
                        blocks.append(temp_content[s:e])
                        temp_content = temp_content[e:]
                    else:
                        break
                
                # Chercher le bloc qui ressemble à une question
                json_str = None
                for block in blocks:
                    if '"question"' in block:
                        json_str = block
                        break
                
                if not json_str and blocks:
                    json_str = blocks[0]
                elif not json_str:
                    json_str = content[content.find("{"):content.rfind("}")+1]
                
                data = json.loads(json_str)
                
                # Valider la structure selon le type de question détecté
                if "question" in data:
                    # Cas standard (QCM ou autre)
                    if "options" in data:
                        options = data.get("options", [])
                        answer = data.get("answer", "")
                        clean_answer = str(answer).split("(")[0].strip() if "(" in str(answer) else str(answer)
                        
                        return {
                            "question": data.get("question", ""),
                            "options": options,
                            "answer": clean_answer
                        }
                    # Cas Reclassement
                    elif "events" in data and "correct_order" in data:
                        return data
                    # Cas Qui suis-je
                    elif "hints" in data:
                        return data
                
        except json.JSONDecodeError:
            print(f"[WARN] Impossible de parser JSON (Format incorrect): {content[:100]}...")
        except Exception as e:
            print(f"[WARN] Erreur parsing IA: {e}")
        
        return None
