
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
from memetext.models import AnnotationBatch, AssignedAnnotation, S3Image, PayoutRate


class Command(BaseCommand):


    def add_arguments(self, parser):
        parser.add_argument('username', type=str) # Demo user username
        parser.add_argument('batch', type=str)    # Name of the batch!

    @transaction.atomic
    def handle(self, *args, **kwargs):
        print("\n Adding Database Objects")
        # setup new user
        pw_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()"
        User = get_user_model()
        new_user = User.objects.create_user(
            username=kwargs['username'],
            password="".join(choice(pw_chars) for _ in range(16)),
        )
        profile = UserProfile.objects.create(user=new_user, assigned_widgets=WIDGET_NAMES.memetext, is_demo=True)
        new_batch = AnnotationBatch.objects.create(
            name=kwargs['batch'],
            batch_message="""<h2><strong>😺 MEMES!</strong></h2><h4 style="color:red"><strong><i>READ THIS BEFORE STARTING</i></strong></h4>""",
            instructions="write the text you seee",
            is_demo=True,
        )
        payout_rate, _ = PayoutRate.objects.get_or_create(rate=Decimal("0.1"))

        file_names = ["sample1.jpg", "sample2.jpg", "sample3.jpg", "sample4.jpg", "sample5.jpg"]
        sis = SampleImageService()
        fps = [sis.get_sample_file_as_binary_io(n) for n in file_names]

        s3service = S3Service()
        for fp, file_name in zip(fps, file_names):
            print(f" S3: Uploading {file_name} to bucket {settings.MEMETEXT_S3_BUCKET} 📡")
            new_img = S3Image.objects.create(
                batch=new_batch,
                file_extension="jpg",
                is_demo=True,
            )
            s3service.upload_fp(fp, settings.MEMETEXT_S3_BUCKET, new_img.s3_path)

        new_assigned_annotation = AssignedAnnotation.objects.create(
            user=new_user,
            batch=new_batch,
            payout_rate=payout_rate,
            assigned_count=len(file_names),
            is_active=True,
            is_demo=True
        )


        login_url = get_log_url_for_user(new_user)
        print(f"\n\n* * * * * login link for {new_user.username} * * * * *\n\n")
        print(login_url)
        print("\n\n* * * * * * * * * * * * * * * * * *")
        print("🌟 🌟 🌟  SUCCESS 🌟 🌟 🌟 \n")
