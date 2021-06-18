
from .base import BaseModel

from django.db import models


class PayoutRate(BaseModel):
    rate = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return f"PayoutRate {self.rate}"


class Payment(BaseModel):
    assignment = models.ForeignKey("memetext.AssignedAnnotation", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    memo = models.CharField(max_length=255, blank=True, null=True, default=None)
