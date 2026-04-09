from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import threading
import os
import uuid
from pathlib import Path
from reddit_fetcher import RedditFetcher
from tts_generator import TTSGenerator
from video_generator import VideoGenerator

app = Flask(__name__, template_folder="templates")
CORS(app)

jobs = {}

reddit_fetcher = RedditFetcher()
tts_generator = TTSGenerator()
video_generator = VideoGenerator(output_dir="output")
os.makedirs("output", exist_ok=True)


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.json

    url = data.get("url", "")
    subreddit = data.get("subreddit", "AskReddit")
    use_random = data.get("use_random", False)
    num_comments = data.get("num_comments", 5)
    voice = data.get("voice", "default")
    speed = data.get("speed", 1.0)
    background_video = data.get("background_video")
    background_music = data.get("background_music")

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "progress": 0, "message": "Starting..."}

    def process_job():
        try:
            jobs[job_id]["message"] = "Fetching post..."
            jobs[job_id]["progress"] = 0.1

            if use_random:
                post = reddit_fetcher.get_popular_post(subreddit)
            else:
                post = reddit_fetcher.get_post_from_url(url)

            if not post:
                jobs[job_id] = {"status": "error", "message": "Could not fetch post"}
                return

            if post.is_nsfw:
                jobs[job_id] = {"status": "error", "message": "NSFW posts are filtered"}
                return

            jobs[job_id]["message"] = "Fetching comments..."
            jobs[job_id]["progress"] = 0.2

            comments = reddit_fetcher.get_comments(post.url, num_comments)

            if not comments:
                jobs[job_id] = {"status": "error", "message": "No comments found"}
                return

            texts_to_speak = []
            text_display = []
            authors = []

            for comment in comments:
                if len(comment.body) > 10:
                    texts_to_speak.append(comment.body)
                    text_display.append(comment.body[:200])
                    authors.append(comment.author)

            jobs[job_id]["message"] = "Generating TTS audio..."
            jobs[job_id]["progress"] = 0.4

            audio_files = tts_generator.generate_batch(texts_to_speak, voice, speed)

            jobs[job_id]["message"] = "Creating video..."
            jobs[job_id]["progress"] = 0.7

            output_filename = f"reddit_video_{job_id}.mp4"

            output_path = video_generator.create_video(
                audio_files,
                text_display,
                authors,
                output_filename,
                background_video,
                background_music,
            )

            tts_generator.cleanup()

            jobs[job_id] = {
                "status": "complete",
                "progress": 1.0,
                "message": "Done",
                "output": output_path,
            }

        except Exception as e:
            jobs[job_id] = {"status": "error", "message": str(e)}

    thread = threading.Thread(target=process_job)
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>", methods=["GET"])
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/api/download/<filename>", methods=["GET"])
def download(filename):
    return send_file(f"output/{filename}", as_attachment=True)


@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
