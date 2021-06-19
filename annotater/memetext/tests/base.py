
from decimal import Decimal

from django.test import TestCase
from django.test import Client as TestClient
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser, User

from website.models import UserProfile
from memetext.models import AnnotationBatch, AssignedAnnotation, S3Image, PayoutRate, TestAnnotation, ControlAnnotation


class BaseTestCase(TestCase):

    PASSWORD_FACTORY = "password-yo"
    ADMIN_USER_NAME = "foobar-admin"
    USER_NAME = "foobar"
    OTHER_USER_NAME = "foobar2"
    SUPER_USER_NAME = "foobar3"


    def setUp(self):
        self.client = TestClient()

        self.user = User.objects.create_user(
            username=self.USER_NAME,
            email=f'{self.USER_NAME}@mail.com',
            password=self.PASSWORD_FACTORY)
        self.user_profile = UserProfile.objects.create(user=self.user)

        self.other_user = User.objects.create_user(
            username=self.OTHER_USER_NAME,
            email=f'{self.OTHER_USER_NAME}@mail.com',
            password=self.PASSWORD_FACTORY)
        self.other_user_profile = UserProfile.objects.create(user=self.other_user)

        self.admin_user = User.objects.create_superuser(
            username=self.SUPER_USER_NAME,
            email=f"{self.SUPER_USER_NAME}@derpmail.com",
            password=self.PASSWORD_FACTORY
        )
        self.admin_user_profile = UserProfile.objects.create(user=self.admin_user)


    def tearDown(self):
        self.client.logout()

    # FACTORY METHODS
    def create_annotation_batch(self, name="test_batch", instructions="type the text you see", batch_message="welcome!"):
        return AnnotationBatch.objects.create(
            name=name, instructions=instructions, batch_message=batch_message,
        )

    def create_assigned_annotation(self, batch, user=None, payout_rate=None, assigned_count=5, is_active=True):
        return AssignedAnnotation.objects.create(
            user=(user or self.user), batch=batch,
            assigned_count=assigned_count, payout_rate=(payout_rate or self.create_payout_rate("0.1"))
        )

    def create_s3_image(self, batch, file_extension="jpg", last_assigned=None):
        return S3Image.objects.create(
            batch=batch, file_extension=file_extension, last_assigned=last_assigned,
        )

    def create_payout_rate(self, rate:Decimal):
        return PayoutRate.objects.create(rate=rate)

    def create_test_annotation(self, s3_image, assigned_annotation):
        return TestAnnotation.objects.create(
            s3_image=s3_image, assigned_annotation=assigned_annotation,
        )

    def create_control_annotation(self, s3_image, data):
        return ControlAnnotation.objects.create(
            s3_image=s3_image, data=data,
        )
