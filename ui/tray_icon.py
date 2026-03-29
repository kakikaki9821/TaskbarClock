"""System tray icon with digital clock display."""

from __future__ import annotations

from datetime import datetime

from loguru import logger
from PySide6.QtCore import QSize, QTimer, Signal
from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from ui.clock_renderer import ClockRenderer
from ui.clock_styles import STYLES


class TrayIcon(QSystemTrayIcon):
    """System tray icon that displays the current time."""

    alarm_requested = Signal()
    timer_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()
    size_changed = Signal(str)
    style_changed = Signal(str)

    def __init__(self, renderer: ClockRenderer) -> None:
        super().__init__()
        self._renderer = renderer
        self._last_minute: tuple[int, int] = (-1, -1)
        self._current_size = "medium"
        self._current_style = "default"
        self.setToolTip("TaskbarClock")

        self._setup_menu()
        self._update_icon()
        self._setup_timer()

        logger.info("TrayIcon initialized")

    def set_current_size(self, preset: str) -> None:
        """Sync current size for menu checkmarks."""
        self._current_size = preset

    def set_current_style(self, style_name: str) -> None:
        """Sync current style for menu checkmarks."""
        self._current_style = style_name

    def _setup_menu(self) -> None:
        """Create right-click context menu."""
        menu = QMenu()

        # Size submenu
        size_menu = menu.addMenu("サイズ")
        self._size_group = QActionGroup(size_menu)
        self._size_group.setExclusive(True)
        size_labels = {"small": "小", "medium": "中", "large": "大", "xlarge": "特大"}
        for key, label in size_labels.items():
            action = QAction(label, size_menu)
            action.setCheckable(True)
            action.setChecked(key == self._current_size)
            action.setData(key)
            action.triggered.connect(lambda checked, k=key: self.size_changed.emit(k))
            self._size_group.addAction(action)
            size_menu.addAction(action)

        # Style submenu
        style_menu = menu.addMenu("スタイル")
        self._style_group = QActionGroup(style_menu)
        self._style_group.setExclusive(True)
        for style in STYLES.values():
            action = QAction(style.label, style_menu)
            action.setCheckable(True)
            action.setChecked(style.name == self._current_style)
            action.setData(style.name)
            action.triggered.connect(lambda checked, s=style.name: self.style_changed.emit(s))
            self._style_group.addAction(action)
            style_menu.addAction(action)

        menu.addSeparator()

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

        if current_minute != self._last_minute:
            self._last_minute = current_minute
            screen = QApplication.primaryScreen()
            dpr = screen.devicePixelRatio() if screen else 1.0
            pixmap = self._renderer.render_digital(now, QSize(64, 64), dpr)
            self.setIcon(QIcon(pixmap))

        self.setToolTip(now.strftime("%Y-%m-%d %H:%M:%S"))

    def update_tooltip_text(self, text: str) -> None:
        """Override tooltip with custom text (e.g., timer remaining)."""
        self.setToolTip(text)
