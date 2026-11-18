---
name: clip-qa
description: Prüfroutine für ClipFabrik. Nutzen nach jeder Code-Änderung, bevor etwas als fertig gemeldet wird.
---

1. `python -m unittest discover -s tests` – muss grün sein.
2. UI geändert? Server starten (`python -m clipfabrik --no-browser`), mit Playwright Screenshots in Desktop (1400×950) und iPhone (390×844) machen, ansehen, Button „Testclip erzeugen“ einmal durchlaufen lassen.
3. Render geändert? Ein Bild aus `data/clips/*/clip.mp4` ziehen (`ffmpeg -ss 1 -frames:v 1`) und ansehen: 1080×1920, Text lesbar, nichts abgeschnitten.
4. Detektor geändert? Tests für ruhigen Chat, Ausschlag, Einzel-Spammer und Clip-Rufe müssen bestehen.
5. Ergebnis in 2–4 Sätzen auf Deutsch melden: was geprüft wurde, was nicht.
