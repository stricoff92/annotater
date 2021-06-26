

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings
from botocore.exceptions import ClientError

from memetext.services.sample_image import SampleImageService
from memetext.services.storage_backend import get_backend_class
from memetext.models import AnnotationBatch, AssignedAnnotation, S3Image, TestAnnotation, ControlAnnotation


class UserDidNotConfirm(Exception):
    pass


class Command(BaseCommand):

    def confirm_y_n(self, text="press Y to continue, any other key to quit"):
        val = input(text + " ")
        if val.strip().lower() != "y":
            raise UserDidNotConfirm("user did not confirm, entered key " + val)


    def add_arguments(self, parser):
        parser.add_argument('batch', type=str)    # Name of the batch!

    def handle(self, *args, **kwargs):
        batch_slug = kwargs['batch']
        batch = AnnotationBatch.objects.get(slug=batch_slug)
        print("deleting batch " + batch.name)

        s3_images = S3Image.objects.filter(batch=batch)
        test_annotations = TestAnnotation.objects.filter(s3_image__in=s3_images)
        control_annotations = ControlAnnotation.objects.filter(s3_image__in=s3_images)
        assigned_annotations = AssignedAnnotation.objects.filter(batch=batch)

        print("you are about to delete the following items")
        print(s3_images.count(), "s3 images")
        print(test_annotations.count(), "test annotations")
        print(control_annotations.count(), "control annotations")
        print(assigned_annotations.count(), "assigned annotations")
        self.confirm_y_n()

        keys_to_delete = []
        keys_to_delete += [ta.s3_path for ta in test_annotations]
        keys_to_delete += [s3i.s3_path for s3i in s3_images]
        storage_service = get_backend_class()()
        try:
            resp = storage_service.delete_objects_with_keys(settings.MEMETEXT_S3_BUCKET, keys_to_delete)
        except (ClientError, FileNotFoundError) as e:
            print(f"\n ⚠️  {storage_service.name} Error  ⚠️")
            print(e, "\n")
        else:
            print("*  ✅  deleted", len(keys_to_delete), f"keys from {storage_service.name}" , f"RESPONSE FROM {storage_service.name} * * * * * * * *")
            print(resp)
            print("* * * * * * * * * * * * * * * * * * * * * * * * \n")


        with transaction.atomic():
            print("deleting objects from the DB")
            deleted_test_annotations = test_annotations.delete()
            deleted_control_annotations = control_annotations.delete()
            deleted_s3_image_records = s3_images.delete()
            deleted_assigned_annotation = assigned_annotations.delete()
            deleted_batch = batch.delete()

        print("deleted_test_annotations", deleted_test_annotations)
        print("deleted_control_annotations", deleted_control_annotations)
        print("deleted_s3_image_records", deleted_s3_image_records)
        print("deleted_assigned_annotation", deleted_assigned_annotation)
        print("deleted_batch", deleted_batch)
        print("* * * * * * * * * * * * * * * * * * * * * * * * ")
        print("\n 🌟 🌟 🌟  SUCCESS 🌟 🌟 🌟 \n")
