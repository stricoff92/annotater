
from io import BytesIO
import hashlib

from django.core.management.base import BaseCommand
from django.conf import settings
from botocore.exceptions import ClientError
import requests

from memetext.models.batch import AnnotationBatch
from memetext.models import CrawledRedditPost, S3Image
from memetext.services.crawler.reddit import RedditCrawler
from memetext.services.storage_backend import get_backend_class
from annotater.script_logger import spawn_logger


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('batch', type=str)                  # Name of the batch!
        parser.add_argument("subreddits", type=str, nargs="*")  # subreddits to crawl!

    def handle(self, *args, **kwargs):
        StorageBackendClass = get_backend_class()
        self.storage_backend = StorageBackendClass()

        self.logger = spawn_logger("redditcrawl", stdout_fh=True)

        batch_name = kwargs['batch']
        subreddits = kwargs['subreddits']
        batch = AnnotationBatch.objects.get(name__iexact=batch_name.lower())
        allowed_extensions = {'png', 'jpg', 'jpeg',}

        crawler = RedditCrawler()
        for subreddit in subreddits:
            self.logger.info("checking subreddit " + subreddit)
            posts = crawler.get_subreddit_top(subreddit, time_span="day")
            for p in posts:
                self.logger.debug("checking post " + p.id)
                if p.is_video:
                    self.logger.info("skipping, is_video")
                    continue
                if p.url.endswith(".gif"):
                    self.logger.debug("skipping, is gif")
                    continue
                if p.url.split(".")[-1].lower() not in allowed_extensions:
                    self.logger.debug("skipping, bad extension " + p.url.split(".")[-1])
                    continue
                if p.over_18:
                    self.logger.debug("skipping, over_18")
                    continue
                if CrawledRedditPost.objects.filter(post_id=p.id).exists():
                    self.logger.debug("skipping, same post id")
                    continue

                response = requests.get(p.url)
                if response.status_code >= 400:
                    self.logger.debug("skipping, could not download image " + str(response.headers))
                    continue
                data = BytesIO(response.content)
                hashed_data = hashlib.md5(data.getvalue()).hexdigest()
                self.logger.info("image hash " + hashed_data)
                if CrawledRedditPost.objects.filter(image_hash=hashed_data).exists():
                    self.logger.debug("skipping, same hash")
                    continue

                s3_image = S3Image.objects.create(
                    batch=batch,
                    file_extension=p.url.split(".")[-1],
                )
                data.seek(0)
                try:
                    self.storage_backend.upload_fp(data, settings.MEMETEXT_S3_BUCKET, s3_image.s3_path)
                    self.logger.info("file saved to " + s3_image.s3_path)
                except:
                    raise
                else:
                    CrawledRedditPost.objects.create(
                        post_id=p.id,
                        post_url=p.url,
                        image_hash=hashed_data,
                    )