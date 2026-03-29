"""Analog clock popup window shown on tray icon hover."""

from __future__ import annotations

from datetime import datetime

from loguru import logger
from PySide6.QtCore import QPoint, QRect, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QApplication, QWidget

from ui.clock_renderer import ClockRenderer


class AnalogClock(QWidget):
    """Frameless, semi-transparent analog clock popup."""

    CLOCK_SIZE = 250
    CORNER_RADIUS = 20

    def __init__(self, renderer: ClockRenderer) -> None:
        super().__init__()
        self._renderer = renderer

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(QSize(self.CLOCK_SIZE, self.CLOCK_SIZE))

        # Accessibility
        self.setAccessibleName("アナログ時計")
        self.setAccessibleDescription("現在時刻をアナログ表示")

        # Paint timer (only active while visible)
        self._paint_timer = QTimer()
        self._paint_timer.setInterval(16)  # ~60fps
        self._paint_timer.timeout.connect(self.update)

        # Auto-hide timer
        self._hide_timer = QTimer()
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(500)
        self._hide_timer.timeout.connect(self._maybe_hide)

        self.setMouseTracking(True)
        logger.debug("AnalogClock widget created")

    def show_at_tray(self, tray_geometry: QRect | None = None) -> None:
        """Show the clock near the system tray area."""
        screen = QApplication.primaryScreen()
        if screen is None:
            self.show()
            return

        available = screen.availableGeometry()

        if tray_geometry and tray_geometry.isValid():
            # Position above the tray icon
            x = tray_geometry.center().x() - self.width() // 2
            y = tray_geometry.top() - self.height() - 8
        else:
            # Fallback: bottom-right corner
            x = available.right() - self.width() - 16
            y = available.bottom() - self.height() - 16

        # Ensure within screen bounds
        x = max(available.left(), min(x, available.right() - self.width()))
        y = max(available.top(), min(y, available.bottom() - self.height()))

        self.move(QPoint(x, y))
        self.show()
        self.raise_()
        logger.debug("AnalogClock shown at ({}, {})", x, y)

    def toggle_at_tray(self, tray_geometry: QRect | None = None) -> None:
        """Toggle visibility."""
        if self.isVisible():
            self.hide()
        else:
            self.show_at_tray(tray_geometry)

    def showEvent(self, event: object) -> None:
        """Start paint timer when visible."""
        self._paint_timer.start()
        super().showEvent(event)  # type: ignore[arg-type]

    def hideEvent(self, event: object) -> None:
        """Stop paint timer when hidden."""
        self._paint_timer.stop()
        super().hideEvent(event)  # type: ignore[arg-type]

    def leaveEvent(self, event: object) -> None:
        """Start auto-hide timer when mouse leaves."""
        self._hide_timer.start()
        super().leaveEvent(event)  # type: ignore[arg-type]

    def enterEvent(self, event: object) -> None:
        """Cancel auto-hide when mouse enters."""
        self._hide_timer.stop()
        super().enterEvent(event)  # type: ignore[arg-type]

    def _maybe_hide(self) -> None:
        """Hide if mouse is not over the widget."""
        if not self.underMouse():
            self.hide()

    def paintEvent(self, event: object) -> None:
        """Draw the analog clock face."""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Rounded rectangle clip + background
            path = QPainterPath()
            path.addRoundedRect(
                0.0,
                0.0,
                float(self.width()),
                float(self.height()),
                self.CORNER_RADIUS,
                self.CORNER_RADIUS,
            )
            painter.setClipPath(path)

            # Semi-transparent background
            bg = QColor(self._renderer.face_color)
            bg.setAlpha(230)
            painter.fillPath(path, bg)

            # Draw clock
            now = datetime.now()
            self._renderer.render_analog(painter, self.rect(), now, smooth_seconds=True)

            # Update accessibility description
            self.setAccessibleDescription(f"現在時刻: {now.hour}時{now.minute}分{now.second}秒")
        finally:
            painter.end()
