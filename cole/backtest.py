"""Backtester + Walk-Forward-Optimierung.

Regeln gegen geschönte Ergebnisse:
- Signal auf Schlusskurs von Kerze i, Ausführung zum Eröffnungskurs von Kerze i+1 (kein Look-ahead)
- Gebühren + Slippage auf jeder Seite
- Stop wird innerhalb einer Kerze VOR dem Take-Profit geprüft (pessimistisch)
- Markt-Kontext (Fear & Greed, Funding) gibt es historisch nicht -> im Backtest neutral
"""
from __future__ import annotations

import copy
import itertools
import math
from typing import Dict, List, Optional

from .config import Config
from .data import Candle, bars_per_year
from .paper import Portfolio, stats
from .strategy import WARMUP, compute, entry_blockers, make_signal, trend_score


def run_backtest(candles: List[Candle], cfg: Config, symbol: str = "X",
                 btc_candles: Optional[List[Candle]] = None) -> dict:
    if len(candles) < WARMUP + 50:
        raise ValueError(f"Mindestens {WARMUP + 50} Kerzen nötig, vorhanden: {len(candles)}")
    d = compute(candles)
    btc = compute(btc_candles) if btc_candles and len(btc_candles) == len(candles) else None
    pf = Portfolio(cfg)
    pending_entry = None
    pending_exit = False
    exposure_bars = 0

    for i in range(WARMUP, len(candles)):
        bar = candles[i]
        prices = {symbol: bar.o}
        # 1) Ausstehende Orders zum Eröffnungskurs ausführen
        if pending_exit and symbol in pf.positions:
            pf.close(symbol, bar.o, bar.t, "Signal: Verkaufen", i)
        pending_exit = False
        if pending_entry and symbol not in pf.positions:
            pf.open(symbol, bar.o, pending_entry["stop_dist"], pending_entry["atr"], bar.t, prices,
                    pending_entry["reason"], pending_entry["score"])
        pending_entry = None
        # 2) Stop / Take-Profit innerhalb der Kerze
        if symbol in pf.positions:
            exposure_bars += 1
            pf.check_exits(symbol, bar.o, bar.h, bar.l, bar.t, i)
        # 3) Am Schlusskurs: Trailing + neues Signal
        pf.update_trailing(symbol, bar.h)
        prices = {symbol: bar.c}
        pf.mark(bar.t, prices)
        if i == len(candles) - 1:
            break
        ctx = {"btc_trend": trend_score(btc, i)} if btc is not None else None
        sig = make_signal(symbol, d, i, cfg, ctx, bar.t)
        if symbol in pf.positions:
            if sig.action == "SELL":
                pending_exit = True
        elif sig.action == "BUY" and not entry_blockers(d, i, cfg) and pf.can_open(symbol, i, prices) is None:
            pending_entry = {"stop_dist": cfg.atr_stop_mult * sig.atr, "atr": sig.atr,
                             "reason": "; ".join(sig.reasons[:3]), "score": sig.score}

    if symbol in pf.positions:
        pf.close(symbol, candles[-1].c, candles[-1].t, "Backtest-Ende", len(candles))
        pf.mark(candles[-1].t, {symbol: candles[-1].c})

    return summarize(pf, candles[WARMUP:], cfg, exposure_bars)


def summarize(pf: Portfolio, candles: List[Candle], cfg: Config, exposure_bars: int) -> dict:
    eq = [e for _, e in pf.equity_curve]
    peak, max_dd = eq[0], 0.0
    for e in eq:
        peak = max(peak, e)
        max_dd = min(max_dd, e / peak - 1)
    rets = [eq[i] / eq[i - 1] - 1 for i in range(1, len(eq)) if eq[i - 1]]
    mean = sum(rets) / len(rets) if rets else 0.0
    sd = math.sqrt(sum((r - mean) ** 2 for r in rets) / len(rets)) if rets else 0.0
    sharpe = (mean / sd) * math.sqrt(bars_per_year(cfg.interval_min)) if sd else 0.0
    s = stats(pf.trades)
    return {
        "start_equity": cfg.start_capital,
        "end_equity": eq[-1],
        "return_pct": (eq[-1] / cfg.start_capital - 1) * 100,
        "buy_hold_pct": (candles[-1].c / candles[0].o - 1) * 100,
        "max_drawdown_pct": max_dd * 100,
        "sharpe": sharpe,
        "exposure_pct": 100 * exposure_bars / max(1, len(candles)),
        "fees_paid": pf.fees_paid,
        "trades": pf.trades,
        "equity_curve": pf.equity_curve,
        **{f"t_{k}": v for k, v in s.items()},
    }


GRID = {
    "buy_threshold": [25.0, 35.0, 45.0],
    "atr_stop_mult": [1.5, 2.0, 3.0],
    "reward_risk": [1.5, 2.0, 3.0],
}


def walk_forward(candles: List[Candle], cfg: Config, symbol: str, train_frac: float = 0.7,
                 min_trades: int = 5) -> List[dict]:
    """Optimiert auf den ersten 70 % der Daten und testet auf den restlichen 30 % (nie gesehen)."""
    split = int(len(candles) * train_frac)
    train = candles[:split]
    # Test-Fenster bekommt die Aufwärmphase aus dem Trainingsteil, bewertet wird aber nur Neues
    test = candles[max(0, split - WARMUP):]
    results = []
    keys = list(GRID)
    for combo in itertools.product(*(GRID[k] for k in keys)):
        c = copy.deepcopy(cfg)
        for k, v in zip(keys, combo):
            setattr(c, k, v)
        tr = run_backtest(train, c, symbol)
        if tr["t_n"] < min_trades:
            continue
        te = run_backtest(test, c, symbol)
        results.append({"params": dict(zip(keys, combo)), "train": tr, "test": te})
    results.sort(key=lambda r: (r["train"]["return_pct"] - 0.5 * abs(r["train"]["max_drawdown_pct"])), reverse=True)
    return results


def fmt_result(r: dict) -> Dict[str, str]:
    pf = r["t_profit_factor"]
    return {
        "Rendite": f"{r['return_pct']:+.2f}%",
        "Buy&Hold": f"{r['buy_hold_pct']:+.2f}%",
        "Max. Drawdown": f"{r['max_drawdown_pct']:.2f}%",
        "Sharpe": f"{r['sharpe']:.2f}",
        "Trades": str(r["t_n"]),
        "Trefferquote": f"{r['t_win_rate']:.1f}%",
        "Profit-Faktor": "∞" if pf == float("inf") else f"{pf:.2f}",
        "Ø R pro Trade": f"{r['t_avg_r']:+.2f}",
        "Gebühren": f"{r['fees_paid']:.2f}",
        "Zeit im Markt": f"{r['exposure_pct']:.1f}%",
    }
