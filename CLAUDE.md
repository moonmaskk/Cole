# Cole · Projekt-Notizen für Claude

Krypto-Analyse- und Paper-Trading-Bot. Sprache für Nutzer-Texte: Deutsch.

## Grundregeln
- Nur Paper-Trading. Keine echten Orders, keine API-Keys, keine Auszahlungsrechte einbauen, außer der Nutzer verlangt es ausdrücklich, und dann nur nach Rückfrage.
- Standard-Einsatz 5–7 € pro Trade. Gebühren und Slippage immer einrechnen.
- Keine Garantien oder Gewinnversprechen in Texten; Hinweis „keine Anlageberatung“ beibehalten.

## Aufbau
- `cole/` Python-Bot ohne Abhängigkeiten (stdlib). Einstieg: `python -m cole <befehl>`.
  - `indicators.py` kausale Indikatoren · `strategy.py` Score & Signale · `paper.py` virtuelles Depot
  - `backtest.py` Backtest + Walk-Forward · `bot.py` Live-Zyklus · `data.py` Kraken/Binance/Simulator
- `web/app.html` Handy-Web-App (eine Datei, ohne Build-Tools). Strategie-Logik ist eine JS-Kopie von `strategy.py`: Änderungen an Gewichten/Regeln in beiden Dateien nachziehen.
- `web/build.py` erzeugt `docs/index.html` für GitHub Pages. Nach jeder Änderung an `web/app.html` ausführen.

## Prüfen
- `python3 -m unittest discover -s tests`
- Offline-Lauf: `python3 -m cole paper --source sim --fast --cycles 200 --quiet`
- Im Cloud-Container sind Börsen-APIs gesperrt; dort nur `--source sim` testen.
