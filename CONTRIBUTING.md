# Contributing

Thanks for helping improve this skill. This guide covers how the repo is laid
out and what a good contribution looks like.

## Repository layout

```
.claude-plugin/marketplace.json   # marketplace catalog (lists the plugin)
plugins/
  design-patterns/        # the skill + plugin — the uploadable unit
    .claude-plugin/plugin.json
    SKILL.md              # instructions + frontmatter
    references/           # one .md file per pattern, grouped by category
      CREATIONAL/  STRUCTURAL/  BEHAVIORAL/
    scripts/validate_skill.py
README.md  LICENSE  CONTRIBUTING.md  AGENTS.md  CHANGELOG.md
.github/                  # CI + release workflows, issue/PR templates
```

## Ground rules

- The `plugins/design-patterns/` folder is what gets uploaded to Claude. Keep it
  self-contained. **Do not** add a `README.md` inside it — skill docs live in
  `SKILL.md`. The repo-level README is for human visitors only.
- `SKILL.md` must be named exactly that (case-sensitive), and the frontmatter
  must contain no XML angle brackets (`<` `>`).
- Keep `SKILL.md` lean. Detailed content belongs in `references/`, loaded only
  when needed (progressive disclosure).

## Editing or adding a pattern

Each pattern file must keep the standard sections, in this order:

`Intent` · `Problem It Solves` · `Solution` · `Structure` · `Participants` ·
`How It Works` · `Code Examples` · `When To Use` · `Pros & Cons` ·
`Relations to Other Patterns` · `Sources`

Code examples must cover all eight languages, each under its own `###` header:
Python, Java, C++, C#, TypeScript, Go, PHP, Ruby. Keep examples runnable and
idiomatic for each language — don't force the Java class diagram onto Python or
Go.

If you add a pattern file, register it in the `Pattern → file` table in
`SKILL.md`. Use the existing numeric-prefix naming (e.g. `24-...md`).

## Before you open a PR

Run the validator — CI runs the same check and will block a failing PR:

```bash
python3 plugins/design-patterns/scripts/validate_skill.py
```

Optionally install the pre-commit hook so it runs automatically:

```bash
pip install pre-commit
pre-commit install
```

## Sources and licensing

Write pattern explanations in your own words. Don't paste copyrighted text from
other pattern references. Cite real sources in the `## Sources` section; don't
invent citations. Contributions are accepted under the repository's MIT license.
