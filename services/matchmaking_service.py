# ============================================================
# services/matchmaking_service.py — Système de matchmaking online
# ============================================================

from typing import Any, List
from supabase import Client
import datetime

class MatchmakingService:
    """
    Gère le matchmaking online :
    - Liste des joueurs disponibles
    - Invitations
    - État des matchs
    """

    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        if not self.client:
            raise RuntimeError("Supabase client non configuré")

    # ────────────────────────────────────────────────────
    # JOUEURS DISPONIBLES
    # ────────────────────────────────────────────────────

    def get_available_players(self, current_user_id: str, limit: int = 10) -> List[dict]:
        """
        Récupère les joueurs en ligne (excluant l'utilisateur courant)
        """
        try:
            print(f"🔍 Recherche joueurs... (Supabase query)")
            print(f"   - Current user ID: {current_user_id}")
            
            # Récupérer TOUS les profils d'abord
            resp = self.client.table("profiles").select(
                "id, email, nickname, avatar, online_status, last_seen"
            ).execute()
            
            all_players = resp.data if resp.data else []
            print(f"📋 {len(all_players)} joueurs total en BD")
            for p in all_players:
                print(f"   - {p.get('nickname', 'N/A')} ({p.get('id', 'N/A')}) : {p.get('online_status', 'N/A')}")
            
            # Filtrer manuellement
            others = [p for p in all_players if p.get('id') != current_user_id]
            print(f"✅ {len(others)} autres joueurs trouvés")
            return others
        except Exception as e:
            print(f"❌ ERREUR récupération joueurs: {e}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Erreur lors de la récupération des joueurs: {e}")

    def set_online_status(self, user_id: str, status: str) -> bool:
        """
        Marque l'utilisateur comme online/offline
        """
        try:
            self.client.table("profiles").update({
                "online_status": status,
                "last_seen": datetime.datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
            print(f"✅ Statut {user_id} mise à jour à '{status}'")
            return True
        except Exception as e:
            print(f"❌ ERREUR mise à jour statut: {e}")
            import traceback
            traceback.print_exc()
            return False

    # ────────────────────────────────────────────────────
    # INVITATIONS
    # ────────────────────────────────────────────────────

    def send_invitation(self, from_user_id: str, to_user_id: str) -> dict:
        """
        Envoie une invitation de match.
        Si l'autre nous a déjà envoyé une invitation RÉCENTE, on l'accepte.
        Si on a déjà envoyé une invitation RÉCENTE à l'autre, on ne fait rien (on attend).
        """
        try:
            # Cutoff de 3 minutes pour considérer une invitation comme "active"
            now = datetime.datetime.utcnow()
            cutoff_time = (now - datetime.timedelta(minutes=3)).isoformat()

            # 1. Vérifier si l'autre nous a déjà envoyé une invitation pending RÉCENTE
            existing_them = self.client.table("match_invitations").select("id").eq("from_user_id", to_user_id).eq("to_user_id", from_user_id).eq("status", "pending").gte("created_at", cutoff_time).execute()
            if existing_them.data:
                print(f"🔄 Déjà une invitation de {to_user_id}, on l'accepte automatiquement.")
                # Accepter l'invitation existante au lieu d'en créer une nouvelle
                match = self.accept_invitation(existing_them.data[0]["id"])
                return {"id": match.get("id"), "auto_accepted": True}

            # 2. Vérifier si NOUS avons déjà envoyé une invitation pending RÉCENTE à l'autre
            existing_us = self.client.table("match_invitations").select("id").eq("from_user_id", from_user_id).eq("to_user_id", to_user_id).eq("status", "pending").gte("created_at", cutoff_time).execute()
            if existing_us.data:
                print(f"⌛ Défi déjà envoyé à {to_user_id}, en attente...")
                return {"id": None, "already_sent": True}

            # 3. Sinon, créer une nouvelle invitation
            resp = self.client.table("match_invitations").insert({
                "from_user_id": from_user_id,
                "to_user_id": to_user_id,
                "status": "pending"
            }).execute()
            return resp.data[0] if resp.data else {}
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'envoi de l'invitation: {e}")

    def get_pending_invitations(self, user_id: str, max_age_minutes: int = 3) -> List[dict]:
        """
        Récupère les invitations en attente RÉCENTES pour cet utilisateur
        (filtre par défaut : 3 dernières minutes)
        """
        try:
            # Calculer la date limite
            now = datetime.datetime.utcnow()
            cutoff_time = (now - datetime.timedelta(minutes=max_age_minutes)).isoformat()
            
            resp = self.client.table("match_invitations").select(
                "id, from_user_id, status, created_at"
            ).eq("to_user_id", user_id).eq("status", "pending").gte(
                "created_at", cutoff_time
            ).order("created_at", desc=True).limit(10).execute()
            
            # Enrichir avec les infos du joueur qui a invité
            invitations = []
            for inv in resp.data:
                try:
                    player = self.client.table("profiles").select(
                        "id, nickname, avatar"
                    ).eq("id", inv["from_user_id"]).single().execute()
                    inv["player"] = player.data if player.data else {}
                except:
                    inv["player"] = {}
                invitations.append(inv)
            
            return invitations
        except Exception as e:
            print(f"Erreur récupération invitations: {e}")
            return []

    def accept_invitation(self, invitation_id: str) -> dict:
        """
        Accepte une invitation et crée un match
        """
        try:
            # Récupérer l'invitation
            inv = self.client.table("match_invitations").select(
                "from_user_id, to_user_id"
            ).eq("id", invitation_id).single().execute()
            
            if not inv.data:
                raise RuntimeError("Invitation introuvable")
            
            from_user_id = inv.data["from_user_id"]
            to_user_id = inv.data["to_user_id"]
            
            import datetime
            now = datetime.datetime.utcnow()
            cutoff_time = (now - datetime.timedelta(seconds=45)).isoformat()
            
            existing_1 = self.client.table("matches").select("*").eq("player1_id", from_user_id).eq("player2_id", to_user_id).gte("created_at", cutoff_time).execute()
            existing_2 = self.client.table("matches").select("*").eq("player1_id", to_user_id).eq("player2_id", from_user_id).gte("created_at", cutoff_time).execute()
            
            existing_matches = existing_1.data + existing_2.data
            if existing_matches:
                existing_matches.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                match_data = existing_matches[0]
                print(f"🔄 Match déjà existant (ID: {match_data['id']}), on le réutilise.")
            else:
                # Créer le match
                resp = self.client.table("matches").insert({
                    "player1_id": from_user_id,
                    "player2_id": to_user_id,
                    "status": "accepted",
                    "questions_generated": False
                }).execute()
                match_data = resp.data[0] if resp.data else {}
            
            # Mettre à jour l'invitation
            self.client.table("match_invitations").update({
                "status": "accepted"
            }).eq("id", invitation_id).execute()
            
            return match_data
        except Exception as e:
            raise RuntimeError(f"Erreur acceptation invitation: {e}")

    def decline_invitation(self, invitation_id: str) -> bool:
        """
        Rejette une invitation
        """
        try:
            self.client.table("match_invitations").update({
                "status": "declined"
            }).eq("id", invitation_id).execute()
            return True
        except Exception as e:
            print(f"Erreur rejet invitation: {e}")
            return False

    # ────────────────────────────────────────────────────
    # MATCHS
    # ────────────────────────────────────────────────────

    def get_active_match(self, user_id: str) -> dict | None:
        """
        Récupère le match actif de l'utilisateur (s'il existe)
        """
        try:
            resp = self.client.table("matches").select(
                "*"
            ).or_(
                f"player1_id.eq.{user_id},player2_id.eq.{user_id}"
            ).neq("status", "finished").limit(1).execute()
            
            return resp.data[0] if resp.data else None
        except Exception as e:
            print(f"Erreur récupération match actif: {e}")
            return None

    def finish_match(self, match_id: str, winner_id: str | None = None) -> bool:
        """
        Marque le match comme terminé
        """
        try:
            self.client.table("matches").update({
                "status": "finished",
                "winner_id": winner_id,
                "finished_at": datetime.datetime.utcnow().isoformat()
            }).eq("id", match_id).execute()
            return True
        except Exception as e:
            print(f"Erreur finalisation match: {e}")
            return False

    def get_user_profile(self, user_id: str) -> dict | None:
        """
        Récupère le profil complet d'un utilisateur
        """
        try:
            resp = self.client.table("profiles").select(
                "*"
            ).eq("id", user_id).single().execute()
            return resp.data if resp.data else None
        except Exception as e:
            print(f"Erreur récupération profil: {e}")
            return None

    # ────────────────────────────────────────────────────
    # QUESTIONS DU MATCH (STATIQUES - API LIMITE ATTEINTE)
    # ────────────────────────────────────────────────────

    def get_static_questions(self, count: int = 30) -> List[dict]:
        """
        Récupère les questions statiques depuis la table static_questions
        Retourne les premières N questions (1-40)
        """
        try:
            resp = self.client.table("static_questions").select(
                "*"
            ).order("question_number", desc=False).limit(count).execute()
            
            questions = []
            for q_data in resp.data:
                questions.append({
                    "id": q_data.get("id"),
                    "question_number": q_data.get("question_number"),
                    "question": q_data.get("question"),
                    "options": q_data.get("options", []),
                    "answer": q_data.get("correct_answer"),
                    "difficulty": q_data.get("difficulty", "medium")
                })
            
            print(f"✅ {len(questions)} questions statiques chargées")
            return questions
        except Exception as e:
            print(f"❌ Erreur chargement questions statiques: {e}")
            return []

    def generate_and_save_match_questions(self, match_id: str, count: int = 11) -> bool:
        """
        Charge les questions statiques et les sauvegarde pour ce match
        (Pas vraie génération - juste copie des questions statiques)
        """
        try:
            # Vérifier si les questions existent déjà
            existing = self.get_match_questions(match_id)
            if existing and len(existing) >= count:
                print(f"✅ Questions déjà préparées pour match {match_id}")
                return True
            
            # Charger les questions statiques
            print(f"🔄 Chargement de {count} questions statiques pour match {match_id}...")
            questions = self.get_static_questions(count=count)
            
            if not questions or len(questions) < count:
                print(f"⚠️ Seulement {len(questions)} questions disponibles (minimum {count})")
            
            # Sauvegarder les questions pour ce match
            return self.generate_match_questions(match_id, questions)
        except Exception as e:
            print(f"❌ Erreur dans generate_and_save_match_questions: {e}")
            return False

    def generate_match_questions(self, match_id: str, questions: List[dict]) -> bool:
        """
        Sauvegarde les questions générées du match (UNE SEULE FOIS)
        Supporte désormais les types de questions variés et les images.
        """
        try:
            questions_data = []
            for i, q in enumerate(questions):
                # On stocke tout le dictionnaire en JSON dans le champ 'question'
                # pour préserver les hints, image_url, type, etc.
                import json
                full_json = json.dumps(q)
                
                questions_data.append({
                    "match_id": match_id,
                    "round_number": i + 1,
                    "question": full_json, # <--- JSON COMPLET
                    "options": q.get("options", []),
                    "correct_answer": q.get("answer", q.get("correct_answer", "")),
                    "difficulty": q.get("difficulty", "medium"),
                })
            
            self.client.table("match_questions").insert(questions_data).execute()
            print(f"✅ {len(questions_data)} questions sauvegardées pour match {match_id}")
            return True
        except Exception as e:
            # Vérifier si c'est une violation de contrainte UNIQUE (autre joueur a déjà sauvé)
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                print(f"[INFO] Questions probablement sauvegardées par l'autre joueur: {e}")
                return False
            else:
                print(f"❌ Erreur sauvegarde questions: {e}")
                return False

    def save_single_question(self, match_id: str, round_number: int, q: dict) -> bool:
        """
        Sauvegarde une seule question pour un match.
        Utile quand une question est annulée et qu'on doit en générer une nouvelle.
        """
        try:
            import json
            full_json = json.dumps(q)
            
            data = {
                "match_id": match_id,
                "round_number": round_number,
                "question": full_json,
                "options": q.get("options", []),
                "correct_answer": q.get("answer", q.get("correct_answer", "")),
                "difficulty": q.get("difficulty", "medium"),
            }
            
            # Essayer d'insérer, si ça échoue (déjà existant), on met à jour
            try:
                self.client.table("match_questions").insert(data).execute()
            except:
                self.client.table("match_questions").update(data).eq("match_id", match_id).eq("round_number", round_number).execute()
            
            print(f"✅ Question individuelle sauvegardée pour match {match_id} round {round_number}")
            return True
        except Exception as e:
            print(f"❌ Erreur save_single_question: {e}")
            return False

    def get_match_questions(self, match_id: str) -> List[dict]:
        """
        Récupère les questions du match (partagées entre les deux joueurs)
        """
        try:
            resp = self.client.table("match_questions").select(
                "*"
            ).eq("match_id", match_id).order("round_number", desc=False).execute()
            
            if not resp.data: return []
            
            # Reconstruire les objets questions
            questions = []
            for row in resp.data:
                q_text = row.get("question", "")
                import json
                try:
                    # Essayer de décoder le JSON s'il y en a un
                    if q_text.startswith("{") and q_text.endswith("}"):
                        q_obj = json.loads(q_text)
                    else:
                        # Fallback pour les anciennes questions texte simple
                        q_obj = {
                            "question": q_text,
                            "options": row.get("options", []),
                            "answer": row.get("correct_answer", ""),
                            "difficulty": row.get("difficulty", "medium")
                        }
                    questions.append(q_obj)
                except:
                    questions.append({"question": q_text})
            
            return questions
        except Exception as e:
            print(f"Erreur récupération questions: {e}")
            return []

    def get_match_info(self, match_id: str) -> dict | None:
        """Récupère les infos complètes du match"""
        try:
            resp = self.client.table("matches").select("*").eq("id", match_id).single().execute()
            return resp.data if resp.data else None
        except:
            return None

    def get_question_by_round(self, match_id: str, round_number: int) -> dict | None:
        """
        Récupère la question d'une manche spécifique
        """
        try:
            resp = self.client.table("match_questions").select(
                "*"
            ).eq("match_id", match_id).eq("round_number", round_number).single().execute()
            
            return resp.data if resp.data else None
        except Exception as e:
            print(f"Erreur récupération question round: {e}")
            return None

    # ────────────────────────────────────────────────────
    # BUZZES EN TEMPS RÉEL
    # ────────────────────────────────────────────────────

    def register_buzz(self, match_id: str, player_id: str, round_number: int) -> bool:
        """
        Enregistre un buzz d'un joueur avec timestamp serveur pour synchronisation
        """
        try:
            # Vérifier si ce joueur a déjà buzzé ce round (éviter les doublons)
            existing = self.client.table("match_buzzes").select("*").eq(
                "match_id", match_id
            ).eq("player_id", player_id).eq("round_number", round_number).execute()
            
            if existing.data:
                print(f"⚠️ Buzz déjà enregistré pour ce joueur ce round")
                return True
            
            # Insérer le buzz avec timestamp serveur
            result = self.client.table("match_buzzes").insert({
                "match_id": match_id,
                "player_id": player_id,
                "round_number": round_number,
                "timestamp": "now()"  # sera via DB trigger, pas via Python
            }).execute()
            
            print(f"📢 Buzz enregistré pour joueur {player_id} round {round_number}")
            return True
        except Exception as e:
            print(f"❌ Erreur buzz: {e}")
            return False

    def get_first_buzz(self, match_id: str, round_number: int) -> dict | None:
        """
        Récupère le premier buzz d'une manche
        Trie par timestamp ascendant, puis par player_id pour déterminisme
        """
        try:
            resp = self.client.table("match_buzzes").select(
                "player_id, timestamp"
            ).eq("match_id", match_id).eq("round_number", round_number).order(
                "timestamp", desc=False
            ).limit(1).execute()
            
            return resp.data[0] if resp.data else None
        except Exception as e:
            print(f"Erreur récupération buzz: {e}")
            return None
        except Exception as e:
            print(f"Erreur récupération buzz: {e}")
            return None

    def get_buzzes_for_round(self, match_id: str, round_number: int) -> List[dict]:
        """
        Récupère tous les buzzes d'une manche
        """
        try:
            resp = self.client.table("match_buzzes").select(
                "*"
            ).eq("match_id", match_id).eq("round_number", round_number).order(
                "timestamp", desc=False
            ).execute()
            
            return resp.data if resp.data else []
        except Exception as e:
            print(f"Erreur récupération buzzes: {e}")
            return []

    def mark_questions_generated(self, match_id: str) -> bool:
        """
        Marque que les questions du match ont été générées
        """
        try:
            self.client.table("matches").update({
                "questions_generated": True
            }).eq("id", match_id).execute()
            print(f"✅ Questions marquées comme générées pour match {match_id}")
            return True
        except Exception as e:
            print(f"Erreur: {e}")
            return False

    def are_questions_generated(self, match_id: str) -> bool:
        """
        Vérifie si les questions du match ont déjà été générées
        """
        try:
            resp = self.client.table("matches").select(
                "questions_generated"
            ).eq("id", match_id).single().execute()
            
            return resp.data.get("questions_generated", False) if resp.data else False
        except Exception as e:
            print(f"Erreur: {e}")
            return False

    def start_match(self, match_id: str) -> bool:
        """
        Marque le match comme lancé (change statut de 'accepted' à 'active')
        """
        try:
            self.client.table("matches").update({
                "status": "active"
            }).eq("id", match_id).execute()
            print(f"✅ Match {match_id} marqué comme ACTIF")
            return True
        except Exception as e:
            print(f"Erreur: {e}")
            return False

    def get_accepted_matches(self, user_id: str) -> List[dict]:
        """
        Récupère les matchs acceptés TRÈS RÉCENTS de cet utilisateur
        (matchs acceptés dans les 30 dernières secondes uniquement)
        """
        try:
            # Calculer la date limite (30 secondes)
            now = datetime.datetime.utcnow()
            cutoff_time = (now - datetime.timedelta(seconds=15)).isoformat()
            
            resp = self.client.table("matches").select(
                "*"
            ).or_(
                f"player1_id.eq.{user_id},player2_id.eq.{user_id}"
            ).eq("status", "accepted").gte(
                "created_at", cutoff_time
            ).order("created_at", desc=True).limit(1).execute()
            
            return resp.data if resp.data else []
        except Exception as e:
            print(f"Erreur récupération matchs acceptés: {e}")
            return []

    # ────────────────────────────────────────────────────
    # RÉPONSES DU MATCH (Synchronisation en temps réel)
    # ────────────────────────────────────────────────────

    def register_answer(self, match_id: str, player_id: str, round_number: int, 
                       chosen_answer: str, is_correct: bool, score_gained: int = 0) -> bool:
        """
        Enregistre la réponse d'un joueur pour une manche
        Si elle existe déjà (2ème chance), mets à jour
        Retourne False si erreur
        """
        try:
            # D'abord, vérifier si une réponse existe déjà pour ce round
            existing = self.client.table("match_answers").select(
                "id"
            ).eq("match_id", match_id).eq("player_id", player_id).eq("round_number", round_number).execute()
            
            if existing.data:
                # Mise à jour (2ème chance)
                resp = self.client.table("match_answers").update({
                    "chosen_answer": chosen_answer,
                    "is_correct": is_correct,
                    "score_gained": score_gained
                }).eq("match_id", match_id).eq("player_id", player_id).eq("round_number", round_number).execute()
                print(f"✅ Réponse mise à jour: joueur {player_id} round {round_number} (2ème chance)")
            else:
                # Insertion (première fois)
                resp = self.client.table("match_answers").insert({
                    "match_id": match_id,
                    "player_id": player_id,
                    "round_number": round_number,
                    "chosen_answer": chosen_answer,
                    "is_correct": is_correct,
                    "score_gained": score_gained
                }).execute()
                print(f"✅ Réponse enregistrée: joueur {player_id} round {round_number}")
            
            return True
        except Exception as e:
            print(f"❌ Erreur enregistrement réponse: {e}")
            return False

    def get_opponent_answer(self, match_id: str, round_number: int, my_player_id: str) -> dict | None:
        """
        Récupère la réponse de l'autre joueur pour une manche
        """
        try:
            # Récupérer les réponses pour ce round (normalement 2: une pour chaque joueur)
            resp = self.client.table("match_answers").select(
                "*"
            ).eq("match_id", match_id).eq("round_number", round_number).execute()
            
            if not resp.data:
                return None
            
            # Trouver la réponse de l'AUTRE joueur (pas la mienne)
            for answer in resp.data:
                if answer.get("player_id") != my_player_id:
                    return {
                        "player_id": answer.get("player_id"),
                        "chosen_answer": answer.get("chosen_answer"),
                        "is_correct": answer.get("is_correct"),
                        "score_gained": answer.get("score_gained", 0),
                        "timestamp": answer.get("timestamp")
                    }
            
            return None
        except Exception as e:
            print(f"Erreur récupération réponse opponent: {e}")
            return None

    def get_round_answers(self, match_id: str, round_number: int) -> List[dict]:
        """
        Récupère les réponses de TOUS les joueurs pour une manche
        """
        try:
            resp = self.client.table("match_answers").select(
                "*"
            ).eq("match_id", match_id).eq("round_number", round_number).execute()
            
            return resp.data if resp.data else []
        except Exception as e:
            print(f"Erreur récupération réponses manche: {e}")
            return []

    def get_all_match_answers(self, match_id: str) -> List[dict]:
        """
        Récupère TOUTES les réponses d'un match
        """
        try:
            resp = self.client.table("match_answers").select(
                "*"
            ).eq("match_id", match_id).order("round_number", desc=False).execute()
            
            return resp.data if resp.data else []
        except Exception as e:
            print(f"Erreur récupération toutes réponses: {e}")
            return []

    def update_match_nicknames(self, match_id: str, player1_nickname: str, player2_nickname: str) -> bool:
        """
        Sauvegarde les noms des joueurs au match (player1=rouge, player2=bleu)
        pour synchronisation entre les deux clients
        """
        try:
            resp = self.client.table("matches").update({
                "player1_nickname": player1_nickname,
                "player2_nickname": player2_nickname
            }).eq("id", match_id).execute()
            
            if resp.data:
                print(f"✅ Noms du match synchronisés: {player1_nickname} vs {player2_nickname}")
                return True
            return False
        except Exception as e:
            print(f"❌ Erreur mise à jour noms match: {e}")
            return False

    def get_match_state(self, match_id: str) -> dict:
        """
        Récupère l'état actuel du match (phase, joueur actif, etc)
        """
        try:
            resp = self.client.table("match_state").select("*").eq("match_id", match_id).single().execute()
            return resp.data if resp.data else None
        except Exception as e:
            print(f"ℹ️ match_state non trouvé: {e}")
            return None

    def init_match_state(self, match_id: str, round_number: int = 1) -> bool:
        """
        Initialise l'état du match (phase=BUZZ, round=N, etc)
        Utilise upsert pour éviter les erreurs de duplication si les deux joueurs lancent en même temps.
        """
        try:
            data = {
                "match_id": match_id,
                "round_number": round_number,
                "phase": "BUZZ",
                "active_player_id": None,
                "pick_index": None
            }
            # Utilisation de upsert avec on_conflict sur match_id
            resp = self.client.table("match_state").upsert(data, on_conflict="match_id").execute()
            
            if resp.data:
                # Note : 'current_round' supprimé car non présent dans le schéma
                
                print(f"✅ État du match initialisé/récupéré pour {match_id} (Round {round_number})")
                return True
            return False
        except Exception as e:
            print(f"❌ Erreur init match_state: {e}")
            return False

    def update_match_phase(self, match_id: str, phase: str, active_player_id: str = None) -> bool:
        """
        Mets à jour la phase du match et le joueur actif
        """
        try:
            resp = self.client.table("match_state").update({
                "phase": phase,
                "active_player_id": active_player_id,
                "updated_at": "now()"
            }).eq("match_id", match_id).execute()
            
            if resp.data:
                print(f"📊 Phase mise à jour: {phase} | Joueur actif: {active_player_id}")
                return True
            return False
        except Exception as e:
            print(f"❌ Erreur mise à jour phase: {e}")
            return False
    
    def store_pick_choice(self, match_id: str, pick_index: int) -> bool:
        """Enregistre le choix du PICK (index du joueur choisi)"""
        try:
            resp = self.client.table("match_state").update({
                "pick_index": pick_index
            }).eq("match_id", match_id).execute()
            
            if resp.data:
                print(f"✅ Pick enregistré: index {pick_index}")
                return True
            return False
        except Exception as e:
            print(f"❌ Erreur enregistrement pick: {e}")
            return False

    def update_match_round(self, match_id: str, round_number: int) -> bool:
        """
        Mets à jour le numéro de la manche
        """
        try:
            resp = self.client.table("match_state").update({
                "round_number": round_number,
                "phase": "BUZZ",
                "active_player_id": None,
                "pick_index": None, # <--- Reset pour la manche suivante
                "updated_at": "now()"
            }).eq("match_id", match_id).execute()
            
            if resp.data:
                print(f"🎯 Manche {round_number} commencée")
                return True
            return False
        except Exception as e:
            print(f"❌ Erreur mise à jour manche: {e}")
            return False

    def get_match_info(self, match_id: str) -> dict:
        """
        Récupère les infos du match (player1_id, player2_id, nicknames, etc)
        """
        try:
            resp = self.client.table("matches").select("*").eq("id", match_id).single().execute()
            return resp.data if resp.data else None
        except Exception as e:
            print(f"❌ Erreur récupération match_info: {e}")
            return None

    def get_all_buzzes_for_round(self, match_id: str, round_number: int) -> list:
        """
        Récupère TOUS les buzzes pour cette manche
        """
        try:
            resp = self.client.table("match_buzzes").select("*").eq("match_id", match_id).eq("round_number", round_number).execute()
            return resp.data if resp.data else []
        except Exception as e:
            print(f"❌ Erreur récupération buzzes: {e}")
            return []

