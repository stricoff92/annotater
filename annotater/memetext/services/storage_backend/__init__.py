

from django.conf import settings

from .filebased import FileBackend
from .s3 import S3Backend


DEFAULT_CLASS = FileBackend


def get_backend_class():
    if settings.FILE_STORAGE_BACKEND == "s3":
        return S3Backend
    elif settings.FILE_STORAGE_BACKEND == "file":
        return FileBackend
    else:
        return DEFAULT_CLASS

