"""Floating clock widget that sits on the taskbar, always visible."""

from __future__ import annotations

from datetime import datetime

from loguru import logger
from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QActionGroup, QColor, QFont, QMouseEvent, QPainter
from PySide6.QtWidgets import QApplication, QMenu, QWidget

# Size presets: (width, height, font_size)
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

    def __init__(self, size_preset: str = "medium") -> None:
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAccessibleName("タスクバー時計")

        # Theme colors
        self._bg_color = QColor(0, 0, 0, 180)
        self._text_color = QColor(255, 255, 255)

        # Size
        self._size_preset = ""
        self._font_size = 14
        self.set_size_preset(size_preset)

        # Drag state
        self._drag_pos: QPoint | None = None

        # Time state
        self._time_text = ""
        self._last_minute: tuple[int, int] = (-1, -1)

        # Position on taskbar
        self._position_on_taskbar()

        # Update timer
        self._timer = QTimer()
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._update_time)
        self._timer.start()

        self._update_time()
        logger.info("TaskbarClockWidget initialized (size={})", size_preset)

    def set_size_preset(self, preset: str) -> None:
        """Change the widget size. Preset: 'small', 'medium', 'large', 'xlarge'."""
        if preset not in SIZE_PRESETS:
            preset = "medium"
        if preset == self._size_preset:
            return
        self._size_preset = preset
        w, h, fs = SIZE_PRESETS[preset]
        self._font_size = fs
        self.setFixedSize(w, h)
        self.update()
        logger.debug("Clock size changed to: {} ({}x{}, font {})", preset, w, h, fs)

    @property
    def size_preset(self) -> str:
        """Current size preset name."""
        return self._size_preset

    def set_position(self, x: int, y: int) -> None:
        """Set widget position (for restoring saved position)."""
        self.move(x, y)

    def _position_on_taskbar(self) -> None:
        """Position widget on the taskbar area (bottom-right, left of system tray)."""
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
        """Update displayed time."""
        now = datetime.now()
        current_minute = (now.hour, now.minute)
        if current_minute != self._last_minute:
            self._last_minute = current_minute
            self._time_text = f"{now.hour:02d}:{now.minute:02d}"
            self.update()
            self.setAccessibleDescription(f"現在時刻: {self._time_text}")

    def update_colors(self, dark: bool) -> None:
        """Update colors for dark/light theme."""
        if dark:
            self._bg_color = QColor(0, 0, 0, 200)
            self._text_color = QColor(255, 255, 255)
        else:
            self._bg_color = QColor(0, 0, 0, 180)
            self._text_color = QColor(255, 255, 255)
        self.update()

    def paintEvent(self, event: object) -> None:
        """Draw semi-transparent background with time text."""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            painter.setBrush(self._bg_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect(), 6, 6)

            painter.setPen(self._text_color)
            font = QFont("Segoe UI", self._font_size, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._time_text)
        finally:
            painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle click and start drag."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Emit left_clicked if not dragged."""
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
        """Drag the widget."""
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def _show_context_menu(self, pos: QPoint) -> None:
        """Show right-click menu with size options."""
        menu = QMenu()

        # Size submenu
        size_menu = menu.addMenu("サイズ")
        size_group = QActionGroup(size_menu)
        size_group.setExclusive(True)

        size_labels = {
            "small": "小",
            "medium": "中",
            "large": "大",
            "xlarge": "特大",
        }
        for key, label in size_labels.items():
            action = QAction(label, size_menu)
            action.setCheckable(True)
            action.setChecked(key == self._size_preset)
            action.triggered.connect(lambda checked, k=key: self._on_size_selected(k))
            size_group.addAction(action)
            size_menu.addAction(action)

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
        """Handle size selection from menu."""
        self.set_size_preset(preset)
        self.size_changed.emit(preset)
