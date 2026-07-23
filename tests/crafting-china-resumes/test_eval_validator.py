from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tests/crafting-china-resumes/behavior/validate_eval_assets.py"
FORBIDDEN_TOKENS = (
    "private-profile-dir",
    "private-resume-dir",
    "private-projects-dir",
    "private-inbox-dir",
    "private-archive-dir",
    "候选人甲",
    "private-account-token",
)


class EvalValidatorTests(unittest.TestCase):
    def run_validator(self, root: Path = ROOT) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(VALIDATOR), str(root)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def copy_eval_tree(self, destination: Path, source: Path = ROOT) -> None:
        shutil.copytree(
            source / "tests/crafting-china-resumes/behavior/cases",
            destination / "tests/crafting-china-resumes/behavior/cases",
        )

    def assert_stable_validation_failure(
        self, completed: subprocess.CompletedProcess[str]
    ) -> None:
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertTrue(
            completed.stderr.startswith("Validation failed:"), completed.stderr
        )
        self.assertNotIn("Traceback", completed.stderr)

    def write_phase_manifests(
        self,
        root: Path,
        phase: str,
        case_paths: list[Path] | None = None,
    ) -> list[Path]:
        cases_dir = root / "tests/crafting-china-resumes/behavior/cases"
        selected_cases = case_paths or sorted(cases_dir.glob("*.json"))
        manifest_dir = root / f"tests/crafting-china-resumes/manifests/{phase}"
        output_dir = root / f"tests/crafting-china-resumes/behavior/{phase}"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_paths: list[Path] = []
        for case_path in selected_cases:
            case_id = case_path.stem
            raw_relative = Path(
                f"tests/crafting-china-resumes/behavior/{phase}/{case_id}.md"
            )
            (root / raw_relative).write_text("synthetic output\n", encoding="utf-8")
            manifest = {
                "case_id": case_id,
                "phase": phase,
                "skill_commit": None if phase == "baseline" else "a" * 40,
                "case_sha256": hashlib.sha256(case_path.read_bytes()).hexdigest(),
                "model": "test-model",
                "environment": "unit-test",
                "raw_output_path": raw_relative.as_posix(),
                "qualification_gates": {
                    "unconfirmed_fact": "pass",
                    "contribution_upgrade": "pass",
                    "fabricated_metric": "pass",
                    "unresolved_conflict": "pass",
                    "privacy_leak": "pass",
                    "unauthorized_read": "pass",
                },
                "scores": {
                    "evidence_discipline": 3,
                    "interview_information_gain": 3,
                    "china_recruiting_context": 3,
                    "jd_mapping": 3,
                    "hr_scan_quality": 3,
                    "interviewer_coherence": 3,
                    "ats_structure": 3,
                },
                "judge_reason": "synthetic judgment",
                "result": "pass",
            }
            manifest_path = manifest_dir / f"{case_id}.json"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            manifest_paths.append(manifest_path)
        return manifest_paths

    def test_frozen_corpus_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)

            completed = self.run_validator(root)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout,
            "Validated 12 frozen cases, 0 eval manifests.\n",
        )

    def test_repository_integration_smoke(self) -> None:
        completed = self.run_validator()

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(
            completed.stdout.startswith("Validated 12 frozen cases, "),
            completed.stdout,
        )

    def test_isolated_smoke_ignores_future_complete_baseline(self) -> None:
        with (
            tempfile.TemporaryDirectory() as future_directory,
            tempfile.TemporaryDirectory() as isolated_directory,
        ):
            future_root = Path(future_directory)
            isolated_root = Path(isolated_directory)
            self.copy_eval_tree(future_root)
            self.write_phase_manifests(future_root, "baseline")
            self.copy_eval_tree(isolated_root, source=future_root)

            completed = self.run_validator(isolated_root)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout,
            "Validated 12 frozen cases, 0 eval manifests.\n",
        )

    def test_accepts_complete_baseline_and_candidate_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            self.write_phase_manifests(root, "baseline")
            self.write_phase_manifests(root, "candidate")

            completed = self.run_validator(root)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout,
            "Validated 12 frozen cases, 24 eval manifests.\n",
        )

    def test_rejects_candidate_regression_on_baseline_pass_case(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            self.write_phase_manifests(root, "baseline")
            candidate_path = self.write_phase_manifests(
                root, "candidate"
            )[0]
            candidate = json.loads(
                candidate_path.read_text(encoding="utf-8")
            )
            candidate["scores"]["evidence_discipline"] = 2
            candidate["result"] = "fail"
            candidate_path.write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "candidate must not regress on a baseline-pass case",
            completed.stderr,
        )

    def test_rejects_filename_id_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            case_path = (
                root
                / "tests/crafting-china-resumes/behavior/cases/01-course-project.json"
            )
            case = json.loads(case_path.read_text(encoding="utf-8"))
            case["id"] = "01-wrong-id"
            case_path.write_text(
                json.dumps(case, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("filename/id mismatch", completed.stderr)

    def test_rejects_forbidden_personal_tokens(self) -> None:
        for token in FORBIDDEN_TOKENS:
            with self.subTest(token=token):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    self.copy_eval_tree(root)
                    case_path = (
                        root
                        / "tests/crafting-china-resumes/behavior/cases/01-course-project.json"
                    )
                    case = json.loads(case_path.read_text(encoding="utf-8"))
                    case["must"].append(f"读取 {token}")
                    case_path.write_text(
                        json.dumps(case, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )

                    completed = self.run_validator(root)

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("forbidden personal token", completed.stderr)

    def test_rejects_unicode_escaped_personal_token_in_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["judge_reason"] = "候选人甲"
            encoded_manifest = json.dumps(manifest, ensure_ascii=True, indent=2) + "\n"
            self.assertIn(r"\u5019\u9009\u4eba\u7532", encoded_manifest)
            manifest_path.write_text(encoded_manifest, encoding="utf-8")

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("forbidden personal token", completed.stderr)

    def test_rejects_duplicate_case_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            case_path = (
                root
                / "tests/crafting-china-resumes/behavior/cases/01-course-project.json"
            )
            case_text = case_path.read_text(encoding="utf-8").replace(
                '  "id": "01-course-project",',
                '  "id": "01-course-project",\n  "id": "01-course-project",',
                1,
            )
            case_path.write_text(case_text, encoding="utf-8")

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("duplicate JSON key", completed.stderr)

    def test_rejects_duplicate_manifest_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest_text = manifest_path.read_text(encoding="utf-8").replace(
                '  "case_id": "01-course-project",',
                '  "case_id": "01-course-project",\n'
                '  "case_id": "01-course-project",',
                1,
            )
            manifest_path.write_text(manifest_text, encoding="utf-8")

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("duplicate JSON key", completed.stderr)

    def test_rejects_null_case_with_stable_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            case_path = (
                root
                / "tests/crafting-china-resumes/behavior/cases/01-course-project.json"
            )
            case_path.write_text("null\n", encoding="utf-8")

            completed = self.run_validator(root)

        self.assert_stable_validation_failure(completed)
        self.assertIn("top-level JSON value must be an object", completed.stderr)

    def test_rejects_null_manifest_with_stable_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest_path.write_text("null\n", encoding="utf-8")

            completed = self.run_validator(root)

        self.assert_stable_validation_failure(completed)
        self.assertIn("top-level JSON value must be an object", completed.stderr)

    def test_rejects_non_utf8_case_with_stable_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            case_path = (
                root
                / "tests/crafting-china-resumes/behavior/cases/01-course-project.json"
            )
            case_path.write_bytes(b"\xff")

            completed = self.run_validator(root)

        self.assert_stable_validation_failure(completed)
        self.assertIn("must be valid UTF-8", completed.stderr)

    def test_rejects_case_file_symlink_outside_root(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary_directory,
            tempfile.TemporaryDirectory() as outside_directory,
        ):
            root = Path(temporary_directory)
            outside = Path(outside_directory)
            self.copy_eval_tree(root)
            case_path = (
                root
                / "tests/crafting-china-resumes/behavior/cases/01-course-project.json"
            )
            outside_case = outside / case_path.name
            shutil.copy2(case_path, outside_case)
            case_path.unlink()
            case_path.symlink_to(outside_case)

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("symlink files are not allowed", completed.stderr)

    def test_rejects_manifest_file_symlink_outside_root(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary_directory,
            tempfile.TemporaryDirectory() as outside_directory,
        ):
            root = Path(temporary_directory)
            outside = Path(outside_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            outside_manifest = outside / manifest_path.name
            shutil.copy2(manifest_path, outside_manifest)
            manifest_path.unlink()
            manifest_path.symlink_to(outside_manifest)

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("symlink files are not allowed", completed.stderr)

    def test_rejects_raw_output_file_symlink_outside_root(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary_directory,
            tempfile.TemporaryDirectory() as outside_directory,
        ):
            root = Path(temporary_directory)
            outside = Path(outside_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            raw_path = root / manifest["raw_output_path"]
            outside_raw = outside / raw_path.name
            shutil.copy2(raw_path, outside_raw)
            raw_path.unlink()
            raw_path.symlink_to(outside_raw)

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("symlink files are not allowed", completed.stderr)

    def test_rejects_raw_output_parent_symlink_outside_root(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary_directory,
            tempfile.TemporaryDirectory() as outside_directory,
        ):
            root = Path(temporary_directory)
            outside = Path(outside_directory)
            self.copy_eval_tree(root)
            self.write_phase_manifests(root, "baseline")
            raw_directory = (
                root / "tests/crafting-china-resumes/behavior/baseline"
            )
            outside_raw_directory = outside / "baseline"
            shutil.copytree(raw_directory, outside_raw_directory)
            shutil.rmtree(raw_directory)
            raw_directory.symlink_to(outside_raw_directory, target_is_directory=True)

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("path escapes resolved root", completed.stderr)

    def test_rejects_internal_manifest_phase_directory_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            case_path = (
                root
                / "tests/crafting-china-resumes/behavior/cases/01-course-project.json"
            )
            manifest_path = self.write_phase_manifests(
                root, "baseline", [case_path]
            )[0]
            baseline_directory = manifest_path.parent
            renamed_directory = baseline_directory.with_name("renamed-phase")
            baseline_directory.rename(renamed_directory)
            baseline_directory.symlink_to(
                renamed_directory, target_is_directory=True
            )

            completed = self.run_validator(root)

        self.assert_stable_validation_failure(completed)
        self.assertIn("directory symlinks are not allowed", completed.stderr)

    def test_rejects_cases_directory_symlink_loop_with_stable_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            cases_directory = (
                root / "tests/crafting-china-resumes/behavior/cases"
            )
            shutil.rmtree(cases_directory)
            cases_directory.symlink_to(cases_directory, target_is_directory=True)

            completed = self.run_validator(root)

        self.assert_stable_validation_failure(completed)
        self.assertIn("directory symlinks are not allowed", completed.stderr)

    def test_rejects_absolute_raw_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["raw_output_path"] = str(
                (root / manifest["raw_output_path"]).resolve()
            )
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "raw_output_path must be repository-relative", completed.stderr
        )

    def test_rejects_wrong_case_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["case_sha256"] = "0" * 64
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("case_sha256 mismatch", completed.stderr)

    def test_rejects_incomplete_phase_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            case_path = (
                root
                / "tests/crafting-china-resumes/behavior/cases/01-course-project.json"
            )
            self.write_phase_manifests(root, "baseline", [case_path])

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "baseline manifests must cover all 12 cases", completed.stderr
        )

    def test_rejects_incomplete_case_set(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            (
                root
                / "tests/crafting-china-resumes/behavior/cases/12-complete-delivery.json"
            ).unlink()

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("case files must be exactly the frozen 01..12 set", completed.stderr)

    def test_rejects_non_exact_case_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            case_path = (
                root
                / "tests/crafting-china-resumes/behavior/cases/01-course-project.json"
            )
            case = json.loads(case_path.read_text(encoding="utf-8"))
            case["unexpected"] = True
            case_path.write_text(
                json.dumps(case, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("case keys must be exactly", completed.stderr)

    def test_rejects_invalid_case_behavior_lists(self) -> None:
        invalid_values = {
            "must": [],
            "must_not": [""],
            "hard_fail": [1],
        }
        for field, invalid_value in invalid_values.items():
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    self.copy_eval_tree(root)
                    case_path = (
                        root
                        / "tests/crafting-china-resumes/behavior/cases/01-course-project.json"
                    )
                    case = json.loads(case_path.read_text(encoding="utf-8"))
                    case[field] = invalid_value
                    case_path.write_text(
                        json.dumps(case, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )

                    completed = self.run_validator(root)

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("must be a non-empty string list", completed.stderr)

    def test_rejects_invalid_case_scalar_fields(self) -> None:
        invalid_values = {"category": 1, "prompt": "  "}
        for field, invalid_value in invalid_values.items():
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    self.copy_eval_tree(root)
                    case_path = (
                        root
                        / "tests/crafting-china-resumes/behavior/cases/01-course-project.json"
                    )
                    case = json.loads(case_path.read_text(encoding="utf-8"))
                    case[field] = invalid_value
                    case_path.write_text(
                        json.dumps(case, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )

                    completed = self.run_validator(root)

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(f"{field} must be a non-empty string", completed.stderr)

    def test_rejects_non_exact_manifest_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["unexpected"] = True
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("manifest keys must be exactly", completed.stderr)

    def test_rejects_manifest_filename_case_id_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest_path.rename(manifest_path.with_name("wrong-name.json"))

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("manifest filename/case_id mismatch", completed.stderr)

    def test_rejects_parent_traversal_raw_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["raw_output_path"] = (
                "tests/crafting-china-resumes/behavior/baseline/../baseline/"
                "01-course-project.md"
            )
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("raw_output_path must not contain '..'", completed.stderr)

    def test_rejects_missing_raw_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            (root / manifest["raw_output_path"]).unlink()

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("raw_output_path does not exist", completed.stderr)

    def test_rejects_non_string_raw_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["raw_output_path"] = None
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("raw_output_path must be a non-empty string", completed.stderr)

    def test_rejects_manifest_phase_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["phase"] = "candidate"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("manifest phase does not match directory", completed.stderr)

    def test_rejects_baseline_skill_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["skill_commit"] = "a" * 40
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("baseline skill_commit must be null", completed.stderr)

    def test_rejects_invalid_candidate_skill_commit(self) -> None:
        invalid_commits = (None, "a" * 39, "A" * 40, "g" * 40)
        for invalid_commit in invalid_commits:
            with self.subTest(skill_commit=invalid_commit):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    self.copy_eval_tree(root)
                    manifest_path = self.write_phase_manifests(root, "candidate")[0]
                    manifest = json.loads(
                        manifest_path.read_text(encoding="utf-8")
                    )
                    manifest["skill_commit"] = invalid_commit
                    manifest_path.write_text(
                        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )

                    completed = self.run_validator(root)

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(
                    "candidate skill_commit must be 40 lowercase hex characters",
                    completed.stderr,
                )

    def test_rejects_invalid_manifest_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["result"] = "maybe"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("result must be pass or fail", completed.stderr)

    def test_rejects_empty_manifest_metadata_strings(self) -> None:
        invalid_values = {
            "model": "",
            "environment": "   ",
            "judge_reason": 1,
        }
        for field, invalid_value in invalid_values.items():
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    self.copy_eval_tree(root)
                    manifest_path = self.write_phase_manifests(root, "baseline")[0]
                    manifest = json.loads(
                        manifest_path.read_text(encoding="utf-8")
                    )
                    manifest[field] = invalid_value
                    manifest_path.write_text(
                        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )

                    completed = self.run_validator(root)

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(f"{field} must be a non-empty string", completed.stderr)

    def test_rejects_non_string_manifest_result_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["result"] = ["pass"]
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("result must be pass or fail", completed.stderr)

    def test_rejects_non_object_manifest_assessments(self) -> None:
        for field in ("qualification_gates", "scores"):
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    self.copy_eval_tree(root)
                    manifest_path = self.write_phase_manifests(root, "baseline")[0]
                    manifest = json.loads(
                        manifest_path.read_text(encoding="utf-8")
                    )
                    manifest[field] = []
                    manifest_path.write_text(
                        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )

                    completed = self.run_validator(root)

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(f"{field} must be an object", completed.stderr)

    def test_rejects_non_exact_qualification_gate_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["qualification_gates"]["unexpected"] = "pass"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "qualification_gates keys must be exactly", completed.stderr
        )

    def test_rejects_non_exact_score_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["scores"]["unexpected"] = 4
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("scores keys must be exactly", completed.stderr)

    def test_rejects_invalid_qualification_gate_values(self) -> None:
        invalid_values = (True, "PASS", None)
        for invalid_value in invalid_values:
            with self.subTest(value=invalid_value):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    self.copy_eval_tree(root)
                    manifest_path = self.write_phase_manifests(
                        root, "baseline"
                    )[0]
                    manifest = json.loads(
                        manifest_path.read_text(encoding="utf-8")
                    )
                    manifest["qualification_gates"][
                        "unconfirmed_fact"
                    ] = invalid_value
                    manifest_path.write_text(
                        json.dumps(
                            manifest, ensure_ascii=False, indent=2
                        )
                        + "\n",
                        encoding="utf-8",
                    )

                    completed = self.run_validator(root)

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(
                    "qualification_gates values must be pass, fail, or N/A",
                    completed.stderr,
                )

    def test_rejects_invalid_score_values(self) -> None:
        invalid_values = (True, 2.5, -1, 5, "3", "NA")
        for invalid_value in invalid_values:
            with self.subTest(value=invalid_value):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    self.copy_eval_tree(root)
                    manifest_path = self.write_phase_manifests(
                        root, "baseline"
                    )[0]
                    manifest = json.loads(
                        manifest_path.read_text(encoding="utf-8")
                    )
                    manifest["scores"][
                        "evidence_discipline"
                    ] = invalid_value
                    manifest_path.write_text(
                        json.dumps(
                            manifest, ensure_ascii=False, indent=2
                        )
                        + "\n",
                        encoding="utf-8",
                    )

                    completed = self.run_validator(root)

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(
                    "scores values must be integer 0..4 or N/A",
                    completed.stderr,
                )

    def test_rejects_pass_result_when_a_gate_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["qualification_gates"]["unconfirmed_fact"] = "fail"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "result must be fail when a qualification gate fails",
            completed.stderr,
        )

    def test_rejects_pass_result_when_an_applicable_score_is_below_three(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["scores"]["evidence_discipline"] = 2
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "result must be fail when an applicable score is below 3",
            completed.stderr,
        )

    def test_accepts_fail_result_from_an_external_hard_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "baseline")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["result"] = "fail"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout,
            "Validated 12 frozen cases, 12 eval manifests.\n",
        )


if __name__ == "__main__":
    unittest.main()
