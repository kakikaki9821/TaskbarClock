"""Timer settings dialog with presets and countdown display."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from clock.timer_manager import TimerState

PRESETS_MINUTES = [1, 3, 5, 10, 30]


class TimerDialog(QDialog):
    """Dialog for setting and controlling the timer."""

    start_requested = Signal(int)  # duration_ms
    pause_requested = Signal()
    resume_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("タイマー")
        self.setMinimumSize(300, 200)
        self.setAccessibleName("タイマーダイアログ")
        self.setAccessibleDescription("カウントダウンタイマーの設定と操作")
        self._state = TimerState.IDLE
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Remaining display
        self._display = QLabel("00:00")
        self._display.setStyleSheet("font-size: 48px; font-weight: bold;")
        layout.addWidget(self._display)

        # Time input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("分:"))
        self._minutes_spin = QSpinBox()
        self._minutes_spin.setRange(0, 999)
        self._minutes_spin.setValue(5)
        input_layout.addWidget(self._minutes_spin)

        input_layout.addWidget(QLabel("秒:"))
        self._seconds_spin = QSpinBox()
        self._seconds_spin.setRange(0, 59)
        self._seconds_spin.setValue(0)
        input_layout.addWidget(self._seconds_spin)
        layout.addLayout(input_layout)

        # Presets
        preset_layout = QHBoxLayout()
        for minutes in PRESETS_MINUTES:
            btn = QPushButton(f"{minutes}分")
            btn.clicked.connect(lambda checked, m=minutes: self._set_preset(m))
            preset_layout.addWidget(btn)
        layout.addLayout(preset_layout)

        # Control buttons
        ctrl_layout = QHBoxLayout()
        self._start_btn = QPushButton("開始")
        self._start_btn.clicked.connect(self._on_start)
        ctrl_layout.addWidget(self._start_btn)

        self._pause_btn = QPushButton("一時停止")
        self._pause_btn.clicked.connect(self._on_pause)
        self._pause_btn.setEnabled(False)
        ctrl_layout.addWidget(self._pause_btn)

        self._cancel_btn = QPushButton("キャンセル")
        self._cancel_btn.clicked.connect(self._on_cancel)
        self._cancel_btn.setEnabled(False)
        ctrl_layout.addWidget(self._cancel_btn)
        layout.addLayout(ctrl_layout)

    def _set_preset(self, minutes: int) -> None:
        self._minutes_spin.setValue(minutes)
        self._seconds_spin.setValue(0)

    def _on_start(self) -> None:
        minutes = self._minutes_spin.value()
        seconds = self._seconds_spin.value()
        duration_ms = (minutes * 60 + seconds) * 1000
        if duration_ms > 0:
            self.start_requested.emit(duration_ms)

    def _on_pause(self) -> None:
        if self._state == TimerState.RUNNING:
            self.pause_requested.emit()
        elif self._state == TimerState.PAUSED:
            self.resume_requested.emit()

    def _on_cancel(self) -> None:
        self.cancel_requested.emit()

    def update_display(self, remaining_ms: int) -> None:
        """Update the countdown display."""
        total_seconds = remaining_ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        self._display.setText(f"{minutes:02d}:{seconds:02d}")

    def update_state(self, state: TimerState) -> None:
        """Update button states based on timer state."""
        self._state = state
        is_idle = state == TimerState.IDLE
        is_running = state == TimerState.RUNNING
        is_paused = state == TimerState.PAUSED

        self._start_btn.setEnabled(is_idle)
        self._minutes_spin.setEnabled(is_idle)
        self._seconds_spin.setEnabled(is_idle)
        self._pause_btn.setEnabled(is_running or is_paused)
        self._cancel_btn.setEnabled(is_running or is_paused)

        if is_paused:
            self._pause_btn.setText("再開")
        else:
            self._pause_btn.setText("一時停止")

        if is_idle:
            self._display.setText("00:00")
