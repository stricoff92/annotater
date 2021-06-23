
from io import BytesIO
from decimal import Decimal
from unittest import mock

from django.urls import reverse
from rest_framework import status
from django.conf import settings
from freezegun import freeze_time

from .base import BaseTestCase
from memetext.models import  ControlAnnotation
from memetext.services.storage_backend import get_backend_class


StorageBackend = get_backend_class()

class TestAdminDownloadImage(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.rate = self.create_payout_rate(Decimal("0.1"))
        self.batch = self.create_annotation_batch()
        self.s3image = self.create_s3_image(self.batch)
        self.url = reverse("memetext-api-admin-download-image", kwargs={'image_slug':self.s3image.slug})

        self.mock_download = BytesIO(b"hello world")
        self.mock_download.seek(0)
        self.mock_download_object_to_fp = mock.patch.object(
            StorageBackend,
            "download_object_to_fp",
            return_value=self.mock_download,
        ).start()


    def test_anon_users_cannot_download_images(self):
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
        self.mock_download_object_to_fp.assert_not_called()


    def test_non_admin_users_cannot_download_images(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
        self.mock_download_object_to_fp.assert_not_called()


    def test_admin_can_download_image(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.mock_download_object_to_fp.assert_called_once_with(
            settings.MEMETEXT_S3_BUCKET,
            self.s3image.s3_path,
        )
        self.assertEquals(response.data, self.mock_download.getvalue())
        self.assertTrue(
            "image/jpeg" in response.headers['Content-Type']
            or "image/jpg" in response.headers['Content-Type'])


    def test_server_sends_no_cache_header(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertTrue("no-store" in response.headers['Cache-Control'])
