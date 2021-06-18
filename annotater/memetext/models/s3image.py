
from .base import BaseModel

from django.db import models
from django.conf import settings


class S3Image(BaseModel):
    batch = models.ForeignKey(
        "memetext.AnnotationBatch",
        blank=True,
        null=True,
        default=None,
        on_delete=models.PROTECT)

    file_extension = models.CharField(max_length=4)
    last_assigned = models.DateTimeField(blank=True, null=True, default=None)


    def s3_path(self) -> str:
        bucket = settings.MEMETEXT_S3_BUCKET
        return f"{bucket}/{self.slug}/image.{self.file_extension}"
