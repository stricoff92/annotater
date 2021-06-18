

""" S3 image is a shared resource
"""


import datetime as dt


from dateutil import parser as datetime_parser
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
import jwt


from .base import BaseModel


class S3Image(BaseModel):
    batch = models.ForeignKey(
        "memetext.AnnotationBatch",
        blank=True,
        null=True,
        default=None,
        on_delete=models.PROTECT)

    file_extension = models.CharField(max_length=4)
    last_assigned = models.DateTimeField(blank=True, null=True, default=None)

    def __str__(self):
        return f"S3Image batch:{self.batch.name} {self.slug}"

    @property
    def s3_path(self) -> str:
        bucket = settings.MEMETEXT_S3_BUCKET
        return f"/{self.slug}/image.{self.file_extension}"


    def get_download_image_url(self, assignment_slug:str) -> str:
        return reverse(
            "memetext-api-download-image",
            kwargs={
                "assignment_slug":assignment_slug,
                "image_slug":self.slug,
            },
        )


    def get_load_image_token(self) -> str:
        """ This token expires quickly.
            It is used by the FE to download the image file.
        """
        return jwt.encode(
            {
                "slug":self.slug,
                "expires":(timezone.now() + dt.timedelta(seconds=5)).isoformat(),
            },
            settings.SECRET_KEY,
            "HS256",
        )

    def load_image_token_is_valid(self, token:str, nowtz=None) -> bool:
        nowtz = nowtz or timezone.now()
        try:
            data = jwt.decode(token.encode(), settings.SECRET_KEY, "HS256")
            if datetime_parser.parse(data['expires']) < nowtz:
                raise Exception
            if data['slug'] != self.slug:
                raise Exception
        except Exception as e:
            print("error ", e)
            return False
        return True


    def get_annotate_image_token(self, load_image_token: str) -> str:
        """ This token does not expire. It is used by the FE when submitting an annotation for this image
        """
        return jwt.encode(
            {
                "__salt":timezone.now().isoformat(),
                "slug":self.slug,
            },
            settings.SECRET_KEY + load_image_token,
            "HS256",
        )

    def annotate_image_token_is_valid(self, token: str, load_image_token: str) -> bool:
        data = jwt.decode(token.encode(), settings.SECRET_KEY + load_image_token, "HS256")
        try:
            if data['slug'] != self.slug:
                raise Exception
        except Exception:
            return False
        return True
