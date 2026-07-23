from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = ROOT / "tests/crafting-resumes/behavior/packaging-cases"
EXPECTED_IDS = {
    "01-reasonable-language",
    "02-high-risk-verbs",
    "03-jd-keyword-gap",
    "04-evidence-backed-keywords",
}
FORBIDDEN_PERSONAL_TOKENS = (
    "private-profile-dir",
    "private-resume-dir",
    "private-projects-dir",
    "private-inbox-dir",
    "private-archive-dir",
    "候选人甲",
    "private-account-token",
    "private-user-token",
)


class PackagingCaseTests(unittest.TestCase):
    def test_exact_case_set_and_schema(self) -> None:
        case_paths = sorted(CASES_DIR.glob("*.json"))
        self.assertEqual({path.stem for path in case_paths}, EXPECTED_IDS)

        for case_path in case_paths:
            with self.subTest(case=case_path.name):
                case = json.loads(case_path.read_text(encoding="utf-8"))
                self.assertIsInstance(case, dict)
                self.assertEqual(
                    set(case),
                    {"id", "prompt", "must", "must_not"},
                )
                self.assertEqual(case["id"], case_path.stem)
                self.assertIsInstance(case["prompt"], str)
                self.assertTrue(case["prompt"].strip())
                for key in ("must", "must_not"):
                    self.assertIsInstance(case[key], list)
                    self.assertTrue(case[key])
                    self.assertTrue(
                        all(
                            isinstance(criterion, str) and criterion.strip()
                            for criterion in case[key]
                        )
                    )

    def test_cases_do_not_contain_synthetic_personal_tokens(self) -> None:
        for case_path in sorted(CASES_DIR.glob("*.json")):
            with self.subTest(case=case_path.name):
                text = case_path.read_text(encoding="utf-8")
                for token in FORBIDDEN_PERSONAL_TOKENS:
                    self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
