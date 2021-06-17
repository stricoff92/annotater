
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from memetext.models import AssignedAnnotation

@login_required
def landing(request):
    assigned = AssignedAnnotation.objects.filter(user=request.user, is_active=True)
    has_assigned = assigned.exists() and any(not a.is_complete for a in assigned)
    context = {
        'has_assigned': has_assigned,
        'all_assigned': AssignedAnnotation.objects.filter(user=request.user).order_by("-created_at")
    }
    return render(request, "landing", context)


@login_required
def add_annotation(request):
    is_admin = request.user.is_superuser
    adding_control_annotation = is_admin and bool(request.GET.get("control"))
    context = {
        "is_control": adding_control_annotation,
    }
    return render(request, "add_annotation", context)
