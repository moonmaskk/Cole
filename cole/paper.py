"""Paper-Trading-Engine (virtuelles Depot) mit Gebühren, Slippage, Stops und Risikolimits.

Wird identisch im Backtest und im Live-Testmodus verwendet. Es wird nie echtes Geld bewegt.
"""
from __future__ import annotations

import csv
import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from .config import Config


@dataclass
class Position:
    symbol: str
    qty: float
    entry: float
    stop: float
    take_profit: float
    risk_per_unit: float
    atr: float
    opened_at: int
    highest: float
    fees: float = 0.0
    reason: str = ""
    last_bar: int = 0      # zuletzt geprüfte Kerze (Live-Modus)


@dataclass
class Trade:
    symbol: str
    qty: float
    entry: float
    exit: float
    opened_at: int
    closed_at: int
    pnl: float          # netto nach Gebühren
    pnl_pct: float
    r_multiple: float
    fees: float
    exit_reason: str
    entry_reason: str = ""


@dataclass
class Portfolio:
    cfg: Config
    cash: Optional[float] = None
    positions: Dict[str, Position] = field(default_factory=dict)
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[list] = field(default_factory=list)   # [t, equity]
    peak_equity: float = 0.0
    day: str = ""
    day_start_equity: float = 0.0
    cooldown_until: Dict[str, int] = field(default_factory=dict)
    fees_paid: float = 0.0

    def __post_init__(self):
        if self.cash is None:
            self.cash = self.cfg.start_capital
        self.peak_equity = self.peak_equity or self.cash
        self.day_start_equity = self.day_start_equity or self.cash

    # ------------------------------------------------------------ Bewertung
    def equity(self, prices: Dict[str, float]) -> float:
        return self.cash + sum(p.qty * prices.get(s, p.entry) for s, p in self.positions.items())

    def mark(self, t: int, prices: Dict[str, float]) -> float:
        eq = self.equity(prices)
        day = time.strftime("%Y-%m-%d", time.gmtime(t))
        if day != self.day:
            self.day, self.day_start_equity = day, eq
        self.peak_equity = max(self.peak_equity, eq)
        self.equity_curve.append([t, round(eq, 2)])
        if len(self.equity_curve) > 20000:
            self.equity_curve = self.equity_curve[-20000:]
        return eq

    # ------------------------------------------------------------ Risiko
    def can_open(self, symbol: str, bar_index: int, prices: Dict[str, float]) -> Optional[str]:
        """None = erlaubt, sonst Begründung, warum nicht."""
        cfg = self.cfg
        if os.path.exists("STOP"):
            return "Not-Aus aktiv (Datei STOP vorhanden)"
        if symbol in self.positions:
            return "Position bereits offen"
        if len(self.positions) >= cfg.max_open_positions:
            return f"Max. {cfg.max_open_positions} offene Positionen"
        eq = self.equity(prices)
        if self.day_start_equity and (eq / self.day_start_equity - 1) * 100 <= -cfg.daily_loss_limit_pct:
            return f"Tagesverlust-Limit ({cfg.daily_loss_limit_pct}%) erreicht"
        if self.peak_equity and (eq / self.peak_equity - 1) * 100 <= -cfg.max_drawdown_pct:
            return f"Max. Drawdown ({cfg.max_drawdown_pct}%) erreicht - Strategie prüfen!"
        if self.cooldown_until.get(symbol, -1) > bar_index:
            return "Cooldown nach Verlust"
        return None

    def fee(self, notional: float) -> float:
        return notional * self.cfg.fee_pct / 100 + self.cfg.fee_fixed

    def position_size(self, price: float, stop: float, prices: Dict[str, float], score: float = 0.0) -> float:
        cfg = self.cfg
        risk_unit = price - stop
        if risk_unit <= 0:
            return 0.0
        if cfg.trade_amount_min > 0:   # Fester Kleinbetrag (z.B. 5-7 EUR), je nach Signalstärke
            hi = max(cfg.trade_amount_min, cfg.trade_amount_max)
            strength = max(0.0, min(1.0, (score - cfg.buy_threshold) / max(1.0, 100 - cfg.buy_threshold)))
            amount = cfg.trade_amount_min + (hi - cfg.trade_amount_min) * strength
            amount = min(amount, self.cash - cfg.fee_fixed - amount * cfg.fee_pct / 100)
            return max(0.0, amount / price)
        eq = self.equity(prices)
        by_risk = eq * cfg.risk_per_trade_pct / 100 / risk_unit
        by_cap = eq * cfg.max_position_pct / 100 / price
        by_cash = self.cash / (price * (1 + cfg.fee_pct / 100))
        return max(0.0, min(by_risk, by_cap, by_cash))

    # ------------------------------------------------------------ Orders (simuliert)
    def open(self, symbol: str, price: float, stop_dist: float, atr: float, t: int,
             prices: Dict[str, float], reason: str = "", score: float = 0.0) -> Optional[Position]:
        cfg = self.cfg
        fill = price * (1 + cfg.slippage_pct / 100)
        stop = fill - stop_dist
        qty = self.position_size(fill, stop, prices, score)
        if qty * fill < cfg.min_order:  # Mindestordergröße der Börse
            return None
        fee = self.fee(qty * fill)
        self.cash -= qty * fill + fee
        self.fees_paid += fee
        pos = Position(symbol, qty, fill, stop, fill + cfg.reward_risk * stop_dist, stop_dist, atr, t, fill, fee, reason)
        self.positions[symbol] = pos
        return pos

    def close(self, symbol: str, price: float, t: int, reason: str, bar_index: int = 0,
              slippage: bool = True) -> Trade:
        cfg = self.cfg
        p = self.positions.pop(symbol)
        fill = price * (1 - cfg.slippage_pct / 100) if slippage else price
        fee = self.fee(p.qty * fill)
        self.cash += p.qty * fill - fee
        self.fees_paid += fee
        pnl = p.qty * (fill - p.entry) - p.fees - fee
        tr = Trade(symbol, p.qty, p.entry, fill, p.opened_at, t, pnl, pnl / (p.qty * p.entry) * 100,
                   pnl / (p.qty * p.risk_per_unit) if p.risk_per_unit else 0.0, p.fees + fee, reason, p.reason)
        self.trades.append(tr)
        # nach Verlust: Cooldown; nach jedem Ausstieg: kein Wiedereinstieg in derselben Kerze
        wait = cfg.cooldown_bars if pnl < 0 else 1
        self.cooldown_until[symbol] = max(self.cooldown_until.get(symbol, 0), bar_index + wait)
        return tr

    def check_exits(self, symbol: str, o: float, h: float, l: float, t: int, bar_index: int = 0) -> Optional[Trade]:
        """Prüft Stop/Take-Profit innerhalb einer Kerze. Konservativ: Stop wird vor TP geprüft."""
        p = self.positions.get(symbol)
        if not p:
            return None
        if o <= p.stop:   # Kurslücke unter den Stop -> Ausführung zum Eröffnungskurs
            return self.close(symbol, o, t, "Stop (Gap)", bar_index)
        if l <= p.stop:
            label = "Trailing-Stop" if p.stop >= p.entry else "Stop-Loss"
            return self.close(symbol, p.stop, t, label, bar_index)
        if h >= p.take_profit:
            return self.close(symbol, max(p.take_profit, o), t, "Take-Profit", bar_index)
        return None

    def update_trailing(self, symbol: str, high: float) -> None:
        p = self.positions.get(symbol)
        if not p or not self.cfg.trailing:
            return
        p.highest = max(p.highest, high)
        if p.highest >= p.entry + p.risk_per_unit:          # +1R erreicht -> Einstand absichern
            p.stop = max(p.stop, p.entry * (1 + 2 * self.cfg.fee_pct / 100))
        if p.highest >= p.entry + 1.5 * p.risk_per_unit:    # danach mit ATR-Abstand nachziehen
            p.stop = max(p.stop, p.highest - self.cfg.atr_stop_mult * p.atr)

    # ------------------------------------------------------------ Persistenz
    def to_dict(self) -> dict:
        return {
            "cash": self.cash, "positions": {k: asdict(v) for k, v in self.positions.items()},
            "trades": [asdict(t) for t in self.trades], "equity_curve": self.equity_curve[-5000:],
            "peak_equity": self.peak_equity, "day": self.day, "day_start_equity": self.day_start_equity,
            "cooldown_until": self.cooldown_until, "fees_paid": self.fees_paid,
        }

    @classmethod
    def from_dict(cls, cfg: Config, d: dict) -> "Portfolio":
        pf = cls(cfg, cash=d["cash"], peak_equity=d.get("peak_equity", 0), day=d.get("day", ""),
                 day_start_equity=d.get("day_start_equity", 0), fees_paid=d.get("fees_paid", 0.0))
        pf.positions = {k: Position(**v) for k, v in d.get("positions", {}).items()}
        pf.trades = [Trade(**t) for t in d.get("trades", [])]
        pf.equity_curve = d.get("equity_curve", [])
        pf.cooldown_until = d.get("cooldown_until", {})
        return pf

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=1)
        os.replace(tmp, path)

    @classmethod
    def load(cls, cfg: Config, path: str) -> "Portfolio":
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                return cls.from_dict(cfg, json.load(fh))
        return cls(cfg)


def append_journal(path: str, trade: Trade) -> None:
    """Trade-Journal als CSV (für Auswertung & Steuer-Dokumentation)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    new = not os.path.exists(path)
    row = asdict(trade)
    row["opened_at"] = time.strftime("%Y-%m-%d %H:%M", time.gmtime(trade.opened_at))
    row["closed_at"] = time.strftime("%Y-%m-%d %H:%M", time.gmtime(trade.closed_at))
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(row), delimiter=";")
        if new:
            w.writeheader()
        w.writerow(row)


def stats(trades: List[Trade]) -> dict:
    if not trades:
        return {"n": 0, "win_rate": 0.0, "profit_factor": 0.0, "avg_r": 0.0, "net": 0.0, "best": 0.0, "worst": 0.0}
    wins = [t.pnl for t in trades if t.pnl > 0]
    losses = [-t.pnl for t in trades if t.pnl <= 0]
    return {
        "n": len(trades),
        "win_rate": 100 * len(wins) / len(trades),
        "profit_factor": (sum(wins) / sum(losses)) if losses and sum(losses) > 0 else float("inf") if wins else 0.0,
        "avg_r": sum(t.r_multiple for t in trades) / len(trades),
        "net": sum(t.pnl for t in trades),
        "best": max(t.pnl for t in trades),
        "worst": min(t.pnl for t in trades),
    }
