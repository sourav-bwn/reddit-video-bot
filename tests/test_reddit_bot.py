"""Offline tests for the Reddit video bot.

No network, Reddit API, gTTS calls or video rendering: gTTS and the heavy
moviepy render path are stubbed where needed.
"""
import math
import os
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reddit_fetcher import RedditFetcher


class TestRedditFetcher(unittest.TestCase):
    def test_instantiates_without_arguments(self):
        # Regression: the constructor annotation was written where the default
        # value belonged, so RedditFetcher() raised TypeError and both the GUI
        # and the Flask server crashed at startup.
        fetcher = RedditFetcher()
        self.assertEqual(fetcher.session.headers["User-Agent"], "RedditVideoBot/1.0")

    def test_custom_user_agent_is_used(self):
        fetcher = RedditFetcher("custom-agent/2.0")
        self.assertEqual(fetcher.session.headers["User-Agent"], "custom-agent/2.0")

    def test_clean_text_strips_markup_and_entities(self):
        f = RedditFetcher()
        self.assertEqual(f._clean_text("Check [this](http://x.com) out"), "Check out")
        self.assertEqual(f._clean_text("a   b\n\nc"), "a b c")
        self.assertEqual(f._clean_text("**bold** _italics_"), "bold italics")
        self.assertEqual(f._clean_text("Tom &amp; Jerry &lt;3"), "Tom and Jerry <3")

    def test_non_reddit_urls_are_rejected_before_any_request(self):
        f = RedditFetcher()
        self.assertIsNone(f.get_post_from_url("https://example.com/not-reddit"))
        self.assertEqual(f.get_comments("https://example.com/not-reddit"), [])


class FakeGTTS:
    """Stands in for gtts.gTTS without network access."""

    calls = []

    def __init__(self, text, lang, tld, slow):
        self.text = text
        self.tld = tld
        self.slow = slow
        FakeGTTS.calls.append({"text": text, "lang": lang, "tld": tld, "slow": slow})

    def save(self, path):
        Path(path).write_bytes(b"fake mp3")


class TestTTSGenerator(unittest.TestCase):
    def setUp(self):
        import gtts

        self._real = gtts.gTTS
        gtts.gTTS = FakeGTTS
        import tts_generator

        tts_generator.gTTS = FakeGTTS
        self.mod = tts_generator
        FakeGTTS.calls = []
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import gtts

        gtts.gTTS = self._real

    def test_file_names_are_deterministic(self):
        gen = self.mod.TTSGenerator(output_dir=self.tmp)
        first = gen.generate_audio("hello world")
        second = gen.generate_audio("hello world")
        self.assertEqual(first, second)
        self.assertNotIn("-", Path(first).stem.replace("audio_", "", 1)[:1])

    def test_voice_map_selects_tld(self):
        gen = self.mod.TTSGenerator(output_dir=self.tmp)
        gen.generate_audio("hi", voice="uk_male")
        gen.generate_audio("hi", voice="default")
        self.assertEqual(FakeGTTS.calls[0]["tld"], "co.uk")
        self.assertEqual(FakeGTTS.calls[1]["tld"], "com")

    def test_batch_skips_empty_texts(self):
        gen = self.mod.TTSGenerator(output_dir=self.tmp)
        files = gen.generate_batch(["one", "   ", "two"])
        self.assertEqual(len(files), 2)
        self.assertTrue(all(Path(f).exists() for f in files))


class TestVideoNarration(unittest.TestCase):
    """Regression: narration audio was loaded but never attached to the video."""

    def _make_wav(self, path, seconds=0.5, rate=8000):
        frames = int(seconds * rate)
        with wave.open(str(path), "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            for i in range(frames):
                sample = int(8000 * math.sin(2 * math.pi * 220 * i / rate))
                w.writeframes(struct.pack("<h", sample))

    def test_create_video_attaches_narration_audio(self):
        import moviepy.editor as mp
        from video_generator import VideoGenerator

        tmp = Path(tempfile.mkdtemp())
        wav1, wav2 = tmp / "a.wav", tmp / "b.wav"
        self._make_wav(wav1, 0.5)
        self._make_wav(wav2, 0.5)

        captured = {}
        real_write = mp.CompositeVideoClip.write_videofile

        def fake_write(self_clip, *args, **kwargs):
            captured["final"] = self_clip

        gen = VideoGenerator(output_dir=str(tmp))
        # TextClip needs ImageMagick; a plain colour clip exercises the same
        # audio-assembly code path without it.
        with mock.patch.object(
            VideoGenerator, "_create_text_with_author",
            lambda self, text, author, dur: mp.ColorClip((100, 100), (0, 0, 0)).set_duration(dur),
        ), mock.patch.object(mp.CompositeVideoClip, "write_videofile", fake_write):
            out = gen.create_video(
                [str(wav1), str(wav2)], ["hello", "world"], ["a", "b"], "out.mp4"
            )

        final = captured.get("final")
        self.assertIsNotNone(final, "create_video should reach write_videofile")
        self.assertIsNotNone(final.audio, "narration track must be attached to the final video")
        self.assertAlmostEqual(final.audio.duration, 1.0, places=1)
        self.assertTrue(out.endswith("out.mp4"))


class TestDownloadRoute(unittest.TestCase):
    def test_traversal_is_rejected_and_real_file_served(self):
        import server

        output = Path("output")
        output.mkdir(exist_ok=True)
        (output / "demo.mp4").write_bytes(b"video")

        client = server.app.test_client()
        ok = client.get("/api/download/demo.mp4")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.data, b"video")

        for attempt in ("..%2F..%2Fetc%2Fpasswd", "..%2Fsecret.txt", "%2e%2e%2fapp.py"):
            resp = client.get(f"/api/download/{attempt}")
            self.assertIn(resp.status_code, (400, 404), attempt)
            self.assertNotIn(b"root:", resp.data)


if __name__ == "__main__":
    unittest.main()
