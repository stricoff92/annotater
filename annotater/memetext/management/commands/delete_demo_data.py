
from secrets import choice
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings

from website.utils import get_log_url_for_user
from website.models import UserProfile
from website.constants import WIDGET_NAMES
from memetext.services.sample_image import SampleImageService
from memetext.services.s3 import S3Service
from memetext.models import AnnotationBatch, AssignedAnnotation, S3Image, PayoutRate, TestAnnotation


class Command(BaseCommand):


    # @transaction.atomic
    def handle(self, *args, **kwargs):
        # query items from the DB.
        demo_batches = AnnotationBatch.objects.filter(is_demo=True)
        demo_s3_images = S3Image.objects.filter(is_demo=True)
        demo_test_annotations = TestAnnotation.objects.filter(s3_image__in=demo_s3_images)
        demo_assigned_annotations = AssignedAnnotation.objects.filter(is_demo=True)
        demo_user_profiles = UserProfile.objects.filter(is_demo=True)
        demo_user_ids = demo_user_profiles.values_list("user_id", flat=True)

        # delete items from S3.
        s3service = S3Service()
        keys_to_delete = []
        keys_to_delete += [ta.s3_path for ta in demo_test_annotations]
        keys_to_delete += [s3i.s3_path for s3i in demo_s3_images]
        resp = s3service.delete_objects_with_keys(settings.MEMETEXT_S3_BUCKET, keys_to_delete)
        print("deleting", len(keys_to_delete), "keys from S3")
        print("* * * * * * * * RESPONSE FROM S3 * * * * * * * *")
        print(resp)
        print("* * * * * * * * * * * * * * * * * * * * * * * * ")

        # delete items from the DB.
        print("deleting objects from the DB")
        deleted_test_annotations = demo_test_annotations.delete()
        deleted_s3_image_records = demo_s3_images.delete()
        deleted_assigned_annotation = demo_assigned_annotations.delete()
        deleted_demo_batches = demo_batches.delete()
        deleted_user_profiles = demo_user_profiles.delete()
        deleted_users = get_user_model().objects.filter(id__in=demo_user_ids).delete()

        print("deleted_test_annotations", deleted_test_annotations)
        print("deleted_s3_image_records", deleted_s3_image_records)
        print("deleted_assigned_annotation", deleted_assigned_annotation)
        print("deleted_demo_batches", deleted_demo_batches)
        print("deleted_user_profiles", deleted_user_profiles)
        print("deleted_users", deleted_users)
        print("* * * * * * * * * * * * * * * * * * * * * * * * ")
        print(" SUCCESS! ")
