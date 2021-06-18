
import datetime as dt
from typing import Tuple

from django.db.models import Q
from django.utils import timezone

from memetext.models import TestAnnotation
from memetext.models import AssignedAnnotation


class QueryService:
    def get_assigned_annotation_and_batch_from_user(self, user) -> Tuple:
        try:
            assigned = AssignedAnnotation.objects.get(user=user, is_active=True)
        except (
            AssignedAnnotation.DoesNotExist,
            AssignedAnnotation.MultipleObjectsReturned,
        ):
            return None, None

        assigned = None if assigned is None or assigned.is_complete else assigned
        batch = assigned.batch if assigned is not None else None
        return assigned, batch


    def remaining_images_user_can_annotate(self, user) -> int:
        assigned_annotation, batch = self.get_assigned_annotation_and_batch_from_user(user)
        if not assigned_annotation:
            return 0

        tested_s3_images = (TestAnnotation.objects
            .filter(s3_image__in=batch.s3image_set.all())
            .values_list("s3_image_id", flat=True))

        return batch.s3image_set.filter(
            ~Q(id__in=tested_s3_images)
            & (
                Q(last_assigned__isnull=True)
                | Q(last_assigned__lt=(timezone.now() - dt.timedelta(minutes=5)).isoformat())
                | Q(slug=user.userprofile.assigned_item)
            )
        ).count()
