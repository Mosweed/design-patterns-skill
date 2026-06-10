#!/usr/bin/env python3
"""Scan a codebase for structural signals of the 23 GoF design patterns.

This finds *candidate* implementations by their tell-tale signals (the same
ones the skill's audit workflow greps for) and reports them with file:line.
These are candidates, NOT confirmed patterns — a class called ``UserFactory``
or a stray ``notify`` proves nothing on its own. Treat the output as a worklist
to inspect, exactly as the skill's audit step does: confirm intent from
behaviour before calling anything a pattern.

Usage:
    python scan_patterns.py                 # scan current directory, table
    python scan_patterns.py src/ --json     # machine-readable, for tooling
    python scan_patterns.py . --pattern observer,singleton
    python scan_patterns.py . --json > patterns.json   # feed uml/tooling

The JSON shape:
    {
      "root": "src",
      "summary": {"observer": 3, "singleton": 1},
      "candidates": [
        {"pattern": "observer", "file": "src/bus.py", "line": 12,
         "signal": "subscribe(", "text": "def subscribe(self, fn):"}
      ]
    }
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SOURCE_EXTENSIONS = {
    ".py", ".java", ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".h",
    ".cs", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".go", ".php", ".rb",
}

SKIP_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build", "out", "target",
    "__pycache__", ".venv", "venv", ".tox", ".mypy_cache", ".idea", ".vscode",
    "bin", "obj", ".next", "coverage",
}

# Each pattern maps to (compiled regex, human label) signal pairs. The labels
# read out in the report so a human sees *why* a line was flagged. Signals are
# deliberately broad — this casts a wide net and accepts false positives, which
# the human/agent then prunes.
def _sig(pattern: str) -> re.Pattern:
    return re.compile(pattern)

SIGNALS: dict[str, list[tuple[re.Pattern, str]]] = {
    "singleton": [
        (_sig(r"\bgetInstance\b"), "getInstance"),
        (_sig(r"\bget_instance\b"), "get_instance"),
        (_sig(r"def __new__\b"), "__new__ override"),
        (_sig(r"\b(private|static)\b.*\binstance\b"), "static instance field"),
        (_sig(r"@(staticmethod|classmethod)\s*\n\s*def instance"), "instance() accessor"),
    ],
    "factory-method": [
        (_sig(r"\b(create|make)[A-Z]\w*\s*\("), "create*/make* factory call"),
        (_sig(r"class \w*Factory\b"), "…Factory class"),
    ],
    "abstract-factory": [
        (_sig(r"class Abstract\w*Factory\b"), "AbstractFactory class"),
        (_sig(r"class \w+Factory\b.*:\s*$"), "concrete factory class"),
    ],
    "builder": [
        (_sig(r"\.build\(\)"), ".build()"),
        (_sig(r"class \w*Builder\b"), "…Builder class"),
        (_sig(r"return (this|self)\s*;?\s*$"), "fluent return this/self"),
    ],
    "prototype": [
        (_sig(r"\bdef clone\b|\bclone\s*\("), "clone()"),
        (_sig(r"__deepcopy__|__copy__"), "copy protocol"),
    ],
    "adapter": [
        (_sig(r"class \w*Adapter\b"), "…Adapter class"),
        (_sig(r"class \w*Wrapper\b"), "…Wrapper class"),
    ],
    "composite": [
        (_sig(r"class \w*Composite\b"), "…Composite class"),
        (_sig(r"\b(add|remove)Child\b|\badd_child\b"), "add/removeChild"),
    ],
    "decorator": [
        (_sig(r"class \w*Decorator\b"), "…Decorator class"),
    ],
    "facade": [
        (_sig(r"class \w*Facade\b"), "…Facade class"),
    ],
    "flyweight": [
        (_sig(r"class \w*Flyweight\b"), "…Flyweight class"),
        (_sig(r"\bgetFlyweight\b|\bflyweight_pool\b"), "flyweight pool"),
    ],
    "proxy": [
        (_sig(r"class \w*Proxy\b"), "…Proxy class"),
        (_sig(r"def __getattr__\b"), "__getattr__ forwarding"),
    ],
    "chain-of-responsibility": [
        (_sig(r"\bset_?[Nn]ext\b"), "setNext/set_next"),
        (_sig(r"\bsuccessor\b"), "successor"),
        (_sig(r"\bhandle(Request)?\s*\("), "handle()/handleRequest()"),
    ],
    "command": [
        (_sig(r"class \w*Command\b"), "…Command class"),
        (_sig(r"\bdef (execute|undo)\b|\.execute\(\)"), "execute()/undo()"),
    ],
    "interpreter": [
        (_sig(r"\bdef (interpret|evaluate)\b"), "interpret()/evaluate()"),
        (_sig(r"class \w*Expression\b"), "…Expression class"),
    ],
    "iterator": [
        (_sig(r"def __iter__\b|def __next__\b"), "__iter__/__next__"),
        (_sig(r"\bhasNext\b|\bSymbol\.iterator\b|\bIEnumerable\b"), "iterator protocol"),
    ],
    "mediator": [
        (_sig(r"class \w*Mediator\b"), "…Mediator class"),
    ],
    "memento": [
        (_sig(r"class \w*Memento\b"), "…Memento class"),
        (_sig(r"\b(create|save)Memento\b|\brestore\s*\("), "save/restore memento"),
    ],
    "observer": [
        (_sig(r"\b(subscribe|unsubscribe|addObserver|removeObserver)\b"), "subscribe/observer"),
        (_sig(r"\b(notify|notifyObservers)\s*\("), "notify()"),
        (_sig(r"\b(addEventListener|addListener|\.emit)\b"), "event emitter"),
        (_sig(r"class \w*Observer\b"), "…Observer class"),
    ],
    "state": [
        (_sig(r"class \w*State\b"), "…State class"),
        (_sig(r"\bset_?[Ss]tate\b|\bchange_?[Ss]tate\b|\btransition_to\b"), "state transition"),
    ],
    "strategy": [
        (_sig(r"class \w*Strategy\b"), "…Strategy class"),
        (_sig(r"\bset_?[Ss]trategy\b"), "setStrategy"),
    ],
    "template-method": [
        (_sig(r"\btemplate_?[Mm]ethod\b"), "templateMethod"),
        (_sig(r"@abstractmethod"), "abstract step (@abstractmethod)"),
    ],
    "visitor": [
        (_sig(r"\bdef accept\b|\baccept\s*\(\s*\w*[Vv]isitor"), "accept(visitor)"),
        (_sig(r"\bdef visit\w*\b"), "visit*()"),
        (_sig(r"class \w*Visitor\b"), "…Visitor class"),
    ],
}


def iter_source_files(root: Path):
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SOURCE_EXTENSIONS:
            yield path


def scan(root: Path, only: set[str] | None) -> list[dict]:
    patterns = SIGNALS if not only else {k: v for k, v in SIGNALS.items() if k in only}
    candidates: list[dict] = []
    for path in iter_source_files(root):
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        rel = path.relative_to(root).as_posix() if root in path.parents or root == path.parent else str(path)
        for lineno, line in enumerate(lines, start=1):
            for pattern, sigs in patterns.items():
                for regex, label in sigs:
                    if regex.search(line):
                        candidates.append({
                            "pattern": pattern,
                            "file": rel,
                            "line": lineno,
                            "signal": label,
                            "text": line.strip()[:160],
                        })
    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", nargs="?", default=".", help="directory to scan")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--pattern", help="comma-separated pattern slugs to limit to")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"No such path: {root}", file=sys.stderr)
        raise SystemExit(2)

    only = set(s.strip() for s in args.pattern.split(",")) if args.pattern else None
    if only:
        unknown = only - set(SIGNALS)
        if unknown:
            print(f"Unknown pattern slug(s): {sorted(unknown)}", file=sys.stderr)
            raise SystemExit(2)

    candidates = scan(root, only)
    summary: dict[str, int] = {}
    for c in candidates:
        summary[c["pattern"]] = summary.get(c["pattern"], 0) + 1

    if args.json:
        print(json.dumps({
            "root": str(root),
            "summary": dict(sorted(summary.items(), key=lambda kv: -kv[1])),
            "candidates": candidates,
        }, indent=2))
        return

    if not candidates:
        print(f"No pattern signals found under {root}")
        return

    print(f"Pattern candidates under {root}")
    print("(signals only — confirm intent before calling anything a pattern)\n")
    for pattern in sorted(summary, key=lambda p: -summary[p]):
        print(f"## {pattern}  ({summary[pattern]} signal(s))")
        for c in [c for c in candidates if c["pattern"] == pattern]:
            print(f"  {c['file']}:{c['line']}  [{c['signal']}]  {c['text']}")
        print()


if __name__ == "__main__":
    main()
