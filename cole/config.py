"""Konfiguration mit sinnvollen Standardwerten. Überschreibbar per config.json."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, fields


@dataclass
class Config:
    # --- Daten ---
    source: str = "kraken"            # kraken | binance | sim
    quote: str = ""                   # leer = Standard der Quelle (kraken: EUR, binance: USDT, sim: EUR)
    watchlist: list = field(default_factory=lambda: ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"])
    interval_min: int = 60            # Kerzen-Zeitrahmen in Minuten (15m ist bei Spot-Gebühren meist zu teuer)
    history: int = 500                # Kerzen für die Analyse
    use_context: bool = True          # Fear & Greed, Funding, BTC-Filter, Trending

    # --- Strategie ---
    buy_threshold: float = 35.0       # Score ab dem ein Kauf vorgeschlagen wird (-100..100)
    sell_threshold: float = -20.0     # Score ab dem eine offene Position verkauft wird
    adx_trend: float = 25.0           # ADX >= -> Trendmarkt
    adx_range: float = 20.0           # ADX <  -> Seitwärtsmarkt
    max_atr_pct: float = 4.0          # ATR in % des Preises; darüber keine neuen Einstiege (zu volatil)
    max_cost_to_risk: float = 0.25    # Gebühren+Slippage (hin & zurück) dürfen max. 25 % des Stop-Abstands sein
    weights: dict = field(default_factory=lambda: {
        "trend": 25, "momentum": 20, "rsi": 15, "bands": 15, "volume": 10, "htf": 15, "context": 20,
    })

    # --- Risiko & Paper-Trading ---
    start_capital: float = 50.0
    trade_amount_min: float = 5.0     # Einsatz pro Trade in Quote-Währung (0 = risikobasiert rechnen)
    trade_amount_max: float = 7.0     # bei starkem Signal bis zu diesem Betrag
    min_order: float = 5.0            # Mindestorder der Börse (oft 5 EUR / 5 USDT)
    risk_per_trade_pct: float = 1.0   # max. Verlust pro Trade in % des Kapitals (bis zum Stop)
    max_position_pct: float = 25.0    # max. Positionsgröße in % des Kapitals
    max_open_positions: int = 3
    atr_stop_mult: float = 2.0        # Stop = Einstieg - k * ATR
    reward_risk: float = 2.0          # Take-Profit = Einstieg + RR * Risiko
    trailing: bool = True             # ab +1R Stop auf Einstand, danach nachziehen
    fee_pct: float = 0.26             # Gebühr pro Seite in % (Binance 0.10, Bitvavo 0.25, Kraken Pro 0.40)
    fee_fixed: float = 0.0            # Fixgebühr pro Order (z.B. 1.0 bei Trade Republic) - killt Kleinbeträge!
    slippage_pct: float = 0.05        # angenommene Slippage pro Seite in %
    daily_loss_limit_pct: float = 10.0 # Tagesverlust-Limit -> keine neuen Trades für den Rest des Tages
    max_drawdown_pct: float = 15.0    # Max. Drawdown -> Bot pausiert neue Einstiege
    cooldown_bars: int = 4            # Wartezeit (Kerzen) nach einem Verlust im selben Coin

    # --- Laufzeit ---
    loop_seconds: int = 60
    data_dir: str = "data"
    telegram_bot_token: str = ""      # optional: Benachrichtigungen
    telegram_chat_id: str = ""

    def resolved_quote(self) -> str:
        if self.quote:
            return self.quote.upper()
        return {"binance": "USDT"}.get(self.source, "EUR")

    def to_dict(self) -> dict:
        return asdict(self)


def load_config(path: str | None = None, **overrides) -> Config:
    cfg = Config()
    candidates = [path] if path else ["config.json"]
    for p in candidates:
        if p and os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                data = json.load(fh)
            known = {f.name for f in fields(Config)}
            unknown = set(data) - known
            if unknown:
                raise ValueError(f"Unbekannte Einstellungen in {p}: {sorted(unknown)}")
            for k, v in data.items():
                if k == "weights":
                    cfg.weights = {**cfg.weights, **v}
                else:
                    setattr(cfg, k, v)
    for k, v in overrides.items():
        if v is not None:
            setattr(cfg, k, v)
    return cfg
