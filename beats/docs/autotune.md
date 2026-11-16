# Autotune geil & einfach

FL Studio hat zwei eingebaute Autotunes: **Pitcher** (live, wie klassisches Auto-Tune) und **NewTone** (nachträglich Note für Note). Mit Antares Auto-Tune oder Waves Tune funktioniert es genauso, die Regler heißen nur anders.

## 1. Die Tonart muss stimmen

Wichtiger als jeder Regler. Nimm dieselbe Tonart wie in den Cole-Skripten:

```
python tools/cole_beats.py tonart Am
```

→ zeigt dir Key + Scale, die du in Pitcher/Auto-Tune einstellst.

## 2. Pitcher-Einstellungen nach Sound

| Sound | Speed | Gender | Sonstiges |
|---|---|---|---|
| **Harter Trap-Effekt** (robotisch, Sprünge) | 0 % (ganz links) | 50 % | Key setzen, *Correction* voll |
| **Melodisch / Rage** (deutlich, aber singbar) | 10–20 % | 50 % | Formant aus |
| **Natürlich** (nur korrigieren) | 40–60 % | 50 % | Für Strophen und R&B |
| **Pitched-Down-Adlibs** | 0 % | 30–40 % | Pitch −5 bis −12 in einer Kopie |

So geht's: Mixer-Spur deiner Vocals → Slot → **Pitcher** → oben *Key* auf deine Tonart, darunter die Töne der Skala anhaken (bei Moll z. B. für Am: A B C D E F G).

## 3. Vocal-Chain (Reihenfolge in den Mixer-Slots)

1. **Pitcher** (Autotune)
2. **Fruity Parametric EQ 2**: unter 100 Hz weg (Low Cut), bei 3–5 kHz leicht anheben für Klarheit
3. **Fruity Limiter** im Compressor-Modus: gleichmäßige Lautstärke
4. **Fruity Reeverb 2** oder **Delay 3** auf einem Send, nicht direkt auf der Spur

Tipp: Diese Kette einmal bauen → Mixer-Spur → Dreieck-Menü → *File → Save mixer track state as* → „Cole Vocals“. Nächstes Mal: in den Mixer ziehen, fertig.

## 4. Aufnehmen

- Mit Pitcher *während* der Aufnahme hörst du dich schon getuned, das hilft beim Treffen.
- Mehrere Takes, später die besten Stücke zusammensetzen (Comping).
- Adlibs und Doubles auf eigene Spuren, Doubles leicht links/rechts panen.
