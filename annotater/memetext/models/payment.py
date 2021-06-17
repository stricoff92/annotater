
from .base import BaseModel

from django.db import models


class PayoutRate(BaseModel):
    rate = models.DecimalField(max_digits=4, decimal_places=2)


class Payment(BaseModel):
    assignment = models.ForeignKey("memetext.AssignedAnnotation", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
