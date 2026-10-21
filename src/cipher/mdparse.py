"""Markdown-aware segmentation of AGENTS.md text into instruction units with exact source spans.

Units keep their 1-based line span, the heading path above them, and whether they sit inside a fenced code block
(code blocks are retained as context but are not treated as normative units).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^\s{0,3}(```|~~~)")
LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
TABLE_ROW = re.compile(r"^\s*\|")


@dataclass
class Unit:
    path: str
    start_line: int
    end_line: int
    text: str
    heading_path: list[str] = field(default_factory=list)
    kind: str = "paragraph"  # paragraph | list_item | table_row

    @property
    def heading(self) -> str:
        return " > ".join(self.heading_path)


def split_lines(content: str) -> list[str]:
    return content.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def heading_map(lines: list[str]) -> list[list[str]]:
    """Heading path in force at each line (index = line number - 1), ignoring headings inside code fences."""
    out: list[list[str]] = []
    stack: list[tuple[int, str]] = []
    in_fence = False
    for line in lines:
        if FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence:
            m = HEADING.match(line)
            if m:
                level = len(m.group(1))
                stack = [(lv, t) for lv, t in stack if lv < level] + [(level, m.group(2).strip())]
        out.append([t for _, t in stack])
    return out


def units(path: str, content: str) -> list[Unit]:
    """Segment a file into list items, table rows and paragraphs outside code fences.

    A list item absorbs its indented continuation lines; nested list items become separate units."""
    lines = split_lines(content)
    heads = heading_map(lines)
    result: list[Unit] = []
    in_fence = False
    cur: Unit | None = None

    def flush() -> None:
        nonlocal cur
        if cur is not None and cur.text.strip():
            cur.text = cur.text.strip()
            result.append(cur)
        cur = None

    for i, line in enumerate(lines, start=1):
        if FENCE.match(line):
            flush()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line.strip() or HEADING.match(line) or re.match(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$", line):
            flush()
            continue
        m = LIST_ITEM.match(line)
        if m:
            flush()
            cur = Unit(path, i, i, m.group(3), heads[i - 1], "list_item")
            continue
        if TABLE_ROW.match(line):
            flush()
            if re.match(r"^\s*\|?\s*:?-{2,}", line):
                continue
            cur = Unit(path, i, i, line.strip(), heads[i - 1], "table_row")
            flush()
            continue
        if cur is not None and (cur.kind == "paragraph" or line.startswith((" ", "\t"))):
            cur.text += " " + line.strip()
            cur.end_line = i
        else:
            flush()
            cur = Unit(path, i, i, line.strip(), heads[i - 1], "paragraph")
    flush()
    return result


def section_text(content: str, start_line: int, end_line: int, max_lines: int = 40) -> tuple[int, int, str]:
    """Return the heading-delimited section that contains the span, capped around the span.

    Returns (first_line, last_line, text) with 1-based inclusive line numbers."""
    lines = split_lines(content)
    in_fence = False
    heading_lines = []
    for i, line in enumerate(lines, start=1):
        if FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and HEADING.match(line):
            heading_lines.append(i)
    first = max([h for h in heading_lines if h <= start_line], default=1)
    nxt = [h for h in heading_lines if h > end_line]
    last = (nxt[0] - 1) if nxt else len(lines)
    while last > first and not lines[last - 1].strip():
        last -= 1
    if last - first + 1 > max_lines:
        half = max_lines // 2
        first = max(first, start_line - half)
        last = min(last, end_line + half)
    return first, last, "\n".join(lines[first - 1:last])


def span_text(content: str, start_line: int, end_line: int) -> str:
    lines = split_lines(content)
    return "\n".join(lines[start_line - 1:end_line])
