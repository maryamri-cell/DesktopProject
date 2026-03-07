# ============================================================
# game/image_loader.py — Téléchargement de photos joueurs
# via Pollinations.ai + cache local
# ============================================================

import os
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap

from config import IMAGES_DIR


# Dossier de cache
Path(IMAGES_DIR).mkdir(parents=True, exist_ok=True)


def _safe_filename(name: str) -> str:
    """Génère un nom de fichier sûr à partir du nom du joueur."""
    h = hashlib.md5(name.encode("utf-8")).hexdigest()[:8]
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    return f"{safe}_{h}.jpg"


def _build_url(player_name: str, club: str = "", width: int = 256, height: int = 256) -> str:
    """
    Construit l'URL Pollinations.ai pour générer un portrait réaliste.
    """
    prompt = f"Professional football player portrait photo of {player_name}"
    if club:
        prompt += f" wearing {club} jersey"
    prompt += ", studio lighting, face close-up, clean background, FIFA style"

    encoded = urllib.parse.quote(prompt, safe="")
    return f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true"


def get_cached_path(player_name: str) -> str | None:
    """Retourne le chemin local si l'image est déjà en cache, sinon None."""
    fname = _safe_filename(player_name)
    path = os.path.join(IMAGES_DIR, fname)
    if os.path.isfile(path) and os.path.getsize(path) > 500:
        return path
    return None


def download_image_sync(player_name: str, club: str = "") -> str | None:
    """
    Télécharge l'image du joueur de manière synchrone.
    Retourne le chemin local ou None en cas d'erreur.
    """
    cached = get_cached_path(player_name)
    if cached:
        return cached

    url = _build_url(player_name, club)
    fname = _safe_filename(player_name)
    dest = os.path.join(IMAGES_DIR, fname)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AhsanKhota/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            if len(data) < 500:
                return None
            with open(dest, "wb") as f:
                f.write(data)
        return dest
    except Exception:
        return None


# ============================================================
# Worker thread pour téléchargement asynchrone (Qt)
# ============================================================

class _DownloadWorker(QThread):
    """Thread qui télécharge une image de joueur."""
    finished = pyqtSignal(str, str)  # (player_name, local_path_or_empty)

    def __init__(self, player_name: str, club: str = ""):
        super().__init__()
        self._name = player_name
        self._club = club

    def run(self):
        path = download_image_sync(self._name, self._club)
        self.finished.emit(self._name, path or "")


class ImageLoader(QObject):
    """
    Gestionnaire de téléchargement d'images non-bloquant.
    Émet image_ready(player_name, local_path) quand une image est prête.
    """
    image_ready = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._workers: list[_DownloadWorker] = []

    def request_image(self, player_name: str, club: str = ""):
        """
        Demande le téléchargement d'une image.
        Si déjà en cache, émet immédiatement.
        """
        cached = get_cached_path(player_name)
        if cached:
            self.image_ready.emit(player_name, cached)
            return

        worker = _DownloadWorker(player_name, club)
        worker.finished.connect(self._on_downloaded)
        self._workers.append(worker)
        worker.start()

    def _on_downloaded(self, name: str, path: str):
        if path:
            self.image_ready.emit(name, path)
        # Nettoyage du worker
        self._workers = [w for w in self._workers if w.isRunning()]

    def cancel_all(self):
        """Annule tous les téléchargements en cours."""
        for w in self._workers:
            if w.isRunning():
                w.quit()
                w.wait(2000)
        self._workers.clear()


def load_pixmap(player_name: str, size: int = 128) -> QPixmap | None:
    """
    Charge un QPixmap depuis le cache.
    Retourne None si l'image n'est pas en cache.
    """
    cached = get_cached_path(player_name)
    if cached:
        px = QPixmap(cached)
        if not px.isNull():
            return px.scaled(size, size)
    return None


# ============================================================
# TEST
# ============================================================
if __name__ == "__main__":
    print(f"Cache dir: {IMAGES_DIR}")
    print(f"URL exemple: {_build_url('Lionel Messi', 'Inter Miami')}")

    # Test synchrone
    path = download_image_sync("Lionel Messi", "Inter Miami")
    if path:
        print(f"Image téléchargée : {path}")
    else:
        print("Erreur de téléchargement")
