
from typing import Tuple

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from memetext.models import AssignedAnnotation
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
    """ View to load the page to enter test and control annotations.
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
