from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EXPECTED_CASE_IDS = {
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
}
CASE_KEYS = {"id", "category", "prompt", "must", "must_not", "hard_fail"}
MANIFEST_KEYS = {
    "case_id",
    "phase",
    "skill_commit",
    "case_sha256",
    "model",
    "environment",
    "raw_output_path",
    "output_sha256",
    "qualification_gates",
    "scores",
    "judge_reason",
    "result",
}
QUALIFICATION_GATE_KEYS = {
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
FORBIDDEN_TOKENS = (
    "private-profile-dir",
    "private-resume-dir",
    "private-projects-dir",
    "private-inbox-dir",
    "private-archive-dir",
    "候选人甲",
    "private-account-token",
)


class ValidationError(ValueError):
    pass


def ensure_within_root(path: Path, root: Path, label: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ValidationError(f"{label} path escapes resolved root: {path}") from error


def resolve_safe_file(path: Path, root: Path, label: str) -> Path:
    if path.is_symlink():
        raise ValidationError(f"{label} symlink files are not allowed: {path}")
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as error:
        raise ValidationError(f"{label} does not exist: {path}") from error
    except RuntimeError as error:
        raise ValidationError(f"{label} cannot be resolved safely: {path}") from error
    ensure_within_root(resolved, root, label)
    if not resolved.is_file():
        raise ValidationError(f"{label} must be a regular file: {path}")
    return resolved


def resolve_optional_directory(path: Path, root: Path, label: str) -> Path | None:
    if path.is_symlink():
        raise ValidationError(f"{label} directory symlinks are not allowed: {path}")
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError:
        return None
    except RuntimeError as error:
        raise ValidationError(f"{label} cannot be resolved safely: {path}") from error
    ensure_within_root(resolved, root, label)
    if not resolved.is_dir():
        raise ValidationError(f"{label} must be a directory: {path}")
    return resolved


def load_json_object(
    path: Path, root: Path, label: str
) -> tuple[Path, dict[str, object]]:
    safe_path = resolve_safe_file(path, root, label)
    try:
        text = safe_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError(
            f"{label} must be valid UTF-8: {safe_path.name}"
        ) from error

    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValidationError(
                    f"{label} contains duplicate JSON key {key!r}: {safe_path.name}"
                )
            result[key] = value
        return result

    try:
        data = json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except json.JSONDecodeError as error:
        raise ValidationError(
            f"{label} is not valid JSON: {safe_path.name}: {error.msg}"
        ) from error
    if not isinstance(data, dict):
        raise ValidationError(
            f"{label} top-level JSON value must be an object: {safe_path.name}"
        )
    return safe_path, data


def reject_forbidden_tokens(
    data: dict[str, object], path: Path, label: str
) -> None:
    serialized = json.dumps(data, ensure_ascii=False)
    for token in FORBIDDEN_TOKENS:
        if token in serialized:
            raise ValidationError(
                f"forbidden personal token {token!r} in {label}: {path.name}"
            )


def load_cases(
    cases_dir: Path, root: Path
) -> list[tuple[Path, dict[str, object]]]:
    cases: list[tuple[Path, dict[str, object]]] = []
    resolved_cases_dir = resolve_optional_directory(cases_dir, root, "cases directory")
    if resolved_cases_dir is None:
        raise ValidationError(f"cases directory does not exist: {cases_dir}")
    paths = sorted(resolved_cases_dir.glob("*.json"))
    if {path.stem for path in paths} != EXPECTED_CASE_IDS:
        raise ValidationError("case files must be exactly the frozen 01..12 set")
    for path in paths:
        safe_path, case = load_json_object(path, root, "case JSON")
        reject_forbidden_tokens(case, safe_path, "case JSON")
        if set(case) != CASE_KEYS:
            raise ValidationError(f"case keys must be exactly {sorted(CASE_KEYS)}: {path.name}")
        if case.get("id") != path.stem:
            raise ValidationError(
                f"filename/id mismatch: {path.name} declares {case.get('id')!r}"
            )
        for field in ("category", "prompt"):
            if not isinstance(case[field], str) or not case[field].strip():
                raise ValidationError(
                    f"{field} must be a non-empty string: {path.name}"
                )
        for field in ("must", "must_not", "hard_fail"):
            values = case[field]
            if not (
                isinstance(values, list)
                and values
                and all(isinstance(value, str) and value.strip() for value in values)
            ):
                raise ValidationError(
                    f"{field} must be a non-empty string list: {path.name}"
                )
        cases.append((safe_path, case))
    return cases


def load_manifests(
    manifests_dir: Path, root: Path
) -> list[tuple[Path, dict[str, object]]]:
    manifests: list[tuple[Path, dict[str, object]]] = []
    for phase in ("baseline", "candidate"):
        phase_dir = resolve_optional_directory(
            manifests_dir / phase, root, f"{phase} manifests directory"
        )
        if phase_dir is None:
            continue
        for path in sorted(phase_dir.glob("*.json")):
            safe_path, manifest = load_json_object(path, root, "manifest JSON")
            reject_forbidden_tokens(manifest, safe_path, "manifest JSON")
            if set(manifest) != MANIFEST_KEYS:
                raise ValidationError(
                    f"manifest keys must be exactly {sorted(MANIFEST_KEYS)}: {path.name}"
                )
            if manifest["case_id"] != path.stem:
                raise ValidationError(
                    f"manifest filename/case_id mismatch: {path.name}"
                )
            for field in ("model", "environment", "judge_reason"):
                if not isinstance(manifest[field], str) or not manifest[field].strip():
                    raise ValidationError(
                        f"{field} must be a non-empty string: {path.name}"
                    )
            if manifest["phase"] != phase:
                raise ValidationError(
                    f"manifest phase does not match directory: {path.name}"
                )
            if phase == "baseline" and manifest["skill_commit"] is not None:
                raise ValidationError(
                    f"baseline skill_commit must be null: {path.name}"
                )
            if phase == "candidate" and not (
                isinstance(manifest["skill_commit"], str)
                and re.fullmatch(r"[0-9a-f]{40}", manifest["skill_commit"])
            ):
                raise ValidationError(
                    "candidate skill_commit must be 40 lowercase hex characters: "
                    f"{path.name}"
                )
            if not isinstance(manifest["result"], str) or manifest["result"] not in {
                "pass",
                "fail",
            }:
                raise ValidationError(f"result must be pass or fail: {path.name}")
            for field in ("qualification_gates", "scores"):
                if not isinstance(manifest[field], dict):
                    raise ValidationError(f"{field} must be an object: {path.name}")
            if set(manifest["qualification_gates"]) != QUALIFICATION_GATE_KEYS:
                raise ValidationError(
                    "qualification_gates keys must be exactly "
                    f"{sorted(QUALIFICATION_GATE_KEYS)}: {path.name}"
                )
            if not all(
                isinstance(value, str)
                and value in {"pass", "fail", "N/A"}
                for value in manifest["qualification_gates"].values()
            ):
                raise ValidationError(
                    "qualification_gates values must be pass, fail, or N/A: "
                    f"{path.name}"
                )
            if set(manifest["scores"]) != SCORE_KEYS:
                raise ValidationError(
                    f"scores keys must be exactly {sorted(SCORE_KEYS)}: {path.name}"
                )
            if not all(
                value == "N/A"
                or (type(value) is int and 0 <= value <= 4)
                for value in manifest["scores"].values()
            ):
                raise ValidationError(
                    f"scores values must be integer 0..4 or N/A: {path.name}"
                )
            if (
                "fail" in manifest["qualification_gates"].values()
                and manifest["result"] != "fail"
            ):
                raise ValidationError(
                    "result must be fail when a qualification gate fails: "
                    f"{path.name}"
                )
            if (
                any(
                    type(value) is int and value < 3
                    for value in manifest["scores"].values()
                )
                and manifest["result"] != "fail"
            ):
                raise ValidationError(
                    "result must be fail when an applicable score is below 3: "
                    f"{path.name}"
                )
            raw_output_path = manifest.get("raw_output_path")
            if not isinstance(raw_output_path, str) or not raw_output_path.strip():
                raise ValidationError(
                    f"raw_output_path must be a non-empty string: {path.name}"
                )
            if Path(raw_output_path).is_absolute():
                raise ValidationError(
                    f"raw_output_path must be repository-relative: {path.name}"
                )
            if ".." in Path(raw_output_path).parts:
                raise ValidationError(
                    f"raw_output_path must not contain '..': {path.name}"
                )
            output_sha256 = manifest.get("output_sha256")
            if not (
                isinstance(output_sha256, str)
                and re.fullmatch(r"[0-9a-f]{64}", output_sha256)
            ):
                raise ValidationError(
                    "output_sha256 must be 64 lowercase hex characters: "
                    f"{path.name}"
                )
            output_path = resolve_safe_file(
                root / raw_output_path,
                root,
                "raw_output_path",
            )
            actual_output_sha256 = hashlib.sha256(
                output_path.read_bytes()
            ).hexdigest()
            if output_sha256 != actual_output_sha256:
                raise ValidationError(
                    f"output_sha256 mismatch: {path.name}"
                )
            manifests.append((safe_path, manifest))
    return manifests


def validate_assets(root: Path) -> tuple[int, int]:
    try:
        resolved_root = root.resolve(strict=True)
    except RuntimeError as error:
        raise ValidationError(f"validation root cannot be resolved safely: {root}") from error
    if not resolved_root.is_dir():
        raise ValidationError(f"validation root must be a directory: {root}")
    cases_dir = resolved_root / "tests/crafting-resumes/behavior/cases"
    manifests_dir = resolved_root / "tests/crafting-resumes/manifests"
    cases = load_cases(cases_dir, resolved_root)
    manifests = load_manifests(manifests_dir, resolved_root)
    case_hashes = {
        path.stem: hashlib.sha256(path.read_bytes()).hexdigest() for path, _ in cases
    }
    for path, manifest in manifests:
        case_id = manifest.get("case_id")
        if case_id in case_hashes and manifest.get("case_sha256") != case_hashes[case_id]:
            raise ValidationError(f"case_sha256 mismatch: {path.name}")
    expected_case_ids = set(case_hashes)
    for phase in ("baseline", "candidate"):
        phase_manifests = [
            manifest for _, manifest in manifests if manifest["phase"] == phase
        ]
        if phase_manifests:
            phase_case_ids = {manifest.get("case_id") for manifest in phase_manifests}
            if (
                len(phase_manifests) != len(expected_case_ids)
                or phase_case_ids != expected_case_ids
            ):
                raise ValidationError(
                    f"{phase} manifests must cover all 12 cases"
                )
    baseline_by_case = {
        manifest["case_id"]: manifest
        for _, manifest in manifests
        if manifest["phase"] == "baseline"
    }
    candidate_by_case = {
        manifest["case_id"]: manifest
        for _, manifest in manifests
        if manifest["phase"] == "candidate"
    }
    if baseline_by_case and candidate_by_case:
        for case_id in sorted(expected_case_ids):
            if (
                baseline_by_case[case_id]["result"] == "pass"
                and candidate_by_case[case_id]["result"] != "pass"
            ):
                raise ValidationError(
                    "candidate must not regress on a baseline-pass case: "
                    f"{case_id}"
                )
        for case_id in sorted(expected_case_ids):
            if candidate_by_case[case_id]["result"] != "pass":
                raise ValidationError(
                    f"candidate result must be pass: {case_id}"
                )
        candidate_skill_commits = {
            manifest["skill_commit"]
            for manifest in candidate_by_case.values()
        }
        if len(candidate_skill_commits) != 1:
            raise ValidationError(
                "candidate manifests must share one skill commit"
            )
    case_count = len(cases)
    manifest_count = len(manifests)
    return case_count, manifest_count


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) == 2 else ROOT
    try:
        case_count, manifest_count = validate_assets(root)
    except (OSError, json.JSONDecodeError, UnicodeError, ValidationError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print(f"Validated {case_count} frozen cases, {manifest_count} eval manifests.")


if __name__ == "__main__":
    main()
