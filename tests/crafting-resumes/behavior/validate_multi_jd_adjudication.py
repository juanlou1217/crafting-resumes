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
    "output_sha256",
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


def read_json(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValidationError(f"{label} must be a regular non-symlink file")
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
    output_sha256: str,
    label: str,
) -> None:
    if set(judgment) != JUDGMENT_KEYS:
        raise ValidationError(
            f"{label} keys must be exactly {sorted(JUDGMENT_KEYS)}"
        )
    exact_values = {
        "case_id": "06-multi-jd",
        "anonymous_label": ANONYMOUS_LABEL,
        "output_sha256": output_sha256,
        "judge_protocol": JUDGE_PROTOCOL,
    }
    for field, expected in exact_values.items():
        actual = judgment[field]
        if field == "output_sha256" and (
            not isinstance(actual, str)
            or LOWER_HEX_64.fullmatch(actual) is None
        ):
            raise ValidationError(
                f"{label} output_sha256 must be 64 lowercase hex"
            )
        if actual != expected:
            if field == "output_sha256":
                raise ValidationError(
                    "judgment records must bind the exact candidate output"
                )
            raise ValidationError(f"{label} {field} mismatch")

    checks_pass = all(
        validate_checks(
            judgment[field],
            case[field],
            f"{label} {field}",
        )
        for field in ("must", "must_not", "hard_fail")
    )
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
        resolved_root / CASE_RELATIVE,
        "multi-JD case",
    )
    output_path = resolved_root / OUTPUT_RELATIVE
    if output_path.is_symlink() or not output_path.is_file():
        raise ValidationError(
            "multi-JD candidate output must be a regular file"
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
            resolved_root / REGRESSION_ROOT / name,
            f"multi-JD judgment {name}",
        )
        validate_judgment(
            judgment,
            case,
            output_sha256,
            name,
        )
        judgments.append((name, judgment))

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
        resolved_root / MANIFEST_RELATIVE,
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

    disposition_path = resolved_root / DISPOSITION_RELATIVE
    if disposition_path.is_symlink() or not disposition_path.is_file():
        raise ValidationError(
            "multi-JD disposition must be a regular file"
        )
    disposition = disposition_path.read_text(encoding="utf-8")
    required_lines = (
        f"Candidate output SHA-256: `{output_sha256}`.",
        f"Aggregation rule: `{AGGREGATION_RULE}`.",
        (
            f"Selected judgment: `{selected_name}` "
            f"(`{selected_digest}`)."
        ),
    )
    for line in required_lines:
        if line not in disposition:
            raise ValidationError(
                "multi-JD disposition missing deterministic binding"
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
