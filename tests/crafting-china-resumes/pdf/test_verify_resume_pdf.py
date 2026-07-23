from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from reportlab.lib.pagesizes import A4, LETTER, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, NameObject, NumberObject


ROOT = Path(__file__).resolve().parents[3]
VERIFIER = ROOT / "skills/crafting-china-resumes/scripts/verify_resume_pdf.py"
EXPECTATION = (
    ROOT / "tests/crafting-china-resumes/pdf/fixtures/expected.json"
)
BASE_MARKERS = ("Candidate Name", "Education", "Experience")


class VerifyResumePdfTests(unittest.TestCase):
    def _write_pdf(
        self,
        path: Path,
        *,
        pagesize: tuple[float, float] = A4,
        pages: tuple[tuple[str, ...], ...] = (BASE_MARKERS,),
    ) -> None:
        document = canvas.Canvas(str(path), pagesize=pagesize)
        for markers in pages:
            y_position = 780
            for marker in markers:
                document.drawString(72, y_position, marker)
                y_position -= 30
            document.showPage()
        document.save()

    def _write_expectation(
        self,
        root: Path,
        **overrides: object,
    ) -> Path:
        expectation = json.loads(EXPECTATION.read_text(encoding="utf-8"))
        expectation.update(overrides)
        path = root / "expected.json"
        path.write_text(
            json.dumps(expectation, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def _run_verifier(
        self,
        *,
        pdf_path: Path,
        report_path: Path,
        expectation_path: Path = EXPECTATION,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(VERIFIER),
                "--pdf",
                str(pdf_path),
                "--expect",
                str(expectation_path),
                "--report",
                str(report_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

    def _read_report(self, path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_accepts_a4_portrait_pdf_with_required_ascii_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            report_path = root / "verification-report.json"
            self._write_pdf(pdf_path)

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["page_count"], 1)
            self.assertEqual(report["page_size"], "A4")
            self.assertEqual(report["orientation"], "portrait")
            self.assertEqual(report["required_text"]["missing"], 0)
            self.assertEqual(report["forbidden_text"]["found"], 0)

    def test_accepts_nfkc_equivalent_extracted_text_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            report_path = root / "verification-report.json"
            expectation_path = self._write_expectation(
                root,
                required_text=["项目经验"],
                forbidden_text=[],
            )
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            document = canvas.Canvas(str(pdf_path), pagesize=A4)
            document.setFont("STSong-Light", 12)
            document.drawString(72, 780, "项⽬经验")
            document.save()

            extracted_text = PdfReader(pdf_path).pages[0].extract_text()
            self.assertIn("项⽬经验", extracted_text)

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
                expectation_path=expectation_path,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["required_text"]["missing"], 0)
            self.assertEqual(report["findings"], [])

    def test_accepts_lapis_non_decomposing_cjk_radical_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            report_path = root / "verification-report.json"
            expectation_path = self._write_expectation(
                root,
                required_text=["技能特长"],
                forbidden_text=[],
            )
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            document = canvas.Canvas(str(pdf_path), pagesize=A4)
            document.setFont("STSong-Light", 12)
            document.drawString(72, 780, "技能特⻓")
            document.save()

            extracted_text = PdfReader(pdf_path).pages[0].extract_text()
            self.assertIn("技能特⻓", extracted_text)

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
                expectation_path=expectation_path,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["required_text"]["missing"], 0)
            self.assertEqual(report["findings"], [])

    def test_accepts_every_mapped_non_decomposing_cjk_radical(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            report_path = root / "verification-report.json"
            expectation_path = self._write_expectation(
                root,
                required_text=["民角长"],
                forbidden_text=[],
            )
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            document = canvas.Canvas(str(pdf_path), pagesize=A4)
            document.setFont("STSong-Light", 12)
            document.drawString(72, 780, "⺠⻆⻓")
            document.save()

            extracted_text = PdfReader(pdf_path).pages[0].extract_text()
            self.assertIn("⺠⻆⻓", extracted_text)

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
                expectation_path=expectation_path,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["required_text"]["missing"], 0)
            self.assertEqual(report["findings"], [])

    def test_rejects_nfkc_equivalent_forbidden_text_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            report_path = root / "verification-report.json"
            expectation_path = self._write_expectation(
                root,
                required_text=[],
                forbidden_text=["项目经验"],
            )
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            document = canvas.Canvas(str(pdf_path), pagesize=A4)
            document.setFont("STSong-Light", 12)
            document.drawString(72, 780, "项⽬经验")
            document.save()

            extracted_text = PdfReader(pdf_path).pages[0].extract_text()
            self.assertIn("项⽬经验", extracted_text)

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
                expectation_path=expectation_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["forbidden_text"]["found"], 1)
            self.assertEqual(report["findings"], ["forbidden_text_present"])

    def test_rejects_mapped_radical_forbidden_text_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            report_path = root / "verification-report.json"
            expectation_path = self._write_expectation(
                root,
                required_text=[],
                forbidden_text=["技能特长"],
            )
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            document = canvas.Canvas(str(pdf_path), pagesize=A4)
            document.setFont("STSong-Light", 12)
            document.drawString(72, 780, "技能特⻓")
            document.save()

            extracted_text = PdfReader(pdf_path).pages[0].extract_text()
            self.assertIn("技能特⻓", extracted_text)

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
                expectation_path=expectation_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["forbidden_text"]["found"], 1)
            self.assertEqual(report["findings"], ["forbidden_text_present"])

    def test_reports_error_when_pdf_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "missing-candidate.pdf"
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
            )

            self.assertEqual(completed.returncode, 2, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "error")
            self.assertIsNone(report["page_count"])
            self.assertEqual(report["findings"], ["pdf_missing"])

    def test_reports_error_when_pdf_is_unreadable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            pdf_path.write_bytes(b"not a pdf")
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
            )

            self.assertEqual(completed.returncode, 2, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "error")
            self.assertEqual(
                report["pdf_sha256"],
                hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
            )
            self.assertIsNone(report["page_count"])
            self.assertEqual(report["findings"], ["pdf_unreadable"])

    def test_reports_error_when_pdf_bytes_cannot_be_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "private-unreadable-candidate.pdf"
            self._write_pdf(pdf_path)
            pdf_path.chmod(0)
            report_path = root / "verification-report.json"

            try:
                completed = self._run_verifier(
                    pdf_path=pdf_path,
                    report_path=report_path,
                )
            finally:
                pdf_path.chmod(0o600)

            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertEqual(completed.stderr, "")
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "error")
            self.assertIsNone(report["pdf_sha256"])
            self.assertEqual(report["findings"], ["pdf_unreadable"])
            emitted = completed.stdout + completed.stderr
            self.assertNotIn(str(root), emitted)
            self.assertNotIn("private-unreadable-candidate", emitted)
            self.assertNotIn("Traceback", emitted)

    def test_reports_encrypted_pdf_as_unreadable_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_pdf = root / "source.pdf"
            pdf_path = root / "private-encrypted-candidate.pdf"
            self._write_pdf(source_pdf)
            reader = PdfReader(source_pdf)
            writer = PdfWriter()
            writer.append_pages_from_reader(reader)
            writer.encrypt("secret-password")
            with pdf_path.open("wb") as pdf_file:
                writer.write(pdf_file)
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
            )

            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertEqual(completed.stderr, "")
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "error")
            self.assertEqual(
                report["pdf_sha256"],
                hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(report["findings"], ["pdf_unreadable"])
            emitted = completed.stdout + completed.stderr
            self.assertNotIn(str(root), emitted)
            self.assertNotIn("private-encrypted-candidate", emitted)
            self.assertNotIn("Traceback", emitted)

    def test_reports_malformed_page_geometry_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_pdf = root / "source.pdf"
            pdf_path = root / "private-malformed-candidate.pdf"
            self._write_pdf(source_pdf)
            reader = PdfReader(source_pdf)
            page = reader.pages[0]
            page[NameObject("/MediaBox")] = ArrayObject(
                [NumberObject(0), NumberObject(0), NumberObject(595)]
            )
            writer = PdfWriter()
            writer.add_page(page)
            with pdf_path.open("wb") as pdf_file:
                writer.write(pdf_file)
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
            )

            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertEqual(completed.stderr, "")
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "error")
            self.assertEqual(
                report["pdf_sha256"],
                hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(report["findings"], ["pdf_unreadable"])
            emitted = completed.stdout + completed.stderr
            self.assertNotIn(str(root), emitted)
            self.assertNotIn("private-malformed-candidate", emitted)
            self.assertNotIn("Traceback", emitted)

    def test_fails_when_required_text_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            self._write_pdf(
                pdf_path,
                pages=(("Candidate Name", "Education"),),
            )
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["required_text"]["missing"], 1)
            self.assertEqual(report["forbidden_text"]["found"], 0)
            self.assertEqual(report["findings"], ["required_text_missing"])

    def test_fails_when_forbidden_text_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            self._write_pdf(
                pdf_path,
                pages=(BASE_MARKERS + ("cssclasses",),),
            )
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["required_text"]["missing"], 0)
            self.assertEqual(report["forbidden_text"]["found"], 1)
            self.assertEqual(report["findings"], ["forbidden_text_present"])

    def test_rejects_exact_forbidden_substring_before_normalization(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            document = canvas.Canvas(str(pdf_path), pagesize=A4)
            document.setFont("STSong-Light", 12)
            document.drawString(72, 780, "cssclasses\u0301")
            document.save()
            expectation_path = self._write_expectation(
                root,
                required_text=[],
                forbidden_text=["cssclasses"],
            )
            report_path = root / "verification-report.json"

            extracted_text = PdfReader(pdf_path).pages[0].extract_text()
            self.assertIn("cssclasses\u0301", extracted_text)

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
                expectation_path=expectation_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["forbidden_text"]["found"], 1)
            self.assertEqual(report["findings"], ["forbidden_text_present"])

    def test_fails_when_page_size_is_not_a4(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            self._write_pdf(pdf_path, pagesize=LETTER)
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "fail")
            self.assertNotEqual(report["page_size"], "A4")
            self.assertEqual(report["orientation"], "portrait")
            self.assertEqual(report["findings"], ["page_size_mismatch"])

    def test_fails_when_any_page_size_is_not_a4(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=A4[0], height=A4[1])
            writer.add_blank_page(width=LETTER[0], height=LETTER[1])
            with pdf_path.open("wb") as pdf_file:
                writer.write(pdf_file)
            expectation_path = self._write_expectation(
                root,
                required_text=[],
                forbidden_text=[],
            )
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
                expectation_path=expectation_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["page_size"], "mixed")
            self.assertEqual(
                report["findings"],
                ["page_size_mismatch", "empty_extracted_text"],
            )

    def test_fails_when_orientation_is_landscape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            self._write_pdf(pdf_path, pagesize=landscape(A4))
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["page_size"], "A4")
            self.assertEqual(report["orientation"], "landscape")
            self.assertEqual(report["findings"], ["orientation_mismatch"])

    def test_fails_when_page_rotation_makes_display_landscape(self) -> None:
        for rotation in (90, 270):
            with self.subTest(rotation=rotation):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    source_pdf = root / "source.pdf"
                    pdf_path = root / "candidate.pdf"
                    self._write_pdf(source_pdf)
                    reader = PdfReader(source_pdf)
                    writer = PdfWriter()
                    page = reader.pages[0]
                    page.rotate(rotation)
                    writer.add_page(page)
                    with pdf_path.open("wb") as pdf_file:
                        writer.write(pdf_file)
                    report_path = root / "verification-report.json"

                    completed = self._run_verifier(
                        pdf_path=pdf_path,
                        report_path=report_path,
                    )

                    self.assertEqual(
                        completed.returncode,
                        1,
                        completed.stderr,
                    )
                    report = self._read_report(report_path)
                    self.assertEqual(report["page_size"], "A4")
                    self.assertEqual(report["orientation"], "landscape")
                    self.assertEqual(
                        report["findings"],
                        ["orientation_mismatch"],
                    )

    def test_fails_when_any_page_orientation_is_landscape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=A4[0], height=A4[1])
            writer.add_blank_page(width=A4[1], height=A4[0])
            with pdf_path.open("wb") as pdf_file:
                writer.write(pdf_file)
            expectation_path = self._write_expectation(
                root,
                required_text=[],
                forbidden_text=[],
            )
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
                expectation_path=expectation_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["page_size"], "A4")
            self.assertEqual(report["orientation"], "mixed")
            self.assertEqual(
                report["findings"],
                ["orientation_mismatch", "empty_extracted_text"],
            )

    def test_fails_when_page_count_is_out_of_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            self._write_pdf(
                pdf_path,
                pages=(
                    BASE_MARKERS,
                    ("Continuation 2",),
                    ("Continuation 3",),
                    ("Continuation 4",),
                ),
            )
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["page_count"], 4)
            self.assertEqual(report["findings"], ["page_count_out_of_bounds"])

    def test_fails_when_pdf_has_no_pages(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            writer = PdfWriter()
            with pdf_path.open("wb") as pdf_file:
                writer.write(pdf_file)
            expectation_path = self._write_expectation(
                root,
                required_text=[],
                forbidden_text=[],
            )
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
                expectation_path=expectation_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["page_count"], 0)
            self.assertIsNone(report["page_size"])
            self.assertIsNone(report["orientation"])
            self.assertEqual(
                report["findings"],
                ["page_count_out_of_bounds", "empty_extracted_text"],
            )

    def test_fails_when_extracted_text_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            self._write_pdf(pdf_path, pages=((),))
            expectation_path = self._write_expectation(
                root,
                required_text=[],
                forbidden_text=[],
            )
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
                expectation_path=expectation_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["required_text"]["missing"], 0)
            self.assertEqual(report["forbidden_text"]["found"], 0)
            self.assertEqual(report["findings"], ["empty_extracted_text"])

    def test_writes_exact_redacted_report_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            self._write_pdf(pdf_path)
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = self._read_report(report_path)
            self.assertEqual(
                set(report),
                {
                    "status",
                    "pdf_sha256",
                    "page_count",
                    "page_size",
                    "orientation",
                    "required_text",
                    "forbidden_text",
                    "findings",
                },
            )
            self.assertEqual(
                report["pdf_sha256"],
                hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                report["required_text"],
                {"expected": 3, "missing": 0},
            )
            self.assertEqual(
                report["forbidden_text"],
                {"expected": 4, "found": 0},
            )
            self.assertEqual(report["findings"], [])

    def test_prints_only_redacted_status_and_counts(self) -> None:
        required_secret = "555-0100"
        forbidden_secret = "private@example.invalid"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "secret-file-marker.pdf"
            self._write_pdf(
                pdf_path,
                pages=((required_secret, forbidden_secret),),
            )
            expectation_path = self._write_expectation(
                root,
                required_text=[required_secret],
                forbidden_text=[forbidden_secret],
            )
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
                expectation_path=expectation_path,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertEqual(completed.stderr, "")
            self.assertEqual(completed.stdout.count("\n"), 1)
            self.assertEqual(
                json.loads(completed.stdout),
                {
                    "status": "fail",
                    "page_count": 1,
                    "required_missing": 0,
                    "forbidden_found": 1,
                    "finding_count": 1,
                },
            )
            emitted = completed.stdout + completed.stderr
            for secret in (
                required_secret,
                forbidden_secret,
                "secret-file-marker",
                str(root),
            ):
                self.assertNotIn(secret, emitted)

    def test_reports_error_when_expectation_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            self._write_pdf(pdf_path)
            expectation_path = root / "private-invalid-expectation.json"
            expectation_path.write_text("not json", encoding="utf-8")
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
                expectation_path=expectation_path,
            )

            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertEqual(completed.stderr, "")
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "error")
            self.assertEqual(report["findings"], ["expectation_unreadable"])
            self.assertNotIn(str(root), completed.stdout)
            self.assertNotIn("private-invalid-expectation", completed.stdout)

    def test_reports_error_when_expectation_schema_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            self._write_pdf(pdf_path)
            expectation_path = self._write_expectation(
                root,
                required_text="Candidate Name",
            )
            report_path = root / "verification-report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
                expectation_path=expectation_path,
            )

            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertEqual(completed.stderr, "")
            report = self._read_report(report_path)
            self.assertEqual(report["status"], "error")
            self.assertEqual(report["findings"], ["expectation_invalid"])

    def test_reports_runtime_error_without_traceback_or_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            self._write_pdf(pdf_path)
            report_path = root / "missing-private-parent" / "report.json"

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
            )

            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(completed.stderr, "unable to verify PDF\n")
            self.assertNotIn(str(root), completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)
            self.assertFalse(report_path.exists())

    def test_does_not_overwrite_an_existing_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "candidate.pdf"
            self._write_pdf(pdf_path)
            report_path = root / "private-existing-report.json"
            report_path.write_bytes(b"existing-report")

            completed = self._run_verifier(
                pdf_path=pdf_path,
                report_path=report_path,
            )

            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(completed.stderr, "unable to verify PDF\n")
            self.assertEqual(report_path.read_bytes(), b"existing-report")
            self.assertNotIn(str(root), completed.stderr)
            self.assertNotIn("private-existing-report", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)


if __name__ == "__main__":
    unittest.main()
