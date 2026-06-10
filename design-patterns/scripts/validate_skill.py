#!/usr/bin/env python3
"""Validate the design-patterns skill: completeness and consistency.

Run from anywhere:  python3 scripts/validate_skill.py
Exits non-zero and lists problems if anything is off.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"

# Pattern slugs per category. Files are prefixed with a number
# (e.g. 01-factory-method.md), so we match by suffix, not exact name.
EXPECTED_PATTERNS = {
    "CREATIONAL": [
        "factory-method", "abstract-factory", "builder", "prototype", "singleton",
    ],
    "STRUCTURAL": [
        "adapter", "bridge", "composite", "decorator", "facade", "flyweight", "proxy",
    ],
    "BEHAVIORAL": [
        "chain-of-responsibility", "command", "interpreter", "iterator", "mediator",
        "memento", "observer", "state", "strategy", "template-method", "visitor",
    ],
}

EXPECTED_LANGUAGES = [
    "Python", "Java", "C++", "C#", "TypeScript", "Go", "PHP", "Ruby",
]

# Expected fence info-string per language section, so a ```python block under
# "### Java" (or an untagged block) is caught.
LANGUAGE_FENCE_TAGS = {
    "Python": "python",
    "Java": "java",
    "C++": "cpp",
    "C#": "csharp",
    "TypeScript": "typescript",
    "Go": "go",
    "PHP": "php",
    "Ruby": "ruby",
}

# Every pattern file must contain these level-2 sections. Matched by prefix,
# so "## Structure (ASCII diagram)" satisfies "Structure".
REQUIRED_SECTIONS = [
    "Intent",
    "Problem It Solves",
    "Solution",
    "Structure",
    "Participants",
    "How It Works",
    "Code Examples",
    "When To Use",
    "Pros & Cons",
    "Relations to Other Patterns",
    "Sources",
]

# A code fence is a line that, ignoring up to 3 leading spaces, starts with ```.
# This deliberately ignores backticks that appear mid-line inside code strings
# (e.g. a Java/Ruby example that builds a markdown string), which a naive
# text.count("```") would miscount.
FENCE_RE = re.compile(r"^\s{0,3}```")
# Language sections are level-3 headers: "### Python", "### C++", etc.
HEADER_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)


def find_file(category_dir: Path, slug: str) -> Path | None:
    matches = sorted(category_dir.glob(f"*{slug}.md"))
    return matches[0] if matches else None


def balanced_fences(text: str) -> bool:
    return sum(1 for line in text.splitlines() if FENCE_RE.match(line)) % 2 == 0


def headers(text: str) -> set[str]:
    return {m.strip() for m in HEADER_RE.findall(text)}


def section_body(text: str, header: str, level: int = 2) -> str | None:
    """Return the body of a section: from its header to the next header of the
    same or higher level (or EOF). None if the section is missing."""
    marker = "#" * level
    start = re.search(
        rf"^{marker}\s+{re.escape(header)}.*$", text, re.MULTILINE
    )
    if start is None:
        return None
    rest = text[start.end():]
    end = re.search(rf"^#{{1,{level}}}\s", rest, re.MULTILINE)
    return rest[: end.start()] if end else rest


def check_language_fences(text: str, rel: Path, errors: list[str]) -> None:
    """Each '### <Language>' section must open with a fence tagged for that
    language. An untagged or mistagged fence renders without highlighting and
    usually means a copy-paste slip."""
    for language, tag in LANGUAGE_FENCE_TAGS.items():
        body = section_body(text, language, level=3)
        if body is None:
            continue  # missing section is reported elsewhere
        opening_tags = []
        inside = False
        for line in body.splitlines():
            if FENCE_RE.match(line):
                if not inside:
                    opening_tags.append(line.strip().removeprefix("```").strip())
                inside = not inside
        if not opening_tags:
            errors.append(f"No code block in '### {language}': {rel}")
        elif tag not in opening_tags:
            errors.append(
                f"'### {language}' has no ```{tag} fence "
                f"(found: {opening_tags}): {rel}"
            )


def check_sources(text: str, rel: Path, errors: list[str]) -> None:
    body = section_body(text, "Sources")
    if body is not None and not body.strip().strip("-").strip():
        errors.append(f"Empty '## Sources' section: {rel}")


def check_skill_md_links(errors: list[str]) -> None:
    """Every references/... path mentioned in SKILL.md must exist, and every
    pattern file must be reachable from SKILL.md — otherwise the skill's
    pattern->file table silently rots."""
    skill_md = ROOT / "SKILL.md"
    if not skill_md.exists():
        errors.append("Missing SKILL.md")
        return
    text = skill_md.read_text(encoding="utf-8")
    mentioned = set(re.findall(r"references/[\w/.\-]+\.md", text))

    for path_str in sorted(mentioned):
        if not (ROOT / path_str).exists():
            errors.append(f"SKILL.md links to missing file: {path_str}")

    for actual in sorted(REFERENCES.rglob("*.md")):
        rel = actual.relative_to(ROOT).as_posix()
        if rel not in mentioned:
            errors.append(f"Pattern file not referenced in SKILL.md: {rel}")


def main() -> None:
    errors: list[str] = []

    for category, slugs in EXPECTED_PATTERNS.items():
        category_dir = REFERENCES / category
        if not category_dir.exists():
            errors.append(f"Missing category directory: {category}")
            continue

        for slug in slugs:
            path = find_file(category_dir, slug)
            if path is None:
                errors.append(f"Missing pattern file: {category}/*{slug}.md")
                continue

            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(ROOT)

            if not text.lstrip().startswith("#"):
                errors.append(f"Missing top-level heading: {rel}")
            if not balanced_fences(text):
                errors.append(f"Unbalanced code fences: {rel}")

            for section in REQUIRED_SECTIONS:
                if not re.search(rf"^##\s+{re.escape(section)}", text, re.MULTILINE):
                    errors.append(f"Missing '## {section}' section: {rel}")

            present = headers(text)
            for language in EXPECTED_LANGUAGES:
                if language not in present:
                    errors.append(f"Missing '### {language}' section: {rel}")

            check_language_fences(text, rel, errors)
            check_sources(text, rel, errors)

    check_skill_md_links(errors)

    if errors:
        print("Skill validation FAILED:\n")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)

    total = sum(len(v) for v in EXPECTED_PATTERNS.values())
    print(f"Skill validation passed: {total} pattern files, "
          f"{len(EXPECTED_LANGUAGES)} languages each.")


if __name__ == "__main__":
    main()
