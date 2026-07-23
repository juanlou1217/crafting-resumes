from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
EXPECTED_PREFIX = (
    "# Crafting Resumes\n\n"
    "> 把普通经历，变成可信、有说服力、经得住面试追问的求职简历。\n\n"
    "Crafting Resumes 是一个以可核验事实为基础的 Codex Skill。"
    "它不会替你编造一段更漂亮的人生，而是通过逐问访谈、证据台账、"
    "岗位价值翻译和 JD 关键词映射，把真实经历中尚未表达出来的价值写清楚。\n\n"
)
EXPECTED_H2 = (
    "## 它解决什么问题",
    "## 核心能力",
    "## 为什么它不只是“润色”",
    "## 快速开始",
    "## 典型工作流",
    "## 输出内容",
    "## 合理包装与真实性边界",
    "## 高价值关键词如何使用",
    "## PDF 交付",
    "## 隐私与权限",
    "## 安装、更新与卸载",
    "## 开发与验证",
    "## FAQ",
    "## License",
)


def assert_in_order(
    test_case: unittest.TestCase,
    text: str,
    expected_fragments: tuple[str, ...],
) -> None:
    cursor = 0
    for fragment in expected_fragments:
        with test_case.subTest(fragment=fragment):
            position = text.find(fragment, cursor)
            test_case.assertNotEqual(
                position,
                -1,
                f"{fragment!r} must appear after the preceding fragment",
            )
            cursor = position + len(fragment)


class ReadmeGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.readme = README.read_text(encoding="utf-8")

    def test_public_guide_has_hero_and_required_section_order(self) -> None:
        self.assertTrue(self.readme.startswith(EXPECTED_PREFIX))
        self.assertEqual(
            tuple(
                line
                for line in self.readme.splitlines()
                if line.startswith("## ")
            ),
            EXPECTED_H2,
        )

    def test_public_identity_uses_only_neutral_invocation_and_repository(self) -> None:
        self.assertIn("$crafting-resumes", self.readme)
        self.assertNotIn("$crafting-china-resumes", self.readme)
        self.assertIn(
            "git@github.com:juanlou1217/crafting-resumes.git",
            self.readme,
        )

    def test_public_packaging_and_keyword_contract_is_documented(self) -> None:
        for expected in (
            "反对事实造假，不反对专业包装",
            "JD 关键词优先",
            "禁止关键词堆砌",
            "| `keyword` | JD 原词优先",
            "| `source` | 关键词来源和候选证据的精确来源",
            "| `candidate_evidence` | 对应的已确认 claim",
            "| `match_strength` | `direct`、`semantic_equivalent`",
            "| `allowed_surface` | 可以出现的简历栏目",
            "| `status` | `include`、`deprioritize`",
            "专业压缩",
            "职责澄清",
            "岗位语言翻译",
            "价值框架",
            "结构优化",
            "关键词对齐",
            "| `负责` | 直接承担清晰模块或交付物",
            "| `推动` | 在负责基础上",
            (
                "| `主导` | 在推动基础上，承担主要目标，并拥有关键决策权、"
                "推进节奏和结果责任 | `负责`、`推动`、`参与` |"
            ),
            "| `从 0 到 1` | 确为新能力",
            "| `落地` | 已确认交付",
            "| `优化` | 有明确改善机制",
            "| `提升` / `降低` | 有指标定义",
            "layout_preview_unverified_content",
            "默认不扫描工作区、主目录、知识库",
            "~/.codex/skills/crafting-resumes",
            "diff -qr",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, self.readme)

    def test_install_examples_are_complete_and_refuse_overwrite(self) -> None:
        for expected in (
            "$skill-installer",
            "git clone git@github.com:juanlou1217/crafting-resumes.git",
            'SKILLS_ROOT="$HOME/.codex/skills"',
            'SKILL_DIR="$SKILLS_ROOT/crafting-resumes"',
            'test ! -e "$SKILL_DIR"',
            'test ! -L "$SKILL_DIR"',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, self.readme)

    def test_uninstall_subsection_has_ordered_destructive_action_guards(self) -> None:
        self.assertIn("### 卸载", self.readme)
        uninstall = self.readme.split("### 卸载", 1)[1].split("\n### ", 1)[0]
        assert_in_order(
            self,
            uninstall,
            (
                "set -euo pipefail",
                'SKILLS_ROOT="$HOME/.codex/skills"',
                'SKILL_DIR="$SKILLS_ROOT/crafting-resumes"',
                'test "$(dirname "$SKILL_DIR")" = "$SKILLS_ROOT"',
                'test "$(basename "$SKILL_DIR")" = "crafting-resumes"',
                'test -d "$SKILL_DIR"',
                'test ! -L "$SKILL_DIR"',
                'rm -rf -- "$SKILL_DIR"',
            ),
        )

    def test_examples_repository_and_license_links_are_present(self) -> None:
        for expected in (
            "### 示例一",
            "### 示例二",
            "https://github.com/juanlou1217/crafting-resumes",
            "[MIT License](LICENSE)",
            "本人对 3 个前端页面及其交互实现的计划、执行与交付负责",
            "记录确认该时间变化来自上述调整",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, self.readme)
        self.assertNotIn("3 个核心前端页面", self.readme)


if __name__ == "__main__":
    unittest.main()
