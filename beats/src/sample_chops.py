# TITLE: Cole - Sample Chops
# INFO: Chop-Muster fuer Slicex / Fruity Slicer. Sample reinziehen, Slices machen, dieses Skript im Piano Roll starten.


STYLES = ['Der Reihe nach (Original-Feeling)', 'Random Flip', 'Stutter / Repeat', 'Hook-Loop (A A B A)',
          'Rueckwaerts-Flip', 'Half-Time (langsam, dunkel)']


def createDialog():
    form = flp.ScriptDialog('Cole - Sample Chops', 'Slicex legt Slice 1 auf C5. Anzahl Slices = so viele wie in Slicex.')
    form.AddInputKnobInt('Anzahl Slices', 8, 2, 32)
    form.AddInputCombo('Stil', STYLES, 1)
    form.AddInputCombo('Laenge', ['4 Takte', '8 Takte', '16 Takte'], 0)
    form.AddInputKnobInt('Variante (Seed)', 1, 1, 999)
    form.AddInputKnobInt('Start-Note (60 = C5)', 60, 0, 100)
    form.AddInputCheckbox('Alte Noten loeschen', True)
    return form


def build_chops(n_slices, style, bars, seed, P):
    rng = Rng(seed * 17 + style)
    s16 = P // 4
    out = []  # (slice_index, time, length)
    if style == 0:
        per = max(1, (16 * 4) // n_slices)  # 4 Takte decken alle Slices ab
        for b4 in range(0, bars, 4):
            for i in range(n_slices):
                t = b4 * 16 + i * per
                if t < (b4 + 4) * 16:
                    out.append((i, t * s16, per * s16))
    elif style in (1, 3, 4):
        phrase = []
        s = 0
        while s < 32:  # 2-Takt-Phrase
            length = rng.choice([2, 2, 4, 4, 1, 3, 6, 8])
            phrase.append((rng.randint(0, n_slices - 1), s, min(length, 32 - s)))
            s += length
        alt = [(rng.randint(0, n_slices - 1), s, l) for _, s, l in phrase]
        for b2 in range(0, bars, 2):
            use = alt if style == 3 and (b2 // 2) % 4 == 2 else phrase
            for idx, s, l in use:
                if style == 4:
                    idx = n_slices - 1 - idx
                out.append((idx, (b2 * 16 + s) * s16, l * s16))
    elif style == 2:
        for b in range(bars):
            s = 0
            while s < 16:
                idx = rng.randint(0, n_slices - 1)
                if rng.chance(0.4):
                    rep = rng.choice([2, 3, 4])
                    for k in range(rep):
                        if s < 16:
                            out.append((idx, (b * 16 + s) * s16, s16))
                            s += 1
                else:
                    l = rng.choice([2, 4])
                    out.append((idx, (b * 16 + s) * s16, min(l, 16 - s) * s16))
                    s += l
    else:
        for b in range(bars):
            for half in range(2):
                idx = rng.randint(0, n_slices - 1)
                out.append((idx, (b * 16 + half * 8) * s16, 8 * s16))
    return out


def apply(form):
    if form.GetInputValue('Alte Noten loeschen'):
        clear_score()
    start = form.GetInputValue('Start-Note (60 = C5)')
    bars = [4, 8, 16][form.GetInputValue('Laenge')]
    for idx, t, l in build_chops(form.GetInputValue('Anzahl Slices'), form.GetInputValue('Stil'), bars,
                                 form.GetInputValue('Variante (Seed)'), ppq()):
        add_note(start + idx, t, l, 0.85)
