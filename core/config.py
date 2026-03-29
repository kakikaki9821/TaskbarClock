"""Configuration management with JSON persistence, debounce, and atomic writes."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from threading import Timer
from typing import Any

from loguru import logger

DEFAULT_CONFIG: dict[str, Any] = {
    "alarms": [],
    "theme": "auto",
    "auto_start": False,
    "window_opacity": 0.95,
    "clock_size": "medium",  # "small", "medium", "large", "xlarge"
    "clock_position": None,  # [x, y] or None for auto
}


class Config:
    """JSON-based configuration with debounced atomic writes and corruption recovery."""

    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            path = Path.home() / ".taskbar-clock" / "config.json"
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, Any] = {}
        self._save_timer: Timer | None = None
        self._load()

    def _load(self) -> None:
        """Load config from file. Recover with defaults on corruption."""
        if not self._path.exists():
            logger.info("Config file not found, using defaults")
            self._data = DEFAULT_CONFIG.copy()
            self._write_atomic()
            return

        try:
            text = self._path.read_text(encoding="utf-8")
            self._data = json.loads(text)
            logger.info("Config loaded from {}", self._path)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Config corrupted ({}), backing up and resetting", e)
            self._backup_corrupted()
            self._data = DEFAULT_CONFIG.copy()
            self._write_atomic()

    def _backup_corrupted(self) -> None:
        """Rename corrupted config file for inspection."""
        backup = self._path.with_suffix(".json.corrupted")
        try:
            shutil.copy2(self._path, backup)
            logger.info("Corrupted config backed up to {}", backup)
        except OSError as e:
            logger.error("Failed to backup corrupted config: {}", e)

    def _write_atomic(self) -> None:
        """Write config atomically: write to temp file, then rename."""
        try:
            fd, tmp_path = tempfile.mkstemp(dir=self._path.parent, suffix=".tmp", prefix="config_")
            with open(fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)

            tmp = Path(tmp_path)
            tmp.replace(self._path)
            logger.debug("Config saved atomically")
        except OSError as e:
            logger.error("Failed to save config: {}", e)

    def save_debounced(self, delay_ms: int = 500) -> None:
        """Schedule a save after delay_ms. Resets timer on repeated calls."""
        if self._save_timer is not None:
            self._save_timer.cancel()
        self._save_timer = Timer(delay_ms / 1000.0, self._write_atomic)
        self._save_timer.daemon = True
        self._save_timer.start()

    def save_immediate(self) -> None:
        """Save immediately, cancelling any pending debounced save."""
        if self._save_timer is not None:
            self._save_timer.cancel()
            self._save_timer = None
        self._write_atomic()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a config value and schedule debounced save."""
        self._data[key] = value
        self.save_debounced()

    @property
    def data(self) -> dict[str, Any]:
        """Read-only access to full config data."""
        return self._data.copy()

    @property
    def path(self) -> Path:
        """Config file path."""
        return self._path
