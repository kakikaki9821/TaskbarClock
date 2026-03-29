"""Alarm data model and manager. Pure logic, no Qt dependency."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class Alarm:
    """Single alarm definition."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    hour: int = 7
    minute: int = 0
    days: list[int] = field(default_factory=lambda: list(range(7)))  # 0=Mon..6=Sun
    enabled: bool = True
    label: str = ""
    snooze_until: datetime | None = None

    def __post_init__(self) -> None:
        """Validate alarm fields."""
        if not (0 <= self.hour <= 23):
            raise ValueError(f"hour must be 0-23, got {self.hour}")
        if not (0 <= self.minute <= 59):
            raise ValueError(f"minute must be 0-59, got {self.minute}")
        if not all(0 <= d <= 6 for d in self.days):
            raise ValueError(f"days must be 0-6 (Mon-Sun), got {self.days}")

    def matches(self, now: datetime) -> bool:
        """Check if this alarm should fire at the given time."""
        if not self.enabled:
            return False
        if now.weekday() not in self.days:
            return False
        if now.hour != self.hour or now.minute != self.minute:
            return False
        if self.snooze_until is not None and now < self.snooze_until:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "id": self.id,
            "hour": self.hour,
            "minute": self.minute,
            "days": self.days,
            "enabled": self.enabled,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Alarm:
        """Deserialize from dict."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            hour=data.get("hour", 7),
            minute=data.get("minute", 0),
            days=data.get("days", list(range(7))),
            enabled=data.get("enabled", True),
            label=data.get("label", ""),
        )


class AlarmManager:
    """Manages multiple alarms. Uses injected clock for testability."""

    def __init__(
        self,
        clock: Callable[[], datetime] | None = None,
        on_triggered: Callable[[Alarm], None] | None = None,
        on_changed: Callable[[], None] | None = None,
    ) -> None:
        self._clock = clock or datetime.now
        self._alarms: dict[str, Alarm] = {}
        self._on_triggered = on_triggered
        self._on_changed = on_changed
        self._last_trigger_minute: tuple[int, int] = (-1, -1)

    @property
    def on_changed(self) -> Callable[[], None] | None:
        """Callback invoked when alarms are added/removed/updated."""
        return self._on_changed

    @on_changed.setter
    def on_changed(self, callback: Callable[[], None] | None) -> None:
        self._on_changed = callback

    @property
    def alarms(self) -> list[Alarm]:
        """Get all alarms."""
        return list(self._alarms.values())

    def add(self, alarm: Alarm) -> None:
        """Add a new alarm."""
        self._alarms[alarm.id] = alarm
        if self._on_changed:
            self._on_changed()

    def remove(self, alarm_id: str) -> None:
        """Remove an alarm by ID."""
        self._alarms.pop(alarm_id, None)
        if self._on_changed:
            self._on_changed()

    def update(self, alarm: Alarm) -> None:
        """Update an existing alarm."""
        if alarm.id in self._alarms:
            self._alarms[alarm.id] = alarm
            if self._on_changed:
                self._on_changed()

    def snooze(self, alarm_id: str, minutes: int = 5) -> None:
        """Snooze an alarm for the given minutes."""
        alarm = self._alarms.get(alarm_id)
        if alarm:
            alarm.snooze_until = self._clock() + timedelta(minutes=minutes)

    def check(self) -> list[Alarm]:
        """Check all alarms against current time. Returns triggered alarms."""
        now = self._clock()
        current_minute = (now.hour, now.minute)

        # Only trigger once per minute
        if current_minute == self._last_trigger_minute:
            return []
        self._last_trigger_minute = current_minute

        triggered: list[Alarm] = []
        for alarm in self._alarms.values():
            if alarm.matches(now):
                triggered.append(alarm)
                if self._on_triggered:
                    self._on_triggered(alarm)

        return triggered

    def serialize(self) -> list[dict[str, Any]]:
        """Serialize all alarms to list of dicts."""
        return [a.to_dict() for a in self._alarms.values()]

    def deserialize(self, data: list[dict[str, Any]]) -> None:
        """Load alarms from list of dicts."""
        self._alarms.clear()
        for item in data:
            alarm = Alarm.from_dict(item)
            self._alarms[alarm.id] = alarm
