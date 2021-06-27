
from abc import ABC, abstractmethod
from typing import BinaryIO, Any


class AbstractBackend(ABC):

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def upload_fp(self, fp:BinaryIO, bucket:str, s3_path:str):
        pass

    @abstractmethod
    def download_object_to_fp(self, bucket:str, s3_path:str) -> BinaryIO:
        pass


    @abstractmethod
    def delete_objects_with_keys(self, bucket:str, s3_keys:list) -> Any:
        pass
