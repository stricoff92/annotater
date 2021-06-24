
import hashlib
from typing import Generator

from django.conf import settings
import praw


class RedditCrawler:
    def __init__(self, redditInstance=None):
        self._reddit = praw.Reddit(
            client_id=settings.REDDIT_APP_ID,
            client_secret=settings.REDDIT_APP_SECRET,
            password=settings.REDDIT_PASSWORD,
            user_agent=f"testscript by u/{settings.REDDIT_USERNAME}",
            username=settings.REDDIT_USERNAME,
        )

    @property
    def subreddits(self):
        return self._reddit.subreddits

    @property
    def subreddit(self):
        return self._reddit.subreddit

    @property
    def user(self):
        return self._reddit.user

    def get_subreddit_top(self,  subreddit:str, time_span="day", limit=None) -> Generator:
        yield from self.subreddit(subreddit).top(time_span, limit=limit)

    def hash_bytes(data: bytes):
        return hashlib.md5(data).hexdigest()
