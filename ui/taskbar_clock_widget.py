"""Floating clock widget that sits on the taskbar, always visible."""

from __future__ import annotations

from datetime import datetime

from loguru import logger
from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QActionGroup, QMouseEvent, QPainter
from PySide6.QtWidgets import QApplication, QMenu, QWidget

from ui.clock_styles import STYLES, ClockStyle, get_style

# Size presets (used for default style; other styles define their own)
SIZE_PRESETS: dict[str, tuple[int, int, int]] = {
    "small": (60, 24, 10),
    "medium": (80, 32, 14),
    "large": (110, 40, 18),
    "xlarge": (140, 50, 24),
}


class TaskbarClockWidget(QWidget):
    """Small frameless widget showing HH:MM on the taskbar area."""

    left_clicked = Signal()
    alarm_requested = Signal()
    timer_requested = Signal()
    quit_requested = Signal()
    size_changed = Signal(str)  # size preset name
    style_changed = Signal(str)  # style name

    def __init__(self, size_preset: str = "medium", style_name: str = "default") -> None:
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAccessibleName("タスクバー時計")

        # State
        self._is_dark = False
        self._drag_pos: QPoint | None = None
        self._time_text = ""
        self._last_minute: tuple[int, int] = (-1, -1)

        # Style and size
        self._style: ClockStyle = get_style(style_name)
        self._size_preset = size_preset
        self._apply_size()

        # Position on taskbar
        self._position_on_taskbar()

        # Update timer
        self._timer = QTimer()
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._update_time)
        self._timer.start()

        self._update_time()
        logger.info(
            "TaskbarClockWidget initialized (size={}, style={})",
            size_preset,
            style_name,
        )

    def _apply_size(self) -> None:
        """Apply current size preset using the active style."""
        w, h = self._style.get_size(self._size_preset)
        self.setFixedSize(w, h)

    def set_size_preset(self, preset: str) -> None:
        """Change the widget size preset."""
        if preset not in SIZE_PRESETS:
            preset = "medium"
        if preset == self._size_preset:
            return
        self._size_preset = preset
        self._apply_size()
        self.update()
        logger.debug("Clock size changed to: {}", preset)

    def set_style(self, style_name: str) -> None:
        """Change the display style."""
        new_style = get_style(style_name)
        if new_style.name == self._style.name:
            return
        self._style = new_style
        self._apply_size()
        self.update()
        logger.debug("Clock style changed to: {}", style_name)

    @property
    def size_preset(self) -> str:
        return self._size_preset

    @property
    def style_name(self) -> str:
        return self._style.name

    def set_position(self, x: int, y: int) -> None:
        self.move(x, y)

    def _position_on_taskbar(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        screen_geo = screen.geometry()
        available = screen.availableGeometry()
        taskbar_height = screen_geo.height() - available.height()
        if taskbar_height < 20:
            taskbar_height = 40
        x = available.right() - self.width() - 200
        y = screen_geo.bottom() - taskbar_height + (taskbar_height - self.height()) // 2
        self.move(x, y)

    def _update_time(self) -> None:
        now = datetime.now()
        current_minute = (now.hour, now.minute)
        if current_minute != self._last_minute:
            self._last_minute = current_minute
            self._time_text = f"{now.hour:02d}:{now.minute:02d}"
            self.update()
            self.setAccessibleDescription(f"現在時刻: {self._time_text}")

    def update_colors(self, dark: bool) -> None:
        self._is_dark = dark
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        try:
            self._style.paint(painter, self.rect(), self._time_text, self._is_dark)
        finally:
            painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._drag_pos is not None:
                moved = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                ) - self._drag_pos
                if abs(moved.x()) < 5 and abs(moved.y()) < 5:
                    self.left_clicked.emit()
            self._drag_pos = None
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def _show_context_menu(self, pos: QPoint) -> None:
        menu = QMenu()

        # Size submenu
        size_menu = menu.addMenu("サイズ")
        size_group = QActionGroup(size_menu)
        size_group.setExclusive(True)
        size_labels = {"small": "小", "medium": "中", "large": "大", "xlarge": "特大"}
        for key, label in size_labels.items():
            action = QAction(label, size_menu)
            action.setCheckable(True)
            action.setChecked(key == self._size_preset)
            action.triggered.connect(lambda checked, k=key: self._on_size_selected(k))
            size_group.addAction(action)
            size_menu.addAction(action)

        # Style submenu
        style_menu = menu.addMenu("スタイル")
        style_group = QActionGroup(style_menu)
        style_group.setExclusive(True)
        for style in STYLES.values():
            action = QAction(style.label, style_menu)
            action.setCheckable(True)
            action.setChecked(style.name == self._style.name)
            action.triggered.connect(lambda checked, s=style.name: self._on_style_selected(s))
            style_group.addAction(action)
            style_menu.addAction(action)

        menu.addSeparator()

        alarm_action = QAction("アラーム設定", menu)
        alarm_action.triggered.connect(self.alarm_requested.emit)
        menu.addAction(alarm_action)

        timer_action = QAction("タイマー", menu)
        timer_action.triggered.connect(self.timer_requested.emit)
        menu.addAction(timer_action)

        menu.addSeparator()

        quit_action = QAction("終了", menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        menu.exec(pos)

    def _on_size_selected(self, preset: str) -> None:
        self.set_size_preset(preset)
        self.size_changed.emit(preset)

    def _on_style_selected(self, style_name: str) -> None:
        self.set_style(style_name)
        self.style_changed.emit(style_name)
