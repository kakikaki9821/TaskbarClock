"""Integration tests for AlarmDialog."""

from __future__ import annotations

import os
import sys

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "linux" and not os.environ.get("DISPLAY"),
    reason="No display available",
)


class TestAlarmDialog:
    def test_dialog_creation_empty(self, qtbot: object) -> None:
        from ui.alarm_dialog import AlarmDialog

        dlg = AlarmDialog(alarms=[])
        assert dlg is not None

    def test_dialog_creation_with_alarms(self, qtbot: object) -> None:
        from clock.alarm import Alarm
        from ui.alarm_dialog import AlarmDialog

        alarms = [Alarm(hour=7, minute=0, label="Test")]
        dlg = AlarmDialog(alarms=alarms)
        assert dlg._list.count() == 1

    def test_add_alarm_signal(self, qtbot: object) -> None:
        from ui.alarm_dialog import AlarmDialog

        dlg = AlarmDialog(alarms=[])
        signals: list[object] = []
        dlg.alarm_added.connect(lambda a: signals.append(a))
        dlg._add_alarm()
        assert len(signals) == 1
