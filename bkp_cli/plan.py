"""Plan Module: pure comparison of source/target Manifests into a Plan."""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


@dataclass
class ManifestEntry:
    path: str
    entry_type: str  # "file" | "dir"
    size: int | None
    mtime: float | None


Manifest = dict[str, ManifestEntry]


class OperationType(Enum):
    WRITE_FILE = "write-file"
    DELETE_FILE = "delete-file"
    WRITE_FOLDER = "write-folder"
    DELETE_FOLDER = "delete-folder"


DELETE_OP_TYPES = {OperationType.DELETE_FILE, OperationType.DELETE_FOLDER}
WRITE_OP_TYPES = {OperationType.WRITE_FILE, OperationType.WRITE_FOLDER}


@dataclass
class Operation:
    op_type: OperationType
    relative_path: str


Plan = list[Operation]


class FileComparator(Protocol):
    def are_equal(self, source_entry: ManifestEntry, target_entry: ManifestEntry) -> bool: ...


class MtimeSizeComparator:
    def are_equal(self, source_entry: ManifestEntry, target_entry: ManifestEntry) -> bool:
        return (
            source_entry.size == target_entry.size
            and source_entry.mtime == target_entry.mtime
        )


def generate_plan(
    source: Manifest,
    target: Manifest,
    comparator: FileComparator | None = None,
) -> Plan:
    if comparator is None:
        comparator = MtimeSizeComparator()

    ops: Plan = []
    covered: set[str] = set()

    def covered_by(path: str) -> bool:
        return any(path == p or path.startswith(p + "/") for p in covered)

    # Pass 1: things to remove from target (missing in source, or type changed)
    for path in sorted(target):
        if covered_by(path):
            continue
        t_entry = target[path]
        s_entry = source.get(path)
        if s_entry is None or s_entry.entry_type != t_entry.entry_type:
            op_type = (
                OperationType.DELETE_FOLDER
                if t_entry.entry_type == "dir"
                else OperationType.DELETE_FILE
            )
            ops.append(Operation(op_type, path))
            if t_entry.entry_type == "dir":
                covered.add(path)

    covered.clear()

    # Pass 2: things to add/update in target
    for path in sorted(source):
        if covered_by(path):
            continue
        s_entry = source[path]
        t_entry = target.get(path)
        if t_entry is None or t_entry.entry_type != s_entry.entry_type:
            op_type = (
                OperationType.WRITE_FOLDER
                if s_entry.entry_type == "dir"
                else OperationType.WRITE_FILE
            )
            ops.append(Operation(op_type, path))
            if s_entry.entry_type == "dir":
                covered.add(path)
        elif s_entry.entry_type == "file" and not comparator.are_equal(s_entry, t_entry):
            ops.append(Operation(OperationType.WRITE_FILE, path))

    return ops
