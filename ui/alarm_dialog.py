"""Alarm settings dialog."""

from __future__ import annotations

from PySide6.QtCore import QTime, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from clock.alarm import Alarm

WEEKDAY_NAMES = ["月", "火", "水", "木", "金", "土", "日"]


class AlarmDialog(QDialog):
    """Dialog for managing alarms."""

    alarm_added = Signal(object)  # Alarm
    alarm_removed = Signal(str)  # alarm_id
    alarm_updated = Signal(object)  # Alarm

    def __init__(self, alarms: list[Alarm], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("アラーム設定")
        self.setMinimumSize(350, 400)
        self.setAccessibleName("アラーム設定ダイアログ")
        self.setAccessibleDescription("アラームの追加、削除、有効/無効の切り替え")
        self._alarms = {a.id: a for a in alarms}
        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Alarm list
        self._list = QListWidget()
        layout.addWidget(self._list)

        # Time picker
        time_layout = QHBoxLayout()
        self._time_edit = QTimeEdit()
        self._time_edit.setDisplayFormat("HH:mm")
        self._time_edit.setTime(QTime(7, 0))
        time_layout.addWidget(QLabel("時刻:"))
        time_layout.addWidget(self._time_edit)
        layout.addLayout(time_layout)

        # Weekday checkboxes
        days_layout = QHBoxLayout()
        self._day_checks: list[QCheckBox] = []
        for i, name in enumerate(WEEKDAY_NAMES):
            cb = QCheckBox(name)
            cb.setChecked(True)
            self._day_checks.append(cb)
            days_layout.addWidget(cb)
        layout.addLayout(days_layout)

        # Buttons
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("追加")
        add_btn.clicked.connect(self._add_alarm)
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton("削除")
        remove_btn.clicked.connect(self._remove_alarm)
        btn_layout.addWidget(remove_btn)

        toggle_btn = QPushButton("ON/OFF")
        toggle_btn.clicked.connect(self._toggle_alarm)
        btn_layout.addWidget(toggle_btn)

        layout.addLayout(btn_layout)

        # Close
        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _add_alarm(self) -> None:
        time = self._time_edit.time()
        days = [i for i, cb in enumerate(self._day_checks) if cb.isChecked()]
        alarm = Alarm(hour=time.hour(), minute=time.minute(), days=days)
        self._alarms[alarm.id] = alarm
        self.alarm_added.emit(alarm)
        self._refresh_list()

    def _remove_alarm(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        alarm_id = item.data(256)  # Qt.ItemDataRole.UserRole
        if alarm_id and alarm_id in self._alarms:
            del self._alarms[alarm_id]
            self.alarm_removed.emit(alarm_id)
            self._refresh_list()

    def _toggle_alarm(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        alarm_id = item.data(256)
        if alarm_id and alarm_id in self._alarms:
            alarm = self._alarms[alarm_id]
            alarm.enabled = not alarm.enabled
            self.alarm_updated.emit(alarm)
            self._refresh_list()

    def _refresh_list(self) -> None:
        self._list.clear()
        for alarm in self._alarms.values():
            days_str = ",".join(WEEKDAY_NAMES[d] for d in sorted(alarm.days))
            status = "ON" if alarm.enabled else "OFF"
            text = f"[{status}] {alarm.hour:02d}:{alarm.minute:02d} ({days_str})"
            if alarm.label:
                text += f" - {alarm.label}"
            item = QListWidgetItem(text)
            item.setData(256, alarm.id)
            self._list.addItem(item)
