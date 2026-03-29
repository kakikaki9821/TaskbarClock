"""Single instance enforcement using shared memory."""

from __future__ import annotations

from loguru import logger
from PySide6.QtCore import QSharedMemory

_shared_memory: QSharedMemory | None = None


def ensure_single_instance(app_id: str = "TaskbarClock_SingleInstance") -> bool:
    """Return True if this is the only running instance. False if another exists."""
    global _shared_memory

    _shared_memory = QSharedMemory(app_id)

    if _shared_memory.attach():
        # Another instance is already running
        _shared_memory.detach()
        logger.warning("Another instance is already running")
        return False

    if not _shared_memory.create(1):
        logger.warning("Failed to create shared memory: {}", _shared_memory.errorString())
        return False

    logger.info("Single instance lock acquired")
    return True


def release_single_instance() -> None:
    """Release the single instance lock."""
    global _shared_memory
    if _shared_memory is not None:
        _shared_memory.detach()
        _shared_memory = None
        logger.debug("Single instance lock released")
