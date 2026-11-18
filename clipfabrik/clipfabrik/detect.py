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
        }


def pre_score(s: dict) -> float:
    """Signale zu einer Note 1-10. Einfach und nachvollziehbar gehalten."""
    score = 2.0
    score += min(4.0, max(0.0, s["z"]) * 0.5)
    score += min(1.5, s["unique_ratio"] * 1.5)
    score += min(1.5, s["hype"] / max(1, s["burst"]) * 3)
    score += min(1.5, s["clip_calls"] * 0.5)
    return round(max(1.0, min(10.0, score)), 1)


class Detector:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.channels: dict[str, ChannelStats] = {}

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
        by_z = s["warm"] and s["z"] >= self.cfg["z_threshold"] and s["unique"] >= self.cfg["min_unique_users"]
        by_calls = s["clip_calls"] >= self.cfg["clip_calls"]
        if not (by_z or by_calls):
            return None
        st.last_trigger = now
        chat = [f"{m[1]}: {m[2]}" for m in st.msgs if m[0] > now - 40]
        return Trigger(peak=now, score=pre_score(s), signals=s, chat=chat)
