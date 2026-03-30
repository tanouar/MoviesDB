"""Tests unitaires pour pipeline/pipeline_logger.py."""
import logging
import sys
from pathlib import Path

import pytest

# Ajout du dossier pipeline au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))

from pipeline_logger import setup_logger, show_only_debug  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture : réinitialiser le logger entre chaque test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_logger():
    """Supprime tous les handlers du logger avant chaque test."""
    logger = logging.getLogger("imdb_pipeline")
    logger.handlers.clear()
    yield
    logger.handlers.clear()


# ---------------------------------------------------------------------------
# show_only_debug
# ---------------------------------------------------------------------------

class TestShowOnlyDebug:
    def _make_record(self, level_name):
        record = logging.LogRecord(
            name="test",
            level=getattr(logging, level_name),
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        return record

    def test_accepts_debug(self):
        assert show_only_debug(self._make_record("DEBUG")) is True

    def test_rejects_info(self):
        assert show_only_debug(self._make_record("INFO")) is False

    def test_rejects_warning(self):
        assert show_only_debug(self._make_record("WARNING")) is False

    def test_rejects_error(self):
        assert show_only_debug(self._make_record("ERROR")) is False

    def test_rejects_critical(self):
        assert show_only_debug(self._make_record("CRITICAL")) is False


# ---------------------------------------------------------------------------
# setup_logger
# ---------------------------------------------------------------------------

class TestSetupLogger:
    def test_returns_logger(self):
        logger = setup_logger()
        assert isinstance(logger, logging.Logger)

    def test_logger_name(self):
        logger = setup_logger()
        assert logger.name == "imdb_pipeline"

    def test_default_level_is_info(self):
        logger = setup_logger()
        assert logger.level == logging.INFO

    def test_custom_level_debug(self):
        logger = setup_logger(level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_has_two_handlers(self):
        """Doit avoir un StreamHandler + un FileHandler."""
        logger = setup_logger()
        assert len(logger.handlers) == 2

    def test_has_stream_handler(self):
        logger = setup_logger()
        types = [type(h) for h in logger.handlers]
        assert logging.StreamHandler in types

    def test_has_file_handler(self):
        logger = setup_logger()
        types = [type(h) for h in logger.handlers]
        assert logging.FileHandler in types

    def test_idempotent_second_call(self):
        """Appeler setup_logger deux fois ne doit pas dupliquer les handlers."""
        setup_logger()
        logger = setup_logger()
        assert len(logger.handlers) == 2

    def test_propagate_is_false(self):
        logger = setup_logger()
        assert logger.propagate is False

    def test_log_file_created(self, tmp_path, monkeypatch):
        """Le fichier de log doit être créé dans pipeline/."""
        monkeypatch.chdir(tmp_path)
        logger = setup_logger()
        logger.info("test message")
        assert (tmp_path / "pipeline" / "pipeline.log").exists()

    def test_log_file_contains_message(self, tmp_path, monkeypatch):
        """Les messages loggués doivent apparaître dans le fichier."""
        monkeypatch.chdir(tmp_path)
        logger = setup_logger()
        logger.info("message de test pipeline")
        log_content = (
            tmp_path / "pipeline" / "pipeline.log"
        ).read_text(encoding="utf-8")
        assert "message de test pipeline" in log_content
