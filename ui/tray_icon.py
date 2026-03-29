"""System tray icon with digital clock display."""

from __future__ import annotations

from datetime import datetime

from loguru import logger
from PySide6.QtCore import QSize, QTimer, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from ui.clock_renderer import ClockRenderer


class TrayIcon(QSystemTrayIcon):
    """System tray icon that displays the current time."""

    alarm_requested = Signal()
    timer_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()

    def __init__(self, renderer: ClockRenderer) -> None:
        super().__init__()
        self._renderer = renderer
        self._last_minute: tuple[int, int] = (-1, -1)
        self.setToolTip("TaskbarClock")

        self._setup_menu()
        self._update_icon()
        self._setup_timer()

        logger.info("TrayIcon initialized")

    def _setup_menu(self) -> None:
        """Create right-click context menu."""
        menu = QMenu()

        alarm_action = QAction("アラーム設定", menu)
        alarm_action.triggered.connect(self.alarm_requested.emit)
        menu.addAction(alarm_action)

        timer_action = QAction("タイマー", menu)
        timer_action.triggered.connect(self.timer_requested.emit)
        menu.addAction(timer_action)

        menu.addSeparator()

        settings_action = QAction("設定", menu)
        settings_action.triggered.connect(self.settings_requested.emit)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction("終了", menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

    def _setup_timer(self) -> None:
        """Start 1-second update timer."""
        self._timer = QTimer()
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._update_icon)
        self._timer.start()

    def _update_icon(self) -> None:
        """Update tray icon and tooltip."""
        now = datetime.now()
        current_minute = (now.hour, now.minute)

        # Only re-render icon when minute changes
        if current_minute != self._last_minute:
            self._last_minute = current_minute
            screen = QApplication.primaryScreen()
            dpr = screen.devicePixelRatio() if screen else 1.0
            pixmap = self._renderer.render_digital(now, QSize(64, 64), dpr)
            self.setIcon(QIcon(pixmap))

        # Always update tooltip with seconds
        self.setToolTip(now.strftime("%Y-%m-%d %H:%M:%S"))

    def update_tooltip_text(self, text: str) -> None:
        """Override tooltip with custom text (e.g., timer remaining)."""
        self.setToolTip(text)
