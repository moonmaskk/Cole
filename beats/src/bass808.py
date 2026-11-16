# TITLE: Cole - 808
# INFO: 808-Bassline auf den Grundtoenen der Cole-Akkorde, mit Slides. Gleiche Tonart/Stimmung waehlen.


def createDialog():
    form = flp.ScriptDialog('Cole - 808', '808 folgt den Akkorden. Slides = Gleiten (im 808-Sampler Porta/Slide an).')
    add_common_inputs(form)
    form.AddInputCombo('Muster', ['Trap (bounce)', 'Drill (gleitend)', 'Simpel (1 pro Takt)', 'Boom Bap', 'Afro / Dancehall'], 0)
    form.AddInputKnob('Slides', 0.35, 0.0, 1.0)
    form.AddInputKnobInt('Oktave', 2, 1, 3)
    form.AddInputCheckbox('Alte Noten loeschen', True)
    return form


PATTERNS_808 = {
    0: [[0, 6, 10], [0, 3, 10, 14], [0, 7, 11], [0, 6, 8, 14]],
    1: [[0, 5, 10], [0, 3, 6, 12], [0, 10, 13]],
    2: [[0]],
    3: [[0, 7, 10], [0, 10], [0, 3, 10]],
    4: [[0, 3, 8, 11], [0, 6, 8, 12]],
}


def build_808(key, scale_name, prog_name, bars, seed, pattern, slides, octave, P):
    rng = Rng(seed * 13 + 5)
    root = root_note(octave, key)
    out = []
    choices = PATTERNS_808[pattern]
    bar_pat = [rng.choice(choices) for _ in range(4)]
    for b, (deg, scale) in enumerate(progression_roots(key, scale_name, prog_name, bars)):
        base = scale_note(root, scale, deg % 7)
        steps = bar_pat[b % 4]
        for i, s in enumerate(steps):
            nxt = steps[i + 1] if i + 1 < len(steps) else 16
            t = b * P * 4 + s * P // 4
            length = (nxt - s) * P // 4
            pitch = base
            if i > 0 and rng.chance(0.25):
                pitch = base + rng.choice([12, 7, -5 if base - 5 > 20 else 7])
            out.append((pitch, t, length, 0.9 if s == 0 else 0.8, False))
            if slides > 0 and i == len(steps) - 1 and rng.chance(slides):
                # Slide-Note am Ende: gleitet zur Oktave / Quinte
                tgt = pitch + rng.choice([12, 7, -12 if pitch - 12 > 20 else 12])
                out.append((tgt, t + length // 2, length // 2, 0.8, True))
    return out


def apply(form):
    key, scale_name, prog_name, bars, seed = common_values(form)
    if form.GetInputValue('Alte Noten loeschen'):
        clear_score()
    for p, t, l, v, sl in build_808(key, scale_name, prog_name, bars, seed, form.GetInputValue('Muster'),
                                    form.GetInputValue('Slides'), form.GetInputValue('Oktave'), ppq()):
        add_note(p, t, l, v, sl)
