"""Entry point: main loop, dispatch, console I/O."""

from pathlib import Path

from bkp_cli import cli, colors, file_io, gui, plan, settings

SETTINGS_PATH = "settings.json"


def _target_status_suffix(app_settings: settings.Settings) -> str:
    if app_settings.target and not settings.is_target_valid(app_settings):
        return colors.negative(" [INVALID - outside whitelist]")
    return ""

def _print_source_and_target(app_settings: settings.Settings) -> None:
    print(f"{colors.highlight('source')}: {app_settings.source or '(not set)'}")
    print(f"{colors.highlight('target')}: {app_settings.target or '(not set)'}{_target_status_suffix(app_settings)}")

def print_banner(app_settings: settings.Settings) -> None:
    print("=" * 57)
    print("bkp-cli - available commands:")
    print(f"  {colors.highlight('config list')}   - show current settings")
    print(f"  {colors.highlight('config set')}    - open settings GUI")
    print(f"  {colors.highlight('config clear')}  - reset settings to defaults")
    print(f"  {colors.highlight('prepare')}       - compare source and target, build a plan")
    print(f"  {colors.highlight('list')}          - show operations in the current plan")
    print(f"  {colors.highlight('commit')}        - execute the most recently prepared plan")
    print(f"  {colors.highlight('quit')}          - exit")
    print("-" * 57)
    _print_source_and_target(app_settings)
    print("=" * 57)


def handle_config_list(app_settings: settings.Settings) -> None:
    _print_source_and_target(app_settings)
    print(f"{colors.highlight('whitelist')}:")
    if app_settings.whitelist:
        for entry in app_settings.whitelist:
            print(f"  {entry}")
    else:
        print("  (empty)")


def handle_config_set(app_settings: settings.Settings):
    gui.open_settings_window(app_settings, SETTINGS_PATH)
    reloaded = settings.load_settings(SETTINGS_PATH)
    # Any existing plan is discarded since target state may have changed.
    return reloaded, None


def handle_config_clear():
    default_settings = settings.Settings()
    settings.save_settings(default_settings, SETTINGS_PATH)
    print("settings reset to defaults")
    # Any existing plan is discarded since source/target state may have changed.
    return default_settings, None


def _is_source_target_overlapping(source: str, target: str) -> bool:
    source_resolved = Path(source).resolve()
    target_resolved = Path(target).resolve()
    if source_resolved == target_resolved:
        return True
    return source_resolved in target_resolved.parents or target_resolved in source_resolved.parents


def handle_prepare(app_settings: settings.Settings):
    if not app_settings.source or not app_settings.target:
        print(f"{colors.negative('error')}: source and target must both be set - use 'config set'")
        return None

    if not settings.is_target_valid(app_settings):
        print(f"{colors.negative('error')}: target is invalid (not under any whitelisted path) - use 'config set'")
        return None

    if not Path(app_settings.source).is_dir():
        print(f"{colors.negative('error')}: source does not exist or is not a directory: {app_settings.source}")
        return None

    if _is_source_target_overlapping(app_settings.source, app_settings.target):
        print(f"{colors.negative('error')}: source and target must not be the same path or nested within each other")
        return None

    source_manifest = file_io.build_manifest(app_settings.source)
    target_manifest = file_io.build_manifest(app_settings.target)
    generated_plan = plan.generate_plan(source_manifest, target_manifest)

    if not generated_plan:
        print("source and target already match - nothing to do")
        return None

    counts: dict[str, int] = {}
    for op in generated_plan:
        counts[op.op_type.value] = counts.get(op.op_type.value, 0) + 1

    print(f"prepared plan with {colors.highlight(f'{len(generated_plan)} operation(s)')}:")
    for op_type_value, count in counts.items():
        print(f"  {op_type_value}: {count}")

    return generated_plan


def _color_op(op: plan.Operation) -> str:
    if op.op_type in plan.DELETE_OP_TYPES:
        return colors.negative(op.op_type.value)
    if op.op_type in plan.WRITE_OP_TYPES:
        return colors.positive(op.op_type.value)
    return op.op_type.value


def handle_list(current_plan) -> None:
    if not current_plan:
        print("no current plan - run 'prepare' first")
        return

    print(f"current plan has {len(current_plan)} operation(s):")
    for op in current_plan:
        print(f"  {_color_op(op)}: {op.relative_path}")


def handle_commit(app_settings: settings.Settings, current_plan):
    if not current_plan:
        print("no plan to commit - run 'prepare' first")
        return current_plan

    _print_source_and_target(app_settings)
    prompt = colors.highlight(f"commit {len(current_plan)} operations? [y/N] ")
    confirmation = input(prompt).strip().lower()
    if confirmation != "y":
        print("commit cancelled")
        return current_plan

    completed = 0
    for op in current_plan:
        success = file_io.execute_operation(op, app_settings.source, app_settings.target)
        if not success:
            print(
                f"{colors.negative('error')}: operation failed: {op.op_type.value} {op.relative_path} "
                f"({completed} of {len(current_plan)} operations completed successfully)"
            )
            return None

        completed += 1

    print(f"commit complete: {colors.positive(f'{completed} operation(s) executed successfully')}")
    return None


def main() -> None:
    app_settings = settings.load_settings(SETTINGS_PATH)
    current_plan = None

    print_banner(app_settings)

    while True:
        raw = input(f"{colors.highlight('>>')} ")
        if not raw.strip():
            continue

        command = cli.parse_command(raw)

        if command.name == "config_list":
            handle_config_list(app_settings)
        elif command.name == "config_set":
            app_settings, current_plan = handle_config_set(app_settings)
        elif command.name == "config_clear":
            app_settings, current_plan = handle_config_clear()
        elif command.name == "prepare":
            current_plan = handle_prepare(app_settings)
        elif command.name == "list":
            handle_list(current_plan)
        elif command.name == "commit":
            current_plan = handle_commit(app_settings, current_plan)
        elif command.name == "quit":
            break
        else:
            print(f"unknown command: {command.raw_input}")


if __name__ == "__main__":
    main()
