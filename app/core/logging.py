import logging


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # basicConfig is a no-op when the root logger already has handlers.
    logging.getLogger().setLevel(level)
    # Provider requests may contain credentials in URLs; do not log them.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
