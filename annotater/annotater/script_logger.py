
import logging
import os
import os.path
import string
import sys
import uuid


from django.conf import settings
from django.utils import timezone


# add level SILLY (5) which is 1 notch more verbose than level DEBUG (10)
LOG_LEVEL_SILLY = 5
logging.addLevelName(LOG_LEVEL_SILLY, "SILLY")
def _silly(self, message:str, *args, **kwargs):
    if self.isEnabledFor(LOG_LEVEL_SILLY):
        # Logger takes its '*args' as 'args'.
        self._log(LOG_LEVEL_SILLY, message, args, **kwargs)
logging.Logger.silly = _silly


def _get_log_dir_path():
    return os.path.join(settings.BASE_DIR, "logs")


def _clean_context_for_file_name(name:str) -> str:
    allowed_chars = string.digits + string.ascii_letters
    return "".join(c if c in allowed_chars else "" for c in name)


class FileHandlerFactory:
    @staticmethod
    def create(*a, **k):
        return logging.FileHandler(*a, **k)


def spawn_logger(context:str, uid=None, level=logging.DEBUG, formating="%(asctime)s - %(levelname)s - %(message)s", stdout_fh=False, stdout_only=False):
    if stdout_only and not stdout_fh:
        raise ValueError

    attach_file_handler = not stdout_only
    cleaned_context = _clean_context_for_file_name(context)
    uid = uid or uuid.uuid4().hex
    now = timezone.now().strftime("%Y%m%dT%H%M%S")
    file_name = f"{now}-{cleaned_context}.log"
    full_log_file_path = os.path.join(_get_log_dir_path(), file_name)

    logger_name = f"{cleaned_context}-{uid}"
    logger = logging.getLogger(logger_name)
    logger.handlers = []
    logger.setLevel(level)

    handler_formatter = logging.Formatter(formating)
    if attach_file_handler:
        file_handler = FileHandlerFactory.create(full_log_file_path)
        file_handler.setFormatter(handler_formatter)
        logger.addHandler(file_handler)

    if stdout_fh:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(handler_formatter)
        logger.addHandler(stream_handler)

    return logger

def spawn_stdout_logger(level=logging.DEBUG, formating="%(asctime)s - %(levelname)s - %(message)s"):
    return spawn_logger(
        "stdout-logger", level=level, formating=formating, stdout_fh=True, stdout_only=True,
    )

def spawn_dummy_logger():
    logger = logging.getLogger('dummy_logger')
    logger.handlers = []
    logger.setLevel(1000)
    logger.addHandler(logging.NullHandler())
    return logger
