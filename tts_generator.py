import hashlib
from gtts import gTTS
from typing import List
from pathlib import Path


class TTSGenerator:
    VOICES = {
        "default": "com",
        "us_male": "com",
        "us_female": "com",
        "uk_male": "co.uk",
        "uk_female": "co.uk",
    }

    def __init__(self, output_dir: str = "temp_audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_audio(
        self, text: str, voice: str = "default", speed: float = 1.0
    ) -> str:
        tld = self.VOICES.get(voice, "com")

        tts = gTTS(text=text, lang="en", tld=tld, slow=(speed < 0.8))

        digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
        output_file = self.output_dir / f"audio_{digest}.mp3"
        tts.save(str(output_file))

        return str(output_file)

    def generate_batch(
        self, texts: List[str], voice: str = "default", speed: float = 1.0
    ) -> List[str]:
        audio_files = []
        for i, text in enumerate(texts):
            if text.strip():
                tld = self.VOICES.get(voice, "com")

                tts = gTTS(text=text, lang="en", tld=tld, slow=(speed < 0.8))

                digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
                output_file = self.output_dir / f"audio_{i}_{digest}.mp3"
                tts.save(str(output_file))
                audio_files.append(str(output_file))

        return audio_files

    def cleanup(self):
        for f in self.output_dir.glob("*.mp3"):
            f.unlink()
