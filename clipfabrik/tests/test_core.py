import os
import random
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault("CLIPFABRIK_DATA", tempfile.mkdtemp(prefix="cf-test-"))

from clipfabrik import config, media  # noqa: E402
from clipfabrik.chat import parse  # noqa: E402
from clipfabrik.detect import Detector  # noqa: E402


class DetectTest(unittest.TestCase):
    def setUp(self):
        self.cfg = config.load()
        random.seed(1)

    def _calm(self, det, t0, seconds=330):
        for s in range(seconds):
            for _ in range(random.randint(0, 2)):
                det.feed("x", t0 + s + random.random(), f"u{random.randint(1, 30)}", "hallo")

    def test_spike_triggers(self):
        det = Detector(self.cfg)
        t0 = 1_000_000.0
        self._calm(det, t0)
        peak = t0 + 335
        for i in range(40):
            det.feed("x", peak - random.random() * 9, f"fan{i}", "KEKW 💀")
        trig = det.check("x", peak)
        self.assertIsNotNone(trig)
        self.assertGreaterEqual(trig.score, 6)
        self.assertIsNone(det.check("x", peak + 5), "Abklingzeit muss greifen")

    def test_calm_chat_no_trigger(self):
        det = Detector(self.cfg)
        t0 = 2_000_000.0
        self._calm(det, t0)
        self.assertIsNone(det.check("x", t0 + 330))

    def test_single_spammer_no_trigger(self):
        det = Detector(self.cfg)
        t0 = 3_000_000.0
        self._calm(det, t0)
        peak = t0 + 335
        for _ in range(60):
            det.feed("x", peak - random.random() * 9, "spammer", "aaaa")
        self.assertIsNone(det.check("x", peak))

    def test_clip_calls_trigger(self):
        det = Detector(self.cfg)
        now = 4_000_000.0
        for i in range(3):
            det.feed("x", now - i, f"u{i}", "clip it!!")
        self.assertIsNotNone(det.check("x", now))


class ChatParseTest(unittest.TestCase):
    def test_privmsg(self):
        line = "@badge=1;color=#FF0000 :alice!alice@alice.tmi.twitch.tv PRIVMSG #papaplatte :KEKW clip das"
        self.assertEqual(parse(line), ("papaplatte", "alice", "KEKW clip das"))

    def test_other(self):
        self.assertIsNone(parse(":tmi.twitch.tv 001 justinfan1 :Welcome"))


class SettingsTest(unittest.TestCase):
    def test_normalize(self):
        out = config.normalize_streamers(["https://twitch.tv/XQC", {"login": "xqc"}, " @Trymacs "])
        self.assertEqual([s["login"] for s in out], ["xqc", "trymacs"])


class AssTest(unittest.TestCase):
    def test_highlight_and_source(self):
        ass = media.build_ass([(0.0, 0.4, "no"), (0.4, 0.8, "way"), (0.8, 1.2, "bro")], 5.0,
                              "twitch.tv/x", "Hook 💀")
        self.assertIn("Quelle: twitch.tv/x", ass)
        self.assertIn("{\\c&H00E5FF&}NO{\\c&HFFFFFF&} WAY BRO", ass)
        self.assertNotIn("💀", ass)


class PipelineDemoTest(unittest.TestCase):
    """Ganze Kette ohne Twitch: Testvideo -> Ausschlag -> Schnitt -> Bewertung -> 9:16-Clip."""

    def test_demo_end_to_end(self):
        from clipfabrik import db
        from clipfabrik.pipeline import Pipeline
        p = Pipeline()
        cid = p.demo()
        self.assertIsNotNone(cid)
        p._cut_one(); p._judge_one(); p._render_one()
        clip = db.get(cid)
        self.assertEqual(clip["status"], "RENDERED", clip["error"])
        self.assertTrue(Path(clip["out_path"]).stat().st_size > 100_000)


if __name__ == "__main__":
    unittest.main()
