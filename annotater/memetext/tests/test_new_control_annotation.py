
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from django.conf import settings
from freezegun import freeze_time

from .base import BaseTestCase
from memetext.models import  ControlAnnotation


class TestNewControlAnnotation(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.rate = self.create_payout_rate(Decimal("0.1"))
        self.batch = self.create_annotation_batch()
        self.s3image = self.create_s3_image(self.batch)
        self.url = reverse("memetext-api-new-control-annotation")


    def test_anon_user_cannot_create_new_control_annotation(self):
        data = {
            'image_slug': self.s3image.slug,
            'text': 'fooo baar'
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_non_admin_user_cannot_create_new_control_annotation(self):
        self.client.force_login(self.other_user)
        data = {
            'image_slug': self.s3image.slug,
            'text': 'fooo baar'
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_admin_cannot_create_control_annotation_for_s3_image_that_already_has_one(self):
        self.client.force_login(self.admin_user)
        self.create_control_annotation(self.s3image, "{}") # create conflicting control annotation.
        data = {
            'image_slug': self.s3image.slug,
            'text': 'fooo baar'
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEquals(response.status_code, status.HTTP_409_CONFLICT)


    def test_admin_can_create_control_annotation(self):
        self.client.force_login(self.admin_user)
        data = {
            'image_slug': self.s3image.slug,
            'text': 'fooo baar'
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ControlAnnotation.objects.count(), 1)

        ca = ControlAnnotation.objects.first()
        self.assertEquals(ca.get_data(), {'data': 'fooo baar'})
