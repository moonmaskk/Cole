# TITLE: Cole - Drums
# INFO: Kompletter Drum-Beat nach Genre (Kick, Snare/Clap, Hi-Hats mit Rolls, Open Hat, Perc).


GENRES = ['Trap', 'Drill', 'Boom Bap', 'Afrobeats', 'Reggaeton / Dembow', 'House', 'Rage', 'Lo-Fi']
GENRE_BPM = {'Trap': 140, 'Drill': 142, 'Boom Bap': 90, 'Afrobeats': 105, 'Reggaeton / Dembow': 95,
             'House': 124, 'Rage': 160, 'Lo-Fi': 80}

# 16 Schritte pro Takt. x = Schlag. Mehrere Varianten pro Genre.
KICKS = {
    'Trap': ['x.........x.....', 'x......x..x.....', 'x.........x..x..', 'x..x......x.....'],
    'Drill': ['x.....x.......x.', 'x......x...x....', 'x.....x...x...x.'],
    'Boom Bap': ['x.......x.x.....', 'x......xx.......', 'x.x.......x.....'],
    'Afrobeats': ['x.....x.x.......', 'x..x..x...x.....', 'x.....x...x..x..'],
    'Reggaeton / Dembow': ['x...x...x...x...'],
    'House': ['x...x...x...x...'],
    'Rage': ['x.......x.x.....', 'x..x....x.......', 'x.....x.x..x....'],
    'Lo-Fi': ['x.......x.......', 'x......x..x.....', 'x.x.......x.....'],
}
SNARES = {
    'Trap': ['........x.......'],
    'Drill': ['........x.......'],
    'Boom Bap': ['....x.......x...'],
    'Afrobeats': ['....x..x....x...', '...x..x...x.x...'],
    'Reggaeton / Dembow': ['...x..x....x..x.'],
    'House': ['....x.......x...'],
    'Rage': ['....x.......x...', '........x.......'],
    'Lo-Fi': ['....x.......x...'],
}
PERCS = {
    'Afrobeats': ['..x..x....x..x..', 'x..x..x...x.x...'],
    'Reggaeton / Dembow': ['..x...x...x...x.'],
    'House': ['..x...x...x...x.'],
    'Drill': ['......x.....x...', '...........x....'],
    'Trap': ['.......x.....x..', '...x.......x....'],
    'Boom Bap': ['..x.......x..x..', '......x.......x.'],
    'Rage': ['...x...x...x...x'],
    'Lo-Fi': ['......x.......x.', '..x.......x.....'],
}
OUTPUTS = ['Alles (FPC / Drumkit)', 'Nur Kick', 'Nur Snare/Clap', 'Nur Hi-Hats', 'Nur Open Hat', 'Nur Perc']
# General-MIDI-Noten (FPC-Standard). FL nennt MIDI 36 "C3".
GM = {'kick': 36, 'snare': 38, 'clap': 39, 'hat': 42, 'open': 46, 'perc': 37}


def createDialog():
    form = flp.ScriptDialog('Cole - Drums', 'Genre waehlen, Variante drehen. "Nur ..." = fuer Kanaele mit einem Sound (Note C5).')
    form.AddInputCombo('Genre', GENRES, 0)
    form.AddInputCombo('Ausgabe', OUTPUTS, 0)
    form.AddInputCombo('Laenge', ['4 Takte', '8 Takte', '16 Takte'], 0)
    form.AddInputKnobInt('Variante (Seed)', 1, 1, 999)
    form.AddInputKnob('Hi-Hat Rolls', 0.5, 0.0, 1.0)
    form.AddInputKnob('Swing', 0.0, 0.0, 1.0)
    form.AddInputCheckbox('Clap auf Snare legen', True)
    form.AddInputCheckbox('Alte Noten loeschen', True)
    return form


def _hits(pattern):
    return [i for i, c in enumerate(pattern) if c == 'x']


def _hats(genre, rng, rolls, P, bar_t, last_bar):
    """Hi-Hats in Ticks. Trap/Drill/Rage bekommen Rolls & Triolen."""
    s16 = P // 4
    out = []
    if genre in ('House', 'Reggaeton / Dembow'):
        for s in range(16):
            if s % 2 == 0:
                out.append((bar_t + s * s16, 0.7 if s % 4 else 0.85))
        return out
    if genre in ('Boom Bap', 'Lo-Fi', 'Afrobeats'):
        for s in range(0, 16, 2):
            out.append((bar_t + s * s16, 0.8 if s % 4 == 0 else 0.6))
        if genre == 'Afrobeats':
            out += [(bar_t + s * s16, 0.5) for s in (3, 11) if rng.chance(0.6)]
        return out
    base = 1 if genre == 'Drill' and rng.chance(0.5) else 2
    if genre == 'Drill':
        # Drill: Triolen-Hats
        step = P // 3
        for i in range(12):
            out.append((bar_t + i * step, 0.8 if i % 3 == 0 else 0.6))
    else:
        s = 0
        while s < 16:
            out.append((bar_t + s * s16, 0.85 if s % 4 == 0 else 0.65))
            s += base if base == 1 or not rng.chance(0.15) else 1
    # Rolls: ersetzt einen Viertel-Schlag durch schnelle Noten
    n_rolls = int(rolls * 3 + (1 if last_bar else 0))
    for _ in range(n_rolls):
        beat = rng.choice([1, 2, 3]) if not last_bar else 3
        start = bar_t + beat * P + rng.choice([0, P // 2])
        end = start + P // 2
        out = [h for h in out if not (start <= h[0] < end)]
        div = rng.choice([6, 8, 12]) if rolls > 0.3 else 8
        step = P // div * 2 if div == 6 else P // div
        n = max(2, (end - start) // step)
        for k in range(n):
            out.append((start + k * step, 0.45 + 0.45 * k / n))
    return out


def build_drums(genre_i, bars, seed, rolls, swing, clap, P):
    genre = GENRES[genre_i]
    rng = Rng(seed * 31 + genre_i)
    s16 = P // 4
    kick_a, kick_b = rng.choice(KICKS[genre]), rng.choice(KICKS[genre])
    snare = rng.choice(SNARES[genre])
    perc = rng.choice(PERCS[genre])
    out = []  # (rolle, time, length, velocity)

    def sw(step, t):
        return t + (int(swing * s16 * 0.5) if step % 2 == 1 else 0)

    for b in range(bars):
        bt = b * P * 4
        last = b % 4 == 3
        kp = kick_b if b % 2 else kick_a
        for s in _hits(kp):
            out.append(('kick', sw(s, bt + s * s16), s16, 0.95))
        if last and genre in ('Trap', 'Rage', 'Drill') and rng.chance(0.5):
            out.append(('kick', bt + 15 * s16, s16, 0.8))
        for s in _hits(snare):
            out.append(('snare', sw(s, bt + s * s16), s16, 0.9))
            if clap:
                out.append(('clap', sw(s, bt + s * s16), s16, 0.85))
        if last and rng.chance(0.4):
            out.append(('snare', bt + 14 * s16, s16, 0.6))
        for t, v in _hats(genre, rng, rolls, P, bt, last):
            step = (t - bt) // s16
            out.append(('hat', sw(step, t) if (t - bt) % s16 == 0 else t, max(s16 // 2, 1), v))
        if genre == 'House':
            open_steps = [2, 6, 10, 14]
        elif last or (b % 2 == 1 and rng.chance(0.5)):
            open_steps = [rng.choice([6, 14])]  # Open Hat als Uebergang am Phrasenende
        else:
            open_steps = []
        for s in open_steps:
            out.append(('open', bt + s * s16, s16 * 2, 0.7))
        if genre in ('Afrobeats', 'Reggaeton / Dembow', 'House', 'Drill') or b % 2 == 1:
            for s in _hits(perc):
                out.append(('perc', sw(s, bt + s * s16), s16, 0.7))
    return out


def apply(form):
    if form.GetInputValue('Alte Noten loeschen'):
        clear_score()
    output = form.GetInputValue('Ausgabe')
    only = {1: ('kick',), 2: ('snare', 'clap'), 3: ('hat',), 4: ('open',), 5: ('perc',)}.get(output)
    bars = [4, 8, 16][form.GetInputValue('Laenge')]
    hits = build_drums(form.GetInputValue('Genre'), bars, form.GetInputValue('Variante (Seed)'),
                       form.GetInputValue('Hi-Hat Rolls'), form.GetInputValue('Swing'),
                       form.GetInputValue('Clap auf Snare legen'), ppq())
    seen = set()
    for role, t, l, v in hits:
        if only is not None:
            if role not in only:
                continue
            pitch = 60
        else:
            pitch = GM[role]
        if (pitch, t) in seen:
            continue
        seen.add((pitch, t))
        add_note(pitch, t, l, v)
