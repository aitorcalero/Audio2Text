import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config_manager import ConfigManager


class ConfigManagerSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.config_name = "unit_config.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _build_manager(self, explicit_path: Path | None = None) -> ConfigManager:
        env = {}
        if explicit_path is not None:
            env["AUDIO2TEXT_CONFIG"] = str(explicit_path)
        with patch.dict(os.environ, env, clear=True):
            return ConfigManager(config_file=self.config_name)

    def test_loads_valid_explicit_json_config(self) -> None:
        config_path = self.temp_path / "valid_config.json"
        config_path.write_text(
            json.dumps(
                {
                    "TRANSCRIPTION_SERVICE": "elevenlabs",
                    "FILE_SIZE_LIMIT_MB": 12,
                }
            ),
            encoding="utf-8",
        )

        manager = self._build_manager(config_path)

        self.assertEqual(manager.get("TRANSCRIPTION_SERVICE"), "elevenlabs")
        self.assertEqual(manager.get_int("FILE_SIZE_LIMIT_MB"), 12)
        self.assertEqual(manager.get("OPENAI_ENGINE"), "gpt-4o-mini")

    def test_skips_non_json_config_without_opening_it(self) -> None:
        unsafe_path = self.temp_path / "ffmpeg.exe"
        unsafe_path.write_bytes(b"MZ" + (b"\x00" * 32))

        with patch("builtins.open", side_effect=AssertionError("no debe abrirse")) as mocked_open:
            manager = self._build_manager(unsafe_path)

        mocked_open.assert_not_called()
        self.assertEqual(manager.get("TRANSCRIPTION_SERVICE"), "openai")

    def test_skips_oversized_json_config_without_opening_it(self) -> None:
        oversized_path = self.temp_path / "oversized.json"
        oversized_path.write_text("{}", encoding="utf-8")

        with patch.object(ConfigManager, "MAX_CONFIG_SIZE_BYTES", 1):
            with patch("builtins.open", side_effect=AssertionError("no debe abrirse")) as mocked_open:
                manager = self._build_manager(oversized_path)

        mocked_open.assert_not_called()
        self.assertEqual(manager.get_int("FILE_SIZE_LIMIT_MB"), 24)

    def test_ignores_invalid_json_and_uses_defaults(self) -> None:
        invalid_path = self.temp_path / "broken.json"
        invalid_path.write_text("{ invalid json", encoding="utf-8")

        manager = self._build_manager(invalid_path)

        self.assertEqual(manager.get("TRANSCRIPTION_SERVICE"), "openai")
        self.assertEqual(manager.get_int("FILE_SIZE_LIMIT_MB"), 24)

    def test_rejects_json_that_is_not_an_object(self) -> None:
        invalid_shape_path = self.temp_path / "list_config.json"
        invalid_shape_path.write_text(json.dumps(["openai"]), encoding="utf-8")

        manager = self._build_manager(invalid_shape_path)

        self.assertEqual(manager.get("TRANSCRIPTION_SERVICE"), "openai")
        self.assertEqual(manager.get_int("FILE_SIZE_LIMIT_MB"), 24)


if __name__ == "__main__":
    unittest.main()
