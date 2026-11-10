import unittest

from bkp_cli.plan import (
    FileComparator,
    ManifestEntry,
    Operation,
    OperationType,
    generate_plan,
)


def file_entry(path: str, size: int = 10, mtime: float = 100.0) -> ManifestEntry:
    return ManifestEntry(path=path, entry_type="file", size=size, mtime=mtime)


def dir_entry(path: str) -> ManifestEntry:
    return ManifestEntry(path=path, entry_type="dir", size=None, mtime=None)


class AlwaysEqualComparator:
    def are_equal(self, source_entry, target_entry) -> bool:
        return True


class AlwaysDifferentComparator:
    def are_equal(self, source_entry, target_entry) -> bool:
        return False


class TestGeneratePlan(unittest.TestCase):
    def test_identical_trees_produce_empty_plan(self):
        source = {"a.txt": file_entry("a.txt")}
        target = {"a.txt": file_entry("a.txt")}
        self.assertEqual(generate_plan(source, target), [])

    def test_added_file(self):
        source = {"a.txt": file_entry("a.txt")}
        target: dict = {}
        plan = generate_plan(source, target)
        self.assertEqual(plan, [Operation(OperationType.WRITE_FILE, "a.txt")])

    def test_removed_file(self):
        source: dict = {}
        target = {"a.txt": file_entry("a.txt")}
        plan = generate_plan(source, target)
        self.assertEqual(plan, [Operation(OperationType.DELETE_FILE, "a.txt")])

    def test_added_folder_including_empty(self):
        source = {"docs": dir_entry("docs")}
        target: dict = {}
        plan = generate_plan(source, target)
        self.assertEqual(plan, [Operation(OperationType.WRITE_FOLDER, "docs")])

    def test_added_folder_does_not_enumerate_children(self):
        source = {
            "docs": dir_entry("docs"),
            "docs/a.txt": file_entry("docs/a.txt"),
        }
        target: dict = {}
        plan = generate_plan(source, target)
        self.assertEqual(plan, [Operation(OperationType.WRITE_FOLDER, "docs")])

    def test_removed_folder_does_not_enumerate_children(self):
        source: dict = {}
        target = {
            "docs": dir_entry("docs"),
            "docs/a.txt": file_entry("docs/a.txt"),
        }
        plan = generate_plan(source, target)
        self.assertEqual(plan, [Operation(OperationType.DELETE_FOLDER, "docs")])

    def test_changed_file_mtime(self):
        source = {"a.txt": file_entry("a.txt", size=10, mtime=200.0)}
        target = {"a.txt": file_entry("a.txt", size=10, mtime=100.0)}
        plan = generate_plan(source, target)
        self.assertEqual(plan, [Operation(OperationType.WRITE_FILE, "a.txt")])

    def test_changed_file_size(self):
        source = {"a.txt": file_entry("a.txt", size=20, mtime=100.0)}
        target = {"a.txt": file_entry("a.txt", size=10, mtime=100.0)}
        plan = generate_plan(source, target)
        self.assertEqual(plan, [Operation(OperationType.WRITE_FILE, "a.txt")])

    def test_unchanged_file_no_op(self):
        source = {"a.txt": file_entry("a.txt", size=10, mtime=100.0)}
        target = {"a.txt": file_entry("a.txt", size=10, mtime=100.0)}
        self.assertEqual(generate_plan(source, target), [])

    def test_file_to_folder_type_swap(self):
        source = {"a": dir_entry("a")}
        target = {"a": file_entry("a")}
        plan = generate_plan(source, target)
        self.assertEqual(
            plan,
            [
                Operation(OperationType.DELETE_FILE, "a"),
                Operation(OperationType.WRITE_FOLDER, "a"),
            ],
        )

    def test_folder_to_file_type_swap(self):
        source = {"a": file_entry("a")}
        target = {
            "a": dir_entry("a"),
            "a/b.txt": file_entry("a/b.txt"),
        }
        plan = generate_plan(source, target)
        self.assertEqual(
            plan,
            [
                Operation(OperationType.DELETE_FOLDER, "a"),
                Operation(OperationType.WRITE_FILE, "a"),
            ],
        )

    def test_deletes_ordered_before_writes(self):
        source = {"new.txt": file_entry("new.txt")}
        target = {"old.txt": file_entry("old.txt")}
        plan = generate_plan(source, target)
        self.assertEqual(
            plan,
            [
                Operation(OperationType.DELETE_FILE, "old.txt"),
                Operation(OperationType.WRITE_FILE, "new.txt"),
            ],
        )

    def test_custom_comparator_always_equal_suppresses_write(self):
        source = {"a.txt": file_entry("a.txt", size=999, mtime=999.0)}
        target = {"a.txt": file_entry("a.txt", size=1, mtime=1.0)}
        plan = generate_plan(source, target, comparator=AlwaysEqualComparator())
        self.assertEqual(plan, [])

    def test_custom_comparator_always_different_forces_write(self):
        source = {"a.txt": file_entry("a.txt", size=1, mtime=1.0)}
        target = {"a.txt": file_entry("a.txt", size=1, mtime=1.0)}
        plan = generate_plan(source, target, comparator=AlwaysDifferentComparator())
        self.assertEqual(plan, [Operation(OperationType.WRITE_FILE, "a.txt")])


if __name__ == "__main__":
    unittest.main()
