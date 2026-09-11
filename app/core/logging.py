"""Logging setup for the application."""

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger using a standard library log level."""

    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Unsupported logging level: {level}")

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
