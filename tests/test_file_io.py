import os
import tempfile
import unittest
from pathlib import Path

from bkp_cli.file_io import build_manifest, execute_operation
from bkp_cli.plan import Operation, OperationType


class TestBuildManifest(unittest.TestCase):
    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = build_manifest(tmp)
            self.assertEqual(manifest, {})

    def test_files_and_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "readme.txt").write_text("hello", encoding="utf-8")
            (root / "empty_dir").mkdir()

            manifest = build_manifest(tmp)

            self.assertEqual(set(manifest.keys()), {"docs", "docs/readme.txt", "empty_dir"})
            self.assertEqual(manifest["docs"].entry_type, "dir")
            self.assertEqual(manifest["empty_dir"].entry_type, "dir")
            self.assertEqual(manifest["docs/readme.txt"].entry_type, "file")
            self.assertEqual(manifest["docs/readme.txt"].size, 5)

    def test_skips_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real_file = root / "real.txt"
            real_file.write_text("data", encoding="utf-8")
            link_path = root / "link.txt"
            try:
                link_path.symlink_to(real_file)
            except OSError:
                self.skipTest("symlink creation requires elevated privileges on this platform")

            manifest = build_manifest(tmp)

            self.assertIn("real.txt", manifest)
            self.assertNotIn("link.txt", manifest)


class TestExecuteOperation(unittest.TestCase):
    def test_write_file(self):
        with tempfile.TemporaryDirectory() as src_tmp, tempfile.TemporaryDirectory() as dst_tmp:
            (Path(src_tmp) / "a.txt").write_text("content", encoding="utf-8")
            op = Operation(OperationType.WRITE_FILE, "a.txt")
            result = execute_operation(op, src_tmp, dst_tmp)
            self.assertTrue(result)
            self.assertEqual((Path(dst_tmp) / "a.txt").read_text(encoding="utf-8"), "content")

    def test_write_file_preserves_mtime(self):
        with tempfile.TemporaryDirectory() as src_tmp, tempfile.TemporaryDirectory() as dst_tmp:
            src_file = Path(src_tmp) / "a.txt"
            src_file.write_text("content", encoding="utf-8")
            os.utime(src_file, (1000000.0, 1000000.0))
            op = Operation(OperationType.WRITE_FILE, "a.txt")
            execute_operation(op, src_tmp, dst_tmp)
            dst_file = Path(dst_tmp) / "a.txt"
            self.assertEqual(int(dst_file.stat().st_mtime), 1000000)

    def test_delete_file(self):
        with tempfile.TemporaryDirectory() as src_tmp, tempfile.TemporaryDirectory() as dst_tmp:
            (Path(dst_tmp) / "a.txt").write_text("content", encoding="utf-8")
            op = Operation(OperationType.DELETE_FILE, "a.txt")
            result = execute_operation(op, src_tmp, dst_tmp)
            self.assertTrue(result)
            self.assertFalse((Path(dst_tmp) / "a.txt").exists())

    def test_write_folder(self):
        with tempfile.TemporaryDirectory() as src_tmp, tempfile.TemporaryDirectory() as dst_tmp:
            src_folder = Path(src_tmp) / "docs"
            src_folder.mkdir()
            (src_folder / "readme.txt").write_text("hi", encoding="utf-8")
            op = Operation(OperationType.WRITE_FOLDER, "docs")
            result = execute_operation(op, src_tmp, dst_tmp)
            self.assertTrue(result)
            self.assertTrue((Path(dst_tmp) / "docs" / "readme.txt").exists())

    def test_delete_folder(self):
        with tempfile.TemporaryDirectory() as src_tmp, tempfile.TemporaryDirectory() as dst_tmp:
            dst_folder = Path(dst_tmp) / "docs"
            dst_folder.mkdir()
            (dst_folder / "readme.txt").write_text("hi", encoding="utf-8")
            op = Operation(OperationType.DELETE_FOLDER, "docs")
            result = execute_operation(op, src_tmp, dst_tmp)
            self.assertTrue(result)
            self.assertFalse(dst_folder.exists())

    def test_returns_false_on_failure_instead_of_raising(self):
        with tempfile.TemporaryDirectory() as src_tmp, tempfile.TemporaryDirectory() as dst_tmp:
            # Deleting a file that doesn't exist should fail gracefully.
            op = Operation(OperationType.DELETE_FILE, "missing.txt")
            result = execute_operation(op, src_tmp, dst_tmp)
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
