from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = (
    ROOT
    / "tests/crafting-resumes/behavior/validate_packaging_eval.py"
)
SOURCE_CASES_DIR = ROOT / "tests/crafting-resumes/behavior/packaging-cases"
CASE_IDS = (
    "01-reasonable-language",
    "02-high-risk-verbs",
    "03-jd-keyword-gap",
    "04-evidence-backed-keywords",
)
REQUIRED_SKILL_PATHS = {
    "skills/crafting-resumes/SKILL.md",
    (
        "skills/crafting-resumes/references/"
        "professional-packaging-and-keywords.md"
    ),
    (
        "skills/crafting-resumes/references/"
        "evidence-and-truthfulness.md"
    ),
}
EXPECTED_COMMIT_FILE = (
    ROOT
    / "tests/crafting-resumes/behavior/packaging-eval/"
    "expected-skill-commit.txt"
)
SIX_FIELD_HEADER = re.compile(
    r"^\|\s*keyword\s*\|\s*source\s*\|\s*candidate_evidence\s*\|"
    r"\s*match_strength\s*\|\s*allowed_surface\s*\|\s*status\s*\|$",
    re.MULTILINE,
)


class PackagingEvalValidatorTests(unittest.TestCase):
    def run_validator(
        self,
        root: Path,
        *arguments: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(VALIDATOR),
                str(root),
                *arguments,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def initialize_fixture(
        self,
        root: Path,
        included_skill_paths: set[str] | None = None,
    ) -> str:
        cases_dir = root / "tests/crafting-resumes/behavior/packaging-cases"
        cases_dir.mkdir(parents=True)
        for case_id in CASE_IDS:
            source = SOURCE_CASES_DIR / f"{case_id}.json"
            (cases_dir / source.name).write_bytes(source.read_bytes())

        subprocess.run(
            ["git", "init", "-q", str(root)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "config", "user.name", "Eval Test"],
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "config",
                "user.email",
                "eval@example.invalid",
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "config", "commit.gpgsign", "false"],
            check=True,
        )
        marker = root / "skill-marker.txt"
        marker.write_text("frozen skill\n", encoding="utf-8")
        selected_skill_paths = (
            REQUIRED_SKILL_PATHS
            if included_skill_paths is None
            else included_skill_paths
        )
        for relative_path in selected_skill_paths:
            skill_path = root / relative_path
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text(
                f"frozen fixture for {relative_path}\n",
                encoding="utf-8",
            )
        subprocess.run(
            ["git", "-C", str(root), "add", "."],
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "commit",
                "-q",
                "-m",
                "test fixture",
            ],
            check=True,
        )
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def write_phase(
        self,
        root: Path,
        phase: str,
        skill_commit: str | None,
    ) -> Path:
        eval_root = (
            root / "tests/crafting-resumes/behavior/packaging-eval"
        )
        output_dir = eval_root / phase
        output_dir.mkdir(parents=True, exist_ok=True)
        results: list[dict[str, object]] = []
        for index, case_id in enumerate(CASE_IDS):
            case_path = (
                root
                / "tests/crafting-resumes/behavior/packaging-cases"
                / f"{case_id}.json"
            )
            case = json.loads(case_path.read_text(encoding="utf-8"))
            output_path = Path(
                "tests/crafting-resumes/behavior/packaging-eval"
            ) / phase / f"{case_id}.md"
            output_bytes = f"{phase} output for {case_id}\n".encode()
            (root / output_path).write_bytes(output_bytes)
            must = [
                {
                    "criterion": criterion,
                    "pass": not (phase == "baseline" and index == 0),
                    "reason": "synthetic focused-eval judgment",
                }
                for criterion in case["must"]
            ]
            must_not = [
                {
                    "criterion": criterion,
                    "pass": True,
                    "reason": "synthetic focused-eval judgment",
                }
                for criterion in case["must_not"]
            ]
            results.append(
                {
                    "id": case_id,
                    "case_sha256": hashlib.sha256(
                        case_path.read_bytes()
                    ).hexdigest(),
                    "output_path": output_path.as_posix(),
                    "output_sha256": hashlib.sha256(
                        output_bytes
                    ).hexdigest(),
                    "must": must,
                    "must_not": must_not,
                    "result": (
                        "fail"
                        if phase == "baseline" and index == 0
                        else "pass"
                    ),
                }
            )
        manifest_path = eval_root / f"{phase}.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "phase": phase,
                    "skill_commit": skill_commit,
                    "cases": results,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return manifest_path

    def assert_validation_failure(
        self,
        completed: subprocess.CompletedProcess[str],
        message: str,
    ) -> None:
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertTrue(
            completed.stderr.startswith("Validation failed:"),
            completed.stderr,
        )
        self.assertIn(message, completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_accepts_valid_baseline_and_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            commit = self.initialize_fixture(root)
            self.write_phase(root, "baseline", None)
            self.write_phase(root, "candidate", commit)

            completed = self.run_validator(
                root,
                "--expected-skill-commit",
                commit,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout,
            "Validated 4 focused packaging cases, 8 phase results.\n",
        )

    def test_accepts_baseline_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.initialize_fixture(root)
            self.write_phase(root, "baseline", None)

            completed = self.run_validator(root, "--phase", "baseline")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout,
            "Validated 4 focused packaging cases, 4 phase results.\n",
        )

    def test_rejects_matching_hash_non_utf8_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.initialize_fixture(root)
            manifest_path = self.write_phase(root, "baseline", None)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            output_path = root / manifest["cases"][0]["output_path"]
            output_bytes = b"\xff\xfe\xfd"
            output_path.write_bytes(output_bytes)
            manifest["cases"][0]["output_sha256"] = hashlib.sha256(
                output_bytes
            ).hexdigest()
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root, "--phase", "baseline")

        self.assert_validation_failure(
            completed,
            "focused output must be valid UTF-8",
        )

    def test_rejects_tampered_output_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.initialize_fixture(root)
            manifest_path = self.write_phase(root, "baseline", None)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            output_path = root / manifest["cases"][0]["output_path"]
            output_path.write_text("tampered\n", encoding="utf-8")

            completed = self.run_validator(root, "--phase", "baseline")

        self.assert_validation_failure(completed, "output_sha256 mismatch")

    def test_rejects_wrong_case_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.initialize_fixture(root)
            manifest_path = self.write_phase(root, "baseline", None)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["cases"][0]["case_sha256"] = "0" * 64
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root, "--phase", "baseline")

        self.assert_validation_failure(completed, "case_sha256 mismatch")

    def test_rejects_expected_commit_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            commit = self.initialize_fixture(root)
            self.write_phase(root, "baseline", None)
            self.write_phase(root, "candidate", commit)

            completed = self.run_validator(
                root,
                "--expected-skill-commit",
                "b" * 40,
            )

        self.assert_validation_failure(
            completed,
            "candidate skill_commit does not match expected commit",
        )

    def test_rejects_commit_missing_each_required_skill_path(self) -> None:
        for missing_path in sorted(REQUIRED_SKILL_PATHS):
            with self.subTest(missing_path=missing_path):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    commit = self.initialize_fixture(
                        root,
                        REQUIRED_SKILL_PATHS - {missing_path},
                    )
                    self.write_phase(root, "baseline", None)
                    self.write_phase(root, "candidate", commit)

                    completed = self.run_validator(
                        root,
                        "--expected-skill-commit",
                        commit,
                    )

                self.assert_validation_failure(
                    completed,
                    (
                        "candidate skill_commit must contain required "
                        f"Skill path: {missing_path}"
                    ),
                )

    def test_rejects_symlink_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.initialize_fixture(root)
            manifest_path = self.write_phase(root, "baseline", None)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            output_path = root / manifest["cases"][0]["output_path"]
            target_path = output_path.with_name("target.md")
            target_path.write_bytes(output_path.read_bytes())
            output_path.unlink()
            output_path.symlink_to(target_path.name)

            completed = self.run_validator(root, "--phase", "baseline")

        self.assert_validation_failure(
            completed,
            "focused output path must not contain symlinks",
        )

    def read_expected_repository_commit(self) -> str:
        if not EXPECTED_COMMIT_FILE.is_file():
            self.skipTest(
                "focused candidate receipt is added with frozen eval assets"
            )
        expected_commit = EXPECTED_COMMIT_FILE.read_text(
            encoding="utf-8"
        ).strip()
        self.assertRegex(expected_commit, r"\A[0-9a-f]{40}\Z")
        return expected_commit

    def test_repository_integration_smoke(self) -> None:
        expected_commit = self.read_expected_repository_commit()
        candidate_manifest = json.loads(
            (
                ROOT
                / "tests/crafting-resumes/behavior/packaging-eval/"
                "candidate.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            candidate_manifest["skill_commit"],
            expected_commit,
        )

        completed = self.run_validator(
            ROOT,
            "--expected-skill-commit",
            expected_commit,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout,
            "Validated 4 focused packaging cases, 8 phase results.\n",
        )

    def test_repository_keyword_gap_output_has_six_field_map(self) -> None:
        self.read_expected_repository_commit()
        output = (
            ROOT
            / "tests/crafting-resumes/behavior/packaging-eval/candidate/"
            "03-jd-keyword-gap.md"
        ).read_text(encoding="utf-8")

        self.assertRegex(output, SIX_FIELD_HEADER)


if __name__ == "__main__":
    unittest.main()
