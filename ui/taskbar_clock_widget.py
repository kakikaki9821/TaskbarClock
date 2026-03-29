"""Floating clock widget that sits on the taskbar, always visible."""

from __future__ import annotations

from datetime import datetime

from loguru import logger
from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter
from PySide6.QtWidgets import QApplication, QWidget


class TaskbarClockWidget(QWidget):
    """Small frameless widget showing HH:MM on the taskbar area."""

    left_clicked = Signal()
    alarm_requested = Signal()
    timer_requested = Signal()
    quit_requested = Signal()

    WIDGET_WIDTH = 80
    WIDGET_HEIGHT = 32

    def __init__(self) -> None:
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self.WIDGET_WIDTH, self.WIDGET_HEIGHT)
        self.setAccessibleName("タスクバー時計")

        # Theme colors
        self._bg_color = QColor(0, 0, 0, 180)
        self._text_color = QColor(255, 255, 255)

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
        logger.info("TaskbarClockWidget initialized")

    def _position_on_taskbar(self) -> None:
        """Position widget on the taskbar area (bottom-right, left of system tray)."""
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        screen_geo = screen.geometry()
        available = screen.availableGeometry()

        # Taskbar height = screen height - available height
        taskbar_height = screen_geo.height() - available.height()
        if taskbar_height < 20:
            taskbar_height = 40  # Fallback

        # Position: bottom-right, offset left from edge to sit near system tray
        x = available.right() - self.WIDGET_WIDTH - 200
        y = screen_geo.bottom() - taskbar_height + (taskbar_height - self.WIDGET_HEIGHT) // 2

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

            # Rounded background
            painter.setBrush(self._bg_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect(), 6, 6)

            # Time text
            painter.setPen(self._text_color)
            font = QFont("Segoe UI", 14, QFont.Weight.Bold)
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
        """Show right-click menu."""
        from PySide6.QtGui import QAction
        from PySide6.QtWidgets import QMenu

        menu = QMenu()

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
