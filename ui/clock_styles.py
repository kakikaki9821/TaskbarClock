"""Clock display styles (Strategy pattern)."""

from __future__ import annotations

from typing import Protocol

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPen,
    QRadialGradient,
)


class ClockStyle(Protocol):
    """Protocol for clock display styles."""

    name: str
    label: str

    def get_size(self, preset: str) -> tuple[int, int]: ...

    def paint(self, painter: QPainter, rect: QRect, time_text: str, dark: bool) -> None: ...


# Size presets per style: {preset: (width, height, font_size)}
_DEFAULT_SIZES: dict[str, tuple[int, int, int]] = {
    "small": (60, 24, 10),
    "medium": (80, 32, 14),
    "large": (110, 40, 18),
    "xlarge": (140, 50, 24),
}

_NIXIE_SIZES: dict[str, tuple[int, int, int]] = {
    "small": (100, 32, 14),
    "medium": (130, 42, 18),
    "large": (170, 54, 24),
    "xlarge": (220, 68, 32),
}


class DefaultStyle:
    """Simple modern clock style."""

    name = "default"
    label = "デフォルト"

    def get_size(self, preset: str) -> tuple[int, int]:
        w, h, _ = _DEFAULT_SIZES.get(preset, _DEFAULT_SIZES["medium"])
        return w, h

    def paint(self, painter: QPainter, rect: QRect, time_text: str, dark: bool) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        bg = QColor(0, 0, 0, 200 if dark else 180)
        painter.setBrush(bg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 6, 6)

        # Text
        painter.setPen(QColor(255, 255, 255))
        _, _, fs = _DEFAULT_SIZES.get("medium", (80, 32, 14))
        # Scale font based on rect height
        font_size = max(8, int(rect.height() * 0.45))
        painter.setFont(QFont("Segoe UI", font_size, QFont.Weight.Bold))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, time_text)


class NixieStyle:
    """Nixie tube retro clock style."""

    name = "nixie"
    label = "ニキシー管"

    # Colors
    GLOW_COLOR = QColor(255, 160, 40)  # Warm orange
    GLOW_DIM = QColor(255, 140, 30, 80)  # Dim glow
    TUBE_BG = QColor(20, 15, 10)  # Dark glass
    TUBE_BORDER = QColor(60, 50, 30)  # Brass border
    BASE_BG = QColor(30, 25, 18)  # Dark metal base
    COLON_COLOR = QColor(255, 140, 30, 200)

    def get_size(self, preset: str) -> tuple[int, int]:
        w, h, _ = _NIXIE_SIZES.get(preset, _NIXIE_SIZES["medium"])
        return w, h

    def paint(self, painter: QPainter, rect: QRect, time_text: str, dark: bool) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Metal base background
        base_grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
        base_grad.setColorAt(0.0, QColor(45, 38, 25))
        base_grad.setColorAt(0.5, self.BASE_BG)
        base_grad.setColorAt(1.0, QColor(20, 15, 10))
        painter.setBrush(base_grad)
        painter.setPen(QPen(QColor(50, 42, 28), 1))
        painter.drawRoundedRect(rect, 8, 8)

        # Calculate digit positions
        font_size = max(10, int(rect.height() * 0.55))
        chars = list(time_text)  # e.g., ['1', '2', ':', '3', '4']

        total_chars = len(chars)
        tube_w = int(rect.width() / (total_chars + 0.5))
        tube_h = int(rect.height() * 0.8)
        tube_y = rect.top() + (rect.height() - tube_h) // 2

        x_offset = rect.left() + (rect.width() - tube_w * total_chars) // 2

        for i, ch in enumerate(chars):
            cx = x_offset + i * tube_w
            tube_rect = QRectF(cx + 2, tube_y, tube_w - 4, tube_h)

            if ch == ":":
                self._draw_colon(painter, tube_rect, font_size)
            else:
                self._draw_nixie_digit(painter, tube_rect, ch, font_size)

    def _draw_nixie_digit(
        self, painter: QPainter, rect: QRectF, digit: str, font_size: int
    ) -> None:
        """Draw a single Nixie tube digit."""
        cx = rect.center().x()
        cy = rect.center().y()
        r = min(rect.width(), rect.height()) / 2

        # Glass tube background (radial gradient for depth)
        tube_grad = QRadialGradient(cx, cy, r)
        tube_grad.setColorAt(0.0, QColor(35, 28, 18))
        tube_grad.setColorAt(0.7, self.TUBE_BG)
        tube_grad.setColorAt(1.0, QColor(10, 8, 5))
        painter.setBrush(tube_grad)
        painter.setPen(QPen(self.TUBE_BORDER, 1))
        painter.drawRoundedRect(rect, 4, 4)

        # Glow effect (larger, transparent orange behind digit)
        glow_font = QFont("Georgia", int(font_size * 1.1), QFont.Weight.Bold)
        painter.setFont(glow_font)
        painter.setPen(self.GLOW_DIM)
        glow_rect = QRectF(rect.left() - 2, rect.top() - 1, rect.width() + 4, rect.height() + 2)
        painter.drawText(glow_rect, Qt.AlignmentFlag.AlignCenter, digit)

        # Main digit (bright orange)
        digit_font = QFont("Georgia", font_size, QFont.Weight.Bold)
        painter.setFont(digit_font)
        painter.setPen(self.GLOW_COLOR)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, digit)

        # Hot center glow (small bright spot)
        hot_grad = QRadialGradient(cx, cy, r * 0.3)
        hot_grad.setColorAt(0.0, QColor(255, 200, 100, 30))
        hot_grad.setColorAt(1.0, QColor(255, 160, 40, 0))
        painter.setBrush(hot_grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect.center(), r * 0.4, r * 0.5)

    def _draw_colon(self, painter: QPainter, rect: QRectF, font_size: int) -> None:
        """Draw a glowing colon separator."""
        painter.setPen(Qt.PenStyle.NoPen)

        dot_r = max(2, font_size // 6)
        cx = rect.center().x()
        top_y = rect.center().y() - rect.height() * 0.18
        bot_y = rect.center().y() + rect.height() * 0.18

        for y in (top_y, bot_y):
            # Glow
            glow = QRadialGradient(cx, y, dot_r * 2.5)
            glow.setColorAt(0.0, QColor(255, 160, 40, 60))
            glow.setColorAt(1.0, QColor(255, 140, 30, 0))
            painter.setBrush(glow)
            painter.drawEllipse(
                int(cx - dot_r * 2.5), int(y - dot_r * 2.5), int(dot_r * 5), int(dot_r * 5)
            )

            # Dot
            painter.setBrush(self.COLON_COLOR)
            painter.drawEllipse(int(cx - dot_r), int(y - dot_r), dot_r * 2, dot_r * 2)


# Registry of available styles
STYLES: dict[str, ClockStyle] = {
    "default": DefaultStyle(),  # type: ignore[dict-item]
    "nixie": NixieStyle(),  # type: ignore[dict-item]
}


def get_style(name: str) -> ClockStyle:
    """Get a style by name, falling back to default."""
    return STYLES.get(name, STYLES["default"])
