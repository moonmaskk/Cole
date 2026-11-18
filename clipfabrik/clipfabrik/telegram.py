"""Telegram-Bot: Clip + fertigen Textblock schicken, Buttons auswerten. Nur stdlib."""
from __future__ import annotations

import json
import uuid
import urllib.request
from pathlib import Path

API = "https://api.telegram.org/bot{token}/{method}"


def call(token: str, method: str, data: dict | None = None, timeout: int = 40) -> dict:
    req = urllib.request.Request(API.format(token=token, method=method),
                                 data=json.dumps(data or {}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def send_video(token: str, chat_id: str, path: Path, caption: str, clip_id: int) -> int:
    boundary = uuid.uuid4().hex
    markup = {"inline_keyboard": [[
        {"text": "✅ gepostet", "callback_data": f"posted:{clip_id}"},
        {"text": "🗑 verwerfen", "callback_data": f"reject:{clip_id}"},
        {"text": "🔁 neu rendern", "callback_data": f"rerender:{clip_id}"},
    ]]}
    fields = {"chat_id": chat_id, "caption": caption[:1024], "supports_streaming": "true",
              "reply_markup": json.dumps(markup)}
    body = b""
    for k, v in fields.items():
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"video\"; filename=\"{path.name}\"\r\n"
             f"Content-Type: video/mp4\r\n\r\n").encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(API.format(token=token, method="sendVideo"), data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=180) as r:
        res = json.loads(r.read())
    if not res.get("ok"):
        raise RuntimeError(res.get("description", "Telegram-Fehler"))
    return res["result"]["message_id"]


def poll(token: str, offset: int) -> tuple[int, list[tuple[str, int, str]]]:
    """Gibt (neuer offset, [(aktion, clip_id, callback_id)]) zurück."""
    res = call(token, "getUpdates", {"offset": offset, "timeout": 25, "allowed_updates": ["callback_query"]})
    actions = []
    for u in res.get("result", []):
        offset = max(offset, u["update_id"] + 1)
        cq = u.get("callback_query")
        if cq and ":" in cq.get("data", ""):
            act, cid = cq["data"].split(":", 1)
            if cid.isdigit():
                actions.append((act, int(cid), cq["id"]))
    return offset, actions
