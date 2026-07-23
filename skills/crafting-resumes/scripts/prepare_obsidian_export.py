from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import stat
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--markdown", required=True, type=pathlib.Path)
    parser.add_argument("--css", required=True, type=pathlib.Path)
    parser.add_argument("--appearance", required=True, type=pathlib.Path)
    parser.add_argument("--workspace", required=True, type=pathlib.Path)
    parser.add_argument("--target-pdf", required=True, type=pathlib.Path)
    parser.add_argument("--manifest", required=True, type=pathlib.Path)
    return parser.parse_args()


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def markdown_css_classes(path: pathlib.Path) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return set()
    try:
        closing_index = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration:
        return set()

    frontmatter = lines[1:closing_index]
    classes: set[str] = set()
    for index, line in enumerate(frontmatter):
        if not line.startswith("cssclasses:"):
            continue
        value = line.split(":", 1)[1].strip()
        if value:
            for item in value.strip("[]").split(","):
                normalized = item.strip().strip("\"'")
                if normalized:
                    classes.add(normalized)
            break
        for nested_line in frontmatter[index + 1 :]:
            stripped = nested_line.strip()
            if not stripped.startswith("-"):
                break
            normalized = stripped[1:].strip().strip("\"'")
            if normalized:
                classes.add(normalized)
        break
    return classes


def main() -> int:
    args = parse_args()

    for argument_name, source in (
        ("markdown", args.markdown),
        ("css", args.css),
        ("appearance", args.appearance),
    ):
        if source.is_symlink():
            print(
                f"{argument_name} input must not be a symlink",
                file=sys.stderr,
            )
            return 1

    suggested_temporary_pdf = args.workspace.parent / (
        f"{args.target_pdf.stem}.temporary.pdf"
    )
    output_paths = (
        args.workspace,
        args.target_pdf,
        args.manifest,
        suggested_temporary_pdf,
    )
    if len({os.path.abspath(path) for path in output_paths}) != len(
        output_paths
    ):
        print("output paths must be distinct", file=sys.stderr)
        return 1
    if os.path.lexists(args.workspace):
        print("workspace already exists", file=sys.stderr)
        return 1
    if os.path.lexists(args.target_pdf):
        print("target PDF already exists", file=sys.stderr)
        return 1
    if os.path.lexists(args.manifest):
        print("manifest already exists", file=sys.stderr)
        return 1
    if os.path.lexists(suggested_temporary_pdf):
        print("temporary PDF already exists", file=sys.stderr)
        return 1
    if args.css.stem not in markdown_css_classes(args.markdown):
        print("markdown CSS class is not enabled", file=sys.stderr)
        return 1
    appearance_data = json.loads(args.appearance.read_text(encoding="utf-8"))
    if not isinstance(appearance_data, dict):
        raise TypeError("appearance root must be an object")
    enabled_snippets = appearance_data.get("enabledCssSnippets", [])
    if not isinstance(enabled_snippets, list) or not all(
        isinstance(item, str) for item in enabled_snippets
    ):
        raise TypeError("enabled CSS snippets must be a string list")
    if args.css.stem not in enabled_snippets:
        print("appearance CSS snippet is not enabled", file=sys.stderr)
        return 1

    args.workspace.mkdir(mode=stat.S_IRWXU)
    os.chmod(args.workspace, stat.S_IRWXU)

    copied_markdown = args.workspace / args.markdown.name
    copied_css = (
        args.workspace / ".obsidian" / "snippets" / args.css.name
    )
    copied_appearance = args.workspace / ".obsidian" / "appearance.json"
    copied_css.parent.mkdir(parents=True)

    shutil.copyfile(args.markdown, copied_markdown)
    shutil.copyfile(args.css, copied_css)
    shutil.copyfile(args.appearance, copied_appearance)

    copies = {
        "markdown": {
            "path": str(copied_markdown),
            "sha256": sha256(copied_markdown),
        },
        "css": {
            "path": str(copied_css),
            "sha256": sha256(copied_css),
        },
        "appearance": {
            "path": str(copied_appearance),
            "sha256": sha256(copied_appearance),
        },
    }
    manifest = {
        "workspace": str(args.workspace),
        "copies": copies,
        "target_pdf": str(args.target_pdf),
        "suggested_temporary_pdf": str(suggested_temporary_pdf),
    }
    with args.manifest.open("x", encoding="utf-8") as manifest_file:
        manifest_file.write(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        )
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError):
        print("unable to prepare export", file=sys.stderr)
        exit_code = 2
    raise SystemExit(exit_code)
