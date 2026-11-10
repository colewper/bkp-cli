"""Colors Module: minimal ANSI color helpers for console output.

Stdlib-only (no external dependencies). Colors are automatically disabled
when stdout is not a terminal (e.g. piped output, test runners).
"""

import os
import sys

_ENABLED = sys.stdout.isatty()

if _ENABLED and os.name == "nt":
    # Enable ANSI/VT100 escape sequence processing in legacy Windows consoles.
    os.system("")

HIGHLIGHT = "\033[96m" if _ENABLED else ""
POSITIVE = "\033[92m" if _ENABLED else ""
NEGATIVE = "\033[91m" if _ENABLED else ""
RESET = "\033[0m" if _ENABLED else ""


def highlight(text: str) -> str:
    return f"{HIGHLIGHT}{text}{RESET}"


def positive(text: str) -> str:
    return f"{POSITIVE}{text}{RESET}"


def negative(text: str) -> str:
    return f"{NEGATIVE}{text}{RESET}"
