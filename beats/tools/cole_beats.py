"""Cole Beats - Packs sortieren, Sounds finden, Tonart-Helfer. Nur Python-Standardbibliothek.

    python cole_beats.py sortieren <ZIP oder Ordner> [...] [--ziel ORDNER]
    python cole_beats.py suche dark 808 [--bpm 140] [--key Am] [--kat Kicks]
    python cole_beats.py tonart F#m
    python cole_beats.py statistik

Die Bibliothek (Standard: Dokumente/Cole Library) einmal in FL Studio eintragen:
Options > File settings > Browser extra search folders. Danach liegt alles sortiert im Browser.
Es wird nur kopiert, nie verschoben oder geloescht.
"""
import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import wave
import zipfile

AUDIO = {'.wav', '.mp3', '.aif', '.aiff', '.flac', '.ogg'}
PRESET = {'.fxp': 'Serum & VST (fxp)', '.fst': 'FL Studio', '.vital': 'Vital', '.nmsv': 'Massive',
          '.h2p': 'u-he', '.serumpreset': 'Serum 2', '.adg': 'Ableton', '.sbf': 'Serum Banks', '.fxb': 'VST Banks'}
MIDI = {'.mid', '.midi'}
INDEX = 'cole_index.json'

# Reihenfolge = Prioritaet. (Ordner, Stichwoerter als einzelne Woerter)
DRUM_CATS = [
    ('Drums/808s', {'808', '808s', 'sub', 'subbass'}),
    ('Drums/Kicks', {'kick', 'kicks', 'kik', 'bd', 'bassdrum'}),
    ('Drums/Open Hats', {'openhat', 'ohat', 'oh', 'open', 'ohh'}),
    ('Drums/Hi-Hats', {'hat', 'hats', 'hh', 'hihat', 'hihats', 'chh', 'closedhat', 'ch'}),
    ('Drums/Claps', {'clap', 'claps', 'clp'}),
    ('Drums/Snares', {'snare', 'snares', 'snr', 'sd'}),
    ('Drums/Rims', {'rim', 'rims', 'rimshot', 'stick'}),
    ('Drums/Percs', {'perc', 'percs', 'percussion', 'conga', 'bongo', 'shaker', 'tamb', 'tambourine',
                     'cowbell', 'tom', 'toms', 'block', 'triangle', 'clave', 'snap', 'snaps'}),
    ('Drums/Crashes', {'crash', 'cymbal', 'ride', 'china', 'splash'}),
    ('FX', {'fx', 'sfx', 'riser', 'sweep', 'impact', 'transition', 'noise', 'downlifter', 'uplifter',
            'reverse', 'rev', 'whoosh', 'texture', 'foley', 'vinyl', 'tag'}),
    ('Vocals', {'vox', 'vocal', 'vocals', 'voice', 'chant', 'adlib', 'adlibs', 'phrase', 'acapella', 'hook'}),
]
LOOP_CATS = [
    ('Loops/Drums', {'drum', 'drums', 'beat', 'top', 'tops', 'break', 'breaks', 'groove', 'hat', 'hats', 'perc'}),
    ('Loops/Bass', {'bass', '808', 'sub'}),
    ('Loops/Vocals', {'vox', 'vocal', 'vocals', 'voice', 'chant', 'acapella', 'hook'}),
    ('Loops/Melodien', set()),  # Rest
]
LOOP_WORDS = {'loop', 'loops', 'lp', 'melody', 'melodies', 'stem', 'stems', 'sample', 'chord', 'chords'}
NOTES = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
FLAT = {'db': 'c#', 'eb': 'd#', 'gb': 'f#', 'ab': 'g#', 'bb': 'a#'}


def tokens(name):
    base = os.path.splitext(os.path.basename(name))[0]
    base = re.sub(r'([a-z])([A-Z])', r'\1 \2', base)
    raw = [t for t in re.split(r'[^0-9A-Za-z#]+', base.lower()) if t]
    out = []
    for t in raw:
        out.append(t)
        m = re.match(r'^([a-z]+)(\d+)$', t)  # "kick01" -> "kick"
        if m:
            out.append(m.group(1))
    joined = ' '.join(raw)
    for a, b in (('open hat', 'openhat'), ('hi hat', 'hihat'), ('closed hat', 'closedhat'), ('one shot', 'oneshot')):
        if a in joined:
            out.append(b)
    return out


def find_bpm(name, toks, loose=True):
    m = re.search(r'(\d{2,3})\s*-?\s*bpm', name.lower())
    if m and 50 <= int(m.group(1)) <= 220:
        return int(m.group(1))
    if loose:  # nackte Zahl nur bei Loops als BPM werten
        for t in toks:
            if t.isdigit() and 60 <= int(t) <= 200:
                return int(t)
    return None


def norm_key(note, quality):
    note = FLAT.get(note, note.replace('s', '#') if len(note) == 2 and note[1] == 's' else note)
    if note not in NOTES:
        return None
    minor = quality in ('m', 'min', 'minor', 'moll')
    return note.upper() + ('m' if minor else '')


def find_key(toks):
    for i, t in enumerate(toks):
        m = re.match(r'^([a-g](?:#|b|s)?)(m|min|minor|maj|major|moll|dur)?$', t)
        if not m:
            continue
        note, q = m.group(1), m.group(2)
        nxt = toks[i + 1] if i + 1 < len(toks) else ''
        if q is None and nxt in ('minor', 'min', 'major', 'maj', 'moll', 'dur', 'm'):
            q = nxt
        if q is None and not (i > 0 and toks[i - 1] == 'key'):
            continue  # einzelner Buchstabe ohne Hinweis = kein Key
        k = norm_key(note, q or 'maj')
        if k:
            return k
    return None


def duration(path):
    if not path.lower().endswith('.wav'):
        return None
    try:
        with wave.open(path, 'rb') as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return None


def classify(path, dur=None):
    """Gibt (Ordner, bpm, key) zurueck."""
    ext = os.path.splitext(path)[1].lower()
    toks = tokens(path)
    folder_toks = tokens(os.path.basename(os.path.dirname(path)))
    if ext in MIDI:
        return 'MIDI', find_bpm(path, toks), find_key(toks)
    if ext in PRESET:
        return 'Presets/' + PRESET[ext], None, None
    if ext not in AUDIO:
        return None, None, None
    bpm, key = find_bpm(os.path.basename(path), toks), find_key(toks)
    words = set(toks)
    is_oneshot = 'oneshot' in words or 'one' in words and 'shot' in words
    is_loop = not is_oneshot and (bool(words & LOOP_WORDS) or bool(set(folder_toks) & {'loop', 'loops', 'melodies'})
                                  or find_bpm(os.path.basename(path), toks, loose=False) is not None
                                  or (dur is not None and dur > 4.0))
    if not is_loop:
        bpm = find_bpm(os.path.basename(path), toks, loose=False)
    if is_loop:
        for cat, kw in LOOP_CATS:
            if not kw or words & kw:
                return cat, bpm, key
    for cat, kw in DRUM_CATS:
        if words & kw:
            return cat, bpm, key
    for cat, kw in DRUM_CATS:  # Ordnername als Hinweis ("Snares/xyz.wav")
        if set(folder_toks) & kw:
            return cat, bpm, key
    return 'Sonstiges', bpm, key


def nice_name(path, cat, bpm, key):
    base = os.path.basename(path)
    if cat.startswith('Loops') or cat == 'MIDI':
        tag = ' '.join(x for x in (str(bpm) if bpm else '', key or '') if x)
        if tag and not base.startswith('['):
            return '[%s] %s' % (tag, base)
    return base


def iter_files(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x != '__MACOSX' and not x.startswith('.')]
        for f in files:
            if not f.startswith('._') and not f.startswith('.'):
                yield os.path.join(d, f)


def load_index(lib):
    p = os.path.join(lib, INDEX)
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    return []


def save_index(lib, idx):
    with open(os.path.join(lib, INDEX), 'w', encoding='utf-8') as f:
        json.dump(idx, f, ensure_ascii=False, indent=0)


def sort_source(src, lib, idx, known):
    tmp = None
    pack = os.path.splitext(os.path.basename(src.rstrip('/\\')))[0]
    try:
        if zipfile.is_zipfile(src):
            tmp = tempfile.mkdtemp(prefix='cole_')
            with zipfile.ZipFile(src) as z:
                for m in z.infolist():
                    target = os.path.realpath(os.path.join(tmp, m.filename))
                    if target.startswith(os.path.realpath(tmp) + os.sep):  # Schutz vor ../-Pfaden
                        z.extract(m, tmp)
            root = tmp
        elif os.path.isdir(src):
            root = src
        else:
            root = None
            files = [src]
        files = list(iter_files(root)) if root else files
        count = 0
        for f in files:
            cat, bpm, key = classify(f, duration(f))
            if not cat:
                continue
            dest_dir = os.path.join(lib, *cat.split('/'))
            os.makedirs(dest_dir, exist_ok=True)
            name = nice_name(f, cat, bpm, key)
            dest = os.path.join(dest_dir, name)
            if os.path.exists(dest):
                if os.path.getsize(dest) == os.path.getsize(f):
                    continue  # schon da
                stem, ext = os.path.splitext(name)
                dest = os.path.join(dest_dir, '%s (%s)%s' % (stem, pack, ext))
                if os.path.exists(dest):
                    continue
            shutil.copy2(f, dest)
            rel = os.path.relpath(dest, lib)
            if rel not in known:
                idx.append({'pfad': rel, 'kat': cat, 'bpm': bpm, 'key': key, 'pack': pack,
                            'woerter': sorted(set(tokens(f) + tokens(pack)))})
                known.add(rel)
            count += 1
        return count
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


def default_lib():
    home = os.path.expanduser('~')
    for d in ('Documents', 'Dokumente'):
        if os.path.isdir(os.path.join(home, d)):
            return os.path.join(home, d, 'Cole Library')
    return os.path.join(home, 'Cole Library')


def cmd_sort(a):
    lib = a.ziel or default_lib()
    os.makedirs(lib, exist_ok=True)
    idx = load_index(lib)
    known = {e['pfad'] for e in idx}
    total = 0
    for src in a.quellen:
        if not os.path.exists(src):
            print('nicht gefunden:', src)
            continue
        n = sort_source(src, lib, idx, known)
        total += n
        print('%4d Dateien  <- %s' % (n, os.path.basename(src)))
    save_index(lib, idx)
    print('\nFertig: %d neue Dateien in %s' % (total, lib))
    cats = {}
    for e in idx:
        cats[e['kat']] = cats.get(e['kat'], 0) + 1
    for c in sorted(cats):
        print('  %-28s %d' % (c, cats[c]))


def search(idx, words, bpm=None, key=None, kat=None, limit=30):
    words = [w.lower() for w in words]
    hits = []
    for e in idx:
        if kat and kat.lower() not in e['kat'].lower():
            continue
        if bpm and (not e.get('bpm') or abs(e['bpm'] - bpm) > 3):
            continue
        if key and (e.get('key') or '').lower() != key.lower():
            continue
        hay = ' '.join(e['woerter']) + ' ' + e['kat'].lower() + ' ' + e['pfad'].lower()
        score = sum(2 if w in e['woerter'] else (1 if w in hay else 0) for w in words)
        if words and score == 0:
            continue
        hits.append((score, e))
    hits.sort(key=lambda x: (-x[0], x[1]['pfad']))
    return [e for _, e in hits[:limit]]


def cmd_search(a):
    lib = a.ziel or default_lib()
    idx = load_index(lib)
    if not idx:
        print('Noch keine Bibliothek. Erst: python cole_beats.py sortieren <Pack>')
        return
    res = search(idx, a.woerter, a.bpm, a.key, a.kat)
    for e in res:
        info = ' '.join(x for x in (str(e['bpm']) + ' BPM' if e.get('bpm') else '', e.get('key') or '') if x)
        print('%-60s %s' % (e['pfad'], info))
    print('\n%d Treffer (Bibliothek: %s)' % (len(res), lib))


def scale_for(keyname):
    m = re.match(r'^([A-Ga-g])(#|b)?(m|min|moll)?$', keyname.strip())
    if not m:
        return None
    note = (m.group(1) + (m.group(2) or '')).lower()
    note = FLAT.get(note, note)
    root = NOTES.index(note)
    minor = bool(m.group(3))
    steps = [0, 2, 3, 5, 7, 8, 10] if minor else [0, 2, 4, 5, 7, 9, 11]
    return root, minor, [NOTES[(root + s) % 12].upper() for s in steps]


def cmd_key(a):
    r = scale_for(a.tonart)
    if not r:
        print('Beispiel: tonart Am   tonart F#m   tonart C')
        return
    root, minor, notes = r
    rel = NOTES[(root + (3 if minor else -3)) % 12].upper() + ('' if minor else 'm')
    print('Tonart:      %s %s' % (notes[0], 'Moll' if minor else 'Dur'))
    print('Toene:       %s' % '  '.join(notes))
    print('Gleiche Toene wie: %s (Paralleltonart)' % rel)
    print('\nAutotune / Pitcher / NewTone:')
    print('  Key = %s, Scale = %s' % (notes[0], 'Minor' if minor else 'Major'))
    print('  In den Cole-Skripten: Tonart = %s, Skala = %s' % (notes[0], 'Moll' if minor else 'Dur'))


def cmd_stats(a):
    lib = a.ziel or default_lib()
    idx = load_index(lib)
    cats, packs = {}, set()
    for e in idx:
        cats[e['kat']] = cats.get(e['kat'], 0) + 1
        packs.add(e['pack'])
    print('%s: %d Dateien aus %d Packs' % (lib, len(idx), len(packs)))
    for c in sorted(cats):
        print('  %-28s %d' % (c, cats[c]))


def main(argv=None):
    p = argparse.ArgumentParser(prog='cole_beats', description='Cole Beats Helfer fuer FL Studio')
    sub = p.add_subparsers(dest='cmd')
    s = sub.add_parser('sortieren', help='Packs (ZIP/Ordner) sortiert in die Bibliothek kopieren')
    s.add_argument('quellen', nargs='+')
    s.add_argument('--ziel')
    s.set_defaults(fn=cmd_sort)
    s = sub.add_parser('suche', help='Sounds finden')
    s.add_argument('woerter', nargs='*')
    s.add_argument('--bpm', type=int)
    s.add_argument('--key')
    s.add_argument('--kat')
    s.add_argument('--ziel')
    s.set_defaults(fn=cmd_search)
    s = sub.add_parser('tonart', help='Toene einer Tonart (fuer Autotune & Skripte)')
    s.add_argument('tonart')
    s.set_defaults(fn=cmd_key)
    s = sub.add_parser('statistik', help='Was ist in der Bibliothek?')
    s.add_argument('--ziel')
    s.set_defaults(fn=cmd_stats)
    a = p.parse_args(argv)
    if not getattr(a, 'fn', None):
        p.print_help()
        return 0
    a.fn(a)
    return 0


if __name__ == '__main__':
    sys.exit(main())
