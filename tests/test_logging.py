import io
import logging

from app.core.logging import configure_logging


def test_configured_level_applies_with_an_existing_handler(monkeypatch):
    output = io.StringIO()
    handler = logging.StreamHandler(output)
    root = logging.getLogger()
    loggers = [root, logging.getLogger("httpx"), logging.getLogger("httpcore")]
    previous_levels = [logger.level for logger in loggers]
    monkeypatch.setattr(root, "handlers", [handler])
    try:
        root.setLevel(logging.ERROR)
        configure_logging("INFO")
        root.info("configured info")
        root.debug("hidden debug")
        configure_logging("ERROR")
        root.info("hidden info")
        root.error("configured error")

        assert output.getvalue().splitlines() == ["configured info", "configured error"]
    finally:
        for logger, previous_level in zip(loggers, previous_levels, strict=True):
            logger.setLevel(previous_level)
        handler.close()
