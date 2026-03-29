"""Dark/light theme management for Windows 11."""

from __future__ import annotations

from collections.abc import Callable

from loguru import logger
from PySide6.QtWidgets import QApplication


class ThemeManager:
    """Detects and applies Windows 11 dark/light theme."""

    def __init__(
        self,
        on_theme_changed: Callable[[bool], None] | None = None,
    ) -> None:
        self._is_dark = False
        self._on_theme_changed = on_theme_changed
        self._listener_thread: object | None = None

    def detect_and_apply(self, app: QApplication) -> bool:
        """Detect current theme and apply stylesheet. Returns True if dark."""
        try:
            import darkdetect

            self._is_dark = darkdetect.isDark() or False
        except ImportError:
            logger.debug("darkdetect not available, defaulting to light theme")
            self._is_dark = False

        self._apply_stylesheet(app)
        return self._is_dark

    def start_listener(self, app: QApplication) -> None:
        """Start listening for OS theme changes."""
        try:
            import darkdetect

            def _callback(theme: str) -> None:
                self._is_dark = theme.lower() == "dark"
                self._apply_stylesheet(app)
                if self._on_theme_changed:
                    self._on_theme_changed(self._is_dark)
                logger.info("Theme changed to: {}", "dark" if self._is_dark else "light")

            import threading

            self._listener_thread = threading.Thread(
                target=darkdetect.listener, args=(_callback,), daemon=True
            )
            self._listener_thread.start()
            logger.info("Theme listener started")
        except ImportError:
            logger.debug("darkdetect not available, theme listener disabled")

    def _apply_stylesheet(self, app: QApplication) -> None:
        """Apply dark or light stylesheet."""
        try:
            import qdarktheme

            theme = "dark" if self._is_dark else "light"
            app.setStyleSheet(qdarktheme.load_stylesheet(theme))
            logger.debug("Applied {} theme", theme)
        except ImportError:
            logger.debug("qdarktheme not available, using default theme")

    @property
    def is_dark(self) -> bool:
        """Current theme state."""
        return self._is_dark
