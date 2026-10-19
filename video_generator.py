import os
import textwrap
from typing import List, Optional
from pathlib import Path
import moviepy.editor as mp
from PIL import Image, ImageDraw, ImageFont
import numpy as np


class VideoGenerator:
    WIDTH = 1080
    HEIGHT = 1920

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def _create_text_overlay(
        self, text: str, duration: float, fontsize: int = 60
    ) -> "mp.TextClip":
        wrapped = textwrap.fill(text, width=40)

        txt = mp.TextClip(
            wrapped,
            fontsize=fontsize,
            color="white",
            font="Arial-Bold",
            method="caption",
            size=(self.WIDTH - 100, None),
            stroke_color="black",
            stroke_width=3,
        )

        return txt.set_duration(duration).set_position(("center", "center"))

    def _create_text_with_author(
        self, comment_text: str, author: str, duration: float
    ) -> "mp.CompositeVideoClip":
        wrapped = textwrap.fill(comment_text, width=35)

        comment_clip = mp.TextClip(
            wrapped,
            fontsize=55,
            color="white",
            font="Arial-Bold",
            method="caption",
            size=(self.WIDTH - 120, None),
            stroke_color="black",
            stroke_width=4,
        )

        author_clip = mp.TextClip(
            f"u/{author}",
            fontsize=40,
            color="#e94560",
            font="Arial",
            stroke_color="black",
            stroke_width=2,
        )

        author_clip = author_clip.set_duration(duration).set_position((30, 30))

        return mp.CompositeVideoClip(
            [comment_clip.set_position(("center", "center")), author_clip]
        ).set_duration(duration)

    def _get_background_clip(
        self, bg_path: Optional[str] = None, duration: float = 10
    ) -> "mp.VideoClip":
        if bg_path and Path(bg_path).exists():
            clip = mp.VideoFileClip(bg_path)
            if clip.duration < duration:
                clip = clip.loop(duration=duration)
            else:
                clip = clip.subclip(0, duration)
            return clip.resize(height=self.HEIGHT).crop(
                x1=0, y1=0, width=self.WIDTH, height=self.HEIGHT
            )

        bg = mp.ColorClip(size=(self.WIDTH, self.HEIGHT), color=(30, 30, 50))
        bg = bg.set_duration(duration)
        return bg

    def create_video(
        self,
        audio_files: List[str],
        texts: List[str],
        authors: List[str],
        output_filename: str,
        background_video: Optional[str] = None,
        background_music: Optional[str] = None,
    ) -> str:
        total_duration = 0
        clips = []
        narration_clips = []

        for i, (audio_file, text, author) in enumerate(
            zip(audio_files, texts, authors)
        ):
            audio = mp.AudioFileClip(audio_file)
            dur = audio.duration

            overlay = self._create_text_with_author(text, author, dur)
            overlay = overlay.set_start(total_duration)
            clips.append(overlay)
            narration_clips.append(audio.set_start(total_duration))

            total_duration += dur

        bg = self._get_background_clip(background_video, total_duration)
        clips.insert(0, bg)

        final = mp.CompositeVideoClip(clips)

        tracks = []
        if narration_clips:
            tracks.append(mp.CompositeAudioClip(narration_clips))
        if background_music and Path(background_music).exists():
            music = mp.AudioFileClip(background_music)
            if music.duration < total_duration:
                music = music.loop(duration=total_duration)
            else:
                music = music.subclip(0, total_duration)
            tracks.append(music.volumex(0.3))
        if tracks:
            final = final.set_audio(
                tracks[0] if len(tracks) == 1 else mp.CompositeAudioClip(tracks)
            )

        output_path = self.output_dir / output_filename
        final.write_videofile(
            str(output_path),
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=4,
        )

        return str(output_path)

    def create_video_simple(
        self,
        audio_files: List[str],
        texts: List[str],
        authors: List[str],
        output_filename: str,
    ) -> str:
        return self.create_video(
            audio_files, texts, authors, output_filename, None, None
        )
