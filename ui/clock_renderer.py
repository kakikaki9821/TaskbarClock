"""Clock rendering: digital icon and analog clock face drawing."""

from __future__ import annotations

import math
from datetime import datetime

from PySide6.QtCore import QPoint, QPointF, QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap


def hour_hand_angle(hour: int, minute: int) -> float:
    """Calculate hour hand angle in degrees (0=12 o'clock, clockwise)."""
    return (hour % 12 + minute / 60.0) * 30.0


def minute_hand_angle(minute: int, second: int = 0) -> float:
    """Calculate minute hand angle in degrees."""
    return (minute + second / 60.0) * 6.0


def second_hand_angle(second: int, millisecond: int = 0) -> float:
    """Calculate second hand angle in degrees."""
    return (second + millisecond / 1000.0) * 6.0


class ClockRenderer:
    """Renders digital and analog clock faces."""

    def __init__(self) -> None:
        self._cached_pixmap: QPixmap | None = None
        self._cached_minute: tuple[int, int] = (-1, -1)
        # Theme colors (defaults: dark text on light background)
        self.bg_color = QColor(255, 255, 255)
        self.text_color = QColor(0, 0, 0)
        self.face_color = QColor(30, 30, 30)
        self.hand_color = QColor(220, 220, 220)
        self.second_color = QColor(255, 80, 80)
        self.tick_color = QColor(180, 180, 180)

    def update_colors(self, dark: bool) -> None:
        """Update colors for dark/light theme."""
        if dark:
            self.bg_color = QColor(30, 30, 30)
            self.text_color = QColor(255, 255, 255)
            self.face_color = QColor(40, 40, 40)
            self.hand_color = QColor(220, 220, 220)
            self.second_color = QColor(255, 80, 80)
            self.tick_color = QColor(140, 140, 140)
        else:
            self.bg_color = QColor(255, 255, 255)
            self.text_color = QColor(0, 0, 0)
            self.face_color = QColor(250, 250, 250)
            self.hand_color = QColor(40, 40, 40)
            self.second_color = QColor(220, 50, 50)
            self.tick_color = QColor(100, 100, 100)

    def render_digital(self, now: datetime, size: QSize, dpr: float = 1.0) -> QPixmap:
        """Render digital time as QPixmap. Cached per minute."""
        current_minute = (now.hour, now.minute)
        if current_minute == self._cached_minute and self._cached_pixmap is not None:
            return self._cached_pixmap

        pixel_size = QSize(int(size.width() * dpr), int(size.height() * dpr))
        pixmap = QPixmap(pixel_size)
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(self.bg_color)

        painter = QPainter(pixmap)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(self.text_color)

            font_size = max(8, int(size.height() * 0.38))
            font = QFont("Segoe UI", font_size, QFont.Weight.Bold)
            painter.setFont(font)

            time_str = f"{now.hour:02d}:{now.minute:02d}"
            painter.drawText(
                QRect(0, 0, size.width(), size.height()),
                Qt.AlignmentFlag.AlignCenter,
                time_str,
            )
        finally:
            painter.end()

        self._cached_minute = current_minute
        self._cached_pixmap = pixmap
        return pixmap

    def render_analog(
        self, painter: QPainter, rect: QRect, now: datetime, smooth_seconds: bool = True
    ) -> None:
        """Draw analog clock face onto an existing QPainter."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = rect.center().x()
        cy = rect.center().y()
        radius = min(rect.width(), rect.height()) // 2 - 10

        # Clock face background
        painter.setBrush(self.face_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(cx, cy), radius, radius)

        # Tick marks
        for i in range(60):
            angle_rad = math.radians(i * 6 - 90)
            if i % 5 == 0:
                inner = radius * 0.82
                pen = QPen(self.tick_color, 2)
            else:
                inner = radius * 0.90
                pen = QPen(self.tick_color, 1)
            painter.setPen(pen)
            x1 = cx + inner * math.cos(angle_rad)
            y1 = cy + inner * math.sin(angle_rad)
            x2 = cx + radius * 0.95 * math.cos(angle_rad)
            y2 = cy + radius * 0.95 * math.sin(angle_rad)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # Hour numbers
        painter.setPen(self.hand_color)
        num_font = QFont("Segoe UI", max(8, radius // 6))
        painter.setFont(num_font)
        for i in range(1, 13):
            angle_rad = math.radians(i * 30 - 90)
            nx = cx + radius * 0.7 * math.cos(angle_rad)
            ny = cy + radius * 0.7 * math.sin(angle_rad)
            text_rect = QRect(int(nx) - 12, int(ny) - 10, 24, 20)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, str(i))

        # Calculate angles
        h_angle = hour_hand_angle(now.hour, now.minute)
        m_angle = minute_hand_angle(now.minute, now.second)
        if smooth_seconds:
            ms = now.microsecond // 1000
            s_angle = second_hand_angle(now.second, ms)
        else:
            s_angle = second_hand_angle(now.second)

        # Hour hand
        self._draw_hand(painter, cx, cy, h_angle, radius * 0.5, 4, self.hand_color)
        # Minute hand
        self._draw_hand(painter, cx, cy, m_angle, radius * 0.72, 3, self.hand_color)
        # Second hand
        self._draw_hand(painter, cx, cy, s_angle, radius * 0.82, 1, self.second_color)

        # Center dot
        painter.setBrush(self.second_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(cx, cy), 4, 4)

    @staticmethod
    def _draw_hand(
        painter: QPainter,
        cx: int,
        cy: int,
        angle_deg: float,
        length: float,
        width: int,
        color: QColor,
    ) -> None:
        """Draw a clock hand from center at the given angle."""
        angle_rad = math.radians(angle_deg - 90)
        end_x = cx + length * math.cos(angle_rad)
        end_y = cy + length * math.sin(angle_rad)
        painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(cx, cy), QPointF(end_x, end_y))
