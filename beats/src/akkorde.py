# TITLE: Cole - Akkorde
# INFO: Fertige Akkordfolge nach Stimmung. Tonart merken - Melodie, 808 und Autotune nutzen dieselbe.


def createDialog():
    form = flp.ScriptDialog('Cole - Akkorde', 'Waehle Tonart + Stimmung. Gleiche Werte in Melodie/808 = passt automatisch zusammen.')
    add_common_inputs(form)
    form.AddInputCombo('Klang', ['Normal (3 Toene)', '7er (voller, R&B/Lo-Fi)', 'Weit (Pads)'], 0)
    form.AddInputCombo('Rhythmus', ['Lang halten', 'Stabs (kurz)', 'Arpeggio', 'Pluck-Muster'], 0)
    form.AddInputKnobInt('Oktave', 4, 2, 6)
    form.AddInputCheckbox('Alte Noten loeschen', True)
    return form


def build_chords(key, scale_name, prog_name, bars, seed, klang, rhythm, octave, P):
    rng = Rng(seed)
    root = 12 * (octave + 1) + key
    size = 4 if klang == 1 else 3
    bar = P * 4
    prev = None
    out = []  # (pitch, time, length, velocity)
    for b, (deg, scale) in enumerate(progression_roots(key, scale_name, prog_name, bars)):
        ch = voice_lead(prev, chord_notes(root, scale, deg, size))
        prev = ch
        voiced = list(ch)
        if klang == 2:
            voiced = [ch[0] - 12] + ch[1:] + [ch[0] + 12]
        t0 = b * bar
        if rhythm == 0:
            for p in voiced:
                out.append((p, t0, bar, 0.72))
        elif rhythm == 1:
            pattern = rng.choice([[0, 3, 6, 10, 12], [0, 3, 8, 11], [0, 6, 8, 14], [0, 2, 6, 10]])
            for step in pattern:
                for p in voiced:
                    out.append((p, t0 + step * P // 4, P // 4, 0.8 if step == 0 else 0.65))
        elif rhythm == 2:
            seq = voiced + [voiced[-2]] if len(voiced) > 2 else voiced
            for i in range(8):
                p = seq[i % len(seq)] + (12 if i >= 4 and rng.chance(0.3) else 0)
                out.append((p, t0 + i * P // 2, P // 2, 0.7 if i % 2 else 0.85))
        else:
            for i in range(16):
                if i % 4 == 0 or rng.chance(0.35):
                    p = voiced[rng.randint(0, len(voiced) - 1)]
                    out.append((p, t0 + i * P // 4, P // 4, 0.75))
    return out


def apply(form):
    key, scale_name, prog_name, bars, seed = common_values(form)
    if form.GetInputValue('Alte Noten loeschen'):
        clear_score()
    for p, t, l, v in build_chords(key, scale_name, prog_name, bars, seed,
                                   form.GetInputValue('Klang'), form.GetInputValue('Rhythmus'),
                                   form.GetInputValue('Oktave'), ppq()):
        add_note(p, t, l, v)
