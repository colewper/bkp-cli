"""File IO Module: filesystem side effects (scanning, executing operations)."""

import os
import shutil
from pathlib import Path

from bkp_cli.plan import Manifest, ManifestEntry, Operation, OperationType


def build_manifest(root: str) -> Manifest:
    manifest: Manifest = {}
    root_path = Path(root)

    for dirpath, dirnames, filenames in os.walk(root_path):
        current_dir = Path(dirpath)

        # Filter out symlinked directories in-place so os.walk doesn't descend into them.
        kept_dirnames = []
        for dirname in dirnames:
            dir_full_path = current_dir / dirname
            if dir_full_path.is_symlink():
                rel_path = dir_full_path.relative_to(root_path).as_posix()
                print(f"skipping symlink: {rel_path}")
                continue
            kept_dirnames.append(dirname)
        dirnames[:] = kept_dirnames

        for dirname in dirnames:
            dir_full_path = current_dir / dirname
            rel_path = dir_full_path.relative_to(root_path).as_posix()
            manifest[rel_path] = ManifestEntry(
                path=rel_path, entry_type="dir", size=None, mtime=None
            )

        for filename in filenames:
            file_full_path = current_dir / filename
            if file_full_path.is_symlink():
                rel_path = file_full_path.relative_to(root_path).as_posix()
                print(f"skipping symlink: {rel_path}")
                continue
            rel_path = file_full_path.relative_to(root_path).as_posix()
            stat_result = file_full_path.stat()
            manifest[rel_path] = ManifestEntry(
                path=rel_path,
                entry_type="file",
                size=stat_result.st_size,
                mtime=stat_result.st_mtime,
            )

    return manifest


def execute_operation(op: Operation, source_root: str, target_root: str) -> bool:
    source_path = Path(source_root) / op.relative_path
    target_path = Path(target_root) / op.relative_path

    try:
        if op.op_type == OperationType.WRITE_FILE:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
        elif op.op_type == OperationType.DELETE_FILE:
            os.remove(target_path)
        elif op.op_type == OperationType.WRITE_FOLDER:
            shutil.copytree(source_path, target_path, copy_function=shutil.copy2)
        elif op.op_type == OperationType.DELETE_FOLDER:
            shutil.rmtree(target_path)
        else:
            print(f"error: unknown operation type: {op.op_type}")
            return False
        return True
    except (OSError, shutil.Error) as exc:
        print(f"error: {op.op_type.value} failed for '{op.relative_path}': {exc}")
        return False
