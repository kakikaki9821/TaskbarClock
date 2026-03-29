"""Loguru logging configuration."""

import sys
from pathlib import Path

from loguru import logger


def setup_logger(log_dir: Path | None = None) -> None:
    """Initialize Loguru with file rotation and Sentry integration."""
    logger.remove()  # Remove default handler

    # Console output (DEBUG+)
    logger.add(
        sys.stderr,
        level="DEBUG",
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}",
    )

    # File output (INFO+, rotation at 500MB)
    if log_dir is None:
        log_dir = Path.home() / ".taskbar-clock" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_dir / "taskbar_clock_{time:YYYY-MM-DD}.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {module}:{function}:{line} | {message}",
        rotation="500 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
    )

    logger.info("Logger initialized")
