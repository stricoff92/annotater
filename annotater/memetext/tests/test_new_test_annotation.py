
from io import BytesIO
from decimal import Decimal
from dateutil import parser as dateutil_parser
from unittest import mock

from django.urls import reverse
from rest_framework import status
from django.conf import settings
import jwt
from freezegun import freeze_time

from .base import BaseTestCase
from website.constants import WIDGET_NAMES
from memetext.services.s3 import S3Service
from memetext.models import TestAnnotation


class TestNewTestAnnotation(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user.userprofile.assigned_widgets = f"derrrrpp,{WIDGET_NAMES.memetext},fooobaaar"
        self.user.userprofile.save()

        self.rate = self.create_payout_rate(Decimal("0.1"))
        self.batch = self.create_annotation_batch()
        self.s3image = self.create_s3_image(self.batch)
        self.url = reverse("memetext-api-new-test-annotation")

        self.mock_s3_upload = mock.patch.object(
            S3Service,
            "upload_fp",
            return_value=None,
        ).start()

    def tearDown(self):
        self.mock_s3_upload.stop()
        super().tearDown()


    def test_anon_user_cannot_create_new_test_annotations(self):
        annotation_assignment = self.create_assigned_annotation(self.batch)
        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()
        load_image_token = self.s3image.get_load_image_token()
        annotate_image_token = self.s3image.get_annotate_image_token(load_image_token)
        data = {
            'text': 'hello world',
            'image_slug': self.s3image.slug,
            'annotate_image_token': annotate_image_token,
            'load_image_token': load_image_token,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(TestAnnotation.objects.exists())


    def test_tokens_are_required_to_create_new_test_annotation(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()
        load_image_token = self.s3image.get_load_image_token()
        annotate_image_token = self.s3image.get_annotate_image_token(load_image_token)
        data = {
            'text': 'hello world',
            'image_slug': self.s3image.slug,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(TestAnnotation.objects.exists())


    def test_user_cannot_create_new_test_annotation_if_no_associated_assignment(self):
        self.client.force_login(self.user)
        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()
        load_image_token = self.s3image.get_load_image_token()
        annotate_image_token = self.s3image.get_annotate_image_token(load_image_token)
        data = {
            'text': 'hello world',
            'image_slug': self.s3image.slug,
            'annotate_image_token': annotate_image_token,
            'load_image_token': load_image_token,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("No assignment." in str(response.data))
        self.assertFalse(TestAnnotation.objects.exists())


    def test_user_cannot_create_new_test_assignment_for_s3_image_that_does_not_exists(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()
        load_image_token = self.s3image.get_load_image_token()
        annotate_image_token = self.s3image.get_annotate_image_token(load_image_token)
        data = {
            'text': 'hello world',
            'image_slug': "FOOOOBAAAAR",
            'annotate_image_token': annotate_image_token,
            'load_image_token': load_image_token,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(TestAnnotation.objects.exists())


    def test_api_returns_400_if_invalid_tokens_are_sent(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()
        load_image_token = self.s3image.get_load_image_token()
        annotate_image_token = self.s3image.get_annotate_image_token(load_image_token)
        data = {
            'text': 'hello world',
            'image_slug': self.s3image.slug,
            'annotate_image_token': annotate_image_token,
            'load_image_token': load_image_token + "foooobaaar", # mess this token up
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("Tokens are not valid." in str(response.data))
        self.assertFalse(TestAnnotation.objects.exists())


    def test_api_returns_400_if_user_is_not_assigned_to_the_s3_image(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        self.user.userprofile.assigned_item = "foobaaarrr" # incorrect assigned_item
        self.user.userprofile.save()
        load_image_token = self.s3image.get_load_image_token()
        annotate_image_token = self.s3image.get_annotate_image_token(load_image_token)
        data = {
            'text': 'hello world',
            'image_slug': self.s3image.slug,
            'annotate_image_token': annotate_image_token,
            'load_image_token': load_image_token,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("Image not assigned." in str(response.data))
        self.assertFalse(TestAnnotation.objects.exists())


    def test_api_returns_400_if_assignment_is_complete(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch, assigned_count=0)
        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()
        load_image_token = self.s3image.get_load_image_token()
        annotate_image_token = self.s3image.get_annotate_image_token(load_image_token)
        data = {
            'text': 'hello world',
            'image_slug': self.s3image.slug,
            'annotate_image_token': annotate_image_token,
            'load_image_token': load_image_token,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("No assignment." in str(response.data))
        self.assertFalse(TestAnnotation.objects.exists())


    def test_user_can_create_new_test_annotation(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()
        load_image_token = self.s3image.get_load_image_token()
        annotate_image_token = self.s3image.get_annotate_image_token(load_image_token)
        data = {
            'text': 'hello world',
            'image_slug': self.s3image.slug,
            'annotate_image_token': annotate_image_token,
            'load_image_token': load_image_token,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(TestAnnotation.objects.count(), 1)
        ta = TestAnnotation.objects.first()
        self.assertEquals(ta.s3_image, self.s3image)


    def test_new_annotation_data_is_uploaded_to_s3(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()
        load_image_token = self.s3image.get_load_image_token()
        annotate_image_token = self.s3image.get_annotate_image_token(load_image_token)
        data = {
            'text': 'hello world',
            'image_slug': self.s3image.slug,
            'annotate_image_token': annotate_image_token,
            'load_image_token': load_image_token,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(TestAnnotation.objects.count(), 1)
        ta = TestAnnotation.objects.first()
        self.assertEquals(
            self.mock_s3_upload.call_args_list[0][0][0].getvalue(),
            b'{"data": "hello world"}',
        )
        self.assertEquals(
            self.mock_s3_upload.call_args_list[0][0][1],
            settings.MEMETEXT_S3_BUCKET,
        )
        self.assertEquals(
            self.mock_s3_upload.call_args_list[0][0][2],
            ta.s3_path,
        )
