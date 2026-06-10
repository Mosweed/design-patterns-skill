# Design Patterns Skill for Claude

<!-- After pushing to GitHub, replace OWNER/REPO with the actual path -->
[![Validate skill](https://github.com/OWNER/REPO/actions/workflows/validate.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/validate.yml)

A Claude [Skill](https://code.claude.com/docs/en/skills) that turns Claude into
a reliable reference for all 23 Gang of Four design patterns. Ask about a
pattern, get help choosing between patterns, or have Claude review and refactor
your code toward the right one — with idiomatic examples in 8 languages, loaded
only when needed instead of dumped into every conversation.

## What you get

- **All 23 GoF patterns** — 5 creational, 7 structural, 11 behavioral — each
  with intent, structure, participants, pitfalls, and relations to other patterns.
- **Runnable examples in 8 languages**: Python, Java, C++, C#, TypeScript, Go,
  PHP, Ruby. Claude reads only the language you ask for.
- **Code review and refactoring** that checks your implementation against the
  pattern's roles and known pitfalls — and tells idiomatic variants apart from
  real mistakes, so you don't get false alarms.
- **Whole-codebase audits**: Claude finds candidate pattern implementations,
  reports problems in a table, and fixes them only after you approve.

## Install

### Claude.ai
1. Download or clone this repo.
2. Zip the `design-patterns/` folder.
3. In Claude.ai: **Settings → Capabilities → Skills → Upload skill**, select the zip.
4. Toggle the skill on.

### Claude Code
Copy the `design-patterns/` folder into a skills directory:

```bash
# Personal — available in all your projects
cp -r design-patterns ~/.claude/skills/

# Or project-scoped — committed with a repo, shared with your team
cp -r design-patterns .claude/skills/
```

Restart Claude Code if the skills directory didn't already exist.

### GitHub Copilot (custom agent)
This repo also ships a GitHub Copilot custom agent that follows the same
workflow, in [`agents/design-patterns.agent.md`](agents/design-patterns.agent.md).
To use it in your own workspace, copy it into `.github/agents/` so VS Code Copilot
detects it:

```bash
mkdir -p .github/agents
cp agents/design-patterns.agent.md .github/agents/
```

Then select **Design Patterns Mentor** from the agent dropdown in Copilot Chat.
The agent is self-contained, but if it can see this repo's
`design-patterns/references/`, it will use those files as its source of truth.

## What it does

The skill picks the right shape for the task automatically:

| You ask | Claude responds with |
|---|---|
| "Explain the Observer pattern in Go" | Intent, structure, one idiomatic Go example, pitfalls |
| "Strategy or State here?" | A comparison table and a single recommendation |
| "Is this a correct Singleton?" + code | A findings table (correctness / robustness / deviation) |
| "Audit the codebase for pattern mistakes" | A report first; fixes only after you approve |
| "Refactor this if/else toward a pattern" | The target pattern and the smallest safe change |

It will also tell you when **no** pattern is the better answer, rather than
forcing one.

## Repository layout

```
design-patterns/          # the skill (this is the uploadable unit)
  SKILL.md                # instructions + frontmatter
  references/             # one file per pattern, grouped by category
  scripts/
    validate_skill.py     # completeness & consistency checker
agents/
  design-patterns.agent.md # GitHub Copilot custom agent (same workflow)
README.md                 # this file (for humans — NOT inside the skill)
CONTRIBUTING.md           # how to contribute
AGENTS.md                 # guidance for AI agents working on the repo
LICENSE
.github/                  # CI workflow + issue/PR templates
.pre-commit-config.yaml   # optional: runs the validator before each commit
```

The skill folder deliberately contains no `README.md` — skill documentation
lives in `SKILL.md`, and this repo-level README is for human visitors.

## Development

Validate completeness and consistency (all 23 files present, every language
section present, balanced code fences, Sources section present):

```bash
python3 design-patterns/scripts/validate_skill.py
```

To run it automatically before each commit, install
[pre-commit](https://pre-commit.com):

```bash
pip install pre-commit
pre-commit install
```

## Support

Questions, bug reports, or pattern corrections: please open a
[GitHub Issue](../../issues). To contribute changes, see
[CONTRIBUTING.md](CONTRIBUTING.md). Pull requests are welcome.

## License

MIT — see [LICENSE](LICENSE).

## Credits

Pattern descriptions are original write-ups informed by the Gang of Four book
(*Design Patterns: Elements of Reusable Object-Oriented Software*, 1994) and
common references such as refactoring.guru and sourcemaking.com.
