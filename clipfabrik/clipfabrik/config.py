"""Einstellungen laden/speichern. Alles liegt lokal in data/settings.json (nicht im Repo)."""
from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path


def app_dir() -> Path:
    """Ordner neben der .exe bzw. dem Projekt; dort liegt data/."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


DATA = Path(os.environ.get("CLIPFABRIK_DATA", app_dir() / "data"))
BUFFER = DATA / "buffer"
CLIPS = DATA / "clips"
SETTINGS_FILE = DATA / "settings.json"

DEFAULTS: dict = {
    "streamers": [],            # [{"login": "xqc", "lang": "en", "facecam": null}]
    "category_filter": "",      # z. B. "Grand Theft Auto" -> nur aufnehmen, wenn Kategorie passt
    "quality": "480p,720p,best",
    "buffer_minutes": 4,
    "segment_seconds": 6,
    "live_check_seconds": 60,
    # Erkennung
    "burst_seconds": 10,
    "baseline_minutes": 5,
    "z_threshold": 4.0,
    "min_unique_users": 6,
    "clip_calls": 3,
    "cooldown_seconds": 90,
    "pre_seconds": 28,          # Chat reagiert verzögert: Clip startet vor dem Ausschlag
    "post_seconds": 6,
    "min_score": 5,             # Mindestnote 1-10
    # Ausgabe
    "subtitles": True,          # braucht faster-whisper (optional)
    "whisper_model": "small",
    "telegram_token": "",
    "telegram_chat_id": "",
    "keep_clips_days": 7,
    "lan_access": False,
    # Geld & Qualität
    "default_cpm": 1.0,         # € pro 1000 Views, wenn beim Streamer nichts steht (Kampagnen-Satz)
    "posts_per_day": 4,
    "progress_bar": True,       # Fortschrittsbalken im Clip (hält Zuschauer länger)
    "ollama_model": "",         # z. B. "llava" oder "qwen2.5vl" -> KI-Bewertung lokal; leer = aus
    "ollama_url": "http://127.0.0.1:11434",
    "port": 8765,
}

_lock = threading.Lock()


def ensure_dirs() -> None:
    for d in (DATA, BUFFER, CLIPS):
        d.mkdir(parents=True, exist_ok=True)


def load() -> dict:
    ensure_dirs()
    cfg = dict(DEFAULTS)
    if SETTINGS_FILE.exists():
        try:
            cfg.update(json.loads(SETTINGS_FILE.read_text("utf-8")))
        except (OSError, ValueError):
            pass
    return cfg


def save(cfg: dict) -> dict:
    ensure_dirs()
    clean = {k: cfg.get(k, v) for k, v in DEFAULTS.items()}
    clean["streamers"] = normalize_streamers(clean["streamers"])
    with _lock:
        tmp = SETTINGS_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(clean, indent=2, ensure_ascii=False), "utf-8")
        tmp.replace(SETTINGS_FILE)
    return clean


def normalize_streamers(items) -> list[dict]:
    out, seen = [], set()
    for it in items or []:
        if isinstance(it, str):
            it = {"login": it}
        login = str(it.get("login", "")).strip().lower()
        login = login.replace("https://", "").replace("www.", "").replace("twitch.tv/", "").strip("/ @")
        if not login or login in seen:
            continue
        seen.add(login)
        try:
            cpm = float(it["cpm"]) if it.get("cpm") not in (None, "") else None
        except (TypeError, ValueError):
            cpm = None
        out.append({"login": login, "lang": it.get("lang", "de"), "facecam": it.get("facecam"), "cpm": cpm})
    return out
