import logging
import time
from pathlib import Path


def show_only_debug(record):
    return record.levelname == "DEBUG"


def setup_logger(level=logging.INFO):
    log_dir = Path("pipeline")
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger("imdb_pipeline")
    logger.setLevel(level)

    formatter = logging.Formatter(
        "{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
    )
    has_console = any(
        type(h) is logging.StreamHandler for h in logger.handlers
    )
    if not has_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    has_file = any(
        isinstance(h, logging.FileHandler) for h in logger.handlers
    )
    if not has_file:
        log_file = "pipeline/pipeline.log"
        file_handler = logging.FileHandler(
            log_file, mode='a', encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger
