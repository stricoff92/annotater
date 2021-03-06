
import os.path

from .settings import *

ENV = "TESTING"
DEBUG = True
IS_TEST_ENV = True
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
AUTH_PASSWORD_VALIDATORS = []


# Faster insecure hashing for testing only
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# File Based DB for Faster setup and teardown
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Disable cache based rate throttling
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'


MEMETEXT_S3_BUCKET = "foobar"
AWS_SECRET_ACCESS_KEY = "foobar"
AWS_ACCESS_KEY_ID = "foobar"
