
from typing import BinaryIO
import os.path
from io import BytesIO

from django.conf import settings


class SampleImageService:

    def _get_full_path(self, filename=None) -> str:
        args = ['memetext', 'tests', 'sample_images']
        if filename:
            args.append(filename)
        return os.path.join(settings.BASE_DIR, *args)

    def get_sample_file_as_binary_io(self, file_name) -> BinaryIO:
        with open(self._get_full_path(file_name), "rb") as f:
            fp = BytesIO(f.read())
        fp.seek(0)
        return fp
