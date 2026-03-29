"""Unit tests for alarm logic."""

from datetime import datetime

import pytest

from clock.alarm import Alarm, AlarmManager
from tests.conftest import FakeClock


class TestAlarm:
    def test_alarm_triggers_at_exact_time(self) -> None:
        alarm = Alarm(hour=7, minute=0, days=list(range(7)))
        now = datetime(2026, 3, 30, 7, 0, 0)  # Monday
        assert alarm.matches(now) is True

    def test_alarm_does_not_trigger_when_disabled(self) -> None:
        alarm = Alarm(hour=7, minute=0, enabled=False)
        now = datetime(2026, 3, 30, 7, 0, 0)
        assert alarm.matches(now) is False

    def test_alarm_respects_weekday_filter(self) -> None:
        alarm = Alarm(hour=7, minute=0, days=[0])  # Monday only
        now = datetime(2026, 3, 31, 7, 0, 0)  # Tuesday
        assert alarm.matches(now) is False

    def test_alarm_triggers_on_correct_weekday(self) -> None:
        alarm = Alarm(hour=7, minute=0, days=[0])  # Monday only
        now = datetime(2026, 3, 30, 7, 0, 0)  # Monday
        assert alarm.matches(now) is True

    def test_alarm_wrong_time(self) -> None:
        alarm = Alarm(hour=7, minute=0, days=list(range(7)))
        now = datetime(2026, 3, 30, 8, 0, 0)
        assert alarm.matches(now) is False

    def test_snooze_delays_next_trigger(self) -> None:
        alarm = Alarm(hour=7, minute=0)
        now = datetime(2026, 3, 30, 7, 0, 0)
        alarm.snooze_until = datetime(2026, 3, 30, 7, 5, 0)
        assert alarm.matches(now) is False

    def test_snooze_triggers_after_delay(self) -> None:
        alarm = Alarm(hour=7, minute=5)
        alarm.snooze_until = datetime(2026, 3, 30, 7, 5, 0)
        now = datetime(2026, 3, 30, 7, 5, 1)
        assert alarm.matches(now) is True

    def test_alarm_serialize_deserialize(self) -> None:
        alarm = Alarm(hour=14, minute=30, days=[0, 2, 4], label="Test")
        data = alarm.to_dict()
        restored = Alarm.from_dict(data)
        assert restored.hour == 14
        assert restored.minute == 30
        assert restored.days == [0, 2, 4]
        assert restored.label == "Test"
        assert restored.id == alarm.id

    def test_alarm_id_uniqueness(self) -> None:
        a1 = Alarm(hour=7, minute=0)
        a2 = Alarm(hour=7, minute=0)
        assert a1.id != a2.id

    def test_invalid_hour_raises(self) -> None:
        with pytest.raises(ValueError, match="hour must be 0-23"):
            Alarm(hour=25, minute=0)

    def test_invalid_minute_raises(self) -> None:
        with pytest.raises(ValueError, match="minute must be 0-59"):
            Alarm(hour=7, minute=60)

    def test_invalid_day_raises(self) -> None:
        with pytest.raises(ValueError, match="days must be 0-6"):
            Alarm(hour=7, minute=0, days=[7])

    def test_boundary_values_valid(self) -> None:
        Alarm(hour=0, minute=0, days=[0])
        Alarm(hour=23, minute=59, days=[6])


class TestAlarmManager:
    def test_add_remove_alarm(self, alarm_manager: AlarmManager) -> None:
        alarm = Alarm(hour=7, minute=0)
        alarm_manager.add(alarm)
        assert len(alarm_manager.alarms) == 1
        alarm_manager.remove(alarm.id)
        assert len(alarm_manager.alarms) == 0

    def test_check_triggers_at_correct_time(self) -> None:
        clock = FakeClock(datetime(2026, 3, 30, 7, 0, 0))  # Monday 07:00
        triggered_list: list[Alarm] = []
        mgr = AlarmManager(clock=clock, on_triggered=lambda a: triggered_list.append(a))
        alarm = Alarm(hour=7, minute=0, days=list(range(7)))
        mgr.add(alarm)
        result = mgr.check()
        assert len(result) == 1
        assert len(triggered_list) == 1

    def test_check_does_not_double_fire(self) -> None:
        clock = FakeClock(datetime(2026, 3, 30, 7, 0, 0))
        mgr = AlarmManager(clock=clock)
        alarm = Alarm(hour=7, minute=0)
        mgr.add(alarm)
        mgr.check()
        result = mgr.check()  # Same minute, should not fire again
        assert len(result) == 0

    def test_multiple_alarms_simultaneous(self) -> None:
        clock = FakeClock(datetime(2026, 3, 30, 7, 0, 0))
        mgr = AlarmManager(clock=clock)
        mgr.add(Alarm(hour=7, minute=0, label="A"))
        mgr.add(Alarm(hour=7, minute=0, label="B"))
        result = mgr.check()
        assert len(result) == 2

    def test_snooze(self) -> None:
        clock = FakeClock(datetime(2026, 3, 30, 7, 0, 0))
        mgr = AlarmManager(clock=clock)
        alarm = Alarm(hour=7, minute=0)
        mgr.add(alarm)
        mgr.snooze(alarm.id, minutes=5)
        assert alarm.snooze_until is not None

    def test_serialize_deserialize(self, alarm_manager: AlarmManager) -> None:
        alarm_manager.add(Alarm(hour=7, minute=0, label="A"))
        alarm_manager.add(Alarm(hour=12, minute=30, label="B"))
        data = alarm_manager.serialize()
        new_mgr = AlarmManager()
        new_mgr.deserialize(data)
        assert len(new_mgr.alarms) == 2

    def test_on_changed_callback(self) -> None:
        changed = []
        mgr = AlarmManager(on_changed=lambda: changed.append(True))
        mgr.add(Alarm(hour=7, minute=0))
        assert len(changed) == 1
        mgr.remove(mgr.alarms[0].id)
        assert len(changed) == 2
