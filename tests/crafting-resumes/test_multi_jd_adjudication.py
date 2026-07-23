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
    "validate_multi_jd_adjudication.py"
)
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
DISPOSITION_RELATIVE = (
    REGRESSION_ROOT / "06-multi-jd-adjudication.md"
)
JUDGMENT_NAMES = (
    "06-multi-jd-first-judge.json",
    "06-multi-jd-adjudicator-a.json",
    "06-multi-jd-adjudicator-b.json",
)
PROTOCOL = (
    "blind-judge/fork_turns=none/"
    "case+rubric+randomized-output-only/v1"
)
AGGREGATION_RULE = (
    "strict-majority-v1; selected by lowest canonical SHA-256 "
    "among judgments agreeing with the majority"
)
MANIFEST_FIELDS = (
    "qualification_gates",
    "scores",
    "judge_reason",
    "result",
)


def canonical_digest(value: dict[str, object]) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class MultiJdAdjudicationTests(unittest.TestCase):
    def run_validator(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(VALIDATOR), str(root)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def build_fixture(
        self,
        root: Path,
    ) -> tuple[str, str, dict[str, dict[str, object]]]:
        for relative_path in (CASE_RELATIVE, OUTPUT_RELATIVE):
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative_path, target)
        output_sha256 = hashlib.sha256(
            (root / OUTPUT_RELATIVE).read_bytes()
        ).hexdigest()

        judgments: dict[str, dict[str, object]] = {}
        for name in JUDGMENT_NAMES:
            judgment = json.loads(
                (ROOT / REGRESSION_ROOT / name).read_text(
                    encoding="utf-8"
                )
            )
            judgment.update(
                {
                    "anonymous_label": "C8",
                    "output_sha256": output_sha256,
                    "judge_protocol": PROTOCOL,
                }
            )
            target = root / REGRESSION_ROOT / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(judgment, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            judgments[name] = judgment

        pass_judgments = [
            (canonical_digest(value), name, value)
            for name, value in judgments.items()
            if value["result"] == "pass"
        ]
        selected_digest, selected_name, selected = min(pass_judgments)
        manifest = {
            "output_sha256": output_sha256,
            **{
                field: selected[field]
                for field in MANIFEST_FIELDS
            },
        }
        manifest_path = root / MANIFEST_RELATIVE
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        disposition = root / DISPOSITION_RELATIVE
        disposition.write_text(
            "# Adjudication\n\n"
            f"Candidate output SHA-256: `{output_sha256}`.\n\n"
            f"Aggregation rule: `{AGGREGATION_RULE}`.\n\n"
            f"Selected judgment: `{selected_name}` "
            f"(`{selected_digest}`).\n",
            encoding="utf-8",
        )
        return selected_name, selected_digest, judgments

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

    def test_accepts_strict_majority_with_deterministic_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            selected_name, selected_digest, _ = self.build_fixture(root)

            completed = self.run_validator(root)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout,
            "Validated multi-JD strict-majority adjudication: "
            f"pass; selected {selected_name} ({selected_digest}).\n",
        )

    def test_rejects_same_case_record_bound_to_different_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.build_fixture(root)
            path = root / REGRESSION_ROOT / JUDGMENT_NAMES[1]
            judgment = json.loads(path.read_text(encoding="utf-8"))
            judgment["output_sha256"] = hashlib.sha256(
                b"different output for the same frozen case\n"
            ).hexdigest()
            path.write_text(
                json.dumps(judgment, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assert_failure(
            completed,
            "judgment records must bind the exact candidate output",
        )

    def test_rejects_manifest_chosen_by_hand_instead_of_rule(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            selected_name, _, judgments = self.build_fixture(root)
            other_name = next(
                name
                for name in JUDGMENT_NAMES
                if name != selected_name
                and judgments[name]["result"] == "pass"
            )
            other = judgments[other_name]
            manifest_path = root / MANIFEST_RELATIVE
            manifest = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )
            for field in MANIFEST_FIELDS:
                manifest[field] = other[field]
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assert_failure(
            completed,
            "manifest must use deterministic selected judgment",
        )

    def test_repository_adjudication_is_machine_bound(self) -> None:
        completed = self.run_validator(ROOT)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(
            "Validated multi-JD strict-majority adjudication: pass;",
            completed.stdout,
        )


if __name__ == "__main__":
    unittest.main()
