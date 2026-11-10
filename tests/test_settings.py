import json
import tempfile
import unittest
from pathlib import Path

from bkp_cli.settings import Settings, is_target_valid, load_settings, save_settings


class TestLoadSettings(unittest.TestCase):
    def test_creates_defaults_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "settings.json")
            settings = load_settings(path)
            self.assertEqual(settings, Settings(source="", target="", whitelist=[]))
            self.assertTrue(Path(path).exists())

    def test_loads_existing_valid_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "settings.json")
            Path(path).write_text(
                json.dumps({"source": "C:\\src", "target": "C:\\dst", "whitelist": ["C:\\dst"]}),
                encoding="utf-8",
            )
            settings = load_settings(path)
            self.assertEqual(settings.source, "C:\\src")
            self.assertEqual(settings.target, "C:\\dst")
            self.assertEqual(settings.whitelist, ["C:\\dst"])

    def test_malformed_json_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "settings.json")
            Path(path).write_text("{not valid json", encoding="utf-8")
            settings = load_settings(path)
            self.assertEqual(settings, Settings(source="", target="", whitelist=[]))
            # file should not be overwritten
            self.assertEqual(Path(path).read_text(encoding="utf-8"), "{not valid json")

    def test_missing_keys_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "settings.json")
            Path(path).write_text(json.dumps({"source": "C:\\src"}), encoding="utf-8")
            settings = load_settings(path)
            self.assertEqual(settings, Settings(source="", target="", whitelist=[]))


class TestSaveSettings(unittest.TestCase):
    def test_writes_formatted_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "settings.json")
            settings = Settings(source="C:\\src", target="C:\\dst", whitelist=["C:\\dst"])
            save_settings(settings, path)
            loaded = json.loads(Path(path).read_text(encoding="utf-8"))
            self.assertEqual(loaded["source"], "C:\\src")
            self.assertEqual(loaded["target"], "C:\\dst")
            self.assertEqual(loaded["whitelist"], ["C:\\dst"])


class TestIsTargetValid(unittest.TestCase):
    def test_empty_target_is_invalid(self):
        settings = Settings(source="", target="", whitelist=["C:\\backups"])
        self.assertFalse(is_target_valid(settings))

    def test_relative_target_is_invalid(self):
        settings = Settings(source="", target="relative\\path", whitelist=["relative"])
        self.assertFalse(is_target_valid(settings))

    def test_target_inside_whitelist_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "backups" / "data"
            target.mkdir(parents=True)
            settings = Settings(source="", target=str(target), whitelist=[str(base / "backups")])
            self.assertTrue(is_target_valid(settings))

    def test_target_equal_to_whitelist_entry_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(source="", target=tmp, whitelist=[tmp])
            self.assertTrue(is_target_valid(settings))

    def test_target_outside_whitelist_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            whitelisted = base / "backups"
            whitelisted.mkdir()
            sibling = base / "backups-old"
            sibling.mkdir()
            settings = Settings(source="", target=str(sibling), whitelist=[str(whitelisted)])
            self.assertFalse(is_target_valid(settings))

    def test_target_not_under_any_whitelist_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            other = base / "other"
            other.mkdir()
            whitelisted = base / "backups"
            whitelisted.mkdir()
            settings = Settings(source="", target=str(other), whitelist=[str(whitelisted)])
            self.assertFalse(is_target_valid(settings))


if __name__ == "__main__":
    unittest.main()
