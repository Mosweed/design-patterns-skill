# Design Patterns Skill for Claude

[![Validate skill](https://github.com/Mosweed/design-patterns-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/Mosweed/design-patterns-skill/actions/workflows/validate.yml)

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
1. Download the `design-patterns-vX.Y.Z.zip` from the
   [latest release](https://github.com/Mosweed/design-patterns-skill/releases),
   or clone this repo and zip the `plugins/design-patterns/` folder yourself.
2. In Claude.ai: **Settings → Capabilities → Skills → Upload skill**, select the zip.
3. Toggle the skill on.

### Claude Code (plugin marketplace — recommended)
This repo doubles as a [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces),
so you can install it once and get automatic updates instead of copying files by hand.

```bash
/plugin marketplace add Mosweed/design-patterns-skill
/plugin install design-patterns@mosweed-plugins
```

To try it straight from a local clone before it's pushed anywhere:

```bash
/plugin marketplace add ./design-patterns-skill
/plugin install design-patterns@mosweed-plugins
```

Update later with `/plugin marketplace update mosweed-plugins`, and remove with
`/plugin uninstall design-patterns@mosweed-plugins`. The same commands work as
`claude plugin …` from a normal shell.

### Claude Code (manual copy)
Prefer not to use a marketplace? Copy the `plugins/design-patterns/` folder into a skills directory:

```bash
# Personal — available in all your projects
cp -r plugins/design-patterns ~/.claude/skills/

# Or project-scoped — committed with a repo, shared with your team
cp -r plugins/design-patterns .claude/skills/
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
`plugins/design-patterns/references/`, it will use those files as its source of truth.

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
.claude-plugin/
  marketplace.json          # marketplace catalog (lists the design-patterns plugin)
plugins/
  design-patterns/          # the skill AND the plugin (this is the uploadable unit)
    .claude-plugin/
      plugin.json           # plugin manifest (skill discovered via "skills": ["./"])
    SKILL.md                # instructions + frontmatter
    references/             # one file per pattern, grouped by category
    scripts/
      validate_skill.py     # completeness & consistency checker
agents/
  design-patterns.agent.md  # GitHub Copilot custom agent (same workflow)
evals/                      # benchmark prompts + fixtures (not shipped in the plugin)
README.md                   # this file (for humans — NOT inside the skill)
CHANGELOG.md                # version history
CONTRIBUTING.md             # how to contribute
AGENTS.md                   # guidance for AI agents working on the repo
LICENSE
.github/                    # CI + release workflows, issue/PR templates
.pre-commit-config.yaml     # optional: runs the validator before each commit
```

The same `plugins/design-patterns/` folder serves three distribution channels: a
Claude Code / Claude.ai **skill** (its `SKILL.md`), a Claude Code **plugin** (via
the nested `.claude-plugin/plugin.json`), and a manual zip. The repo root is the
**marketplace** that lists the plugin.

The skill folder deliberately contains no `README.md` — skill documentation
lives in `SKILL.md`, and this repo-level README is for human visitors.

## Development

Validate completeness and consistency (all 23 files present, every language
section present, balanced code fences, Sources section present):

```bash
python3 plugins/design-patterns/scripts/validate_skill.py
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
