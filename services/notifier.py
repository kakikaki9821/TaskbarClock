"""Toast notification service using win11toast (thread-safe)."""

from __future__ import annotations

import sys
from collections.abc import Callable

from loguru import logger


class Notifier:
    """Windows 11 toast notifications with thread-safe callbacks."""

    def __init__(
        self,
        on_snooze: Callable[[str], None] | None = None,
    ) -> None:
        self._on_snooze = on_snooze

    def show_alarm(self, alarm_id: str, label: str, time_str: str) -> None:
        """Show alarm notification with snooze button."""
        title = "アラーム"
        body = f"{time_str} - {label}" if label else time_str
        self._show_toast(title, body, alarm_id=alarm_id, show_snooze=True)

    def show_timer_done(self) -> None:
        """Show timer completion notification."""
        self._show_toast("タイマー", "タイマーが終了しました")

    def _show_toast(
        self,
        title: str,
        body: str,
        alarm_id: str = "",
        show_snooze: bool = False,
    ) -> None:
        """Display a Windows toast notification."""
        if sys.platform != "win32":
            logger.info("Toast (non-Windows): {} - {}", title, body)
            return

        try:
            from win11toast import notify

            buttons = []
            if show_snooze and alarm_id:
                buttons = ["スヌーズ (5分)", "閉じる"]

            def on_click(args: dict) -> None:  # type: ignore[type-arg]
                if args.get("arguments") == "スヌーズ (5分)" and self._on_snooze:
                    self._on_snooze(alarm_id)

            if buttons:
                notify(
                    title,
                    body,
                    buttons=buttons,
                    on_click=on_click if show_snooze else None,
                )
            else:
                notify(title, body)

            logger.debug("Toast shown: {} - {}", title, body)
        except ImportError:
            logger.info("win11toast not available: {} - {}", title, body)
        except Exception as e:
            logger.warning("Toast notification failed: {}", e)
