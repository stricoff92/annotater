
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
from memetext.services.storage_backend import get_backend_class


StorageBackend = get_backend_class()

class TestImageDownload(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user.userprofile.assigned_widgets = f"derrrrpp,{WIDGET_NAMES.memetext},fooobaaar"
        self.user.userprofile.save()

        self.rate = self.create_payout_rate(Decimal("0.1"))
        self.batch = self.create_annotation_batch()
        self.s3image = self.create_s3_image(self.batch)

        self.downloaded_fp = BytesIO(b"Hello world!")
        self.downloaded_fp.seek(0)
        self.mock_s3_download = mock.patch.object(
            StorageBackend,
            "download_object_to_fp",
            return_value=self.downloaded_fp,
        ).start()

    def tearDown(self):
        self.mock_s3_download.stop()
        super().tearDown()


    # GET IMAGE ROUTE

    def test_user_must_be_authenticated(self):
        annotation_assignment = self.create_assigned_annotation(self.batch)
        url = reverse(
            "memetext-api-get-image",
            kwargs={"assignment_slug":annotation_assignment.slug})

        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_user_cannot_user_another_users_assigned_annotation(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch, user=self.other_user)
        url = reverse(
            "memetext-api-get-image",
            kwargs={"assignment_slug":annotation_assignment.slug})

        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_user_can_request_image_url_from_api(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        url = reverse(
            "memetext-api-get-image",
            kwargs={"assignment_slug":annotation_assignment.slug})

        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(set(response.data.keys()), set(['load_image_token', 'url', 'annotate_image_token', 'image_slug']))
        self.assertEquals(response.data['url'], self.s3image.get_download_image_url(annotation_assignment.slug))
        self.assertEquals(response.data['image_slug'], self.s3image.slug)


    def test_user_is_given_the_same_assigned_item(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        url = reverse(
            "memetext-api-get-image",
            kwargs={"assignment_slug":annotation_assignment.slug})

        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()

        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.user.userprofile.refresh_from_db()
        self.assertEqual(self.user.userprofile.assigned_item, self.s3image.slug)
        self.assertEqual(response.data['url'], self.s3image.get_download_image_url(annotation_assignment.slug))


    @freeze_time("2020-05-17T14:17:30+00:00")
    def test_claims_from_load_image_token(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        url = reverse(
            "memetext-api-get-image",
            kwargs={"assignment_slug":annotation_assignment.slug})

        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        load_image_token_claims = jwt.decode(response.data['load_image_token'], settings.SECRET_KEY, "HS256")
        self.assertEqual(set(['slug', 'expires']), set(load_image_token_claims.keys()))
        self.assertEqual(load_image_token_claims['slug'], self.s3image.slug)
        self.assertEqual(load_image_token_claims['expires'], "2020-05-17T14:17:35+00:00") # 5 seconds later.


    @freeze_time("2020-05-17T14:17:30+00:00")
    def test_claims_from_annotate_image_token(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        url = reverse(
            "memetext-api-get-image",
            kwargs={"assignment_slug":annotation_assignment.slug})

        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        load_image_token_claims = jwt.decode(response.data['load_image_token'], settings.SECRET_KEY, "HS256")
        annotate_image_token_claims = jwt.decode(
            response.data['annotate_image_token'],
            settings.SECRET_KEY + response.data['load_image_token'],
            "HS256"
        )
        self.assertEqual(set(['__salt', 'slug']), set(annotate_image_token_claims.keys()))
        self.assertEqual(annotate_image_token_claims['slug'], self.s3image.slug)
        self.assertEqual(annotate_image_token_claims['__salt'], "2020-05-17T14:17:30+00:00")


    def test_user_cant_request_image_url_from_api_if_no_unannotated_s3_images(self):
        other_user_assigned_annotation = self.create_assigned_annotation(self.batch, user=self.other_user)
        other_user_test_annotation = self.create_test_annotation(
            self.s3image, other_user_assigned_annotation)

        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        url = reverse(
            "memetext-api-get-image",
            kwargs={"assignment_slug":annotation_assignment.slug})

        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, {'load_image_token': None, 'annotate_image_token': None, 'url': None})


    def test_user_gets_empty_response_url_from_api_if_assignment_complete(self):
        self.client.force_login(self.user)
        another_s3image = self.create_s3_image(self.batch)
        annotation_assignment = self.create_assigned_annotation(self.batch, assigned_count=1)
        test_annotation = self.create_test_annotation(
            self.s3image, annotation_assignment)
        url = reverse(
            "memetext-api-get-image",
            kwargs={"assignment_slug":annotation_assignment.slug})

        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, {'load_image_token': None, 'annotate_image_token': None, 'url': None})


    def test_missing_assigned_item_is_updated(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        self.user.userprofile.assigned_item = "foooobaaaaar"
        self.user.userprofile.save()
        url = reverse(
            "memetext-api-get-image",
            kwargs={"assignment_slug":annotation_assignment.slug})
        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.user.userprofile.refresh_from_db()
        self.assertEqual(self.user.userprofile.assigned_item, self.s3image.slug)


    def test_assigned_item_is_updated_if_annotation_already_exists(self):
        self.client.force_login(self.user)
        other_user_assigned_annotation = self.create_assigned_annotation(self.batch, user=self.other_user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        another_s3image = self.create_s3_image(self.batch)
        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()
        test_annotation = self.create_test_annotation(
            self.s3image, annotation_assignment)

        url = reverse(
            "memetext-api-get-image",
            kwargs={"assignment_slug":annotation_assignment.slug})
        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.user.userprofile.refresh_from_db()
        self.assertEqual(self.user.userprofile.assigned_item, another_s3image.slug)


    def test_get_url_api_returns_empty_response_if_no_unannotated_images(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        test_annotation = self.create_test_annotation(
            self.s3image, annotation_assignment)
        url = reverse(
            "memetext-api-get-image",
            kwargs={"assignment_slug":annotation_assignment.slug})
        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, {'load_image_token': None, 'annotate_image_token': None, 'url': None})


    def test_assinged_item_is_set_if_url_is_downloaded(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        url = reverse(
            "memetext-api-get-image",
            kwargs={"assignment_slug":annotation_assignment.slug})

        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.user.userprofile.refresh_from_db()
        self.assertEquals(self.user.userprofile.assigned_item, self.s3image.slug)


    @freeze_time("2020-05-17T14:17:30+00:00")
    def test_s3_image_last_assigned_is_set_when_downloaded(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        url = reverse(
            "memetext-api-get-image",
            kwargs={"assignment_slug":annotation_assignment.slug})

        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.s3image.refresh_from_db()
        self.assertEquals(self.s3image.last_assigned, dateutil_parser.parse("2020-05-17T14:17:30+00:00"))


    @freeze_time("2020-05-17T14:17:30+00:00")
    def test_user_cannot_download_if_last_assigned_is_recent_and_s3_image_is_not_the_users_assigned_item(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        self.s3image.last_assigned = dateutil_parser.parse("2020-05-17T14:17:27+00:00")
        self.s3image.save()
        self.user.userprofile.assigned_item = "foobar"
        self.user.userprofile.save()
        url = reverse(
            "memetext-api-get-image",
            kwargs={"assignment_slug":annotation_assignment.slug})

        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)

        self.s3image.last_assigned = dateutil_parser.parse("2020-05-17T14:11:22+00:00")
        self.s3image.save()
        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)


    @freeze_time("2020-05-17T14:17:30+00:00")
    def test_user_can_download_if_last_assigned_is_recent_and_s3_image_is_the_users_assigned_item(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        self.s3image.last_assigned = dateutil_parser.parse("2020-05-17T14:17:27+00:00")
        self.s3image.save()
        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()
        url = reverse(
            "memetext-api-get-image",
            kwargs={"assignment_slug":annotation_assignment.slug})

        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)


    # DOWNLOAD IMAGE ROUTE

    def test_anon_user_cant_download_image(self):
        annotation_assignment = self.create_assigned_annotation(self.batch)
        url = reverse("memetext-api-download-image", kwargs={
            "assignment_slug":annotation_assignment.slug,
            "image_slug":self.s3image.slug,
        })
        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_user_cant_download_without_sending_token(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        url = reverse("memetext-api-download-image", kwargs={
            "assignment_slug":annotation_assignment.slug,
            "image_slug":self.s3image.slug,
        })
        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_user_can_download_by_including_download_token(self):
        self.client.force_login(self.user)
        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()

        annotation_assignment = self.create_assigned_annotation(self.batch)
        url = reverse("memetext-api-download-image", kwargs={
            "assignment_slug":annotation_assignment.slug,
            "image_slug":self.s3image.slug,
        })
        get_image_token = self.s3image.get_load_image_token()
        response = self.client.get(url + "?t=" + get_image_token)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertTrue('image/jpeg' in response.headers['Content-Type'])


    def test_image_is_downloaded_from_s3(self):
        self.client.force_login(self.user)
        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()

        annotation_assignment = self.create_assigned_annotation(self.batch)
        url = reverse("memetext-api-download-image", kwargs={
            "assignment_slug":annotation_assignment.slug,
            "image_slug":self.s3image.slug,
        })
        get_image_token = self.s3image.get_load_image_token()
        response = self.client.get(url + "?t=" + get_image_token)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.mock_s3_download.assert_called_once_with(
            settings.MEMETEXT_S3_BUCKET, self.s3image.s3_path)
        self.assertEquals(response.data, b"Hello world!")


    def test_headers_are_sent_to_avoid_caching(self):
        self.client.force_login(self.user)
        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()

        annotation_assignment = self.create_assigned_annotation(self.batch)
        url = reverse("memetext-api-download-image", kwargs={
            "assignment_slug":annotation_assignment.slug,
            "image_slug":self.s3image.slug,
        })
        get_image_token = self.s3image.get_load_image_token()
        response = self.client.get(url + "?t=" + get_image_token)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertTrue('no-store' in response.headers['Cache-Control'])


    def test_user_gets_empty_response_when_downloading_image_if_assignment_is_complete(self):
        self.client.force_login(self.user)
        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()

        annotation_assignment = self.create_assigned_annotation(self.batch, assigned_count=0)
        url = reverse("memetext-api-download-image", kwargs={
            "assignment_slug":annotation_assignment.slug,
            "image_slug":self.s3image.slug,
        })
        get_image_token = self.s3image.get_load_image_token()
        response = self.client.get(url + "?t=" + get_image_token)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

        annotation_assignment.assigned_count = 1
        annotation_assignment.save()
        response = self.client.get(url + "?t=" + get_image_token)
        self.assertEquals(response.status_code, status.HTTP_200_OK)


    def test_user_gets_400_if_they_request_s3_image_that_is_not_their_assigned_item(self):
        self.client.force_login(self.user)
        annotation_assignment = self.create_assigned_annotation(self.batch)
        url = reverse("memetext-api-download-image", kwargs={
            "assignment_slug":annotation_assignment.slug,
            "image_slug":self.s3image.slug,
        })
        get_image_token = self.s3image.get_load_image_token()
        response = self.client.get(url + "?t=" + get_image_token)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.userprofile.assigned_item = self.s3image.slug
        self.user.userprofile.save()
        response = self.client.get(url + "?t=" + get_image_token)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
