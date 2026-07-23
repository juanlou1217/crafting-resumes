from __future__ import annotations

import ctypes
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts/exclusive_rename.py"


class ExclusiveRenamePresenceTests(unittest.TestCase):
    def test_helper_exists(self) -> None:
        self.assertTrue(HELPER.is_file(), f"missing migration helper: {HELPER}")


@unittest.skipUnless(sys.platform == "darwin", "macOS migration helper")
class ExclusiveRenameTests(unittest.TestCase):
    helper: ModuleType

    @classmethod
    def setUpClass(cls) -> None:
        if not HELPER.is_file():
            raise unittest.SkipTest("migration helper does not exist yet")
        spec = importlib.util.spec_from_file_location(
            "exclusive_rename_under_test", HELPER
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load migration helper: {HELPER}")
        cls.helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.helper)

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    def run_helper(
        self, source: str | Path, target: str | Path
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(HELPER), str(source), str(target)],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

    def assert_rejection(
        self, completed: subprocess.CompletedProcess[str]
    ) -> None:
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertTrue(
            completed.stderr.startswith("exclusive rename failed:"),
            completed.stderr,
        )
        self.assertNotIn("Traceback", completed.stderr)

    def test_uses_exact_macos_constants_and_ctypes_prototype(self) -> None:
        self.assertEqual(self.helper.AT_FDCWD, -2)
        self.assertEqual(self.helper.RENAME_EXCL, 4)
        self.assertEqual(self.helper.RENAME_NOFOLLOW_ANY, 16)

        renameatx_np = self.helper._load_renameatx_np()

        self.assertEqual(
            renameatx_np.argtypes,
            [
                ctypes.c_int,
                ctypes.c_char_p,
                ctypes.c_int,
                ctypes.c_char_p,
                ctypes.c_uint,
            ],
        )
        self.assertIs(renameatx_np.restype, ctypes.c_int)

    def test_syscall_uses_parent_fds_relative_names_and_exact_flags(
        self,
    ) -> None:
        source = self.root / "source"
        target = self.root / "target"
        source.mkdir()
        source_stat = source.stat()
        parent_descriptor = os.open(self.root, os.O_RDONLY)
        self.addCleanup(os.close, parent_descriptor)
        calls: list[tuple[object, ...]] = []

        def fake_renameatx_np(*arguments: object) -> int:
            calls.append(arguments)
            return 0

        self.helper._invoke_renameatx_np(
            fake_renameatx_np,
            parent_descriptor,
            b"source",
            parent_descriptor,
            b"target",
            source_stat,
            source,
        )

        self.assertEqual(
            calls,
            [
                (
                    parent_descriptor,
                    b"source",
                    parent_descriptor,
                    b"target",
                    self.helper.RENAME_EXCL
                    | self.helper.RENAME_NOFOLLOW_ANY,
                )
            ],
        )
        self.assertNotEqual(parent_descriptor, self.helper.AT_FDCWD)

    def test_moves_absent_target_without_changing_identity(self) -> None:
        source = self.root / "source"
        target = self.root / "target"
        source.mkdir()
        source_identity = source.stat().st_dev, source.stat().st_ino

        completed = self.run_helper(source, target)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(os.path.lexists(source))
        self.assertTrue(target.is_dir())
        self.assertEqual(
            (target.stat().st_dev, target.stat().st_ino), source_identity
        )

    def test_refuses_existing_directory_without_nesting_source(self) -> None:
        source = self.root / "source"
        target = self.root / "target"
        source.mkdir()
        target.mkdir()

        completed = self.run_helper(source, target)

        self.assert_rejection(completed)
        self.assertTrue(source.is_dir())
        self.assertTrue(target.is_dir())
        self.assertFalse((target / source.name).exists())

    def test_refuses_dangling_target_symlink(self) -> None:
        source = self.root / "source"
        target = self.root / "target"
        source.mkdir()
        target.symlink_to(self.root / "missing", target_is_directory=True)

        completed = self.run_helper(source, target)

        self.assert_rejection(completed)
        self.assertTrue(source.is_dir())
        self.assertTrue(target.is_symlink())

    def test_refuses_symlink_source(self) -> None:
        real_source = self.root / "real-source"
        source = self.root / "source"
        target = self.root / "target"
        real_source.mkdir()
        source.symlink_to(real_source, target_is_directory=True)

        completed = self.run_helper(source, target)

        self.assert_rejection(completed)
        self.assertTrue(source.is_symlink())
        self.assertFalse(os.path.lexists(target))

    def test_refuses_relative_source_and_target(self) -> None:
        source = self.root / "source"
        target = self.root / "target"
        source.mkdir()
        for source_argument, target_argument in (
            ("source", target),
            (source, "target"),
        ):
            with self.subTest(
                source=source_argument, target=target_argument
            ):
                completed = self.run_helper(
                    source_argument, target_argument
                )
                self.assert_rejection(completed)
                self.assertTrue(source.is_dir())
                self.assertFalse(os.path.lexists(target))

    def test_refuses_parent_symlink(self) -> None:
        real_parent = self.root / "real-parent"
        linked_parent = self.root / "linked-parent"
        target_parent = self.root / "target-parent"
        real_parent.mkdir()
        target_parent.mkdir()
        source = real_parent / "source"
        source.mkdir()
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        target = target_parent / "target"

        completed = self.run_helper(linked_parent / source.name, target)

        self.assert_rejection(completed)
        self.assertTrue(source.is_dir())
        self.assertFalse(os.path.lexists(target))

    def test_same_filesystem_guard_is_enforced(self) -> None:
        source_parent = self.root / "source-parent"
        target_parent = self.root / "target-parent"
        source_parent.mkdir()
        target_parent.mkdir()
        source = source_parent / "source"
        target = target_parent / "target"
        source.mkdir()

        with mock.patch.object(
            self.helper, "_same_filesystem", return_value=False
        ) as same_filesystem:
            with self.assertRaisesRegex(
                ValueError, "source and target must share a filesystem"
            ):
                self.helper.exclusive_rename(source, target)

        same_filesystem.assert_called_once()
        self.assertTrue(source.is_dir())
        self.assertFalse(os.path.lexists(target))

    def test_same_filesystem_checks_source_and_both_parents(self) -> None:
        source = mock.Mock(st_dev=41)
        source_parent = mock.Mock(st_dev=41)
        target_parent = mock.Mock(st_dev=41)

        self.assertTrue(
            self.helper._same_filesystem(
                source, source_parent, target_parent
            )
        )
        source.st_dev = 42
        self.assertFalse(
            self.helper._same_filesystem(
                source, source_parent, target_parent
            ),
            "a mounted source must not pass the parent filesystem guard",
        )
        source.st_dev = 41
        source_parent.st_dev = 42
        self.assertFalse(
            self.helper._same_filesystem(
                source, source_parent, target_parent
            ),
            "a source parent on another device must be rejected",
        )
        source_parent.st_dev = 41
        target_parent.st_dev = 43
        self.assertFalse(
            self.helper._same_filesystem(
                source, source_parent, target_parent
            )
        )

    def test_kernel_exclusive_flag_rejects_target_created_after_precheck(
        self,
    ) -> None:
        source = self.root / "source"
        target = self.root / "target"
        source.mkdir()
        invoke = self.helper._invoke_renameatx_np

        def create_target_then_invoke(*arguments: object) -> None:
            target.mkdir()
            invoke(*arguments)

        with mock.patch.object(
            self.helper,
            "_invoke_renameatx_np",
            side_effect=create_target_then_invoke,
        ):
            with self.assertRaises(OSError):
                self.helper.exclusive_rename(source, target)

        self.assertTrue(source.is_dir())
        self.assertTrue(target.is_dir())
        self.assertFalse((target / source.name).exists())

    def test_source_identity_recheck_rejects_symlink_swap_before_syscall(
        self,
    ) -> None:
        source = self.root / "source"
        moved_source = self.root / "moved-source"
        target = self.root / "target"
        source.mkdir()
        invoke = self.helper._invoke_renameatx_np

        def replace_source_then_invoke(*arguments: object) -> None:
            source.rename(moved_source)
            source.symlink_to(moved_source, target_is_directory=True)
            invoke(*arguments)

        with mock.patch.object(
            self.helper,
            "_invoke_renameatx_np",
            side_effect=replace_source_then_invoke,
        ):
            with self.assertRaises((OSError, RuntimeError, ValueError)):
                self.helper.exclusive_rename(source, target)

        self.assertTrue(source.is_symlink())
        self.assertTrue(moved_source.is_dir())
        self.assertFalse(os.path.lexists(target))

    def test_usage_error_returns_two_without_traceback(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(HELPER)],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(
            completed.stderr,
            "usage: exclusive_rename.py SOURCE TARGET\n",
        )
        self.assertNotIn("Traceback", completed.stderr)

    def test_rejection_has_stable_error_prefix_without_traceback(self) -> None:
        real_source = self.root / "real-source"
        source = self.root / "source"
        target = self.root / "target"
        real_source.mkdir()
        source.symlink_to(real_source, target_is_directory=True)

        completed = self.run_helper(source, target)

        self.assert_rejection(completed)

    def test_system_error_has_stable_error_prefix_without_traceback(
        self,
    ) -> None:
        completed = self.run_helper(
            self.root / "missing-source", self.root / "target"
        )

        self.assert_rejection(completed)


if __name__ == "__main__":
    unittest.main()
