
from django.conf import settings
import boto3


boto_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)



class S3Service:
    def __init__(self):
        self._boto_client = boto_client


    def _get_boto_client(self):
        return self._boto_client
