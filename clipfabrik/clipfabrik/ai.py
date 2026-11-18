"""Optionale KI-Bewertung über Ollama (läuft lokal, kostenlos). Ohne Ollama bleibt die Chat-Note."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

from . import media

PROMPT = """Du bist ein strenger Shorts-Editor für Twitch-Clips (TikTok/YouTube Shorts).
Du bekommst Standbilder aus einem Clip und die Chatzeilen dazu.
Bewerte auf einer Skala 1-10, wie viral der Moment ist. Die meisten Momente sind Mittelmaß (4-6).
keep=false bei Langeweile, Ladebildschirm, Cutscene, Werbung oder Spoiler. Nichts erfinden.
Hook: max. 6 Wörter, macht neugierig, Sprache: {lang}. Titel: max. 8 Wörter.
Antworte NUR als JSON:
{{"keep": true, "hype": 7, "hook": "...", "title": "...", "cutscene": false, "reason": "..."}}

Streamer: {streamer}
Chat:
{chat}"""


def parse(text: str) -> dict:
    """Robust: JSON auch aus Text mit Drumherum fischen, Werte prüfen."""
    a, b = text.find("{"), text.rfind("}")
    data = json.loads(text[a:b + 1]) if a >= 0 and b > a else {}
    hype = float(data.get("hype", 0) or 0)
    return {
        "keep": bool(data.get("keep", hype >= 5)) and not bool(data.get("cutscene", False)),
        "hype": max(1.0, min(10.0, hype)) if hype else None,
        "hook": str(data.get("hook", "")).strip()[:60],
        "title": str(data.get("title", "")).strip()[:80],
        "reason": str(data.get("reason", "")).strip()[:160],
    }


def judge(cfg: dict, clip: dict, raw: Path, offset: float, workdir: Path, lang: str) -> dict:
    dur = clip["end"] - clip["start"]
    images = []
    for i, frac in enumerate((0.45, 0.7, 0.9)):    # Höhepunkt liegt im hinteren Teil
        f = workdir / f"ai{i}.jpg"
        media.frame(raw, f, offset + dur * frac)
        images.append(base64.b64encode(f.read_bytes()).decode())
        f.unlink(missing_ok=True)
    chat = "\n".join(json.loads(clip.get("chat") or "[]")[-25:])
    body = {"model": cfg["ollama_model"], "stream": False, "format": "json", "images": images,
            "prompt": PROMPT.format(lang="Deutsch" if lang == "de" else "English",
                                    streamer=clip["streamer"], chat=chat),
            "options": {"temperature": 0.2}}
    req = urllib.request.Request(cfg["ollama_url"].rstrip("/") + "/api/generate",
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return parse(json.loads(r.read()).get("response", ""))
