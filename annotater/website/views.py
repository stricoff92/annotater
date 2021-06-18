from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_safe
from django.contrib.auth import login, logout

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
    if request.user.is_authenticated:
        return redirect("anon-landing")

    token = request.GET.get('t')
    if not token:
        return HttpResponseBadRequest()
    user = get_user_from_login_token(token)
    if not user or user.is_superuser:
        return HttpResponseBadRequest()
    login(request, user)
    return redirect("anon-landing")


@require_safe
def logout_page(request):
    logout(request)
    return render(request, "goodbye.html")
