"""Lokaler Webserver für das Dashboard (stdlib). Videos mit Range-Support, damit Safari/iPad abspielen."""
from __future__ import annotations

import json
import re
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import config, db
from .pipeline import Pipeline, text_block

UI = Path(__file__).with_name("ui.html")
SECRET_KEYS = ("telegram_token",)


def lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def make_handler(p: Pipeline):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _json(self, obj, code=200):
            body = json.dumps(obj, ensure_ascii=False, default=str).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}") if n else {}

        def _file(self, path: Path, ctype: str):
            if not path.exists():
                return self._json({"error": "nicht gefunden"}, 404)
            size = path.stat().st_size
            rng = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
            start, end = 0, size - 1
            if rng:
                if rng.group(1):
                    start = int(rng.group(1))
                    if rng.group(2):
                        end = min(int(rng.group(2)), size - 1)
                elif rng.group(2):
                    start = max(0, size - int(rng.group(2)))
                self.send_response(206)
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            else:
                self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(end - start + 1))
            self.end_headers()
            with path.open("rb") as f:
                f.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = f.read(min(1 << 16, left))
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                    except (BrokenPipeError, ConnectionResetError):
                        return
                    left -= len(chunk)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html"):
                body = UI.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif path == "/api/state":
                snap = p.snapshot()
                for c in snap["clips"]:
                    c["text"] = text_block(c, p.streamers.get(c["streamer"], {}))
                    c.pop("chat", None)
                self._json(snap)
            elif path == "/api/settings":
                cfg = dict(p.cfg)
                for k in SECRET_KEYS:
                    cfg[k] = "••••••" if cfg.get(k) else ""
                cfg["_lan_url"] = f"http://{lan_ip()}:{cfg['port']}"
                self._json(cfg)
            elif m := re.fullmatch(r"/media/(\d+)\.mp4", path):
                self._file(config.CLIPS / f"{int(m.group(1)):06d}" / "clip.mp4", "video/mp4")
            elif m := re.fullmatch(r"/api/frame/([a-z0-9_]+)\.jpg", path):
                try:
                    f = p.preview_frame(m.group(1))
                except Exception:
                    f = None
                if f:
                    self._file(f, "image/jpeg")
                else:
                    self._json({"error": "noch kein Bild – Streamer muss live sein"}, 404)
            elif m := re.fullmatch(r"/thumb/(\d+)\.jpg", path):
                self._file(config.CLIPS / f"{int(m.group(1)):06d}" / "thumb.jpg", "image/jpeg")
            else:
                self._json({"error": "nicht gefunden"}, 404)

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            try:
                data = self._body()
            except ValueError:
                return self._json({"error": "ungültiges JSON"}, 400)
            if path == "/api/settings":
                for k in SECRET_KEYS:
                    if data.get(k) == "••••••":
                        data.pop(k)
                p.set_cfg(data)
                self._json({"ok": True})
            elif m := re.fullmatch(r"/api/clip/(\d+)/(posted|reject|rerender)", path):
                self._json({"ok": p.action(int(m.group(1)), m.group(2))})
            elif m := re.fullmatch(r"/api/clip/(\d+)/stats", path):
                self._json({"ok": p.set_stats(int(m.group(1)), int(data.get("views") or 0),
                                              str(data.get("platform") or ""))})
            elif m := re.fullmatch(r"/api/clip/(\d+)/trim", path):
                self._json({"ok": p.trim(int(m.group(1)), float(data.get("start") or 0),
                                         float(data.get("end") or 0))})
            elif m := re.fullmatch(r"/api/facecam/([a-z0-9_]+)", path):
                self._json({"ok": p.set_facecam(m.group(1), data.get("box"))})
            elif path == "/api/demo":
                try:
                    cid = p.demo()
                    self._json({"ok": cid is not None, "id": cid})
                except Exception as e:
                    self._json({"ok": False, "error": str(e)[:300]}, 500)
            else:
                self._json({"error": "nicht gefunden"}, 404)

    return H


def serve(p: Pipeline, open_browser: bool = True) -> None:
    cfg = p.cfg
    host = "0.0.0.0" if cfg.get("lan_access") else "127.0.0.1"
    port = int(cfg.get("port", 8765))
    httpd = ThreadingHTTPServer((host, port), make_handler(p))
    url = f"http://127.0.0.1:{port}"
    print(f"\n  ClipFabrik läuft:  {url}")
    if cfg.get("lan_access"):
        print(f"  iPad/Handy im WLAN: http://{lan_ip()}:{port}")
    print("  Beenden: dieses Fenster schließen oder Strg+C\n")
    if open_browser:
        import webbrowser
        webbrowser.open(url)
    httpd.serve_forever()
