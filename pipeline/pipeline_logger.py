import logging
from pathlib import Path


def show_only_debug(record):
    return record.levelname == "DEBUG"


def setup_logger(level=logging.INFO):
    log_dir = Path("pipeline")
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger("imdb_pipeline")
    logger.setLevel(level)
    if logger.handlers:
        return logger
    formatter = logging.Formatter(
        "{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
    )

    console_handler = logging.StreamHandler()
    # console_handler.setLevel("DEBUG")
    console_handler.setFormatter(formatter)
    # console_handler.addFilter(show_only_debug)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(
        'pipeline/pipeline.log', mode='a', encoding='utf-8')
    # file_handler.setLevel("DEBUG")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger
