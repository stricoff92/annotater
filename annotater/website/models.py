
from django.db import models

from django.contrib.auth import get_user_model


class UserProfile(models.Model):
    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.PROTECT,
    )
    assigned_widgets = models.TextField()


    def can_use_widget(self, name:str) -> bool:
        return name in self.assigned_widgets
        return self.user.is_superuser or name in self.assigned_widgets
