"""Unit tests for sound player (mocked)."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from services.sounds import SoundPlayer


class TestSoundPlayer:
    def test_play_with_no_file(self) -> None:
        player = SoundPlayer(default_sound=None)
        with (
            patch.object(player, "_system_beep") as mock_beep,
            patch.object(player, "_try_winsound", return_value=False),
        ):
            player.play()
            mock_beep.assert_called_once()

    def test_play_nonexistent_file(self, tmp_path: Path) -> None:
        player = SoundPlayer(default_sound=tmp_path / "nonexistent.wav")
        with (
            patch.object(player, "_try_winsound", return_value=False),
            patch.object(player, "_system_beep") as mock_beep,
        ):
            player.play()
            mock_beep.assert_called_once()

    def test_stop(self) -> None:
        player = SoundPlayer()
        player._playing = True
        player.stop()
        assert player.is_playing() is False

    def test_is_playing_default(self) -> None:
        player = SoundPlayer()
        assert player.is_playing() is False

    def test_fallback_chain_qt_success(self, tmp_path: Path) -> None:
        """When QMediaPlayer succeeds, winsound and beep are not called."""
        player = SoundPlayer()
        with (
            patch.object(player, "_try_qt_media", return_value=True) as mock_qt,
            patch.object(player, "_try_winsound") as mock_win,
            patch.object(player, "_system_beep") as mock_beep,
        ):
            player.play(tmp_path / "test.wav")
            mock_qt.assert_called_once()
            mock_win.assert_not_called()
            mock_beep.assert_not_called()

    @pytest.mark.skipif(sys.platform != "win32", reason="winsound only on Windows")
    def test_fallback_chain_winsound_success(self, tmp_path: Path) -> None:
        """When QMediaPlayer fails but winsound succeeds (Windows only)."""
        player = SoundPlayer()
        with (
            patch.object(player, "_try_qt_media", return_value=False),
            patch.object(player, "_try_winsound", return_value=True) as mock_win,
            patch.object(player, "_system_beep") as mock_beep,
        ):
            player.play(tmp_path / "test.wav")
            mock_win.assert_called_once()
            mock_beep.assert_not_called()
