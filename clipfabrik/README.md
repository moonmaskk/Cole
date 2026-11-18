# ClipFabrik

Nimmt Twitch-Streams auf, erkennt die besten Momente am Chat und schneidet daraus fertige 9:16-Clips mit Quellenangabe (optional mit Untertiteln). Posten musst du selbst.

> Clippe nur Streamer, die Clipping erlauben oder eine Clipping-Kampagne haben, und nenne sie immer als Quelle. Ob sich das Clippen finanziell lohnt, ist nicht garantiert.

## Starten (Windows)
**Variante A – .exe:** Unter *GitHub → Actions → „ClipFabrik Windows-EXE“ → letzter Lauf → Artifacts* `ClipFabrik-Windows` herunterladen, entpacken, `ClipFabrik.exe` doppelklicken.

**Variante B – mit Python (inkl. Untertitel):** Python 3.11+ installieren (Haken bei „Add to PATH“), dann `Start-ClipFabrik.bat` doppelklicken. Beim ersten Start wird alles eingerichtet.

Danach öffnet sich das Dashboard im Browser. Drück **„Testclip erzeugen“**: daran siehst du, dass alles läuft. Danach Streamer unter *Einstellungen* eintragen.

## Was das Programm macht
1. **Aufnehmen:** prüft jede Minute, wer live ist, und hält von jedem Stream die letzten Minuten im Puffer (ohne Neukodierung).
2. **Chat lesen:** Schreibt der Chat plötzlich viel mehr als sonst (robuster z-Wert, genug verschiedene Leute) oder rufen mehrere „clip“, wird der Moment markiert.
3. **Bewerten:** Note 1–10 aus den Chat-Signalen; unter der Mindestnote fliegt der Clip raus. Doppelte Momente: der stärkere bleibt.
4. **Schneiden:** 9:16 mit unscharfem Hintergrund (oder Facecam oben/Gameplay unten), Hook, Quellenangabe, einheitliche Lautstärke, optional Wort-für-Wort-Untertitel.
5. **Liefern:** im Dashboard (Vorschau, Text kopieren, Download) und optional per Telegram mit Buttons „gepostet / verwerfen / neu rendern“.

## 16 Streamer – geht das?
Ja. Die Aufnahme kostet kaum Rechenleistung, entscheidend ist die **Internetleitung**:

| Qualität | pro Stream | 16 Streamer |
|---|---|---|
| 480p | ~1,5 Mbit/s | ~25 Mbit/s |
| 720p | ~3–4,5 Mbit/s | ~50–70 Mbit/s |

Standard ist 480p (für Hochkant-Clips reicht das meist). Puffer auf der Festplatte: ca. 1–2 GB. Rendern dauert pro Clip je nach PC 10–40 s.

## iPad, Laptop, PC
- **PC (empfohlen):** läuft hier, muss angeschaltet bleiben.
- **Laptop:** kann ebenfalls ClipFabrik laufen lassen, z. B. 8 Streamer auf dem PC und 8 auf dem Laptop, wenn die Leitung eines Geräts nicht reicht. Er muss dann auch an bleiben (Energiesparmodus aus).
- **iPad/Handy:** können das Programm nicht selbst ausführen, aber das **Dashboard im WLAN öffnen** (Einstellungen → „Zugriff im WLAN erlauben“, Neustart, angezeigte Adresse im Safari öffnen) oder die Clips per Telegram bekommen und von dort posten.

## Für Entwickler
```
pip install -r requirements.txt   # optional: pip install faster-whisper
python -m clipfabrik              # Dashboard auf http://127.0.0.1:8765
python -m unittest discover -s tests
```
