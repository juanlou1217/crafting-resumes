from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NOTICE = ROOT / "skills/crafting-resumes/THIRD_PARTY_NOTICES.md"

RESUME_REPOSITORY = "https://github.com/coinluu/resume-jd-optimizer-cn"
RESUME_COMMIT = "114c85c32dc77bc9ec7315976a21a1f761868664"
RESUME_FILES = (
    "SKILL.md",
    "docs/workflow.md",
    "docs/resume_truthfulness_policy.md",
    "prompts/experience_interviewer.md",
    "docs/metric_dictionary.md",
    "docs/chinese_job_market_context.md",
    "docs/role_taxonomy.md",
    "prompts/resume_rewriter.md",
    "prompts/hr_reviewer.md",
    "rubrics/ats_score.md",
    "rubrics/credibility_score.md",
    "rubrics/hr_score.md",
    "rubrics/interview_readiness_score.md",
    "rubrics/jd_match_score.md",
    "templates/ats_plain_text_resume_template.md",
    "templates/boss_intro_template.md",
    "templates/headhunter_intro_template.md",
    "templates/interview_story_template.md",
    "templates/jd_match_report_template.md",
    "templates/optimized_resume_template.md",
)

EASY_JOB_TUTOR_REPOSITORY = "https://github.com/yicLionel/Easy-Job-Tutor"
EASY_JOB_TUTOR_COMMIT = "8b628a2865144383fd955236c16f62e686a7b0d5"
EASY_JOB_TUTOR_FILES = (
    "scripts/verify_resume_pdf.py",
    "design/resume-design-principles.md",
    "design/resume-layout-spec.md",
)

MIT_BODY = """Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

RESUME_LICENSE = f"""MIT License

Copyright (c) 2026 coinluu

{MIT_BODY}"""
RESUME_COPYRIGHT = "Copyright (c) 2026 coinluu"

EASY_JOB_TUTOR_LICENSE = f"""MIT License

Copyright (c) 2026 Easy-Job-Tutor contributors

{MIT_BODY}"""
EASY_JOB_TUTOR_COPYRIGHT = "Copyright (c) 2026 Easy-Job-Tutor contributors"


class ThirdPartyNoticesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.notice = NOTICE.read_text(encoding="utf-8")

    def extract_section(
        self,
        notice: str,
        start_heading: str,
        end_heading: str | None,
    ) -> str:
        end_pattern = (
            rf"^{re.escape(end_heading)}$" if end_heading is not None else r"\Z"
        )
        match = re.search(
            rf"^{re.escape(start_heading)}\n(?P<body>.*?){end_pattern}",
            notice,
            flags=re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(match, f"missing section: {start_heading}")
        assert match is not None
        return match.group("body")

    def assert_adapted_section(
        self,
        section: str,
        repository: str,
        commit: str,
        expected_files: tuple[str, ...],
    ) -> None:
        repository_lines = tuple(
            line for line in section.splitlines() if line.startswith("Repository: ")
        )
        commit_lines = tuple(
            line for line in section.splitlines() if line.startswith("Pinned commit: ")
        )
        adapted_file_lines = tuple(
            line for line in section.splitlines() if line.startswith("- ")
        )
        self.assertEqual(repository_lines, (f"Repository: {repository}",))
        self.assertEqual(commit_lines, (f"Pinned commit: {commit}",))
        self.assertEqual(
            adapted_file_lines,
            tuple(f"- `{path}`" for path in expected_files),
        )

    def assert_license_section(
        self,
        section: str,
        copyright_line: str,
        complete_license: str,
    ) -> None:
        copyright_lines = tuple(
            line for line in section.splitlines() if line.startswith("Copyright ")
        )
        license_blocks = tuple(
            re.findall(r"^```text\n(.*?)^```$", section, re.MULTILINE | re.DOTALL)
        )
        self.assertEqual(copyright_lines, (copyright_line,))
        self.assertEqual(license_blocks, (complete_license + "\n",))

    def assert_valid_notice(self, notice: str) -> None:
        resume_adapted = self.extract_section(
            notice,
            "### coinluu/resume-jd-optimizer-cn",
            "### yicLionel/Easy-Job-Tutor",
        )
        easy_job_tutor_adapted = self.extract_section(
            notice,
            "### yicLionel/Easy-Job-Tutor",
            "## Modification summary",
        )
        resume_license = self.extract_section(
            notice,
            "## License for coinluu/resume-jd-optimizer-cn",
            "## License for yicLionel/Easy-Job-Tutor",
        )
        easy_job_tutor_license = self.extract_section(
            notice,
            "## License for yicLionel/Easy-Job-Tutor",
            None,
        )

        self.assert_adapted_section(
            resume_adapted,
            RESUME_REPOSITORY,
            RESUME_COMMIT,
            RESUME_FILES,
        )
        self.assert_adapted_section(
            easy_job_tutor_adapted,
            EASY_JOB_TUTOR_REPOSITORY,
            EASY_JOB_TUTOR_COMMIT,
            EASY_JOB_TUTOR_FILES,
        )
        self.assert_license_section(
            resume_license,
            RESUME_COPYRIGHT,
            RESUME_LICENSE,
        )
        self.assert_license_section(
            easy_job_tutor_license,
            EASY_JOB_TUTOR_COPYRIGHT,
            EASY_JOB_TUTOR_LICENSE,
        )
        self.assertIn("selectively rewritten", notice)
        self.assertIn("native Obsidian", notice)
        self.assertNotIn("build_resume_pdf.py", notice)
        self.assertEqual(notice.count(MIT_BODY), 2)

    @staticmethod
    def swap_values(notice: str, first: str, second: str) -> str:
        sentinel = "__THIRD_PARTY_NOTICE_SWAP_SENTINEL__"
        if sentinel in notice:
            raise ValueError("swap sentinel unexpectedly present in notice")
        return notice.replace(first, sentinel).replace(second, first).replace(
            sentinel, second
        )

    def test_records_exact_sources_modifications_and_full_licenses(self) -> None:
        self.assert_valid_notice(self.notice)

    def test_rejects_values_swapped_between_sources(self) -> None:
        source_value_pairs = (
            (RESUME_REPOSITORY, EASY_JOB_TUTOR_REPOSITORY),
            (RESUME_COMMIT, EASY_JOB_TUTOR_COMMIT),
            (RESUME_COPYRIGHT, EASY_JOB_TUTOR_COPYRIGHT),
            (RESUME_LICENSE, EASY_JOB_TUTOR_LICENSE),
        )
        for first, second in source_value_pairs:
            with self.subTest(first=first.splitlines()[0]):
                mutated_notice = self.swap_values(self.notice, first, second)
                with self.assertRaises(AssertionError):
                    self.assert_valid_notice(mutated_notice)

    def test_rejects_extra_or_differently_formatted_adapted_file_items(self) -> None:
        mutations = (
            ("- `SKILL.md`", "- `SKILL.md`\n- README.md"),
            ("- `SKILL.md`", "- SKILL.md"),
            ("- `SKILL.md`", "- `SKILL.md`\n- `README.md`"),
        )
        for original, replacement in mutations:
            with self.subTest(replacement=replacement):
                mutated_notice = self.notice.replace(original, replacement, 1)
                self.assertNotEqual(mutated_notice, self.notice)
                with self.assertRaises(AssertionError):
                    self.assert_valid_notice(mutated_notice)


if __name__ == "__main__":
    unittest.main()
