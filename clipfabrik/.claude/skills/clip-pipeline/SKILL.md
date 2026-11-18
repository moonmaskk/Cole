---
name: clip-pipeline
description: Architektur-Regeln für ClipFabrik (Status-Maschine, Worker, Erkennung, Render). Nutzen bei Änderungen an pipeline, detect, recorder, media oder db.
---

- **Status-Maschine ist die Wahrheit.** Jeder Worker holt sich genau einen Clip mit seinem Eingangsstatus (`db.next_with`), arbeitet, setzt den Folgestatus. Nie Status überspringen, nie Arbeit nur im Speicher halten. Nach Absturz muss es dort weitergehen.
- **Bester zuerst:** `next_with` sortiert nach Score, dann neuester. Neue Queues genauso.
- **Erkennung:** robuster z-Wert `(burst - median) / (1.4826·MAD + 1)`, Zählung max. 2 Nachrichten/Nutzer/Fenster. Chat reagiert 5–10 s verzögert, deshalb `pre_seconds` groß. Schwellen gehören in `config.DEFAULTS` + UI, nicht in den Code.
- **Aufnahme ohne Neukodierung** (`-c copy`, mpegts-Segmente mit Uhrzeit im Namen). Neukodierung nur im Render.
- **Render:** zuerst exakt zuschneiden (`src.mp4`), dann Layout + `subtitles=subs.ass` mit `cwd` im Clip-Ordner (vermeidet Windows-Pfad-Escaping). Ohne libass-Erfolg ohne Untertitel weiterrendern, nie abbrechen.
- **Windows:** Subprozesse mit `creationflags=media.NO_WINDOW`; Pfade über `pathlib`; keine `%s`-strftime.
- **16+ Streamer:** ein Chat-Socket für alle Kanäle, ein Recorder-Thread je Streamer, Render seriell (CPU/GPU-Last). Bandbreite ≈ Streamer × Bitrate der gewählten Qualität.
