# ============================================================
# game/image_loader.py — Téléchargement de photos joueurs
# via SoFIFA CDN (vraies photos FIFA) + cache local
# ============================================================

import os
import urllib.request
import ssl
from pathlib import Path
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap

from config import IMAGES_DIR


# Dossier de cache
Path(IMAGES_DIR).mkdir(parents=True, exist_ok=True)

# URLs sources pour les visages FIFA (par ordre de priorité)
# SoFIFA CDN split le player_id en 2 blocs de 3 chiffres: 158023 → 158/023
_FACE_URLS = [
    "https://cdn.sofifa.net/players/{hi}/{lo}/24_120.png",
    "https://cdn.sofifa.net/players/{hi}/{lo}/24_60.png",
]


def _split_pid(player_id: int) -> tuple[str, str]:
    """Split player_id en (hi, lo) pour l'URL SoFIFA. Ex: 158023 → ('158','023')."""
    s = str(player_id).zfill(6)
    return s[:-3], s[-3:]


def _get_path(player_id: int) -> str:
    """Chemin local du cache pour un joueur."""
    return os.path.join(IMAGES_DIR, f"{player_id}.png")


def get_cached_path(player_id: int) -> str | None:
    """Retourne le chemin local si l'image est déjà en cache, sinon None."""
    path = _get_path(player_id)
    if os.path.isfile(path) and os.path.getsize(path) > 200:
        return path
    return None


def download_image_sync(player_id: int) -> str | None:
    """
    Télécharge la photo FIFA du joueur.
    Retourne le chemin local ou None en cas d'erreur.
    """
    cached = get_cached_path(player_id)
    if cached:
        return cached

    dest = _get_path(player_id)
    ctx = ssl.create_default_context()
    hi, lo = _split_pid(player_id)

    for url_template in _FACE_URLS:
        url = url_template.format(hi=hi, lo=lo)
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            })
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                if resp.status == 200:
                    data = resp.read()
                    if len(data) > 200:
                        with open(dest, "wb") as f:
                            f.write(data)
                        return dest
        except Exception:
            continue

    return None


# ============================================================
# Worker thread pour téléchargement asynchrone (Qt)
# ============================================================

class _DownloadWorker(QThread):
    """Thread qui télécharge une image de joueur."""
    finished = pyqtSignal(int, str)  # (player_id, local_path_or_empty)

    def __init__(self, player_id: int):
        super().__init__()
        self._pid = player_id

    def run(self):
        path = download_image_sync(self._pid)
        self.finished.emit(self._pid, path or "")


class ImageLoader(QObject):
    """
    Gestionnaire de téléchargement d'images non-bloquant.
    Émet image_ready(player_id, local_path) quand une image est prête.
    """
    image_ready = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._workers: list[_DownloadWorker] = []

    def request_image(self, player_id: int):
        """
        Demande le téléchargement d'une image.
        Si déjà en cache, émet immédiatement.
        """
        cached = get_cached_path(player_id)
        if cached:
            self.image_ready.emit(player_id, cached)
            return

        worker = _DownloadWorker(player_id)
        worker.finished.connect(self._on_downloaded)
        self._workers.append(worker)
        worker.start()

    def _on_downloaded(self, pid: int, path: str):
        if path:
            self.image_ready.emit(pid, path)
        self._workers = [w for w in self._workers if w.isRunning()]

    def cancel_all(self):
        """Annule tous les téléchargements en cours."""
        for w in self._workers:
            if w.isRunning():
                w.quit()
                w.wait(2000)
        self._workers.clear()


def load_pixmap(player_id: int, size: int = 128) -> QPixmap | None:
    """
    Charge un QPixmap depuis le cache.
    Retourne None si l'image n'est pas en cache.
    """
    cached = get_cached_path(player_id)
    if cached:
        px = QPixmap(cached)
        if not px.isNull():
            return px.scaled(size, size)
    return None
