
from typing import Tuple

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q

from memetext.models import AssignedAnnotation, AnnotationBatch, S3Image, ControlAnnotation, TestAnnotation
from memetext.decorators import user_can_use_web_widget
from memetext.services.query import QueryService


@login_required
@user_can_use_web_widget
def landing(request):
    """ View to load the memetext landing page.
    """
    service = QueryService()
    assigned, batch = service.get_assigned_annotation_and_batch_from_user(request.user)
    remaining_annotations = service.remaining_images_user_can_annotate(request.user)

    context = {
        'assignment': assigned,
        'batch': batch,
        'remaining_annotations': remaining_annotations,
        'all_assigned': AssignedAnnotation.objects.filter(user=request.user).order_by("-created_at"),
    }
    return render(request, "landing.html", context)


@login_required
@user_can_use_web_widget
def add_annotation(request):
    """ View to load the page to enter test annotations.
    """
    service = QueryService()
    assigned, batch = service.get_assigned_annotation_and_batch_from_user(request.user)
    remaining_annotations = service.remaining_images_user_can_annotate(request.user)
    if assigned is None:
        return redirect("memetext-web-landing")
    context = {
        "assigned": assigned,
        "batch": batch,
        "remaining_count":remaining_annotations,
    }
    return render(request, "add_annotation.html", context)


@login_required
@user_can_use_web_widget
def add_control_annotation(request):
    """ View to load the page to enter control annotations.
    """
    if not request.user.is_superuser:
        return redirect("memetext-web-landing")

    batch_slug = request.GET.get("batch_slug")
    if not batch_slug:
        batches = AnnotationBatch.objects.order_by("-created_at")
        return render(request, "select_batch.html", {'batches': batches})

    batch = get_object_or_404(AnnotationBatch, slug=batch_slug)
    s3images = S3Image.objects.filter(batch=batch)
    s3_images_with_control = ControlAnnotation.objects.filter(s3_image__batch=batch).values_list("s3_image_id", flat=True)
    s3_images_with_test = TestAnnotation.objects.filter(s3_image__batch=batch).values_list("s3_image_id", flat=True)
    filtered_image_qs = s3images.filter(Q(id__in=s3_images_with_test) & ~Q(id__in=s3_images_with_control))
    found = True
    if not filtered_image_qs.exists():
        filtered_image_qs = s3images.filter(~Q(id__in=s3_images_with_control))
        if not filtered_image_qs.exists():
            target_s3_image = None
            found = False
    if found:
        target_s3_image = filtered_image_qs.order_by("created_at").first()

    context = {
        's3_image':target_s3_image,
    }
    return render(request, "add_control_annotation.html", context)
