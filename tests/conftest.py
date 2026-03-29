"""Shared test fixtures."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from clock.alarm import Alarm, AlarmManager
from clock.timer_manager import TimerManager
from core.config import Config


class FakeClock:
    """Controllable clock for testing."""

    def __init__(self, initial: datetime | None = None) -> None:
        self._now = initial or datetime(2026, 3, 29, 12, 0, 0)

    def __call__(self) -> datetime:
        return self._now

    def set(self, dt: datetime) -> None:
        self._now = dt

    def advance_seconds(self, seconds: int) -> None:
        from datetime import timedelta

        self._now += timedelta(seconds=seconds)

    def advance_minutes(self, minutes: int) -> None:
        from datetime import timedelta

        self._now += timedelta(minutes=minutes)


@pytest.fixture
def fake_clock() -> FakeClock:
    """Controllable clock starting at 2026-03-29 12:00:00."""
    return FakeClock()


@pytest.fixture
def mock_config(tmp_path: Path) -> Config:
    """Config using a temporary directory."""
    return Config(path=tmp_path / "config.json")


@pytest.fixture
def alarm_manager(fake_clock: FakeClock) -> AlarmManager:
    """AlarmManager with fake clock."""
    return AlarmManager(clock=fake_clock)


@pytest.fixture
def timer_manager() -> TimerManager:
    """Fresh TimerManager."""
    return TimerManager()


@pytest.fixture
def mock_sound_player() -> MagicMock:
    """Mock SoundPlayer."""
    player = MagicMock()
    player.play = MagicMock()
    player.stop = MagicMock()
    player.is_playing = MagicMock(return_value=False)
    return player


@pytest.fixture
def mock_notifier() -> MagicMock:
    """Mock Notifier."""
    return MagicMock()


@pytest.fixture
def sample_alarm() -> Alarm:
    """Sample alarm at 07:00, all weekdays."""
    return Alarm(hour=7, minute=0, days=list(range(7)), label="Morning")


@pytest.fixture
def sample_alarm_monday() -> Alarm:
    """Sample alarm at 08:30, Monday only."""
    return Alarm(hour=8, minute=30, days=[0], label="Monday meeting")
