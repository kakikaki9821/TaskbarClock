"""Integration tests for AnalogClock popup."""

from __future__ import annotations

import os
import sys

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "linux" and not os.environ.get("DISPLAY"),
    reason="No display available",
)


class TestAnalogClock:
    def test_creation(self, qtbot: object) -> None:
        from ui.analog_clock import AnalogClock
        from ui.clock_renderer import ClockRenderer

        renderer = ClockRenderer()
        clock = AnalogClock(renderer)
        assert clock is not None
        assert clock.isVisible() is False

    def test_show_and_hide(self, qtbot: object) -> None:
        from ui.analog_clock import AnalogClock
        from ui.clock_renderer import ClockRenderer

        renderer = ClockRenderer()
        clock = AnalogClock(renderer)
        clock.show_at_tray()
        assert clock.isVisible() is True
        clock.hide()
        assert clock.isVisible() is False

    def test_toggle(self, qtbot: object) -> None:
        from ui.analog_clock import AnalogClock
        from ui.clock_renderer import ClockRenderer

        renderer = ClockRenderer()
        clock = AnalogClock(renderer)
        clock.toggle_at_tray()
        assert clock.isVisible() is True
        clock.toggle_at_tray()
        assert clock.isVisible() is False
