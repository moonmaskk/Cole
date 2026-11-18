"""Twitch-Chat anonym mitlesen (IRC über TLS, kein Login und kein API-Key nötig)."""
from __future__ import annotations

import random
import socket
import ssl
import time
from typing import Callable

HOST, PORT = "irc.chat.twitch.tv", 6697


def parse(line: str) -> tuple[str, str, str] | None:
    """'@tags :user!user@user.tmi.twitch.tv PRIVMSG #chan :text' -> (chan, user, text)"""
    if " PRIVMSG #" not in line:
        return None
    if line.startswith("@"):
        _, line = line.split(" ", 1)
    try:
        prefix, rest = line[1:].split(" PRIVMSG #", 1)
        chan, text = rest.split(" :", 1)
    except ValueError:
        return None
    return chan.strip().lower(), prefix.split("!", 1)[0].lower(), text.strip()


class ChatClient:
    def __init__(self, on_message: Callable[[str, float, str, str], None], log: Callable[[str], None]):
        self.on_message = on_message
        self.log = log
        self.wanted: set[str] = set()
        self.joined: set[str] = set()
        self.connected = False
        self.stop = False

    def set_channels(self, logins) -> None:
        self.wanted = {l.lower() for l in logins}

    def run(self) -> None:
        backoff = 2
        while not self.stop:
            try:
                self._session()
                backoff = 2
            except (OSError, ssl.SSLError) as e:
                self.connected = False
                self.log(f"Chat getrennt ({e.__class__.__name__}), neuer Versuch in {backoff}s")
                time.sleep(backoff)
                backoff = min(60, backoff * 2)

    def _session(self) -> None:
        raw = socket.create_connection((HOST, PORT), timeout=10)
        sock = ssl.create_default_context().wrap_socket(raw, server_hostname=HOST)
        sock.settimeout(1.0)
        nick = f"justinfan{random.randint(10000, 99999)}"
        sock.sendall(f"PASS SCHMOOPIIE\r\nNICK {nick}\r\n".encode())
        self.joined = set()
        self.connected = True
        self.log("Chat verbunden")
        buf = b""
        last_rx = time.time()
        while not self.stop:
            self._sync(sock)
            try:
                data = sock.recv(65536)
                if not data:
                    raise OSError("Verbindung geschlossen")
                last_rx = time.time()
                buf += data
            except socket.timeout:
                if time.time() - last_rx > 360:
                    raise OSError("Zeitüberschreitung")
                continue
            *lines, buf = buf.split(b"\r\n")
            now = time.time()
            for ln in lines:
                s = ln.decode("utf-8", "replace")
                if s.startswith("PING"):
                    sock.sendall(b"PONG :tmi.twitch.tv\r\n")
                    continue
                msg = parse(s)
                if msg:
                    self.on_message(msg[0], now, msg[1], msg[2])

    def _sync(self, sock) -> None:
        for ch in sorted(self.wanted - self.joined)[:15]:   # Twitch: max 20 JOINs / 10 s
            sock.sendall(f"JOIN #{ch}\r\n".encode())
            self.joined.add(ch)
        for ch in self.joined - self.wanted:
            sock.sendall(f"PART #{ch}\r\n".encode())
        self.joined &= self.wanted
