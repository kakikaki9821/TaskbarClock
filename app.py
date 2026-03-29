"""TaskbarClock - Windows 11 system tray clock application."""

from __future__ import annotations

import sys
from pathlib import Path

from core.config import Config
from core.crash_report import setup_sentry
from core.logger import setup_logger


def resource_path(relative: str) -> Path:
    """Get absolute path to resource, works for dev and PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative  # type: ignore[attr-defined]
    return Path(__file__).parent / relative


def main() -> int:
    """Application entry point with strict initialization order."""
    # 1. Logger
    setup_logger()

    from loguru import logger

    logger.info("TaskbarClock starting...")

    # 2. Config
    config = Config()

    # 3. Sentry
    setup_sentry()

    # 4. QApplication (must be before any QWidget)
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray
    app.setApplicationName("TaskbarClock")

    # 5. Singleton check
    from core.singleton import ensure_single_instance, release_single_instance

    if not ensure_single_instance():
        logger.error("Another instance is already running. Exiting.")
        return 1

    # 6. Theme
    from ui.theme import ThemeManager

    theme_manager = ThemeManager()
    is_dark = theme_manager.detect_and_apply(app)
    theme_manager.start_listener(app)

    # 7. Clock Renderer
    from ui.clock_renderer import ClockRenderer

    renderer = ClockRenderer()
    renderer.update_colors(is_dark)

    # 8. Services
    sound_path = resource_path("resources/alarm.wav")
    from services.notifier import Notifier
    from services.sounds import SoundPlayer

    sound_player = SoundPlayer(default_sound=sound_path if sound_path.exists() else None)

    # 9. Alarm Manager
    from clock.alarm import AlarmManager

    alarm_manager = AlarmManager()
    alarm_data = config.get("alarms", [])
    if alarm_data:
        alarm_manager.deserialize(alarm_data)

    # 10. Timer Manager
    from clock.timer_manager import TimerManager

    timer_manager = TimerManager()

    # 11. Notifier with snooze callback
    notifier = Notifier(on_snooze=lambda aid: alarm_manager.snooze(aid))

    # 12. Tray Icon
    from ui.tray_icon import TrayIcon

    tray_icon = TrayIcon(renderer)
    tray_icon.show()

    # 13. Analog Clock
    from ui.analog_clock import AnalogClock

    analog_clock = AnalogClock(renderer)

    # 14. Dialogs (lazy)
    from ui.alarm_dialog import AlarmDialog
    from ui.timer_dialog import TimerDialog

    # --- Signal/Slot connections ---

    # Tray icon activation → analog clock toggle
    def on_tray_activated(reason: object) -> None:
        from PySide6.QtWidgets import QSystemTrayIcon

        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            analog_clock.toggle_at_tray(tray_icon.geometry())

    tray_icon.activated.connect(on_tray_activated)

    # Tray menu → dialogs
    def show_alarm_dialog() -> None:
        dlg = AlarmDialog(alarm_manager.alarms)
        dlg.alarm_added.connect(alarm_manager.add)
        dlg.alarm_removed.connect(alarm_manager.remove)
        dlg.alarm_updated.connect(alarm_manager.update)
        dlg.exec()

    def show_timer_dialog() -> None:
        dlg = TimerDialog()
        dlg.start_requested.connect(lambda ms: timer_manager.start(ms))
        dlg.pause_requested.connect(timer_manager.pause)
        dlg.resume_requested.connect(timer_manager.resume)
        dlg.cancel_requested.connect(timer_manager.cancel)

        # Timer tick → dialog display
        timer_manager._on_tick = dlg.update_display
        timer_manager._on_state_changed = dlg.update_state
        timer_manager._on_finished = lambda: (
            sound_player.play(),
            notifier.show_timer_done(),
        )

        dlg.exec()
        # Cleanup callbacks
        timer_manager._on_tick = None
        timer_manager._on_state_changed = None

    tray_icon.alarm_requested.connect(show_alarm_dialog)
    tray_icon.timer_requested.connect(show_timer_dialog)
    tray_icon.quit_requested.connect(app.quit)

    # Alarm check timer (every 1 second)
    alarm_check_timer = QTimer()

    def check_alarms() -> None:
        triggered = alarm_manager.check()
        for alarm in triggered:
            sound_player.play()
            notifier.show_alarm(
                alarm.id,
                alarm.label,
                f"{alarm.hour:02d}:{alarm.minute:02d}",
            )

    alarm_check_timer.timeout.connect(check_alarms)
    alarm_check_timer.start(1000)

    # Alarm persistence
    alarm_manager._on_changed = lambda: config.set("alarms", alarm_manager.serialize())

    # Timer tick → tray tooltip
    def on_timer_tick(remaining_ms: int) -> None:
        tray_icon.update_tooltip_text(f"タイマー: {timer_manager.format_remaining()}")

    # Theme change → renderer colors
    def on_theme_changed(dark: bool) -> None:
        renderer.update_colors(dark)

    theme_manager._on_theme_changed = on_theme_changed

    # --- Run ---
    logger.info("TaskbarClock ready")
    exit_code = app.exec()

    # Cleanup
    config.save_immediate()
    release_single_instance()
    logger.info("TaskbarClock exiting with code {}", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
