"""Pro Streamer: prüfen, ob live; wenn ja, Stream per streamlink holen und in den Ringpuffer schreiben."""
from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path

from . import config, media


class Recorder(threading.Thread):
    def __init__(self, login: str, cfg_get, state: dict, log):
        super().__init__(daemon=True, name=f"rec-{login}")
        self.login = login
        self.cfg_get = cfg_get
        self.state = state          # dict für die UI
        self.log = log
        self.stop = threading.Event()
        self.dir: Path = config.BUFFER / login
        self.dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> None:
        while not self.stop.is_set():
            cfg = self.cfg_get()
            try:
                stream, category = self._find_stream(cfg)
            except Exception as e:  # Netzwerk, Plugin, gesperrt ...
                msg = str(e)
                if "Unable to open URL" in msg or "resolve" in msg.lower():
                    msg = "Twitch nicht erreichbar (Internet?)"
                self.state.update(live=False, status=f"Fehler: {msg[:80]}")
                self.stop.wait(cfg["live_check_seconds"])
                continue
            self.state["category"] = category or ""
            if stream is None:
                self.state.update(live=False, status="offline")
                self.stop.wait(cfg["live_check_seconds"])
                continue
            filt = cfg["category_filter"].strip().lower()
            if filt and filt not in (category or "").lower():
                self.state.update(live=True, recording=False, status=f"live, andere Kategorie")
                self.stop.wait(cfg["live_check_seconds"])
                continue
            self._record(stream, cfg)

    def _find_stream(self, cfg):
        from streamlink import Streamlink
        session = Streamlink()
        url = f"https://www.twitch.tv/{self.login}"
        _, plugin_cls, resolved = session.resolve_url(url)
        plugin = plugin_cls(session, resolved)
        streams = plugin.streams()
        if not streams:
            return None, None
        try:
            category = plugin.get_category()
        except Exception:
            category = None
        for q in cfg["quality"].split(","):
            if q.strip() in streams:
                return streams[q.strip()], category
        return streams.get("best"), category

    def _record(self, stream, cfg) -> None:
        self.state.update(live=True, recording=True, status="nimmt auf")
        self.log(f"{self.login}: Aufnahme gestartet")
        proc = subprocess.Popen(media.segment_cmd(self.dir, cfg["segment_seconds"]),
                                stdin=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                creationflags=media.NO_WINDOW)
        last_prune = 0.0
        try:
            fd = stream.open()
            try:
                while not self.stop.is_set():
                    data = fd.read(64 * 1024)
                    if not data:
                        break
                    proc.stdin.write(data)
                    if time.time() - last_prune > 15:
                        media.prune(self.dir, cfg["buffer_minutes"] * 60)
                        last_prune = time.time()
            finally:
                fd.close()
        except Exception as e:
            self.log(f"{self.login}: Aufnahme unterbrochen ({str(e)[:80]})")
        finally:
            try:
                proc.stdin.close()
                proc.wait(timeout=10)
            except Exception:
                proc.kill()
            self.state.update(recording=False, status="Stream beendet")
            self.log(f"{self.login}: Aufnahme beendet")
