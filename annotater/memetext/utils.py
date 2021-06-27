
import logging

from annotater.script_logger import spawn_logger


def get_annotation_logger(level=logging.INFO):
    return spawn_logger("testannotation", level=level, file_per_day=True)
