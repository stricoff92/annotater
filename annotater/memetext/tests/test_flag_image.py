
from decimal import Decimal
from dateutil import parser as dateutil_parser
from unittest import mock

from django.urls import reverse
from rest_framework import status
from django.conf import settings
from freezegun import freeze_time

from .base import BaseTestCase
from website.constants import WIDGET_NAMES



class TestFlagImage(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user.userprofile.assigned_widgets = f"derrrrpp,{WIDGET_NAMES.memetext},fooobaaar"
        self.user.userprofile.save()
        self.other_user.userprofile.assigned_widgets = f"derrrrpp,{WIDGET_NAMES.memetext},fooobaaar"
        self.other_user.userprofile.save()

        self.rate = self.create_payout_rate(Decimal("0.1"))
        self.batch = self.create_annotation_batch()
        self.s3image = self.create_s3_image(self.batch)

    def tearDown(self):
        super().tearDown()


    def test_anonymous_user_cannot_flag_images(self):
        url = reverse("memetext-api-flag-image", kwargs={'image_slug':self.s3image.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_flag_image_if_no_assigned_annotations(self):
        self.client.force_login(self.user)
        url = reverse("memetext-api-flag-image", kwargs={'image_slug':self.s3image.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("No assignment" in response.data)

    def test_user_cannot_flag_image_user_is_assigned_different_batch(self):
        other_batch = self.create_annotation_batch(name="other test batch")
        other_s3image = self.create_s3_image(other_batch)
        assignment = self.create_assigned_annotation(other_batch, user=self.other_user)

        self.client.force_login(self.other_user)
        url = reverse("memetext-api-flag-image", kwargs={'image_slug':self.s3image.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("Invalid batch" in response.data)

    def test_user_cannot_flag_image_if_item_is_not_assigned(self):
        self.client.force_login(self.user)
        self.create_assigned_annotation(self.batch, user=self.user)
        url = reverse("memetext-api-flag-image", kwargs={'image_slug':self.s3image.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("Item not assigned" in response.data)

    def test_user_can_flag_assigned_image(self):
        self.client.force_login(self.user)
        self.create_assigned_annotation(self.batch, user=self.user)
        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()
        url = reverse("memetext-api-flag-image", kwargs={'image_slug':self.s3image.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(self.s3image.is_flagged)
        self.s3image.refresh_from_db()
        self.assertTrue(self.s3image.is_flagged)
