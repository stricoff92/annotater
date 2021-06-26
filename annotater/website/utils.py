
import datetime as dt
import os.path

from dateutil import parser as datetime_parser
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import HttpResponse
from django_otp.util import random_hex
from django_otp import user_has_device
from rest_framework import status
import jwt



def get_tmp_file_dir(filename: str=None) -> str:
    args = ['tmp']
    if filename:
        args.append(filename)
    return os.path.join(settings.BASE_DIR, *args)


def get_login_token(user):
    claims = {
        "userprofile_id":user.userprofile.id,
        "created_at":timezone.now().isoformat(),
        "expires_at": (timezone.now() + dt.timedelta(days=45)).isoformat(),
    }
    return jwt.encode(claims, settings.SECRET_KEY, "HS256")

def get_user_from_login_token(token: str):
    try:
        claims = jwt.decode(token.encode(), settings.SECRET_KEY, "HS256")
        if datetime_parser.parse(claims['expires_at']) < timezone.now():
            return None
        if datetime_parser.parse(claims['created_at']) > timezone.now():
            return None
        return get_user_model().objects.get(userprofile__id=claims['userprofile_id'])
    except Exception:
        return None


def get_log_url_for_user(user) -> str:
    token = get_login_token(user)
    url = settings.ABSOLUTE_BASE_URL + reverse("anon-login-with-link") + f"?t={token}"
    return url
