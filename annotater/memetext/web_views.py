
import csv
import json
import random
from typing import Tuple

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q
from django.urls import reverse
import Levenshtein

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
        "skip_instructions": request.GET.get("skip_instructions") is not None,
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
    base_url = reverse('memetext-web-add-control-annotation')
    if not batch_slug:
        batches = AnnotationBatch.objects.order_by("-created_at")
        return render(
            request,
            "select_batch.html",
            {'batches': batches, 'base_url':base_url, 'page_title':'NewControl Annotation: Select a Batch'}
        )

    batch = get_object_or_404(AnnotationBatch, slug=batch_slug)
    s3images = S3Image.objects.filter(batch=batch)
    s3_images_with_control = ControlAnnotation.objects.filter(s3_image__batch=batch).values_list("s3_image_id", flat=True)
    s3_images_with_test = TestAnnotation.objects.filter(s3_image__batch=batch).values_list("s3_image_id", flat=True)
    filtered_image_qs = s3images.filter(Q(id__in=s3_images_with_test) & ~Q(id__in=s3_images_with_control))
    found = True
    # TODO: test this logic
    if not filtered_image_qs.exists():
        filtered_image_qs = s3images.filter(~Q(id__in=s3_images_with_control))
        if not filtered_image_qs.exists():
            target_s3_image = None
            found = False
    if found:
        pool = filtered_image_qs.order_by("created_at")
        count = pool.count()
        if count:
            target_s3_image = pool[random.randint(0, count - 1)]
        else:
            target_s3_image = None

    context = {
        's3_image':target_s3_image,
    }
    return render(request, "add_control_annotation.html", context)


@login_required
@user_can_use_web_widget
def view_annotation_audit(request):
    if not request.user.is_superuser:
        return redirect("memetext-web-landing")

    batch_slug = request.GET.get("batch_slug")
    base_url = reverse('memetext-annotation-audit')
    if not batch_slug:
        batches = AnnotationBatch.objects.order_by("-created_at")
        return render(
            request,
            "select_batch.html",
            {'batches': batches, 'base_url':base_url, 'page_title':'Annotation Audit Report: Select a Batch'}
        )

    query_service = QueryService()
    batch = get_object_or_404(AnnotationBatch, slug=batch_slug)
    s3_images = S3Image.objects.filter(batch=batch)
    test_annotations = TestAnnotation.objects.filter(s3_image__in=s3_images)
    control_annotations = ControlAnnotation.objects.filter(s3_image__in=s3_images)

    overlapping_s3_ids = set(s3_images.values_list("id", flat=True))
    overlapping_s3_ids = overlapping_s3_ids.intersection(set(test_annotations.values_list("s3_image_id", flat=True)))
    overlapping_s3_ids = overlapping_s3_ids.intersection(set(control_annotations.values_list("s3_image_id", flat=True)))

    s3_images = s3_images.filter(id__in=overlapping_s3_ids)
    test_annotations = test_annotations.filter(s3_image__in=s3_images)
    control_annotations = control_annotations.filter(s3_image__in=s3_images)

    s3_image_id_to_control_annotation_map = {}
    for ca in control_annotations:
        s3_image_id_to_control_annotation_map[ca.s3_image_id] = ca

    def _sanitize(s):
        return s.lower().replace(" ", "")

    report_rows = []
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="audit-{batch.name}.csv"'},
    )
    writer = csv.writer(response)
    writer.writerow([
        "user", "image_slug", "time", "test text", "control text", "raw ratio", "clean ratio"
    ])
    for test_annotation in test_annotations.values(
        "assigned_annotation__user__username", "s3_image_id", "s3_image__slug", "data", "created_at"
    ):
        username = test_annotation['assigned_annotation__user__username']
        test_text = json.loads(test_annotation['data'])['data'] if test_annotation['data'] else ""
        s3_image_id = test_annotation['s3_image_id']
        s3_image_slug = test_annotation['s3_image__slug']
        control_annotation = s3_image_id_to_control_annotation_map[s3_image_id]
        control_text = control_annotation.get_data().get("data", "")
        raw_ratio = Levenshtein.ratio(control_text, test_text)
        sanitized_ratio = Levenshtein.ratio(_sanitize(control_text), _sanitize(test_text))

        writer.writerow([
            username,
            s3_image_slug,
            test_annotation['created_at'].replace(microsecond=0).isoformat(),
            repr(test_text),
            repr(control_text),
            raw_ratio,
            sanitized_ratio,
        ])

    return response
