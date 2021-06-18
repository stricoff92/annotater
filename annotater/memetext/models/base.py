
from uuid import uuid4

from django.db import models


class BaseModel(models.Model):
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def new_slug(self) -> str:
        while True:
            slug = str(uuid4())
            if not models.QuerySet(self).filter(slug=slug).exists():
                return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.new_slug()
            if "update_fields" in kwargs and "slug" not in kwargs["update_fields"]:
                kwargs['update_fields'] = list(kwargs['update_fields']) + ["slug"]

        return super().save(*args, **kwargs)
