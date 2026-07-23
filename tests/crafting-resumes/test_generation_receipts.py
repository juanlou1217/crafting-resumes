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
VALIDATOR = (
    ROOT
    / "tests/crafting-resumes/behavior/"
    "validate_generation_receipts.py"
)
PROTOCOL = "fresh-agent/fork_turns=none/frozen-skill+single-prompt/v1"
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


class GenerationReceiptTests(unittest.TestCase):
    def run_validator(
        self,
        root: Path,
        commit: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(VALIDATOR),
                str(root),
                "--expected-skill-commit",
                commit,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def build_fixture(self, root: Path) -> tuple[str, list[Path]]:
        subprocess.run(
            ["git", "init", "-q", str(root)],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "config", "user.name", "Receipt Test"],
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "config",
                "user.email",
                "receipt@example.invalid",
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "config", "commit.gpgsign", "false"],
            check=True,
        )
        for relative_path in REQUIRED_SKILL_PATHS:
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture Skill\n", encoding="utf-8")
        for config in SUITES.values():
            for case_id in config["ids"]:
                source = ROOT / config["case_root"] / f"{case_id}.json"
                target = root / config["case_root"] / f"{case_id}.json"
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        subprocess.run(
            ["git", "-C", str(root), "add", "."],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "commit", "-q", "-m", "fixture"],
            check=True,
        )
        commit = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        receipt_paths: list[Path] = []
        agent_index = 0
        for suite, config in SUITES.items():
            for case_id in config["ids"]:
                agent_index += 1
                case_relative = config["case_root"] / f"{case_id}.json"
                output_relative = config["output_root"] / f"{case_id}.md"
                case_path = root / case_relative
                output_path = root / output_relative
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(
                    f"synthetic output {suite} {case_id}\n",
                    encoding="utf-8",
                )
                case = json.loads(case_path.read_text(encoding="utf-8"))
                receipt = {
                    "suite": suite,
                    "case_id": case_id,
                    "case_path": case_relative.as_posix(),
                    "case_sha256": hashlib.sha256(
                        case_path.read_bytes()
                    ).hexdigest(),
                    "prompt_sha256": hashlib.sha256(
                        case["prompt"].encode("utf-8")
                    ).hexdigest(),
                    "frozen_skill_commit": commit,
                    "skill_root": "skills/crafting-resumes",
                    "output_path": output_relative.as_posix(),
                    "output_sha256": hashlib.sha256(
                        output_path.read_bytes()
                    ).hexdigest(),
                    "agent_task": (
                        "/root/task5_refresh_behavior/"
                        f"fixture_generator_{agent_index:02d}"
                    ),
                    "generation_protocol": PROTOCOL,
                    "direct_write": True,
                    "verbatim": True,
                }
                receipt_path = (
                    root
                    / "tests/crafting-resumes/behavior/provenance"
                    / suite
                    / f"{case_id}.json"
                )
                receipt_path.parent.mkdir(parents=True, exist_ok=True)
                receipt_path.write_text(
                    json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                receipt_paths.append(receipt_path)
        return commit, receipt_paths

    def assert_failure(
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

    def test_accepts_complete_receipt_set(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            commit, _ = self.build_fixture(root)

            completed = self.run_validator(root, commit)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout,
            f"Validated 16 fresh generation receipts at {commit}.\n",
        )

    def test_rejects_output_changed_after_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            commit, receipts = self.build_fixture(root)
            receipt = json.loads(receipts[0].read_text(encoding="utf-8"))
            (root / receipt["output_path"]).write_text(
                "different output for the same case\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root, commit)

        self.assert_failure(completed, "output_sha256 mismatch")

    def test_rejects_prompt_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            commit, receipts = self.build_fixture(root)
            receipt = json.loads(receipts[0].read_text(encoding="utf-8"))
            receipt["prompt_sha256"] = "0" * 64
            receipts[0].write_text(
                json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root, commit)

        self.assert_failure(completed, "prompt_sha256 mismatch")

    def test_rejects_reused_generator_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            commit, receipts = self.build_fixture(root)
            first = json.loads(receipts[0].read_text(encoding="utf-8"))
            second = json.loads(receipts[1].read_text(encoding="utf-8"))
            second["agent_task"] = first["agent_task"]
            receipts[1].write_text(
                json.dumps(second, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root, commit)

        self.assert_failure(
            completed,
            "agent_task values must be unique",
        )

    def test_rejects_false_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            commit, receipts = self.build_fixture(root)
            receipt = json.loads(receipts[0].read_text(encoding="utf-8"))
            receipt["verbatim"] = False
            receipts[0].write_text(
                json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root, commit)

        self.assert_failure(
            completed,
            "verbatim attestation must be true",
        )

    def test_rejects_missing_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            commit, receipts = self.build_fixture(root)
            receipts[0].unlink()

            completed = self.run_validator(root, commit)

        self.assert_failure(
            completed,
            "focused receipt files must be exactly",
        )

    def test_repository_receipts_bind_current_outputs(self) -> None:
        receipt = json.loads(
            (
                ROOT
                / "tests/crafting-resumes/behavior/provenance/"
                "focused/01-reasonable-language.json"
            ).read_text(encoding="utf-8")
        )
        commit = receipt["frozen_skill_commit"]

        completed = self.run_validator(ROOT, commit)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout,
            f"Validated 16 fresh generation receipts at {commit}.\n",
        )


if __name__ == "__main__":
    unittest.main()
