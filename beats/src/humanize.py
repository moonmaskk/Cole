# TITLE: Cole - Humanize
# INFO: Macht vorhandene Noten lebendiger (Timing + Lautstaerke leicht variieren). Wirkt auf alle Noten.


def createDialog():
    form = flp.ScriptDialog('Cole - Humanize', 'Kleine Abweichungen = klingt wie eingespielt statt Roboter.')
    form.AddInputKnob('Timing', 0.3, 0.0, 1.0)
    form.AddInputKnob('Lautstaerke', 0.4, 0.0, 1.0)
    form.AddInputKnobInt('Variante (Seed)', 1, 1, 999)
    return form


def humanize_values(time, velocity, rng, timing, vel_amt, P):
    max_shift = int(round(P / 12.0 * timing))
    nt = max(0, time + rng.randint(-max_shift, max_shift)) if max_shift else time
    nv = velocity * (1 + (rng.random() - 0.5) * 0.5 * vel_amt)
    return nt, max(0.05, min(1.0, nv))


def apply(form):
    rng = Rng(form.GetInputValue('Variante (Seed)'))
    timing = form.GetInputValue('Timing')
    vel_amt = form.GetInputValue('Lautstaerke')
    P = ppq()
    for i in range(flp.score.noteCount):
        n = flp.score.getNote(i)
        n.time, n.velocity = humanize_values(n.time, n.velocity, rng, timing, vel_amt, P)
