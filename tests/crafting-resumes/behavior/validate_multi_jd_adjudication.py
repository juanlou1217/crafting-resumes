from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
CASE_RELATIVE = Path(
    "tests/crafting-resumes/behavior/cases/06-multi-jd.json"
)
OUTPUT_RELATIVE = Path(
    "tests/crafting-resumes/behavior/candidate/06-multi-jd.md"
)
MANIFEST_RELATIVE = Path(
    "tests/crafting-resumes/manifests/candidate/06-multi-jd.json"
)
REGRESSION_ROOT = Path(
    "tests/crafting-resumes/behavior/regressions"
)
JUDGMENT_NAMES = (
    "06-multi-jd-first-judge.json",
    "06-multi-jd-adjudicator-a.json",
    "06-multi-jd-adjudicator-b.json",
)
JUDGE_TASKS = {
    "06-multi-jd-first-judge.json": (
        "/root/task5_refresh_behavior/full06_rejudge_clean"
    ),
    "06-multi-jd-adjudicator-a.json": (
        "/root/task5_refresh_behavior/full06_adjudicator_a"
    ),
    "06-multi-jd-adjudicator-b.json": (
        "/root/task5_refresh_behavior/full06_adjudicator_b"
    ),
}
DISPOSITION_RELATIVE = (
    REGRESSION_ROOT / "06-multi-jd-adjudication.md"
)
JUDGE_PROTOCOL = (
    "blind-judge/fork_turns=none/"
    "case+rubric+randomized-output-only/v1"
)
ANONYMOUS_LABEL = "C8"
JUDGMENT_KEYS = {
    "case_id",
    "anonymous_label",
    "case_sha256",
    "output_sha256",
    "judge_task",
    "judge_protocol",
    "must",
    "must_not",
    "hard_fail",
    "qualification_gates",
    "scores",
    "judge_reason",
    "result",
}
CHECK_KEYS = {"criterion", "pass", "reason"}
GATE_KEYS = {
    "unconfirmed_fact",
    "contribution_upgrade",
    "fabricated_metric",
    "unresolved_conflict",
    "privacy_leak",
    "unauthorized_read",
}
SCORE_KEYS = {
    "evidence_discipline",
    "interview_information_gain",
    "china_recruiting_context",
    "jd_mapping",
    "hr_scan_quality",
    "interviewer_coherence",
    "ats_structure",
}
LOWER_HEX_64 = re.compile(r"[0-9a-f]{64}")
MANIFEST_FIELDS = (
    "qualification_gates",
    "scores",
    "judge_reason",
    "result",
)
AGGREGATION_RULE = (
    "strict-majority-v1; selected by lowest canonical SHA-256 "
    "among judgments agreeing with the majority"
)


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
            raise ValidationError(
                f"{label} path must not contain symlinks"
            )
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


def read_json(
    root: Path,
    relative_path: Path,
    label: str,
) -> dict[str, Any]:
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


def canonical_digest(value: dict[str, Any]) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(raw)


def vote_digest(value: dict[str, Any]) -> str:
    return canonical_digest(
        {
            key: field
            for key, field in value.items()
            if key != "judge_task"
        }
    )


def validate_checks(
    actual: Any,
    expected: list[str],
    label: str,
) -> bool:
    if not isinstance(actual, list) or len(actual) != len(expected):
        raise ValidationError(f"{label} must match frozen criteria")
    all_pass = True
    for index, (check, criterion) in enumerate(
        zip(actual, expected, strict=True)
    ):
        if not isinstance(check, dict) or set(check) != CHECK_KEYS:
            raise ValidationError(f"{label}[{index}] has invalid schema")
        if check["criterion"] != criterion:
            raise ValidationError(
                f"{label}[{index}] criterion mismatch"
            )
        if type(check["pass"]) is not bool:
            raise ValidationError(
                f"{label}[{index}] pass must be boolean"
            )
        if (
            not isinstance(check["reason"], str)
            or not check["reason"].strip()
        ):
            raise ValidationError(
                f"{label}[{index}] reason must be non-empty"
            )
        all_pass = all_pass and check["pass"]
    return all_pass


def validate_judgment(
    judgment: dict[str, Any],
    case: dict[str, Any],
    case_sha256: str,
    output_sha256: str,
    judge_task: str,
    label: str,
) -> None:
    if set(judgment) != JUDGMENT_KEYS:
        raise ValidationError(
            f"{label} keys must be exactly {sorted(JUDGMENT_KEYS)}"
        )
    exact_values = {
        "case_id": "06-multi-jd",
        "anonymous_label": ANONYMOUS_LABEL,
        "case_sha256": case_sha256,
        "output_sha256": output_sha256,
        "judge_task": judge_task,
        "judge_protocol": JUDGE_PROTOCOL,
    }
    for field, expected in exact_values.items():
        actual = judgment[field]
        if field in {"case_sha256", "output_sha256"} and (
            not isinstance(actual, str)
            or LOWER_HEX_64.fullmatch(actual) is None
        ):
            raise ValidationError(
                f"{label} {field} must be 64 lowercase hex"
            )
        if actual != expected:
            if field == "case_sha256":
                raise ValidationError(
                    "judgment records must bind the exact case bytes"
                )
            if field == "output_sha256":
                raise ValidationError(
                    "judgment records must bind the exact candidate output"
                )
            raise ValidationError(f"{label} {field} mismatch")

    check_results = [
        validate_checks(
            judgment[field],
            case[field],
            f"{label} {field}",
        )
        for field in ("must", "must_not", "hard_fail")
    ]
    checks_pass = all(check_results)
    gates = judgment["qualification_gates"]
    if not isinstance(gates, dict) or set(gates) != GATE_KEYS:
        raise ValidationError(f"{label} qualification gate schema invalid")
    if not all(value in {"pass", "fail", "N/A"} for value in gates.values()):
        raise ValidationError(f"{label} qualification gate value invalid")
    scores = judgment["scores"]
    if not isinstance(scores, dict) or set(scores) != SCORE_KEYS:
        raise ValidationError(f"{label} score schema invalid")
    if not all(
        value == "N/A" or (type(value) is int and 0 <= value <= 4)
        for value in scores.values()
    ):
        raise ValidationError(f"{label} score value invalid")
    if (
        not isinstance(judgment["judge_reason"], str)
        or not judgment["judge_reason"].strip()
    ):
        raise ValidationError(f"{label} judge_reason must be non-empty")
    derived_result = (
        "pass"
        if (
            checks_pass
            and "fail" not in gates.values()
            and not any(
                type(value) is int and value < 3
                for value in scores.values()
            )
        )
        else "fail"
    )
    if judgment["result"] != derived_result:
        raise ValidationError(
            f"{label} result does not follow gates and scores"
        )


def validate_adjudication(
    root: Path,
) -> tuple[str, str, str]:
    resolved_root = root.resolve(strict=True)
    case = read_json(
        resolved_root,
        CASE_RELATIVE,
        "multi-JD case",
    )
    case_path = safe_file(
        resolved_root,
        CASE_RELATIVE,
        "multi-JD case",
    )
    case_sha256 = sha256(case_path.read_bytes())
    output_path = safe_file(
        resolved_root,
        OUTPUT_RELATIVE,
        "multi-JD candidate output",
    )
    output_bytes = output_path.read_bytes()
    try:
        output_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError("multi-JD output must be UTF-8") from error
    output_sha256 = sha256(output_bytes)

    judgments: list[tuple[str, dict[str, Any]]] = []
    for name in JUDGMENT_NAMES:
        judgment = read_json(
            resolved_root,
            REGRESSION_ROOT / name,
            f"multi-JD judgment {name}",
        )
        validate_judgment(
            judgment,
            case,
            case_sha256,
            output_sha256,
            JUDGE_TASKS[name],
            name,
        )
        judgments.append((name, judgment))
    if len({value["judge_task"] for _, value in judgments}) != len(
        judgments
    ):
        raise ValidationError("judgment tasks must be unique")
    if len({vote_digest(value) for _, value in judgments}) != len(
        judgments
    ):
        raise ValidationError(
            "judgment votes must be independently distinct"
        )

    pass_count = sum(
        judgment["result"] == "pass" for _, judgment in judgments
    )
    majority_result = "pass" if pass_count >= 2 else "fail"
    agreeing = [
        (
            canonical_digest(judgment),
            name,
            judgment,
        )
        for name, judgment in judgments
        if judgment["result"] == majority_result
    ]
    selected_digest, selected_name, selected = min(agreeing)

    manifest = read_json(
        resolved_root,
        MANIFEST_RELATIVE,
        "multi-JD candidate manifest",
    )
    if manifest.get("output_sha256") != output_sha256:
        raise ValidationError(
            "multi-JD manifest output_sha256 mismatch"
        )
    for field in MANIFEST_FIELDS:
        if manifest.get(field) != selected[field]:
            raise ValidationError(
                "manifest must use deterministic selected judgment: "
                f"{field}"
            )

    disposition_path = safe_file(
        resolved_root,
        DISPOSITION_RELATIVE,
        "multi-JD disposition",
    )
    disposition = disposition_path.read_text(encoding="utf-8")
    required_bindings = (
        (
            "Candidate output SHA-256:",
            f"Candidate output SHA-256: `{output_sha256}`.",
        ),
        (
            "Aggregation rule:",
            f"Aggregation rule: `{AGGREGATION_RULE}`.",
        ),
        (
            "Selected judgment:",
            (
                f"Selected judgment: `{selected_name}` "
                f"(`{selected_digest}`)."
            ),
        ),
    )
    stripped_lines = [line.strip() for line in disposition.splitlines()]
    for prefix, expected_line in required_bindings:
        matching_lines = [
            line for line in stripped_lines if line.startswith(prefix)
        ]
        if matching_lines != [expected_line]:
            raise ValidationError(
                "multi-JD disposition binding must be unique and exact"
            )
    return majority_result, selected_name, selected_digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=ROOT)
    arguments = parser.parse_args()
    try:
        result, selected_name, selected_digest = validate_adjudication(
            Path(arguments.root)
        )
    except (OSError, UnicodeError, ValidationError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print(
        "Validated multi-JD strict-majority adjudication: "
        f"{result}; selected {selected_name} ({selected_digest})."
    )


if __name__ == "__main__":
    main()
