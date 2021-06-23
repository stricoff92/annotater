
from typing import BinaryIO, Dict
from io import BytesIO

from django.conf import settings
import boto3


from .abstract import AbstractBackend

boto_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)



class S3Backend(AbstractBackend):

    name = "S3"

    def __init__(self):
        self._boto_client = boto_client


    def _get_boto_client(self):
        return self._boto_client


    def upload_fp(self, fp:BinaryIO, bucket:str, s3_path:str):
        fp.seek(0)
        return self._get_boto_client().upload_fileobj(fp, bucket, s3_path)


    def download_object_to_fp(self, bucket:str, s3_path:str) -> BinaryIO:
        fp = BytesIO()
        self._get_boto_client().download_fileobj(bucket, s3_path, fp)
        return fp


    def delete_objects_with_keys(self, bucket:str, s3_keys:list) -> Dict:
        data = {'Objects':[{'Key': k} for k in s3_keys]}
        return self._get_boto_client().delete_objects(Bucket=bucket, Delete=data)
