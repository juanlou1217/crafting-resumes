from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


MAPPING_RELATIVE = Path(
    "tests/crafting-resumes/behavior/provenance/"
    "commit-equivalence.json"
)
MAPPING_KEYS = {
    "schema_version",
    "kind",
    "original_commit",
    "published_commit",
    "commit_tree_oid",
    "skill_path",
    "skill_tree_oid",
    "reason",
}
LOWER_HEX_40 = re.compile(r"[0-9a-f]{40}")
EXPECTED_KIND = "tree-identical-pre-publication-history-rewrite"
EXPECTED_SKILL_PATH = "skills/crafting-resumes"


class CommitEquivalenceError(RuntimeError):
    pass


def _reject_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CommitEquivalenceError(
                f"commit equivalence mapping has duplicate key: {key}"
            )
        result[key] = value
    return result


def _run_git(
    root: Path, *arguments: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def _git_value(root: Path, *arguments: str, label: str) -> str:
    completed = _run_git(root, *arguments)
    if completed.returncode != 0:
        raise CommitEquivalenceError(label)
    value = completed.stdout.strip()
    if not value:
        raise CommitEquivalenceError(label)
    return value


def _commit_exists(root: Path, commit: str) -> bool:
    completed = _run_git(root, "cat-file", "-t", commit)
    return completed.returncode == 0 and completed.stdout.strip() == "commit"


def _require_hex_oid(value: Any, label: str) -> str:
    if not isinstance(value, str) or LOWER_HEX_40.fullmatch(value) is None:
        raise CommitEquivalenceError(
            f"{label} must be 40 lowercase hex characters"
        )
    return value


def _load_mapping(root: Path) -> dict[str, Any] | None:
    path = root / MAPPING_RELATIVE
    if not path.exists() and not path.is_symlink():
        return None
    parent = root
    for component in MAPPING_RELATIVE.parent.parts:
        parent /= component
        if parent.is_symlink() or not parent.is_dir():
            raise CommitEquivalenceError(
                "commit equivalence mapping parents must be real directories"
            )
    if path.is_symlink() or not path.is_file():
        raise CommitEquivalenceError(
            "commit equivalence mapping must be a regular file"
        )
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise CommitEquivalenceError(
            "commit equivalence mapping must be valid UTF-8"
        ) from error
    try:
        mapping = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
        )
    except json.JSONDecodeError as error:
        raise CommitEquivalenceError(
            "commit equivalence mapping must be valid JSON"
        ) from error
    if not isinstance(mapping, dict):
        raise CommitEquivalenceError(
            "commit equivalence mapping must be a JSON object"
        )
    if set(mapping) != MAPPING_KEYS:
        raise CommitEquivalenceError(
            "commit equivalence mapping keys must be exactly "
            f"{sorted(MAPPING_KEYS)}"
        )
    if mapping["schema_version"] != 1:
        raise CommitEquivalenceError(
            "commit equivalence schema_version must be 1"
        )
    if mapping["kind"] != EXPECTED_KIND:
        raise CommitEquivalenceError(
            f"commit equivalence kind must be {EXPECTED_KIND}"
        )
    original = _require_hex_oid(
        mapping["original_commit"], "original_commit"
    )
    published = _require_hex_oid(
        mapping["published_commit"], "published_commit"
    )
    if original == published:
        raise CommitEquivalenceError(
            "original_commit and published_commit must differ"
        )
    _require_hex_oid(mapping["commit_tree_oid"], "commit_tree_oid")
    _require_hex_oid(mapping["skill_tree_oid"], "skill_tree_oid")
    if mapping["skill_path"] != EXPECTED_SKILL_PATH:
        raise CommitEquivalenceError(
            f"skill_path must be {EXPECTED_SKILL_PATH}"
        )
    reason = mapping["reason"]
    if not isinstance(reason, str) or not reason.strip():
        raise CommitEquivalenceError("reason must be a non-empty string")
    return mapping


def _verify_mapping(root: Path, mapping: dict[str, Any]) -> str:
    original = mapping["original_commit"]
    published = mapping["published_commit"]
    if not _commit_exists(root, published):
        raise CommitEquivalenceError(
            "published_commit must resolve to a reachable commit"
        )
    ancestor = _run_git(
        root, "merge-base", "--is-ancestor", published, "HEAD"
    )
    if ancestor.returncode != 0:
        raise CommitEquivalenceError(
            "published_commit must be an ancestor of HEAD"
        )

    published_tree = _git_value(
        root,
        "rev-parse",
        f"{published}^{{tree}}",
        label="cannot read published commit tree",
    )
    if published_tree != mapping["commit_tree_oid"]:
        raise CommitEquivalenceError(
            "published commit tree does not match equivalence mapping"
        )
    published_skill_tree = _git_value(
        root,
        "rev-parse",
        f"{published}:{mapping['skill_path']}",
        label="cannot read published Skill tree",
    )
    if published_skill_tree != mapping["skill_tree_oid"]:
        raise CommitEquivalenceError(
            "published Skill tree does not match equivalence mapping"
        )

    if _commit_exists(root, original):
        original_tree = _git_value(
            root,
            "rev-parse",
            f"{original}^{{tree}}",
            label="cannot read original commit tree",
        )
        if original_tree != mapping["commit_tree_oid"]:
            raise CommitEquivalenceError(
                "original commit tree does not match equivalence mapping"
            )
        original_skill_tree = _git_value(
            root,
            "rev-parse",
            f"{original}:{mapping['skill_path']}",
            label="cannot read original Skill tree",
        )
        if original_skill_tree != mapping["skill_tree_oid"]:
            raise CommitEquivalenceError(
                "original Skill tree does not match equivalence mapping"
            )
    return published


def resolve_skill_commit(root: Path, requested_commit: str) -> str:
    try:
        resolved_root = root.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise CommitEquivalenceError(
            "repository root cannot resolve safely"
        ) from error
    if not resolved_root.is_dir():
        raise CommitEquivalenceError(
            "repository root must be a directory"
        )
    requested = _require_hex_oid(
        requested_commit, "requested commit"
    )
    mapping = _load_mapping(resolved_root)
    if mapping is not None and requested == mapping["original_commit"]:
        return _verify_mapping(resolved_root, mapping)
    if not _commit_exists(resolved_root, requested):
        raise CommitEquivalenceError(
            "requested commit must resolve to a commit"
        )
    return requested


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "usage: commit_equivalence.py REPOSITORY COMMIT",
            file=sys.stderr,
        )
        return 2
    try:
        published = resolve_skill_commit(Path(sys.argv[1]), sys.argv[2])
    except CommitEquivalenceError as error:
        print(f"commit equivalence failed: {error}", file=sys.stderr)
        return 1
    print(published)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
