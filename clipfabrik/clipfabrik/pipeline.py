"""Orchestrator: ein Prozess, viele Worker. Der Supervisor startet abgestürzte Worker neu."""
from __future__ import annotations

import json
import random
import shutil
import threading
import time
import traceback
from collections import deque
from pathlib import Path

from . import config, db, media, telegram
from .chat import ChatClient
from .detect import Detector
from .recorder import Recorder


class Pipeline:
    def __init__(self):
        self.cfg = config.load()
        self.logs: deque = deque(maxlen=200)
        self.streamers: dict[str, dict] = {}     # UI-Status je Streamer
        self.workers: dict[str, str] = {}
        self.recorders: dict[str, Recorder] = {}
        self.detector = Detector(self.cfg)
        self.chat = ChatClient(self._on_chat, self.log)
        self.last_delivery = 0.0
        self.tg_offset = 0
        self.started = time.time()
        db.init()
        db.recover()

    # ---------- Grundlagen ----------
    def log(self, msg: str) -> None:
        self.logs.appendleft({"t": time.time(), "msg": msg})

    def get_cfg(self) -> dict:
        return self.cfg

    def set_cfg(self, new: dict) -> dict:
        merged = dict(self.cfg)
        merged.update(new)
        self.cfg = config.save(merged)
        self.detector.cfg = self.cfg
        self.log("Einstellungen gespeichert")
        return self.cfg

    def start(self) -> None:
        self._spawn("chat", self.chat.run, loop=False)
        self._spawn("manager", self._manage, every=3)
        self._spawn("detector", self._detect_tick, every=1)
        self._spawn("cutter", self._cut_one, every=2)
        self._spawn("judge", self._judge_one, every=2)
        self._spawn("renderer", self._render_one, every=2)
        self._spawn("delivery", self._deliver_one, every=5)
        self._spawn("telegram", self._telegram_poll, every=1)
        self._spawn("cleanup", self._cleanup, every=600)
        self.log("ClipFabrik gestartet")

    def _spawn(self, name: str, fn, every: float = 1, loop: bool = True) -> None:
        def runner():
            backoff = 2
            while True:
                try:
                    self.workers[name] = "läuft"
                    if not loop:
                        fn()
                    else:
                        while True:
                            fn()
                            time.sleep(every)
                except Exception as e:
                    self.workers[name] = f"neu gestartet ({e.__class__.__name__})"
                    self.log(f"Worker {name} abgestürzt: {e}")
                    traceback.print_exc()
                    time.sleep(backoff)
                    backoff = min(60, backoff * 2)
        threading.Thread(target=runner, daemon=True, name=name).start()

    # ---------- Aufnahme & Chat ----------
    def _manage(self) -> None:
        wanted = {s["login"] for s in self.cfg["streamers"]}
        for login in wanted - self.recorders.keys():
            st = self.streamers.setdefault(login, {"live": False, "recording": False, "status": "prüfe …",
                                                   "category": "", "z": 0, "rate": 0, "clips": 0})
            r = Recorder(login, self.get_cfg, st, self.log)
            self.recorders[login] = r
            r.start()
        for login in list(self.recorders.keys() - wanted):
            self.recorders.pop(login).stop.set()
            self.streamers.pop(login, None)
        self.chat.set_channels(wanted)

    def _on_chat(self, ch: str, ts: float, user: str, text: str) -> None:
        self.detector.feed(ch, ts, user, text)

    def _detect_tick(self) -> None:
        now = time.time()
        for login, st in list(self.streamers.items()):
            stats = self.detector.stats(login)
            st["rate"] = stats.rate(now, 60)
            if not st.get("recording"):
                continue
            snap = stats.snapshot(now)
            st["z"] = snap["z"]
            trig = self.detector.check(login, now)
            if trig:
                self.add_candidate(login, trig)

    def add_candidate(self, login: str, trig) -> int | None:
        c = self.cfg
        start, end = trig.peak - c["pre_seconds"], trig.peak + c["post_seconds"]
        if trig.score < 3:
            return None                                   # schwacher Vorab-Score fällt sofort weg
        dup = db.overlapping(login, start, end)
        if dup:
            if dup["pre_score"] >= trig.score or dup["status"] != "NEW":
                return None
            db.update(dup["id"], status="REJECTED", error="Duplikat (schwächer)")
        cid = db.add_clip(login, trig.peak, start, end, trig.score, trig.signals, trig.chat)
        if login in self.streamers:
            self.streamers[login]["clips"] = self.streamers[login].get("clips", 0) + 1
        self.log(f"{login}: Moment erkannt (Vorab-Score {trig.score}, z={trig.signals.get('z')})")
        return cid

    # ---------- Verarbeitung ----------
    def clip_dir(self, cid: int) -> Path:
        d = config.CLIPS / f"{cid:06d}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _cut_one(self) -> None:
        clip = db.next_with("NEW", ready_before=time.time() - self.cfg["segment_seconds"] - 2)
        if not clip:
            return
        try:
            raw = self.clip_dir(clip["id"]) / "raw.ts"
            offset = media.cut(config.BUFFER / clip["streamer"], clip["start"], clip["end"], raw)
            sig = json.loads(clip["signals"] or "{}")
            sig["raw_offset"] = offset
            db.update(clip["id"], status="CUT", raw_path=str(raw), signals=json.dumps(sig))
        except Exception as e:
            db.update(clip["id"], status="FAILED", error=f"Schnitt: {e}")

    def _judge_one(self) -> None:
        clip = db.next_with("CUT")
        if not clip:
            return
        # v1: Bewertung aus den Chat-Signalen. Hook für lokale/Cloud-KI: judge_ai() unten.
        score = clip["pre_score"]
        title = make_title(clip)
        if score < self.cfg["min_score"]:
            db.update(clip["id"], status="REJECTED", score=score, title=title,
                      error=f"unter Mindestnote ({score} < {self.cfg['min_score']})")
        else:
            db.update(clip["id"], status="JUDGED", score=score, title=title)

    def _render_one(self) -> None:
        clip = db.next_with("JUDGED")
        if not clip:
            return
        self.render_clip(clip)

    def render_clip(self, clip: dict) -> None:
        try:
            d = self.clip_dir(clip["id"])
            sig = json.loads(clip["signals"] or "{}")
            s = next((x for x in self.cfg["streamers"] if x["login"] == clip["streamer"]), {})
            duration = clip["end"] - clip["start"]
            out = d / "clip.mp4"
            words: list = []
            if self.cfg["subtitles"]:
                try:
                    words = media.transcribe(Path(clip["raw_path"]), self.cfg["whisper_model"], s.get("lang"))
                    off = sig.get("raw_offset", 0)
                    words = [(a - off, b - off, w) for a, b, w in words if b > off and a < off + duration]
                except Exception as e:
                    self.log(f"Untertitel übersprungen: {e}")
            ass = media.build_ass(words, duration, f"twitch.tv/{clip['streamer']}", clip["title"])
            media.render(Path(clip["raw_path"]), sig.get("raw_offset", 0), duration, out, s.get("facecam"), ass)
            (d / "src.mp4").unlink(missing_ok=True)
            db.update(clip["id"], status="RENDERED", out_path=str(out), error="")
            self.log(f"Clip #{clip['id']} fertig ({clip['streamer']}, Note {clip['score']})")
        except Exception as e:
            db.update(clip["id"], status="FAILED", error=f"Render: {e}")
            self.log(f"Clip #{clip['id']} Render-Fehler: {str(e)[:120]}")

    def _deliver_one(self) -> None:
        c = self.cfg
        if not (c["telegram_token"] and c["telegram_chat_id"]):
            return
        if time.time() - self.last_delivery < 45:          # fester Takt, der beste zuerst
            return
        clip = db.next_with("RENDERED")
        if not clip:
            return
        try:
            mid = telegram.send_video(c["telegram_token"], c["telegram_chat_id"], Path(clip["out_path"]),
                                      text_block(clip, self.streamers.get(clip["streamer"], {})), clip["id"])
            db.update(clip["id"], status="DELIVERED", tg_message=mid)
            self.last_delivery = time.time()
        except Exception as e:
            self.log(f"Telegram: {str(e)[:120]}")
            self.last_delivery = time.time()

    def _telegram_poll(self) -> None:
        token = self.cfg["telegram_token"]
        if not token:
            time.sleep(5)
            return
        self.tg_offset, actions = telegram.poll(token, self.tg_offset)
        for act, cid, cb in actions:
            self.action(cid, act)
            try:
                telegram.call(token, "answerCallbackQuery", {"callback_query_id": cb, "text": "Erledigt"})
            except Exception:
                pass

    def action(self, cid: int, act: str) -> bool:
        clip = db.get(cid)
        if not clip:
            return False
        if act == "posted":
            db.update(cid, status="POSTED")
        elif act == "reject":
            db.update(cid, status="REJECTED", error="von dir verworfen")
        elif act == "rerender" and clip["raw_path"]:
            db.update(cid, status="JUDGED", score=clip["score"] or clip["pre_score"])
        else:
            return False
        return True

    def _cleanup(self) -> None:
        cutoff = time.time() - self.cfg["keep_clips_days"] * 86400
        for d in config.CLIPS.glob("*"):
            if d.is_dir() and d.stat().st_mtime < cutoff:
                shutil.rmtree(d, ignore_errors=True)
        for d in config.CLIPS.glob("*/raw.ts"):            # Rohschnitte fertiger Clips nach 1 Tag weg
            if d.stat().st_mtime < time.time() - 86400:
                d.unlink(missing_ok=True)

    # ---------- Für die UI ----------
    def snapshot(self) -> dict:
        return {
            "streamers": self.streamers,
            "workers": self.workers,
            "chat_connected": self.chat.connected,
            "counts": db.counts(),
            "clips": db.recent(60),
            "logs": list(self.logs)[:60],
            "uptime": time.time() - self.started,
            "now": time.time(),
        }

    # ---------- Demo ohne Twitch ----------
    def demo(self) -> int | None:
        """Erzeugt ein Testvideo + simulierten Chat-Ausschlag und schickt beides durch die Pipeline."""
        login = "demo"
        buf = config.BUFFER / login
        buf.mkdir(parents=True, exist_ok=True)
        tmp = buf / "_gen"
        tmp.mkdir(exist_ok=True)
        media.run(["-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30:duration=60",
                   "-f", "lavfi", "-i", "sine=frequency=330:duration=60",
                   "-c:v", "libx264", "-preset", "ultrafast", "-g", "30", "-c:a", "aac", "-shortest",
                   "-f", "segment", "-segment_time", "6", "-reset_timestamps", "1", str(tmp / "s%03d.ts")])
        now = time.time()
        files = sorted(tmp.glob("s*.ts"))
        base = now - len(files) * 6
        for i, f in enumerate(files):
            name = time.strftime(media.SEG_FMT, time.localtime(base + i * 6)) + ".ts"
            f.replace(buf / name)
        shutil.rmtree(tmp, ignore_errors=True)
        # Chat simulieren: ruhige Baseline, dann Ausschlag
        det = Detector(self.cfg)
        t0 = now - 340
        for s in range(330):
            for _ in range(random.randint(0, 2)):
                det.feed(login, t0 + s + random.random(), f"user{random.randint(1, 40)}", "hallo")
        peak = now - 20
        for i in range(40):
            det.feed(login, peak - random.random() * 9, f"fan{i}", random.choice(["KEKW 💀", "NO WAY", "clip it", "OMG 😂"]))
        trig = det.check(login, peak)
        if not trig:
            return None
        self.log("Demo: Testclip angelegt")
        return self.add_candidate(login, trig)


def make_title(clip: dict) -> str:
    sig = json.loads(clip.get("signals") or "{}")
    if sig.get("clip_calls", 0) >= 3:
        return "Chat ruft CLIP IT 😳"
    if sig.get("hype", 0) >= 5:
        return "Der Chat eskaliert 💀"
    return "Dieser Moment …"


def text_block(clip: dict, st: dict) -> str:
    login = clip["streamer"]
    cat = (st.get("category") or "").strip()
    tags = ["#twitch", f"#{login}", "#clips", "#fyp"]
    if "grand theft auto" in cat.lower() or "gta" in cat.lower():
        tags[2:2] = ["#gta6", "#gta"]
    return (f"🎬 {clip['title']}\n\n"
            f"Titel: {login}: {clip['title']}\n"
            f"Caption: {clip['title']} | Quelle: twitch.tv/{login}\n"
            f"Hashtags: {' '.join(tags)}\n"
            f"Quelle: https://twitch.tv/{login}\n"
            f"Note: {clip['score']}/10")
