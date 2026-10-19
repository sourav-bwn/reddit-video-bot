import re
import requests
from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class RedditPost:
    title: str
    body: str
    author: str
    subreddit: str
    is_nsfw: bool
    url: str


@dataclass
class RedditComment:
    author: str
    body: str
    score: int


class RedditFetcher:
    def __init__(self, user_agent: str = "RedditVideoBot/1.0"):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\[.*?\]\([^)]*\)", "", text)  # markdown links
        text = re.sub(r"\[.*?\]", "", text)
        text = re.sub(r"http\S+", "", text)
        text = re.sub(r"\*+", "", text)
        text = re.sub(r"_+", "", text)
        text = re.sub(r"&amp;", "and", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def get_post_from_url(self, url: str) -> Optional[RedditPost]:
        match = re.search(r"reddit\.com/r/(\w+)/comments/(\w+)", url)
        if not match:
            return None

        subreddit, post_id = match.groups()
        api_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"

        try:
            response = self.session.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            post_data = data[0]["data"]["children"][0]["data"]

            return RedditPost(
                title=self._clean_text(post_data.get("title", "")),
                body=self._clean_text(post_data.get("selftext", "")),
                author=post_data.get("author", "anonymous"),
                subreddit=post_data.get("subreddit", ""),
                is_nsfw=post_data.get("over_18", False),
                url=url,
            )
        except Exception as e:
            print(f"Error fetching post: {e}")
            return None

    def get_popular_post(self, subreddit: str = "AskReddit") -> Optional[RedditPost]:
        api_url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=50"

        try:
            response = self.session.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            posts = data["data"]["children"]
            for post in posts:
                post_data = post["data"]
                if not post_data.get("over_18", False):
                    return RedditPost(
                        title=self._clean_text(post_data.get("title", "")),
                        body=self._clean_text(post_data.get("selftext", "")),
                        author=post_data.get("author", "anonymous"),
                        subreddit=post_data.get("subreddit", ""),
                        is_nsfw=False,
                        url="https://reddit.com" + post_data.get("permalink", ""),
                    )
            return None
        except Exception as e:
            print(f"Error fetching popular post: {e}")
            return None

    def get_comments(self, url: str, limit: int = 5) -> List[RedditComment]:
        match = re.search(r"reddit\.com/r/(\w+)/comments/(\w+)", url)
        if not match:
            return []

        subreddit, post_id = match.groups()
        api_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"

        try:
            response = self.session.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            comments = []
            for child in data[1]["data"]["children"]:
                if len(comments) >= limit:
                    break

                comment_data = child.get("data", {})
                body = self._clean_text(comment_data.get("body", ""))

                if body and comment_data.get("author") != "[deleted]":
                    comments.append(
                        RedditComment(
                            author=comment_data.get("author", "anonymous"),
                            body=body,
                            score=comment_data.get("score", 0),
                        )
                    )

            comments.sort(key=lambda x: x.score, reverse=True)
            return comments[:limit]
        except Exception as e:
            print(f"Error fetching comments: {e}")
            return []
