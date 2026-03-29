"""Unit tests for configuration management."""

import json
import time
from pathlib import Path

from core.config import DEFAULT_CONFIG, Config


class TestConfig:
    def test_load_default_on_missing_file(self, tmp_path: Path) -> None:
        config = Config(path=tmp_path / "nonexistent" / "config.json")
        assert config.get("theme") == DEFAULT_CONFIG["theme"]

    def test_load_default_on_corrupted_json(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text("NOT VALID JSON {{{", encoding="utf-8")
        config = Config(path=config_path)
        assert config.get("theme") == DEFAULT_CONFIG["theme"]
        # Check corrupted backup exists
        assert (tmp_path / "config.json.corrupted").exists()

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config = Config(path=config_path)
        config.set("theme", "dark")
        config.save_immediate()

        config2 = Config(path=config_path)
        assert config2.get("theme") == "dark"

    def test_atomic_write_produces_valid_json(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config = Config(path=config_path)
        config.set("test_key", "test_value")
        config.save_immediate()

        raw = config_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        assert data["test_key"] == "test_value"

    def test_debounce_multiple_saves(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config = Config(path=config_path)

        # Multiple rapid saves
        config.set("a", 1)
        config.set("b", 2)
        config.set("c", 3)

        # Wait for debounce
        time.sleep(0.7)

        # Should have saved the last values
        config2 = Config(path=config_path)
        assert config2.get("c") == 3

    def test_alarm_persistence(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config = Config(path=config_path)
        alarms = [
            {"id": "test1", "hour": 7, "minute": 0, "days": [0, 1], "enabled": True, "label": ""}
        ]
        config.set("alarms", alarms)
        config.save_immediate()

        config2 = Config(path=config_path)
        assert config2.get("alarms") == alarms

    def test_get_with_default(self, tmp_path: Path) -> None:
        config = Config(path=tmp_path / "config.json")
        assert config.get("nonexistent", "fallback") == "fallback"

    def test_data_returns_copy(self, tmp_path: Path) -> None:
        config = Config(path=tmp_path / "config.json")
        data = config.data
        data["hacked"] = True
        assert config.get("hacked") is None
