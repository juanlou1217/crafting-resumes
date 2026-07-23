from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CASE_PATH = (
    ROOT / "tests/crafting-resumes/behavior/cases/06-multi-jd.json"
)
OUTPUT_PATH = (
    ROOT / "tests/crafting-resumes/behavior/candidate/06-multi-jd.md"
)
MANIFEST_PATH = (
    ROOT / "tests/crafting-resumes/manifests/candidate/06-multi-jd.json"
)
REGRESSION_ROOT = ROOT / "tests/crafting-resumes/behavior/regressions"
DISPOSITION_PATH = REGRESSION_ROOT / "06-multi-jd-adjudication.md"
JUDGMENT_PATHS = {
    "first": REGRESSION_ROOT / "06-multi-jd-first-judge.json",
    "a": REGRESSION_ROOT / "06-multi-jd-adjudicator-a.json",
    "b": REGRESSION_ROOT / "06-multi-jd-adjudicator-b.json",
}


class MultiJdAdjudicationTests(unittest.TestCase):
    def test_adjudication_is_bound_to_exact_output_and_case(self) -> None:
        case = json.loads(CASE_PATH.read_text(encoding="utf-8"))
        judgments = {
            name: json.loads(path.read_text(encoding="utf-8"))
            for name, path in JUDGMENT_PATHS.items()
        }
        output_sha256 = hashlib.sha256(OUTPUT_PATH.read_bytes()).hexdigest()
        disposition = DISPOSITION_PATH.read_text(encoding="utf-8")

        self.assertIn(f"`{output_sha256}`", disposition)
        for judgment in judgments.values():
            self.assertEqual(judgment["case_id"], case["id"])
            for field in ("must", "must_not", "hard_fail"):
                self.assertEqual(
                    [check["criterion"] for check in judgment[field]],
                    case[field],
                )
                self.assertTrue(
                    all(
                        type(check["pass"]) is bool
                        and check["reason"].strip()
                        for check in judgment[field]
                    )
                )

        self.assertEqual(judgments["first"]["result"], "fail")
        self.assertEqual(judgments["a"]["result"], "pass")
        self.assertEqual(judgments["b"]["result"], "pass")

    def test_candidate_manifest_uses_selected_adjudication(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        selected = json.loads(
            JUDGMENT_PATHS["b"].read_text(encoding="utf-8")
        )
        output_sha256 = hashlib.sha256(OUTPUT_PATH.read_bytes()).hexdigest()

        self.assertEqual(manifest["output_sha256"], output_sha256)
        for field in (
            "qualification_gates",
            "scores",
            "judge_reason",
            "result",
        ):
            with self.subTest(field=field):
                self.assertEqual(manifest[field], selected[field])


if __name__ == "__main__":
    unittest.main()
