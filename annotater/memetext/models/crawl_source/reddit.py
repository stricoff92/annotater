

from django.db import models



class CrawledRedditPost(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    post_id = models.CharField(max_length=12, unique=True)
    post_url = models.CharField(max_length=255)
    image_hash = models.CharField(max_length=255)

    s3_image = models.OneToOneField(
        "memetext.S3Image", on_delete=models.SET_NULL,
        blank=True, null=True, default=None)
