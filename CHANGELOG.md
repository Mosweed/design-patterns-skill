# Changelog

All notable changes to the design-patterns skill are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/):

- **major** — breaking restructure (renamed files, changed section layout that
  consumers of the skill rely on)
- **minor** — new content (a new reference file, a new language, a new workflow
  in SKILL.md)
- **patch** — corrections and clarifications to existing content

The version lives in the `metadata.version` field of
`plugins/design-patterns/SKILL.md`. The release workflow refuses to publish a
tag that doesn't match it.

## [Unreleased]

### Added
- Three Claude Code subagents shipped with the plugin: `design-patterns`
  (mentor — explain / choose / review / audit), `design-patterns-uml` (UML
  diagrams for a pattern or a codebase), and `design-patterns-refactorer`
  (applies a pattern refactor, with write access and a test-first workflow).
- `scripts/uml.py` + `scripts/uml_data/` — a UML builder that renders each of
  the 23 patterns' canonical class diagram as Mermaid, PlantUML, or an editable
  draw.io (`.drawio`) file (`uml.py <slug> -f drawio`, `--all`, `--list`).
- `scripts/scan_patterns.py` — scans a codebase for pattern signals and reports
  candidate implementations with file:line (`--json` for tooling); the audit
  workflow and the UML agent use it.
- SKILL.md "Bundled scripts" section wiring the scanner and UML builder into the
  audit and diagram workflows.

### Changed
- Repo layout: the plugin now lives at `plugins/design-patterns/` (was
  `design-patterns/` at the repo root), following the standard marketplace
  convention. The skill content, plugin name, and install command are
  unchanged — only paths in the repo moved.

## [1.0.0] — 2026-06-10

First public release.

### Patterns & skill
- All 23 GoF pattern references (5 creational, 7 structural, 11 behavioral),
  each with intent, problem, solution, ASCII structure diagram, participants,
  step-by-step walkthrough, runnable examples in 8 languages, when-to-use,
  pros & cons, relations, and sources.
- SKILL.md with output formats per task type, single-implementation review
  workflow, whole-codebase audit workflow, and a quick selection guide.
- Grep-based section navigation and a "Pattern file layout" map in SKILL.md,
  so Claude reads only the needed slice of the 1,000+ line pattern files.
- `references/pattern-confusions.md`: the 11 classic mix-ups (Strategy vs
  State, the four wrappers, the creational trio, …) with comparison tables and
  a tell-tale question each, so comparison answers no longer require loading
  multiple full pattern files.
- `references/modern-alternatives.md`: when language features replace a
  pattern (lambdas vs Strategy, generators vs Iterator, events vs Observer,
  DI vs Singleton, pattern matching vs Visitor, …) and when the full GoF form
  still earns its keep.

### Distribution
- Plugin + marketplace distribution: `.claude-plugin/marketplace.json` at the
  repo root lists the `design-patterns` plugin, and `design-patterns/.claude-plugin/plugin.json`
  makes the skill folder installable via
  `/plugin install design-patterns@mosweed-plugins`. The skill, manual-copy, and
  zip workflows all use the same `design-patterns/` folder.
- GitHub Copilot custom agent (`agents/design-patterns.agent.md`).

### Tooling
- Completeness/consistency validator (`scripts/validate_skill.py`) with checks
  for missing sections/languages, SKILL.md link rot, mistagged/untagged code
  fences, and empty Sources sections; CI workflow; pre-commit hook;
  issue/PR templates.
- Release workflow: pushing a `v*` tag validates, zips `design-patterns/`,
  and attaches it to a GitHub Release.
- `evals/`: three test prompts plus a deliberately broken Singleton fixture
  for benchmarking the skill against a no-skill baseline.
