"""Integration tests for TimerDialog."""

from __future__ import annotations

import os
import sys

import pytest

from clock.timer_manager import TimerState  # noqa: E402

pytestmark = pytest.mark.skipif(
    sys.platform == "linux" and not os.environ.get("DISPLAY"),
    reason="No display available",
)


class TestTimerDialog:
    def test_dialog_creation(self, qtbot: object) -> None:
        from ui.timer_dialog import TimerDialog

        dlg = TimerDialog()
        assert dlg is not None

    def test_preset_sets_minutes(self, qtbot: object) -> None:
        from ui.timer_dialog import TimerDialog

        dlg = TimerDialog()
        dlg._set_preset(10)
        assert dlg._minutes_spin.value() == 10
        assert dlg._seconds_spin.value() == 0

    def test_start_emits_signal(self, qtbot: object) -> None:
        from ui.timer_dialog import TimerDialog

        dlg = TimerDialog()
        dlg._minutes_spin.setValue(1)
        dlg._seconds_spin.setValue(30)
        signals: list[int] = []
        dlg.start_requested.connect(lambda ms: signals.append(ms))
        dlg._on_start()
        assert len(signals) == 1
        assert signals[0] == 90000

    def test_update_display(self, qtbot: object) -> None:
        from ui.timer_dialog import TimerDialog

        dlg = TimerDialog()
        dlg.update_display(125000)
        assert dlg._display.text() == "02:05"

    def test_update_state_idle(self, qtbot: object) -> None:
        from ui.timer_dialog import TimerDialog

        dlg = TimerDialog()
        dlg.update_state(TimerState.RUNNING)
        assert dlg._start_btn.isEnabled() is False
        dlg.update_state(TimerState.IDLE)
        assert dlg._start_btn.isEnabled() is True
