import customtkinter as ctk
from tkinter import filedialog
import threading
import os
from pathlib import Path
from reddit_fetcher import RedditFetcher, RedditPost, RedditComment
from tts_generator import TTSGenerator
from video_generator import VideoGenerator

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class RedditVideoBot(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Reddit Video Bot")
        self.geometry("600x750")
        self.resizable(False, False)

        self.reddit_fetcher = RedditFetcher()
        self.tts_generator = TTSGenerator()
        self.video_generator = VideoGenerator()

        self.setup_ui()

    def setup_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title = ctk.CTkLabel(
            main_frame,
            text="Reddit Video Bot",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title.pack(pady=(0, 20))

        input_section = ctk.CTkFrame(main_frame)
        input_section.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            input_section, text="Reddit Post URL:", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.url_entry = ctk.CTkEntry(
            input_section, placeholder_text="https://reddit.com/r/..."
        )
        self.url_entry.pack(fill="x", padx=15, pady=(0, 10))

        self.use_random_var = ctk.BooleanVar(value=False)
        random_check = ctk.CTkCheckBox(
            input_section,
            text="Use random popular post from subreddit",
            variable=self.use_random_var,
            command=self.toggle_random_mode,
        )
        random_check.pack(anchor="w", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            input_section, text="Subreddit:", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=15, pady=(5, 5))

        self.subreddit_entry = ctk.CTkEntry(input_section, placeholder_text="AskReddit")
        self.subreddit_entry.insert(0, "AskReddit")
        self.subreddit_entry.pack(fill="x", padx=15, pady=(0, 15))

        settings_section = ctk.CTkFrame(main_frame)
        settings_section.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            settings_section, text="Settings", font=ctk.CTkFont(weight="bold", size=18)
        ).pack(pady=(15, 10))

        settings_grid = ctk.CTkFrame(settings_section, fg_color="transparent")
        settings_grid.pack(fill="x", padx=15)

        ctk.CTkLabel(settings_grid, text="Number of comments:").grid(
            row=0, column=0, sticky="w", pady=5
        )
        self.comments_slider = ctk.CTkSlider(
            settings_grid, from_=1, to=10, number_of_steps=9
        )
        self.comments_slider.set(5)
        self.comments_slider.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.comments_label = ctk.CTkLabel(settings_grid, text="5")
        self.comments_label.grid(row=0, column=2, sticky="w", padx=(10, 0), pady=5)

        settings_grid.columnconfigure(1, weight=1)

        ctk.CTkLabel(settings_grid, text="Voice:").grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.voice_dropdown = ctk.CTkOptionMenu(
            settings_grid,
            values=["default", "us_male", "us_female", "uk_male", "uk_female"],
        )
        self.voice_dropdown.grid(
            row=1, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=5
        )

        ctk.CTkLabel(settings_grid, text="Speed:").grid(
            row=2, column=0, sticky="w", pady=5
        )
        self.speed_slider = ctk.CTkSlider(
            settings_grid, from_=0.5, to=1.5, number_of_steps=10
        )
        self.speed_slider.set(1.0)
        self.speed_slider.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.speed_label = ctk.CTkLabel(settings_grid, text="1.0x")
        self.speed_label.grid(row=2, column=2, sticky="w", padx=(10, 0), pady=5)

        self.comments_slider.configure(command=self.update_comments_label)
        self.speed_slider.configure(command=self.update_speed_label)

        bg_section = ctk.CTkFrame(main_frame)
        bg_section.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            bg_section,
            text="Background & Music",
            font=ctk.CTkFont(weight="bold", size=18),
        ).pack(pady=(15, 10))

        bg_grid = ctk.CTkFrame(bg_section, fg_color="transparent")
        bg_grid.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(bg_grid, text="Background video:").grid(
            row=0, column=0, sticky="w", pady=5
        )
        self.bg_video_entry = ctk.CTkEntry(
            bg_grid, placeholder_text="(optional) Leave empty for solid color"
        )
        self.bg_video_entry.grid(row=0, column=1, sticky="ew", padx=(10, 5), pady=5)
        ctk.CTkButton(
            bg_grid, text="Browse", width=80, command=self.browse_bg_video
        ).grid(row=0, column=2, pady=5)

        ctk.CTkLabel(bg_grid, text="Background music:").grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.bg_music_entry = ctk.CTkEntry(bg_grid, placeholder_text="(optional)")
        self.bg_music_entry.grid(row=1, column=1, sticky="ew", padx=(10, 5), pady=5)
        ctk.CTkButton(
            bg_grid, text="Browse", width=80, command=self.browse_bg_music
        ).grid(row=1, column=2, pady=5)

        bg_grid.columnconfigure(1, weight=1)

        self.generate_btn = ctk.CTkButton(
            main_frame,
            text="Generate Video",
            font=ctk.CTkFont(size=20, weight="bold"),
            height=50,
            fg_color="#e94560",
            hover_color="#c73e54",
            command=self.start_generation,
        )
        self.generate_btn.pack(fill="x", pady=(0, 15))

        self.progress_bar = ctk.CTkProgressBar(
            main_frame, orientation="horizontal", mode="determinate"
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 10))

        self.status_label = ctk.CTkLabel(main_frame, text="Ready", text_color="gray")
        self.status_label.pack()

        self.log_text = ctk.CTkTextbox(
            main_frame, height=120, font=ctk.CTkFont(size=12)
        )
        self.log_text.pack(fill="x")

        self.comments_slider.bind(
            "<Configure>", lambda e: self.update_comments_label(None)
        )
        self.speed_slider.bind("<Configure>", lambda e: self.update_speed_label(None))

    def toggle_random_mode(self):
        if self.use_random_var.get():
            self.url_entry.configure(state="disabled")
        else:
            self.url_entry.configure(state="normal")

    def update_comments_label(self, _):
        val = int(self.comments_slider.get())
        self.comments_label.configure(text=str(val))

    def update_speed_label(self, _):
        val = round(self.speed_slider.get(), 1)
        self.speed_label.configure(text=f"{val}x")

    def browse_bg_video(self):
        path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")]
        )
        if path:
            self.bg_video_entry.delete(0, "end")
            self.bg_video_entry.insert(0, path)

    def browse_bg_music(self):
        path = filedialog.askopenfilename(
            filetypes=[("Audio files", "*.mp3 *.wav *.m4a")]
        )
        if path:
            self.bg_music_entry.delete(0, "end")
            self.bg_music_entry.insert(0, path)

    def log(self, message: str):
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.update_idletasks()

    def set_progress(self, value: float):
        self.progress_bar.set(value)
        self.update_idletasks()

    def start_generation(self):
        self.generate_btn.configure(state="disabled")
        self.log_text.delete("1.0", "end")

        thread = threading.Thread(target=self.generate_video, daemon=True)
        thread.start()

    def generate_video(self):
        try:
            self.log("Starting video generation...")
            self.set_progress(0.1)

            use_random = self.use_random_var.get()
            url = self.url_entry.get().strip() if not use_random else ""
            subreddit = self.subreddit_entry.get().strip() or "AskReddit"
            num_comments = int(self.comments_slider.get())
            voice = self.voice_dropdown.get()
            speed = self.speed_slider.get()

            self.log(f"Fetching post from {'random post' if use_random else url}...")

            if use_random:
                post = self.reddit_fetcher.get_popular_post(subreddit)
            else:
                post = self.reddit_fetcher.get_post_from_url(url)

            if not post:
                self.log(
                    "ERROR: Could not fetch post. Please check the URL or try again."
                )
                self.generate_btn.configure(state="normal")
                return

            if post.is_nsfw:
                self.log("ERROR: NSFW posts are filtered out. Please try another post.")
                self.generate_btn.configure(state="normal")
                return

            self.log(f"Got post: {post.title[:50]}...")
            self.set_progress(0.2)

            self.log(f"Fetching top {num_comments} comments...")
            comments = self.reddit_fetcher.get_comments(post.url, num_comments)

            if not comments:
                self.log("ERROR: No comments found for this post.")
                self.generate_btn.configure(state="normal")
                return

            self.log(f"Got {len(comments)} comments")
            self.set_progress(0.3)

            texts_to_speak = []
            text_display = []
            authors = []

            for comment in comments:
                if len(comment.body) > 10:
                    texts_to_speak.append(comment.body)
                    text_display.append(
                        comment.body[:200] + "..."
                        if len(comment.body) > 200
                        else comment.body
                    )
                    authors.append(comment.author)

            self.log("Generating TTS audio...")
            self.set_progress(0.4)

            audio_files = self.tts_generator.generate_batch(
                texts_to_speak, voice, speed
            )

            if not audio_files:
                self.log("ERROR: Could not generate audio.")
                self.generate_btn.configure(state="normal")
                return

            self.log(f"Generated {len(audio_files)} audio files")
            self.set_progress(0.6)

            bg_video = self.bg_video_entry.get().strip() or None
            bg_music = self.bg_music_entry.get().strip() or None

            output_filename = f"reddit_video_{int(os.times().elapsed * 1000)}.mp4"

            self.log("Creating video... (this may take a few minutes)")
            self.set_progress(0.7)

            output_path = self.video_generator.create_video(
                audio_files,
                text_display,
                authors,
                output_filename,
                bg_video,
                bg_music,
            )

            self.set_progress(1.0)
            self.log(f"Video saved to: {output_path}")
            self.log("Done! You can now upload the video.")

            self.tts_generator.cleanup()

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            import traceback

            self.log(traceback.format_exc())

        self.generate_btn.configure(state="normal")


if __name__ == "__main__":
    app = RedditVideoBot()
    app.mainloop()
