"""Technische Indikatoren in reinem Python (keine Abhängigkeiten).

Alle Funktionen sind kausal: Wert i nutzt nur Daten bis einschließlich i
(kein Look-ahead-Bias). Werte vor der Aufwärmphase sind None.
"""
from __future__ import annotations

import math
from typing import List, Optional

Series = List[Optional[float]]


def sma(values: Series, n: int) -> Series:
    out: Series = [None] * len(values)
    window: list = []
    total = 0.0
    for i, v in enumerate(values):
        if v is None:
            window, total = [], 0.0
            continue
        window.append(v)
        total += v
        if len(window) > n:
            total -= window.pop(0)
        if len(window) == n:
            out[i] = total / n
    return out


def ema(values: Series, n: int) -> Series:
    """EMA, gestartet mit dem SMA der ersten n gültigen Werte."""
    out: Series = [None] * len(values)
    k = 2.0 / (n + 1)
    seed: list = []
    prev: Optional[float] = None
    for i, v in enumerate(values):
        if v is None:
            continue
        if prev is None:
            seed.append(v)
            if len(seed) == n:
                prev = sum(seed) / n
                out[i] = prev
            continue
        prev = v * k + prev * (1 - k)
        out[i] = prev
    return out


def wilder(values: Series, n: int) -> Series:
    """Wilder-Glättung (RMA), wie bei RSI/ATR/ADX üblich."""
    out: Series = [None] * len(values)
    seed: list = []
    prev: Optional[float] = None
    for i, v in enumerate(values):
        if v is None:
            continue
        if prev is None:
            seed.append(v)
            if len(seed) == n:
                prev = sum(seed) / n
                out[i] = prev
            continue
        prev = (prev * (n - 1) + v) / n
        out[i] = prev
    return out


def rsi(closes: List[float], n: int = 14) -> Series:
    gains: Series = [None]
    losses: Series = [None]
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    ag, al = wilder(gains, n), wilder(losses, n)
    out: Series = [None] * len(closes)
    for i in range(len(closes)):
        if ag[i] is None or al[i] is None:
            continue
        out[i] = 100.0 if al[i] == 0 else 100.0 - 100.0 / (1 + ag[i] / al[i])
    return out


def macd(closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
    ef, es = ema(closes, fast), ema(closes, slow)
    line: Series = [None if (a is None or b is None) else a - b for a, b in zip(ef, es)]
    sig = ema(line, signal)
    hist: Series = [None if (a is None or b is None) else a - b for a, b in zip(line, sig)]
    return line, sig, hist


def bollinger(closes: List[float], n: int = 20, k: float = 2.0):
    mid = sma(closes, n)
    upper: Series = [None] * len(closes)
    lower: Series = [None] * len(closes)
    for i in range(n - 1, len(closes)):
        if mid[i] is None:
            continue
        w = closes[i - n + 1:i + 1]
        sd = math.sqrt(sum((x - mid[i]) ** 2 for x in w) / n)
        upper[i], lower[i] = mid[i] + k * sd, mid[i] - k * sd
    return mid, upper, lower


def true_range(highs, lows, closes) -> Series:
    out: Series = [None] * len(closes)
    for i in range(len(closes)):
        if i == 0:
            out[i] = highs[i] - lows[i]
        else:
            pc = closes[i - 1]
            out[i] = max(highs[i] - lows[i], abs(highs[i] - pc), abs(lows[i] - pc))
    return out


def atr(highs, lows, closes, n: int = 14) -> Series:
    return wilder(true_range(highs, lows, closes), n)


def adx(highs, lows, closes, n: int = 14) -> Series:
    plus_dm: Series = [None]
    minus_dm: Series = [None]
    for i in range(1, len(closes)):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        plus_dm.append(up if (up > down and up > 0) else 0.0)
        minus_dm.append(down if (down > up and down > 0) else 0.0)
    tr = true_range(highs, lows, closes)
    tr[0] = None
    s_tr, s_p, s_m = wilder(tr, n), wilder(plus_dm, n), wilder(minus_dm, n)
    dx: Series = [None] * len(closes)
    for i in range(len(closes)):
        if s_tr[i] in (None, 0) or s_p[i] is None or s_m[i] is None:
            continue
        pdi, mdi = 100 * s_p[i] / s_tr[i], 100 * s_m[i] / s_tr[i]
        dx[i] = 0.0 if pdi + mdi == 0 else 100 * abs(pdi - mdi) / (pdi + mdi)
    return wilder(dx, n)


def rolling_max(values, n: int) -> Series:
    return [None if i < n - 1 else max(values[i - n + 1:i + 1]) for i in range(len(values))]


def rolling_min(values, n: int) -> Series:
    return [None if i < n - 1 else min(values[i - n + 1:i + 1]) for i in range(len(values))]


def zscore(values, n: int = 20) -> Series:
    out: Series = [None] * len(values)
    for i in range(n - 1, len(values)):
        w = values[i - n + 1:i + 1]
        m = sum(w) / n
        sd = math.sqrt(sum((x - m) ** 2 for x in w) / n)
        out[i] = 0.0 if sd == 0 else (values[i] - m) / sd
    return out


def rolling_vwap(highs, lows, closes, volumes, n: int = 96) -> Series:
    out: Series = [None] * len(closes)
    pv = [(h + l + c) / 3 * v for h, l, c, v in zip(highs, lows, closes, volumes)]
    for i in range(n - 1, len(closes)):
        vol = sum(volumes[i - n + 1:i + 1])
        out[i] = None if vol == 0 else sum(pv[i - n + 1:i + 1]) / vol
    return out
