
import datetime as dt
from io import BytesIO

from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import (
    IsAuthenticated,
    IsAdminUser,
)

from memetext.decorators import user_can_use_api_widget as user_can_use_memetext_api_widget
from memetext.forms import NewTestAnnotation
from memetext.models import S3Image, TestAnnotation
from memetext.renderers import JPGRenderer
from memetext.services.s3 import S3Service
from website.utils import sanitize_token


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@user_can_use_memetext_api_widget
def get_image_to_annotate(request, assignment_slug:str):
    empty_response = {
        "load_image_token": None,
        "annotate_image_token": None,
        "url": None,
    }
    user = request.user
    assignment = get_object_or_404(
        user.assignedannotation_set.filter(is_active=True),
        slug=assignment_slug,
    )
    if assignment.is_complete:
        return Response(
            empty_response, status.HTTP_204_NO_CONTENT)

    assigned_item = None
    assigned_item_slug = user.userprofile.assigned_item
    if assigned_item_slug is not None:
        s3image = S3Image.objects.filter(slug=assigned_item_slug).first()
        if s3image is None:
            user.userprofile.assigned_item = None
            user.userprofile.save()
            assigned_item = None
        elif s3image.testannotation_set.exists():
            user.userprofile.assigned_item = None
            user.userprofile.save()
            assigned_item = None
        else:
            assigned_item = s3image

    new = False
    if assigned_item is None:
        five_mins_ago = timezone.now() - dt.timedelta(minutes=5)
        s3image_ids_with_test_annotations = (TestAnnotation.objects
            .filter(s3_image__batch=assignment.batch)
            .values_list("s3_image_id", flat=True))
        assigned_item = S3Image.objects.filter(
            Q(batch=assignment.batch)
            & (Q(last_assigned__isnull=True) | Q(last_assigned__lt=five_mins_ago))
            & ~Q(id__in=s3image_ids_with_test_annotations)
        ).first()
        new = True

    if assigned_item is not None:
        if new:
            user.userprofile.assigned_item = assigned_item.slug
            user.userprofile.save()

        assigned_item.last_assigned = timezone.now()
        assigned_item.save(update_fields=['last_assigned'])
        load_image_token = assigned_item.get_load_image_token()
        return Response(
            {
                "load_image_token": load_image_token,
                "annotate_image_token": assigned_item.get_annotate_image_token(load_image_token),
                "url": assigned_item.get_download_image_url(assignment.slug),
            },
            status.HTTP_200_OK,
        )

    else:
        return Response(
            empty_response, status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@user_can_use_memetext_api_widget
@renderer_classes([JPGRenderer])
def download_image(request, assignment_slug:str, image_slug:str):
    nowtz = timezone.now()
    user = request.user
    assignment = get_object_or_404(
        user.assignedannotation_set.filter(is_active=True),
        slug=assignment_slug,
    )
    if assignment.is_complete:
        return Response(b"", status.HTTP_400_BAD_REQUEST)

    s3image = get_object_or_404(
        S3Image.objects.filter(batch=assignment.batch),
        slug=image_slug)

    if s3image.slug != user.userprofile.assigned_item:
        return Response(b"", status.HTTP_400_BAD_REQUEST)

    if not s3image.load_image_token_is_valid(
        sanitize_token(request.GET.get("load_image_token")),
        nowtz=nowtz,
    ):
        return Response(b"", status.HTTP_400_BAD_REQUEST)
    else:
        service = S3Service()
        fp = service.download_object_to_fp(
            settings.MEMETEXT_S3_BUCKET,
            s3image.s3_path,
        )
        response = Response(fp.getvalue(), status.HTTP_200_OK)
        response['Cache-Control'] = 'no-store'
        return response
