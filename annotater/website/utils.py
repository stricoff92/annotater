
from django.conf import settings


def sanitize_token(token: str):
    return "".join(c for c in token if c in settings.ALLOWED_TOKEN_CHARS)

