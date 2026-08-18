"""Load meeting notes from data/samples into normalized Note objects."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

NOTE_EXTENSIONS = (".md", ".txt")

# Matches an optional leading frontmatter block:
#   ---
#   date: 2026-03-05
#   title: Pricing sync
#   ---
_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_DATE_IN_NAME_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
_HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


@dataclass
class Note:
    id: str
    date: str | None
    title: str
    raw_text: str
    source_path: str


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split a leading `key: value` frontmatter block off the body, if present."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip().lower()] = value.strip()

    body = text[match.end():]
    return fields, body


def _infer_date(fields: dict[str, str], path: Path) -> str | None:
    if "date" in fields:
        return fields["date"]
    match = _DATE_IN_NAME_RE.search(path.stem)
    return match.group(1) if match else None


def _infer_title(fields: dict[str, str], body: str, path: Path) -> str:
    if "title" in fields:
        return fields["title"]
    heading = _HEADING_RE.search(body)
    if heading:
        return heading.group(1).strip()
    return path.stem.replace("_", " ").replace("-", " ").strip()


def load_note(path: Path) -> Note:
    raw_text = path.read_text(encoding="utf-8")
    fields, body = _parse_frontmatter(raw_text)
    return Note(
        id=path.stem,
        date=_infer_date(fields, path),
        title=_infer_title(fields, body, path),
        raw_text=raw_text,
        source_path=str(path),
    )


def load_notes(samples_dir: Path | str = "data/samples") -> list[Note]:
    """Read all .md/.txt files from samples_dir, sorted by filename for determinism."""
    dir_path = Path(samples_dir)
    if not dir_path.is_dir():
        return []

    paths = sorted(
        p for p in dir_path.iterdir()
        if p.is_file() and p.suffix.lower() in NOTE_EXTENSIONS
    )
    return [load_note(p) for p in paths]
