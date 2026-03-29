"""Timer countdown manager with explicit state machine and autonomous tick."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum, auto


class TimerState(Enum):
    """Timer states."""

    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    FINISHED = auto()


class TimerManager:
    """Countdown timer with state machine.

    State transitions:
        IDLE → RUNNING (start)
        RUNNING → PAUSED (pause)
        PAUSED → RUNNING (resume)
        RUNNING → FINISHED (count reaches 0)
        RUNNING → IDLE (cancel)
        PAUSED → IDLE (cancel)
        FINISHED → IDLE (dismiss)
    """

    def __init__(self) -> None:
        self._state = TimerState.IDLE
        self._remaining_ms: int = 0
        self._total_ms: int = 0
        self._tick_listeners: list[Callable[[int], None]] = []
        self._finished_listeners: list[Callable[[], None]] = []
        self._state_listeners: list[Callable[[TimerState], None]] = []

    @property
    def state(self) -> TimerState:
        """Current timer state."""
        return self._state

    @property
    def remaining_ms(self) -> int:
        """Remaining time in milliseconds."""
        return self._remaining_ms

    @property
    def total_ms(self) -> int:
        """Total time set in milliseconds."""
        return self._total_ms

    # --- Listener registration (multi-listener support) ---

    def on_tick(self, callback: Callable[[int], None]) -> None:
        """Register a tick listener."""
        self._tick_listeners.append(callback)

    def on_finished(self, callback: Callable[[], None]) -> None:
        """Register a finished listener."""
        self._finished_listeners.append(callback)

    def on_state_changed(self, callback: Callable[[TimerState], None]) -> None:
        """Register a state change listener."""
        self._state_listeners.append(callback)

    def remove_tick_listener(self, callback: Callable[[int], None]) -> None:
        """Remove a tick listener."""
        try:
            self._tick_listeners.remove(callback)
        except ValueError:
            pass

    def remove_state_listener(self, callback: Callable[[TimerState], None]) -> None:
        """Remove a state change listener."""
        try:
            self._state_listeners.remove(callback)
        except ValueError:
            pass

    def _notify_tick(self, remaining: int) -> None:
        for cb in self._tick_listeners:
            cb(remaining)

    def _notify_finished(self) -> None:
        for cb in self._finished_listeners:
            cb()

    def _notify_state_changed(self, state: TimerState) -> None:
        for cb in self._state_listeners:
            cb(state)

    # --- State transitions ---

    def _set_state(self, new_state: TimerState) -> None:
        """Set state and notify listeners."""
        self._state = new_state
        self._notify_state_changed(new_state)

    def start(self, duration_ms: int) -> bool:
        """Start countdown. Returns False if not in IDLE state."""
        if self._state != TimerState.IDLE:
            return False
        self._total_ms = duration_ms
        self._remaining_ms = duration_ms
        self._set_state(TimerState.RUNNING)
        return True

    def pause(self) -> bool:
        """Pause countdown. Returns False if not RUNNING."""
        if self._state != TimerState.RUNNING:
            return False
        self._set_state(TimerState.PAUSED)
        return True

    def resume(self) -> bool:
        """Resume countdown. Returns False if not PAUSED."""
        if self._state != TimerState.PAUSED:
            return False
        self._set_state(TimerState.RUNNING)
        return True

    def cancel(self) -> bool:
        """Cancel countdown. Returns False if IDLE or FINISHED."""
        if self._state in (TimerState.IDLE, TimerState.FINISHED):
            return False
        self._remaining_ms = 0
        self._set_state(TimerState.IDLE)
        return True

    def dismiss(self) -> bool:
        """Dismiss finished timer. Returns False if not FINISHED."""
        if self._state != TimerState.FINISHED:
            return False
        self._remaining_ms = 0
        self._set_state(TimerState.IDLE)
        return True

    def tick(self, elapsed_ms: int) -> None:
        """Called periodically to advance the countdown."""
        if self._state != TimerState.RUNNING:
            return

        self._remaining_ms = max(0, self._remaining_ms - elapsed_ms)
        self._notify_tick(self._remaining_ms)

        if self._remaining_ms <= 0:
            self._set_state(TimerState.FINISHED)
            self._notify_finished()

    def format_remaining(self) -> str:
        """Format remaining time as MM:SS."""
        total_seconds = self._remaining_ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
