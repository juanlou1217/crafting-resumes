from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
NEW_SKILL = ROOT / "skills/crafting-resumes"
OLD_SKILL = ROOT / "skills/crafting-china-resumes"


class NeutralIdentityTests(unittest.TestCase):
    def test_only_neutral_skill_directory_is_active(self) -> None:
        self.assertTrue((NEW_SKILL / "SKILL.md").is_file())
        self.assertFalse(OLD_SKILL.exists())

    def test_skill_and_agent_identity_are_neutral(self) -> None:
        skill = (NEW_SKILL / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = yaml.safe_load(skill.split("---", 2)[1])
        agent = yaml.safe_load(
            (NEW_SKILL / "agents/openai.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(frontmatter["name"], "crafting-resumes")
        self.assertIn("# Crafting Resumes", skill)
        self.assertEqual(agent["interface"]["display_name"], "求职简历教练")
        self.assertIn("$crafting-resumes", agent["interface"]["default_prompt"])

    def test_active_public_surfaces_do_not_advertise_old_name(self) -> None:
        paths = (
            ROOT / "README.md",
            ROOT / ".github/workflows/validate.yml",
            NEW_SKILL / "SKILL.md",
            NEW_SKILL / "agents/openai.yaml",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertNotIn(
                    "crafting-china-resumes", path.read_text(encoding="utf-8")
                )


if __name__ == "__main__":
    unittest.main()
