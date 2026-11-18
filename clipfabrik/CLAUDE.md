# ClipFabrik · Notizen für Claude

Lokale Clip-Pipeline: Twitch-Streams aufnehmen → Chat-Ausschlag erkennen → bewerten → 9:16-Clip mit Untertiteln → Dashboard/Telegram. Nutzer-Texte auf Deutsch. Nutzer ist kein Entwickler: kurz, klar, ohne Jargon.

## Ziel (für /goal)
Ein Programm, das auf Windows per Doppelklick läuft, 16 Streamer parallel überwacht und fertige, postbare Clips liefert. Jede Änderung muss `python -m unittest discover -s tests` grün lassen und den Demo-Lauf (`python -m clipfabrik --demo`) bestehen.

## Regeln
- Clippen nur mit Erlaubnis der Streamer; Quellenangabe bleibt im Clip. Nichts erfinden/generieren, nur vorhandenes Material schneiden.
- Keine Schlüssel in Code/Repo. Einstellungen liegen in `data/settings.json` (gitignored).
- Nur stdlib + `streamlink` + `imageio-ffmpeg`; `faster-whisper` optional. Neue Abhängigkeiten nur mit Grund.
- Token sparen: `data/`, `build/`, `dist/`, `.venv/` nie lesen. Gezielt greppen statt ganze Dateien lesen. Antworten kurz.

## Aufbau (`clipfabrik/`)
`config` Einstellungen · `db` SQLite, Status je Clip (NEW→CUT→JUDGED→RENDERED→DELIVERED→POSTED | REJECTED/FAILED) · `chat` anonymer Twitch-IRC · `detect` z-Wert/Signale/Vorab-Score · `recorder` streamlink→ffmpeg-Ringpuffer · `media` Schnitt, ASS-Untertitel, 9:16-Render · `pipeline` Worker + Supervisor + Demo · `telegram` Lieferung · `server` + `ui.html` Dashboard (eine Datei, kein Build).

## Prüfen
- `python -m unittest discover -s tests` (~30 s, inkl. End-to-End-Demo)
- `python -m clipfabrik --no-browser` → http://127.0.0.1:8765, Button „Testclip erzeugen“
- Im Cloud-Container ist Twitch gesperrt: dort nur Demo/Tests.
- Windows-.exe baut GitHub Actions (`.github/workflows/clipfabrik-exe.yml`).

## Nächste Schritte
1. KI-Bewertung (Ollama-Vision oder Cloud) in `Pipeline._judge_one` mit festem JSON (keep, hype, start_s, end_s, subject_x, hook).
2. Facecam-Bereich pro Streamer im UI markieren (Feld `facecam` existiert schon).
3. Kick/YouTube als weitere Quellen.
