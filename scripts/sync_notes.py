#!/usr/bin/env python3
"""Prepare website copies of selected Obsidian notes without writing to the Vault."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "publish-map.yml"
STATE = ROOT / "sync-state.json"
GENERATED = ROOT / "sync-generated.json"
PENDING = ROOT / ".sync-pending"
ENGLISH_TITLES = {
    "Find a Function Between Power Sets": "Functions Between Power Sets",
    "03 Cardinality & Power Sets": "03 Cardinality and Power Sets",
    "初等对称多项式": "Elementary Symmetric Polynomials",
    "复数开方": "Square Roots of Complex Numbers",
    "有理数和无理数的稠密性": "Density of Rational and Irrational Numbers",
}
GROUP_TITLES = {
    "Appendix": "Appendix",
    "Atomization": "Short Explorations",
    "MATH1964 Notes": "MATH1964: Discrete Mathematics for Computation (Adv)",
}
WIKI_LINK = re.compile(r"(?<!!)\[\[([^\]]+)\]\]")
EMBED = re.compile(r"!\[\[([^\]]+)\]\]")
MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)(#[^)]*)?\)")
CALLOUT = re.compile(r"^\[!\s*([^\]]+)\]\s*(.*)$", re.I)
COLLECTIONS_START = "<!-- BEGIN GENERATED NOTE COLLECTIONS -->"
COLLECTIONS_END = "<!-- END GENERATED NOTE COLLECTIONS -->"


def load_manifest() -> tuple[list[tuple[Path, Path]], set[str]]:
    """Read the deliberately small, documented subset of YAML used by this map."""
    section = ""
    folders: list[tuple[Path, Path]] = []
    extensions: set[str] = set()
    for raw in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if not raw.startswith(" "):
            section = line.removesuffix(":")
        elif section == "source_folders" and line.startswith("- path: "):
            folders.append((Path(line[len("- path: ") :]), Path()))
        elif section == "source_folders" and line.startswith("destination: "):
            if not folders:
                raise ValueError("A destination must follow a source path.")
            folders[-1] = (folders[-1][0], Path(line[len("destination: ") :]))
        elif section == "include_extensions" and line.startswith("- "):
            extensions.add(line[2:])
    if not folders or not extensions:
        raise ValueError("publish-map.yml needs folders and extensions.")
    for source, destination in folders:
        for path in (source, destination):
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ValueError(f"Unsafe manifest path: {path}")
        if not destination.parts or destination == Path("."):
            raise ValueError(f"Missing destination for {source}")
    return folders, extensions


def front_matter_and_body(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    marker = text.find("\n---\n", 4)
    if marker == -1:
        return "", text
    return text[4:marker], text[marker + 5 :]


def title_from(source: Path, metadata: str) -> str:
    if source.stem in ENGLISH_TITLES:
        return ENGLISH_TITLES[source.stem]
    for line in metadata.splitlines():
        if line.startswith("title:"):
            return line.split(":", 1)[1].strip().strip("'\"") or source.stem
    return source.stem


def link_to(from_output: Path, to_output: Path) -> str:
    relative = os.path.relpath(to_output, from_output.parent).replace(os.sep, "/")
    return f"<{relative}>"


def convert_body(
    body: str,
    source: Path,
    output: Path,
    by_stem: dict[str, Path],
    warnings: list[str],
) -> str:
    if EMBED.search(body):
        raise ValueError(f"Obsidian embed needs manual review: {source}")

    def wiki(match: re.Match[str]) -> str:
        raw = match.group(1)
        target, _, alias = raw.partition("|")
        name = target.split("#", 1)[0].removesuffix(".md").removesuffix(".qmd")
        label = alias or name
        linked = by_stem.get(name.casefold())
        if linked is None:
            warnings.append(f"{source.name}: unpublished link [[{raw}]] shown as text")
            return label
        return f"[{label}]({link_to(output, linked)})"

    body = WIKI_LINK.sub(wiki, body)
    body = re.sub(r"(?m)^\^[A-Za-z0-9-]+\s*$", "", body)

    def markdown_link(match: re.Match[str]) -> str:
        label, target = match.group(1), match.group(2)
        name = Path(target).stem
        linked = by_stem.get(name.casefold())
        if linked is None:
            warnings.append(f"{source.name}: unpublished link {target} shown as text")
            return label
        return f"[{label}]({link_to(output, linked)})"

    body = MD_LINK.sub(markdown_link, body)
    lines = body.splitlines()
    changed_lines: list[str] = []
    index = 0
    while index < len(lines):
        if not re.match(r"^\s*>", lines[index]):
            changed_lines.append(lines[index])
            index += 1
            continue
        quoted: list[str] = []
        while index < len(lines) and re.match(r"^\s*>", lines[index]):
            quoted.append(re.sub(r"^\s*>\s?", "", lines[index]))
            index += 1
        if changed_lines and changed_lines[-1].strip():
            changed_lines.append("")
        callout = CALLOUT.match(quoted[0])
        if callout:
            kind, heading = callout.groups()
            style = {
                "tip": "tip", "warning": "warning", "caution": "caution",
                "important": "important",
            }.get(kind.strip().lower(), "note")
            label = heading.strip() or kind.strip().title()
            changed_lines.extend([f"::: {{.callout-{style}}}", f"## {label}", ""])
            content = quoted[1:]
        else:
            changed_lines.append("::: {.blockquote}")
            content = quoted
        in_math = False
        for item in content:
            # Obsidian permits >$$ while Pandoc needs a separate math block.
            if item.startswith(">"):
                item = re.sub(r"^>\s?", "", item)
                item = f"*{item}*" if item else ""
            if item == "$$":
                if not in_math and changed_lines[-1].strip():
                    changed_lines.append("")
                changed_lines.append(item)
                if in_math:
                    changed_lines.append("")
                in_math = not in_math
            else:
                changed_lines.append(item)
        changed_lines.extend([":::", ""])
    return "\n".join(changed_lines).rstrip() + "\n"


def make_qmd(source: Path, output: Path, by_stem: dict[str, Path], category: str,
             warnings: list[str]) -> str:
    metadata, body = front_matter_and_body(source.read_text(encoding="utf-8"))
    title = title_from(source, metadata)
    converted = convert_body(body, source, output, by_stem, warnings)
    header = (
        "---\n"
        f"title: {json.dumps(title, ensure_ascii=False)}\n"
        f"categories: [{json.dumps(category, ensure_ascii=False)}]\n"
        "---\n\n"
    )
    return header + converted


def make_index(title: str, intro: str, entries: list[tuple[str, str]]) -> str:
    lines = ["---", f"title: {json.dumps(title, ensure_ascii=False)}",
             "toc: false", "---", "", intro, ""]
    for label, href in entries:
        lines.append(f"- [{label}](<{href}>)")
    return "\n".join(lines).rstrip() + "\n"


def update_notes_index(current: str | None, entries: list[tuple[str, str]]) -> str:
    """Refresh source-folder links without rewriting hand-maintained collections."""
    if current is None:
        current = (
            make_index("Notes", "A selection of my course notes and shorter mathematical explorations.", [])
            + f"\n{COLLECTIONS_START}\n{COLLECTIONS_END}\n"
        )
    if current.count(COLLECTIONS_START) != 1 or current.count(COLLECTIONS_END) != 1:
        raise ValueError("Notes index must contain one generated note collections block; no index was replaced.")
    start = current.index(COLLECTIONS_START) + len(COLLECTIONS_START)
    end = current.index(COLLECTIONS_END)
    if end < start:
        raise ValueError("Notes index collection markers are in the wrong order; no index was replaced.")
    links = "\n".join(f"- [{label}](<{href}>)" for label, href in entries)
    return current[:start] + "\n" + links + "\n" + current[end:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, required=True, help="Absolute Vault path")
    parser.add_argument("--sync", action="store_true", help="Write new pages and pending copies")
    parser.add_argument("--refresh-generated", action="store_true",
                        help="Refresh only unchanged, previously generated website copies")
    parser.add_argument("--record-generated-hashes", action="store_true",
                        help="Record hashes of the current generated copies before a converter update")
    parser.add_argument("--acknowledge", metavar="SOURCE", help="Mark a manually reviewed source as current")
    args = parser.parse_args()
    vault = args.vault.resolve()
    if not vault.is_dir():
        parser.error(f"Vault not found: {vault}")
    if ROOT == vault or ROOT.is_relative_to(vault):
        parser.error("The website project must not live inside the Vault.")

    folders, extensions = load_manifest()
    selected: list[tuple[Path, Path, str]] = []
    empty: list[str] = []
    for source_folder, destination_folder in folders:
        directory = vault / source_folder
        if not directory.is_dir() or not directory.resolve().is_relative_to(vault):
            parser.error(f"Source folder unavailable: {directory}")
        for source in sorted(directory.rglob("*")):
            if source.suffix.lower() not in extensions or not source.is_file():
                continue
            if source.is_symlink() or not source.resolve().is_relative_to(vault):
                parser.error(f"Source link escapes the Vault: {source}")
            if any(part.startswith(".") for part in source.relative_to(vault).parts):
                continue
            relative = source.relative_to(directory)
            output = ROOT / destination_folder / relative.with_suffix(".qmd")
            if not output.resolve().is_relative_to(ROOT):
                parser.error(f"Output escapes the website project: {output}")
            if not source.read_text(encoding="utf-8").strip():
                empty.append(str(source.relative_to(vault)))
                continue
            selected.append((source, output, destination_folder.name))

    by_stem: dict[str, Path] = {}
    for source, output, _ in selected:
        if not output.exists():
            continue
        key = source.stem.casefold()
        if key in by_stem:
            parser.error(f"Ambiguous note name: {source.stem}")
        by_stem[key] = output

    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    generated = json.loads(GENERATED.read_text(encoding="utf-8")) if GENERATED.exists() else {}
    if args.record_generated_hashes:
        for source, output, _ in selected:
            key = str(source.relative_to(vault))
            if key in state and output.exists():
                generated[key] = hashlib.sha256(output.read_bytes()).hexdigest()
        GENERATED.write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
        print(f"Recorded {len(generated)} generated page hashes.")
        return 0
    if args.acknowledge:
        matching = [(source, output) for source, output, _ in selected
                    if str(source.relative_to(vault)) == args.acknowledge]
        if len(matching) != 1 or not matching[0][1].exists():
            parser.error("--acknowledge requires one existing website page from the selected folders")
        source, _ = matching[0]
        state[args.acknowledge] = hashlib.sha256(source.read_bytes()).hexdigest()
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Reviewed source recorded: {args.acknowledge}")
        return 0

    warnings: list[str] = []
    changes: list[str] = []
    for source, output, category in selected:
        key = str(source.relative_to(vault))
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if state.get(key) == digest and output.exists():
            if not args.refresh_generated:
                continue
            if generated.get(key) != hashlib.sha256(output.read_bytes()).hexdigest():
                warnings.append(f"{key}: website copy has manual edits; refresh skipped")
                continue
        try:
            qmd = make_qmd(source, output, by_stem, category, warnings)
        except ValueError as exc:
            warnings.append(str(exc))
            continue
        if not output.exists():
            changes.append(f"NEW PENDING {key}")
            if args.sync:
                pending = PENDING / output.relative_to(ROOT)
                pending.parent.mkdir(parents=True, exist_ok=True)
                pending.write_text(qmd, encoding="utf-8")
        elif args.refresh_generated and state.get(key) == digest:
            changes.append(f"REFRESH {key}")
            if args.sync:
                output.write_text(qmd, encoding="utf-8")
                generated[key] = hashlib.sha256(qmd.encode("utf-8")).hexdigest()
        else:
            changes.append(f"PENDING {key}")
            if args.sync:
                pending = PENDING / output.relative_to(ROOT)
                pending.parent.mkdir(parents=True, exist_ok=True)
                pending.write_text(qmd, encoding="utf-8")

    if args.sync:
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        GENERATED.write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
        group_entries: list[tuple[str, str]] = []
        for source_folder, destination_folder in folders:
            group = destination_folder.name
            pages = [(source, output) for source, output, _ in selected
                     if output.is_relative_to(ROOT / destination_folder) and output.exists()]
            if not pages:
                continue
            folder_index = ROOT / destination_folder / "index.qmd"
            entries = [(title_from(source, front_matter_and_body(source.read_text(encoding="utf-8"))[0]),
                        output.relative_to(folder_index.parent).as_posix())
                       for source, output in pages]
            folder_index.parent.mkdir(parents=True, exist_ok=True)
            folder_index.write_text(
                make_index(GROUP_TITLES.get(source_folder.name, source_folder.name),
                           "Working notes; some pages still need mathematical review.", entries),
                encoding="utf-8",
            )
            group_entries.append((GROUP_TITLES.get(source_folder.name, source_folder.name),
                                  f"{group}/index.qmd"))
        main_index = ROOT / "notes" / "index.qmd"
        main_index.parent.mkdir(parents=True, exist_ok=True)
        current_index = main_index.read_text(encoding="utf-8") if main_index.exists() else None
        main_index.write_text(
            update_notes_index(current_index, group_entries),
            encoding="utf-8",
        )

    print("\n".join(changes) if changes else "No source changes.")
    print(f"Selected: {len(selected)} non-empty notes; skipped: {len(empty)} empty notes.")
    for item in warnings:
        print(f"REVIEW {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
