# 50 Aspekte für Krypto-Daytrading mit einem Bot

Recherche-Stand: 4. November 2026. ✅ = im Bot umgesetzt · 🟡 = teilweise · 📝 = deine Aufgabe / Hinweis

## A. Marktlage jetzt (Anfang November 2026)

1. 📝 **BTC unter Druck:** um 76.000–77.000 $, Oktober −7,3 %. Wichtige Marken: Unterstützung 76.000 $, 200-Tage-Linie ~73.000 $, Widerstand 80.000–82.000 $.
2. ✅ **Stimmung „Angst“:** Fear & Greed bei 26. Der Bot liest den Index live und wertet extreme Angst (≤ 20) leicht antizyklisch, extreme Gier (≥ 80) als Warnung.
3. 📝 **ETF-Abflüsse:** Spot-Bitcoin-ETFs verloren am 30.10. 643 Mio. $. Das ist ein Gegenwind für Long-Trades.
4. 📝 **Binance-Hack:** Ende Oktober wurden laut Medien ~6,3 Mrd. $ gestohlen, Auszahlungen waren pausiert. Lehre: Börsenrisiko ist real (siehe 41–43).
5. 📝 **Termine:** US-Midterms (3.11.) und die MSCI-Entscheidung zu Strategy (11.11.) können Kurssprünge auslösen. An solchen Tagen kleinere Beträge oder Pause.
6. ✅ **BTC-Dominanz** zeigt, ob Altcoins Rückenwind haben. Der Bot zeigt sie an und filtert Altcoin-Käufe, wenn BTC im Abwärtstrend ist.
7. ✅ **Trending-Coins** (CoinGecko) und Top-Mover (24h) stehen im Reiter „Trends“. Ein Coin mit +30 % am Tag ist meist schon gelaufen.
8. 📝 **Narrative 2026:** RWA-Tokenisierung, KI-Agenten, DePIN, Prediction Markets, Perp-DEXs und Stablecoins. Narrative wechseln schnell, Hype-Coins sind extrem volatil.

## B. Signale & Analyse

9. ✅ **Trend:** Kurs gegenüber EMA50 und EMA200.
10. ✅ **Momentum:** MACD-Histogramm, Vorzeichen und Richtung.
11. ✅ **RSI regimeabhängig:** Im Trend gilt RSI > 50 als Stärke, im Seitwärtsmarkt RSI < 30 als Kaufzone.
12. ✅ **Marktregime per ADX:** Trend (≥ 25) oder Seitwärts (< 20). Der Bot liest Signale je nach Regime anders.
13. ✅ **Ausbrüche:** Schlusskurs über dem 20-Kerzen-Hoch (Donchian) im Trendmarkt.
14. ✅ **Bollinger-Bänder** für Rückkehr zur Mitte im Seitwärtsmarkt.
15. ✅ **Volumen-Bestätigung:** Volumen-Spike (z-Score > 1,5) in Kerzenrichtung.
16. ✅ **Übergeordneter Trend:** Steigung der EMA200 in ATR-Einheiten.
17. ✅ **Score −100 bis +100** mit Begründung in Klartext statt Black Box.
18. ✅ **Nur abgeschlossene Kerzen** werden bewertet. Die laufende Kerze wird ignoriert, damit Signale nicht flackern.
19. 🟡 **Funding-Rate & Open Interest** (Bybit/Binance-Futures): im Python-Bot. Hohe positive Funding-Rate bedeutet überfüllte Longs und Squeeze-Gefahr. Nur an Extremen aussagekräftig.
20. 📝 **News & Social-Sentiment** (X, Reddit) sind nicht eingebaut. Sie sind leicht manipulierbar und für 5-€-Trades den Aufwand nicht wert.

## C. Risiko-Management

21. ✅ **Stop-Loss bei jedem Trade:** 2 × ATR unter dem Einstieg.
22. ✅ **Kursziel = 2 × Risiko** (Chance-Risiko-Verhältnis 2:1).
23. ✅ **Trailing-Stop:** ab +1R auf Einstand, ab +1,5R mit ATR-Abstand nachziehen.
24. ✅ **Feste Kleinbeträge 5–7 €** je nach Signalstärke.
25. ✅ **Max. offene Positionen** (Standard 3), damit nicht alles im selben Markteinbruch hängt.
26. ✅ **Tagesverlust-Limit:** danach keine neuen Trades bis zum nächsten Tag.
27. ✅ **Max. Drawdown-Stopp** (Python-Bot): Bot pausiert, Strategie muss geprüft werden.
28. ✅ **Cooldown nach Verlust:** kein sofortiger „Rache-Trade“ im selben Coin.
29. ✅ **Volatilitätsfilter:** keine Einstiege bei ATR > 4 % pro Kerze.
30. ✅ **Not-Aus:** Datei `STOP` anlegen (Python) oder Auto-Trading in den Einstellungen ausschalten (Web-App).
31. 📝 **Kein Hebel, keine Futures:** Mit 5 € und Hebel ist das Konto in Minuten weg.

## D. Kosten (bei 5–7 € entscheidend)

32. ✅ **Prozent-Gebühren je Börse** sind wählbar: Binance 0,10 %, Bitvavo 0,25 %, Kraken Pro 0,40 %, Coinbase 1,20 %, Bitpanda ~1,49 %.
33. ✅ **Fixgebühren entlarven:** 1 € fix (Trade Republic) sind bei 6 € Einsatz rund 33 % pro Hin- und Rückweg. Die App warnt und blockiert solche Trades.
34. ✅ **Slippage** (0,05 % pro Seite) ist eingerechnet.
35. ✅ **Kostenfilter:** Wenn Gebühren und Slippage mehr als 25 % des Stop-Abstands ausmachen, wird nicht gekauft.
36. ✅ **Zeitrahmen 1h statt 15m:** größere Bewegungen pro Kerze, Gebühren fallen weniger ins Gewicht.
37. 📝 **Mindestorder:** oft 5 € oder 5 USDT. 5 € liegen genau an der Grenze, 6–7 € sind sicherer.
38. 📝 **Spread bei „Broker-Apps“:** Kauf- und Verkaufskurs liegen oft weit auseinander (versteckte Gebühr). Lieber eine echte Börse mit Orderbuch.

## E. Testen statt Hoffen

39. ✅ **Paper-Trading zuerst:** alles mit Spielgeld, inklusive Gebühren, Slippage und Stops.
40. ✅ **Backtest ohne Look-ahead** (Python): Signal am Schlusskurs, Ausführung zur nächsten Eröffnung, Stop wird vor dem Ziel geprüft.
41. ✅ **Walk-Forward-Optimierung** gegen Überanpassung: auf 70 % optimieren, auf 30 % ungesehenen Daten prüfen.
42. 📝 **Genug Trades:** Unter 30 Trades sagt das Ergebnis fast nichts, ab 100 wird es belastbar.
43. 📝 **Vergleich mit Buy & Hold:** Wenn einfaches Halten besser ist, lohnt sich der Aufwand nicht.
44. 📝 **Mindestens 4 Wochen Paper-Trading**, bevor echtes Geld fließt. Märkte ändern sich, vergangene Ergebnisse garantieren nichts.

## F. Sicherheit, Börse & Recht (Deutschland)

45. 📝 **Nur Börsen mit MiCA-Lizenz** (BaFin oder EU-Pass). Die Übergangsfrist in Deutschland endete am 31.12.2025.
46. 📝 **Nie alles auf einer Börse:** Der Binance-Fall zeigt, dass auch große Börsen Auszahlungen stoppen können.
47. 📝 **API-Keys (falls je echt gehandelt wird):** nur „Handel“, nie „Auszahlung“ erlauben, IP-Whitelist, 2FA. Dieser Bot braucht keine Keys.
48. 📝 **Steuer (§ 23 EStG):** Gewinne aus Verkäufen innerhalb eines Jahres sind steuerpflichtig, jeder Bot-Verkauf ist ein Vorgang. Laut einer Quelle sind Gewinne bis 1.000 €/Jahr steuerfrei (Freigrenze, bitte mit Steuerberater prüfen). Ab 2027 sind Änderungen im Gespräch, und mit DAC8 melden Börsen Transaktionen ans Finanzamt.
49. ✅ **Trade-Journal:** Der Python-Bot schreibt `data/journal.csv` mit Zeit, Kurs, Gebühren und Gewinn, als Grundlage für Steuer und Auswertung.

## G. Psychologie

50. 📝 **Regeln vor Gefühl:** Kein FOMO, kein Nachkaufen von Verlierern, kein Erhöhen der Beträge nach Gewinnen. Der Bot ist ein Werkzeug zum Lernen, kein Geldautomat. Die meisten Daytrader verlieren langfristig Geld.

---

### Quellen
- Marktlage: [KuCoin Daily Report 03.11.2026](https://www.kucoin.com/news/articles/crypto-daily-market-report-november-3-2026), [Yahoo Finance BTC-Ausblick Nov. 2026](https://finance.yahoo.com/markets/crypto/articles/bitcoin-price-outlook-november-2026-020000012.html), [21Shares Ausblick](https://www.21shares.com/en-us/insights/bitcoin-outlook-november-2026), [24/7 Wall St.](https://247wallst.com/investing/cryptocurrency/2026/11/01/bitcoin-price-prediction-for-november-2026/), [cryptonews.net](https://cryptonews.net/news/bitcoin/33687336/)
- Binance-Hack: [TechCrunch](https://techcrunch.com/2026/10/29/binance-pauses-withdrawals-as-hackers-suspected-of-stealing-billions-in-crypto/), [The National](https://www.thenationalnews.com/business/2026/10/31/binance-covers-90-per-cent-of-assets-stolen-in-security-incident/), [Crypto Briefing](https://cryptobriefing.com/binance-covers-90-of-6b-hack-losses-plans-withdrawals-nov-1/)
- Funding & Open Interest: [FXStreet](https://www.fxstreet.com/cryptocurrencies/news/why-is-everyone-in-the-crypto-market-talking-about-open-interest-and-funding-rates-202508070945), [Altrady](https://www.altrady.com/blog/crypto-trading-strategies/crypto-funding-rates-explained), [Chainspot](https://news.chainspot.io/?p=2843)
- Narrative: [CoinGecko Narratives](https://coingecko.com/learn/crypto-narratives), [DEXTools](https://www.dextools.io/news/top-altcoin-trends-2026-narrative-guide), [Yellow Research](https://yellow.com/research/crypto-narratives-2026-capital-flows)
- Backtesting-Fallen: [Coin Bureau](https://coinbureau.com/guides/crypto-trading-bot-mistakes-to-avoid), [Bitsgap](https://bitsgap.com/blog/crypto-bot-backtesting-in-2026-what-it-shows-and-what-it-cannot-predict), [Bitsgap Checkliste](https://bitsgap.com/blog/how-to-read-crypto-backtest-results-like-a-pro-the-8-point-checklist)
- Steuer & MiCA: [PwC](https://blogs.pwc.de/en/german-tax-and-legal-news/article/256917/a-turning-point-in-german-crypto-taxation/), [Tangem MiCA Deutschland](https://tangem.com/en/learning-hub/post/mica-crypto-rules-germany/), [Cointelegraph 2027](https://cointelegraph.com/news/germany-signals-2027-crypto-tax-overhaul-one-year-holding-perk-under-threat), [getdtax](https://getdtax.com/blog/germany-crypto-tax-2026-filing-guide)

Gebührensätze sind Richtwerte für die niedrigste Volumenstufe. Bitte auf der Börsen-Website prüfen, sie ändern sich.
