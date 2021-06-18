
from django.db import models

from django.contrib.auth import get_user_model


class UserProfile(models.Model):
    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.PROTECT,
    )
    assigned_widgets = models.TextField()

    assigned_item = models.CharField(
        max_length=100, blank=True, null=True, default=None)

    def __str__(self):
        return "UserProfile for " + str(self.user)

    def can_use_widget(self, name:str) -> bool:
        return name in self.assigned_widgets
        return self.user.is_superuser or name in self.assigned_widgets
