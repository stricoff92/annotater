
from functools import wraps

from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status

from website.constants import WIDGET_NAMES


def user_can_use_web_widget(function):
    @wraps(function)
    def decorator(request, *a, **k):
        if request.user.userprofile.can_use_widget(WIDGET_NAMES.memetext):
            return function(request, *a, **k)
        else:
            return HttpResponse(
                "<h1>ERROR 401: No access to this widget.</h1>",
                status=status.HTTP_401_UNAUTHORIZED,
            )
    return decorator


def user_can_use_api_widget(function):
    @wraps(function)
    def decorator(request, *a, **k):
        if request.user.userprofile.can_use_widget(WIDGET_NAMES.memetext):
            return function(request, *a, **k)
        else:
            return Response(
                "no access to this widget",
                status.HTTP_401_UNAUTHORIZED,
            )
    return decorator
