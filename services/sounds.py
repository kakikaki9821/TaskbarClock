"""Sound playback with 3-level fallback: QMediaPlayer → winsound → SystemBeep."""

from __future__ import annotations

import sys
import threading
from pathlib import Path

from loguru import logger


class SoundPlayer:
    """Plays alarm/timer sounds with fallback chain."""

    def __init__(self, default_sound: Path | None = None) -> None:
        self._default_sound = default_sound
        self._qt_player: object | None = None
        self._playing = False

    def play(self, sound_path: Path | None = None) -> None:
        """Play a sound file. Falls back through available methods."""
        path = sound_path or self._default_sound

        # Try QMediaPlayer first
        if self._try_qt_media(path):
            return

        # Fallback to winsound (Windows only, in separate thread)
        if sys.platform == "win32" and path and self._try_winsound(path):
            return

        # Final fallback: system beep
        self._system_beep()

    def stop(self) -> None:
        """Stop current playback."""
        self._playing = False
        if self._qt_player is not None:
            try:
                self._qt_player.stop()  # type: ignore[union-attr]
            except Exception:
                pass

    def is_playing(self) -> bool:
        """Check if sound is currently playing."""
        return self._playing

    def _try_qt_media(self, path: Path | None) -> bool:
        """Try playing with QMediaPlayer."""
        if path is None or not path.exists():
            return False
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

            if self._qt_player is None:
                self._qt_player = QMediaPlayer()
                audio = QAudioOutput()
                self._qt_player.setAudioOutput(audio)  # type: ignore[union-attr]

            self._qt_player.setSource(QUrl.fromLocalFile(str(path)))  # type: ignore[union-attr]
            self._qt_player.play()  # type: ignore[union-attr]
            self._playing = True
            logger.debug("Playing sound via QMediaPlayer: {}", path)
            return True
        except Exception as e:
            logger.debug("QMediaPlayer failed: {}", e)
            return False

    def _try_winsound(self, path: Path) -> bool:
        """Try playing with winsound in a separate thread."""
        try:
            import winsound

            def _play() -> None:
                try:
                    winsound.PlaySound(str(path), winsound.SND_FILENAME)
                    self._playing = False
                except Exception as e:
                    logger.debug("winsound failed: {}", e)
                    self._system_beep()

            self._playing = True
            thread = threading.Thread(target=_play, daemon=True)
            thread.start()
            logger.debug("Playing sound via winsound: {}", path)
            return True
        except ImportError:
            return False

    def _system_beep(self) -> None:
        """Final fallback: system beep."""
        try:
            if sys.platform == "win32":
                import winsound

                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                logger.debug("Played system beep (fallback)")
            else:
                print("\a", end="", flush=True)
        except Exception as e:
            logger.warning("All sound methods failed: {}", e)
        self._playing = False
