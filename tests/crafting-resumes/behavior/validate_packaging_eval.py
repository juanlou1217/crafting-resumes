from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path(__file__).resolve().parents[3]
RELATIVE_EVAL_ROOT = Path(
    "tests/crafting-resumes/behavior/packaging-eval"
)
RELATIVE_CASES_ROOT = Path(
    "tests/crafting-resumes/behavior/packaging-cases"
)
CASE_IDS = (
    "01-reasonable-language",
    "02-high-risk-verbs",
    "03-jd-keyword-gap",
    "04-evidence-backed-keywords",
)
CASE_KEYS = {"id", "prompt", "must", "must_not"}
PHASE_KEYS = {"phase", "skill_commit", "cases"}
RESULT_KEYS = {
    "id",
    "case_sha256",
    "output_path",
    "output_sha256",
    "must",
    "must_not",
    "result",
}
CHECK_KEYS = {"criterion", "pass", "reason"}
LOWER_HEX_40 = re.compile(r"[0-9a-f]{40}")
LOWER_HEX_64 = re.compile(r"[0-9a-f]{64}")
REQUIRED_SKILL_PATHS = (
    "skills/crafting-resumes/SKILL.md",
    (
        "skills/crafting-resumes/references/"
        "professional-packaging-and-keywords.md"
    ),
)


class ValidationError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValidationError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def read_json_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw_bytes = path.read_bytes()
    except OSError as error:
        raise ValidationError(f"cannot read {label}: {error}") from error
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError(f"{label} must be valid UTF-8") from error
    try:
        value = json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except json.JSONDecodeError as error:
        raise ValidationError(f"{label} must be valid JSON: {error.msg}") from error
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be a JSON object")
    return value, raw_bytes


def require_exact_keys(
    value: dict[str, Any],
    expected: set[str],
    label: str,
) -> None:
    actual = set(value)
    if actual != expected:
        raise ValidationError(
            f"{label} keys must be exactly {sorted(expected)}; "
            f"got {sorted(actual)}"
        )


def sha256(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()


def require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label} must be a non-empty string")
    return value


def require_repository_file(
    root: Path,
    relative_path: Path,
    label: str,
) -> Path:
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValidationError(f"{label} must stay inside the repository")
    if root.is_symlink():
        raise ValidationError(f"{label} path must not contain symlinks")
    current = root
    for index, part in enumerate(relative_path.parts):
        current = current / part
        if current.is_symlink():
            raise ValidationError(f"{label} path must not contain symlinks")
        if index < len(relative_path.parts) - 1:
            if not current.is_dir():
                raise ValidationError(
                    f"{label} parent must be a regular directory: "
                    f"{relative_path.as_posix()}"
                )
        elif not current.is_file():
            raise ValidationError(
                f"{label} must be a regular file: "
                f"{relative_path.as_posix()}"
            )
    return current


def load_cases(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, bytes]]:
    cases_root = root / RELATIVE_CASES_ROOT
    if cases_root.is_symlink() or not cases_root.is_dir():
        raise ValidationError(
            "focused packaging cases directory must be a regular directory"
        )
    actual_names = sorted(path.name for path in cases_root.iterdir())
    expected_names = [f"{case_id}.json" for case_id in CASE_IDS]
    if actual_names != expected_names:
        raise ValidationError(
            "focused packaging cases must be exactly "
            f"{expected_names}; got {actual_names}"
        )

    cases: dict[str, dict[str, Any]] = {}
    case_bytes: dict[str, bytes] = {}
    for case_id in CASE_IDS:
        relative_path = RELATIVE_CASES_ROOT / f"{case_id}.json"
        path = require_repository_file(
            root,
            relative_path,
            "focused packaging case",
        )
        case, raw_bytes = read_json_object(
            path,
            f"focused packaging case {case_id}",
        )
        require_exact_keys(
            case,
            CASE_KEYS,
            f"focused packaging case {case_id}",
        )
        if case["id"] != case_id:
            raise ValidationError(
                f"focused packaging case filename/id mismatch: {case_id}"
            )
        require_nonempty_string(
            case["prompt"],
            f"focused packaging case {case_id} prompt",
        )
        for field in ("must", "must_not"):
            criteria = case[field]
            if not isinstance(criteria, list) or not criteria:
                raise ValidationError(
                    f"focused packaging case {case_id} {field} "
                    "must be a non-empty list"
                )
            for index, criterion in enumerate(criteria):
                require_nonempty_string(
                    criterion,
                    f"focused packaging case {case_id} "
                    f"{field}[{index}]",
                )
        cases[case_id] = case
        case_bytes[case_id] = raw_bytes
    return cases, case_bytes


def validate_checks(
    actual: Any,
    expected: list[str],
    label: str,
) -> list[bool]:
    if not isinstance(actual, list) or len(actual) != len(expected):
        raise ValidationError(
            f"{label} checks must match the case criteria count"
        )
    pass_values: list[bool] = []
    for index, (check, criterion) in enumerate(zip(actual, expected, strict=True)):
        if not isinstance(check, dict):
            raise ValidationError(f"{label}[{index}] must be an object")
        require_exact_keys(check, CHECK_KEYS, f"{label}[{index}]")
        if check["criterion"] != criterion:
            raise ValidationError(
                f"{label}[{index}] criterion must match the frozen case"
            )
        if type(check["pass"]) is not bool:
            raise ValidationError(f"{label}[{index}] pass must be a boolean")
        require_nonempty_string(
            check["reason"],
            f"{label}[{index}] reason",
        )
        pass_values.append(check["pass"])
    return pass_values


def prove_skill_commit(root: Path, commit: str) -> None:
    completed = subprocess.run(
        ["git", "-C", str(root), "cat-file", "-e", f"{commit}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValidationError(
            "candidate skill_commit must name a commit in the repository"
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
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise ValidationError(
                "candidate skill_commit must contain required "
                f"Skill path: {relative_path}"
            )


def validate_phase(
    root: Path,
    phase: str,
    cases: dict[str, dict[str, Any]],
    case_bytes: dict[str, bytes],
    expected_skill_commit: str | None,
) -> list[str]:
    manifest_relative = RELATIVE_EVAL_ROOT / f"{phase}.json"
    manifest_path = require_repository_file(
        root,
        manifest_relative,
        f"{phase} focused manifest",
    )
    manifest, _ = read_json_object(
        manifest_path,
        f"{phase} focused manifest",
    )
    require_exact_keys(manifest, PHASE_KEYS, f"{phase} focused manifest")
    if manifest["phase"] != phase:
        raise ValidationError(f"{phase} manifest phase mismatch")

    skill_commit = manifest["skill_commit"]
    if phase == "baseline":
        if skill_commit is not None:
            raise ValidationError("baseline skill_commit must be null")
    else:
        if (
            not isinstance(skill_commit, str)
            or LOWER_HEX_40.fullmatch(skill_commit) is None
        ):
            raise ValidationError(
                "candidate skill_commit must be 40 lowercase hex characters"
            )
        if expected_skill_commit is None:
            raise ValidationError(
                "--expected-skill-commit is required for candidate validation"
            )
        if skill_commit != expected_skill_commit:
            raise ValidationError(
                "candidate skill_commit does not match expected commit"
            )
        prove_skill_commit(root, skill_commit)

    results = manifest["cases"]
    if not isinstance(results, list):
        raise ValidationError(f"{phase} manifest cases must be a list")
    actual_ids = [
        result.get("id") if isinstance(result, dict) else None
        for result in results
    ]
    if actual_ids != list(CASE_IDS):
        raise ValidationError(
            f"{phase} manifest cases must be in exact frozen order"
        )

    phase_results: list[str] = []
    for result, case_id in zip(results, CASE_IDS, strict=True):
        if not isinstance(result, dict):
            raise ValidationError(f"{phase}/{case_id} result must be an object")
        require_exact_keys(
            result,
            RESULT_KEYS,
            f"{phase}/{case_id} result",
        )
        case_sha = result["case_sha256"]
        if (
            not isinstance(case_sha, str)
            or LOWER_HEX_64.fullmatch(case_sha) is None
            or case_sha != sha256(case_bytes[case_id])
        ):
            raise ValidationError(f"{phase}/{case_id} case_sha256 mismatch")

        expected_output_path = (
            RELATIVE_EVAL_ROOT / phase / f"{case_id}.md"
        ).as_posix()
        if result["output_path"] != expected_output_path:
            raise ValidationError(
                f"{phase}/{case_id} output_path must be "
                f"{expected_output_path}"
            )
        output_path = require_repository_file(
            root,
            Path(expected_output_path),
            "focused output",
        )
        try:
            output_bytes = output_path.read_bytes()
        except OSError as error:
            raise ValidationError(
                f"cannot read focused output: {error}"
            ) from error
        try:
            output_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValidationError(
                "focused output must be valid UTF-8"
            ) from error
        output_sha = result["output_sha256"]
        if (
            not isinstance(output_sha, str)
            or LOWER_HEX_64.fullmatch(output_sha) is None
            or output_sha != sha256(output_bytes)
        ):
            raise ValidationError(f"{phase}/{case_id} output_sha256 mismatch")

        case = cases[case_id]
        checks = validate_checks(
            result["must"],
            case["must"],
            f"{phase}/{case_id} must",
        )
        checks.extend(
            validate_checks(
                result["must_not"],
                case["must_not"],
                f"{phase}/{case_id} must_not",
            )
        )
        expected_result = "pass" if all(checks) else "fail"
        if result["result"] not in {"pass", "fail"}:
            raise ValidationError(
                f"{phase}/{case_id} result must be pass or fail"
            )
        if result["result"] != expected_result:
            raise ValidationError(
                f"{phase}/{case_id} result is inconsistent with checks"
            )
        phase_results.append(result["result"])

    if phase == "baseline" and "fail" not in phase_results:
        raise ValidationError("baseline must contain at least one failing case")
    if phase == "candidate" and phase_results != ["pass"] * len(CASE_IDS):
        raise ValidationError("candidate must pass all focused packaging cases")
    return phase_results


def validate(
    root: Path,
    phase_selection: str,
    expected_skill_commit: str | None,
) -> tuple[int, int]:
    if (
        expected_skill_commit is not None
        and LOWER_HEX_40.fullmatch(expected_skill_commit) is None
    ):
        raise ValidationError(
            "expected skill commit must be 40 lowercase hex characters"
        )
    cases, case_bytes = load_cases(root)
    phases = ("baseline",) if phase_selection == "baseline" else (
        "baseline",
        "candidate",
    )
    result_count = 0
    for phase in phases:
        result_count += len(
            validate_phase(
                root,
                phase,
                cases,
                case_bytes,
                expected_skill_commit,
            )
        )
    return len(cases), result_count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate focused resume-packaging behavior assets."
    )
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=DEFAULT_ROOT,
        help="repository root (defaults to this checkout)",
    )
    parser.add_argument(
        "--phase",
        choices=("baseline", "both"),
        default="both",
    )
    parser.add_argument("--expected-skill-commit")
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    try:
        case_count, result_count = validate(
            arguments.root,
            arguments.phase,
            arguments.expected_skill_commit,
        )
    except Exception as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        return 1
    print(
        f"Validated {case_count} focused packaging cases, "
        f"{result_count} phase results."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
