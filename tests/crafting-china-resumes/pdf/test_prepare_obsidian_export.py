from __future__ import annotations

import hashlib
import json
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PREPARER = (
    ROOT
    / "skills/crafting-china-resumes/scripts/prepare_obsidian_export.py"
)
MARKDOWN_BYTES = (
    b"---\n"
    b"cssclasses: [sample-cv]\n"
    b"---\n\n"
    b"# Candidate Name\n\n"
    b"## Education\n"
)
CSS_BYTES = b".sample-cv { color: #123456; }\n"
APPEARANCE_BYTES = (
    b'{"enabledCssSnippets":["sample-cv"],"cssTheme":""}\n'
)


class PrepareObsidianExportTests(unittest.TestCase):
    def _write_valid_inputs(self, root: Path) -> tuple[Path, Path, Path]:
        markdown = root / "candidate.md"
        css = root / "sample-cv.css"
        appearance = root / "appearance.json"
        markdown.write_bytes(MARKDOWN_BYTES)
        css.write_bytes(CSS_BYTES)
        appearance.write_bytes(APPEARANCE_BYTES)
        return markdown, css, appearance

    def _run_preparer(
        self,
        *,
        markdown: Path,
        css: Path,
        appearance: Path,
        workspace: Path,
        target_pdf: Path,
        manifest_path: Path,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(PREPARER),
                "--markdown",
                str(markdown),
                "--css",
                str(css),
                "--appearance",
                str(appearance),
                "--workspace",
                str(workspace),
                "--target-pdf",
                str(target_pdf),
                "--manifest",
                str(manifest_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

    def test_prepares_isolated_vault_and_records_copy_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown, css, appearance = self._write_valid_inputs(root)
            workspace = root / "isolated-vault"
            target_pdf = root / "published.pdf"
            manifest_path = root / "prepare-manifest.json"

            self.assertFalse(workspace.exists())
            self.assertFalse(target_pdf.exists())
            self.assertFalse(manifest_path.exists())

            completed = self._run_preparer(
                markdown=markdown,
                css=css,
                appearance=appearance,
                workspace=workspace,
                target_pdf=target_pdf,
                manifest_path=manifest_path,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(markdown.read_bytes(), MARKDOWN_BYTES)
            self.assertEqual(css.read_bytes(), CSS_BYTES)
            self.assertEqual(appearance.read_bytes(), APPEARANCE_BYTES)
            self.assertFalse(target_pdf.exists())
            self.assertEqual(stat.S_IMODE(workspace.stat().st_mode), 0o700)

            copied_markdown = workspace / markdown.name
            copied_css = workspace / ".obsidian/snippets" / css.name
            copied_appearance = workspace / ".obsidian/appearance.json"
            self.assertEqual(copied_markdown.read_bytes(), MARKDOWN_BYTES)
            self.assertEqual(copied_css.read_bytes(), CSS_BYTES)
            self.assertEqual(copied_appearance.read_bytes(), APPEARANCE_BYTES)

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            expected_copies = {
                "markdown": {
                    "path": str(copied_markdown),
                    "sha256": hashlib.sha256(MARKDOWN_BYTES).hexdigest(),
                },
                "css": {
                    "path": str(copied_css),
                    "sha256": hashlib.sha256(CSS_BYTES).hexdigest(),
                },
                "appearance": {
                    "path": str(copied_appearance),
                    "sha256": hashlib.sha256(APPEARANCE_BYTES).hexdigest(),
                },
            }
            self.assertEqual(manifest["workspace"], str(workspace))
            self.assertEqual(manifest["copies"], expected_copies)
            self.assertEqual(manifest["target_pdf"], str(target_pdf))

            suggested_pdf = Path(manifest["suggested_temporary_pdf"])
            self.assertTrue(suggested_pdf.is_absolute())
            self.assertTrue(
                suggested_pdf.resolve().is_relative_to(root.resolve())
            )
            self.assertEqual(suggested_pdf.suffix, ".pdf")
            self.assertNotEqual(suggested_pdf, target_pdf)
            self.assertFalse(suggested_pdf.exists())

    def test_suggests_temporary_pdf_under_workspace_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown, css, appearance = self._write_valid_inputs(root)
            temporary_parent = root / "temporary-artifacts"
            temporary_parent.mkdir()
            final_parent = root / "final-output"
            final_parent.mkdir()
            workspace = temporary_parent / "isolated-vault"
            target_pdf = final_parent / "published.pdf"
            manifest_path = temporary_parent / "prepare-manifest.json"

            completed = self._run_preparer(
                markdown=markdown,
                css=css,
                appearance=appearance,
                workspace=workspace,
                target_pdf=target_pdf,
                manifest_path=manifest_path,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            suggested_pdf = Path(manifest["suggested_temporary_pdf"])
            self.assertTrue(
                suggested_pdf.resolve().is_relative_to(
                    temporary_parent.resolve()
                )
            )
            self.assertFalse(
                suggested_pdf.resolve().is_relative_to(final_parent.resolve())
            )
            self.assertFalse(suggested_pdf.exists())

    def test_rejects_existing_suggested_temporary_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown, css, appearance = self._write_valid_inputs(root)
            workspace = root / "isolated-vault"
            target_pdf = root / "published.pdf"
            suggested_pdf = root / "published.temporary.pdf"
            suggested_pdf.write_bytes(b"existing-temporary")
            manifest_path = root / "prepare-manifest.json"

            completed = self._run_preparer(
                markdown=markdown,
                css=css,
                appearance=appearance,
                workspace=workspace,
                target_pdf=target_pdf,
                manifest_path=manifest_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(
                completed.stderr,
                "temporary PDF already exists\n",
            )
            self.assertEqual(
                suggested_pdf.read_bytes(),
                b"existing-temporary",
            )
            self.assertFalse(workspace.exists())
            self.assertFalse(manifest_path.exists())
            self.assertFalse(target_pdf.exists())

    def test_rejects_existing_manifest_without_overwriting_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown, css, appearance = self._write_valid_inputs(root)
            workspace = root / "isolated-vault"
            target_pdf = root / "published.pdf"
            manifest_path = root / "prepare-manifest.json"
            manifest_path.write_bytes(b"existing-manifest")

            completed = self._run_preparer(
                markdown=markdown,
                css=css,
                appearance=appearance,
                workspace=workspace,
                target_pdf=target_pdf,
                manifest_path=manifest_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(completed.stderr, "manifest already exists\n")
            self.assertEqual(
                manifest_path.read_bytes(),
                b"existing-manifest",
            )
            self.assertFalse(workspace.exists())
            self.assertFalse(target_pdf.exists())

    def test_rejects_manifest_output_path_aliases(self) -> None:
        for alias in ("workspace", "target", "temporary"):
            with self.subTest(alias=alias):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    markdown, css, appearance = self._write_valid_inputs(root)
                    workspace = root / "isolated-vault"
                    target_pdf = root / "published.pdf"
                    suggested_pdf = root / "published.temporary.pdf"
                    manifest_path = {
                        "workspace": workspace,
                        "target": target_pdf,
                        "temporary": suggested_pdf,
                    }[alias]

                    completed = self._run_preparer(
                        markdown=markdown,
                        css=css,
                        appearance=appearance,
                        workspace=workspace,
                        target_pdf=target_pdf,
                        manifest_path=manifest_path,
                    )

                    self.assertEqual(
                        completed.returncode,
                        1,
                        completed.stderr,
                    )
                    self.assertEqual(completed.stdout, "")
                    self.assertEqual(
                        completed.stderr,
                        "output paths must be distinct\n",
                    )
                    self.assertFalse(workspace.exists())
                    self.assertFalse(target_pdf.exists())
                    self.assertFalse(suggested_pdf.exists())

    def test_rejects_existing_workspace_without_deleting_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown, css, appearance = self._write_valid_inputs(root)
            workspace = root / "isolated-vault"
            workspace.mkdir()
            sentinel = workspace / "keep.bin"
            sentinel.write_bytes(b"keep")
            target_pdf = root / "published.pdf"
            manifest_path = root / "prepare-manifest.json"

            completed = self._run_preparer(
                markdown=markdown,
                css=css,
                appearance=appearance,
                workspace=workspace,
                target_pdf=target_pdf,
                manifest_path=manifest_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(
                completed.stderr,
                "workspace already exists\n",
            )
            self.assertEqual(sentinel.read_bytes(), b"keep")
            self.assertEqual(
                {path.name for path in workspace.iterdir()},
                {"keep.bin"},
            )
            self.assertFalse(manifest_path.exists())
            self.assertFalse(target_pdf.exists())

    def test_rejects_dangling_workspace_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown, css, appearance = self._write_valid_inputs(root)
            missing_destination = root / "missing-vault"
            workspace = root / "isolated-vault"
            workspace.symlink_to(missing_destination)
            target_pdf = root / "published.pdf"
            manifest_path = root / "prepare-manifest.json"

            completed = self._run_preparer(
                markdown=markdown,
                css=css,
                appearance=appearance,
                workspace=workspace,
                target_pdf=target_pdf,
                manifest_path=manifest_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(completed.stderr, "workspace already exists\n")
            self.assertTrue(workspace.is_symlink())
            self.assertFalse(missing_destination.exists())
            self.assertFalse(manifest_path.exists())
            self.assertFalse(target_pdf.exists())

    def test_rejects_existing_target_without_overwriting_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown, css, appearance = self._write_valid_inputs(root)
            workspace = root / "isolated-vault"
            target_pdf = root / "published.pdf"
            target_pdf.write_bytes(b"existing-target")
            manifest_path = root / "prepare-manifest.json"

            completed = self._run_preparer(
                markdown=markdown,
                css=css,
                appearance=appearance,
                workspace=workspace,
                target_pdf=target_pdf,
                manifest_path=manifest_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(
                completed.stderr,
                "target PDF already exists\n",
            )
            self.assertEqual(target_pdf.read_bytes(), b"existing-target")
            self.assertFalse(workspace.exists())
            self.assertFalse(manifest_path.exists())

    def test_rejects_dangling_target_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown, css, appearance = self._write_valid_inputs(root)
            workspace = root / "isolated-vault"
            missing_destination = root / "missing-output.pdf"
            target_pdf = root / "published.pdf"
            target_pdf.symlink_to(missing_destination)
            manifest_path = root / "prepare-manifest.json"

            completed = self._run_preparer(
                markdown=markdown,
                css=css,
                appearance=appearance,
                workspace=workspace,
                target_pdf=target_pdf,
                manifest_path=manifest_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(completed.stderr, "target PDF already exists\n")
            self.assertTrue(target_pdf.is_symlink())
            self.assertFalse(missing_destination.exists())
            self.assertFalse(workspace.exists())
            self.assertFalse(manifest_path.exists())

    def test_rejects_symlink_source_inputs(self) -> None:
        for argument_name in ("markdown", "css", "appearance"):
            with self.subTest(argument_name=argument_name):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    markdown, css, appearance = self._write_valid_inputs(root)
                    inputs = {
                        "markdown": markdown,
                        "css": css,
                        "appearance": appearance,
                    }
                    real_source = inputs[argument_name]
                    symlink_source = root / f"{argument_name}-link{real_source.suffix}"
                    symlink_source.symlink_to(real_source)
                    inputs[argument_name] = symlink_source
                    workspace = root / "isolated-vault"
                    target_pdf = root / "published.pdf"
                    manifest_path = root / "prepare-manifest.json"

                    completed = self._run_preparer(
                        markdown=inputs["markdown"],
                        css=inputs["css"],
                        appearance=inputs["appearance"],
                        workspace=workspace,
                        target_pdf=target_pdf,
                        manifest_path=manifest_path,
                    )

                    self.assertEqual(
                        completed.returncode,
                        1,
                        completed.stderr,
                    )
                    self.assertEqual(completed.stdout, "")
                    self.assertEqual(
                        completed.stderr,
                        f"{argument_name} input must not be a symlink\n",
                    )
                    self.assertFalse(workspace.exists())
                    self.assertFalse(manifest_path.exists())
                    self.assertFalse(target_pdf.exists())

    def test_rejects_markdown_missing_css_stem_class(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown, css, appearance = self._write_valid_inputs(root)
            markdown.write_bytes(
                b"---\n"
                b"cssclasses: [other-cv]\n"
                b"---\n\n"
                b"# Candidate Name\n"
            )
            workspace = root / "isolated-vault"
            target_pdf = root / "published.pdf"
            manifest_path = root / "prepare-manifest.json"

            completed = self._run_preparer(
                markdown=markdown,
                css=css,
                appearance=appearance,
                workspace=workspace,
                target_pdf=target_pdf,
                manifest_path=manifest_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(
                completed.stderr,
                "markdown CSS class is not enabled\n",
            )
            self.assertFalse(workspace.exists())
            self.assertFalse(manifest_path.exists())
            self.assertFalse(target_pdf.exists())

    def test_rejects_appearance_missing_enabled_css_stem(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown, css, appearance = self._write_valid_inputs(root)
            appearance.write_bytes(
                b'{"enabledCssSnippets":["other-cv"],"cssTheme":""}\n'
            )
            workspace = root / "isolated-vault"
            target_pdf = root / "published.pdf"
            manifest_path = root / "prepare-manifest.json"

            completed = self._run_preparer(
                markdown=markdown,
                css=css,
                appearance=appearance,
                workspace=workspace,
                target_pdf=target_pdf,
                manifest_path=manifest_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(
                completed.stderr,
                "appearance CSS snippet is not enabled\n",
            )
            self.assertFalse(workspace.exists())
            self.assertFalse(manifest_path.exists())
            self.assertFalse(target_pdf.exists())

    def test_reports_invalid_appearance_root_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown, css, appearance = self._write_valid_inputs(root)
            appearance.write_text("[]\n", encoding="utf-8")
            workspace = root / "isolated-vault"
            target_pdf = root / "published.pdf"
            manifest_path = root / "prepare-manifest.json"

            completed = self._run_preparer(
                markdown=markdown,
                css=css,
                appearance=appearance,
                workspace=workspace,
                target_pdf=target_pdf,
                manifest_path=manifest_path,
            )

            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(completed.stderr, "unable to prepare export\n")
            self.assertNotIn(str(root), completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)
            self.assertFalse(workspace.exists())
            self.assertFalse(manifest_path.exists())
            self.assertFalse(target_pdf.exists())

    def test_rejects_non_list_enabled_css_snippets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown, css, appearance = self._write_valid_inputs(root)
            appearance.write_text(
                json.dumps(
                    {"enabledCssSnippets": "prefix-sample-cv-suffix"}
                ),
                encoding="utf-8",
            )
            workspace = root / "isolated-vault"
            target_pdf = root / "published.pdf"
            manifest_path = root / "prepare-manifest.json"

            completed = self._run_preparer(
                markdown=markdown,
                css=css,
                appearance=appearance,
                workspace=workspace,
                target_pdf=target_pdf,
                manifest_path=manifest_path,
            )

            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(completed.stderr, "unable to prepare export\n")
            self.assertFalse(workspace.exists())
            self.assertFalse(manifest_path.exists())
            self.assertFalse(target_pdf.exists())

    def test_does_not_emit_contact_text(self) -> None:
        phone = "555-0100"
        email = "candidate.redaction@example.test"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown, css, appearance = self._write_valid_inputs(root)
            markdown.write_text(
                "---\n"
                "cssclasses: [sample-cv]\n"
                "---\n\n"
                "# Candidate Name\n\n"
                f"{phone} | {email}\n",
                encoding="utf-8",
            )
            workspace = root / "isolated-vault"
            target_pdf = root / "published.pdf"
            manifest_path = root / "prepare-manifest.json"

            completed = self._run_preparer(
                markdown=markdown,
                css=css,
                appearance=appearance,
                workspace=workspace,
                target_pdf=target_pdf,
                manifest_path=manifest_path,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            emitted = (
                manifest_path.read_text(encoding="utf-8")
                + completed.stdout
                + completed.stderr
            )
            for secret in (phone, email):
                self.assertNotIn(secret, emitted)
            self.assertFalse(target_pdf.exists())

    def test_reports_runtime_error_without_traceback_or_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _, css, appearance = self._write_valid_inputs(root)
            missing_markdown = root / "private-candidate-missing.md"
            workspace = root / "isolated-vault"
            target_pdf = root / "published.pdf"
            manifest_path = root / "prepare-manifest.json"

            completed = self._run_preparer(
                markdown=missing_markdown,
                css=css,
                appearance=appearance,
                workspace=workspace,
                target_pdf=target_pdf,
                manifest_path=manifest_path,
            )

            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(completed.stderr, "unable to prepare export\n")
            self.assertNotIn(str(root), completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)
            self.assertFalse(workspace.exists())
            self.assertFalse(manifest_path.exists())
            self.assertFalse(target_pdf.exists())


if __name__ == "__main__":
    unittest.main()
