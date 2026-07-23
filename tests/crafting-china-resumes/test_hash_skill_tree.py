from __future__ import annotations

import hashlib
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


HELPER_PATH = Path(__file__).with_name("hash_skill_tree.py")
SPEC = importlib.util.spec_from_file_location("hash_skill_tree", HELPER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load hash_skill_tree helper")
HASH_SKILL_TREE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HASH_SKILL_TREE)


class HashSkillTreeTests(unittest.TestCase):
    def create_tree(self, root: Path, entries: list[tuple[str, bytes]]) -> None:
        for relative_path, contents in entries:
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)

    def test_equivalent_trees_created_in_different_orders_hash_equally(
        self,
    ) -> None:
        entries = [
            ("SKILL.md", b"router\n"),
            ("references/evidence.md", b"truth\n"),
            ("scripts/check.py", b"print('ok')\n"),
        ]
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            first = temporary_root / "first"
            second = temporary_root / "second"
            first.mkdir()
            second.mkdir()
            self.create_tree(first, entries)
            self.create_tree(second, list(reversed(entries)))

            self.assertEqual(
                HASH_SKILL_TREE.tree_hash(first),
                HASH_SKILL_TREE.tree_hash(second),
            )

    def test_one_byte_change_changes_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "skill"
            root.mkdir()
            tracked_file = root / "SKILL.md"
            tracked_file.write_bytes(b"abc")
            before = HASH_SKILL_TREE.tree_hash(root)

            tracked_file.write_bytes(b"abd")

            self.assertNotEqual(before, HASH_SKILL_TREE.tree_hash(root))

    def test_file_record_boundaries_cannot_collide_with_file_bytes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            first = temporary_root / "first"
            second = temporary_root / "second"
            first.mkdir()
            second.mkdir()
            self.create_tree(first, [("a", b"x\0b\0y")])
            self.create_tree(second, [("a", b"x"), ("b", b"y")])

            self.assertNotEqual(
                HASH_SKILL_TREE.tree_hash(first),
                HASH_SKILL_TREE.tree_hash(second),
            )

    def test_hash_matches_sorted_path_nul_uint64_length_bytes_contract(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "skill"
            root.mkdir()
            entries = [
                ("z-last.txt", b"last"),
                ("nested/a-first.txt", b"first"),
            ]
            self.create_tree(root, entries)
            expected = hashlib.sha256()
            for relative_path, contents in sorted(entries):
                expected.update(relative_path.encode("utf-8"))
                expected.update(b"\0")
                expected.update(len(contents).to_bytes(8, byteorder="big"))
                expected.update(contents)

            self.assertEqual(
                HASH_SKILL_TREE.tree_hash(root),
                expected.hexdigest(),
            )

    def test_rejects_missing_root_and_regular_file_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            missing = temporary_root / "missing"
            regular_file = temporary_root / "regular-file"
            regular_file.write_bytes(b"not a tree")

            for unsafe_root in (missing, regular_file):
                with self.subTest(root=unsafe_root.name):
                    with self.assertRaises(ValueError):
                        HASH_SKILL_TREE.tree_hash(unsafe_root)

    def test_rejects_root_and_child_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            real_root = temporary_root / "real"
            real_root.mkdir()
            (real_root / "SKILL.md").write_bytes(b"safe")
            root_symlink = temporary_root / "root-link"
            try:
                root_symlink.symlink_to(real_root, target_is_directory=True)
            except (NotImplementedError, OSError) as error:
                self.skipTest(f"symlinks unavailable: {error}")

            with self.assertRaises(ValueError):
                HASH_SKILL_TREE.tree_hash(root_symlink)

            outside_file = temporary_root / "outside.txt"
            outside_file.write_bytes(b"outside")
            child_symlink = real_root / "linked.txt"
            child_symlink.symlink_to(outside_file)
            with self.assertRaises(ValueError):
                HASH_SKILL_TREE.tree_hash(real_root)

            child_symlink.unlink()
            dangling_symlink = real_root / "dangling.txt"
            dangling_symlink.symlink_to(temporary_root / "absent.txt")
            with self.assertRaises(ValueError):
                HASH_SKILL_TREE.tree_hash(real_root)

            dangling_symlink.unlink()
            outside_directory = temporary_root / "outside-directory"
            outside_directory.mkdir()
            (outside_directory / "outside.txt").write_bytes(b"outside")
            directory_symlink = real_root / "linked-directory"
            directory_symlink.symlink_to(
                outside_directory,
                target_is_directory=True,
            )
            with self.assertRaises(ValueError):
                HASH_SKILL_TREE.tree_hash(real_root)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation unavailable")
    def test_rejects_non_regular_tree_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "skill"
            root.mkdir()
            os.mkfifo(root / "unsafe-fifo")

            with self.assertRaises(ValueError):
                HASH_SKILL_TREE.tree_hash(root)


if __name__ == "__main__":
    unittest.main()
