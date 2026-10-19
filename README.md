# Reddit Video Bot

Creates TikTok/YouTube style videos from Reddit posts with TTS narration.

## Features
- Input specific Reddit post URL or fetch random popular post from subreddit
- TTS reads top comments with multiple voice options
- Text appears on screen synchronized with audio
- Custom background video and background music support
- NSFW filter (enabled by default)
- 1080x1920 vertical video format

## Requirements
- Python 3.10+
- ffmpeg (for video encoding)
- ImageMagick (for the on-screen text rendering via moviepy TextClip)

## Installation

```bash
cd reddit-video-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

### Web server

A Flask web UI and JSON API are also included (`flask` and `flask-cors` are in
requirements.txt):

```bash
python server.py
# open http://localhost:5000
```

## Tests

Offline unit tests for the fetcher, TTS naming, video audio assembly and the
download route. No network, Reddit API keys or video rendering needed:

```bash
python -m unittest discover -s tests
```

## GUI Options
- **Reddit URL**: Paste a specific Reddit post link
- **Use random**: Fetch popular post from chosen subreddit
- **Comments**: Number of top comments to include (1-10)
- **Voice**: Select TTS voice (default, us_male, us_female, uk_male, uk_female)
- **Speed**: Adjust TTS speech rate
- **Background video**: Optional custom video file
- **Background music**: Optional audio file

## Output
Video saved to `output/` directory as `reddit_video_[timestamp].mp4`
