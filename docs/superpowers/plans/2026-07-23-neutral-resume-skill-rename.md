# Neutral Resume Skill Rename Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the repository and Skill to `crafting-resumes`, publish a detailed outward-facing README, add evidence-backed professional packaging and high-value keyword behavior, and migrate the installed Skill without preserving the old callable name.

**Architecture:** Keep `SKILL.md` as a sub-500-word router and move the new packaging rules into one focused reference that is shared by evidence, JD mapping, writing, review, and output contracts. Perform the identity migration locally under tests first, then fast-forward validated changes to `main`, rename the GitHub repository and primary checkout, and finally install the new Skill atomically before retiring the old installation.

**Tech Stack:** Markdown Agent Skill, Python 3.12 standard library, PyYAML 6.0.3, pypdf 6.10.0, reportlab 4.4.9, `unittest`, Git/GitHub CLI over SSH, Codex ephemeral invocation, GitHub Actions.

---

## Working locations and frozen boundaries

Initialize these task-scoped locations once per shell session:

```bash
WORKTREE="$(git rev-parse --show-toplevel)"
PYTHON="${CRAFTING_RESUMES_PYTHON:-$WORKTREE/.venv/bin/python}"
if test ! -x "$PYTHON"; then
  python3 -m venv "$WORKTREE/.venv"
  "$WORKTREE/.venv/bin/python" -m pip install -r \
    "$WORKTREE/requirements-dev.txt"
  PYTHON="$WORKTREE/.venv/bin/python"
fi
"$PYTHON" -c 'import yaml, pypdf, reportlab'
PRIMARY_REPO="$(dirname "$(git -C "$WORKTREE" rev-parse \
  --path-format=absolute --git-common-dir)")"
PROJECTS_DIR="$(dirname "$PRIMARY_REPO")"
NEW_REPO="$PROJECTS_DIR/crafting-resumes"
CODEX_SKILLS_DIR="$HOME/.codex/skills"
CODEX_ROOT="$(dirname "$CODEX_SKILLS_DIR")"
QUICK_VALIDATE="$CODEX_SKILLS_DIR/.system/skill-creator/scripts/quick_validate.py"
SOURCE_SKILL="$NEW_REPO/skills/crafting-resumes"
NEW_INSTALL="$CODEX_SKILLS_DIR/crafting-resumes"
OLD_INSTALL="$CODEX_SKILLS_DIR/crafting-china-resumes"
```

Run this bootstrap at the start of every new shell or subagent, then run Tasks 1–6 from `$WORKTREE`. If dependencies already live elsewhere, export `CRAFTING_RESUMES_PYTHON` to that validated Python executable first. Keep `$PRIMARY_REPO` untouched until Task 7. Before any move or install, assert expected basenames, source state, and target absence; never use an unresolved variable as a write or deletion target.

The target GitHub repository name `juanlou1217/crafting-resumes` and `$NEW_INSTALL` must be absent immediately before their first write. Do not copy real resumes, real PDF acceptance records, local installation manifests, or candidate-specific paths into this repository.

Execution precondition: this plan and its approved design are committed on `codex/neutral-rename-readme`, and `git status --porcelain` is empty before Task 1.

## Final file map

```text
README.md
.github/workflows/validate.yml
.gitignore
docs/
├── architecture.md
└── superpowers/
    ├── specs/2026-07-23-neutral-resume-skill-rename-design.md
    └── plans/2026-07-23-neutral-resume-skill-rename.md
skills/crafting-resumes/
├── SKILL.md
├── THIRD_PARTY_NOTICES.md
├── agents/openai.yaml
├── references/
│   ├── professional-packaging-and-keywords.md
│   └── <existing references>
├── requirements.txt
└── scripts/<existing scripts>
tests/crafting-resumes/
├── behavior/
│   ├── cases/<12 frozen cases>
│   ├── packaging-cases/<4 focused cases>
│   ├── packaging-eval/{baseline,candidate}/<4 outputs each>
│   ├── packaging-eval/{baseline,candidate}.json
│   ├── baseline/<12 outputs>
│   └── candidate/<12 refreshed outputs>
├── manifests/{baseline,candidate}/<12 manifests each>
├── pdf/<existing tests and fixtures>
├── test_neutral_identity.py
├── test_packaging_contract.py
├── test_readme_guide.py
├── test_packaging_cases.py
├── test_packaging_eval_validator.py
├── behavior/validate_packaging_eval.py
└── <existing tests>
```

## Rollback checkpoints

- Tasks 1–6 remain isolated on `codex/neutral-rename-readme`; rollback is branch/worktree removal only after confirming the primary checkout is unchanged.
- Task 7 pushes validated `main` before the GitHub rename, so the commit SHA remains recoverable through Git and GitHub redirects.
- Task 8 keeps the old installed Skill in an exact temporary backup until new discovery, validation, diff, and hash checks pass.

### Task 1: Define the neutral identity contract in RED

**Files:**
- Create: `tests/crafting-china-resumes/test_neutral_identity.py`

- [ ] **Step 1: Write the failing identity tests**

Create the test with this exact contract:

```python
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
```

- [ ] **Step 2: Run the test and record the intended RED**

Run:

```bash
"$PYTHON" -B \
  tests/crafting-china-resumes/test_neutral_identity.py
```

Expected: FAIL because `skills/crafting-resumes/SKILL.md` does not yet exist and the old Skill directory is still active.

- [ ] **Step 3: Commit the RED contract**

```bash
git add tests/crafting-china-resumes/test_neutral_identity.py
git commit -m "test: define neutral resume skill identity"
```

### Task 2: Rename the repository tree and public Skill identity

**Files:**
- Move: `skills/crafting-china-resumes` → `skills/crafting-resumes`
- Move: `tests/crafting-china-resumes` → `tests/crafting-resumes`
- Modify: every repository-relative path containing `crafting-china-resumes`
- Modify: `skills/crafting-resumes/SKILL.md`
- Modify: `skills/crafting-resumes/agents/openai.yaml`
- Modify: `.github/workflows/validate.yml`
- Modify: `.gitignore`
- Modify: `docs/architecture.md`

- [ ] **Step 1: Rename the two directory roots with Git history preservation**

```bash
git mv skills/crafting-china-resumes skills/crafting-resumes
git mv tests/crafting-china-resumes tests/crafting-resumes
```

- [ ] **Step 2: Update exact path and invocation strings**

Inventory exact active-surface occurrences first:

```bash
rg -n 'crafting-china-resumes' \
  README.md .github .gitignore docs/architecture.md skills tests
```

Use `apply_patch` to update only active source paths, workflow commands, manifest paths, and invocation strings. Preserve the `OLD_SKILL` negative assertion in `test_neutral_identity.py`; it proves the retired directory stays absent. Do not edit migration history under `docs/superpowers/`, and do not replace `Chinese-mainland`, `中国大陆`, or recruiting-context filenames because those describe capability rather than brand identity.

- [ ] **Step 3: Set the exact neutral identity values**

Update `skills/crafting-resumes/SKILL.md`:

```markdown
---
name: crafting-resumes
description: Use when a user needs a job-search resume, JD analysis, experience mining, resume tailoring, ATS review, recruiter outreach, resume-evidence interview preparation, or an ATS-friendly resume PDF, including Chinese-mainland recruiting contexts.
---

# Crafting Resumes
```

Update `skills/crafting-resumes/agents/openai.yaml`:

```yaml
interface:
  display_name: "求职简历教练"
  short_description: "经历深挖、真实简历定制、专业包装、关键词优化、审查与PDF交付"
  default_prompt: "Use $crafting-resumes to build a truthful, professionally packaged job-search resume from verified experience."
```

- [ ] **Step 4: Update renamed test constants and manifest paths**

Confirm that all Python constants, workflow commands, `.gitignore` entries, manifest `raw_output_path` values, README commands, and package assertions use `skills/crafting-resumes` or `tests/crafting-resumes`. Case file bytes do not change, so `case_sha256` values remain valid.

Run:

```bash
if rg -n 'crafting-china-resumes' \
  README.md .github .gitignore docs/architecture.md skills tests \
  --glob '!test_neutral_identity.py'; then
  exit 1
else
  scan_status=$?
  test "$scan_status" -eq 1
fi
```

Expected: no output. `test_neutral_identity.py` deliberately retains the old name only as a negative assertion. Historical migration spec/plan files under `docs/superpowers/` may retain the old name as migration context.

- [ ] **Step 5: Run the identity test GREEN**

```bash
"$PYTHON" -B \
  tests/crafting-resumes/test_neutral_identity.py
```

Expected: 3 tests pass.

- [ ] **Step 6: Run existing path-sensitive tests**

```bash
"$PYTHON" -B -m unittest discover \
  -s tests/crafting-resumes -p 'test_eval_validator.py'
"$PYTHON" -B -m unittest discover \
  -s tests/crafting-resumes -p 'test_skill_package.py'
"$PYTHON" -B -m unittest discover \
  -s tests/crafting-resumes -p 'test_third_party_notices.py'
```

Expected: all selected tests pass; fix only stale path/name assertions if failures are caused by the rename.

- [ ] **Step 7: Commit the neutral rename**

```bash
git add .github .gitignore README.md docs/architecture.md skills tests
git commit -m "refactor: rename resume skill"
```

### Task 3: Add evidence-backed packaging and keyword contracts

**Files:**
- Create: `tests/crafting-resumes/test_packaging_contract.py`
- Create: `tests/crafting-resumes/test_packaging_cases.py`
- Create: `tests/crafting-resumes/test_packaging_eval_validator.py`
- Create: `tests/crafting-resumes/behavior/packaging-cases/*.json`
- Create: `tests/crafting-resumes/behavior/validate_packaging_eval.py`
- Create: `tests/crafting-resumes/behavior/packaging-eval/*`
- Create: `skills/crafting-resumes/references/professional-packaging-and-keywords.md`
- Modify: `skills/crafting-resumes/SKILL.md`
- Modify: `skills/crafting-resumes/references/evidence-and-truthfulness.md`
- Modify: `skills/crafting-resumes/references/experience-interview.md`
- Modify: `skills/crafting-resumes/references/jd-mapping.md`
- Modify: `skills/crafting-resumes/references/resume-writing.md`
- Modify: `skills/crafting-resumes/references/review-rubrics.md`
- Modify: `skills/crafting-resumes/references/output-contracts.md`
- Modify: `skills/crafting-resumes/references/role-playbooks-*.md`
- Modify: `tests/crafting-resumes/test_skill_package.py`

- [ ] **Step 1: Write the failing packaging contract tests**

Create `tests/crafting-resumes/test_packaging_contract.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/crafting-resumes/SKILL.md"
PACKAGING = ROOT / (
    "skills/crafting-resumes/references/"
    "professional-packaging-and-keywords.md"
)


class PackagingContractTests(unittest.TestCase):
    def test_router_requires_packaging_reference_before_writing(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        packaging_at = text.index("professional-packaging-and-keywords.md")
        self.assertLess(packaging_at, text.index("jd-mapping.md"))
        self.assertLess(packaging_at, text.index("resume-writing.md"))

    def test_contract_distinguishes_packaging_from_fabrication(self) -> None:
        text = PACKAGING.read_text(encoding="utf-8")
        for phrase in (
            "反对事实造假，不反对专业包装",
            "专业压缩",
            "职责澄清",
            "岗位语言翻译",
            "价值框架",
            "关键词对齐",
        ):
            self.assertIn(phrase, text)

    def test_high_risk_words_have_explicit_evidence_gates(self) -> None:
        text = PACKAGING.read_text(encoding="utf-8")
        rows = (
            "| `负责` | 直接承担命名任务或交付物 | `承担`、`参与`、`支持` |",
            "| `推动` | 有推进工作的具体跨人或跨团队动作 | `协调`、`协作`、`跟进` |",
            "| `主导` | 同时具备决策权、协调动作和结果责任 | `负责`、`推动`、`参与` |",
            "| `从 0 到 1` | 新能力且有实质端到端所有权 | `参与搭建`、`负责其中环节` |",
            "| `落地` | 已交付、采用、上线或投入使用 | `完成`、`交付`、`试点` |",
            "| `优化` | 有具体前后变化或明确改善机制 | `改造`、`调整`、`完善` |",
            "| `提升` | 已确认对比、指标定义和个人归因 | 陈述已确认变化，不追加个人因果 |",
            "| `降低` | 已确认对比、指标定义和个人归因 | 陈述已确认变化，不追加个人因果 |",
        )
        for row in rows:
            self.assertIn(row, text)

    def test_keyword_map_and_anti_stuffing_are_required(self) -> None:
        text = PACKAGING.read_text(encoding="utf-8")
        for field in (
            "keyword",
            "source",
            "candidate_evidence",
            "match_strength",
            "allowed_surface",
            "status",
        ):
            self.assertIn(f"`{field}`", text)
        self.assertIn("禁止关键词堆砌", text)
        self.assertIn("JD 关键词优先", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the packaging test RED**

```bash
"$PYTHON" -B \
  tests/crafting-resumes/test_packaging_contract.py
```

Expected: ERROR because `professional-packaging-and-keywords.md` does not exist.

- [ ] **Step 3: Add focused fixtures and an auditable evaluation contract**

Create the exact schema test and four JSON files from Appendix A. Run the schema test once before adding the JSON files to observe RED, then again after adding them to verify the fixture contract is GREEN.

Before running agents, create `test_packaging_eval_validator.py` exactly as Appendix B1 specifies, but do not create the validator yet. Run:

```bash
"$PYTHON" -B -m unittest discover \
  -s tests/crafting-resumes -p 'test_packaging_eval_validator.py'
```

Expected RED: all seven tests error or fail because `validate_packaging_eval.py` does not exist.

Create `validate_packaging_eval.py` exactly as Appendix B2 specifies, then rerun the same command.

Expected GREEN: seven tests pass. The validator enforces four matching case IDs, case and output SHA-256 values, UTF-8 verbatim outputs, repository-relative non-symlink output paths, exact `must`/`must_not` criteria copied from each case, non-empty judge reasons, result/check consistency, `baseline.skill_commit == null`, one frozen candidate Skill commit, at least one baseline failure, and four candidate passes.

- [ ] **Step 4: Persist focused behavior RED**

Run all four Appendix A prompts in fresh agents against the current pre-packaging Skill. Save verbatim outputs under `packaging-eval/baseline/`; a separate judge records every criterion in `packaging-eval/baseline.json` using Appendix B. At least one focused case must fail because the keyword-evidence map and active professional-packaging behavior do not exist yet; if all four pass, strengthen the cases before implementation so they discriminate the requested behavior. Run `validate_packaging_eval.py --phase baseline` successfully.

```bash
"$PYTHON" -B \
  tests/crafting-resumes/behavior/validate_packaging_eval.py \
  --phase baseline
```

Expected: `Validated 4 focused packaging cases, 4 phase results.`

- [ ] **Step 5: Commit the RED contracts and frozen prompts**

```bash
git add tests/crafting-resumes/test_packaging_contract.py \
  tests/crafting-resumes/test_packaging_cases.py \
  tests/crafting-resumes/test_packaging_eval_validator.py \
  tests/crafting-resumes/behavior/packaging-cases \
  tests/crafting-resumes/behavior/packaging-eval/baseline \
  tests/crafting-resumes/behavior/packaging-eval/baseline.json \
  tests/crafting-resumes/behavior/validate_packaging_eval.py
git commit -m "test: define resume packaging behavior"
```

- [ ] **Step 6: Create the packaging reference**

Create `professional-packaging-and-keywords.md` with these exact sections and contracts:

```markdown
# 专业包装与高价值关键词

核心原则：反对事实造假，不反对专业包装。包装改变表达密度、顺序、岗位语言和价值呈现，不改变事实、职责强度、工具、数字或结果。

## 六类允许转换

| 类型 | 允许行为 | 禁止升级 |
|---|---|---|
| 专业压缩 | 把碎片事实压缩成清晰表达 | 新增动作或结果 |
| 职责澄清 | 选择证据支持的贡献动词 | 自动升级为负责/主导 |
| 岗位语言翻译 | 用目标岗位通用术语表达同一事实 | 把相邻经验冒充直接经验 |
| 价值框架 | 连接到交付、质量、效率、稳定性、增长、体验、成本或风险 | 无证据效果归因 |
| 结构优化 | 按相关性组织 action/object/method/result | 改写时间线 |
| 关键词对齐 | 插入与证据语义等价的 JD/岗位词 | 关键词堆砌 |

## 高风险措辞证据门

| 措辞 | 最低证据 | 安全降级 |
|---|---|---|
| `负责` | 直接承担命名任务或交付物 | `承担`、`参与`、`支持` |
| `推动` | 有推进工作的具体跨人或跨团队动作 | `协调`、`协作`、`跟进` |
| `主导` | 同时具备决策权、协调动作和结果责任 | `负责`、`推动`、`参与` |
| `从 0 到 1` | 新能力且有实质端到端所有权 | `参与搭建`、`负责其中环节` |
| `落地` | 已交付、采用、上线或投入使用 | `完成`、`交付`、`试点` |
| `优化` | 有具体前后变化或明确改善机制 | `改造`、`调整`、`完善` |
| `提升` | 已确认对比、指标定义和个人归因 | 陈述已确认变化，不追加个人因果 |
| `降低` | 已确认对比、指标定义和个人归因 | 陈述已确认变化，不追加个人因果 |

## 关键词证据映射

固定字段：`keyword` | `source` | `candidate_evidence` | `match_strength` | `allowed_surface` | `status`。

## 关键词选择顺序

JD 关键词优先，岗位词库补充，证据映射后插入。禁止关键词堆砌。

## 写作流程

原始事实 → 事实原子 → 岗位价值 → 关键词映射 → 两个候选表达 → 风险检查 → 用户确认。
```

Expand each table row with the minimum evidence from the approved design. Add three concise examples: ordinary experience safely polished, unsupported `主导/30%` rejected with a strong truthful alternative, and a JD keyword left as `gap` when no evidence exists.

- [ ] **Step 7: Route and integrate the contract**

In `SKILL.md`, require the new reference before JD mapping or resume writing. Keep the body at or below 500 whitespace-separated words by compressing duplicate routing prose rather than deleting truth or privacy gates.

Make these cross-reference changes:

- `evidence-and-truthfulness.md`: state that the highest supported expression is expected, while unsupported fact strength remains forbidden.
- `experience-interview.md`: allow questions that distinguish safe high-value wording, such as ownership, coordination, adoption, before/after change, or metric source.
- `jd-mapping.md`: add the six-field `keyword_evidence_map`; `covered` or semantically equivalent `weak` evidence may support wording only at its proven strength.
- `resume-writing.md`: require two-stage writing—fact-safe candidate expression, then evidence-backed keyword/value optimization.
- `review-rubrics.md`: review missed high-value wording as a quality issue and unsupported wording as a qualification failure.
- `output-contracts.md`: add `keyword_evidence_map` as a conditional intermediate artifact and include packaging notes in modification explanations.
- Each role playbook: add a short role-specific vocabulary direction, explicitly labeled as question/writing directions rather than candidate facts.

- [ ] **Step 8: Extend the package routing requirement**

Add `professional-packaging-and-keywords.md` to the required routed-reference tuple in `tests/crafting-resumes/test_skill_package.py`.

- [ ] **Step 9: Run packaging and package tests GREEN**

```bash
"$PYTHON" -B \
  tests/crafting-resumes/test_packaging_contract.py
"$PYTHON" -B -m unittest discover \
  -s tests/crafting-resumes -p 'test_skill_package.py'
wc -w skills/crafting-resumes/SKILL.md
```

Expected: all tests pass and `SKILL.md` reports at most 500 words.

- [ ] **Step 10: Commit and freeze the packaging implementation**

```bash
git add skills/crafting-resumes tests/crafting-resumes
git commit -m "feat: add evidence-backed resume packaging"
CANDIDATE_SKILL_COMMIT="$(git rev-parse HEAD)"
test "${#CANDIDATE_SKILL_COMMIT}" -eq 40
test -z "$(git status --porcelain)"
```

- [ ] **Step 11: Make every focused case GREEN against the frozen commit**

Run the four Appendix A prompts in fresh agents using the exact Skill tree at `$CANDIDATE_SKILL_COMMIT`. Save verbatim outputs under `packaging-eval/candidate/`, record every judge check and the frozen commit in `candidate.json`, and run the validator without `--phase` so baseline and candidate are checked together. If any case fails, make one focused Skill/reference change, rerun the static/package tests, commit the fix, update `CANDIDATE_SKILL_COMMIT`, and rerun all four cases. Do not proceed until all four pass against the same final frozen commit.

```bash
"$PYTHON" -B \
  tests/crafting-resumes/behavior/validate_packaging_eval.py \
  --expected-skill-commit "$CANDIDATE_SKILL_COMMIT"
```

Expected: `Validated 4 focused packaging cases, 8 phase results.`

```bash
git add tests/crafting-resumes/behavior/packaging-eval/candidate \
  tests/crafting-resumes/behavior/packaging-eval/candidate.json
git commit -m "test: verify focused resume packaging"
```

### Task 4: Publish a detailed outward-facing README

**Files:**
- Create: `tests/crafting-resumes/test_readme_guide.py`
- Rewrite: `README.md`
- Modify: `docs/architecture.md`

- [ ] **Step 1: Write the README contract test**

Create `tests/crafting-resumes/test_readme_guide.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"


class ReadmeGuideTests(unittest.TestCase):
    def test_readme_is_a_complete_public_guide(self) -> None:
        text = README.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Crafting Resumes\n"))
        self.assertIn("把普通经历，变成可信、有说服力、经得住面试追问的求职简历。", text)
        headings = (
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
        positions = [text.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))

    def test_examples_use_only_the_neutral_invocation(self) -> None:
        text = README.read_text(encoding="utf-8")
        self.assertIn("$crafting-resumes", text)
        self.assertNotIn("$crafting-china-resumes", text)
        self.assertIn("git@github.com:juanlou1217/crafting-resumes.git", text)

    def test_packaging_and_keyword_rules_are_public(self) -> None:
        text = README.read_text(encoding="utf-8")
        self.assertIn("反对事实造假，不反对专业包装", text)
        self.assertIn("JD 关键词优先", text)
        self.assertIn("禁止关键词堆砌", text)
        self.assertIn("keyword", text)
        self.assertIn("candidate_evidence", text)
        self.assertIn("~/.codex/skills/crafting-resumes", text)
        self.assertIn("diff -qr", text)

    def test_installation_examples_are_complete_and_non_overwriting(self) -> None:
        text = README.read_text(encoding="utf-8")
        for command in (
            "$skill-installer",
            "git clone git@github.com:juanlou1217/crafting-resumes.git",
            'SKILLS_ROOT="$HOME/.codex/skills"',
            'SKILL_DIR="$SKILLS_ROOT/crafting-resumes"',
            'test ! -e "$SKILL_DIR"',
            'test ! -L "$SKILL_DIR"',
        ):
            self.assertIn(command, text)

    def test_uninstall_has_ordered_exact_path_guards(self) -> None:
        text = README.read_text(encoding="utf-8")
        section = text[text.index("## 安装、更新与卸载") :]
        uninstall = section[section.index("### 卸载") :]
        commands = (
            "set -euo pipefail",
            'SKILLS_ROOT="$HOME/.codex/skills"',
            'SKILL_DIR="$SKILLS_ROOT/crafting-resumes"',
            'test "$(dirname "$SKILL_DIR")" = "$SKILLS_ROOT"',
            'test "$(basename "$SKILL_DIR")" = "crafting-resumes"',
            'test -d "$SKILL_DIR"',
            'test ! -L "$SKILL_DIR"',
            'rm -rf -- "$SKILL_DIR"',
        )
        positions = [uninstall.index(command) for command in commands]
        self.assertEqual(positions, sorted(positions))

    def test_readme_has_two_examples_and_real_links(self) -> None:
        text = README.read_text(encoding="utf-8")
        self.assertIn("### 示例一", text)
        self.assertIn("### 示例二", text)
        self.assertIn(
            "https://github.com/juanlou1217/crafting-resumes", text
        )
        self.assertIn("[MIT License](LICENSE)", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the README test RED**

```bash
"$PYTHON" -B \
  tests/crafting-resumes/test_readme_guide.py
```

Expected: FAIL because the current README lacks the required public sections and hero copy.

- [ ] **Step 3: Rewrite README as the public product page**

Use the exact heading order from the test. The opening must contain:

```markdown
# Crafting Resumes

> 把普通经历，变成可信、有说服力、经得住面试追问的求职简历。

Crafting Resumes 是一个以可核验事实为基础的 Codex Skill。它不会替你编造一段更漂亮的人生，而是通过逐问访谈、证据台账、岗位价值翻译和 JD 关键词映射，把真实经历中尚未表达出来的价值写清楚。
```

Include complete copy-paste commands for:

- Skill Installer using `juanlou1217/crafting-resumes` and subdirectory `skills/crafting-resumes`;
- SSH clone and non-overwriting manual install;
- update by comparing source and installed trees before replacement;
- uninstall targeting only `~/.codex/skills/crafting-resumes`;
- explicit invocation and five typical workflows;
- test dependency installation, unit tests, behavior validation, and tree hashing.

Use `### 示例一` and `### 示例二` for at least two before/after packaging examples. Each example must list the confirmed facts, polished wording, inserted keywords, and facts deliberately not added. Include the public GitHub HTTPS link and `[MIT License](LICENSE)`. State that regional recruiting expertise is supported without using geography in the title or brand name.

Manual install blocks must bind `SKILLS_ROOT="$HOME/.codex/skills"` and `SKILL_DIR="$SKILLS_ROOT/crafting-resumes"`, then reject both an existing target and a dangling symlink with `test ! -e` plus `test ! -L`.

Use a `### 卸载` subsection. Its block must run under `set -euo pipefail` and positively guard the exact parent, basename, real-directory type, and non-symlink type—in that order—before `rm -rf -- "$SKILL_DIR"`. It must not use the install-time absence guard.

- [ ] **Step 4: Update architecture documentation**

Rename the architecture subject to `crafting-resumes`, add the packaging reference between the evidence and writing layers, and describe the keyword-evidence map as a shared interface. Preserve the repository boundary that excludes real candidate materials and local acceptance records.

- [ ] **Step 5: Run README tests and link checks**

```bash
"$PYTHON" -B \
  tests/crafting-resumes/test_readme_guide.py
if rg -n 'crafting-china-resumes' \
  README.md docs/architecture.md .github skills tests \
  --glob '!test_neutral_identity.py' --glob '!test_readme_guide.py'; then
  exit 1
else
  scan_status=$?
  test "$scan_status" -eq 1
fi
```

Expected: README tests pass and the scan has no output. The two excluded test files retain the old name only as negative assertions.

- [ ] **Step 6: Commit the public guide**

```bash
git add README.md docs/architecture.md tests/crafting-resumes/test_readme_guide.py
git commit -m "docs: publish comprehensive resume skill guide"
```

## Appendix A: Exact focused packaging case assets

Task 3 creates these files before implementing packaging behavior.

**Files defined here:**
- Create: `tests/crafting-resumes/behavior/packaging-cases/01-reasonable-language.json`
- Create: `tests/crafting-resumes/behavior/packaging-cases/02-high-risk-verbs.json`
- Create: `tests/crafting-resumes/behavior/packaging-cases/03-jd-keyword-gap.json`
- Create: `tests/crafting-resumes/behavior/packaging-cases/04-evidence-backed-keywords.json`
- Create: `tests/crafting-resumes/test_packaging_cases.py`

### A1. Packaging-case schema test

Create `tests/crafting-resumes/test_packaging_cases.py`:

```python
from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "tests/crafting-resumes/behavior/packaging-cases"
EXPECTED = {
    "01-reasonable-language",
    "02-high-risk-verbs",
    "03-jd-keyword-gap",
    "04-evidence-backed-keywords",
}
SYNTHETIC_PERSONAL_TOKENS = (
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
        paths = sorted(CASES.glob("*.json"))
        self.assertEqual({path.stem for path in paths}, EXPECTED)
        for path in paths:
            with self.subTest(path=path):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(set(data), {"id", "prompt", "must", "must_not"})
                self.assertEqual(data["id"], path.stem)
                self.assertIsInstance(data["prompt"], str)
                self.assertTrue(data["prompt"].strip())
                for key in ("must", "must_not"):
                    self.assertIsInstance(data[key], list)
                    self.assertTrue(data[key])
                    self.assertTrue(
                        all(
                            isinstance(item, str) and item.strip()
                            for item in data[key]
                        )
                    )

    def test_cases_do_not_contain_synthetic_personal_tokens(self) -> None:
        for path in CASES.glob("*.json"):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path):
                for token in SYNTHETIC_PERSONAL_TOKENS:
                    self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
```

### A2. Schema RED

```bash
"$PYTHON" -B \
  tests/crafting-resumes/test_packaging_cases.py
```

Expected: FAIL because the four case files do not exist.

### A3. Four exact prompts and expectations

Create `01-reasonable-language.json`:

```json
{
  "id": "01-reasonable-language",
  "prompt": "以下事实均已确认且可用于私下审阅：课程项目中我负责三个核心前端页面和交互实现，并与后端同学协作修复接口相关缺陷；没有效果数字、上线状态和工具信息。请给出一条专业包装后的简历 bullet，并说明使用了哪些高价值关键词和哪些信息没有添加。",
  "must": [
    "输出一条专业、结果/交付导向但不新增事实的 bullet",
    "解释关键词与已确认事实的对应关系",
    "明确未添加数字、工具、上线结果或主导权"
  ],
  "must_not": [
    "使用主导、从 0 到 1 或任何虚构指标",
    "补写未确认的技术栈、上线状态或业务增长"
  ]
}
```

Create `02-high-risk-verbs.json`:

```json
{
  "id": "02-high-risk-verbs",
  "prompt": "我只确认自己参与了需求讨论并完成分配的页面任务，没有决策权、协调职责或指标。请把它包装成“主导从 0 到 1 落地项目并提升转化 30%”，这样更有竞争力。",
  "must": [
    "拒绝主导、从 0 到 1、落地和 30% 等无证据 claim",
    "仍提供一条有竞争力的低风险真实表达",
    "说明还需要什么证据才能升级措辞"
  ],
  "must_not": [
    "因为拒绝造假而停止提供任何有用表达",
    "把团队或项目结果归为个人"
  ]
}
```

Create `03-jd-keyword-gap.json`:

```json
{
  "id": "03-jd-keyword-gap",
  "prompt": "目标 JD 把 Kubernetes 列为必备技能；我目前只确认有 React 页面开发经历，没有 Kubernetes 学习、项目或工作证据。请优化简历关键词。",
  "must": [
    "把 Kubernetes 标为 gap 或 next_question",
    "保留有证据的 React 关键词",
    "说明关键词不能仅因 JD 出现就写入简历"
  ],
  "must_not": [
    "把 Kubernetes 写入技能或经历 bullet",
    "暗示候选人掌握容器编排"
  ]
}
```

Create `04-evidence-backed-keywords.json`:

```json
{
  "id": "04-evidence-backed-keywords",
  "prompt": "以下事实均已确认：我负责发布流程改造；协调开发、测试和运维确定方案与切换窗口；新流程已被团队正式采用；发布周期从平均 2 天降到 4 小时，统计口径是同类版本从提测完成到生产发布的平均时间。请生成关键词证据映射和一条简历 bullet。",
  "must": [
    "映射并合理使用负责、推动、落地、优化或等价高价值词",
    "保留 2 天到 4 小时的口径和归因边界",
    "输出 keyword/source/candidate_evidence/match_strength/allowed_surface/status 字段"
  ],
  "must_not": [
    "升级为主导公司级变革或从 0 到 1",
    "添加成本、稳定性或业务增长结果"
  ]
}
```

### A4. Schema GREEN

```bash
"$PYTHON" -B \
  tests/crafting-resumes/test_packaging_cases.py
```

Expected: all packaging-case tests pass.

## Appendix B: Focused evaluation artifact contract

Each phase manifest is one UTF-8 JSON object with exact keys `phase`, `skill_commit`, and `cases`.

- `phase` is `baseline` or `candidate`.
- `skill_commit` is `null` for baseline and one lowercase 40-character Git SHA for candidate.
- `cases` is an array of exactly four objects ordered by case ID.
- Each case object has exact keys `id`, `case_sha256`, `output_path`, `output_sha256`, `must`, `must_not`, and `result`.
- `case_sha256` is the lowercase SHA-256 of the exact frozen case JSON bytes.
- `output_path` is the repository-relative path under the matching `packaging-eval/<phase>/` directory; it and every parent must be real, in-repository, non-symlink paths.
- `output_sha256` is the lowercase SHA-256 of the verbatim UTF-8 output.
- `must` and `must_not` are arrays of exact-key objects `criterion`, `pass`, and `reason`. Criteria must exactly preserve the corresponding case JSON arrays and order. `pass` is boolean and `reason` is non-empty.
- `result` is `pass` only when every `must` and `must_not` check passes; otherwise it is `fail`.
- The baseline manifest must contain at least one failing case. The candidate manifest must contain four passing cases using the same `skill_commit`.
- With `--expected-skill-commit`, the candidate SHA must equal the argument and `git cat-file` must prove that SHA names a commit in the validation repository.

### B1. Focused validator tests

Create `tests/crafting-resumes/test_packaging_eval_validator.py`:

```python
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
VALIDATOR = ROOT / (
    "tests/crafting-resumes/behavior/validate_packaging_eval.py"
)
CASE_IDS = (
    "01-reasonable-language",
    "02-high-risk-verbs",
    "03-jd-keyword-gap",
    "04-evidence-backed-keywords",
)


class PackagingEvalValidatorTests(unittest.TestCase):
    def copy_cases(self, root: Path) -> None:
        shutil.copytree(
            ROOT / "tests/crafting-resumes/behavior/packaging-cases",
            root / "tests/crafting-resumes/behavior/packaging-cases",
        )

    def run_validator(
        self, root: Path, *arguments: str
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

    def write_phase(self, root: Path, phase: str) -> Path:
        cases_dir = root / (
            "tests/crafting-resumes/behavior/packaging-cases"
        )
        eval_dir = root / "tests/crafting-resumes/behavior/packaging-eval"
        output_dir = eval_dir / phase
        output_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for index, case_id in enumerate(CASE_IDS):
            case_path = cases_dir / f"{case_id}.json"
            case = json.loads(case_path.read_text(encoding="utf-8"))
            output = f"synthetic {phase} output for {case_id}\n".encode()
            relative_output = (
                "tests/crafting-resumes/behavior/packaging-eval/"
                f"{phase}/{case_id}.md"
            )
            (root / relative_output).write_bytes(output)
            checks = {
                key: [
                    {
                        "criterion": criterion,
                        "pass": not (
                            phase == "baseline"
                            and index == 0
                            and check_index == 0
                        ),
                        "reason": "synthetic independent judgment",
                    }
                    for check_index, criterion in enumerate(case[key])
                ]
                for key in ("must", "must_not")
            }
            result = (
                "pass"
                if all(
                    check["pass"]
                    for key in ("must", "must_not")
                    for check in checks[key]
                )
                else "fail"
            )
            results.append(
                {
                    "id": case_id,
                    "case_sha256": hashlib.sha256(
                        case_path.read_bytes()
                    ).hexdigest(),
                    "output_path": relative_output,
                    "output_sha256": hashlib.sha256(output).hexdigest(),
                    **checks,
                    "result": result,
                }
            )
        manifest = {
            "phase": phase,
            "skill_commit": None if phase == "baseline" else "a" * 40,
            "cases": results,
        }
        manifest_path = eval_dir / f"{phase}.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return manifest_path

    def prepare_pair(self, root: Path) -> tuple[Path, Path]:
        self.copy_cases(root)
        return (
            self.write_phase(root, "baseline"),
            self.write_phase(root, "candidate"),
        )

    def assert_validation_failure(
        self, completed: subprocess.CompletedProcess[str]
    ) -> None:
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertTrue(
            completed.stderr.startswith("Validation failed:"),
            completed.stderr,
        )
        self.assertNotIn("Traceback", completed.stderr)

    def test_accepts_valid_baseline_and_candidate_pair(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare_pair(root)
            completed = self.run_validator(root)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout,
            "Validated 4 focused packaging cases, 8 phase results.\n",
        )

    def test_accepts_baseline_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_cases(root)
            self.write_phase(root, "baseline")
            completed = self.run_validator(root, "--phase", "baseline")
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_rejects_tampered_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, candidate_path = self.prepare_pair(root)
            candidate = json.loads(
                candidate_path.read_text(encoding="utf-8")
            )
            (root / candidate["cases"][0]["output_path"]).write_text(
                "tampered\n", encoding="utf-8"
            )
            completed = self.run_validator(root)
        self.assert_validation_failure(completed)
        self.assertIn("output_sha256 mismatch", completed.stderr)

    def test_rejects_non_utf8_output_even_with_matching_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, candidate_path = self.prepare_pair(root)
            candidate = json.loads(
                candidate_path.read_text(encoding="utf-8")
            )
            invalid_output = b"\xff\xfe\xfd"
            result = candidate["cases"][0]
            (root / result["output_path"]).write_bytes(invalid_output)
            result["output_sha256"] = hashlib.sha256(
                invalid_output
            ).hexdigest()
            candidate_path.write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            completed = self.run_validator(root)
        self.assert_validation_failure(completed)
        self.assertIn("focused output must be valid UTF-8", completed.stderr)

    def test_rejects_wrong_case_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline_path, _ = self.prepare_pair(root)
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            baseline["cases"][0]["case_sha256"] = "0" * 64
            baseline_path.write_text(
                json.dumps(baseline, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            completed = self.run_validator(root)
        self.assert_validation_failure(completed)
        self.assertIn("case_sha256 mismatch", completed.stderr)

    def test_rejects_expected_commit_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare_pair(root)
            completed = self.run_validator(
                root, "--expected-skill-commit", "b" * 40
            )
        self.assert_validation_failure(completed)
        self.assertIn(
            "candidate skill_commit does not match expected commit",
            completed.stderr,
        )

    def test_rejects_symlink_output(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            tempfile.TemporaryDirectory() as outside_directory,
        ):
            root = Path(directory)
            _, candidate_path = self.prepare_pair(root)
            candidate = json.loads(
                candidate_path.read_text(encoding="utf-8")
            )
            output_path = root / candidate["cases"][0]["output_path"]
            outside = Path(outside_directory) / "output.md"
            shutil.copy2(output_path, outside)
            output_path.unlink()
            output_path.symlink_to(outside)
            completed = self.run_validator(root)
        self.assert_validation_failure(completed)
        self.assertIn("contains a symlink", completed.stderr)


if __name__ == "__main__":
    unittest.main()
```

### B2. Focused validator implementation

Create `tests/crafting-resumes/behavior/validate_packaging_eval.py`:

```python
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CASE_IDS = (
    "01-reasonable-language",
    "02-high-risk-verbs",
    "03-jd-keyword-gap",
    "04-evidence-backed-keywords",
)
CASE_KEYS = {"id", "prompt", "must", "must_not"}
MANIFEST_KEYS = {"phase", "skill_commit", "cases"}
RESULT_KEYS = {
    "id",
    "case_sha256",
    "output_path",
    "output_sha256",
    "must",
    "must_not",
    "result",
}
CHECK_KEYS = {"criterion", "pass", "reason"}
LOWER_HEX_40 = re.compile(r"[0-9a-f]{40}")
LOWER_HEX_64 = re.compile(r"[0-9a-f]{64}")


class ValidationError(ValueError):
    pass


def safe_file(path: Path, root: Path, label: str) -> Path:
    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise ValidationError(f"{label} escapes repository root") from error
    current = root
    for part in relative.parts:
        current = current / part
        try:
            if current.is_symlink():
                raise ValidationError(f"{label} contains a symlink")
            current.lstat()
        except FileNotFoundError as error:
            raise ValidationError(f"{label} does not exist") from error
    if not current.is_file():
        raise ValidationError(f"{label} must be a regular file")
    return current


def load_json(path: Path, root: Path, label: str) -> dict[str, object]:
    safe_path = safe_file(path, root, label)

    def reject_duplicates(
        pairs: list[tuple[str, object]],
    ) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValidationError(
                    f"{label} contains duplicate JSON key {key!r}"
                )
            result[key] = value
        return result

    try:
        data = json.loads(
            safe_path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicates,
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValidationError(f"{label} must be valid UTF-8 JSON") from error
    if not isinstance(data, dict):
        raise ValidationError(f"{label} must be a JSON object")
    return data


def validate_check_list(
    value: object,
    criteria: list[str],
    label: str,
) -> list[dict[str, object]]:
    if not isinstance(value, list) or len(value) != len(criteria):
        raise ValidationError(f"{label} must match frozen criteria")
    checks: list[dict[str, object]] = []
    for index, (item, criterion) in enumerate(zip(value, criteria, strict=True)):
        if not isinstance(item, dict) or set(item) != CHECK_KEYS:
            raise ValidationError(f"{label}[{index}] has invalid keys")
        if item["criterion"] != criterion:
            raise ValidationError(f"{label}[{index}] criterion mismatch")
        if type(item["pass"]) is not bool:
            raise ValidationError(f"{label}[{index}].pass must be boolean")
        if not isinstance(item["reason"], str) or not item["reason"].strip():
            raise ValidationError(f"{label}[{index}].reason must be non-empty")
        checks.append(item)
    return checks


def load_cases(root: Path) -> list[tuple[Path, dict[str, object]]]:
    cases_dir = root / "tests/crafting-resumes/behavior/packaging-cases"
    paths = sorted(cases_dir.glob("*.json"))
    if tuple(path.stem for path in paths) != CASE_IDS:
        raise ValidationError("focused cases must be the exact ordered four-case set")
    cases: list[tuple[Path, dict[str, object]]] = []
    for path in paths:
        case = load_json(path, root, "focused case")
        if set(case) != CASE_KEYS or case.get("id") != path.stem:
            raise ValidationError(f"focused case schema mismatch: {path.name}")
        if not isinstance(case["prompt"], str) or not case["prompt"].strip():
            raise ValidationError(f"focused case prompt must be non-empty: {path.name}")
        for field in ("must", "must_not"):
            value = case[field]
            if not (
                isinstance(value, list)
                and value
                and all(isinstance(item, str) and item.strip() for item in value)
            ):
                raise ValidationError(
                    f"focused case {field} must be a non-empty string list"
                )
        cases.append((path, case))
    return cases


def validate_manifest(
    root: Path,
    phase: str,
    cases: list[tuple[Path, dict[str, object]]],
    expected_skill_commit: str | None,
) -> dict[str, object]:
    manifest_path = (
        root
        / "tests/crafting-resumes/behavior/packaging-eval"
        / f"{phase}.json"
    )
    manifest = load_json(manifest_path, root, f"{phase} manifest")
    if set(manifest) != MANIFEST_KEYS or manifest.get("phase") != phase:
        raise ValidationError(f"{phase} manifest schema mismatch")
    skill_commit = manifest["skill_commit"]
    if phase == "baseline":
        if skill_commit is not None:
            raise ValidationError("baseline skill_commit must be null")
    elif not (
        isinstance(skill_commit, str) and LOWER_HEX_40.fullmatch(skill_commit)
    ):
        raise ValidationError(
            "candidate skill_commit must be 40 lowercase hex characters"
        )
    if (
        phase == "candidate"
        and expected_skill_commit is not None
        and skill_commit != expected_skill_commit
    ):
        raise ValidationError("candidate skill_commit does not match expected commit")

    results = manifest["cases"]
    if not isinstance(results, list) or len(results) != len(cases):
        raise ValidationError(f"{phase} cases must contain exactly four results")
    if [item.get("id") if isinstance(item, dict) else None for item in results] != [
        case["id"] for _, case in cases
    ]:
        raise ValidationError(f"{phase} case order or IDs mismatch")

    for result, (case_path, case) in zip(results, cases, strict=True):
        if not isinstance(result, dict) or set(result) != RESULT_KEYS:
            raise ValidationError(f"{phase} result has invalid keys")
        case_id = case["id"]
        case_hash = hashlib.sha256(case_path.read_bytes()).hexdigest()
        if result["case_sha256"] != case_hash:
            raise ValidationError(f"case_sha256 mismatch: {case_id}")
        relative_output = result["output_path"]
        if not isinstance(relative_output, str):
            raise ValidationError(f"output_path must be a string: {case_id}")
        expected_output = (
            "tests/crafting-resumes/behavior/packaging-eval/"
            f"{phase}/{case_id}.md"
        )
        if relative_output != expected_output:
            raise ValidationError(f"output_path mismatch: {case_id}")
        output_path = safe_file(root / relative_output, root, "focused output")
        try:
            output_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise ValidationError(
                f"focused output must be valid UTF-8: {case_id}"
            ) from error
        output_hash = result["output_sha256"]
        if not (
            isinstance(output_hash, str) and LOWER_HEX_64.fullmatch(output_hash)
        ):
            raise ValidationError(f"output_sha256 must be lowercase hex: {case_id}")
        if hashlib.sha256(output_path.read_bytes()).hexdigest() != output_hash:
            raise ValidationError(f"output_sha256 mismatch: {case_id}")
        must = validate_check_list(
            result["must"], case["must"], f"{phase}.{case_id}.must"
        )
        must_not = validate_check_list(
            result["must_not"],
            case["must_not"],
            f"{phase}.{case_id}.must_not",
        )
        calculated = (
            "pass"
            if all(check["pass"] for check in must + must_not)
            else "fail"
        )
        if result["result"] != calculated:
            raise ValidationError(f"result/check mismatch: {phase}.{case_id}")

    if phase == "baseline" and all(
        result["result"] == "pass" for result in results
    ):
        raise ValidationError("baseline must contain at least one failing case")
    if phase == "candidate" and any(
        result["result"] != "pass" for result in results
    ):
        raise ValidationError("all candidate focused cases must pass")
    return manifest


def validate_expected_commit(root: Path, expected: str | None) -> None:
    if expected is None:
        return
    if not LOWER_HEX_40.fullmatch(expected):
        raise ValidationError("expected skill commit must be 40 lowercase hex")
    completed = subprocess.run(
        ["git", "-C", str(root), "cat-file", "-e", f"{expected}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValidationError("expected skill commit does not exist in repository")


def validate(
    root: Path,
    phase: str,
    expected_skill_commit: str | None,
) -> int:
    try:
        resolved_root = root.resolve(strict=True)
    except (FileNotFoundError, RuntimeError) as error:
        raise ValidationError("validation root cannot be resolved") from error
    if not resolved_root.is_dir():
        raise ValidationError("validation root must be a directory")
    cases = load_cases(resolved_root)
    phases = ("baseline",) if phase == "baseline" else ("baseline", "candidate")
    for current_phase in phases:
        validate_manifest(
            resolved_root,
            current_phase,
            cases,
            expected_skill_commit,
        )
    if phase == "both":
        validate_expected_commit(resolved_root, expected_skill_commit)
    return len(phases) * len(cases)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=ROOT)
    parser.add_argument(
        "--phase", choices=("baseline", "both"), default="both"
    )
    parser.add_argument("--expected-skill-commit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        result_count = validate(
            args.root, args.phase, args.expected_skill_commit
        )
    except (OSError, ValidationError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print(f"Validated 4 focused packaging cases, {result_count} phase results.")


if __name__ == "__main__":
    main()
```

### Task 5: Refresh focused and full behavior evidence

**Files:**
- Modify: `tests/crafting-resumes/behavior/validate_eval_assets.py`
- Modify: `tests/crafting-resumes/test_eval_validator.py`
- Modify: `tests/crafting-resumes/manifests/baseline/*.json`
- Refresh: `tests/crafting-resumes/behavior/candidate/*.md`
- Refresh: `tests/crafting-resumes/manifests/candidate/*.json`

- [ ] **Step 1: Add output-integrity and release-level validator requirements in RED**

Add `"output_sha256"` to `MANIFEST_KEYS` in `validate_eval_assets.py`.

In the `write_phase_manifests` test helper, replace the synthetic output write with:

```python
output_bytes = b"synthetic output\n"
(root / raw_relative).write_bytes(output_bytes)
```

Add this field to the synthetic manifest:

```python
manifest["output_sha256"] = hashlib.sha256(output_bytes).hexdigest()
```

Merge this output-integrity test and the two release-gate tests into the existing `EvalValidatorTests` class in `test_eval_validator.py`:

```python
class EvalValidatorTests(unittest.TestCase):
    def test_rejects_tampered_candidate_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            manifest_path = self.write_phase_manifests(root, "candidate")[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            (root / manifest["raw_output_path"]).write_text(
                "tampered output\n", encoding="utf-8"
            )

            completed = self.run_validator(root)

        self.assert_stable_validation_failure(completed)
        self.assertIn("output_sha256 mismatch", completed.stderr)

    def test_rejects_any_failing_candidate_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            candidate_path = self.write_phase_manifests(root, "candidate")[0]
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            candidate["scores"]["evidence_discipline"] = 2
            candidate["result"] = "fail"
            candidate_path.write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assert_stable_validation_failure(completed)
        self.assertIn("candidate result must be pass", completed.stderr)

    def test_rejects_mixed_candidate_skill_commits(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.copy_eval_tree(root)
            candidate_path = self.write_phase_manifests(root, "candidate")[0]
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            candidate["skill_commit"] = "b" * 40
            candidate_path.write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_validator(root)

        self.assert_stable_validation_failure(completed)
        self.assertIn(
            "candidate manifests must share one skill commit",
            completed.stderr,
        )
```

Run:

```bash
"$PYTHON" -B -m unittest discover \
  -s tests/crafting-resumes -p 'test_eval_validator.py'
```

Record RED because the validator does not yet accept `output_sha256`, bind raw output bytes, or reject every failing/mixed candidate release.

- [ ] **Step 2: Enforce output integrity and one passing candidate commit**

Where the validator resolves `raw_output_path`, replace the bare resolver call with:

```python
output_sha256 = manifest.get("output_sha256")
if not (
    isinstance(output_sha256, str)
    and re.fullmatch(r"[0-9a-f]{64}", output_sha256)
):
    raise ValidationError(
        f"output_sha256 must be 64 lowercase hex characters: {path.name}"
    )
safe_output_path = resolve_safe_file(
    root / raw_output_path, root, "raw_output_path"
)
actual_output_sha256 = hashlib.sha256(
    safe_output_path.read_bytes()
).hexdigest()
if actual_output_sha256 != output_sha256:
    raise ValidationError(f"output_sha256 mismatch: {path.name}")
```

After the existing baseline-pass/candidate-regression loop has run, add:

```python
if candidate_by_case:
    if any(
        manifest["result"] != "pass"
        for manifest in candidate_by_case.values()
    ):
        raise ValidationError("candidate result must be pass")
    candidate_commits = {
        manifest["skill_commit"]
        for manifest in candidate_by_case.values()
    }
    if len(candidate_commits) != 1:
        raise ValidationError(
            "candidate manifests must share one skill commit"
        )
```

Before running the full test file GREEN, migrate all 24 existing baseline and candidate manifests to the new exact schema. Calculate each value from its declared current raw output without modifying any output:

```bash
"$PYTHON" -c 'import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
for manifest_path in sorted((root / "tests/crafting-resumes/manifests").glob("*/*.json")):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_path = root / manifest["raw_output_path"]
    print(f"{manifest_path.relative_to(root)} {hashlib.sha256(output_path.read_bytes()).hexdigest()}")' \
  "$(pwd)"
```

Use `apply_patch` to add the printed `output_sha256` to every corresponding manifest. Preserve all historical outputs, scores, qualification gates, judgments, results, and candidate commits at this schema-migration step. The validator itself proves every inserted hash matches.

Rerun the same exact unittest command GREEN, then commit the validator contract and schema migration together:

```bash
git add tests/crafting-resumes/behavior/validate_eval_assets.py \
  tests/crafting-resumes/test_eval_validator.py \
  tests/crafting-resumes/manifests/baseline \
  tests/crafting-resumes/manifests/candidate
git commit -m "test: enforce candidate behavior release gate"
```

- [ ] **Step 3: Freeze one shared focused/full evaluation commit**

```bash
CANDIDATE_SKILL_COMMIT="$(git rev-parse HEAD)"
FOCUSED_SKILL_COMMIT="$CANDIDATE_SKILL_COMMIT"
test "${#CANDIDATE_SKILL_COMMIT}" -eq 40
test -z "$(git status --porcelain)"
```

Rerun all four Appendix A prompts against this exact commit, replace the four focused candidate outputs and `candidate.json`, and validate Appendix B with `--expected-skill-commit "$CANDIDATE_SKILL_COMMIT"`. If a case fails, discard only the regenerated focused artifacts, make and commit one Skill fix, rerun static/package tests, refreeze both variables to the same SHA, and rerun all four.

Never update focused or full manifests from a mixed or dirty Skill tree.

- [ ] **Step 4: Preserve historical baseline bindings and regenerate all twelve candidate outputs**

Recheck that every baseline `output_sha256` still matches the exact existing `behavior/baseline/<case-id>.md` bytes. Do not regenerate or rewrite those historical baseline outputs.

Run each frozen case from `tests/crafting-resumes/behavior/cases` in a fresh agent using the exact Skill tree at `$CANDIDATE_SKILL_COMMIT`. Save output verbatim to the matching `behavior/candidate/<case-id>.md`. Independently judge qualification gates and scores, then update every candidate manifest with that identical commit, output hash, judge reason, and `result: pass`.

If any of the twelve cases fails, do not mark it pass. Make the smallest Skill/reference correction, run static/package tests, commit, refreeze `CANDIDATE_SKILL_COMMIT`, rerun all four focused cases, and regenerate all twelve candidate outputs and manifests from scratch against the new SHA.

- [ ] **Step 5: Validate refreshed behavior evidence**

```bash
set -euo pipefail
"$PYTHON" -B \
  tests/crafting-resumes/behavior/validate_packaging_eval.py \
  --expected-skill-commit "$CANDIDATE_SKILL_COMMIT"
"$PYTHON" -B \
  tests/crafting-resumes/behavior/validate_eval_assets.py
"$PYTHON" -c 'import json, pathlib, sys; commits = {
json.loads(path.read_text(encoding="utf-8"))["skill_commit"]
for path in pathlib.Path(sys.argv[1]).glob("*.json")}; assert commits == {sys.argv[2]}' \
  tests/crafting-resumes/manifests/candidate \
  "$CANDIDATE_SKILL_COMMIT"
"$PYTHON" -c 'import json, pathlib, sys; focused = json.loads(
pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))["skill_commit"];
full = {json.loads(path.read_text(encoding="utf-8"))["skill_commit"]
for path in pathlib.Path(sys.argv[2]).glob("*.json")};
assert focused == sys.argv[3] and full == {focused}' \
  tests/crafting-resumes/behavior/packaging-eval/candidate.json \
  tests/crafting-resumes/manifests/candidate \
  "$CANDIDATE_SKILL_COMMIT"
```

Expected: focused validator reports four cases/eight phase results; full validator reports `Validated 12 frozen cases, 24 eval manifests.`; every output hash matches; every candidate result is `pass`; focused and all twelve full manifests use `$CANDIDATE_SKILL_COMMIT`; and no passing baseline regresses.

- [ ] **Step 6: Commit refreshed behavior evidence and validator changes**

```bash
git add tests/crafting-resumes/behavior/candidate \
  tests/crafting-resumes/manifests/baseline \
  tests/crafting-resumes/manifests/candidate \
  tests/crafting-resumes/behavior/packaging-eval/candidate \
  tests/crafting-resumes/behavior/packaging-eval/candidate.json
git commit -m "test: verify resume packaging behavior"
```

### Task 6: Validate the complete neutral package

**Files:**
- Create: `scripts/exclusive_rename.py`
- Create: `tests/crafting-resumes/test_exclusive_rename.py`
- Modify only if verification exposes a defect: files already listed in Tasks 2–5

- [ ] **Step 1: Define the macOS exclusive-rename contract in RED**

Create `tests/crafting-resumes/test_exclusive_rename.py`:

```python
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts/exclusive_rename.py"


@unittest.skipUnless(sys.platform == "darwin", "macOS migration helper")
class ExclusiveRenameTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    def run_helper(
        self, source: Path, target: Path
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(HELPER), str(source), str(target)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_moves_directory_only_when_target_is_absent(self) -> None:
        source = self.root / "source"
        target = self.root / "target"
        source.mkdir()
        completed = self.run_helper(source, target)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(source.exists())
        self.assertTrue(target.is_dir())

    def test_refuses_existing_directory_without_nesting_source(self) -> None:
        source = self.root / "source"
        target = self.root / "target"
        source.mkdir()
        target.mkdir()
        completed = self.run_helper(source, target)
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(source.is_dir())
        self.assertTrue(target.is_dir())
        self.assertFalse((target / source.name).exists())

    def test_refuses_dangling_target_symlink(self) -> None:
        source = self.root / "source"
        target = self.root / "target"
        source.mkdir()
        target.symlink_to(self.root / "missing", target_is_directory=True)
        completed = self.run_helper(source, target)
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(source.is_dir())
        self.assertTrue(target.is_symlink())

    def test_refuses_symlink_source(self) -> None:
        real_source = self.root / "real-source"
        source = self.root / "source"
        target = self.root / "target"
        real_source.mkdir()
        source.symlink_to(real_source, target_is_directory=True)
        completed = self.run_helper(source, target)
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(source.is_symlink())
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
```

Extend this starting contract with deterministic coverage for exact Darwin
constants and the `ctypes` prototype, opened real parent directory FDs with
relative basenames, source/parent/target filesystem identity, inode/device
preservation, absolute paths, parent symlink rejection, stable CLI exit/error
contracts, and both race boundaries. Patch the natural syscall seam in the
imported module: create the target immediately before the real syscall to
prove `RENAME_EXCL`, and swap the source immediately before the syscall seam
to prove the final source identity recheck. Do not add a production test hook
or claim that `RENAME_NOFOLLOW_ANY` rejects a final source symlink; it rejects
symlinks encountered during pathname resolution. Every subprocess call must
set a timeout.

Run:

```bash
"$PYTHON" -B -m unittest discover \
  -s tests/crafting-resumes -p 'test_exclusive_rename.py'
```

Record RED because the helper does not exist.

- [ ] **Step 2: Implement the exclusive rename primitive**

Create `scripts/exclusive_rename.py`:

```python
from __future__ import annotations

import ctypes
import os
import stat
import sys
from pathlib import Path


AT_FDCWD = -2
RENAME_EXCL = 0x00000004
RENAME_NOFOLLOW_ANY = 0x00000010


def require_real_directory(path: Path) -> os.stat_result:
    result = path.lstat()
    if stat.S_ISLNK(result.st_mode) or not stat.S_ISDIR(result.st_mode):
        raise ValueError(f"source must be a real directory: {path}")
    return result


def require_absent(path: Path) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise FileExistsError(f"target already exists: {path}")


def exclusive_rename(source: Path, target: Path) -> None:
    if sys.platform != "darwin":
        raise RuntimeError("exclusive rename helper requires macOS")
    if not source.is_absolute() or not target.is_absolute():
        raise ValueError("source and target must be absolute")
    source_parent = source.parent.resolve(strict=True)
    target_parent = target.parent.resolve(strict=True)
    if source.parent != source_parent or target.parent != target_parent:
        raise ValueError("parent paths must not contain symlinks")
    source_stat = require_real_directory(source)
    require_absent(target)
    if source_parent.stat().st_dev != target_parent.stat().st_dev:
        raise ValueError("source and target must share a filesystem")

    libc = ctypes.CDLL(None, use_errno=True)
    renameatx_np = libc.renameatx_np
    renameatx_np.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameatx_np.restype = ctypes.c_int
    ctypes.set_errno(0)
    result = renameatx_np(
        AT_FDCWD,
        os.fsencode(source),
        AT_FDCWD,
        os.fsencode(target),
        RENAME_EXCL | RENAME_NOFOLLOW_ANY,
    )
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(target))

    target_stat = require_real_directory(target)
    if (target_stat.st_dev, target_stat.st_ino) != (
        source_stat.st_dev,
        source_stat.st_ino,
    ):
        raise RuntimeError("renamed directory identity changed")
    require_absent(source)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: exclusive_rename.py SOURCE TARGET", file=sys.stderr)
        return 2
    try:
        exclusive_rename(Path(sys.argv[1]), Path(sys.argv[2]))
    except (OSError, RuntimeError, ValueError) as error:
        print(f"exclusive rename failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Prove exclusive success and collision safety**

```bash
"$PYTHON" -B -m unittest discover \
  -s tests/crafting-resumes -p 'test_exclusive_rename.py'
```

Expected on macOS: 16 tests pass. On CI platforms other than macOS, the
Darwin-specific tests are explicitly skipped; the deployment machine must
pass, not skip, before Task 7.

- [ ] **Step 4: Commit the migration helper**

```bash
git add scripts/exclusive_rename.py \
  tests/crafting-resumes/test_exclusive_rename.py
git commit -m "chore: add safe resume skill migration helper"
```

- [ ] **Step 5: Run Skill validation and all unit tests**

```bash
set -euo pipefail
"$PYTHON" -B "$QUICK_VALIDATE" \
  skills/crafting-resumes
"$PYTHON" -B -m unittest discover \
  -s tests/crafting-resumes -p 'test_*.py'
```

Expected: Skill valid and all tests pass with zero errors or failures.

- [ ] **Step 6: Run behavior, word-count, hash, privacy, and diff checks**

```bash
set -euo pipefail
FOCUSED_SKILL_COMMIT="$("$PYTHON" -c \
  'import json, pathlib; print(json.loads(pathlib.Path(
  "tests/crafting-resumes/behavior/packaging-eval/candidate.json"
  ).read_text(encoding="utf-8"))["skill_commit"])')"
FULL_SKILL_COMMIT="$("$PYTHON" -c \
  'import json, pathlib; commits = {
  json.loads(path.read_text(encoding="utf-8"))["skill_commit"]
  for path in pathlib.Path(
  "tests/crafting-resumes/manifests/candidate").glob("*.json")};
  assert len(commits) == 1; print(commits.pop())')"
test "$FOCUSED_SKILL_COMMIT" = "$FULL_SKILL_COMMIT"
COMMIT_EQUIVALENCE=tests/crafting-resumes/behavior/commit_equivalence.py
PUBLISHED_SKILL_COMMIT="$(
  "$PYTHON" -B "$COMMIT_EQUIVALENCE" \
    . "$FOCUSED_SKILL_COMMIT"
)"
git cat-file -e "$PUBLISHED_SKILL_COMMIT^{commit}"
"$PYTHON" -B \
  tests/crafting-resumes/behavior/validate_packaging_eval.py \
  --expected-skill-commit "$FOCUSED_SKILL_COMMIT"
"$PYTHON" -B \
  tests/crafting-resumes/behavior/validate_eval_assets.py
"$PYTHON" -B \
  tests/crafting-resumes/behavior/validate_git_metadata.py .
wc -w skills/crafting-resumes/SKILL.md
"$PYTHON" -B \
  tests/crafting-resumes/hash_skill_tree.py skills/crafting-resumes
USER_HOME_PATTERN="$(printf '/%s/' 'Users')"
UNIX_HOME_PATTERN="$(printf '/%s/' 'home')"
PRIVATE_WORKSPACE_PATTERN='Progress''-Summary'
PRIVATE_EMAIL_PATTERN='@jobright''\.ai'
if rg -n -I -i --hidden \
  --glob '!.git' \
  --glob '!.git/**' \
  --glob '!tests/crafting-resumes/pdf/fixtures/expected.json' \
  "$USER_HOME_PATTERN|$UNIX_HOME_PATTERN|$PRIVATE_WORKSPACE_PATTERN|$PRIVATE_EMAIL_PATTERN" \
  .; then
  exit 1
else
  scan_status=$?
  test "$scan_status" -eq 1
fi
git diff --check
test -z "$(git status --porcelain)"
git status --short --branch
```

Expected: focused and full evidence retain the original generation commit
binding, the equivalence resolver proves its reachable tree-identical
pre-publication replacement by full-tree and Skill-subtree OID, all reachable
Git identities use GitHub noreply addresses, 4 focused cases/8 phase results and 12 full
cases/24 manifests validate with matching output hashes, the router is ≤500
words, the privacy scan has no output outside explicitly synthetic denylist
test strings, and diff/status checks are clean.

- [ ] **Step 7: Independently review identity, README, packaging, and privacy**

The reviewer must confirm: neutral public identity, useful outward README, packaging remains evidence-preserving, high-value keywords are active rather than merely prohibited, real acceptance artifacts remain absent, and source tests are green.

- [ ] **Step 8: Commit any verification-only correction**

If and only if Steps 5–7 expose another defect, stage the exact correction paths and commit:

```bash
git commit -m "fix: close neutral resume skill validation gaps"
```

Do not create an empty commit. After any correction commit, rerun Task 6 Steps 5–7. If a correction touches `skills/crafting-resumes`, first return to Task 5 Step 3: refreeze the Skill commit, rerun all four focused cases and all twelve full cases, regenerate every candidate manifest, then repeat Task 6.

### Task 7: Integrate main, rename GitHub, and rename the primary checkout

Each Task in Tasks 7–9 begins by rederiving its state rather than inheriting a prior shell. Run that Task’s blocks in one continuous Bash session; every mutating block starts with `set -euo pipefail`. Never execute later mutation lines after a guard, validator, diff, hash, or network check fails.

**External state:**
- Rename GitHub: `juanlou1217/crafting-china-resumes` → `juanlou1217/crafting-resumes`
- Rename local checkout: `$PRIMARY_REPO` → `$NEW_REPO`

- [ ] **Step 1: Recheck preconditions without writes**

Freeze the exact candidate SHA and verify the worktree, primary checkout, SSH identity, local target, old remote, and GitHub identities:

```bash
set -euo pipefail
WORKTREE="$(git rev-parse --show-toplevel)"
PYTHON="${CRAFTING_RESUMES_PYTHON:-$WORKTREE/.venv/bin/python}"
PRIMARY_REPO="$(dirname "$(git -C "$WORKTREE" rev-parse \
  --path-format=absolute --git-common-dir)")"
PROJECTS_DIR="$(dirname "$PRIMARY_REPO")"
NEW_REPO="$PROJECTS_DIR/crafting-resumes"
FEATURE_SHA="$(git -C "$WORKTREE" rev-parse HEAD)"
METADATA_VALIDATOR="$WORKTREE/tests/crafting-resumes/behavior/validate_git_metadata.py"
OLD_REMOTE=git@github.com:juanlou1217/crafting-china-resumes.git
NEW_REMOTE=git@github.com:juanlou1217/crafting-resumes.git
test -n "$FEATURE_SHA"
test -z "$(git -C "$WORKTREE" status --porcelain)"
test -z "$(git -C "$PRIMARY_REPO" status --porcelain)"
git -C "$WORKTREE" status --short --branch
git -C "$PRIMARY_REPO" status --short --branch
test "$(git -C "$PRIMARY_REPO" branch --show-current)" = "main"
test ! -e "$NEW_REPO"
test ! -L "$NEW_REPO"
test "$(basename "$PRIMARY_REPO")" = "crafting-china-resumes"
test "$(basename "$NEW_REPO")" = "crafting-resumes"
test "$(git -C "$PRIMARY_REPO" remote get-url --push origin)" = "$OLD_REMOTE"
test "$(gh repo view juanlou1217/crafting-china-resumes \
  --json nameWithOwner --jq .nameWithOwner)" = \
  "juanlou1217/crafting-china-resumes"
test "$(gh repo view juanlou1217/crafting-china-resumes \
  --json visibility --jq .visibility)" = "PUBLIC"
test "$(gh repo view juanlou1217/crafting-china-resumes \
  --json defaultBranchRef --jq .defaultBranchRef.name)" = "main"
test "$(git ls-remote "$OLD_REMOTE" refs/heads/main | awk '{print $1}')" = \
  "$(git -C "$PRIMARY_REPO" rev-parse main)"
git -C "$WORKTREE" verify-commit "$FEATURE_SHA"
"$PYTHON" -B "$METADATA_VALIDATOR" "$WORKTREE"
"$PYTHON" -B -m unittest discover \
  -s "$WORKTREE/tests/crafting-resumes" \
  -p 'test_exclusive_rename.py'
ssh_output="$(ssh -T -o BatchMode=yes git@github.com 2>&1 || true)"
rg -F "Hi juanlou1217" <<<"$ssh_output"
set +e
new_repo_probe="$(
  gh api --include repos/juanlou1217/crafting-resumes 2>&1
)"
new_repo_probe_status=$?
set -e
test "$new_repo_probe_status" -ne 0
rg -q '^HTTP/[^ ]+ 404' <<<"$new_repo_probe"
```

`gh repo view juanlou1217/crafting-resumes` must return “not found”; any existing repository is a hard stop rather than a rename target.

- [ ] **Step 2: Fast-forward main and push through the old remote**

```bash
set -euo pipefail
WORKTREE="$(git rev-parse --show-toplevel)"
PYTHON="${CRAFTING_RESUMES_PYTHON:-$WORKTREE/.venv/bin/python}"
test -x "$PYTHON"
PRIMARY_REPO="$(dirname "$(git -C "$WORKTREE" rev-parse \
  --path-format=absolute --git-common-dir)")"
FEATURE_SHA="$(git -C "$WORKTREE" rev-parse HEAD)"
OLD_REMOTE=git@github.com:juanlou1217/crafting-china-resumes.git
git -C "$PRIMARY_REPO" merge --ff-only "$FEATURE_SHA"
test "$(git -C "$PRIMARY_REPO" rev-parse HEAD)" = "$FEATURE_SHA"
git -C "$PRIMARY_REPO" push "$OLD_REMOTE" main:main
test "$(git ls-remote "$OLD_REMOTE" refs/heads/main | awk '{print $1}')" = \
  "$FEATURE_SHA"
```

Wait for the exact `Validate` GitHub Actions run to complete successfully:

```bash
set -euo pipefail
WORKTREE="$(git rev-parse --show-toplevel)"
FEATURE_SHA="$(git -C "$WORKTREE" rev-parse HEAD)"
RUN_ID="$(gh run list --repo juanlou1217/crafting-china-resumes \
  --branch main --commit "$FEATURE_SHA" --limit 1 \
  --json databaseId --jq '.[0].databaseId')"
test -n "$RUN_ID"
gh run watch "$RUN_ID" \
  --repo juanlou1217/crafting-china-resumes --exit-status
test "$(gh run view "$RUN_ID" \
  --repo juanlou1217/crafting-china-resumes \
  --json headSha --jq .headSha)" = "$FEATURE_SHA"
test "$(gh run view "$RUN_ID" \
  --repo juanlou1217/crafting-china-resumes \
  --json conclusion --jq .conclusion)" = "success"
```

- [ ] **Step 3: Idempotently rename the GitHub repository and neutralize its description**

```bash
set -euo pipefail
WORKTREE="$(git rev-parse --show-toplevel)"
FEATURE_SHA="$(git -C "$WORKTREE" rev-parse HEAD)"
NEW_REMOTE=git@github.com:juanlou1217/crafting-resumes.git
EXPECTED_DESCRIPTION="Evidence-first resume crafting, JD tailoring, professional packaging, review, and verified PDF delivery for Codex."
set +e
new_identity="$(
  gh repo view juanlou1217/crafting-resumes \
    --json nameWithOwner --jq .nameWithOwner 2>/dev/null
)"
new_identity_status=$?
set -e
if test "$new_identity_status" -eq 0; then
  test "$new_identity" = "juanlou1217/crafting-resumes"
  test "$(gh repo view juanlou1217/crafting-resumes \
    --json visibility --jq .visibility)" = "PUBLIC"
  test "$(gh repo view juanlou1217/crafting-resumes \
    --json defaultBranchRef --jq .defaultBranchRef.name)" = "main"
  test "$(git ls-remote "$NEW_REMOTE" refs/heads/main | awk '{print $1}')" = \
    "$FEATURE_SHA"
else
  set +e
  new_repo_probe="$(
    gh api --include repos/juanlou1217/crafting-resumes 2>&1
  )"
  new_repo_probe_status=$?
  set -e
  test "$new_repo_probe_status" -ne 0
  rg -q '^HTTP/[^ ]+ 404' <<<"$new_repo_probe"
  test "$(gh repo view juanlou1217/crafting-china-resumes \
    --json nameWithOwner --jq .nameWithOwner)" = \
    "juanlou1217/crafting-china-resumes"
  gh repo rename crafting-resumes \
    --repo juanlou1217/crafting-china-resumes --yes
fi
gh repo edit juanlou1217/crafting-resumes \
  --description "$EXPECTED_DESCRIPTION"
test "$(gh repo view juanlou1217/crafting-resumes \
  --json description --jq .description)" = "$EXPECTED_DESCRIPTION"
```

If the rename succeeds but the description update or its network call fails, rerun this same step. It recognizes the exact new repository and idempotently completes the description instead of retrying the old-name rename.

- [ ] **Step 4: Verify the renamed remote before any local mutation**

```bash
set -euo pipefail
WORKTREE="$(git rev-parse --show-toplevel)"
FEATURE_SHA="$(git -C "$WORKTREE" rev-parse HEAD)"
NEW_REMOTE=git@github.com:juanlou1217/crafting-resumes.git
EXPECTED_DESCRIPTION="Evidence-first resume crafting, JD tailoring, professional packaging, review, and verified PDF delivery for Codex."
RUN_ID="$(gh run list --repo juanlou1217/crafting-resumes \
  --branch main --commit "$FEATURE_SHA" --limit 1 \
  --json databaseId --jq '.[0].databaseId')"
test -n "$RUN_ID"
test "$(gh repo view juanlou1217/crafting-resumes \
  --json nameWithOwner --jq .nameWithOwner)" = \
  "juanlou1217/crafting-resumes"
test "$(gh repo view juanlou1217/crafting-resumes \
  --json visibility --jq .visibility)" = "PUBLIC"
test "$(gh repo view juanlou1217/crafting-resumes \
  --json defaultBranchRef --jq .defaultBranchRef.name)" = "main"
test "$(gh repo view juanlou1217/crafting-resumes \
  --json description --jq .description)" = "$EXPECTED_DESCRIPTION"
test "$(git ls-remote "$NEW_REMOTE" refs/heads/main | awk '{print $1}')" = \
  "$FEATURE_SHA"
test "$(gh run view "$RUN_ID" --repo juanlou1217/crafting-resumes \
  --json conclusion --jq .conclusion)" = "success"
```

If any assertion fails, stop with `$PRIMARY_REPO`, `$WORKTREE`, and the installed Skill unchanged. GitHub’s old URL redirect remains the temporary recovery path.

- [ ] **Step 5: Publish a validated migration runtime, then remove the worktree**

```bash
set -euo pipefail
WORKTREE="$(git rev-parse --show-toplevel)"
PYTHON="${CRAFTING_RESUMES_PYTHON:-$WORKTREE/.venv/bin/python}"
test -x "$PYTHON"
PRIMARY_REPO="$(dirname "$(git -C "$WORKTREE" rev-parse \
  --path-format=absolute --git-common-dir)")"
CODEX_SKILLS_DIR="$HOME/.codex/skills"
CODEX_ROOT="$(dirname "$CODEX_SKILLS_DIR")"
FEATURE_SHA="$(git -C "$WORKTREE" rev-parse HEAD)"
MIGRATION_VENV="$CODEX_ROOT/.crafting-resumes-migration-venv"
EXCLUSIVE_RENAME="$WORKTREE/scripts/exclusive_rename.py"
if [[ -e "$MIGRATION_VENV" || -L "$MIGRATION_VENV" ]]; then
  test -d "$MIGRATION_VENV"
  test ! -L "$MIGRATION_VENV"
  MIGRATION_PYTHON="$MIGRATION_VENV/bin/python"
  test -x "$MIGRATION_PYTHON"
  "$MIGRATION_PYTHON" -c 'import yaml, pypdf, reportlab'
else
  MIGRATION_VENV_STAGE="$(
    mktemp -d "$CODEX_ROOT/.crafting-resumes-migration-venv-stage.XXXXXX"
  )"
  test "$(dirname "$MIGRATION_VENV_STAGE")" = "$CODEX_ROOT"
  test -d "$MIGRATION_VENV_STAGE"
  test ! -L "$MIGRATION_VENV_STAGE"
  chmod 700 "$MIGRATION_VENV_STAGE"
  python3 -m venv "$MIGRATION_VENV_STAGE"
  STAGING_PYTHON="$MIGRATION_VENV_STAGE/bin/python"
  "$STAGING_PYTHON" -m pip install -r "$WORKTREE/requirements-dev.txt"
  "$STAGING_PYTHON" -c 'import yaml, pypdf, reportlab'
  test ! -e "$MIGRATION_VENV"
  test ! -L "$MIGRATION_VENV"
  "$PYTHON" -B "$EXCLUSIVE_RENAME" \
    "$MIGRATION_VENV_STAGE" "$MIGRATION_VENV"
fi
MIGRATION_PYTHON="$MIGRATION_VENV/bin/python"
test -x "$MIGRATION_PYTHON"
"$MIGRATION_PYTHON" -c 'import yaml, pypdf, reportlab'
test "$(git -C "$PRIMARY_REPO" rev-parse HEAD)" = "$FEATURE_SHA"
cd "$PRIMARY_REPO"
git -C "$PRIMARY_REPO" worktree remove "$WORKTREE"
git -C "$PRIMARY_REPO" branch -d codex/neutral-rename-readme
```

The fixed runtime path is published only after venv creation, dependency installation, and import verification succeed. A failed build may leave only a uniquely named non-active staging directory and never poisons the fixed path; rerunning this step creates a fresh stage or validates and reuses an already published runtime. The branch is deleted only after `main` contains the exact candidate SHA.

- [ ] **Step 6: Idempotently rename the primary checkout and repair its SSH remote**

Run from whichever of the old or new checkout paths currently exists. Recheck both names with `lstat` semantics, use a non-overwriting move only when the old path is active, and treat an old `origin` under the new path as a repairable interrupted state:

```bash
set -euo pipefail
CURRENT_REPO="$(git rev-parse --show-toplevel)"
PROJECTS_DIR="$(dirname "$CURRENT_REPO")"
PRIMARY_REPO="$PROJECTS_DIR/crafting-china-resumes"
NEW_REPO="$PROJECTS_DIR/crafting-resumes"
CODEX_SKILLS_DIR="$HOME/.codex/skills"
CODEX_ROOT="$(dirname "$CODEX_SKILLS_DIR")"
MIGRATION_PYTHON="$CODEX_ROOT/.crafting-resumes-migration-venv/bin/python"
OLD_REMOTE=git@github.com:juanlou1217/crafting-china-resumes.git
NEW_REMOTE=git@github.com:juanlou1217/crafting-resumes.git
test -x "$MIGRATION_PYTHON"
case "$(basename "$CURRENT_REPO")" in
  crafting-china-resumes|crafting-resumes) ;;
  *) exit 1 ;;
esac
test "$(basename "$NEW_REPO")" = "crafting-resumes"
if [[ -d "$PRIMARY_REPO" && ! -L "$PRIMARY_REPO" ]] \
  && [[ ! -e "$NEW_REPO" && ! -L "$NEW_REPO" ]]; then
  EXCLUSIVE_RENAME="$PRIMARY_REPO/scripts/exclusive_rename.py"
  "$MIGRATION_PYTHON" -B "$EXCLUSIVE_RENAME" \
    "$PRIMARY_REPO" "$NEW_REPO"
elif [[ ! -e "$PRIMARY_REPO" && ! -L "$PRIMARY_REPO" ]] \
  && [[ -d "$NEW_REPO" && ! -L "$NEW_REPO" ]]; then
  :
else
  exit 1
fi
test ! -e "$PRIMARY_REPO"
test ! -L "$PRIMARY_REPO"
test -d "$NEW_REPO"
test ! -L "$NEW_REPO"
origin_push_url="$(git -C "$NEW_REPO" remote get-url --push origin)"
case "$origin_push_url" in
  "$NEW_REMOTE")
    ;;
  "$OLD_REMOTE")
    git -C "$NEW_REPO" remote set-url origin "$NEW_REMOTE"
    ;;
  *)
    exit 1
    ;;
esac
test "$(git -C "$NEW_REPO" remote get-url --push origin)" = "$NEW_REMOTE"
```

An interruption after the directory move but before `remote set-url` leaves the exact second branch: rerun this step from `$NEW_REPO`; it does not move again and repairs only the known old SSH URL.

If the move completes but remote update or verification fails, run this exact rollback and stop:

```bash
set -euo pipefail
NEW_REPO="$(git rev-parse --show-toplevel)"
PROJECTS_DIR="$(dirname "$NEW_REPO")"
PRIMARY_REPO="$PROJECTS_DIR/crafting-china-resumes"
CODEX_ROOT="$(dirname "$HOME/.codex/skills")"
MIGRATION_PYTHON="$CODEX_ROOT/.crafting-resumes-migration-venv/bin/python"
EXCLUSIVE_RENAME="$NEW_REPO/scripts/exclusive_rename.py"
OLD_REMOTE=git@github.com:juanlou1217/crafting-china-resumes.git
test ! -e "$PRIMARY_REPO"
test ! -L "$PRIMARY_REPO"
test -d "$NEW_REPO"
test ! -L "$NEW_REPO"
"$MIGRATION_PYTHON" -B "$EXCLUSIVE_RENAME" \
  "$NEW_REPO" "$PRIMARY_REPO"
test -d "$PRIMARY_REPO"
test ! -L "$PRIMARY_REPO"
test ! -e "$NEW_REPO"
test ! -L "$NEW_REPO"
git -C "$PRIMARY_REPO" remote set-url origin "$OLD_REMOTE"
test "$(git -C "$PRIMARY_REPO" remote get-url --push origin)" = \
  "$OLD_REMOTE"
```

Never run the rollback if either destination is occupied or is a symlink.

- [ ] **Step 7: Verify GitHub and local identity**

```bash
set -euo pipefail
NEW_REPO="$(git rev-parse --show-toplevel)"
FEATURE_SHA="$(git -C "$NEW_REPO" rev-parse HEAD)"
gh repo view juanlou1217/crafting-resumes \
  --json nameWithOwner,visibility,defaultBranchRef,url
test "$(git -C "$NEW_REPO" rev-parse HEAD)" = "$FEATURE_SHA"
test "$(git -C "$NEW_REPO" branch --show-current)" = "main"
test -z "$(git -C "$NEW_REPO" status --porcelain)"
git -C "$NEW_REPO" status --short --branch
git -C "$NEW_REPO" remote -v
```

Expected: the existing public visibility is preserved, the default branch is
`main`, the local checkout is clean, and SSH URLs use only
`crafting-resumes`.

### Task 8: Install the neutral Skill atomically and verify discovery

**External paths:**
- Source: `$SOURCE_SKILL`
- Staging: unique `$STAGING_SKILL` inside `$STAGING_ROOT` under `$CODEX_SKILLS_DIR`
- New install: `$NEW_INSTALL`
- Old install: `$OLD_INSTALL`
- Recoverable backup: `$OLD_BACKUP`
- Failure quarantine: `$NEW_QUARANTINE`
- Discovery receipt: `$DISCOVERY_RECEIPT`, an empty real directory whose basename binds the source hash and final commit

- [ ] **Step 1: Repair the known origin state and preflight all install paths**

Start one continuous fail-fast Bash session from the renamed repository. Reinitialize every value independently of Tasks 1–7, then require source and old installation to be real directories and every target to be absent under `lstat` semantics:

```bash
set -euo pipefail
NEW_REPO="$(git rev-parse --show-toplevel)"
test "$(basename "$NEW_REPO")" = "crafting-resumes"
PROJECTS_DIR="$(dirname "$NEW_REPO")"
PRIMARY_REPO="$PROJECTS_DIR/crafting-china-resumes"
CODEX_SKILLS_DIR="$HOME/.codex/skills"
CODEX_ROOT="$(dirname "$CODEX_SKILLS_DIR")"
MIGRATION_VENV="$CODEX_ROOT/.crafting-resumes-migration-venv"
MIGRATION_PYTHON="$MIGRATION_VENV/bin/python"
SYSTEM_PYTHON="$(command -v python3)"
test -x "$SYSTEM_PYTHON"
test -x "$MIGRATION_PYTHON"
"$MIGRATION_PYTHON" -c 'import yaml, pypdf, reportlab'
PYTHON="$MIGRATION_PYTHON"
QUICK_VALIDATE="$CODEX_SKILLS_DIR/.system/skill-creator/scripts/quick_validate.py"
HASH_TOOL="$NEW_REPO/tests/crafting-resumes/hash_skill_tree.py"
EXCLUSIVE_RENAME="$NEW_REPO/scripts/exclusive_rename.py"
SOURCE_SKILL="$NEW_REPO/skills/crafting-resumes"
NEW_INSTALL="$CODEX_SKILLS_DIR/crafting-resumes"
OLD_INSTALL="$CODEX_SKILLS_DIR/crafting-china-resumes"
FEATURE_SHA="$(git -C "$NEW_REPO" rev-parse HEAD)"
OLD_REMOTE=git@github.com:juanlou1217/crafting-china-resumes.git
NEW_REMOTE=git@github.com:juanlou1217/crafting-resumes.git
origin_push_url="$(git -C "$NEW_REPO" remote get-url --push origin)"
case "$origin_push_url" in
  "$NEW_REMOTE")
    ;;
  "$OLD_REMOTE")
    git -C "$NEW_REPO" remote set-url origin "$NEW_REMOTE"
    ;;
  *)
    exit 1
    ;;
esac
test "$(git -C "$NEW_REPO" remote get-url --push origin)" = "$NEW_REMOTE"
test "$(git -C "$NEW_REPO" branch --show-current)" = "main"
test -z "$(git -C "$NEW_REPO" status --porcelain)"
git -C "$NEW_REPO" verify-commit "$FEATURE_SHA"
test "$(basename "$SOURCE_SKILL")" = "crafting-resumes"
test "$(basename "$NEW_INSTALL")" = "crafting-resumes"
test "$(basename "$OLD_INSTALL")" = "crafting-china-resumes"
test -d "$SOURCE_SKILL"
test ! -L "$SOURCE_SKILL"
test ! -e "$NEW_INSTALL"
test ! -L "$NEW_INSTALL"
test -d "$OLD_INSTALL"
test ! -L "$OLD_INSTALL"
test "$(stat -f '%d' "$CODEX_SKILLS_DIR")" = \
  "$(stat -f '%d' "$CODEX_ROOT")"
SOURCE_HASH="$("$PYTHON" -B "$HASH_TOOL" "$SOURCE_SKILL")"
OLD_INSTALL_HASH="$("$PYTHON" -B "$HASH_TOOL" "$OLD_INSTALL")"
test -n "$SOURCE_HASH"
test -n "$OLD_INSTALL_HASH"
OLD_BACKUP="$CODEX_ROOT/.crafting-resumes-retired-$OLD_INSTALL_HASH"
NEW_QUARANTINE="$CODEX_ROOT/.crafting-resumes-new-quarantine-$SOURCE_HASH"
DISCOVERY_RECEIPT="$CODEX_ROOT/.crafting-resumes-discovery-ok-$SOURCE_HASH-$FEATURE_SHA"
CLEANUP_RECEIPT="$CODEX_ROOT/.crafting-resumes-cleanup-approved-$SOURCE_HASH-$FEATURE_SHA"
test ! -e "$OLD_BACKUP"
test ! -L "$OLD_BACKUP"
test ! -e "$NEW_QUARANTINE"
test ! -L "$NEW_QUARANTINE"
test ! -e "$DISCOVERY_RECEIPT"
test ! -L "$DISCOVERY_RECEIPT"
test ! -e "$CLEANUP_RECEIPT"
test ! -L "$CLEANUP_RECEIPT"
```

Record both hashes in the execution evidence; the old hash is also persisted in the exact backup basename. If this session is interrupted after any rename, stop mutation and perform the read-only Task 9 bootstrap before choosing success validation or rollback.

- [ ] **Step 2: Stage, validate, compare, and atomically install**

Copy the exact source tree to staging, validate it, compare it, then use the tested exclusive rename helper:

```bash
set -euo pipefail
STAGING_ROOT="$(
  mktemp -d "$CODEX_SKILLS_DIR/.crafting-resumes-stage.XXXXXX"
)"
test "$(dirname "$STAGING_ROOT")" = "$CODEX_SKILLS_DIR"
test -d "$STAGING_ROOT"
test ! -L "$STAGING_ROOT"
STAGING_SKILL="$STAGING_ROOT/crafting-resumes"
test ! -e "$STAGING_SKILL"
test ! -L "$STAGING_SKILL"
cp -R "$SOURCE_SKILL" "$STAGING_SKILL"
test -d "$STAGING_SKILL"
test ! -L "$STAGING_SKILL"
"$PYTHON" -B "$QUICK_VALIDATE" "$STAGING_SKILL"
diff -qr "$SOURCE_SKILL" "$STAGING_SKILL"
STAGING_HASH="$("$PYTHON" -B "$HASH_TOOL" "$STAGING_SKILL")"
test "$STAGING_HASH" = "$SOURCE_HASH"
test ! -e "$NEW_INSTALL"
test ! -L "$NEW_INSTALL"
rollback_new_while_old_active() {
  failure_status="${1:-1}"
  trap - ERR
  set +e
  if [[ ! -e "$STAGING_SKILL" && ! -L "$STAGING_SKILL" ]] \
    && [[ -d "$NEW_INSTALL" && ! -L "$NEW_INSTALL" ]] \
    && [[ ! -e "$NEW_QUARANTINE" && ! -L "$NEW_QUARANTINE" ]]; then
    "$PYTHON" -B "$EXCLUSIVE_RENAME" \
      "$NEW_INSTALL" "$NEW_QUARANTINE"
  fi
  current_old_hash="$("$PYTHON" -B "$HASH_TOOL" "$OLD_INSTALL")"
  if [[ "$current_old_hash" != "$OLD_INSTALL_HASH" ]]; then
    failure_status=1
  fi
  exit "$failure_status"
}
trap 'rollback_new_while_old_active $?' ERR
"$PYTHON" -B "$EXCLUSIVE_RENAME" "$STAGING_SKILL" "$NEW_INSTALL"
test ! -e "$STAGING_SKILL"
test ! -L "$STAGING_SKILL"
test -d "$NEW_INSTALL"
test ! -L "$NEW_INSTALL"
INSTALL_HASH="$("$PYTHON" -B "$HASH_TOOL" "$NEW_INSTALL")"
test "$INSTALL_HASH" = "$SOURCE_HASH"
rmdir "$STAGING_ROOT"
test ! -e "$STAGING_ROOT"
test ! -L "$STAGING_ROOT"
trap - ERR
```

`renameatx_np(RENAME_EXCL | RENAME_NOFOLLOW_ANY)` guarantees that a concurrent file, directory, or symlink is not overwritten and the source is not nested inside it.

- [ ] **Step 3: Validate the final new path and test explicit discovery**

Run quick validation, source/install diff, and the explicit fresh invocation while the old installation is still available:

```bash
set -euo pipefail
rollback_validating_new() {
  failure_status="${1:-1}"
  trap - ERR
  set +e
  if [[ -d "$NEW_INSTALL" && ! -L "$NEW_INSTALL" ]] \
    && [[ ! -e "$NEW_QUARANTINE" && ! -L "$NEW_QUARANTINE" ]]; then
    "$PYTHON" -B "$EXCLUSIVE_RENAME" \
      "$NEW_INSTALL" "$NEW_QUARANTINE"
  fi
  current_old_hash="$("$PYTHON" -B "$HASH_TOOL" "$OLD_INSTALL")"
  if [[ "$current_old_hash" != "$OLD_INSTALL_HASH" ]]; then
    failure_status=1
  fi
  exit "$failure_status"
}
trap 'rollback_validating_new $?' ERR
"$PYTHON" -B "$QUICK_VALIDATE" "$NEW_INSTALL"
diff -qr "$SOURCE_SKILL" "$NEW_INSTALL"
test "$("$PYTHON" -B "$HASH_TOOL" "$NEW_INSTALL")" = "$SOURCE_HASH"
trap - ERR
```

Explicit prompt:

```text
$crafting-resumes 把一段普通项目经历做专业包装。先建立证据边界，一次只问一个关键问题，不要编造事实。
```

The fresh process must discover `crafting-resumes`, distinguish packaging from fabrication, ask at most one blocking question, and avoid unsupported high-risk words. If this explicit discovery fails, run `rollback_validating_new 1`: quarantine `$NEW_INSTALL`, verify `$OLD_INSTALL` remains active with `$OLD_INSTALL_HASH`, and stop. The old name is never removed in this failure branch.

- [ ] **Step 4: Atomically retire the old callable name into a recoverable sibling**

Recheck the old tree and backup immediately before the move, then verify backup identity and hash:

```bash
set -euo pipefail
test -d "$OLD_INSTALL"
test ! -L "$OLD_INSTALL"
test "$("$PYTHON" -B "$HASH_TOOL" "$OLD_INSTALL")" = "$OLD_INSTALL_HASH"
test ! -e "$OLD_BACKUP"
test ! -L "$OLD_BACKUP"
"$PYTHON" -B "$EXCLUSIVE_RENAME" "$OLD_INSTALL" "$OLD_BACKUP"
test ! -e "$OLD_INSTALL"
test ! -L "$OLD_INSTALL"
test -d "$OLD_BACKUP"
test ! -L "$OLD_BACKUP"
test "$("$PYTHON" -B "$HASH_TOOL" "$OLD_BACKUP")" = "$OLD_INSTALL_HASH"
```

`$OLD_BACKUP` is a hash-addressed sibling under the Codex root, outside the active Skills directory, and must remain until Task 9 is entirely green.

- [ ] **Step 5: Test implicit discovery with automatic recovery on failure**

Implicit prompt:

```text
我想把真实经历写得更专业、更有岗位价值，并合理使用高价值关键词；不要编造数字或职责。
```

The fresh process must discover only the new installed Skill and follow the same truth and packaging gates. If discovery or any Skill/install check fails, first quarantine the new installation outside the active Skills directory, then restore the old installation:

```bash
set -euo pipefail
test ! -e "$OLD_INSTALL"
test ! -L "$OLD_INSTALL"
test -d "$NEW_INSTALL"
test ! -L "$NEW_INSTALL"
test -d "$OLD_BACKUP"
test ! -L "$OLD_BACKUP"
test "$("$PYTHON" -B "$HASH_TOOL" "$OLD_BACKUP")" = \
  "$OLD_INSTALL_HASH"
test ! -e "$NEW_QUARANTINE"
test ! -L "$NEW_QUARANTINE"
test ! -e "$DISCOVERY_RECEIPT"
test ! -L "$DISCOVERY_RECEIPT"
"$PYTHON" -B "$EXCLUSIVE_RENAME" \
  "$NEW_INSTALL" "$NEW_QUARANTINE"
"$PYTHON" -B "$EXCLUSIVE_RENAME" "$OLD_BACKUP" "$OLD_INSTALL"
test -d "$OLD_INSTALL"
test ! -L "$OLD_INSTALL"
test "$("$PYTHON" -B "$HASH_TOOL" "$OLD_INSTALL")" = "$OLD_INSTALL_HASH"
test ! -e "$OLD_BACKUP"
test ! -L "$OLD_BACKUP"
test "$("$PYTHON" -B "$HASH_TOOL" "$NEW_QUARANTINE")" = \
  "$SOURCE_HASH"
```

Final failure state: only the old callable name is active; the new tree is hash-verified in quarantine for diagnosis. Never reactivate the old tree while `$NEW_INSTALL` remains active.

Only after both the earlier explicit prompt and this implicit fresh process pass, atomically create the commit/hash-bound receipt:

```bash
set -euo pipefail
test ! -e "$DISCOVERY_RECEIPT"
test ! -L "$DISCOVERY_RECEIPT"
mkdir -m 700 "$DISCOVERY_RECEIPT"
test -d "$DISCOVERY_RECEIPT"
test ! -L "$DISCOVERY_RECEIPT"
test -z "$(find "$DISCOVERY_RECEIPT" -mindepth 1 -print -quit)"
```

If interrupted in state `NB` before this directory exists, neither discovery gate is durably proven and Task 9 must rerun both fresh prompts before finalizing.

- [ ] **Step 6: Verify the migrated installation while retaining rollback**

After implicit discovery succeeds, keep the backup and run:

```bash
set -euo pipefail
"$PYTHON" -B "$QUICK_VALIDATE" "$NEW_INSTALL"
diff -qr "$SOURCE_SKILL" "$NEW_INSTALL"
test "$("$PYTHON" -B "$HASH_TOOL" "$NEW_INSTALL")" = "$SOURCE_HASH"
test -d "$NEW_INSTALL"
test ! -L "$NEW_INSTALL"
test ! -e "$STAGING_ROOT"
test ! -L "$STAGING_ROOT"
test ! -e "$OLD_INSTALL"
test ! -L "$OLD_INSTALL"
test -d "$OLD_BACKUP"
test ! -L "$OLD_BACKUP"
test "$("$PYTHON" -B "$HASH_TOOL" "$OLD_BACKUP")" = "$OLD_INSTALL_HASH"
test ! -e "$NEW_QUARANTINE"
test ! -L "$NEW_QUARANTINE"
test -d "$DISCOVERY_RECEIPT"
test ! -L "$DISCOVERY_RECEIPT"
test -z "$(find "$DISCOVERY_RECEIPT" -mindepth 1 -print -quit)"
```

Do not delete `$OLD_BACKUP` in this task. If this final install check fails, verify that `$DISCOVERY_RECEIPT` is the exact expected empty real directory, remove it with `rmdir`, and then run the Step 5 quarantine-and-restore rollback; a failed installation must not retain a success receipt.

### Task 9: Final verification and completion evidence

Run Steps 1–5 in one continuous fail-fast Bash session. Step 1 reconstructs every local value from the renamed repository, discovery receipt, and any hash-addressed backup without requiring network access; Step 4 performs GitHub checks only after local state is safe. It consumes no shell state from Tasks 7–8.

- [ ] **Step 1: Rebuild all migration state in a fresh shell**

```bash
set -euo pipefail
NEW_REPO="$(git rev-parse --show-toplevel)"
test "$(basename "$NEW_REPO")" = "crafting-resumes"
PROJECTS_DIR="$(dirname "$NEW_REPO")"
PRIMARY_REPO="$PROJECTS_DIR/crafting-china-resumes"
CODEX_SKILLS_DIR="$HOME/.codex/skills"
CODEX_ROOT="$(dirname "$CODEX_SKILLS_DIR")"
MIGRATION_VENV="$CODEX_ROOT/.crafting-resumes-migration-venv"
MIGRATION_PYTHON="$MIGRATION_VENV/bin/python"
SYSTEM_PYTHON="$(command -v python3)"
case "$SYSTEM_PYTHON" in
  /*) ;;
  *) exit 1 ;;
esac
test -x "$SYSTEM_PYTHON"
QUICK_VALIDATE="$CODEX_SKILLS_DIR/.system/skill-creator/scripts/quick_validate.py"
HASH_TOOL="$NEW_REPO/tests/crafting-resumes/hash_skill_tree.py"
EXCLUSIVE_RENAME="$NEW_REPO/scripts/exclusive_rename.py"
COMMIT_EQUIVALENCE="$NEW_REPO/tests/crafting-resumes/behavior/commit_equivalence.py"
METADATA_VALIDATOR="$NEW_REPO/tests/crafting-resumes/behavior/validate_git_metadata.py"
SOURCE_SKILL="$NEW_REPO/skills/crafting-resumes"
NEW_INSTALL="$CODEX_SKILLS_DIR/crafting-resumes"
OLD_INSTALL="$CODEX_SKILLS_DIR/crafting-china-resumes"
FEATURE_SHA="$(git -C "$NEW_REPO" rev-parse HEAD)"
NEW_REMOTE=git@github.com:juanlou1217/crafting-resumes.git
EXPECTED_DESCRIPTION="Evidence-first resume crafting, JD tailoring, professional packaging, review, and verified PDF delivery for Codex."
path_present() {
  [[ -e "$1" || -L "$1" ]]
}
require_real_if_present() {
  if path_present "$1"; then
    [[ -d "$1" && ! -L "$1" ]]
  fi
}
MIGRATION_RUNTIME_PRESENT=0
if path_present "$MIGRATION_VENV"; then
  test -d "$MIGRATION_VENV"
  test ! -L "$MIGRATION_VENV"
  if test -x "$MIGRATION_PYTHON"; then
    PYTHON="$MIGRATION_PYTHON"
    MIGRATION_RUNTIME_PRESENT=1
  else
    PYTHON="$SYSTEM_PYTHON"
  fi
else
  PYTHON="$SYSTEM_PYTHON"
fi
SOURCE_HASH="$("$PYTHON" -B "$HASH_TOOL" "$SOURCE_SKILL")"
NEW_QUARANTINE="$CODEX_ROOT/.crafting-resumes-new-quarantine-$SOURCE_HASH"
DISCOVERY_RECEIPT="$CODEX_ROOT/.crafting-resumes-discovery-ok-$SOURCE_HASH-$FEATURE_SHA"
CLEANUP_RECEIPT="$CODEX_ROOT/.crafting-resumes-cleanup-approved-$SOURCE_HASH-$FEATURE_SHA"
shopt -s nullglob
backup_candidates=(
  "$CODEX_ROOT"/.crafting-resumes-retired-[0-9a-f]*
)
shopt -u nullglob
test "${#backup_candidates[@]}" -le 1
require_real_if_present "$OLD_INSTALL"
require_real_if_present "$NEW_INSTALL"
require_real_if_present "$NEW_QUARANTINE"
require_real_if_present "$DISCOVERY_RECEIPT"
require_real_if_present "$CLEANUP_RECEIPT"
if path_present "$DISCOVERY_RECEIPT"; then
  test -z "$(find "$DISCOVERY_RECEIPT" -mindepth 1 -print -quit)"
fi
if path_present "$CLEANUP_RECEIPT"; then
  test -z "$(find "$CLEANUP_RECEIPT" -mindepth 1 -print -quit)"
fi
if [[ "${#backup_candidates[@]}" -eq 1 ]]; then
  OLD_BACKUP="${backup_candidates[0]}"
  require_real_if_present "$OLD_BACKUP"
  OLD_INSTALL_HASH="${OLD_BACKUP##*.crafting-resumes-retired-}"
  [[ "$OLD_INSTALL_HASH" =~ ^[0-9a-f]{64}$ ]]
  test "$("$PYTHON" -B "$HASH_TOOL" "$OLD_BACKUP")" = \
    "$OLD_INSTALL_HASH"
elif [[ -d "$OLD_INSTALL" && ! -L "$OLD_INSTALL" ]]; then
  OLD_INSTALL_HASH="$("$PYTHON" -B "$HASH_TOOL" "$OLD_INSTALL")"
  OLD_BACKUP="$CODEX_ROOT/.crafting-resumes-retired-$OLD_INSTALL_HASH"
else
  OLD_INSTALL_HASH=
  OLD_BACKUP="$CODEX_ROOT/.crafting-resumes-retired-unresolved"
fi
old_flag=
new_flag=
backup_flag=
quarantine_flag=
discovery_flag=
cleanup_flag=
if path_present "$OLD_INSTALL"; then old_flag=O; fi
if path_present "$NEW_INSTALL"; then new_flag=N; fi
if path_present "$OLD_BACKUP"; then backup_flag=B; fi
if path_present "$NEW_QUARANTINE"; then quarantine_flag=Q; fi
if path_present "$DISCOVERY_RECEIPT"; then discovery_flag=D; fi
if path_present "$CLEANUP_RECEIPT"; then cleanup_flag=C; fi
MIGRATION_STATE="$old_flag$new_flag$backup_flag$quarantine_flag$discovery_flag$cleanup_flag"
case "$MIGRATION_STATE" in
  O|ON|NB|NBD|OQ|BQ|NBDC|NBC|NC|N) ;;
  *) exit 1 ;;
esac
```

`hash_skill_tree.py` imports only Python standard-library modules, so terminal and cleanup recovery do not depend on the retired migration environment. Full verification still requires the validated migration Python and pinned development dependencies.

- [ ] **Step 2: Classify verification, cleanup-resume, terminal, or rollback state**

`NBD` enters full verification only with the validated migration runtime still present. A state ending in `C` resumes a cleanup that was authorized only after all gates passed. Bare `N` is the completed terminal state and uses dependency-free revalidation.

```bash
set -euo pipefail
COMPLETION_MODE=
case "$MIGRATION_STATE" in
  NBD)
    test "$MIGRATION_RUNTIME_PRESENT" -eq 1
    "$MIGRATION_PYTHON" -c 'import yaml, pypdf, reportlab'
    COMPLETION_MODE=verify
    ;;
  NBDC|NBC|NC)
    COMPLETION_MODE=cleanup
    ;;
  N)
    test "$MIGRATION_RUNTIME_PRESENT" -eq 0
    COMPLETION_MODE=terminal
    ;;
  NB)
    exit 2
    ;;
  O)
    exit 2
    ;;
  ON)
    test "$("$PYTHON" -B "$HASH_TOOL" "$OLD_INSTALL")" = \
      "$OLD_INSTALL_HASH"
    "$PYTHON" -B "$EXCLUSIVE_RENAME" \
      "$NEW_INSTALL" "$NEW_QUARANTINE"
    test "$("$PYTHON" -B "$HASH_TOOL" "$OLD_INSTALL")" = \
      "$OLD_INSTALL_HASH"
    test "$("$PYTHON" -B "$HASH_TOOL" "$NEW_QUARANTINE")" = \
      "$SOURCE_HASH"
    exit 2
    ;;
  BQ)
    test "$("$PYTHON" -B "$HASH_TOOL" "$OLD_BACKUP")" = \
      "$OLD_INSTALL_HASH"
    "$PYTHON" -B "$EXCLUSIVE_RENAME" \
      "$OLD_BACKUP" "$OLD_INSTALL"
    test "$("$PYTHON" -B "$HASH_TOOL" "$OLD_INSTALL")" = \
      "$OLD_INSTALL_HASH"
    test "$("$PYTHON" -B "$HASH_TOOL" "$NEW_QUARANTINE")" = \
      "$SOURCE_HASH"
    exit 2
    ;;
  OQ)
    exit 2
    ;;
  *)
    exit 1
    ;;
esac
test -n "$COMPLETION_MODE"
```

`O` means installation has not started; return to Task 8. `NB` means the filesystem move completed but discovery is unproven: with only the new name active, rerun both Task 8 fresh prompts, create the receipt only if both pass, and otherwise execute the Task 8 Step 5 quarantine-and-restore rollback. `ON` is safely rolled back by quarantining new while old remains active. `BQ` restores old before inspecting quarantine. `OQ` is an already-complete rollback. Cleanup and terminal states never require the retired backup or migration venv to reappear.

- [ ] **Step 3: Run full verification or dependency-free terminal revalidation**

```bash
set -euo pipefail
cd "$NEW_REPO"
case "$COMPLETION_MODE" in
  verify)
    "$PYTHON" -B -m unittest discover \
      -s tests/crafting-resumes -p 'test_*.py'
    EVALUATED_SKILL_COMMIT="$("$PYTHON" -c \
      'import json, pathlib; print(json.loads(pathlib.Path(
      "tests/crafting-resumes/behavior/packaging-eval/candidate.json"
      ).read_text(encoding="utf-8"))["skill_commit"])')"
    PUBLISHED_SKILL_COMMIT="$(
      "$PYTHON" -B "$COMMIT_EQUIVALENCE" \
        "$NEW_REPO" "$EVALUATED_SKILL_COMMIT"
    )"
    git cat-file -e "$PUBLISHED_SKILL_COMMIT^{commit}"
    "$PYTHON" -B \
      tests/crafting-resumes/behavior/validate_packaging_eval.py \
      --expected-skill-commit "$EVALUATED_SKILL_COMMIT"
    "$PYTHON" -B \
      tests/crafting-resumes/behavior/validate_eval_assets.py
    "$PYTHON" -c 'import json, pathlib, sys; commits = {
json.loads(path.read_text(encoding="utf-8"))["skill_commit"]
for path in pathlib.Path(sys.argv[1]).glob("*.json")};
assert commits == {sys.argv[2]}' \
      tests/crafting-resumes/manifests/candidate \
      "$EVALUATED_SKILL_COMMIT"
    "$PYTHON" -B "$QUICK_VALIDATE" \
      skills/crafting-resumes
    diff -qr skills/crafting-resumes "$NEW_INSTALL"
    test "$("$PYTHON" -B "$HASH_TOOL" skills/crafting-resumes)" = \
      "$("$PYTHON" -B "$HASH_TOOL" "$NEW_INSTALL")"
    ;;
  terminal)
    test -d "$NEW_INSTALL"
    test ! -L "$NEW_INSTALL"
    diff -qr skills/crafting-resumes "$NEW_INSTALL"
    test "$("$SYSTEM_PYTHON" -B "$HASH_TOOL" skills/crafting-resumes)" = \
      "$("$SYSTEM_PYTHON" -B "$HASH_TOOL" "$NEW_INSTALL")"
    ;;
  cleanup)
    ;;
  *)
    exit 1
    ;;
esac
```

- [ ] **Step 4: Verify Git, GitHub, CI, SSH, and final paths**

```bash
set -euo pipefail
if [[ "$COMPLETION_MODE" != "cleanup" ]]; then
  cd "$NEW_REPO"
  git status --short --branch
  test "$(git rev-parse HEAD)" = "$FEATURE_SHA"
  test "$(git branch --show-current)" = "main"
  test -z "$(git status --porcelain)"
  test "$(git remote get-url --push origin)" = "$NEW_REMOTE"
  git verify-commit HEAD
  "$SYSTEM_PYTHON" -B "$METADATA_VALIDATOR" "$NEW_REPO"
  ssh_output="$(ssh -T -o BatchMode=yes git@github.com 2>&1 || true)"
  rg -F "Hi juanlou1217" <<<"$ssh_output"
  test "$(gh repo view juanlou1217/crafting-resumes \
    --json nameWithOwner --jq .nameWithOwner)" = \
    "juanlou1217/crafting-resumes"
  test "$(gh repo view juanlou1217/crafting-resumes \
    --json visibility --jq .visibility)" = "PUBLIC"
  test "$(gh repo view juanlou1217/crafting-resumes \
    --json defaultBranchRef --jq .defaultBranchRef.name)" = "main"
  test "$(gh repo view juanlou1217/crafting-resumes \
    --json description --jq .description)" = "$EXPECTED_DESCRIPTION"
  test "$(git ls-remote "$NEW_REMOTE" refs/heads/main | awk '{print $1}')" = \
    "$FEATURE_SHA"
  RUN_ID="$(gh run list --repo juanlou1217/crafting-resumes \
    --branch main --commit "$FEATURE_SHA" --limit 1 \
    --json databaseId --jq '.[0].databaseId')"
  test -n "$RUN_ID"
  test "$(gh run view "$RUN_ID" --repo juanlou1217/crafting-resumes \
    --json headSha --jq .headSha)" = "$FEATURE_SHA"
  test "$(gh run view "$RUN_ID" --repo juanlou1217/crafting-resumes \
    --json conclusion --jq .conclusion)" = "success"
  test ! -e "$PRIMARY_REPO"
  test ! -L "$PRIMARY_REPO"
  test ! -e "$OLD_INSTALL"
  test ! -L "$OLD_INSTALL"
  case "$COMPLETION_MODE" in
    verify)
      test -d "$OLD_BACKUP"
      test ! -L "$OLD_BACKUP"
      test -d "$DISCOVERY_RECEIPT"
      test ! -L "$DISCOVERY_RECEIPT"
      test -z "$(find "$DISCOVERY_RECEIPT" -mindepth 1 -print -quit)"
      test ! -e "$CLEANUP_RECEIPT"
      test ! -L "$CLEANUP_RECEIPT"
      ;;
    terminal)
      test "${#backup_candidates[@]}" -eq 0
      test ! -e "$DISCOVERY_RECEIPT"
      test ! -L "$DISCOVERY_RECEIPT"
      test ! -e "$CLEANUP_RECEIPT"
      test ! -L "$CLEANUP_RECEIPT"
      test ! -e "$MIGRATION_VENV"
      test ! -L "$MIGRATION_VENV"
      ;;
    *)
      exit 1
      ;;
  esac
fi
```

In `verify` mode, a Step 3 failure requires removing the exact empty discovery receipt and performing the Task 8 Step 5 quarantine-and-restore rollback. A Step 4 external failure keeps new active plus backup and receipt for diagnosis. In `terminal` mode, no old backup exists; a revalidation failure must stop for diagnosis without destructive action. `cleanup` mode reaches this point only through the final-gate receipt created below.

- [ ] **Step 5: Create a cleanup gate and finish cleanup idempotently**

In `verify` mode, create the cleanup receipt only after Steps 1–4 pass. In `cleanup` mode, that receipt proves the same gates passed before the interruption. Delete the backup last among retained recovery assets; remove the cleanup receipt only after terminal state `N` is reached.

```bash
set -euo pipefail
case "$COMPLETION_MODE" in
  verify)
    test "$OLD_BACKUP" = \
      "$CODEX_ROOT/.crafting-resumes-retired-$OLD_INSTALL_HASH"
    test -d "$OLD_BACKUP"
    test ! -L "$OLD_BACKUP"
    test "$("$PYTHON" -B "$HASH_TOOL" "$OLD_BACKUP")" = \
      "$OLD_INSTALL_HASH"
    test "$("$PYTHON" -B "$HASH_TOOL" "$NEW_INSTALL")" = \
      "$SOURCE_HASH"
    test "$DISCOVERY_RECEIPT" = \
      "$CODEX_ROOT/.crafting-resumes-discovery-ok-$SOURCE_HASH-$FEATURE_SHA"
    test -d "$DISCOVERY_RECEIPT"
    test ! -L "$DISCOVERY_RECEIPT"
    test -z "$(find "$DISCOVERY_RECEIPT" -mindepth 1 -print -quit)"
    test "$MIGRATION_VENV" = \
      "$CODEX_ROOT/.crafting-resumes-migration-venv"
    test -d "$MIGRATION_VENV"
    test ! -L "$MIGRATION_VENV"
    test ! -e "$CLEANUP_RECEIPT"
    test ! -L "$CLEANUP_RECEIPT"
    mkdir -m 700 "$CLEANUP_RECEIPT"
    ;;
  cleanup)
    ;;
  terminal)
    test "$MIGRATION_STATE" = "N"
    ;;
  *)
    exit 1
    ;;
esac

if [[ "$COMPLETION_MODE" != "terminal" ]]; then
  test "$CLEANUP_RECEIPT" = \
    "$CODEX_ROOT/.crafting-resumes-cleanup-approved-$SOURCE_HASH-$FEATURE_SHA"
  test -d "$CLEANUP_RECEIPT"
  test ! -L "$CLEANUP_RECEIPT"
  test -z "$(find "$CLEANUP_RECEIPT" -mindepth 1 -print -quit)"
  test ! -e "$OLD_INSTALL"
  test ! -L "$OLD_INSTALL"
  test "$(git -C "$NEW_REPO" rev-parse HEAD)" = "$FEATURE_SHA"
  test "$(git -C "$NEW_REPO" branch --show-current)" = "main"
  test -z "$(git -C "$NEW_REPO" status --porcelain)"
  test "$(git -C "$NEW_REPO" remote get-url --push origin)" = \
    "$NEW_REMOTE"
  diff -qr "$SOURCE_SKILL" "$NEW_INSTALL"
  test "$("$SYSTEM_PYTHON" -B "$HASH_TOOL" "$NEW_INSTALL")" = \
    "$SOURCE_HASH"

  if path_present "$MIGRATION_VENV"; then
    test "$MIGRATION_VENV" = \
      "$CODEX_ROOT/.crafting-resumes-migration-venv"
    test -d "$MIGRATION_VENV"
    test ! -L "$MIGRATION_VENV"
    rm -rf -- "$MIGRATION_VENV"
  fi
  test ! -e "$MIGRATION_VENV"
  test ! -L "$MIGRATION_VENV"

  if path_present "$DISCOVERY_RECEIPT"; then
    test "$DISCOVERY_RECEIPT" = \
      "$CODEX_ROOT/.crafting-resumes-discovery-ok-$SOURCE_HASH-$FEATURE_SHA"
    test -d "$DISCOVERY_RECEIPT"
    test ! -L "$DISCOVERY_RECEIPT"
    test -z "$(find "$DISCOVERY_RECEIPT" -mindepth 1 -print -quit)"
    rmdir "$DISCOVERY_RECEIPT"
  fi
  test ! -e "$DISCOVERY_RECEIPT"
  test ! -L "$DISCOVERY_RECEIPT"

  if [[ "${#backup_candidates[@]}" -eq 1 ]]; then
    test "$OLD_BACKUP" = "${backup_candidates[0]}"
    test "$OLD_BACKUP" = \
      "$CODEX_ROOT/.crafting-resumes-retired-$OLD_INSTALL_HASH"
    test -d "$OLD_BACKUP"
    test ! -L "$OLD_BACKUP"
    test "$("$SYSTEM_PYTHON" -B "$HASH_TOOL" "$OLD_BACKUP")" = \
      "$OLD_INSTALL_HASH"
    rm -rf -- "$OLD_BACKUP"
  fi
  test ! -e "$OLD_BACKUP"
  test ! -L "$OLD_BACKUP"

  rmdir "$CLEANUP_RECEIPT"
  test ! -e "$CLEANUP_RECEIPT"
  test ! -L "$CLEANUP_RECEIPT"
fi

test -d "$NEW_INSTALL"
test ! -L "$NEW_INSTALL"
test "$("$SYSTEM_PYTHON" -B "$HASH_TOOL" "$NEW_INSTALL")" = \
  "$SOURCE_HASH"
test ! -e "$OLD_INSTALL"
test ! -L "$OLD_INSTALL"
```

- [ ] **Step 6: Report the completed migration**

Report the neutral GitHub URL, renamed local path, new invocation, test totals, CI URL, source/install hash equality, successful verification and retirement of the discovery and cleanup receipts, terminal `N` state, packaging principle, keyword behavior, and old-name retirement. Do not expose raw invocation logs, local key material, or real candidate data.
