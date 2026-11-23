# Lernvideos

Erzeugt MP4-Lernvideos mit deutscher Sprachausgabe und Untertiteln.
Kein Build-Tool, keine Web-Abhaengigkeiten: Frames mit PIL, Stimme mit
piper-tts, Schnitt mit ffmpeg.

## Aufbau
- `vlib.py` – Renderbibliothek (Themes, Header, Karten, Pfeile, Untertitel-Leiste)
- `video_bio.py` – Video 1: E605 (Parathion) an der cholinergen Synapse
- `video_de.py` – Video 2: Anglizismen, Pruefungsvortrag
- `build.py` – rendert Frames, synthetisiert die Stimme, baut das MP4

Ein Video besteht aus `SHOTS`: Paare aus Untertiteltext und Zeichenfunktion.
Der Untertiteltext ist zugleich der gesprochene Text; seine Audiodauer legt
fest, wie lange das Bild steht.

## Bauen
    pip install piper-tts
    # deutsche Stimme (de-thorsten-low.onnx + .json) nach $SCR/voice/ legen
    python3 build.py video_bio /pfad/01_Bio.mp4 "Titel"
    python3 build.py video_de  /pfad/02_Deutsch.mp4 "Titel"

Der Pfad zur Stimme steht in `build.py` (`SCR`, `VOICE`).

Die fertigen MP4/SRT/Vorschaubilder sind bewusst nicht eingecheckt
(siehe `.gitignore`) – sie lassen sich jederzeit neu bauen.
