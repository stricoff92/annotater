
from decimal import Decimal
import json
from typing import Dict

from .base import BaseModel

from django.db import models
from django.db.models import Sum
from django.conf import settings
from django.contrib.auth import get_user_model
from django.forms import ValidationError


class AssignedAnnotation(BaseModel):
    """ AssignedAnnotation represents an task given to a user to look at N number of item and annotate them.
    """
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
    )
    batch = models.ForeignKey("memetext.AnnotationBatch", on_delete=models.PROTECT)
    payout_rate = models.ForeignKey("memetext.PayoutRate", on_delete=models.PROTECT)
    assigned_count = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    @property
    def completed_count(self) -> int:
        return self.testannotation_set.count()

    @property
    def is_complete(self) -> bool:
        return self.completed_count >= self.assigned_count

    @property
    def payout_amount(self) -> Decimal:
        return self.payout_rate.rate * self.completed_count

    @property
    def paid_amount(self) -> Decimal:
        return self.payment_set.aggregate(s=Sum("amount"))["s"] or Decimal(0)

    @property
    def is_paid(self):
        return self.payout_amount >= self.paid_amount

    @property
    def invoice_id(self) -> str:
        return self.slug[:8]

    def save(self, *a, **k):
        if self.id:
            if AssignedAnnotation.objects.exclude(id=self.id).filter(user=self.user, is_active=True).exists():
                raise ValidationError
        else:
            if AssignedAnnotation.objects.filter(user=self.user, is_active=True).exists():
                raise ValidationError
        return super().save(*a, **k)


class TestAnnotation(BaseModel):
    """ Instance of a user provided annotation of an s3_image.
    """
    s3_image = models.ForeignKey(
        "memetext.S3Image", on_delete=models.PROTECT)

    assigned_annotation = models.ForeignKey(
        AssignedAnnotation, on_delete=models.PROTECT,
    )

    def s3_path(self) -> str:
        return f"{settings.MEMETEXT_S3_BUCKET}/{self.s3_image.slug}/data-{self.slug}.json"




class ControlAnnotation(BaseModel):
    """ Expected value a TestAnnotation's data
    """
    s3_image = models.ForeignKey(
        "memetext.S3Image", on_delete=models.PROTECT)

    data = models.TextField(blank=True, null=True, default=None)

    def get_data(self) -> Dict:
        if self.data is not None:
            return json.loads(self.data)
        else:
            return {}
