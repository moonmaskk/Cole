"""Marktdaten: öffentliche Börsen-APIs (ohne API-Key) + Offline-Simulator.

Alle Endpunkte sind reine Lese-Endpunkte. Der Bot sendet NIE Orders an eine Börse.
"""
from __future__ import annotations

import json
import random
import time
import urllib.parse
import urllib.request
import zlib
from dataclasses import dataclass
from typing import Dict, List, Optional

USER_AGENT = "cole-paper-bot/1.0"


@dataclass
class Candle:
    t: int      # Startzeit der Kerze (Unix-Sekunden)
    o: float
    h: float
    l: float
    c: float
    v: float


class DataError(RuntimeError):
    pass


def http_json(url: str, params: Optional[dict] = None, timeout: int = 15, retries: int = 2):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # Netzwerkfehler, Rate-Limit, Geo-Block ...
            last = exc
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise DataError(f"{url.split('?')[0]}: {last}")


# ---------------------------------------------------------------- Kraken
class KrakenSource:
    """Kraken (in der EU/Deutschland reguliert). Max. 720 Kerzen pro Abfrage."""

    name = "kraken"
    BASE = "https://api.kraken.com/0/public"
    INTERVALS = (1, 5, 15, 30, 60, 240, 1440)
    ALIASES = {"BTC": "XBT", "DOGE": "XDG"}

    def pair(self, base: str, quote: str) -> str:
        return self.ALIASES.get(base.upper(), base.upper()) + quote.upper()

    def _result(self, data: dict) -> dict:
        if data.get("error"):
            raise DataError("Kraken: " + ", ".join(data["error"]))
        return data["result"]

    def candles(self, base: str, quote: str, interval_min: int, limit: int = 500) -> List[Candle]:
        if interval_min not in self.INTERVALS:
            raise DataError(f"Kraken unterstützt nur Intervalle {self.INTERVALS}")
        res = self._result(http_json(f"{self.BASE}/OHLC", {"pair": self.pair(base, quote), "interval": interval_min}))
        rows = next(v for k, v in res.items() if k != "last")
        out = [Candle(int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[6])) for r in rows]
        return out[-limit:]

    def tickers(self, quote: str) -> List[dict]:
        """Alle Paare einer Quote-Währung. Änderung = seit 00:00 UTC (Kraken liefert kein 24h-Change)."""
        pairs = self._result(http_json(f"{self.BASE}/AssetPairs"))
        wanted = {}
        for key, info in pairs.items():
            ws = info.get("wsname", "")
            if ws.endswith("/" + quote.upper()) and ".d" not in key:
                base = ws.split("/")[0]
                wanted[key] = {"XBT": "BTC", "XDG": "DOGE"}.get(base, base)
        data = self._result(http_json(f"{self.BASE}/Ticker"))
        out = []
        for key, t in data.items():
            if key not in wanted:
                continue
            last, open_ = float(t["c"][0]), float(t["o"])
            vol_quote = float(t["v"][1]) * float(t["p"][1])
            out.append({"base": wanted[key], "last": last,
                        "change_pct": (last / open_ - 1) * 100 if open_ else 0.0,
                        "quote_volume": vol_quote,
                        "high": float(t["h"][1]), "low": float(t["l"][1])})
        return out


# ---------------------------------------------------------------- Binance
class BinanceSource:
    """Binance Spot-Marktdaten über den öffentlichen Daten-Mirror. Bis 1000 Kerzen/Abfrage, paginiert."""

    name = "binance"
    BASE = "https://data-api.binance.vision/api/v3"
    INTERVALS = {1: "1m", 5: "5m", 15: "15m", 30: "30m", 60: "1h", 240: "4h", 1440: "1d"}

    def candles(self, base: str, quote: str, interval_min: int, limit: int = 500) -> List[Candle]:
        if interval_min not in self.INTERVALS:
            raise DataError(f"Binance: Intervall {interval_min} nicht unterstützt")
        symbol = base.upper() + quote.upper()
        out: List[Candle] = []
        end: Optional[int] = None
        while len(out) < limit:
            params = {"symbol": symbol, "interval": self.INTERVALS[interval_min], "limit": min(1000, limit - len(out))}
            if end is not None:
                params["endTime"] = end
            rows = http_json(f"{self.BASE}/klines", params)
            if not rows:
                break
            batch = [Candle(int(r[0]) // 1000, float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])) for r in rows]
            out = batch + out
            end = int(rows[0][0]) - 1
            if len(rows) < params["limit"]:
                break
        return out[-limit:]

    def tickers(self, quote: str) -> List[dict]:
        out = []
        for t in http_json(f"{self.BASE}/ticker/24hr"):
            sym = t["symbol"]
            if not sym.endswith(quote.upper()):
                continue
            base = sym[: -len(quote)]
            if base.endswith(("UP", "DOWN", "BULL", "BEAR")) or float(t["lastPrice"]) == 0:
                continue
            out.append({"base": base, "last": float(t["lastPrice"]), "change_pct": float(t["priceChangePercent"]),
                        "quote_volume": float(t["quoteVolume"]), "high": float(t["highPrice"]), "low": float(t["lowPrice"])})
        return out


# ---------------------------------------------------------------- Simulator
class SimSource:
    """Offline-Markt-Simulator mit Regimewechseln (Trend auf/ab, Seitwärts, Volatilitätsschübe).

    Deterministisch pro Coin (Seed aus dem Namen). Bei jedem Aufruf von candles()
    kommt eine neue Kerze hinzu - so lässt sich der Live-Loop ohne Internet testen.
    """

    name = "sim"
    START_PRICES = {"BTC": 70000, "ETH": 2200, "SOL": 160, "XRP": 2.2, "ADA": 0.6, "LINK": 15,
                    "AVAX": 25, "DOGE": 0.18, "DOT": 4.5, "SUI": 3.0}

    def __init__(self, seed: int = 0, steps_per_call: int = 1):
        self.seed = seed
        self.steps_per_call = steps_per_call
        self._series: Dict[str, List[Candle]] = {}
        self._rng: Dict[str, random.Random] = {}
        self._regime: Dict[str, list] = {}

    def _step(self, key: str, interval_min: int) -> None:
        rng, series = self._rng[key], self._series[key]
        reg = self._regime[key]
        if reg[1] <= 0:  # neues Regime: [drift, verbleibende Kerzen, vol]
            kind = rng.choice(["up", "down", "range", "range", "vol"])
            drift = {"up": 0.0012, "down": -0.0012, "range": 0.0, "vol": 0.0}[kind]
            vol = {"vol": 0.012}.get(kind, 0.005)
            reg[:] = [drift, rng.randint(60, 250), vol]
        reg[1] -= 1
        prev = series[-1].c if series else self._start(key)
        drift, _, vol = reg
        ret = drift + rng.gauss(0, vol)
        o = prev * (1 + rng.gauss(0, vol * 0.1))
        c = max(o * (1 + ret), 1e-9)
        h = max(o, c) * (1 + abs(rng.gauss(0, vol * 0.6)))
        l = min(o, c) * (1 - abs(rng.gauss(0, vol * 0.6)))
        v = abs(rng.gauss(1000, 300)) * (1 + 8 * abs(ret))
        t = series[-1].t + interval_min * 60 if series else 1_700_000_000
        series.append(Candle(t, o, h, l, c, v))

    def _start(self, key: str) -> float:
        return float(self.START_PRICES.get(key.split("|")[0], 10.0))

    def candles(self, base: str, quote: str, interval_min: int, limit: int = 500) -> List[Candle]:
        key = f"{base.upper()}|{interval_min}"
        if key not in self._series:
            self._series[key] = []
            self._rng[key] = random.Random(zlib.crc32(key.encode()) + self.seed)
            self._regime[key] = [0.0, 0, 0.005]
            for _ in range(limit):
                self._step(key, interval_min)
        else:
            for _ in range(self.steps_per_call):
                self._step(key, interval_min)
        return list(self._series[key][-limit:])

    def tickers(self, quote: str) -> List[dict]:
        out = []
        for base in self.START_PRICES:
            cs = self.candles(base, quote, 60, 300)
            day = cs[-24:]
            out.append({"base": base, "last": cs[-1].c, "change_pct": (cs[-1].c / day[0].o - 1) * 100,
                        "quote_volume": sum(c.v * c.c for c in day), "high": max(c.h for c in day),
                        "low": min(c.l for c in day)})
        return out


def get_source(name: str, **kw):
    sources = {"kraken": KrakenSource, "binance": BinanceSource, "sim": SimSource}
    if name not in sources:
        raise ValueError(f"Unbekannte Datenquelle '{name}'. Erlaubt: {', '.join(sources)}")
    return sources[name](**kw) if name == "sim" else sources[name]()


# ---------------------------------------------------------------- Markt-Kontext
def fear_greed() -> Optional[dict]:
    """Crypto Fear & Greed Index (alternative.me). 0 = extreme Angst, 100 = extreme Gier."""
    try:
        d = http_json("https://api.alternative.me/fng/", {"limit": 2}, retries=1)["data"]
        return {"value": int(d[0]["value"]), "label": d[0]["value_classification"],
                "previous": int(d[1]["value"]) if len(d) > 1 else None}
    except Exception:
        return None


def coingecko_trending() -> List[dict]:
    try:
        coins = http_json("https://api.coingecko.com/api/v3/search/trending", retries=1).get("coins", [])
        out = []
        for c in coins[:10]:
            it = c["item"]
            chg = (it.get("data") or {}).get("price_change_percentage_24h", {}).get("usd")
            out.append({"symbol": it["symbol"].upper(), "name": it["name"], "rank": it.get("market_cap_rank"),
                        "change_24h": chg})
        return out
    except Exception:
        return []


def coingecko_global() -> Optional[dict]:
    try:
        d = http_json("https://api.coingecko.com/api/v3/global", retries=1)["data"]
        return {"btc_dominance": d["market_cap_percentage"].get("btc"),
                "eth_dominance": d["market_cap_percentage"].get("eth"),
                "mcap_change_24h": d.get("market_cap_change_percentage_24h_usd"),
                "total_mcap_usd": d.get("total_market_cap", {}).get("usd")}
    except Exception:
        return None


def funding_and_oi(base: str) -> Optional[dict]:
    """Funding-Rate & Open Interest des Perpetual-Futures (Bybit, Fallback Binance). Nur Lesen."""
    sym = base.upper() + "USDT"
    try:
        lst = http_json("https://api.bybit.com/v5/market/tickers", {"category": "linear", "symbol": sym},
                        retries=0)["result"]["list"]
        if lst:
            t = lst[0]
            return {"funding": float(t["fundingRate"]), "open_interest": float(t["openInterest"]),
                    "source": "bybit"}
    except Exception:
        pass
    try:
        t = http_json("https://fapi.binance.com/fapi/v1/premiumIndex", {"symbol": sym}, retries=0)
        oi = http_json("https://fapi.binance.com/fapi/v1/openInterest", {"symbol": sym}, retries=0)
        return {"funding": float(t["lastFundingRate"]), "open_interest": float(oi["openInterest"]),
                "source": "binance"}
    except Exception:
        return None


def market_context(source_name: str, watchlist: List[str]) -> dict:
    """Sammelt den übergeordneten Markt-Kontext. Fehlende Daten werden einfach weggelassen."""
    if source_name == "sim":
        return {"fear_greed": None, "global": None, "trending": [], "funding": {}}
    return {
        "fear_greed": fear_greed(),
        "global": coingecko_global(),
        "trending": coingecko_trending(),
        "funding": {b: f for b in watchlist if (f := funding_and_oi(b))},
    }


def interval_label(minutes: int) -> str:
    if minutes % 1440 == 0:
        return f"{minutes // 1440}d"
    if minutes % 60 == 0:
        return f"{minutes // 60}h"
    return f"{minutes}m"


def bars_per_year(interval_min: int) -> float:
    return 365 * 24 * 60 / interval_min


__all__ = ["Candle", "DataError", "get_source", "market_context", "interval_label", "bars_per_year"]
