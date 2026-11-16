# Sampling in FL Studio, einfach gemacht

Wie Produzenten Samples einsetzen, grob in sechs Arten. Alle gehen mit FL-Bordmitteln.

| Technik | Wie es klingt | So machst du es in FL |
|---|---|---|
| **Loop (Original)** | Sample bleibt erkennbar, Drums drunter | Sample in die Playlist, Tempo per *Stretch* (Sampler → Time → Stretch, Modus „Resample“ oder „Auto“) anpassen |
| **Chop & Flip** | Stücke neu angeordnet, neue Melodie aus altem Material | Sample in **Slicex** ziehen → Slices entstehen automatisch → **Cole - Sample Chops** → Stil „Random Flip“ oder „Hook-Loop“ |
| **Stutter / Vocal Chops** | Abgehackte, rhythmische Wiederholungen | Slicex + Chops-Stil „Stutter / Repeat“. Kurze Release, Hall drauf |
| **Pitch & Slow** | Dunkel, schwer, „Chopped & Screwed“ | Sampler → Pitch −3 bis −7 Halbtöne, oder Chops-Stil „Half-Time“ |
| **Rückwärts** | Traumhaft, Übergänge | Sampler → *Reverse* anhaken, oder Chops-Stil „Rückwärts-Flip“ |
| **Layer / Textur** | Sample nur als Atmosphäre im Hintergrund | Leise, Lowpass-Filter (Fruity Filter oder EQ), Vinyl-Rauschen aus `FX` |

## Schritt für Schritt: Chop & Flip in 2 Minuten

1. Sample aus dem Browser auf einen leeren Kanal ziehen, Rechtsklick → *Replace → Slicex*. Oder Slicex laden und das Sample hineinziehen.
2. In Slicex oben *Auto-Slicing* wählen (z. B. „Medium“). Merk dir die Anzahl Slices.
3. Piano Roll von Slicex → **Cole - Sample Chops** → *Anzahl Slices* einstellen → Stil wählen → Variante drehen.
4. Gefällt dir eine Stelle? Den Rest löschen, Noten verschieben, eigene Slices nachspielen: Jetzt ist es dein Flip.

Tipps: Mit **Edison** (Kanal → Rechtsklick → *Edit in Edison*) kannst du Samples zuschneiden, Rauschen entfernen und Tempo erkennen. *Stretch* in Slicex/Sampler hält das Sample im Projekttempo.

## Tonart vom Sample herausfinden

- Steht oft im Dateinamen; der Pack-Sortierer schreibt sie vorne hin: `[90 Cm] ...`
- Sonst: In FL einen Piano-Kanal öffnen und Töne zum Sample spielen, bis einer „sitzt“. Mit `python tools/cole_beats.py tonart Cm` siehst du dann alle passenden Töne.

## Rechte

Samples aus fremden Songs brauchen für Veröffentlichungen eine Freigabe (Clearance). Royalty-free Packs (z. B. aus Splice oder gekauften Drumkits) sind meist frei nutzbar; lies trotzdem die Lizenz des Packs.
