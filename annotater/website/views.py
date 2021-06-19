from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_safe
from django.contrib.auth import login, logout
from django.conf import settings

from website.utils import get_user_from_login_token
from website.constants import WIDGET_NAMES


def landing(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    else:
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
    # Must logout before you can log in.
    if request.user.is_authenticated:
        logout(request)
    login(request, user)
    return redirect("anon-landing")


@require_safe
def logout_page(request):
    logout(request)
    return render(request, "goodbye.html")
