from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


NOREPLY_EMAIL = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9+._-]*@users\.noreply\.github\.com"
)


class MetadataValidationError(RuntimeError):
    pass


def validate_metadata(root: Path) -> int:
    try:
        resolved_root = root.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise MetadataValidationError(
            "repository root cannot resolve safely"
        ) from error
    if not resolved_root.is_dir():
        raise MetadataValidationError(
            "repository root must be a directory"
        )
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(resolved_root),
            "log",
            "--format=%H%x00%ae%x00%ce",
            "HEAD",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise MetadataValidationError(
            "cannot read reachable Git metadata"
        )
    records = completed.stdout.splitlines()
    if not records:
        raise MetadataValidationError(
            "reachable Git history must not be empty"
        )
    for record in records:
        fields = record.split("\0")
        if len(fields) != 3:
            raise MetadataValidationError(
                "reachable Git metadata record is malformed"
            )
        commit, author_email, committer_email = fields
        for label, email in (
            ("author", author_email),
            ("committer", committer_email),
        ):
            if NOREPLY_EMAIL.fullmatch(email) is None:
                raise MetadataValidationError(
                    f"{commit} {label} email must use a GitHub "
                    "noreply address"
                )
    return len(records)


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "usage: validate_git_metadata.py REPOSITORY",
            file=sys.stderr,
        )
        return 2
    try:
        count = validate_metadata(Path(sys.argv[1]))
    except MetadataValidationError as error:
        print(f"Git metadata validation failed: {error}", file=sys.stderr)
        return 1
    print(
        f"Validated reachable Git metadata: {count} commits use "
        "GitHub noreply addresses."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
