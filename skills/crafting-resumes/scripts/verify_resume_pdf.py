from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import sys
import unicodedata
from pathlib import Path

from pypdf import PdfReader


A4_WIDTH = 595.2756
A4_HEIGHT = 841.8898
LAPIS_NON_DECOMPOSING_RADICALS = str.maketrans(
    {"⺠": "民", "⻆": "角", "⻓": "长"}
)


def normalize_text_marker(text: str) -> str:
    return unicodedata.normalize("NFKC", text).translate(
        LAPIS_NON_DECOMPOSING_RADICALS
    )


def write_report(path: Path, report: dict[str, object]) -> None:
    with path.open("x", encoding="utf-8") as report_file:
        report_file.write(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        )


def finish(
    report_path: Path,
    report: dict[str, object],
    exit_code: int,
) -> int:
    write_report(report_path, report)
    required_text = report["required_text"]
    forbidden_text = report["forbidden_text"]
    findings = report["findings"]
    summary = {
        "status": report["status"],
        "page_count": report["page_count"],
        "required_missing": required_text["missing"],
        "forbidden_found": forbidden_text["found"],
        "finding_count": len(findings),
    }
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True))
    return exit_code


def error_report(
    expectation: dict[str, object],
    finding: str,
    pdf_sha256: str | None = None,
) -> dict[str, object]:
    return {
        "status": "error",
        "pdf_sha256": pdf_sha256,
        "page_count": None,
        "page_size": None,
        "orientation": None,
        "required_text": {
            "expected": len(expectation["required_text"]),
            "missing": None,
        },
        "forbidden_text": {
            "expected": len(expectation["forbidden_text"]),
            "found": None,
        },
        "findings": [finding],
    }


def unavailable_report(finding: str) -> dict[str, object]:
    return {
        "status": "error",
        "pdf_sha256": None,
        "page_count": None,
        "page_size": None,
        "orientation": None,
        "required_text": {"expected": None, "missing": None},
        "forbidden_text": {"expected": None, "found": None},
        "findings": [finding],
    }


def expectation_is_valid(expectation: object) -> bool:
    if not isinstance(expectation, dict):
        return False
    required_text = expectation.get("required_text")
    forbidden_text = expectation.get("forbidden_text")
    min_pages = expectation.get("min_pages")
    max_pages = expectation.get("max_pages")
    return (
        isinstance(required_text, list)
        and all(isinstance(item, str) and item for item in required_text)
        and isinstance(forbidden_text, list)
        and all(isinstance(item, str) and item for item in forbidden_text)
        and isinstance(min_pages, int)
        and not isinstance(min_pages, bool)
        and isinstance(max_pages, int)
        and not isinstance(max_pages, bool)
        and 0 <= min_pages <= max_pages
        and expectation.get("page_size") == "A4"
        and expectation.get("orientation") == "portrait"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--expect", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    arguments = parser.parse_args()

    try:
        expectation = json.loads(
            arguments.expect.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError):
        return finish(
            arguments.report,
            unavailable_report("expectation_unreadable"),
            2,
        )
    if not expectation_is_valid(expectation):
        return finish(
            arguments.report,
            unavailable_report("expectation_invalid"),
            2,
        )
    if not arguments.pdf.is_file():
        return finish(
            arguments.report,
            error_report(expectation, "pdf_missing"),
            2,
        )

    logging.getLogger("pypdf").setLevel(logging.CRITICAL)
    try:
        pdf_bytes = arguments.pdf.read_bytes()
    except OSError:
        return finish(
            arguments.report,
            error_report(expectation, "pdf_unreadable"),
            2,
        )
    pdf_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = list(reader.pages)
        extracted_text = "\n".join(
            page.extract_text() or "" for page in pages
        )
        page_count = len(pages)

        if page_count:
            page_sizes: list[str] = []
            orientations: list[str] = []
            for page in pages:
                width = float(page.mediabox.width)
                height = float(page.mediabox.height)
                a4_dimensions = (
                    abs(width - A4_WIDTH) < 1
                    and abs(height - A4_HEIGHT) < 1
                ) or (
                    abs(width - A4_HEIGHT) < 1
                    and abs(height - A4_WIDTH) < 1
                )
                page_sizes.append("A4" if a4_dimensions else "unknown")
                rotation = int(page.rotation or 0) % 180
                display_width, display_height = (
                    (height, width) if rotation == 90 else (width, height)
                )
                orientations.append(
                    "portrait"
                    if display_height >= display_width
                    else "landscape"
                )
            page_size = (
                page_sizes[0] if len(set(page_sizes)) == 1 else "mixed"
            )
            orientation = (
                orientations[0]
                if len(set(orientations)) == 1
                else "mixed"
            )
        else:
            page_size = None
            orientation = None
    except Exception:
        return finish(
            arguments.report,
            error_report(
                expectation,
                "pdf_unreadable",
                pdf_sha256,
            ),
            2,
        )
    comparison_text = normalize_text_marker(extracted_text)
    required_missing = sum(
        marker not in extracted_text
        and normalize_text_marker(marker) not in comparison_text
        for marker in expectation["required_text"]
    )
    forbidden_found = sum(
        marker in extracted_text
        or normalize_text_marker(marker) in comparison_text
        for marker in expectation["forbidden_text"]
    )
    findings: list[str] = []
    if required_missing:
        findings.append("required_text_missing")
    if forbidden_found:
        findings.append("forbidden_text_present")
    if page_count and page_size != expectation["page_size"]:
        findings.append("page_size_mismatch")
    if page_count and orientation != expectation["orientation"]:
        findings.append("orientation_mismatch")
    if not expectation["min_pages"] <= page_count <= expectation["max_pages"]:
        findings.append("page_count_out_of_bounds")
    if not extracted_text.strip():
        findings.append("empty_extracted_text")

    report = {
        "status": "fail" if findings else "pass",
        "pdf_sha256": pdf_sha256,
        "page_count": page_count,
        "page_size": page_size,
        "orientation": orientation,
        "required_text": {
            "expected": len(expectation["required_text"]),
            "missing": required_missing,
        },
        "forbidden_text": {
            "expected": len(expectation["forbidden_text"]),
            "found": forbidden_found,
        },
        "findings": findings,
    }
    return finish(arguments.report, report, 1 if findings else 0)


if __name__ == "__main__":
    try:
        exit_code = main()
    except (OSError, UnicodeError, TypeError, ValueError):
        print("unable to verify PDF", file=sys.stderr)
        exit_code = 2
    raise SystemExit(exit_code)
