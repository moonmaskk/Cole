"""Live-Testmodus: holt laufend Daten, analysiert, gibt Vorschläge und handelt mit virtuellem Geld."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .config import Config
from .data import DataError, http_json, market_context
from .paper import Portfolio, append_journal
from .strategy import Signal, analyze, compute, trend_score


@dataclass
class CycleReport:
    t: int
    signals: List[Signal] = field(default_factory=list)
    prices: Dict[str, float] = field(default_factory=dict)
    events: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    equity: float = 0.0


class ContextCache:
    """Markt-Kontext nur alle paar Minuten neu laden (Rate-Limits schonen)."""

    def __init__(self, ttl: int = 600):
        self.ttl, self.data, self.at = ttl, {}, 0.0
        self.notes: Dict[str, str] = {}   # letzte Hinweis-Meldung je Coin (gegen Wiederholungen)

    def get(self, cfg: Config) -> dict:
        if not cfg.use_context:
            return {}
        if time.time() - self.at > self.ttl:
            self.data, self.at = market_context(cfg.source, cfg.watchlist), time.time()
        return self.data


def notify(cfg: Config, text: str) -> None:
    if not (cfg.telegram_bot_token and cfg.telegram_chat_id):
        return
    try:
        http_json(f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage",
                  {"chat_id": cfg.telegram_chat_id, "text": text}, retries=0)
    except Exception:
        pass


def symbol_context(base: str, ctx: dict, btc_trend: Optional[float]) -> dict:
    out: dict = {"is_btc": base.upper() == "BTC"}
    fg = ctx.get("fear_greed")
    if fg:
        out["fear_greed"] = fg["value"]
    f = ctx.get("funding", {}).get(base.upper())
    if f:
        out["funding"] = f["funding"]
    if btc_trend is not None:
        out["btc_trend"] = btc_trend
    return out


def run_cycle(cfg: Config, source, pf: Portfolio, ctx_cache: ContextCache, trade: bool = True) -> CycleReport:
    quote = cfg.resolved_quote()
    bar_sec = cfg.interval_min * 60
    ctx = ctx_cache.get(cfg)
    rep = CycleReport(t=0, context=ctx)

    data = {}
    for base in dict.fromkeys(["BTC"] + list(cfg.watchlist)):
        try:
            data[base] = source.candles(base, quote, cfg.interval_min, cfg.history)
        except DataError as exc:
            if base in cfg.watchlist:
                rep.errors.append(f"{base}: {exc}")
    btc_trend = None
    if "BTC" in data and len(data["BTC"]) > 220:
        closed = data["BTC"][:-1]
        btc_trend = trend_score(compute(closed), len(closed) - 1)

    for base in cfg.watchlist:
        candles = data.get(base)
        if not candles:
            continue
        price = candles[-1].c
        rep.prices[base] = price
        rep.t = max(rep.t, candles[-1].t)
        try:
            sig = analyze(base, candles, cfg, symbol_context(base, ctx, btc_trend) if cfg.use_context else None)
        except ValueError as exc:
            rep.errors.append(str(exc))
            continue
        rep.signals.append(sig)
        if trade:
            _manage(cfg, pf, base, candles, sig, rep, bar_sec, ctx_cache.notes)

    if rep.prices:
        rep.equity = pf.mark(rep.t, rep.prices)
    return rep


def _manage(cfg: Config, pf: Portfolio, base: str, candles, sig: Signal, rep: CycleReport, bar_sec: int,
            notes: Dict[str, str]) -> None:
    now_bar = candles[-1].t // bar_sec
    price = candles[-1].c

    def closed(tr):
        if tr:
            msg = (f"VERKAUF {base} @ {tr.exit:.6g} ({tr.exit_reason}) -> "
                   f"{tr.pnl:+.2f} {cfg.resolved_quote()} ({tr.pnl_pct:+.2f}%, {tr.r_multiple:+.2f}R)")
            rep.events.append(msg)
            append_journal(os.path.join(cfg.data_dir, "journal.csv"), tr)
            notify(cfg, "[Cole Paper] " + msg)
        return tr

    pos = pf.positions.get(base)
    if pos:
        last_done = max(pos.last_bar, pos.opened_at)
        for c in candles[:-1]:                 # abgeschlossene Kerzen seit dem Einstieg
            if c.t <= last_done:
                continue
            if closed(pf.check_exits(base, c.o, c.h, c.l, c.t, c.t // bar_sec)):
                return
            pf.update_trailing(base, c.h)
            last_done = c.t
        pos.last_bar = last_done
        if price <= pos.stop:
            closed(pf.close(base, price, candles[-1].t, "Stop-Loss (live)", now_bar))
            return
        if price >= pos.take_profit:
            closed(pf.close(base, price, candles[-1].t, "Take-Profit (live)", now_bar))
            return
        if sig.action == "SELL":
            closed(pf.close(base, price, candles[-1].t, f"Signal: Verkaufen (Score {sig.score})", now_bar))
        return

    def note(msg: str) -> None:
        if notes.get(base) != msg:
            notes[base] = msg
            rep.events.append(msg)

    if sig.action != "BUY":
        notes.pop(base, None)
        return
    if sig.blockers:
        note(f"{base}: Kaufsignal ignoriert - {', '.join(sig.blockers)}")
        return
    why_not = pf.can_open(base, now_bar, rep.prices)
    if why_not:
        note(f"{base}: Kaufsignal ignoriert - {why_not}")
        return
    notes.pop(base, None)
    p = pf.open(base, price, cfg.atr_stop_mult * sig.atr, sig.atr, candles[-1].t, rep.prices,
                "; ".join(sig.reasons[:3]), sig.score)
    if p:
        msg = (f"KAUF {base} {p.qty:.6g} @ {p.entry:.6g} | Stop {p.stop:.6g} | Ziel {p.take_profit:.6g} "
               f"| Score {sig.score}")
        rep.events.append(msg)
        notify(cfg, "[Cole Paper] " + msg)
