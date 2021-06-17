
from decimal import Decimal
import json
from typing import Dict

from .base import BaseModel

from django.db import models
from django.db.models import Sum
from django.conf import settings
from django.contrib.auth import get_user_model


class AssignedAnnotation(BaseModel):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
    )
    batch = models.ForeignKey("memetext.AnnotationBatch", on_delete=models.PROTECT)
    payout_rate = models.ForeignKey("memetext.PayoutRate", on_delete=models.PROTECT)
    assigned_count = models.PositiveIntegerField()

    @property
    def completed_count(self) -> int:
        self.testannotation_set.count()

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


class TestAnnotation(BaseModel):
    s3_image = models.ForeignKey(
        "memetext.S3Image", on_delete=models.PROTECT)

    assigned_annotation = models.ForeignKey(
        AssignedAnnotation, on_delete=models.PROTECT,
    )

    def s3_path(self) -> str:
        return f"{settings.MEMETEXT_S3_BUCKET}/{self.s3_image.slug}/data.json"


class ControlAnnotation(BaseModel):
    s3_image = models.ForeignKey(
        "memetext.S3Image", on_delete=models.PROTECT)

    data = models.TextField(blank=True, null=True, default=None)

    def get_data(self) -> Dict:
        if self.data is not None:
            return json.loads(self.data)
        else:
            return {}
