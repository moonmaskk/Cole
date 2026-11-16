"""Tests fuer Cole Beats. Laufen ohne FL Studio (flpianoroll wird nachgebaut).

    python3 -m unittest discover -s beats/tests
"""
import os
import sys
import tempfile
import types
import unittest
import wave
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build  # noqa: E402
import cole_beats  # noqa: E402


class FakeNote:
    def __init__(self):
        self.number, self.time, self.length, self.velocity, self.slide = 60, 0, 0, 0.8, False


class FakeScore:
    PPQ = 96

    def __init__(self):
        self.notes = []

    @property
    def noteCount(self):
        return len(self.notes)

    def addNote(self, n):
        self.notes.append(n)

    def getNote(self, i):
        return self.notes[i]

    def deleteNote(self, i):
        del self.notes[i]


class FakeForm:
    def __init__(self, title, desc):
        self.values, self.combos = {}, {}

    def _add(self, name, value):
        assert name not in self.values, 'doppelter Name ' + name
        self.values[name] = value

    def AddInputKnob(self, name, default, lo, hi):
        assert lo <= default <= hi
        self._add(name, default)

    def AddInputKnobInt(self, name, default, lo, hi):
        assert lo <= default <= hi
        self._add(name, default)

    def AddInputCombo(self, name, options, default):
        assert 0 <= default < len(options)
        self.combos[name] = options
        self._add(name, default)

    def AddInputCheckbox(self, name, default):
        self._add(name, default)

    def GetInputValue(self, name):
        return self.values[name]


def load_script(name):
    flp = types.ModuleType('flpianoroll')
    flp.Note, flp.ScriptDialog, flp.score = FakeNote, FakeForm, FakeScore()
    sys.modules['flpianoroll'] = flp
    _, text = build.build_one(name)
    ns = {'__name__': 'cole_' + name}
    exec(compile(text, name, 'exec'), ns)
    return ns, flp


def run_script(name, **values):
    ns, flp = load_script(name)
    form = ns['createDialog']()
    form.values.update(values)
    ns['apply'](form)
    return flp.score.notes, form


class PianoRollScripts(unittest.TestCase):
    def check_notes(self, notes, bars=4):
        self.assertTrue(notes)
        end = bars * 4 * FakeScore.PPQ
        for n in notes:
            self.assertTrue(0 <= n.number <= 127)
            self.assertGreater(n.length, 0)
            self.assertTrue(0 <= n.time < end + FakeScore.PPQ, n.time)
            self.assertTrue(0 < n.velocity <= 1)

    def test_all_scripts_all_options(self):
        for name in build.SCRIPTS:
            if name == 'humanize.py':
                continue
            ns, _ = load_script(name)
            combos = ns['createDialog']().combos
            for cname, opts in combos.items():
                for i in range(len(opts)):
                    for seed in (1, 77):
                        notes, form = run_script(name, **{cname: i, 'Variante (Seed)': seed})
                        bars = [4, 8, 16][form.values['Laenge']]
                        self.check_notes(notes, bars)

    def test_same_seed_same_result(self):
        a, _ = run_script('melodie.py', **{'Variante (Seed)': 5})
        b, _ = run_script('melodie.py', **{'Variante (Seed)': 5})
        c, _ = run_script('melodie.py', **{'Variante (Seed)': 6})
        sig = lambda ns: [(n.number, n.time, n.length) for n in ns]
        self.assertEqual(sig(a), sig(b))
        self.assertNotEqual(sig(a), sig(c))

    def test_melody_stays_in_key(self):
        for key in range(12):
            notes, _ = run_script('melodie.py', Tonart=key, Skala=0)
            allowed = {(key + s) % 12 for s in [0, 2, 3, 5, 7, 8, 10]}
            self.assertTrue(all(n.number % 12 in allowed for n in notes))

    def test_808_and_chords_share_roots(self):
        chords, _ = run_script('akkorde.py', Tonart=2)
        bass, _ = run_script('bass808.py', Tonart=2, Slides=0.0)
        P = FakeScore.PPQ
        for bar in range(4):
            c_low = min(n.number for n in chords if n.time == bar * 4 * P)
            b_first = [n.number for n in bass if n.time == bar * 4 * P][0]
            # Grundton des Akkords = Grundton der 808 (als Tonklasse)
            chord_pcs = {n.number % 12 for n in chords if n.time == bar * 4 * P}
            self.assertIn(b_first % 12, chord_pcs)

    def test_drums_single_channel_mode(self):
        notes, _ = run_script('drums.py', Ausgabe=1)
        self.assertTrue(all(n.number == 60 for n in notes))
        full, _ = run_script('drums.py', Ausgabe=0)
        self.assertIn(36, {n.number for n in full})
        self.assertIn(42, {n.number for n in full})

    def test_keep_existing_notes(self):
        ns, flp = load_script('akkorde.py')
        old = FakeNote()
        flp.score.addNote(old)
        form = ns['createDialog']()
        form.values['Alte Noten loeschen'] = False
        ns['apply'](form)
        self.assertIn(old, flp.score.notes)

    def test_humanize(self):
        ns, flp = load_script('humanize.py')
        for i in range(16):
            n = FakeNote()
            n.time, n.length, n.velocity = i * 24, 24, 0.8
            flp.score.addNote(n)
        ns['apply'](ns['createDialog']())
        self.assertTrue(any(n.time != i * 24 for i, n in enumerate(flp.score.notes)))
        self.assertTrue(all(abs(n.time - i * 24) <= 3 and n.time >= 0 for i, n in enumerate(flp.score.notes)))

    def test_slicex_notes_in_range(self):
        notes, _ = run_script('sample_chops.py', **{'Anzahl Slices': 6})
        self.assertTrue(all(60 <= n.number < 66 for n in notes))


class PackTool(unittest.TestCase):
    def test_classify(self):
        c = cole_beats.classify
        self.assertEqual(c('Pack/Kick 01 Hard.wav')[0], 'Drums/Kicks')
        self.assertEqual(c('Pack/808_Mafia_Glide (C).wav')[0], 'Drums/808s')
        self.assertEqual(c('Pack/OpenHat_3.wav')[0], 'Drums/Open Hats')
        self.assertEqual(c('Pack/hihat 2.wav')[0], 'Drums/Hi-Hats')
        self.assertEqual(c('Pack/Snares/Crack.wav')[0], 'Drums/Snares')
        self.assertEqual(c('Pack/Kick 120.wav')[0], 'Drums/Kicks')
        self.assertEqual(c('Pack/Dark Piano Loop 140bpm F#min.wav'), ('Loops/Melodien', 140, 'F#m'))
        self.assertEqual(c('Pack/drum loop 90 BPM.wav')[:2], ('Loops/Drums', 90))
        self.assertEqual(c('Pack/vox chop Am.wav')[0], 'Vocals')
        self.assertEqual(c('Pack/riser.wav')[0], 'FX')
        self.assertEqual(c('Pack/melody.mid')[0], 'MIDI')
        self.assertEqual(c('Pack/Bell Lead.fxp')[0], 'Presets/Serum & VST (fxp)')
        self.assertIsNone(c('Pack/readme.txt')[0])
        self.assertEqual(c('Pack/strings.wav', dur=8.0)[0], 'Loops/Melodien')

    def test_keys(self):
        k = lambda s: cole_beats.find_key(cole_beats.tokens(s))
        self.assertEqual(k('loop Ebm 140'), 'D#m')
        self.assertEqual(k('loop C minor'), 'Cm')
        self.assertEqual(k('loop Gmaj'), 'G')
        self.assertIsNone(k('a loop for you'))

    def test_sort_zip_and_search(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, 'src')
            os.makedirs(src)
            names = ['Kick Boom.wav', 'Clap Dry.wav', 'Sad Guitar Loop 130bpm Am.wav', 'hat roll.wav', 'Lead.fxp']
            for n in names:
                p = os.path.join(src, n)
                with wave.open(p, 'wb') as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(8000)
                    w.writeframes(b'\0\0' * 800)
            z = os.path.join(d, 'Mein Pack.zip')
            with zipfile.ZipFile(z, 'w') as zf:
                for n in names:
                    zf.write(os.path.join(src, n), 'Mein Pack/' + n)
                zf.writestr('__MACOSX/._junk.wav', 'x')
                zf.writestr('../boese.wav', 'x')
            lib = os.path.join(d, 'lib')
            cole_beats.main(['sortieren', z, '--ziel', lib])
            self.assertTrue(os.path.exists(os.path.join(lib, 'Drums', 'Kicks', 'Kick Boom.wav')))
            self.assertTrue(os.path.exists(os.path.join(lib, 'Loops', 'Melodien', '[130 Am] Sad Guitar Loop 130bpm Am.wav')))
            self.assertFalse(os.path.exists(os.path.join(d, 'boese.wav')))
            idx = cole_beats.load_index(lib)
            self.assertEqual(len(idx), 5)
            cole_beats.main(['sortieren', z, '--ziel', lib])  # zweimal = keine Duplikate
            self.assertEqual(len(cole_beats.load_index(lib)), 5)
            res = cole_beats.search(idx, ['guitar'], key='Am')
            self.assertEqual(len(res), 1)
            self.assertEqual(cole_beats.search(idx, ['kick'])[0]['kat'], 'Drums/Kicks')

    def test_scale_for(self):
        self.assertEqual(cole_beats.scale_for('Am')[2], ['A', 'B', 'C', 'D', 'E', 'F', 'G'])
        self.assertEqual(cole_beats.scale_for('Eb')[2][0], 'D#')


if __name__ == '__main__':
    unittest.main()
