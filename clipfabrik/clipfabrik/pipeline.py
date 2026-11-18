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

from . import ai, config, db, media, telegram
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
        self.audio_done: dict[str, float] = {}
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
        self._spawn("audio", self._audio_tick, every=2)
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

    def _audio_tick(self) -> None:
        """Neue fertige Puffer-Segmente anhören und Lautstärke in den Detektor geben."""
        if not self.cfg.get("audio_detection", True):
            return
        for login, st in list(self.streamers.items()):
            if not st.get("recording"):
                continue
            segs = media.segments(config.BUFFER / login)[:-1]        # das laufende Segment auslassen
            last = self.audio_done.get(login, 0.0)
            for t, path in segs:
                if t <= last:
                    continue
                try:
                    for i, db_ in enumerate(media.loudness(path)):
                        self.detector.feed_audio(login, t + i * 0.5, db_)
                except Exception:
                    pass
                self.audio_done[login] = t
            au = self.detector.audio.get(login)
            if au and au.samples:
                st["audio_z"] = au.snapshot(au.samples[-1][0])["audio_z"]
            trig = self.detector.check_audio(login)
            if trig:
                self.add_candidate(login, trig, window=(20, 10))

    def add_candidate(self, login: str, trig, dedupe: bool = True,
                      window: tuple[float, float] | None = None) -> int | None:
        c = self.cfg
        pre, post = window or (c["pre_seconds"], c["post_seconds"])
        start, end = trig.peak - pre, trig.peak + post
        if trig.score < 3:
            return None                                   # schwacher Vorab-Score fällt sofort weg
        dup = db.overlapping(login, start, end) if dedupe else None
        if dup:
            if dup["pre_score"] >= trig.score or dup["status"] != "NEW":
                return None
            db.update(dup["id"], status="REJECTED", error="Duplikat (schwächer)")
        cid = db.add_clip(login, trig.peak, start, end, trig.score, trig.signals, trig.chat)
        if login in self.streamers:
            self.streamers[login]["clips"] = self.streamers[login].get("clips", 0) + 1
        src = "Ton" if trig.signals.get("source") == "ton" else "Chat"
        self.log(f"{login}: Moment erkannt über {src} – {trig.signals.get('category', '?')} (Vorab {trig.score})")
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
        s = self.streamer_cfg(clip["streamer"])
        score = clip["pre_score"]
        title = make_title(clip, s.get("lang", "de"))
        if self.cfg.get("ollama_model"):
            try:
                sig = json.loads(clip["signals"] or "{}")
                v = ai.judge(self.cfg, clip, Path(clip["raw_path"]), sig.get("raw_offset", 0),
                             self.clip_dir(clip["id"]), s.get("lang", "de"))
                if v["hype"]:
                    score = round(0.4 * clip["pre_score"] + 0.6 * v["hype"], 1)
                title = v["hook"] or v["title"] or title
                if not v["keep"]:
                    db.update(clip["id"], status="REJECTED", score=score, title=title,
                              error=f"KI: {v['reason'] or 'nicht stark genug'}")
                    return
            except Exception as e:
                self.log(f"KI-Bewertung nicht erreichbar, nutze Chat-Note ({str(e)[:60]})")
        factor = self.learn_factor(json.loads(clip["signals"] or "{}").get("category", "unklar"))
        score = round(max(1.0, min(10.0, score * factor)), 1)
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
            s = self.streamer_cfg(clip["streamer"])
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
            media.render(Path(clip["raw_path"]), sig.get("raw_offset", 0), duration, out, s.get("facecam"), ass,
                         progress_bar=self.cfg.get("progress_bar", True))
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

    def streamer_cfg(self, login: str) -> dict:
        return next((x for x in self.cfg["streamers"] if x["login"] == login), {})

    def cpm(self, login: str) -> float:
        v = self.streamer_cfg(login).get("cpm")
        return float(v if v is not None else self.cfg.get("default_cpm", 1.0))

    def set_stats(self, cid: int, views: int, platform: str) -> bool:
        clip = db.get(cid)
        if not clip:
            return False
        db.update(cid, views=max(0, int(views)), platform=platform[:20], status="POSTED",
                  posted_at=clip.get("posted_at") or time.time())
        return True

    def trim(self, cid: int, d_start: float, d_end: float) -> bool:
        """Start/Ende verschieben (Sekunden) und neu rendern. Bleibt innerhalb des Rohschnitts."""
        clip = db.get(cid)
        if not clip or not clip["raw_path"] or not Path(clip["raw_path"]).exists():
            return False
        sig = json.loads(clip["signals"] or "{}")
        off = sig.get("raw_offset", 0)
        d_start = max(-off, d_start)
        start, end = clip["start"] + d_start, clip["end"] + d_end
        if end - start < 5:
            return False
        sig["raw_offset"] = off + d_start
        db.update(cid, start=start, end=end, signals=json.dumps(sig), status="JUDGED",
                  score=clip["score"] or clip["pre_score"])
        return True

    def set_facecam(self, login: str, box: dict | None) -> bool:
        streamers = [dict(s) for s in self.cfg["streamers"]]
        for s in streamers:
            if s["login"] == login:
                s["facecam"] = None if not box else {k: round(min(1, max(0, float(box[k]))), 4)
                                                     for k in ("x", "y", "w", "h")}
                self.set_cfg({"streamers": streamers})
                return True
        return False

    def preview_frame(self, login: str) -> Path | None:
        """Aktuelles Bild eines Streamers (aus dem Puffer, sonst aus dem letzten Clip)."""
        out = config.DATA / f"frame-{login}.jpg"
        segs = media.segments(config.BUFFER / login)
        src = segs[-2][1] if len(segs) >= 2 else (segs[-1][1] if segs else None)
        if src is None:
            raws = sorted(config.CLIPS.glob("*/raw.ts"), key=lambda p: p.stat().st_mtime, reverse=True)
            src = next((r for r in raws if (c := db.get(int(r.parent.name))) and c["streamer"] == login), None)
        if src is None:
            return None
        media.frame(src, out, 0.5)
        return out

    def learn_factor(self, category: str) -> float:
        """Lernen aus deinen Ergebnissen: Clip-Arten mit überdurchschnittlichen Views bekommen bis +30 %."""
        if not self.cfg.get("learn_from_views", True):
            return 1.0
        posted = [(json.loads(c["signals"] or "{}").get("category", "unklar"), c["views"] or 0)
                  for c in db.all_clips() if c["status"] == "POSTED" and (c["views"] or 0) > 0]
        mine = sorted(v for k, v in posted if k == category)
        if len(posted) < 6 or len(mine) < 3:
            return 1.0
        allv = sorted(v for _, v in posted)
        med_all, med_cat = allv[len(allv) // 2], mine[len(mine) // 2]
        return round(max(0.7, min(1.3, med_cat / med_all)), 2) if med_all else 1.0

    def learning(self) -> list[dict]:
        out: dict[str, list[int]] = {}
        for c in db.all_clips():
            if c["status"] == "POSTED" and (c["views"] or 0) > 0:
                out.setdefault(json.loads(c["signals"] or "{}").get("category", "unklar"), []).append(c["views"])
        return sorted(({"category": k, "posts": len(v), "median_views": sorted(v)[len(v) // 2],
                        "factor": self.learn_factor(k)} for k, v in out.items()),
                      key=lambda r: r["median_views"], reverse=True)

    def money(self) -> dict:
        """Verdienst-Übersicht: geschätzt aus eingetragenen Views × € pro 1000 Views."""
        rows: dict[str, dict] = {}
        total_views = total_eur = posted = 0
        for c in db.all_clips():
            r = rows.setdefault(c["streamer"], {"streamer": c["streamer"], "clips": 0, "posted": 0, "views": 0,
                                                "eur": 0.0, "score_sum": 0.0, "cpm": self.cpm(c["streamer"])})
            r["clips"] += 1
            r["score_sum"] += c["score"] or c["pre_score"] or 0
            if c["status"] == "POSTED":
                eur = (c["views"] or 0) / 1000 * r["cpm"]
                r["posted"] += 1
                r["views"] += c["views"] or 0
                r["eur"] += eur
                posted += 1
                total_views += c["views"] or 0
                total_eur += eur
        table = []
        for r in rows.values():
            r["avg_score"] = round(r.pop("score_sum") / r["clips"], 1) if r["clips"] else 0
            r["eur_per_clip"] = round(r["eur"] / r["posted"], 2) if r["posted"] else 0
            r["eur"] = round(r["eur"], 2)
            table.append(r)
        table.sort(key=lambda r: (r["eur"], r["avg_score"]), reverse=True)
        avg_views = total_views / posted if posted else 0
        views_list = sorted(c["views"] or 0 for c in db.all_clips() if c["status"] == "POSTED")
        median = views_list[len(views_list) // 2] if views_list else 0   # Ausreißer verzerren nicht
        avg_cpm = (total_eur / total_views * 1000) if total_views else self.cfg.get("default_cpm", 1.0)
        per_month = median / 1000 * avg_cpm * self.cfg.get("posts_per_day", 4) * 30 if posted >= 5 else None
        return {"views": total_views, "eur": round(total_eur, 2), "posted": posted,
                "avg_views": round(avg_views), "month_estimate": round(per_month, 2) if per_month is not None else None, "table": table}

    def action(self, cid: int, act: str) -> bool:
        clip = db.get(cid)
        if not clip:
            return False
        if act == "posted":
            db.update(cid, status="POSTED", posted_at=clip.get("posted_at") or time.time())
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
            "money": self.money(),
            "learning": self.learning(),
            "facecams": {s["login"]: bool(s.get("facecam")) for s in self.cfg["streamers"]},
            "posts_per_day": self.cfg.get("posts_per_day", 4),
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
        return self.add_candidate(login, trig, dedupe=False)


CAT_HOOKS = {
    "de": {
        "lustig": ["Ich kann nicht mehr 😂", "Warum ist das so lustig", "Der Chat liegt am Boden", "Bester Moment des Streams"],
        "fail": ["Das ging komplett schief", "Wie kann man nur", "Er hat es fast geschafft …", "Der schlimmste Fail heute"],
        "krass": ["Was für ein Play", "Das war einfach nur krank", "Niemand macht ihm das nach", "Wie hat er das gemacht?!"],
        "schock": ["Damit hat keiner gerechnet", "Warte aufs Ende", "Was ist hier passiert?!", "Der ganze Chat so: WTF"],
        "rage": ["Er rastet komplett aus", "Das war zu viel für ihn", "Bitte nicht noch mal …"],
        "wholesome": ["Das ist so wholesome", "Bester Moment heute ❤", "Chat ist gerührt"],
        "reaktion": ["Seine Reaktion 😭", "Hör genau hin", "Er konnte nicht anders"],
    },
    "en": {
        "lustig": ["I can't stop laughing", "Why is this so funny", "Chat is on the floor", "Funniest moment of the stream"],
        "fail": ["That went horribly wrong", "How do you even do that", "He almost had it …", "Biggest fail today"],
        "krass": ["What a play", "That was actually insane", "Nobody can do this", "How did he pull that off?!"],
        "schock": ["Nobody expected this", "Wait for the end", "What just happened?!", "Chat went WTF"],
        "rage": ["He completely lost it", "That broke him", "Not again …"],
        "wholesome": ["This is so wholesome", "Best moment today", "Chat is emotional"],
        "reaktion": ["His reaction 😭", "Listen closely", "He couldn't hold it in"],
    },
}

HOOKS = {
    "de": {
        "calls": ["Chat schreit nur noch CLIP", "Das musste geclippt werden", "Chat hat sofort reagiert"],
        "hype": ["Der Chat ist komplett eskaliert", "Damit hat keiner gerechnet", "Wie ist das passiert?!",
                 "Warte aufs Ende", "Er hat es wirklich getan"],
        "base": ["Dieser Moment …", "Achte genau hin", "Niemand war bereit dafür"],
    },
    "en": {
        "calls": ["Chat spammed CLIP IT", "This had to be clipped", "Chat lost it instantly"],
        "hype": ["Chat went absolutely crazy", "Nobody expected this", "Wait for the end",
                 "He actually did it", "How did this happen?!"],
        "base": ["This moment …", "Watch closely", "Nobody was ready"],
    },
}


def make_title(clip: dict, lang: str = "de") -> str:
    """Wechselnde Hooks je nach Signal und Sprache (gleicher Clip -> gleicher Hook)."""
    sig = json.loads(clip.get("signals") or "{}")
    cat = CAT_HOOKS.get(lang, CAT_HOOKS["en"]).get(sig.get("category", ""))
    if cat:
        return cat[(clip.get("id") or 0) % len(cat)]
    lib = HOOKS.get(lang, HOOKS["en"])
    kind = "calls" if sig.get("clip_calls", 0) >= 3 else "hype" if sig.get("hype", 0) >= 5 else "base"
    options = lib[kind]
    return options[(clip.get("id") or 0) % len(options)]


def text_block(clip: dict, st: dict) -> str:
    login = clip["streamer"]
    cat = (st.get("category") or "").strip()
    tags = ["#twitch", f"#{login}", "#clips", "#fyp"]
    if "grand theft auto" in cat.lower() or "gta" in cat.lower():
        tags[2:2] = ["#gta6", "#gta"]
    kind = json.loads(clip.get("signals") or "{}").get("category", "")
    extra = {"lustig": ["#funny", "#lustig"], "fail": ["#fail", "#fails"], "krass": ["#insane", "#gaming"],
             "schock": ["#wtf", "#crazy"], "rage": ["#rage"], "wholesome": ["#wholesome"], "reaktion": ["#reaction"]}
    tags[2:2] = extra.get(kind, [])
    return (f"🎬 {clip['title']}\n\n"
            f"Titel: {login}: {clip['title']}\n"
            f"Caption: {clip['title']} | Quelle: twitch.tv/{login}\n"
            f"Hashtags: {' '.join(tags)}\n"
            f"Quelle: https://twitch.tv/{login}\n"
            f"Note: {clip['score']}/10")
