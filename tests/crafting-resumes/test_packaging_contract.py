from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_FILE = ROOT / "skills/crafting-resumes/SKILL.md"
REFERENCE_FILE = (
    ROOT
    / "skills/crafting-resumes/references/"
    "professional-packaging-and-keywords.md"
)

EVIDENCE_GATE_ROWS = (
    "| `负责` | 直接承担命名任务或交付物 | `承担`、`参与`、`支持` |",
    "| `推动` | 有推进工作的具体跨人或跨团队动作 | `协调`、`协作`、`跟进` |",
    "| `主导` | 同时具备决策权、协调动作和结果责任 | `负责`、`推动`、`参与` |",
    "| `从 0 到 1` | 新能力且有实质端到端所有权 | `参与搭建`、`负责其中环节` |",
    "| `落地` | 已交付、采用、上线或投入使用 | `完成`、`交付`、`试点` |",
    "| `优化` | 有具体前后变化或明确改善机制 | `改造`、`调整`、`完善` |",
    "| `提升` | 已确认对比、指标定义和个人归因 | 陈述已确认变化，不追加个人因果 |",
    "| `降低` | 已确认对比、指标定义和个人归因 | 陈述已确认变化，不追加个人因果 |",
)


class PackagingContractTests(unittest.TestCase):
    def test_packaging_reference_is_routed_before_mapping_and_writing(self) -> None:
        skill_text = SKILL_FILE.read_text(encoding="utf-8")

        packaging_index = skill_text.index(
            "professional-packaging-and-keywords.md"
        )
        self.assertLess(packaging_index, skill_text.index("jd-mapping.md"))
        self.assertLess(packaging_index, skill_text.index("resume-writing.md"))

    def test_reference_defines_principle_and_allowed_transformations(self) -> None:
        reference_text = REFERENCE_FILE.read_text(encoding="utf-8")

        for expected in (
            "反对事实造假，不反对专业包装",
            "专业压缩",
            "职责澄清",
            "岗位语言翻译",
            "价值框架",
            "关键词对齐",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, reference_text)

    def test_reference_contains_exact_evidence_gate_rows(self) -> None:
        reference_text = REFERENCE_FILE.read_text(encoding="utf-8")

        for row in EVIDENCE_GATE_ROWS:
            with self.subTest(row=row):
                self.assertIn(row, reference_text)

    def test_reference_defines_keyword_map_and_selection_policy(self) -> None:
        reference_text = REFERENCE_FILE.read_text(encoding="utf-8")

        for field in (
            "`keyword`",
            "`source`",
            "`candidate_evidence`",
            "`match_strength`",
            "`allowed_surface`",
            "`status`",
        ):
            with self.subTest(field=field):
                self.assertIn(field, reference_text)
        self.assertIn("禁止关键词堆砌", reference_text)
        self.assertIn("JD 关键词优先", reference_text)


if __name__ == "__main__":
    unittest.main()
