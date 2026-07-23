from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PROVENANCE_ROOT = Path(
    "tests/crafting-resumes/behavior/provenance"
)
PROTOCOL = "fresh-agent/fork_turns=none/frozen-skill+single-prompt/v1"
RECEIPT_KEYS = {
    "suite",
    "case_id",
    "case_path",
    "case_sha256",
    "prompt_sha256",
    "frozen_skill_commit",
    "skill_root",
    "output_path",
    "output_sha256",
    "agent_task",
    "generation_protocol",
    "direct_write",
    "verbatim",
}
LOWER_HEX_40 = re.compile(r"[0-9a-f]{40}")
LOWER_HEX_64 = re.compile(r"[0-9a-f]{64}")
AGENT_TASK = re.compile(
    r"/root/task5_refresh_behavior/[a-z0-9_]+"
)
REQUIRED_SKILL_PATHS = (
    "skills/crafting-resumes/SKILL.md",
    (
        "skills/crafting-resumes/references/"
        "professional-packaging-and-keywords.md"
    ),
    (
        "skills/crafting-resumes/references/"
        "evidence-and-truthfulness.md"
    ),
)
SUITES = {
    "focused": {
        "case_root": Path(
            "tests/crafting-resumes/behavior/packaging-cases"
        ),
        "output_root": Path(
            "tests/crafting-resumes/behavior/"
            "packaging-eval/candidate"
        ),
        "ids": (
            "01-reasonable-language",
            "02-high-risk-verbs",
            "03-jd-keyword-gap",
            "04-evidence-backed-keywords",
        ),
    },
    "full": {
        "case_root": Path(
            "tests/crafting-resumes/behavior/cases"
        ),
        "output_root": Path(
            "tests/crafting-resumes/behavior/candidate"
        ),
        "ids": (
            "01-course-project",
            "02-overclaim-pressure",
            "03-conflict-and-privacy",
            "04-jd-only",
            "05-resume-only",
            "06-multi-jd",
            "07-career-transition",
            "08-product-role",
            "09-operations-role",
            "10-sales-role",
            "11-unauthorized-scan",
            "12-complete-delivery",
        ),
    },
}


class ValidationError(ValueError):
    pass


def sha256(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()


def reject_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def safe_file(root: Path, relative_path: Path, label: str) -> Path:
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValidationError(f"{label} must stay inside repository")
    current = root
    for part in relative_path.parts:
        current /= part
        if current.is_symlink():
            raise ValidationError(f"{label} path must not contain symlinks")
    try:
        resolved = current.resolve(strict=True)
    except (FileNotFoundError, RuntimeError) as error:
        raise ValidationError(f"{label} must exist safely") from error
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValidationError(f"{label} escapes repository") from error
    if not resolved.is_file():
        raise ValidationError(f"{label} must be a regular file")
    return resolved


def read_json(root: Path, relative_path: Path, label: str) -> dict[str, Any]:
    path = safe_file(root, relative_path, label)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError(f"{label} must be valid UTF-8") from error
    try:
        value = json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
        )
    except json.JSONDecodeError as error:
        raise ValidationError(f"{label} must be valid JSON") from error
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be a JSON object")
    return value


def prove_skill_commit(root: Path, commit: str) -> None:
    if LOWER_HEX_40.fullmatch(commit) is None:
        raise ValidationError(
            "frozen_skill_commit must be 40 lowercase hex characters"
        )
    for relative_path in REQUIRED_SKILL_PATHS:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "cat-file",
                "-e",
                f"{commit}:{relative_path}",
            ],
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise ValidationError(
                "frozen_skill_commit must contain required Skill path: "
                f"{relative_path}"
            )


def validate_receipts(
    root: Path,
    expected_skill_commit: str | None = None,
) -> tuple[int, str]:
    try:
        resolved_root = root.resolve(strict=True)
    except RuntimeError as error:
        raise ValidationError("repository root cannot resolve safely") from error
    if not resolved_root.is_dir():
        raise ValidationError("repository root must be a directory")

    commits: set[str] = set()
    agent_tasks: set[str] = set()
    receipt_count = 0
    for suite, config in SUITES.items():
        receipt_root = resolved_root / PROVENANCE_ROOT / suite
        if receipt_root.is_symlink() or not receipt_root.is_dir():
            raise ValidationError(
                f"{suite} receipt directory must be a regular directory"
            )
        expected_names = [
            f"{case_id}.json" for case_id in config["ids"]
        ]
        actual_names = sorted(path.name for path in receipt_root.iterdir())
        if actual_names != expected_names:
            raise ValidationError(
                f"{suite} receipt files must be exactly {expected_names}"
            )

        for case_id in config["ids"]:
            receipt_relative = (
                PROVENANCE_ROOT / suite / f"{case_id}.json"
            )
            receipt = read_json(
                resolved_root,
                receipt_relative,
                f"{suite} generation receipt",
            )
            if set(receipt) != RECEIPT_KEYS:
                raise ValidationError(
                    f"{suite} receipt keys must be exactly "
                    f"{sorted(RECEIPT_KEYS)}: {case_id}"
                )
            expected_case_path = (
                config["case_root"] / f"{case_id}.json"
            )
            expected_output_path = (
                config["output_root"] / f"{case_id}.md"
            )
            exact_values = {
                "suite": suite,
                "case_id": case_id,
                "case_path": expected_case_path.as_posix(),
                "skill_root": "skills/crafting-resumes",
                "output_path": expected_output_path.as_posix(),
                "generation_protocol": PROTOCOL,
            }
            for field, expected in exact_values.items():
                if receipt[field] != expected:
                    raise ValidationError(
                        f"{field} mismatch in generation receipt: {case_id}"
                    )
            if receipt["direct_write"] is not True:
                raise ValidationError(
                    f"direct_write attestation must be true: {case_id}"
                )
            if receipt["verbatim"] is not True:
                raise ValidationError(
                    f"verbatim attestation must be true: {case_id}"
                )
            agent_task = receipt["agent_task"]
            if (
                not isinstance(agent_task, str)
                or AGENT_TASK.fullmatch(agent_task) is None
            ):
                raise ValidationError(
                    f"agent_task must be a canonical generator task: {case_id}"
                )
            if agent_task in agent_tasks:
                raise ValidationError(
                    "agent_task values must be unique across receipts"
                )
            agent_tasks.add(agent_task)

            commit = receipt["frozen_skill_commit"]
            if not isinstance(commit, str):
                raise ValidationError(
                    f"frozen_skill_commit must be a string: {case_id}"
                )
            commits.add(commit)

            case_path = safe_file(
                resolved_root,
                expected_case_path,
                "generation case",
            )
            output_path = safe_file(
                resolved_root,
                expected_output_path,
                "generation output",
            )
            case_bytes = case_path.read_bytes()
            case = read_json(
                resolved_root,
                expected_case_path,
                "generation case",
            )
            prompt = case.get("prompt")
            if not isinstance(prompt, str) or not prompt:
                raise ValidationError(
                    f"case prompt must be a non-empty string: {case_id}"
                )
            output_bytes = output_path.read_bytes()
            try:
                output_bytes.decode("utf-8")
            except UnicodeDecodeError as error:
                raise ValidationError(
                    f"generation output must be UTF-8: {case_id}"
                ) from error
            expected_hashes = {
                "case_sha256": sha256(case_bytes),
                "prompt_sha256": sha256(prompt.encode("utf-8")),
                "output_sha256": sha256(output_bytes),
            }
            for field, expected in expected_hashes.items():
                actual = receipt[field]
                if (
                    not isinstance(actual, str)
                    or LOWER_HEX_64.fullmatch(actual) is None
                ):
                    raise ValidationError(
                        f"{field} must be 64 lowercase hex: {case_id}"
                    )
                if actual != expected:
                    raise ValidationError(
                        f"{field} mismatch in generation receipt: {case_id}"
                    )
            receipt_count += 1

    if len(commits) != 1:
        raise ValidationError(
            "generation receipts must share one frozen Skill commit"
        )
    commit = next(iter(commits))
    if expected_skill_commit is not None and commit != expected_skill_commit:
        raise ValidationError(
            "generation receipt commit does not match expected commit"
        )
    prove_skill_commit(resolved_root, commit)
    return receipt_count, commit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=ROOT)
    parser.add_argument("--expected-skill-commit")
    arguments = parser.parse_args()
    try:
        count, commit = validate_receipts(
            Path(arguments.root),
            arguments.expected_skill_commit,
        )
    except (OSError, UnicodeError, ValidationError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print(
        f"Validated {count} fresh generation receipts at {commit}."
    )


if __name__ == "__main__":
    main()
