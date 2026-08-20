from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RESOLVER = (
    ROOT / "tests/crafting-resumes/behavior/commit_equivalence.py"
)
METADATA_VALIDATOR = (
    ROOT / "tests/crafting-resumes/behavior/validate_git_metadata.py"
)
MAPPING_RELATIVE = Path(
    "tests/crafting-resumes/behavior/provenance/"
    "commit-equivalence.json"
)
ORIGINAL_COMMIT = "48d7110a6de4273dcb3e64bffec1f887d16f5167"
PUBLISHED_COMMIT = "91ea918de813d3a1f3f400682af96afa5055e0f7"
COMMIT_TREE_OID = "9b336cf6baa55a3987ef1adaef668daf24655062"
SKILL_TREE_OID = "23ea85ebb907417fe484a0f793550bda57304c64"
NOREPLY_EMAIL = "juanlou1217@users.noreply.github.com"


class CommitEquivalenceTests(unittest.TestCase):
    def run_command(
        self,
        arguments: list[str],
        *,
        cwd: Path,
        input_text: str | None = None,
        env: dict[str, str] | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            arguments,
            cwd=cwd,
            input=input_text,
            capture_output=True,
            text=True,
            env=env,
            check=False,
            timeout=30,
        )
        if check and completed.returncode != 0:
            self.fail(
                f"command failed ({completed.returncode}): "
                f"{arguments}\n{completed.stdout}\n{completed.stderr}"
            )
        return completed

    def git(
        self,
        root: Path,
        *arguments: str,
        input_text: str | None = None,
        env: dict[str, str] | None = None,
    ) -> str:
        return self.run_command(
            ["git", "-C", str(root), *arguments],
            cwd=root,
            input_text=input_text,
            env=env,
        ).stdout.strip()

    def commit_environment(
        self, email: str = NOREPLY_EMAIL
    ) -> dict[str, str]:
        environment = os.environ.copy()
        environment.update(
            {
                "GIT_AUTHOR_NAME": "Fixture Author",
                "GIT_AUTHOR_EMAIL": email,
                "GIT_COMMITTER_NAME": "Fixture Committer",
                "GIT_COMMITTER_EMAIL": email,
            }
        )
        return environment

    def build_rewrite_fixture(
        self, root: Path
    ) -> tuple[str, str, str]:
        self.run_command(["git", "init", "-q", str(root)], cwd=root.parent)
        self.git(root, "config", "user.name", "Fixture")
        self.git(root, "config", "user.email", NOREPLY_EMAIL)
        self.git(root, "config", "commit.gpgsign", "false")

        (root / "README.md").write_text("base\n", encoding="utf-8")
        self.git(root, "add", "README.md")
        self.git(root, "commit", "-q", "-m", "base")
        base_commit = self.git(root, "rev-parse", "HEAD")

        required_paths = (
            Path("skills/crafting-resumes/SKILL.md"),
            Path(
                "skills/crafting-resumes/references/"
                "professional-packaging-and-keywords.md"
            ),
            Path(
                "skills/crafting-resumes/references/"
                "evidence-and-truthfulness.md"
            ),
        )
        for relative_path in required_paths:
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture Skill\n", encoding="utf-8")
        self.git(root, "add", "skills")
        self.run_command(
            ["git", "-C", str(root), "commit", "-q", "-m", "original"],
            cwd=root,
            env=self.commit_environment("private@example.invalid"),
        )
        original_commit = self.git(root, "rev-parse", "HEAD")
        commit_tree = self.git(
            root, "rev-parse", f"{original_commit}^{{tree}}"
        )
        skill_tree = self.git(
            root,
            "rev-parse",
            f"{original_commit}:skills/crafting-resumes",
        )

        published_commit = self.run_command(
            [
                "git",
                "-C",
                str(root),
                "commit-tree",
                commit_tree,
                "-p",
                base_commit,
            ],
            cwd=root,
            input_text="published equivalent\n",
            env=self.commit_environment(),
        ).stdout.strip()
        self.git(root, "branch", "published", published_commit)
        self.git(root, "checkout", "-q", "published")

        mapping_path = root / MAPPING_RELATIVE
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        mapping_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": (
                        "tree-identical-pre-publication-history-rewrite"
                    ),
                    "original_commit": original_commit,
                    "published_commit": published_commit,
                    "commit_tree_oid": commit_tree,
                    "skill_path": "skills/crafting-resumes",
                    "skill_tree_oid": skill_tree,
                    "reason": (
                        "Before the first public push, history was rewritten "
                        "to remove a private email; commit metadata, ancestry, "
                        "and signatures changed, while the tracked full tree "
                        "and Skill subtree remain byte-identical."
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.git(root, "add", str(MAPPING_RELATIVE))
        self.git(root, "commit", "-q", "-m", "record equivalence")
        return original_commit, published_commit, commit_tree

    def run_resolver(
        self, root: Path, commit: str
    ) -> subprocess.CompletedProcess[str]:
        return self.run_command(
            [sys.executable, "-B", str(RESOLVER), str(root), commit],
            cwd=ROOT,
            check=False,
        )

    def run_metadata_validator(
        self, root: Path
    ) -> subprocess.CompletedProcess[str]:
        return self.run_command(
            [
                sys.executable,
                "-B",
                str(METADATA_VALIDATOR),
                str(root),
            ],
            cwd=ROOT,
            check=False,
        )

    def test_repository_mapping_resolves_old_receipt_without_rebinding(
        self,
    ) -> None:
        mapping = json.loads(
            (ROOT / MAPPING_RELATIVE).read_text(encoding="utf-8")
        )
        self.assertEqual(mapping["original_commit"], ORIGINAL_COMMIT)
        self.assertEqual(mapping["published_commit"], PUBLISHED_COMMIT)
        self.assertEqual(mapping["commit_tree_oid"], COMMIT_TREE_OID)
        self.assertEqual(mapping["skill_tree_oid"], SKILL_TREE_OID)

        completed = self.run_resolver(ROOT, ORIGINAL_COMMIT)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), PUBLISHED_COMMIT)

    def test_fresh_clone_does_not_need_unreachable_original_object(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            source = temporary_root / "source"
            source.mkdir()
            original, published, _ = self.build_rewrite_fixture(source)
            self.assertEqual(
                self.run_resolver(source, original).stdout.strip(),
                published,
            )

            clone = temporary_root / "clone"
            self.run_command(
                [
                    "git",
                    "clone",
                    "-q",
                    "--no-local",
                    "--single-branch",
                    "--branch",
                    "published",
                    str(source),
                    str(clone),
                ],
                cwd=temporary_root,
            )
            original_probe = self.run_command(
                [
                    "git",
                    "-C",
                    str(clone),
                    "cat-file",
                    "-e",
                    f"{original}^{{commit}}",
                ],
                cwd=clone,
                check=False,
            )
            self.assertNotEqual(original_probe.returncode, 0)

            resolved = self.run_resolver(clone, original)

            self.assertEqual(resolved.returncode, 0, resolved.stderr)
            self.assertEqual(resolved.stdout.strip(), published)

    def test_mapping_rejects_wrong_published_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original, _, _ = self.build_rewrite_fixture(root)
            mapping_path = root / MAPPING_RELATIVE
            mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
            mapping["commit_tree_oid"] = "0" * 40
            mapping_path.write_text(
                json.dumps(mapping, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = self.run_resolver(root, original)

            self.assertEqual(completed.returncode, 1)
            self.assertIn("published commit tree does not match", completed.stderr)

    def test_workflow_fetches_full_history_for_equivalence_gate(
        self,
    ) -> None:
        workflow = yaml.safe_load(
            (ROOT / ".github/workflows/validate.yml").read_text(
                encoding="utf-8"
            )
        )
        checkout_steps = [
            step
            for step in workflow["jobs"]["test"]["steps"]
            if step.get("uses") == "actions/checkout@v4"
        ]
        self.assertEqual(len(checkout_steps), 1)
        self.assertEqual(
            checkout_steps[0].get("with", {}).get("fetch-depth"),
            0,
        )
        self.assertEqual(
            checkout_steps[0].get("with", {}).get("ref"),
            "${{ github.event.pull_request.head.sha || github.sha }}",
        )
        metadata_steps = [
            step
            for step in workflow["jobs"]["test"]["steps"]
            if step.get("name") == "Validate reachable Git metadata"
        ]
        self.assertEqual(len(metadata_steps), 1)
        self.assertEqual(
            metadata_steps[0].get("run"),
            (
                "python -B tests/crafting-resumes/behavior/"
                "validate_git_metadata.py ."
            ),
        )

    def test_reachable_repository_metadata_uses_noreply_addresses(
        self,
    ) -> None:
        completed = self.run_metadata_validator(ROOT)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Validated reachable Git metadata:", completed.stdout)

    def test_metadata_validator_rejects_reachable_private_email(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.run_command(["git", "init", "-q", str(root)], cwd=root.parent)
            self.git(root, "config", "commit.gpgsign", "false")
            (root / "README.md").write_text("fixture\n", encoding="utf-8")
            self.git(root, "add", "README.md")
            self.run_command(
                ["git", "-C", str(root), "commit", "-q", "-m", "private"],
                cwd=root,
                env=self.commit_environment("private@example.invalid"),
            )

            completed = self.run_metadata_validator(root)

            self.assertEqual(completed.returncode, 1)
            self.assertIn("must use a GitHub noreply address", completed.stderr)


if __name__ == "__main__":
    unittest.main()
