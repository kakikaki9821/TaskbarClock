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


class ApplicationController:
    """Orchestrates application initialization and signal wiring."""

    def __init__(self, config: Config) -> None:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication

        self._config = config
        self._app = QApplication(sys.argv)
        self._app.setQuitOnLastWindowClosed(False)
        self._app.setApplicationName("TaskbarClock")

        # Singleton
        from core.singleton import ensure_single_instance

        if not ensure_single_instance():
            from loguru import logger

            logger.error("Another instance is already running. Exiting.")
            raise SystemExit(1)

        # Theme
        from ui.theme import ThemeManager

        self._theme_manager = ThemeManager(on_theme_changed=self._on_theme_changed)
        is_dark = self._theme_manager.detect_and_apply(self._app)
        self._theme_manager.start_listener(self._app)

        # Renderer
        from ui.clock_renderer import ClockRenderer

        self._renderer = ClockRenderer()
        self._renderer.update_colors(is_dark)

        # Services
        from services.notifier import Notifier
        from services.sounds import SoundPlayer

        sound_path = resource_path("resources/alarm.wav")
        self._sound_player = SoundPlayer(default_sound=sound_path if sound_path.exists() else None)

        # Alarm Manager
        from clock.alarm import AlarmManager

        self._alarm_manager = AlarmManager()
        alarm_data = config.get("alarms", [])
        if alarm_data:
            self._alarm_manager.deserialize(alarm_data)
        self._alarm_manager.on_changed = lambda: config.set(
            "alarms", self._alarm_manager.serialize()
        )

        # Timer Manager (autonomous tick via QTimer)
        from clock.timer_manager import TimerManager

        self._timer_manager = TimerManager()
        self._timer_manager.on_tick(self._on_timer_tick)
        self._timer_manager.on_finished(self._on_timer_finished)

        # Timer tick driver (always running, independent of dialogs)
        self._timer_tick_driver = QTimer()
        self._timer_tick_driver.setInterval(100)
        self._timer_tick_driver.timeout.connect(lambda: self._timer_manager.tick(100))
        self._timer_tick_driver.start()

        # Notifier
        self._notifier = Notifier(on_snooze=lambda aid: self._alarm_manager.snooze(aid))

        # UI: Tray Icon
        from ui.tray_icon import TrayIcon

        self._tray_icon = TrayIcon(self._renderer)
        self._tray_icon.show()

        # UI: Floating Clock Widget
        from ui.taskbar_clock_widget import TaskbarClockWidget

        clock_size = config.get("clock_size", "medium")
        clock_style = config.get("clock_style", "default")
        self._clock_widget = TaskbarClockWidget(size_preset=clock_size, style_name=clock_style)
        self._clock_widget.update_colors(is_dark)
        saved_pos = config.get("clock_position")
        if saved_pos and isinstance(saved_pos, list) and len(saved_pos) == 2:
            self._clock_widget.set_position(saved_pos[0], saved_pos[1])
        self._clock_widget.show()

        # UI: Analog Clock
        from ui.analog_clock import AnalogClock

        self._analog_clock = AnalogClock(self._renderer)

        # Alarm check timer
        self._alarm_check_timer = QTimer()
        self._alarm_check_timer.timeout.connect(self._check_alarms)
        self._alarm_check_timer.start(1000)

        # Wire signals
        self._connect_signals()

        from loguru import logger

        logger.info("TaskbarClock ready")

    def _connect_signals(self) -> None:
        """Wire all signal/slot connections."""
        # Tray icon
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.alarm_requested.connect(self._show_alarm_dialog)
        self._tray_icon.timer_requested.connect(self._show_timer_dialog)
        self._tray_icon.quit_requested.connect(self._app.quit)

        # Floating clock widget
        self._clock_widget.left_clicked.connect(lambda: self._analog_clock.toggle_at_tray())
        self._clock_widget.alarm_requested.connect(self._show_alarm_dialog)
        self._clock_widget.timer_requested.connect(self._show_timer_dialog)
        self._clock_widget.quit_requested.connect(self._app.quit)
        self._clock_widget.size_changed.connect(lambda s: self._config.set("clock_size", s))
        self._clock_widget.style_changed.connect(lambda s: self._config.set("clock_style", s))

    def _on_tray_activated(self, reason: object) -> None:
        from PySide6.QtWidgets import QSystemTrayIcon

        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._analog_clock.toggle_at_tray(self._tray_icon.geometry())

    def _show_alarm_dialog(self) -> None:
        from ui.alarm_dialog import AlarmDialog

        dlg = AlarmDialog(self._alarm_manager.alarms)
        dlg.alarm_added.connect(self._alarm_manager.add)
        dlg.alarm_removed.connect(self._alarm_manager.remove)
        dlg.alarm_updated.connect(self._alarm_manager.update)
        dlg.exec()

    def _show_timer_dialog(self) -> None:
        from ui.timer_dialog import TimerDialog

        dlg = TimerDialog()
        dlg.start_requested.connect(lambda ms: self._timer_manager.start(ms))
        dlg.pause_requested.connect(self._timer_manager.pause)
        dlg.resume_requested.connect(self._timer_manager.resume)
        dlg.cancel_requested.connect(self._timer_manager.cancel)

        # Register dialog as listener (removed when dialog closes)
        self._timer_manager.on_tick(dlg.update_display)
        self._timer_manager.on_state_changed(dlg.update_state)

        # Sync current state to dialog
        dlg.update_state(self._timer_manager.state)
        dlg.update_display(self._timer_manager.remaining_ms)

        dlg.exec()

        # Cleanup dialog listeners
        self._timer_manager.remove_tick_listener(dlg.update_display)
        self._timer_manager.remove_state_listener(dlg.update_state)

    def _check_alarms(self) -> None:
        triggered = self._alarm_manager.check()
        for alarm in triggered:
            self._sound_player.play()
            self._notifier.show_alarm(alarm.id, alarm.label, f"{alarm.hour:02d}:{alarm.minute:02d}")

    def _on_timer_tick(self, remaining_ms: int) -> None:
        self._tray_icon.update_tooltip_text(f"タイマー: {self._timer_manager.format_remaining()}")

    def _on_timer_finished(self) -> None:
        self._sound_player.play()
        self._notifier.show_timer_done()
        self._tray_icon.update_tooltip_text("TaskbarClock")

    def _on_theme_changed(self, dark: bool) -> None:
        self._renderer.update_colors(dark)
        self._clock_widget.update_colors(dark)

    def run(self) -> int:
        """Run the application event loop."""
        exit_code = self._app.exec()
        self._shutdown()
        return exit_code

    def _shutdown(self) -> None:
        """Save state and cleanup."""
        from loguru import logger

        from core.singleton import release_single_instance

        pos = self._clock_widget.pos()
        self._config.set("clock_position", [pos.x(), pos.y()])
        self._config.save_immediate()
        release_single_instance()
        logger.info("TaskbarClock exiting")


def main() -> int:
    """Application entry point."""
    # 1. Logger (first — captures all subsequent errors)
    setup_logger()

    from loguru import logger

    logger.info("TaskbarClock starting...")

    # 2. Config
    config = Config()

    # 3. Sentry
    setup_sentry()

    # 4. Application
    try:
        controller = ApplicationController(config)
        return controller.run()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    except Exception:
        logger.exception("Fatal error during startup")
        try:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(
                None, "TaskbarClock", "起動中にエラーが発生しました。\nログを確認してください。"
            )
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
