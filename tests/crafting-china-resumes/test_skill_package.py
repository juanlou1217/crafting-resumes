from __future__ import annotations

import re
import tempfile
import unicodedata
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = ROOT / "skills/crafting-china-resumes"
SKILL_FILE = SKILL_ROOT / "SKILL.md"
NOTICE_FILE = SKILL_ROOT / "THIRD_PARTY_NOTICES.md"

EXPECTED_REFERENCES = {
    "references/china-recruiting-context.md",
    "references/evidence-and-truthfulness.md",
    "references/experience-interview.md",
    "references/jd-mapping.md",
    "references/modes-and-state-machine.md",
    "references/obsidian-pdf-delivery.md",
    "references/output-contracts.md",
    "references/resume-writing.md",
    "references/review-rubrics.md",
    "references/role-playbooks-campus-and-transition.md",
    "references/role-playbooks-operations-and-commercial.md",
    "references/role-playbooks-product-and-delivery.md",
    "references/role-playbooks-tech-and-data.md",
}
SCAFFOLD_TEXT_PATTERNS = (
    re.compile(r"\[TODO", re.IGNORECASE),
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"example_asset", re.IGNORECASE),
    re.compile(r"Structuring This Skill", re.IGNORECASE),
    re.compile(
        r"^\s*(?:(?:#|//|;|--|\*)\s*)?TODO\s*:",
        re.IGNORECASE | re.MULTILINE,
    ),
    re.compile(r"\bThis is a placeholder\b", re.IGNORECASE),
)
SCAFFOLD_RELATIVE_PATHS = {
    "scripts/example.py",
}
GENERATED_NAMES = {
    "__pycache__",
    ".DS_Store",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage",
    "coverage.xml",
    "htmlcov",
    ".tox",
    ".nox",
}
GENERATED_SUFFIXES = (".pyc", ".pyo", ".swp", ".swo", ".tmp")
GENERATED_PATH_PARTS = {
    "build",
    "dist",
    ".eggs",
}
GENERATED_METADATA_SUFFIXES = (
    ".egg-info",
    ".dist-info",
)
RETIRED_FILE_NAMES = {
    "build_resume_pdf.py",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
}
RETIRED_PATH_PARTS = {
    "node_modules",
    "templates",
}
RETIRED_STEMS = {
    "modern-minimal",
    "classic-professional",
    "creative-clean",
}
PLAYWRIGHT_PROHIBITION_PATTERNS = (
    re.compile(
        r"(?:严禁|不得|禁止|不可|不要|不应|未使用|没有使用|不使用)"
        r"[^。\n]*playwright",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:must\s+not|do\s+not|never)\b[^.\n]*\bplaywright\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bplaywright\b[^.\n]*\b(?:must\s+not|is\s+not\s+used|"
        r"is\s+forbidden|is\s+prohibited|is\s+not\s+allowed)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bplaywright\b\s*(?:被|应被|是)?\s*"
        r"(?:严禁|禁止|不允许|不可|不得)",
        re.IGNORECASE,
    ),
)
PLAYWRIGHT_POSITIVE_INVOCATION_PATTERNS = (
    re.compile(r"\b(?:from|import)\s+playwright\b", re.IGNORECASE),
    re.compile(r"\brequire\s*\(\s*['\"]playwright", re.IGNORECASE),
    re.compile(r"@playwright/", re.IGNORECASE),
    re.compile(r"\bplaywright\.(?:chromium|firefox|webkit)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:npx|npm\s+exec|pnpm\s+exec|yarn)\s+playwright\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bplaywright\s+(?:install|test|pdf|screenshot|open|codegen)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:this|current)\s+skill\b[^.\n]{0,80}"
        r"\b(?:use|uses|using|run|runs|invoke|invokes|include|includes)\b"
        r"[^.\n]{0,40}\bplaywright\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:当前|本)\s*skill[^。\n]{0,80}"
        r"(?:使用|运行|调用|引入|包含|采用)[^。\n]{0,40}\bplaywright\b",
        re.IGNORECASE,
    ),
)
PLAYWRIGHT_PROVENANCE_SOURCE_PATTERNS = (
    re.compile(
        r"\bupstream\s+(?:project|repository|source)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"上游(?:项目|仓库|来源)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bprovenance\s*:[^.\n]*"
        r"\b(?:Easy-Job-Tutor|resume-jd-optimizer-cn)\b",
        re.IGNORECASE,
    ),
)
PLAYWRIGHT_ATTACHED_EXCLUSION_PATTERNS = (
    re.compile(
        r"\bplaywright\b\s*,?\s*"
        r"(?:(?:which|that|and\s+it|it)\s+)?"
        r"(?:(?:is|was|were|are|has\s+been|had\s+been)\s+)?"
        r"not\s+(?:adapted|included|used|invoked|packaged|executed)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:does|did|has|had|will|would)\s+not\s+"
        r"(?:adapt|include|use|invoke|package|execute)\s+\bplaywright\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bplaywright\b\s*(?:本身)?\s*(?:未|不)(?:被)?"
        r"(?:纳入|采用|采纳|包含|引入|使用|执行|运行)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:未|不)(?:曾)?(?:纳入|采用|采纳|包含|引入|使用|执行|运行)"
        r"\s*\bplaywright\b",
        re.IGNORECASE,
    ),
)
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
ANONYMOUS_FIXTURE_PATHS = (
    ROOT / "tests/crafting-china-resumes/behavior/cases",
    ROOT / "tests/crafting-china-resumes/behavior/baseline",
    ROOT / "tests/crafting-china-resumes/behavior/candidate",
    ROOT / "tests/crafting-china-resumes/behavior/regressions",
    ROOT / "tests/crafting-china-resumes/pdf/fixtures",
    ROOT / "tests/crafting-china-resumes/manifests/baseline",
    ROOT / "tests/crafting-china-resumes/manifests/candidate",
)
ANONYMOUS_FIXTURE_FILES = (
    ROOT / "tests/crafting-china-resumes/behavior/baseline-summary.md",
    ROOT / "tests/crafting-china-resumes/behavior/rubric.md",
)

UPSTREAM_NOTICE_VALUES = (
    "https://github.com/coinluu/resume-jd-optimizer-cn",
    "114c85c32dc77bc9ec7315976a21a1f761868664",
    "Copyright (c) 2026 coinluu",
    "https://github.com/yicLionel/Easy-Job-Tutor",
    "8b628a2865144383fd955236c16f62e686a7b0d5",
    "Copyright (c) 2026 Easy-Job-Tutor contributors",
)
MIT_PERMISSION = (
    "Permission is hereby granted, free of charge, to any person obtaining a copy"
)
MIT_WARRANTY = (
    'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR'
)


def parse_skill() -> tuple[dict[str, object], str]:
    if SKILL_FILE.is_symlink():
        raise AssertionError("SKILL.md must not be a symlink")
    text = SKILL_FILE.read_text(encoding="utf-8")
    match = re.fullmatch(
        r"---\n(?P<frontmatter>.*?)\n---\n(?P<body>.*)",
        text,
        flags=re.DOTALL,
    )
    if match is None:
        raise AssertionError("SKILL.md must contain one leading YAML frontmatter block")
    frontmatter = yaml.safe_load(match.group("frontmatter"))
    if not isinstance(frontmatter, dict):
        raise AssertionError("SKILL.md frontmatter must be a mapping")
    return frontmatter, match.group("body")


def normalize_policy_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def utf8_text_files(
    root: Path,
) -> tuple[list[tuple[Path, str]], list[str]]:
    text_files: list[tuple[Path, str]] = []
    violations: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        relative_path = path.relative_to(root)
        try:
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            violations.append(
                f"Skill file must be UTF-8 text: {relative_path.as_posix()}"
            )
            continue
        text_files.append((relative_path, text))
    return text_files, violations


def scaffold_violations(root: Path) -> list[str]:
    text_files, violations = utf8_text_files(root)
    for relative_path, text in text_files:
        normalized_path = normalize_policy_text(relative_path.as_posix())
        if (
            normalized_path in SCAFFOLD_RELATIVE_PATHS
            or "example_asset" in normalized_path
        ):
            violations.append(f"scaffold path: {relative_path.as_posix()}")
        for pattern in SCAFFOLD_TEXT_PATTERNS:
            if pattern.search(text):
                violations.append(
                    f"scaffold text in {relative_path.as_posix()}: "
                    f"{pattern.pattern}"
                )
    return violations


def generated_artifact_violations(root: Path) -> list[str]:
    violations: list[str] = []
    normalized_names = {
        normalize_policy_text(name) for name in GENERATED_NAMES
    }
    normalized_parts = {
        normalize_policy_text(part) for part in GENERATED_PATH_PARTS
    }
    for path in sorted(root.rglob("*")):
        relative_path = path.relative_to(root)
        relative_parts = tuple(
            normalize_policy_text(part) for part in relative_path.parts
        )
        name = normalize_policy_text(path.name)
        generated = (
            name in normalized_names
            or name.startswith(".coverage.")
            or name.endswith(tuple(suffix.casefold() for suffix in GENERATED_SUFFIXES))
            or name.endswith("~")
            or any(part in normalized_parts for part in relative_parts)
            or any(
                part.endswith(GENERATED_METADATA_SUFFIXES)
                for part in relative_parts
            )
        )
        if generated:
            violations.append(relative_path.as_posix())
    return violations


def playwright_statement_is_allowed(statement: str) -> bool:
    normalized_statement = normalize_policy_text(statement)
    if "playwright" not in normalized_statement:
        return True
    if any(
        pattern.search(normalized_statement)
        for pattern in PLAYWRIGHT_PROHIBITION_PATTERNS
    ):
        return True
    if any(
        pattern.search(normalized_statement)
        for pattern in PLAYWRIGHT_POSITIVE_INVOCATION_PATTERNS
    ):
        return False
    has_precise_source = any(
        pattern.search(normalized_statement)
        for pattern in PLAYWRIGHT_PROVENANCE_SOURCE_PATTERNS
    )
    has_attached_exclusion = any(
        pattern.search(normalized_statement)
        for pattern in PLAYWRIGHT_ATTACHED_EXCLUSION_PATTERNS
    )
    return has_precise_source and has_attached_exclusion


def playwright_violations(root: Path) -> list[str]:
    violations: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            continue
        relative_path = path.relative_to(root)
        if "playwright" in normalize_policy_text(relative_path.as_posix()):
            violations.append(
                f"Playwright path is not allowed: {relative_path.as_posix()}"
            )
    text_files, encoding_violations = utf8_text_files(root)
    violations.extend(encoding_violations)
    for relative_path, text in text_files:
        for line_number, line in enumerate(text.splitlines(), start=1):
            statements = re.split(r"[.;；。]", line)
            for statement in statements:
                if "playwright" not in normalize_policy_text(statement):
                    continue
                allowed_location = (
                    bool(relative_path.parts)
                    and relative_path.parts[0] == "references"
                ) or relative_path.as_posix() == "THIRD_PARTY_NOTICES.md"
                if not allowed_location or not playwright_statement_is_allowed(
                    statement
                ):
                    violations.append(
                        f"Playwright statement is not allowed: "
                        f"{relative_path.as_posix()}:{line_number}"
                    )
    return violations


def forbidden_personal_tokens(value: str) -> list[str]:
    normalized_value = normalize_policy_text(value)
    return [
        token
        for token in FORBIDDEN_PERSONAL_TOKENS
        if normalize_policy_text(token) in normalized_value
    ]


def anonymous_fixture_violations(
    fixture_roots: tuple[Path, ...],
    fixture_files: tuple[Path, ...] = (),
) -> list[str]:
    violations: list[str] = []

    def inspect_file(path: Path, display_path: str) -> None:
        if path.is_symlink():
            violations.append(f"anonymous fixture symlink: {display_path}")
            return
        if not path.is_file():
            violations.append(f"anonymous fixture missing: {display_path}")
            return
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            violations.append(f"anonymous fixture is not UTF-8: {display_path}")
            return
        for token in forbidden_personal_tokens(text):
            violations.append(
                f"personal token {token!r} in fixture content: {display_path}"
            )

    for fixture_root in fixture_roots:
        if not fixture_root.exists():
            continue
        if fixture_root.is_symlink() or not fixture_root.is_dir():
            violations.append(f"unsafe anonymous fixture root: {fixture_root.name}")
            continue
        for path in sorted(fixture_root.rglob("*")):
            relative_path = path.relative_to(fixture_root).as_posix()
            for token in forbidden_personal_tokens(relative_path):
                violations.append(
                    f"personal token {token!r} in fixture path: {relative_path}"
                )
            if path.is_symlink():
                violations.append(
                    f"anonymous fixture symlink: {relative_path}"
                )
            elif path.is_file():
                inspect_file(path, relative_path)

    for path in fixture_files:
        for token in forbidden_personal_tokens(path.name):
            violations.append(
                f"personal token {token!r} in fixture path: {path.name}"
            )
        inspect_file(path, path.name)
    return violations


class SkillPackageTests(unittest.TestCase):
    def test_frontmatter_has_only_name_and_description(self) -> None:
        frontmatter, _ = parse_skill()
        self.assertEqual(set(frontmatter), {"name", "description"})
        self.assertEqual(frontmatter["name"], "crafting-china-resumes")
        self.assertIsInstance(frontmatter["description"], str)

    def test_description_starts_with_use_when(self) -> None:
        frontmatter, _ = parse_skill()
        description = frontmatter["description"]
        self.assertIsInstance(description, str)
        assert isinstance(description, str)
        self.assertTrue(description.startswith("Use when"))
        self.assertLessEqual(len(description), 1024)

    def test_skill_router_body_is_at_most_500_words(self) -> None:
        _, body = parse_skill()
        self.assertLessEqual(len(re.findall(r"\S+", body)), 500)

    def test_every_required_reference_is_routed_and_exists(self) -> None:
        skill_text = SKILL_FILE.read_text(encoding="utf-8")
        routed = set(
            re.findall(r"`(references/[A-Za-z0-9._/-]+\.md)`", skill_text)
        )
        on_disk = {
            path.relative_to(SKILL_ROOT).as_posix()
            for path in (SKILL_ROOT / "references").glob("*.md")
        }
        self.assertEqual(routed, EXPECTED_REFERENCES)
        self.assertEqual(on_disk, EXPECTED_REFERENCES)
        for relative_path in routed:
            with self.subTest(reference=relative_path):
                path = SKILL_ROOT / relative_path
                self.assertTrue(path.is_file())
                self.assertFalse(path.is_symlink())

    def test_skill_text_contains_no_scaffold_marker(self) -> None:
        self.assertEqual(scaffold_violations(SKILL_ROOT), [])

    def test_skill_tree_contains_no_generated_artifacts_or_symlinks(self) -> None:
        self.assertEqual(generated_artifact_violations(SKILL_ROOT), [])
        for path in SKILL_ROOT.rglob("*"):
            relative_path = path.relative_to(SKILL_ROOT).as_posix()
            with self.subTest(path=relative_path):
                self.assertFalse(path.is_symlink())

    def test_skill_tree_contains_no_retired_template_or_builder_files(self) -> None:
        for path in SKILL_ROOT.rglob("*"):
            relative = path.relative_to(SKILL_ROOT)
            normalized_parts = {part.lower() for part in relative.parts}
            normalized_name = path.name.lower()
            with self.subTest(path=relative.as_posix()):
                self.assertNotIn(normalized_name, RETIRED_FILE_NAMES)
                self.assertTrue(RETIRED_PATH_PARTS.isdisjoint(normalized_parts))
                self.assertNotIn(path.suffix.lower(), {".html", ".htm"})
                self.assertFalse(
                    any(stem in normalized_name for stem in RETIRED_STEMS)
                )

    def test_playwright_has_no_dependency_import_code_or_positive_invocation(
        self,
    ) -> None:
        self.assertEqual(playwright_violations(SKILL_ROOT), [])

    def test_notices_pin_both_upstreams_and_complete_mit_text(self) -> None:
        self.assertFalse(NOTICE_FILE.is_symlink())
        notice = NOTICE_FILE.read_text(encoding="utf-8")
        for value in UPSTREAM_NOTICE_VALUES:
            with self.subTest(value=value):
                self.assertEqual(notice.count(value), 1)
        self.assertEqual(notice.count("MIT License"), 2)
        self.assertEqual(notice.count(MIT_PERMISSION), 2)
        self.assertEqual(notice.count(MIT_WARRANTY), 2)
        self.assertEqual(
            notice.count(
                "IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE"
            ),
            2,
        )

    def test_anonymous_fixtures_contain_no_personal_tokens(self) -> None:
        self.assertEqual(
            anonymous_fixture_violations(
                ANONYMOUS_FIXTURE_PATHS,
                ANONYMOUS_FIXTURE_FILES,
            ),
            [],
        )


class PackagePolicyMutationTests(unittest.TestCase):
    def test_generic_source_word_does_not_make_playwright_usage_provenance(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            reference = root / "references/rule.md"
            reference.parent.mkdir()
            reference.write_text(
                "来源：该流程使用 Playwright 生成 PDF\n",
                encoding="utf-8",
            )

            self.assertTrue(playwright_violations(root))

    def test_explicit_playwright_prohibition_may_name_forbidden_command(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            reference = root / "references/rule.md"
            reference.parent.mkdir()
            reference.write_text(
                "不得运行 npx playwright test。\n",
                encoding="utf-8",
            )

            self.assertEqual(playwright_violations(root), [])

    def test_reverse_chinese_playwright_prohibition_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            reference = root / "references/rule.md"
            reference.parent.mkdir()
            reference.write_text(
                "Playwright 禁止用于本流程。\n",
                encoding="utf-8",
            )

            self.assertEqual(playwright_violations(root), [])

    def test_precise_upstream_playwright_provenance_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            notice = root / "THIRD_PARTY_NOTICES.md"
            notice.write_text(
                "Provenance: upstream project Easy-Job-Tutor used "
                "Playwright, which is not included in this Skill.\n",
                encoding="utf-8",
            )

            self.assertEqual(playwright_violations(root), [])

    def test_project_name_does_not_mask_positive_playwright_usage(self) -> None:
        mutations = (
            "Easy-Job-Tutor 建议当前 Skill 使用 Playwright",
            "Easy-Job-Tutor: npx playwright test",
        )
        for text in mutations:
            with self.subTest(text=text):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    notice = root / "THIRD_PARTY_NOTICES.md"
                    notice.write_text(text + "\n", encoding="utf-8")

                    self.assertTrue(playwright_violations(root))

    def test_other_tool_exclusion_does_not_validate_playwright_provenance(
        self,
    ) -> None:
        mutations = (
            "Easy-Job-Tutor recommends this Skill use Playwright, "
            "while Pandoc is not included.",
            "Easy-Job-Tutor recommends this Skill use Playwright. "
            "Pandoc is not included.",
        )
        for text in mutations:
            with self.subTest(text=text):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    notice = root / "THIRD_PARTY_NOTICES.md"
                    notice.write_text(text + "\n", encoding="utf-8")

                    self.assertTrue(playwright_violations(root))

    def test_contradictory_current_skill_recommendation_is_not_provenance(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            notice = root / "THIRD_PARTY_NOTICES.md"
            notice.write_text(
                "Easy-Job-Tutor recommends this Skill use Playwright, "
                "while Playwright is not included.\n",
                encoding="utf-8",
            )

            self.assertTrue(playwright_violations(root))

    def test_chinese_current_skill_recommendation_is_not_provenance(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            notice = root / "THIRD_PARTY_NOTICES.md"
            notice.write_text(
                "上游项目 Easy-Job-Tutor 建议当前 Skill 使用 Playwright，"
                "而 Playwright 未纳入本 Skill。\n",
                encoding="utf-8",
            )

            self.assertTrue(playwright_violations(root))

    def test_provenance_cannot_allow_positive_playwright_command(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            notice = root / "THIRD_PARTY_NOTICES.md"
            notice.write_text(
                "Provenance: upstream Easy-Job-Tutor ran "
                "npx playwright test, but Playwright is not included "
                "in this Skill.\n",
                encoding="utf-8",
            )

            self.assertTrue(playwright_violations(root))

    def test_utf8_text_scan_includes_extensionless_and_dependency_files(
        self,
    ) -> None:
        for name in ("run", "Pipfile", "setup.cfg"):
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    (root / name).write_text(
                        "This package uses Playwright.\n",
                        encoding="utf-8",
                    )

                    self.assertTrue(playwright_violations(root))

    def test_non_utf8_skill_file_is_not_silently_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "run").write_bytes(
                "uses Playwright".encode("utf-16")
            )

            self.assertTrue(playwright_violations(root))

    def test_scaffold_policy_detects_path_and_common_markers(self) -> None:
        mutations = (
            ("scripts/example.py", "print('ok')\n"),
            ("references/note.md", "# TODO: replace me\n"),
            ("references/note.md", "This is a placeholder\n"),
        )
        for relative_path, text in mutations:
            with self.subTest(relative_path=relative_path, text=text.strip()):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    path = root / relative_path
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(text, encoding="utf-8")

                    self.assertTrue(scaffold_violations(root))

    def test_generated_policy_detects_build_outputs(self) -> None:
        for relative_path in (
            ".coverage",
            "dist/package.whl",
            "build/generated.py",
            "sample.egg-info/PKG-INFO",
        ):
            with self.subTest(relative_path=relative_path):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    path = root / relative_path
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b"generated")

                    self.assertTrue(generated_artifact_violations(root))

    def test_anonymous_policy_scans_relative_paths_and_casefolded_content(
        self,
    ) -> None:
        mutations = (
            ("候选人甲.json", "{}"),
            ("safe.json", '{"candidate": "Private-User-Token"}'),
            ("safe.json", '{"account": "PRIVATE-ACCOUNT-TOKEN"}'),
            ("safe.json", '{"candidate": "ＰＲＩＶＡＴＥ－ＵＳＥＲ－ＴＯＫＥＮ"}'),
        )
        for relative_path, text in mutations:
            with self.subTest(relative_path=relative_path, text=text):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory) / "fixtures"
                    path = root / relative_path
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(text, encoding="utf-8")

                    self.assertTrue(
                        anonymous_fixture_violations((root,))
                    )


if __name__ == "__main__":
    unittest.main()
