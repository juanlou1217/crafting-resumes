from __future__ import annotations

import hashlib
import os
import stat
import sys
from pathlib import Path


def tree_hash(root: Path) -> str:
    root = Path(root)
    try:
        root_mode = root.lstat().st_mode
    except FileNotFoundError as error:
        raise ValueError("skill tree root does not exist") from error
    if stat.S_ISLNK(root_mode):
        raise ValueError("skill tree root must not be a symlink")
    if not stat.S_ISDIR(root_mode):
        raise ValueError("skill tree root must be a directory")

    files: list[tuple[str, Path]] = []
    for path in root.rglob("*"):
        mode = path.lstat().st_mode
        relative_path = path.relative_to(root).as_posix()
        if stat.S_ISLNK(mode):
            raise ValueError(
                f"skill tree entries must not be symlinks: {relative_path}"
            )
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ValueError(
                f"skill tree entries must be regular files: {relative_path}"
            )
        files.append((relative_path, path))

    digest = hashlib.sha256()
    for relative_path, path in sorted(files):
        open_flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            open_flags |= os.O_NOFOLLOW
        descriptor = os.open(path, open_flags)
        try:
            opened_stat = os.fstat(descriptor)
            if not stat.S_ISREG(opened_stat.st_mode):
                raise ValueError(
                    "skill tree entry changed to a non-regular file: "
                    f"{relative_path}"
                )
            file_size = opened_stat.st_size
            if not 0 <= file_size < 2**64:
                raise ValueError(
                    f"skill tree entry has unsupported size: {relative_path}"
                )
            digest.update(relative_path.encode("utf-8"))
            digest.update(b"\0")
            digest.update(file_size.to_bytes(8, byteorder="big"))
            bytes_read = 0
            while bytes_read < file_size:
                chunk = os.read(
                    descriptor,
                    min(1024 * 1024, file_size - bytes_read),
                )
                if not chunk:
                    break
                digest.update(chunk)
                bytes_read += len(chunk)
            has_trailing_byte = bool(os.read(descriptor, 1))
            final_size = os.fstat(descriptor).st_size
            if (
                bytes_read != file_size
                or has_trailing_byte
                or final_size != file_size
            ):
                raise ValueError(
                    f"skill tree entry changed while hashing: {relative_path}"
                )
        finally:
            os.close(descriptor)
    return digest.hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: hash_skill_tree.py SKILL_DIR", file=sys.stderr)
        return 2
    try:
        digest = tree_hash(Path(sys.argv[1]))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"unable to hash skill tree: {error}", file=sys.stderr)
        return 1
    print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
