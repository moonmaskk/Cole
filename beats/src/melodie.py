# TITLE: Cole - Melodie
# INFO: Erzeugt eine eingaengige Melodie passend zu den Cole-Akkorden (gleiche Tonart/Stimmung waehlen).


def createDialog():
    form = flp.ScriptDialog('Cole - Melodie', 'Gleiche Tonart + Stimmung wie bei den Akkorden. Variante drehen, bis es knallt.')
    add_common_inputs(form)
    form.AddInputCombo('Stil', ['Catchy (wiederholt sich)', 'Flowing (viele Noten)', 'Simpel (wenige Noten)', 'Bell / Pluck'], 0)
    form.AddInputKnob('Dichte', 0.55, 0.1, 1.0)
    form.AddInputKnobInt('Oktave', 5, 3, 7)
    form.AddInputCheckbox('Alte Noten loeschen', True)
    return form


def _bar_rhythm(rng, density, style):
    steps = []
    for s in range(16):
        strong = s % 4 == 0
        p = density * (0.95 if strong else (0.55 if s % 2 == 0 else 0.3))
        if style == 1:
            p += 0.15
        if style == 2:
            p *= 0.55
        if rng.chance(min(p, 0.97)):
            steps.append(s)
    if not steps:
        steps = [0]
    return steps


def build_melody(key, scale_name, prog_name, bars, seed, style, density, octave, P):
    rng = Rng(seed * 7 + 3)
    root = 12 * (octave + 1) + key
    roots = progression_roots(key, scale_name, prog_name, bars)
    motif_a = _bar_rhythm(rng, density, style)
    motif_b = _bar_rhythm(rng, density, style)
    contour = [rng.randint(-2, 2) for _ in range(16)]
    out = []
    last_deg = 4
    for b, (deg, scale) in enumerate(roots):
        # Form A A B A -> wiedererkennbar
        rhythm = motif_b if b % 4 == 2 else motif_a
        chord_degs = [deg, deg + 2, deg + 4]
        for i, s in enumerate(rhythm):
            nxt = rhythm[i + 1] if i + 1 < len(rhythm) else 16
            length = max(1, nxt - s) * P // 4
            if style == 3:
                length = min(length, P // 4)
            if s % 4 == 0:
                # starke Zaehlzeit: Akkordton nahe der letzten Note
                cand = [d + 7 * o for d in chord_degs for o in (-1, 0, 1)]
                target = min(cand, key=lambda d: abs(d - last_deg) + (0 if b % 4 != 2 else rng.random()))
            else:
                target = last_deg + (contour[s] if b % 4 != 2 else rng.randint(-2, 2))
            target = max(-3, min(10, target))
            last_deg = target
            vel = 0.85 if s % 4 == 0 else 0.68
            out.append((scale_note(root, scale, target), b * P * 4 + s * P // 4, length, vel))
    return out


def apply(form):
    key, scale_name, prog_name, bars, seed = common_values(form)
    if form.GetInputValue('Alte Noten loeschen'):
        clear_score()
    for p, t, l, v in build_melody(key, scale_name, prog_name, bars, seed, form.GetInputValue('Stil'),
                                   form.GetInputValue('Dichte'), form.GetInputValue('Oktave'), ppq()):
        add_note(p, t, l, v)
