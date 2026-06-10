# AGENTS.md

Guidance for AI coding agents (Claude Code, Cursor, Codex, etc.) working in
this repository. This file is tool-agnostic; it describes how to work on the
repo, not how the skill behaves at runtime (that lives in
`design-patterns/SKILL.md`).

## What this repo is

An open-source Claude Skill: a reference for the 23 Gang of Four design
patterns. The `design-patterns/` folder is the deliverable — it gets zipped and
uploaded to Claude. Everything else (README, LICENSE, CI, this file) supports
the repo for humans and agents.

## Hard rules — do not break these

- Do **not** create a `README.md` inside `design-patterns/`. Skill docs go in
  `SKILL.md`; the repo-level README is separate and for humans.
- `SKILL.md` must keep that exact name (case-sensitive).
- The `SKILL.md` frontmatter must contain no `<` or `>` characters — this is a
  security restriction (frontmatter is injected into Claude's system prompt).
- Do not put secrets, emails, or tokens in `SKILL.md` frontmatter; it is
  published publicly.
- The repo ships as a plugin marketplace. Keep `.claude-plugin/marketplace.json`
  (repo root) and `design-patterns/.claude-plugin/plugin.json` in place. The
  plugin loads the skill via `"skills": ["./"]`, so the plugin root is the same
  `design-patterns/` folder — do not move `SKILL.md` out of it. Validate both
  manifests with `claude plugin validate .` and `claude plugin validate ./design-patterns`.
- Plugin version lives in `design-patterns/.claude-plugin/plugin.json` and should
  track the `metadata.version` in `SKILL.md`. Do not also set `version` in the
  marketplace entry — `plugin.json` wins silently and a second copy only drifts.

## When you change anything under `design-patterns/`

Run the validator and make it pass before committing:

```bash
python3 design-patterns/scripts/validate_skill.py
```

It checks that all 23 pattern files exist, each has the 11 required sections,
each has all 8 language subsections, and code fences are balanced. CI runs the
same check on every push and pull request.

## Conventions

- Pattern files: numeric-prefixed kebab-case (`01-factory-method.md`), grouped
  under `references/CREATIONAL`, `STRUCTURAL`, or `BEHAVIORAL`.
- Required sections per file: Intent, Problem It Solves, Solution, Structure,
  Participants, How It Works, Code Examples, When To Use, Pros & Cons,
  Relations to Other Patterns, Sources.
- Code examples: Python, Java, C++, C#, TypeScript, Go, PHP, Ruby — each under a
  `###` header. Keep them idiomatic per language, not a literal port of one.
- New pattern file → also add it to the `Pattern → file` table in `SKILL.md`.

See `CONTRIBUTING.md` for the human-facing version of these guidelines.
