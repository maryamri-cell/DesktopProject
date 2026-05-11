# ============================================================
# services/supabase_service.py — Auth + profils + score history
# ============================================================

from __future__ import annotations

from typing import Any
import json
import os

SESSION_FILE = "session.json"

from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_KEY

try:
    from supabase import create_client
except Exception:
    create_client = None


class SupabaseService:
    """Wrapper simple pour centraliser les appels Supabase."""

    def __init__(self):
        self.client = None
        key = SUPABASE_ANON_KEY or SUPABASE_KEY
        if create_client and SUPABASE_URL and key:
            self.client = create_client(SUPABASE_URL, key)

    @property
    def is_ready(self) -> bool:
        return self.client is not None

    def _require_client(self):
        if not self.client:
            raise RuntimeError(
                "Supabase non configure. Definis SUPABASE_URL et SUPABASE_ANON_KEY."
            )

    def sign_up(self, email: str, password: str, nickname: str, avatar: str) -> dict[str, Any]:
        self._require_client()

        try:
            resp = self.client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "nickname": nickname,
                            "avatar": avatar,
                        }
                    },
                }
            )
        except Exception as e:
            err_msg = str(e).lower()
            if "rate limit" in err_msg or "too many requests" in err_msg:
                raise RuntimeError(
                    "Trop de tentatives d'inscription. Attends quelques minutes avant de reessayer."
                )
            elif "already exists" in err_msg or "user already registered" in err_msg:
                raise RuntimeError("Cet email est deja utilise. Utilise Log in ou choisis un autre email.")
            else:
                raise RuntimeError(f"Inscription echouee: {e}")

        # Le profil est créé automatiquement par la fonction SQL trigger
        # Connexion directe sans vérifier l'email
        return self.login(email, password)

    def login(self, email: str, password: str) -> dict[str, Any]:
        self._require_client()

        try:
            auth = self.client.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password,
                }
            )
        except Exception as e:
            err_msg = str(e).lower()
            if "invalid grant" in err_msg or "invalid credentials" in err_msg:
                raise RuntimeError("Email ou mot de passe incorrect.")
            elif "unconfirmed" in err_msg or "not confirmed" in err_msg:
                # Ignorer l'erreur d'email non confirmé - permettre la connexion quand même
                pass
            elif "rate limit" in err_msg or "too many requests" in err_msg:
                raise RuntimeError("Trop de tentatives. Attends quelques minutes avant de reessayer.")
            else:
                raise RuntimeError(f"Connexion echouee: {e}")

        if not auth or not auth.user:
            raise RuntimeError("Connexion echouee: utilisateur introuvable.")

        return self._ensure_profile(auth.user)

    def _ensure_profile(self, user) -> dict[str, Any]:
        import datetime
        user_id = user.id
        user_meta = user.user_metadata or {}
        profile = {
            "id": user_id,
            "email": user.email,
            "nickname": user_meta.get("nickname") or user.email.split("@")[0],
            "avatar": user_meta.get("avatar") or "⚽",
            "online_status": "online",  # Marquer comme en ligne à la connexion
            "last_seen": datetime.datetime.utcnow().isoformat(),
        }

        existing = (
            self.client.table("profiles")
            .select("id,email,nickname,avatar,online_status,last_seen")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        rows = existing.data or []

        if rows:
            # Mettre à jour le statut online seulement
            self.client.table("profiles").update({
                "online_status": "online",
                "last_seen": datetime.datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
            profile.update(rows[0])
            profile["online_status"] = "online"  # S'assurer que c'est à jour
        else:
            (
                self.client.table("profiles")
                .upsert(profile, on_conflict="id")
                .execute()
            )

        return profile

    def save_match_score(
        self,
        user_id: str,
        mode: str,
        team_rouge_name: str,
        team_bleu_name: str,
        team_rouge_score: int,
        team_bleu_score: int,
        winner: str,
    ) -> None:
        self._require_client()
        payload = {
            "user_id": user_id,
            "mode": mode,
            "team_rouge_name": team_rouge_name,
            "team_bleu_name": team_bleu_name,
            "team_rouge_score": team_rouge_score,
            "team_bleu_score": team_bleu_score,
            "winner": winner,
        }
        self.client.table("score_history").insert(payload).execute()

    def get_score_history(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        self._require_client()
        resp = (
            self.client.table("score_history")
            .select(
                "created_at,mode,team_rouge_name,team_bleu_name,"
                "team_rouge_score,team_bleu_score,winner"
            )
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
