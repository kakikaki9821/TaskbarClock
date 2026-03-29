"""Integration tests for TrayIcon (requires display)."""

from __future__ import annotations

import os
import sys

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "linux" and not os.environ.get("DISPLAY"),
    reason="No display available",
)


class TestTrayIcon:
    def test_tray_icon_creation(self, qtbot: object) -> None:
        from ui.clock_renderer import ClockRenderer
        from ui.tray_icon import TrayIcon

        renderer = ClockRenderer()
        icon = TrayIcon(renderer)
        assert icon is not None

    def test_context_menu_has_items(self, qtbot: object) -> None:
        from ui.clock_renderer import ClockRenderer
        from ui.tray_icon import TrayIcon

        renderer = ClockRenderer()
        icon = TrayIcon(renderer)
        menu = icon.contextMenu()
        assert menu is not None
        labels = [a.text() for a in menu.actions()]
        assert "アラーム設定" in labels
        assert "タイマー" in labels
        assert "終了" in labels
