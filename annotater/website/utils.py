
import datetime as dt
from functools import wraps
from base64 import b32encode
from binascii import unhexlify

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


def get_login_token(user):
    claims = {
        "userprofile_id":user.userprofile.id,
        "created_at":timezone.now().isoformat(),
        "expires_at": (timezone.now() + dt.timedelta(days=7)).isoformat(),
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


def set_tfa_qr_session_key(function):
    @wraps(function)
    def decorated_function(request, *args, **kwargs):
        if user_has_device(request.user):
            return HttpResponse(status=status.HTTP_409_CONFLICT)

        key = random_hex(20)
        rawkey = unhexlify(key.encode('ascii'))
        b32key = b32encode(rawkey).decode('utf-8')
        request.session[settings.TFA_QR_SESSION_SECRET_KEY] = b32key
        request.session[settings.TFA_QR_SESSION_SECRET_KEY_HEX] = key
        return function(request, *args, **kwargs)

    return decorated_function
