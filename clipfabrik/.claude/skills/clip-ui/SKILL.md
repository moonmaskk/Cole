---
name: clip-ui
description: UI-Regeln für das ClipFabrik-Dashboard (ui.html). Nutzen bei jeder Änderung an der Oberfläche.
---

- Eine Datei `clipfabrik/ui.html`, Vanilla-JS, kein Build, keine CDN-Abhängigkeit (läuft offline und in der .exe).
- Dunkles Theme über die CSS-Variablen in `:root`; neue Farben nur dort.
- Muss auf Desktop, iPad und iPhone funktionieren (Dashboard ist im WLAN erreichbar). Touch-Ziele ≥ 36 px.
- Texte deutsch, kurz, ohne Fachbegriffe; Zustände immer sichtbar (leer, lädt, Fehler).
- Wenn global installiert, für Feinschliff diese Skills nutzen: `frontend-design`, `impeccable-polish`, `impeccable-layout`, `impeccable-typeset`, `web-design-guidelines`, `emil-design-eng`, `writing-guidelines`.
- Danach `clip-qa` ausführen (Screenshots ansehen).
