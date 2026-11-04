"""Multi-Faktor-Strategie: bewertet jeden Coin mit einem Score von -100 (stark bärisch) bis +100 (stark bullisch).

Faktoren: Trend (EMA), Momentum (MACD), RSI (regimeabhängig), Bollinger/Donchian,
Volumen-Bestätigung, übergeordneter Trend (EMA200-Steigung) und Markt-Kontext
(Fear & Greed, Funding-Rate, BTC-Filter für Altcoins).
Das Marktregime (Trend vs. Seitwärts) wird per ADX bestimmt und ändert, wie RSI und Bänder gelesen werden.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import indicators as ind
from .config import Config
from .data import Candle

WARMUP = 210  # EMA200 + Puffer


@dataclass
class Signal:
    symbol: str
    action: str                 # BUY | SELL | HOLD
    score: float
    price: float
    stop: float
    take_profit: float
    atr: float
    regime: str
    reasons: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    values: Dict[str, float] = field(default_factory=dict)
    time: int = 0

    @property
    def confidence(self) -> str:
        a = abs(self.score)
        return "hoch" if a >= 60 else "mittel" if a >= 35 else "niedrig"


def compute(candles: List[Candle]) -> Dict[str, list]:
    """Berechnet alle Indikatoren einmal für die ganze Serie (für Live und Backtest identisch)."""
    o = [c.o for c in candles]
    h = [c.h for c in candles]
    l = [c.l for c in candles]
    c = [c.c for c in candles]
    v = [x.v for x in candles]
    macd_line, macd_sig, macd_hist = ind.macd(c)
    bb_mid, bb_up, bb_lo = ind.bollinger(c)
    return {
        "open": o, "high": h, "low": l, "close": c, "volume": v,
        "ema20": ind.ema(c, 20), "ema50": ind.ema(c, 50), "ema200": ind.ema(c, 200),
        "rsi": ind.rsi(c), "macd": macd_line, "macd_signal": macd_sig, "macd_hist": macd_hist,
        "bb_mid": bb_mid, "bb_up": bb_up, "bb_lo": bb_lo,
        "atr": ind.atr(h, l, c), "adx": ind.adx(h, l, c),
        "don_hi": ind.rolling_max(h, 20), "don_lo": ind.rolling_min(l, 20),
        "vol_z": ind.zscore(v, 20), "vwap": ind.rolling_vwap(h, l, c, v, 96),
    }


def _sign(x: float, dead: float = 0.0) -> float:
    return 1.0 if x > dead else -1.0 if x < -dead else 0.0


def regime_of(adx: Optional[float], cfg: Config) -> str:
    if adx is None:
        return "unbekannt"
    if adx >= cfg.adx_trend:
        return "trend"
    if adx < cfg.adx_range:
        return "seitwärts"
    return "neutral"


def trend_score(d: Dict[str, list], i: int) -> float:
    """Reiner Trendfaktor in [-1, 1] - wird auch als BTC-Marktfilter genutzt."""
    c, e50, e200 = d["close"][i], d["ema50"][i], d["ema200"][i]
    if e50 is None or e200 is None:
        return 0.0
    return 0.5 * _sign(c - e50) + 0.5 * _sign(e50 - e200)


def score_at(d: Dict[str, list], i: int, cfg: Config, context: Optional[dict] = None):
    """Score für Kerze i. Gibt (score, regime, reasons, values) zurück."""
    w = cfg.weights
    c = d["close"][i]
    reg = regime_of(d["adx"][i], cfg)
    parts: Dict[str, float] = {}
    reasons: List[str] = []

    # 1) Trend
    t = trend_score(d, i)
    parts["trend"] = t
    if t >= 1:
        reasons.append("Aufwärtstrend: Kurs > EMA50 > EMA200")
    elif t <= -1:
        reasons.append("Abwärtstrend: Kurs < EMA50 < EMA200")

    # 2) Momentum (MACD-Histogramm: Vorzeichen + Richtung)
    hist, prev = d["macd_hist"][i], d["macd_hist"][i - 1]
    if hist is not None and prev is not None:
        m = 0.5 * _sign(hist) + 0.5 * _sign(hist - prev)
        parts["momentum"] = m
        if m >= 1:
            reasons.append("MACD positiv und steigend")
        elif m <= -1:
            reasons.append("MACD negativ und fallend")

    # 3) RSI - im Trend Momentum-Lesart, im Seitwärtsmarkt Mean-Reversion
    r = d["rsi"][i]
    if r is not None:
        if reg == "trend":
            if r > 78:
                s = -0.5
                reasons.append(f"RSI {r:.0f} überkauft (Trend, Vorsicht)")
            elif r >= 50:
                s = 1.0
            elif r < 30:
                s = -0.5
            else:
                s = -1.0
        else:
            s = max(-1.0, min(1.0, (50 - r) / 20))
            if r < 30:
                reasons.append(f"RSI {r:.0f} überverkauft (Seitwärtsmarkt -> Rebound möglich)")
            elif r > 70:
                reasons.append(f"RSI {r:.0f} überkauft (Seitwärtsmarkt -> Rücksetzer möglich)")
        parts["rsi"] = s

    # 4) Bänder: Ausbruch (Trend) oder Rückkehr zur Mitte (Seitwärts)
    up, lo = d["bb_up"][i], d["bb_lo"][i]
    dh, dl = d["don_hi"][i - 1], d["don_lo"][i - 1]
    if up is not None and lo is not None and dh is not None:
        if reg == "trend":
            if c > dh:
                parts["bands"] = 1.0
                reasons.append("Ausbruch über 20-Kerzen-Hoch")
            elif c < dl:
                parts["bands"] = -1.0
                reasons.append("Bruch unter 20-Kerzen-Tief")
            else:
                parts["bands"] = 0.0
        else:
            pb = (c - lo) / (up - lo) if up > lo else 0.5
            parts["bands"] = max(-1.0, min(1.0, (0.5 - pb) * 2))
            if pb < 0.05:
                reasons.append("Kurs am unteren Bollinger-Band")
            elif pb > 0.95:
                reasons.append("Kurs am oberen Bollinger-Band")

    # 5) Volumen bestätigt die Kerzenrichtung
    vz = d["vol_z"][i]
    if vz is not None:
        direction = _sign(c - d["open"][i])
        parts["volume"] = direction if vz > 1.5 else 0.0
        if vz > 1.5:
            reasons.append(f"Volumen-Spike (z={vz:.1f}) {'kaufseitig' if direction > 0 else 'verkaufsseitig'}")

    # 6) Übergeordneter Trend: Steigung der EMA200 relativ zur ATR
    e200, e200p, a = d["ema200"][i], d["ema200"][i - 20] if i >= 20 else None, d["atr"][i]
    if e200 is not None and e200p is not None and a:
        slope = (e200 - e200p) / a
        parts["htf"] = max(-1.0, min(1.0, slope / 1.5))

    # 7) Markt-Kontext (nur live verfügbar)
    if context:
        ctx_val, ctx_reasons = context_factor(context)
        if ctx_val is not None:
            parts["context"] = ctx_val
            reasons.extend(ctx_reasons)

    total_w = sum(w.get(k, 0) for k in parts)
    score = 0.0 if total_w == 0 else 100 * sum(w.get(k, 0) * v for k, v in parts.items()) / total_w
    values = {"rsi": r, "adx": d["adx"][i], "atr": a, "macd_hist": hist, "vol_z": vz,
              "ema50": d["ema50"][i], "ema200": e200, "vwap": d["vwap"][i]}
    values.update({f"f_{k}": v for k, v in parts.items()})
    return score, reg, reasons, values


def context_factor(ctx: dict):
    """Kontext-Faktor in [-1, 1]. ctx kann enthalten: fear_greed, funding, btc_trend, is_btc."""
    vals: List[float] = []
    reasons: List[str] = []
    fg = ctx.get("fear_greed")
    if fg is not None:
        if fg <= 20:
            vals.append(0.5)
            reasons.append(f"Extreme Angst (F&G {fg}) - antizyklisch leicht positiv")
        elif fg >= 80:
            vals.append(-0.5)
            reasons.append(f"Extreme Gier (F&G {fg}) - Überhitzungsgefahr")
        else:
            vals.append(0.0)
    fr = ctx.get("funding")
    if fr is not None:
        if fr > 0.0005:
            vals.append(-1.0)
            reasons.append(f"Funding {fr*100:.3f}% hoch - überfüllte Longs, Squeeze-Gefahr")
        elif fr < -0.0003:
            vals.append(0.5)
            reasons.append(f"Funding {fr*100:.3f}% negativ - Short-Squeeze möglich")
        else:
            vals.append(0.0)
    bt = ctx.get("btc_trend")
    if bt is not None and not ctx.get("is_btc"):
        vals.append(bt)
        if bt <= -1:
            reasons.append("BTC im Abwärtstrend - Altcoins meist schwächer")
        elif bt >= 1:
            reasons.append("BTC im Aufwärtstrend - Rückenwind für Altcoins")
    if not vals:
        return None, []
    return sum(vals) / len(vals), reasons


def entry_blockers(d: Dict[str, list], i: int, cfg: Config) -> List[str]:
    """Filter, die einen Kauf trotz gutem Score verhindern."""
    out = []
    a, c = d["atr"][i], d["close"][i]
    if a and c and 100 * a / c > cfg.max_atr_pct:
        out.append(f"Volatilität zu hoch (ATR {100*a/c:.1f}% > {cfg.max_atr_pct}%)")
    if a and c:
        amount = cfg.trade_amount_min or 100.0
        cost_pct = 2 * (cfg.fee_pct + cfg.slippage_pct + 100 * cfg.fee_fixed / amount)
        stop_pct = 100 * cfg.atr_stop_mult * a / c
        if cost_pct > cfg.max_cost_to_risk * stop_pct:
            out.append(f"Kosten zu hoch: {cost_pct:.2f}% Gebühren/Slippage vs. {stop_pct:.2f}% Stop "
                       f"-> größeren Zeitrahmen nutzen")
    if i < WARMUP:
        out.append("Zu wenig Historie")
    return out


def make_signal(symbol: str, d: Dict[str, list], i: int, cfg: Config, context: Optional[dict] = None,
                t: int = 0) -> Signal:
    score, reg, reasons, values = score_at(d, i, cfg, context)
    price = d["close"][i]
    a = d["atr"][i] or price * 0.01
    stop = price - cfg.atr_stop_mult * a
    tp = price + cfg.reward_risk * (price - stop)
    blockers = entry_blockers(d, i, cfg)
    if score >= cfg.buy_threshold:
        action = "BUY"
    elif score <= cfg.sell_threshold:
        action = "SELL"
    else:
        action = "HOLD"
    return Signal(symbol, action, round(score, 1), price, stop, tp, a, reg, reasons, blockers, values, t)


def analyze(symbol: str, candles: List[Candle], cfg: Config, context: Optional[dict] = None) -> Signal:
    """Analysiert die letzte ABGESCHLOSSENE Kerze (die laufende Kerze wird ignoriert)."""
    closed = candles[:-1] if len(candles) > 1 else candles
    if len(closed) < 30:
        raise ValueError(f"{symbol}: zu wenig Kerzen ({len(closed)})")
    d = compute(closed)
    i = len(closed) - 1
    sig = make_signal(symbol, d, i, cfg, context, closed[i].t)
    sig.values["last_price"] = candles[-1].c
    return sig
