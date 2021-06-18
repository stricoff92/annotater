
from django.db import models

from .base import BaseModel


class AnnotationBatch(BaseModel):
    name = models.CharField(max_length=20)
    instructions = models.TextField()
    batch_message = models.TextField()
