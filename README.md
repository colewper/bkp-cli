# bkp-cli

A Python CLI tool that mirrors the contents of a **source** directory into a **target** directory, recursively. It is strictly one-directional: source is read-only (never written to or deleted from), and all mutations happen on target.

See [spec.md](spec.md) for the full design specification.

## Requirements

- Python 3.10+
- No external dependencies (standard library only, including `tkinter` for the settings GUI)

## Running

```
py bkp-cli.py
```

This starts an interactive loop exposing five commands:

- `config list` - show current settings
- `config set` - open settings GUI
- `config clear` - reset settings to defaults
- `prepare` - compare source and target, build a plan
- `list` - show operations in the current plan
- `commit` - execute the most recently prepared plan
- `quit` - exit

On first run, an empty `settings.json` is created in the project root. Use `config set` to choose a source directory, a target directory, and at least one whitelisted path that the target must fall under.

## Running the tests

Tests use Python's built-in `unittest` framework - no third-party test runner required.

From the project root:

```
py -m unittest discover
```

Add `-v` for verbose per-test output:

```
py -m unittest discover -v
```

To run a single test module:

```
py -m unittest tests.test_plan
```

## Project structure

```
bkp-cli/
  bkp-cli.py            # entry point: main loop, dispatch, console I/O
  settings.json          # generated at runtime, not checked in
  bkp_cli/
    __init__.py
    cli.py               # parse_command()
    plan.py              # generate_plan(), Operation/OperationType, FileComparator, MtimeSizeComparator
    file_io.py           # build_manifest(), execute_operation()
    settings.py          # Settings dataclass, load_settings(), save_settings(), is_target_valid()
    gui.py               # Tkinter config-set window
  tests/
    test_cli.py
    test_plan.py
    test_settings.py
    test_file_io.py
```
