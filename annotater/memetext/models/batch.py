import datetime as dt

from django.utils import timezone
from django.db import models
from django.db.models import Q

from .base import BaseModel


class AnnotationBatch(BaseModel):
    name = models.CharField(max_length=20)
    instructions = models.TextField()
    batch_message = models.TextField()

    def __str__(self):
        return f"Batch {self.name}"

    @property
    def remainder_to_be_annotated(self):
        from memetext.models import TestAnnotation
        tested_s3_images = TestAnnotation.objects.filter(s3_image__in=self.s3image_set.all()).values_list("s3_image_id", flat=True)
        return self.s3image_set.filter(
            ~models.Q(id__in=tested_s3_images)
            & (
                Q(last_assigned__isnull=True)
                | Q(last_assigned__lt=(timezone.now() - dt.timedelta(minutes=5)).isoformat())
            )
        ).count()

    def remainder_to_be_annotated_including_items_assigned_to_user(self, user):
        from memetext.models import TestAnnotation
        tested_s3_images = TestAnnotation.objects.filter(s3_image__in=self.s3image_set.all()).values_list("s3_image_id", flat=True)
        return self.s3image_set.filter(
            ~models.Q(id__in=tested_s3_images)
            & (
                Q(last_assigned__isnull=True)
                | Q(last_assigned__lt=(timezone.now() - dt.timedelta(minutes=5)).isoformat())
                | Q(slug=user.userprofile.assigned_item)
            )
        ).count()
