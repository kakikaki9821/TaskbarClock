"""Unit tests for timer state machine."""

from clock.timer_manager import TimerManager, TimerState


class TestTimerManager:
    def test_initial_state_is_idle(self, timer_manager: TimerManager) -> None:
        assert timer_manager.state == TimerState.IDLE

    def test_start_transitions_to_running(self, timer_manager: TimerManager) -> None:
        assert timer_manager.start(60000) is True
        assert timer_manager.state == TimerState.RUNNING

    def test_pause_transitions_to_paused(self, timer_manager: TimerManager) -> None:
        timer_manager.start(60000)
        assert timer_manager.pause() is True
        assert timer_manager.state == TimerState.PAUSED

    def test_resume_transitions_to_running(self, timer_manager: TimerManager) -> None:
        timer_manager.start(60000)
        timer_manager.pause()
        assert timer_manager.resume() is True
        assert timer_manager.state == TimerState.RUNNING

    def test_cancel_from_running(self, timer_manager: TimerManager) -> None:
        timer_manager.start(60000)
        assert timer_manager.cancel() is True
        assert timer_manager.state == TimerState.IDLE

    def test_cancel_from_paused(self, timer_manager: TimerManager) -> None:
        timer_manager.start(60000)
        timer_manager.pause()
        assert timer_manager.cancel() is True
        assert timer_manager.state == TimerState.IDLE

    def test_countdown_reaches_zero(self, timer_manager: TimerManager) -> None:
        finished = []
        timer_manager._on_finished = lambda: finished.append(True)
        timer_manager.start(1000)
        timer_manager.tick(500)
        assert timer_manager.state == TimerState.RUNNING
        timer_manager.tick(600)
        assert timer_manager.state == TimerState.FINISHED
        assert len(finished) == 1

    def test_tick_emits_remaining_ms(self) -> None:
        ticks: list[int] = []
        mgr = TimerManager(on_tick=lambda ms: ticks.append(ms))
        mgr.start(5000)
        mgr.tick(1000)
        mgr.tick(1000)
        assert ticks == [4000, 3000]

    def test_cannot_start_when_running(self, timer_manager: TimerManager) -> None:
        timer_manager.start(60000)
        assert timer_manager.start(30000) is False

    def test_cannot_pause_when_idle(self, timer_manager: TimerManager) -> None:
        assert timer_manager.pause() is False

    def test_cannot_resume_when_running(self, timer_manager: TimerManager) -> None:
        timer_manager.start(60000)
        assert timer_manager.resume() is False

    def test_dismiss_from_finished(self, timer_manager: TimerManager) -> None:
        timer_manager.start(100)
        timer_manager.tick(200)
        assert timer_manager.state == TimerState.FINISHED
        assert timer_manager.dismiss() is True
        assert timer_manager.state == TimerState.IDLE

    def test_dismiss_from_non_finished(self, timer_manager: TimerManager) -> None:
        assert timer_manager.dismiss() is False

    def test_format_remaining(self, timer_manager: TimerManager) -> None:
        timer_manager.start(125000)  # 2:05
        assert timer_manager.format_remaining() == "02:05"

    def test_state_changed_callback(self) -> None:
        states: list[TimerState] = []
        mgr = TimerManager(on_state_changed=lambda s: states.append(s))
        mgr.start(1000)
        mgr.pause()
        mgr.resume()
        mgr.cancel()
        assert states == [
            TimerState.RUNNING,
            TimerState.PAUSED,
            TimerState.RUNNING,
            TimerState.IDLE,
        ]

    def test_tick_ignored_when_not_running(self, timer_manager: TimerManager) -> None:
        timer_manager.tick(1000)  # IDLE — should be ignored
        assert timer_manager.remaining_ms == 0

    def test_remaining_does_not_go_negative(self, timer_manager: TimerManager) -> None:
        timer_manager.start(500)
        timer_manager.tick(1000)
        assert timer_manager.remaining_ms == 0
