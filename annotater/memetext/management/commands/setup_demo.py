
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
from memetext.services.storage_backend import get_backend_class
from memetext.models import AnnotationBatch, AssignedAnnotation, S3Image, PayoutRate



class Command(BaseCommand):


    def add_arguments(self, parser):
        parser.add_argument('username', type=str) # Demo user username
        parser.add_argument('batch', type=str)    # Name of the batch!

    @transaction.atomic
    def handle(self, *args, **kwargs):
        DEMO_INSTRUCTIONS = """
            <p>Look at the image surrounded by red lines. Type the text you see <i>exactly how you would read it</i>. Ordering of words matters.</p>
            <p>If you are not sure of the ordering, simply type how you would naturally read the image to understand it: Left to right, top to bottom. If there is no text in the image: leave the text box empty and click submit.</p>
            <p>Do not include watermarks or insignificant text.<p>
            <hr>
            <h3>Example 1</h3>
            <div><img src="/static/example1.jpg" style="border:5px dashed #ff9191; max-width:80vw; max-height:80vh;"></div>
            <div class="alert alert-secondary mt-2 p-1">
            <strong>Text From the Image</strong><br>
            Dog owners: What breed is that, Husky? No! That's an Alaskan Malamute!!! Cat Owners: Hey What breed is he? Cat.
            </div>
        """
        DEMO_INSTRUCTIONS_EXPANDED = """
            <hr>
            <h3>Example 1</h3>
            <div><img src="/static/example1.jpg" style="border:5px dashed #ff9191; max-width:80vw; max-height:80vh;"></div>
            <div class="alert alert-secondary mt-2 p-1">
            <strong>Text From the Image</strong><br>
            Dog owners: What breed is that, Husky? No! That's an Alaskan Malamute!!! Cat Owners: Hey What breed is he? Cat.
            </div>
        """
        BATCH_MESSAGE = """
            <h2><strong>😺 MEMES!</strong></h2>
            <p>
            Thanks for helping! Your task is to read memes from the internet and type the text you see.
            </p>
            <p>
            See <strong>Instructions</strong> on the next page for details.
            </p>
        """


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
            batch_message=BATCH_MESSAGE,
            instructions=DEMO_INSTRUCTIONS,
            instructions_expanded=DEMO_INSTRUCTIONS_EXPANDED,
            is_demo=True,
        )
        payout_rate, _ = PayoutRate.objects.get_or_create(rate=Decimal("0.1"))

        file_names = ["sample1.jpg", "sample2.jpg", "sample3.jpg", "sample4.jpg", "sample5.jpg"]
        sis = SampleImageService()
        fps = [sis.get_sample_file_as_binary_io(n) for n in file_names]

        storage_service = get_backend_class()()
        for fp, file_name in zip(fps, file_names):
            print(f" {storage_service.name}: Uploading {file_name} to bucket {settings.MEMETEXT_S3_BUCKET} 📡")
            new_img = S3Image.objects.create(
                batch=new_batch,
                file_extension="jpg",
                is_demo=True,
            )
            storage_service.upload_fp(fp, settings.MEMETEXT_S3_BUCKET, new_img.s3_path)

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
