"""CLI Module: parse raw input strings into Command objects."""

from dataclasses import dataclass

_COMMAND_NAMES = {
    "config list": "config_list",
    "config set": "config_set",
    "config clear": "config_clear",
    "prepare": "prepare",
    "commit": "commit",
    "list": "list",
    "quit": "quit",
}


@dataclass
class Command:
    name: str
    raw_input: str


def parse_command(raw: str) -> Command:
    normalized = raw.strip().lower()
    name = _COMMAND_NAMES.get(normalized, "unknown")
    return Command(name=name, raw_input=raw)
