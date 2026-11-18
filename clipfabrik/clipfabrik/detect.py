"""Chat-Statistik: robuster z-Wert, verschiedene Nutzer, Hype-Wörter, Clip-Rufe."""
from __future__ import annotations

import re
import statistics
from collections import deque
from dataclasses import dataclass, field

HYPE = re.compile(
    r"(💀|😂|🤣|😭|🔥|omg|wtf|lol|lmao|kekw|lul|omegalul|pog|pogchamp|poggers|"
    r"no way|holy|insane|bro|digga|alter|krass|haha|xd|monkas|clap|ez|gg)",
    re.IGNORECASE,
)
# Clip-Arten nach Emotes/Wörtern (Twitch-Kultur). Reihenfolge = Priorität bei Gleichstand.
CATEGORIES = {
    "lustig": re.compile(r"(kekw|lul|lulw|omegalul|icant|😂|🤣|haha|hahaha|xd|lmao|lol|ich kann nicht|💀💀)", re.I),
    "fail": re.compile(r"(\bf\b|rip|💀|bruh|unlucky|throw|sadge|noooo?|wie kann man|unglaublich schlecht)", re.I),
    "krass": re.compile(r"(pog|pogchamp|poggers|insane|clean|clutch|🔥|cracked|goat|\bw\b|sheesh|was ein play|krass)", re.I),
    "schock": re.compile(r"(wtf|no way|monkas|holy|😳|😱|what|was\?+|omg|digga|alter)", re.I),
    "rage": re.compile(r"(rage|angry|madge|😡|ausraster|tilt|bro is mad)", re.I),
    "wholesome": re.compile(r"(❤|<3|aww|wholesome|süß|cute|🥺)", re.I),
}


def classify(texts: list[str]) -> str:
    """Welche Art Moment? Zählt pro Kategorie die Nachrichten mit passenden Emotes/Wörtern."""
    counts = {k: sum(1 for t in texts if rx.search(t)) for k, rx in CATEGORIES.items()}
    best = max(counts, key=counts.get) if counts else "unklar"
    return best if counts.get(best, 0) >= max(2, len(texts) * 0.15) else "unklar"


CLIP = re.compile(r"\bclip\b|\bclipp?\s*(it|that|das)\b", re.IGNORECASE)


@dataclass
class Trigger:
    peak: float
    score: float          # Vorab-Score 1-10
    signals: dict
    chat: list[str]


@dataclass
class ChannelStats:
    burst_s: int = 10
    baseline_s: int = 300
    msgs: deque = field(default_factory=deque)      # (ts, user, text)
    last_trigger: float = 0.0

    def add(self, ts: float, user: str, text: str) -> None:
        self.msgs.append((ts, user, text))
        horizon = ts - self.baseline_s - self.burst_s
        while self.msgs and self.msgs[0][0] < horizon:
            self.msgs.popleft()

    def rate(self, now: float, seconds: float) -> int:
        return sum(1 for m in self.msgs if m[0] > now - seconds)

    @staticmethod
    def _capped(msgs) -> int:
        """Nachrichten zählen, aber höchstens 2 pro Nutzer: einzelne Spammer verziehen nichts."""
        per: dict[str, int] = {}
        for m in msgs:
            per[m[1]] = per.get(m[1], 0) + 1
        return sum(min(2, n) for n in per.values())

    def snapshot(self, now: float) -> dict:
        b = self.burst_s
        recent = [m for m in self.msgs if m[0] > now - b]
        # Baseline: Nachrichten pro Burst-Fenster der letzten Minuten (ohne das aktuelle)
        windows = []
        t = now - b
        while t - b >= now - self.baseline_s - b:
            windows.append(self._capped(m for m in self.msgs if t - b < m[0] <= t))
            t -= b
        if len(windows) >= 3:
            med = statistics.median(windows)
            mad = statistics.median([abs(w - med) for w in windows])
        else:
            med, mad = 0.0, 0.0
        burst = self._capped(recent)
        z = (burst - med) / (1.4826 * mad + 1)
        users = {m[1] for m in recent}
        hype = sum(1 for m in recent if HYPE.search(m[2]))
        texts = [m[2].strip().lower() for m in recent]
        top = max((texts.count(t) for t in set(texts)), default=0)
        clips = len({m[1] for m in self.msgs if m[0] > now - 15 and CLIP.search(m[2])})  # verschiedene Rufer
        return {
            "burst": burst,
            "median": round(med, 2),
            "z": round(z, 2),
            "unique": len(users),
            "unique_ratio": round(len(users) / len(recent), 2) if recent else 0.0,
            "hype": hype,
            "clip_calls": clips,
            "warm": len(windows) >= 3,
            "emote_wall": round(top / len(texts), 2) if len(texts) >= 5 else 0.0,  # alle spammen das Gleiche
            "category": classify([m[2] for m in recent]),
        }


def pre_score(s: dict) -> float:
    """Signale zu einer Note 1-10. Einfach und nachvollziehbar gehalten."""
    score = 2.0
    score += min(4.0, max(0.0, s["z"]) * 0.5)
    score += min(1.5, s["unique_ratio"] * 1.5)
    score += min(1.5, s["hype"] / max(1, s["burst"]) * 3)
    score += min(1.5, s["clip_calls"] * 0.5)
    score += min(0.8, s.get("emote_wall", 0) * 1.5)
    score += min(3.5, max(0.0, s.get("audio_z", 0) - 1.5) * 0.5)   # Streamer wird laut/lacht/schreit
    return round(max(1.0, min(10.0, score)), 1)


@dataclass
class AudioStats:
    """Lautstärke des Streams (dBFS je 0,5 s). Robuster z-Wert wie beim Chat."""
    baseline_s: int = 300
    samples: deque = field(default_factory=deque)      # (ts, db)
    last_trigger: float = 0.0
    last_checked: float = 0.0

    def add(self, ts: float, db: float) -> None:
        self.samples.append((ts, db))
        while self.samples and self.samples[0][0] < ts - self.baseline_s:
            self.samples.popleft()

    def snapshot(self, at: float, window: float = 3.0) -> dict:
        recent = [d for t, d in self.samples if at - window < t <= at]
        base = [d for t, d in self.samples if t <= at - window]
        if len(base) < 60 or not recent:                # mind. 30 s Vorlauf
            return {"audio_z": 0.0, "audio_db": max(recent) if recent else -90.0, "audio_warm": False}
        med = statistics.median(base)
        mad = statistics.median([abs(b - med) for b in base])
        # Mittel der lautesten Hälfte: ein einzelner Knall zählt weniger als anhaltendes Schreien/Lachen
        top = sorted(recent, reverse=True)[:max(1, len(recent) // 2)]
        level = sum(top) / len(top)
        scale = 1.4826 * mad + 1.0
        loud_n = sum(1 for d in recent if (d - med) / scale >= 2.5)   # wie lange es laut ist (je 0,5 s)
        return {"audio_z": round((level - med) / scale, 2), "audio_db": round(level, 1),
                "audio_warm": True, "audio_loud_s": loud_n * 0.5}


class Detector:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.channels: dict[str, ChannelStats] = {}
        self.audio: dict[str, AudioStats] = {}

    def audio_stats(self, ch: str) -> AudioStats:
        if ch not in self.audio:
            self.audio[ch] = AudioStats(self.cfg["baseline_minutes"] * 60)
        return self.audio[ch]

    def feed_audio(self, ch: str, ts: float, db: float) -> None:
        self.audio_stats(ch).add(ts, db)

    def check_audio(self, ch: str) -> Trigger | None:
        """Ton-Auslöser: Streamer wird deutlich lauter als sonst, auch wenn der Chat ruhig ist."""
        if not self.cfg.get("audio_detection", True):
            return None
        au = self.audio_stats(ch)
        st = self.stats(ch)
        cool = self.cfg["cooldown_seconds"]
        # Alle neuen Messpunkte seit der letzten Prüfung durchgehen (sonst entgeht uns die Mitte eines Segments)
        new = [t for t, _ in au.samples if t > au.last_checked]
        if not new:
            return None
        au.last_checked = new[-1]
        thr = self.cfg.get("audio_z_threshold", 3.5)
        best = None
        for at in new:
            if at - au.last_trigger < cool or abs(at - st.last_trigger) < cool / 2:
                continue
            a = au.snapshot(at)
            if a["audio_warm"] and a["audio_z"] >= thr and a["audio_db"] >= -35 and a["audio_loud_s"] >= 1.5:
                if best is None or a["audio_z"] > best[1]["audio_z"]:
                    best = (at, a)
            elif best:
                break                               # Höhepunkt vorbei: lautesten Punkt nehmen
        if not best:
            return None
        at, a = best
        au.last_trigger = at
        s = st.snapshot(at + 8)     # Chat reagiert verzögert: die Sekunden danach mitnehmen
        s.update(a)
        if s["category"] == "unklar":
            s["category"] = "reaktion"
        s["source"] = "ton"
        chat = [f"{m[1]}: {m[2]}" for m in st.msgs if at - 20 < m[0] <= at + 10]
        return Trigger(peak=at, score=pre_score(s), signals=s, chat=chat)

    def stats(self, ch: str) -> ChannelStats:
        if ch not in self.channels:
            self.channels[ch] = ChannelStats(self.cfg["burst_seconds"], self.cfg["baseline_minutes"] * 60)
        return self.channels[ch]

    def feed(self, ch: str, ts: float, user: str, text: str) -> None:
        self.stats(ch).add(ts, user, text)

    def check(self, ch: str, now: float) -> Trigger | None:
        st = self.stats(ch)
        if now - st.last_trigger < self.cfg["cooldown_seconds"]:
            return None
        s = st.snapshot(now)
        # Ton der letzten ~15 s (Chat hängt hinterher) verstärkt die Note
        au = self.audio.get(ch)
        if au and au.samples:
            a = au.snapshot(now - 6, window=12)
            s.update(a)
        by_z = s["warm"] and s["z"] >= self.cfg["z_threshold"] and s["unique"] >= self.cfg["min_unique_users"]
        by_calls = s["clip_calls"] >= self.cfg["clip_calls"]
        if not (by_z or by_calls):
            return None
        st.last_trigger = now
        s["source"] = "chat"
        chat = [f"{m[1]}: {m[2]}" for m in st.msgs if m[0] > now - 40]
        return Trigger(peak=now, score=pre_score(s), signals=s, chat=chat)
