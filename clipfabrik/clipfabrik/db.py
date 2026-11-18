"""SQLite mit einem Status pro Clip. Jeder Worker holt sich seine Arbeit hier ab."""
from __future__ import annotations

import json
import sqlite3
import threading
import time

from . import config

STATES = ("NEW", "CUT", "JUDGED", "RENDERED", "DELIVERED", "POSTED", "REJECTED", "FAILED")

_local = threading.local()


def conn() -> sqlite3.Connection:
    c = getattr(_local, "c", None)
    if c is None:
        config.ensure_dirs()
        c = sqlite3.connect(config.DATA / "clips.db", timeout=30)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        _local.c = c
    return c


def init() -> None:
    conn().executescript(
        """
        CREATE TABLE IF NOT EXISTS clips(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          streamer TEXT NOT NULL,
          created REAL NOT NULL,
          peak REAL NOT NULL,
          start REAL NOT NULL,
          end REAL NOT NULL,
          pre_score REAL NOT NULL DEFAULT 0,
          score REAL,
          status TEXT NOT NULL DEFAULT 'NEW',
          title TEXT DEFAULT '',
          signals TEXT DEFAULT '{}',
          chat TEXT DEFAULT '[]',
          raw_path TEXT DEFAULT '',
          out_path TEXT DEFAULT '',
          error TEXT DEFAULT '',
          tg_message INTEGER,
          updated REAL
        );
        CREATE INDEX IF NOT EXISTS ix_status ON clips(status);
        """
    )
    conn().commit()


def add_clip(streamer: str, peak: float, start: float, end: float, pre_score: float,
             signals: dict, chat: list[str]) -> int:
    cur = conn().execute(
        "INSERT INTO clips(streamer,created,peak,start,end,pre_score,signals,chat,updated)"
        " VALUES(?,?,?,?,?,?,?,?,?)",
        (streamer, time.time(), peak, start, end, pre_score,
         json.dumps(signals), json.dumps(chat[-40:], ensure_ascii=False), time.time()),
    )
    conn().commit()
    return cur.lastrowid


def update(clip_id: int, **fields) -> None:
    fields["updated"] = time.time()
    keys = ", ".join(f"{k}=?" for k in fields)
    conn().execute(f"UPDATE clips SET {keys} WHERE id=?", (*fields.values(), clip_id))
    conn().commit()


def get(clip_id: int) -> dict | None:
    r = conn().execute("SELECT * FROM clips WHERE id=?", (clip_id,)).fetchone()
    return dict(r) if r else None


def next_with(status: str, ready_before: float | None = None) -> dict | None:
    """Bester Kandidat zuerst: höchster Score, dann neuester."""
    q = "SELECT * FROM clips WHERE status=?"
    args: list = [status]
    if ready_before is not None:
        q += " AND end<?"
        args.append(ready_before)
    q += " ORDER BY COALESCE(score, pre_score) DESC, created DESC LIMIT 1"
    r = conn().execute(q, args).fetchone()
    return dict(r) if r else None


def recent(limit: int = 60) -> list[dict]:
    rows = conn().execute("SELECT * FROM clips ORDER BY created DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def counts() -> dict:
    rows = conn().execute("SELECT status, COUNT(*) n FROM clips GROUP BY status").fetchall()
    return {r["status"]: r["n"] for r in rows}


def overlapping(streamer: str, start: float, end: float) -> dict | None:
    r = conn().execute(
        "SELECT * FROM clips WHERE streamer=? AND status NOT IN ('REJECTED','FAILED')"
        " AND start<? AND end>? ORDER BY pre_score DESC LIMIT 1",
        (streamer, end, start),
    ).fetchone()
    return dict(r) if r else None


def recover() -> None:
    """Nach Absturz: halbfertige Arbeit nicht verlieren (Status bleibt, Worker greifen erneut zu)."""
    conn().execute("UPDATE clips SET status='FAILED', error='Puffer verloren' "
                   "WHERE status='NEW' AND end < ?", (time.time() - 3600,))
    conn().commit()
