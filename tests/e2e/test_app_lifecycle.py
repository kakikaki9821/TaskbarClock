"""End-to-end tests for application lifecycle."""

from __future__ import annotations

import os
import sys

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "linux" and not os.environ.get("DISPLAY"),
    reason="No display available",
)


class TestAppLifecycle:
    def test_core_imports(self) -> None:
        from core.config import Config
        from core.logger import setup_logger

        assert Config is not None
        assert setup_logger is not None

    def test_clock_imports(self) -> None:
        from clock.alarm import Alarm, AlarmManager
        from clock.timer_manager import TimerManager, TimerState

        assert Alarm is not None
        assert AlarmManager is not None
        assert TimerManager is not None
        assert TimerState is not None

    def test_ui_imports(self) -> None:
        from ui.alarm_dialog import AlarmDialog
        from ui.analog_clock import AnalogClock
        from ui.clock_renderer import ClockRenderer
        from ui.timer_dialog import TimerDialog
        from ui.tray_icon import TrayIcon

        assert ClockRenderer is not None
        assert TrayIcon is not None
        assert AnalogClock is not None
        assert AlarmDialog is not None
        assert TimerDialog is not None

    def test_services_imports(self) -> None:
        from services.notifier import Notifier
        from services.sounds import SoundPlayer

        assert SoundPlayer is not None
        assert Notifier is not None

    def test_config_roundtrip(self, tmp_path: object) -> None:
        from pathlib import Path

        from clock.alarm import Alarm, AlarmManager
        from core.config import Config

        config = Config(path=Path(str(tmp_path)) / "test_config.json")
        mgr = AlarmManager()
        mgr.add(Alarm(hour=7, minute=30, label="E2E Test"))
        config.set("alarms", mgr.serialize())
        config.save_immediate()

        config2 = Config(path=Path(str(tmp_path)) / "test_config.json")
        mgr2 = AlarmManager()
        mgr2.deserialize(config2.get("alarms", []))
        assert len(mgr2.alarms) == 1
        assert mgr2.alarms[0].label == "E2E Test"

    def test_alarm_to_timer_flow(self) -> None:
        from datetime import datetime

        from clock.alarm import Alarm, AlarmManager
        from clock.timer_manager import TimerManager, TimerState
        from tests.conftest import FakeClock

        clock = FakeClock(datetime(2026, 3, 30, 7, 0, 0))
        triggered: list[object] = []
        alarm_mgr = AlarmManager(clock=clock, on_triggered=lambda a: triggered.append(a))
        alarm_mgr.add(Alarm(hour=7, minute=0))
        alarm_mgr.check()
        assert len(triggered) == 1

        finished: list[bool] = []
        timer_mgr = TimerManager()
        timer_mgr.on_finished(lambda: finished.append(True))
        timer_mgr.start(5000)
        timer_mgr.tick(3000)
        assert timer_mgr.state == TimerState.RUNNING
        timer_mgr.tick(3000)
        assert timer_mgr.state == TimerState.FINISHED
        assert len(finished) == 1
