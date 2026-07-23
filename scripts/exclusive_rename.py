from __future__ import annotations

import ctypes
import os
import stat
import sys
from pathlib import Path
from typing import Any


AT_FDCWD = -2
RENAME_EXCL = 4
RENAME_NOFOLLOW_ANY = 16

_DIRECTORY_OPEN_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_NOFOLLOW", 0)
)


def _identity(result: os.stat_result) -> tuple[int, int]:
    return result.st_dev, result.st_ino


def _open_real_directory(path: Path) -> tuple[int, os.stat_result]:
    if not path.is_absolute():
        raise ValueError(f"parent path must be absolute: {path}")

    descriptor = os.open("/", _DIRECTORY_OPEN_FLAGS)
    try:
        for component in path.parts[1:]:
            if component in ("", ".", ".."):
                raise ValueError(f"parent path must be normalized: {path}")
            entry_stat = os.stat(
                component,
                dir_fd=descriptor,
                follow_symlinks=False,
            )
            if stat.S_ISLNK(entry_stat.st_mode):
                raise ValueError(
                    f"parent paths must not contain symlinks: {path}"
                )
            if not stat.S_ISDIR(entry_stat.st_mode):
                raise ValueError(f"parent must be a real directory: {path}")

            next_descriptor = os.open(
                component,
                _DIRECTORY_OPEN_FLAGS,
                dir_fd=descriptor,
            )
            opened_stat = os.fstat(next_descriptor)
            if (
                not stat.S_ISDIR(opened_stat.st_mode)
                or _identity(opened_stat) != _identity(entry_stat)
            ):
                os.close(next_descriptor)
                raise RuntimeError(
                    f"parent directory identity changed while opening: {path}"
                )
            os.close(descriptor)
            descriptor = next_descriptor

        opened_stat = os.fstat(descriptor)
        current_stat = os.stat(path, follow_symlinks=False)
        if (
            stat.S_ISLNK(current_stat.st_mode)
            or not stat.S_ISDIR(current_stat.st_mode)
        ):
            raise ValueError(f"parent must be a real directory: {path}")
        if _identity(current_stat) != _identity(opened_stat):
            raise RuntimeError(
                f"parent directory identity changed while opening: {path}"
            )
        return descriptor, opened_stat
    except BaseException:
        os.close(descriptor)
        raise


def _require_real_directory_at(
    parent_descriptor: int, basename: str, display_path: Path
) -> os.stat_result:
    result = os.stat(
        basename,
        dir_fd=parent_descriptor,
        follow_symlinks=False,
    )
    if stat.S_ISLNK(result.st_mode) or not stat.S_ISDIR(result.st_mode):
        raise ValueError(f"source must be a real directory: {display_path}")
    return result


def _require_absent_at(
    parent_descriptor: int, basename: str, display_path: Path
) -> None:
    try:
        os.stat(
            basename,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        return
    raise FileExistsError(f"target already exists: {display_path}")


def _same_filesystem(
    source_stat: os.stat_result,
    source_parent_stat: os.stat_result,
    target_parent_stat: os.stat_result,
) -> bool:
    return (
        source_stat.st_dev
        == source_parent_stat.st_dev
        == target_parent_stat.st_dev
    )


def _load_renameatx_np() -> Any:
    libc = ctypes.CDLL(None, use_errno=True)
    renameatx_np = libc.renameatx_np
    renameatx_np.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameatx_np.restype = ctypes.c_int
    return renameatx_np


def _invoke_renameatx_np(
    renameatx_np: Any,
    source_parent_descriptor: int,
    source_basename: bytes,
    target_parent_descriptor: int,
    target_basename: bytes,
    expected_source_stat: os.stat_result,
    source_display_path: Path,
) -> None:
    current_source_stat = _require_real_directory_at(
        source_parent_descriptor,
        os.fsdecode(source_basename),
        source_display_path,
    )
    if _identity(current_source_stat) != _identity(expected_source_stat):
        raise RuntimeError(
            "source directory identity changed before rename"
        )

    ctypes.set_errno(0)
    result = renameatx_np(
        source_parent_descriptor,
        source_basename,
        target_parent_descriptor,
        target_basename,
        RENAME_EXCL | RENAME_NOFOLLOW_ANY,
    )
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(
            error,
            os.strerror(error),
            os.fsdecode(target_basename),
        )


def exclusive_rename(source: Path, target: Path) -> None:
    if sys.platform != "darwin":
        raise RuntimeError("exclusive rename helper requires macOS")
    if not source.is_absolute() or not target.is_absolute():
        raise ValueError("source and target must be absolute")
    if not source.name or not target.name:
        raise ValueError("source and target must name directory entries")

    source_parent_descriptor, source_parent_stat = _open_real_directory(
        source.parent
    )
    try:
        target_parent_descriptor, target_parent_stat = _open_real_directory(
            target.parent
        )
        try:
            source_stat = _require_real_directory_at(
                source_parent_descriptor, source.name, source
            )
            _require_absent_at(
                target_parent_descriptor, target.name, target
            )
            if not _same_filesystem(
                source_stat, source_parent_stat, target_parent_stat
            ):
                raise ValueError(
                    "source and target must share a filesystem"
                )

            renameatx_np = _load_renameatx_np()
            _invoke_renameatx_np(
                renameatx_np,
                source_parent_descriptor,
                os.fsencode(source.name),
                target_parent_descriptor,
                os.fsencode(target.name),
                source_stat,
                source,
            )

            target_stat = _require_real_directory_at(
                target_parent_descriptor, target.name, target
            )
            if _identity(target_stat) != _identity(source_stat):
                raise RuntimeError("renamed directory identity changed")
            _require_absent_at(
                source_parent_descriptor, source.name, source
            )
        finally:
            os.close(target_parent_descriptor)
    finally:
        os.close(source_parent_descriptor)


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "usage: exclusive_rename.py SOURCE TARGET",
            file=sys.stderr,
        )
        return 2
    try:
        exclusive_rename(Path(sys.argv[1]), Path(sys.argv[2]))
    except (OSError, RuntimeError, ValueError) as error:
        print(f"exclusive rename failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
