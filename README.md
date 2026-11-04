# Cole · Krypto-Radar

Analysiert laufend Krypto-Trends, gibt Kauf- und Verkaufsvorschläge mit Stop-Loss und Kursziel und handelt im **Testmodus mit Spielgeld** (Paper-Trading), standardmäßig mit **5–7 € pro Trade**. Echtes Geld wird nie bewegt, es werden keine API-Keys gebraucht.

> Keine Anlageberatung. Krypto-Daytrading ist hochriskant, die meisten Daytrader verlieren Geld.

Die 50 recherchierten Aspekte stehen in [ASPEKTE.md](ASPEKTE.md).

## 1. Handy-Web-App (`web/app.html` → `docs/index.html`)

Eine einzige HTML-Datei, die direkt im Browser läuft:
- holt alle 60 s Kerzen von Binance (öffentliche Daten), dazu Fear & Greed, BTC-Dominanz, Top-Mover und CoinGecko-Trending
- Score −100…+100 aus 7 Faktoren, mit Begründung in Klartext
- Paper-Trading mit 5–7 €, Gebühren je Börse, Stop, Ziel, Trailing-Stop, Tagesverlust-Limit
- Depot, Verlauf und Einstellungen bleiben im Browser gespeichert
- lässt sich als App auf den Home-Bildschirm legen (Manifest und Icon liegen bei)

Wenn keine Börsendaten erreichbar sind (z. B. in der claude.ai-Vorschau), läuft automatisch ein **Simulationsmodus**, deutlich markiert.

**Veröffentlichen über GitHub Pages:** Der Workflow `.github/workflows/pages.yml` veröffentlicht den Ordner `docs/` bei jedem Push auf `main`. Einmalig nötig:
1. Repo öffentlich machen (Pages für private Repos braucht GitHub Pro): *Settings → General → Danger Zone → Change visibility*.
2. *Settings → Pages → Source: GitHub Actions*.

Danach ist die App unter `https://<nutzername>.github.io/<repo>/` erreichbar.
Nach Änderungen an `web/app.html`: `python3 web/build.py` ausführen.

## 2. Python-Bot (`cole/`)

Für den PC, ohne Zusatzpakete (Python 3.10+):

```bash
python -m cole trends                 # Markt-Überblick: Top-Mover, Trending, Stimmung + Analyse
python -m cole scan                   # Watchlist analysieren, Vorschläge mit Einsatz/Stop/Ziel
python -m cole paper                  # Live-Testmodus: handelt laufend mit Spielgeld (Strg+C beendet)
python -m cole status                 # Paper-Depot und Trade-Historie
python -m cole backtest --all --source binance --bars 4000
python -m cole optimize --symbol ETH --source binance
python -m cole paper --source sim --fast --cycles 300   # Offline-Test mit Simulator
```

`paper` schreibt zusätzlich `data/dashboard.html` (lädt sich selbst neu) und `data/journal.csv` (Trade-Journal).

Einstellungen: `config.example.json` nach `config.json` kopieren und anpassen. Wichtige Werte:
`trade_amount_min/max` (5/7), `fee_pct`, `fee_fixed`, `interval_min` (60), `buy_threshold` (35), `max_open_positions`, `daily_loss_limit_pct`.

Datenquellen: `kraken` (Standard, EUR), `binance` (USDT, längere Historie für Backtests), `sim` (offline).

Tests: `python -m unittest discover -s tests`
