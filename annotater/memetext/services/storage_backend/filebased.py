
from io import StringIO, BytesIO
import hashlib
import os.path
from typing import BinaryIO, Any, List

from django.conf import settings

from .abstract import AbstractBackend




class FileBackend(AbstractBackend):

    name = "tmp/"

    def _hash_path(self, path: str) -> str:
        return hashlib.md5(path.encode()).hexdigest()

    def _get_full_path(self, filename: str):
        return os.path.join(settings.BASE_DIR, "tmp", filename)

    def upload_fp(self, fp:BinaryIO, bucket:str, s3_path:str):
        ext = s3_path.split(".")[-1]
        hashed_path = self._hash_path(bucket + s3_path)
        full_path = self._get_full_path(f"{hashed_path}.{ext}")
        with open(full_path, 'wb') as f:
            f.write(fp.read())


    def download_object_to_fp(self, bucket:str, s3_path:str) -> BinaryIO:
        ext = s3_path.split(".")[-1]
        hashed_path = self._hash_path(bucket + s3_path)
        full_path = self._get_full_path(f"{hashed_path}.{ext}")
        data = BytesIO()
        with open(full_path, 'rb') as f:
            data.write(f.read())
        data.seek(0)
        return data



    def delete_objects_with_keys(self, bucket:str, s3_keys:list) -> List[str]:
        file_paths = []
        for key in s3_keys:
            ext = key.split(".")[-1]
            hashed_path = self._hash_path(bucket + key)
            full_path = self._get_full_path(f"{hashed_path}.{ext}")
            if not os.path.exists(full_path):
                raise FileNotFoundError
            else:
                file_paths.append(full_path)
        for p in file_paths:
            os.remove(p)
        return [v.split("/")[-1] for v in file_paths]
