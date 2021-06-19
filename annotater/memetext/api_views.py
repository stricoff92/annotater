
import datetime as dt
from io import BytesIO
import json

from django.conf import settings
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
from botocore.exceptions import ClientError

from memetext.decorators import user_can_use_api_widget as user_can_use_memetext_api_widget
from memetext.forms import NewTestAnnotation, NewControlAnnotation
from memetext.models import S3Image, TestAnnotation, ControlAnnotation, AnnotationBatch
from memetext.renderers import JPGRenderer
from memetext.services.s3 import S3Service
from memetext.services.query import QueryService


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
                "image_slug":assigned_item.slug,
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
        request.GET.get("t"),
        nowtz=nowtz,
    ):
        return Response(b"", status.HTTP_400_BAD_REQUEST)
    else:
        service = S3Service()
        try:
            fp = service.download_object_to_fp(
                settings.MEMETEXT_S3_BUCKET,
                s3image.s3_path,
            )
        except ClientError as e:
            if "404" in str(e):
                return Response(b"", status.HTTP_404_NOT_FOUND)
            else:
                raise

        response = Response(fp.getvalue(), status.HTTP_200_OK)
        response['Cache-Control'] = 'no-store'
        return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@user_can_use_memetext_api_widget
def add_test_annotation(request):
    form = NewTestAnnotation(request.data)
    if not form.is_valid():
        return Response(form.errors.as_json(), status.HTTP_400_BAD_REQUEST)

    text = form.cleaned_data['text']
    image_slug = form.cleaned_data['image_slug']
    annotate_image_token = form.cleaned_data['annotate_image_token']
    load_image_token = form.cleaned_data['load_image_token']

    query_service = QueryService()
    assigned_annotation, batch = query_service.get_assigned_annotation_and_batch_from_user(
        request.user)
    if not assigned_annotation:
        return Response(
            "No assignment.",
            status.HTTP_400_BAD_REQUEST)

    s3image = get_object_or_404(S3Image, slug=image_slug, batch=batch)

    if not s3image.annotate_image_token_is_valid(
        annotate_image_token,
        load_image_token,
    ):
        return Response(
            "Tokens are not valid.",
            status.HTTP_400_BAD_REQUEST)

    if request.user.userprofile.assigned_item != image_slug:
        return Response(
            "Image not assigned.",
            status.HTTP_400_BAD_REQUEST)


    s3_service = S3Service()
    test_annotation = TestAnnotation.objects.create(
        s3_image=s3image,
        assigned_annotation=assigned_annotation,
        data=json.dumps({"data":text}),
    )
    fp = BytesIO(bytes(json.dumps({"data":text}).encode()))
    try:
        s3_service.upload_fp(
            fp, settings.MEMETEXT_S3_BUCKET, test_annotation.s3_path)
    except Exception as e:
        test_annotation.delete()
        print("ERROR", e)
        return Response({}, status.HTTP_502_BAD_GATEWAY)
    else:
        request.user.userprofile.assigned_item = None
        request.user.userprofile.save(update_fields=['assigned_item'])
        return Response({"rate":assigned_annotation.payout_rate.rate}, status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAdminUser])
@user_can_use_memetext_api_widget
def add_control_annotation(request):
    form = NewControlAnnotation(request.data)

    if not form.is_valid():
        return Response(form.errors.as_json(), status.HTTP_400_BAD_REQUEST)

    text = form.cleaned_data['text']
    image_slug = form.cleaned_data['image_slug']
    s3image = get_object_or_404(S3Image, slug=image_slug)

    try:
        if s3image.controlannotation is not None:
            return Response(form.errors.as_json(), status.HTTP_409_CONFLICT)
    except ControlAnnotation.DoesNotExist:
        pass

    ControlAnnotation.objects.create(
        s3_image=s3image,
        data=json.dumps({'data':text})
    )
    return Response({}, status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
@user_can_use_memetext_api_widget
@renderer_classes([JPGRenderer])
def admin_download_image(request, image_slug: str):
    s3image = get_object_or_404(S3Image, slug=image_slug)
    service = S3Service()
    try:
        fp = service.download_object_to_fp(
            settings.MEMETEXT_S3_BUCKET,
            s3image.s3_path,
        )
    except ClientError as e:
        if "404" in str(e):
            return Response(b"", status.HTTP_404_NOT_FOUND)
        else:
            raise

    response = Response(fp.getvalue(), status.HTTP_200_OK)
    response['Cache-Control'] = 'no-store'
    return response
