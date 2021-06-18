
from django.urls import reverse
from rest_framework import status

from memetext.tests.base import BaseTestCase
from website.constants import WIDGET_NAMES

class TestWidgetAccess(BaseTestCase):

    def test_user_without_assigned_widget_gets_401_response(self):
        self.user.userprofile.assigned_widgets = "derp"
        self.user.userprofile.save()
        self.client.force_login(self.user)
        response = self.client.get(reverse("memetext-web-landing"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.get(reverse("memetext-web-add-annotation"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_with_assigned_widget_gets_200_response(self):
        self.user.userprofile.assigned_widgets = WIDGET_NAMES.memetext
        self.user.userprofile.save()
        self.client.force_login(self.user)
        response = self.client.get(reverse("memetext-web-landing"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse("memetext-web-add-annotation"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
