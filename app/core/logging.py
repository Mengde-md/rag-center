import logging


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # basicConfig is a no-op when the root logger already has handlers.
    root = logging.getLogger()
    root.setLevel(level)
    # Provider requests may contain credentials in URLs; do not log them.
    http_level = max(root.level, logging.WARNING)
    logging.getLogger("httpx").setLevel(http_level)
    logging.getLogger("httpcore").setLevel(http_level)
