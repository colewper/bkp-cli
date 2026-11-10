"""Settings Module: load/save settings.json, validate target against whitelist."""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Settings:
    source: str = ""
    target: str = ""
    whitelist: list[str] = field(default_factory=list)


def _default_settings() -> Settings:
    return Settings(source="", target="", whitelist=[])


def load_settings(path: str = "settings.json") -> Settings:
    settings_path = Path(path)

    if not settings_path.exists():
        settings = _default_settings()
        save_settings(settings, path)
        return settings

    try:
        raw = settings_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return Settings(
            source=data["source"],
            target=data["target"],
            whitelist=list(data["whitelist"]),
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"error: failed to read settings from {path}: {exc}")
        return _default_settings()


def save_settings(settings: Settings, path: str = "settings.json") -> None:
    settings_path = Path(path)
    settings_path.write_text(
        json.dumps(asdict(settings), indent=2),
        encoding="utf-8",
    )


def is_target_valid(settings: Settings) -> bool:
    if not settings.target:
        return False

    target_path = Path(settings.target)
    if not target_path.is_absolute():
        return False

    resolved_target = target_path.resolve()

    for whitelist_entry in settings.whitelist:
        whitelist_path = Path(whitelist_entry)
        if not whitelist_path.is_absolute():
            continue
        resolved_whitelist = whitelist_path.resolve()
        try:
            common = os.path.commonpath([str(resolved_target), str(resolved_whitelist)])
        except ValueError:
            # Different drives on Windows, for example - cannot be related.
            continue
        if common == str(resolved_whitelist):
            return True

    return False

