from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_safe
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings

from website.utils import get_user_from_login_token
from website.constants import WIDGET_NAMES


@require_safe
@login_required
def landing(request):
    if request.user.userprofile.can_use_widget(WIDGET_NAMES.memetext):
        return redirect("memetext-web-landing")
    else:
        return HttpResponseBadRequest("Error 400: No Assigned Widgets")


@require_safe
def login_with_magic_link(request):
    token = request.GET.get('t')
    if not token:
        return HttpResponseBadRequest()
    user = get_user_from_login_token(token)

    if not user or (not settings.DEBUG and user.is_superuser):
        return HttpResponseBadRequest()
    if not user.userprofile.is_active:
        return HttpResponseBadRequest()

    if request.user.is_authenticated:
        logout(request) # Must logout before you can log in.
    login(request, user)
    return redirect("anon-landing")


@require_safe
@login_required
def logout_page(request):
    logout(request)
    return render(request, "goodbye.html")
