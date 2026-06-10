---
name: design-patterns
description: "Use for Gang of Four design-pattern tasks: explaining a named pattern (Factory Method, Singleton, Observer, Strategy, Decorator, Adapter, Proxy, Visitor, etc.), choosing between patterns, reviewing or refactoring code toward a pattern, or generating idiomatic examples in Python, Java, C++, C#, TypeScript, Go, PHP, or Ruby. Do not use for general debugging unless the issue concerns pattern structure or intent."
compatibility: "Works on Claude.ai, Claude Code, and the API. No MCP or network required. The optional validation script (scripts/validate_skill.py) needs Python 3."
license: MIT
metadata:
  author: Mosweed
  version: 1.0.0
  category: software-engineering
  tags: [design-patterns, gof, code-review, refactoring]
---

# GoF Design Patterns

A complete reference for the 23 Gang of Four design patterns. Each pattern
lives in its own file under `references/`, grouped by category. Every file
covers: intent, the problem it solves, solution, an ASCII structure diagram,
participants, a step-by-step walkthrough, runnable code in 8 languages
(Python, Java, C++, C#, TypeScript, Go, PHP, Ruby), when to use it,
pros & cons, and relations to other patterns.

## How to use this skill

1. Identify which pattern the user is asking about (or which one fits their
   problem — see the selection guide below).
2. **Read only the relevant file** from the table. Do not load all files;
   each one is large. Read more than one only when comparing patterns.
3. Answer from that file. When the user names a language, read only that
   file's section for that language (each file has `### Python`, `### Java`,
   etc. as headers) instead of loading the whole file or pasting all eight.
   Pattern files are 1,000+ lines, so don't read them top to bottom: first
   Grep the file for the headers you need (e.g. `^### Go` or `^## Pros`) with
   line numbers, then Read just that line range. The section order is fixed
   (see "Pattern file layout" below), so one Grep for `^##[#]? ` gives you a
   map of the whole file.

## Pattern file layout

Every pattern file has the same level-2 sections, in this order: Intent,
Problem It Solves, Solution, Structure, Participants, How It Works,
Code Examples (with `### Python`, `### Java`, `### C++`, `### C#`,
`### TypeScript`, `### Go`, `### PHP`, `### Ruby`), When To Use, Pros & Cons,
Relations to Other Patterns, Sources.

## Output formats

Match the answer to the task.

**Explaining one pattern:** intent in one sentence → when to use it → minimal
structure → one small idiomatic example in the requested language → common
pitfalls → related patterns.

**Choosing between patterns:** a comparison table, then a single recommendation
with the reason.

| Pattern | Use when | Avoid when | Trade-off |
|---|---|---|---|

**Reviewing code:** a findings table.

| File:line | Finding type | Pattern role affected | Why it matters | Suggested fix |
|---|---|---|---|---|

Finding type = `correctness`, `robustness`, or `deviation`. An idiomatic
language variant is **not** a finding — don't list it; only mention it if the
user might mistake it for a problem, and then label it clearly as intentional.

**Refactoring code:** name the target pattern and the smallest safe change
first, then give a patch or rewritten snippet. Don't rewrite unrelated logic.

## Scope note

This skill is a pattern reference, **not a general debugger**. It only finds
bugs that are *pattern* bugs (e.g. a non-thread-safe Singleton, an Observer
that never detaches subscribers, a Decorator that breaks the wrapped
interface). Ordinary logic or runtime bugs are out of scope — say so plainly
rather than forcing a pattern lens onto unrelated code.

If the user's problem is better solved without a GoF pattern, say so and
suggest the simpler design. Patterns are tools, not a goal in themselves.

## Reviewing a single implementation

When the user points at one class or file and asks if a pattern is correct:

1. Confirm which pattern is intended. If unclear, infer from the structure and
   state your assumption.
2. Read that pattern's file. Check the code against, in order:
   - **Participants** — is every required role present and playing its part?
   - **Structure** — do the relationships and delegation match the diagram?
   - **Cons / common pitfalls** — the failure is most often one of these.
3. Report **every** deviation from the pattern (file + line), even ones where
   the code still works — flag those as `deviation` and say what the canonical
   form would be. Explain why each matters. Reporting and fixing are separate:
   report all deviations, but when fixing only change what's broken or risky
   unless the user asks you to align working code to the textbook too.

See "Deviation vs idiomatic variant" below before flagging anything.

## Auditing a whole codebase

When the user asks to check the entire codebase for pattern-implementation
errors, **report first, fix only after approval**. Follow this workflow:

### 1. Scope
If the repo is large, agree on scope first (which directories, which
languages). Skip vendored / generated / third-party code.

### 2. Discover
Patterns are rarely labelled, so find candidate implementations by their
structural signals. Grep for these and inspect each hit:

| Pattern | Signals to grep for |
|---|---|
| Singleton | `getInstance`, `get_instance`, private/static instance field, `__new__` override |
| Factory Method / Abstract Factory | `create*()` / `make*()` returning an interface; a factory class with several `create*` methods |
| Builder | `.build()`, fluent `with*`/`set*` returning `this`/`self` |
| Prototype | `clone()`, `copy()`, `__copy__`, `__deepcopy__` |
| Adapter | a class wrapping another and renaming/translating its methods |
| Decorator | wrapper implementing the same interface as the object it holds |
| Proxy | same interface as the real subject; lazy init, caching, access checks, `__getattr__` |
| Composite | `add`/`remove`(child), a `children` collection, recursive operations |
| Facade | one class delegating into many subsystem classes |
| Flyweight | a factory/pool returning shared instances; intrinsic vs extrinsic state |
| Observer | `subscribe`/`unsubscribe`/`attach`/`detach`/`notify`/`addListener`/`emit` |
| Strategy | a context holding a strategy reference; `setStrategy` |
| State | state objects with transitions; `setState`/`changeState` |
| Command | command objects with `execute()` / `undo()` |
| Chain of Responsibility | `setNext`/`successor`/`handle` passing along a chain |
| Iterator | `hasNext`/`next`, `__iter__`/`__next__`, `Symbol.iterator`, `IEnumerable` |
| Mediator | a central coordinator others call instead of each other |
| Memento | `save`/`restore`, snapshot/state objects, a caretaker |
| Template Method | abstract base whose template method calls abstract steps |
| Visitor | `accept(visitor)`, `visit*` methods |
| Interpreter | expression classes with `interpret()` / `evaluate()` |

Distinguish "clearly meant to be pattern X but broken" from "merely resembles
X" — only the former is a finding. Read the relevant pattern file before
judging each candidate.

Treat pattern names in class names (`UserFactory`, `PaymentStrategy`,
`NotificationObserver`) as hints, not proof. A class called `...Factory` is not
automatically a Factory Method or Abstract Factory. Confirm the intent from
behavior and dependencies before reporting a finding.

### Deviation vs idiomatic variant
Flag a deviation when the code departs from the pattern's **intent or
structure** — a missing role, broken delegation, a leak, a swallowed
responsibility. Do **not** flag code merely because it differs from the Java
class diagram. Each pattern file gives idiomatic implementations for 8
languages on purpose: Python often replaces a Strategy interface with a plain
callable, Go uses struct composition instead of inheritance, C# uses events for
Observer, and so on. These are correct, not deviations. The test is: does it
still achieve what the pattern is *for*? If yes, it's idiomatic; if it quietly
loses a guarantee the pattern exists to provide, it's a deviation — report it
and name the lost guarantee.

### 3. Report (do NOT fix yet)
Produce one table for the user, then stop and wait for go-ahead:

| # | File:line | Pattern | Issue | Severity | Proposed fix |
|---|---|---|---|---|---|

Severity = **correctness** (broken / will misbehave) > **robustness** (works
now, fails under concurrency, growth, edge cases) > **deviation** (works, but
departs from the pattern's structure or intent). **Report deviations too** —
do not drop a finding just because the code runs fine. For each deviation,
state what the canonical form would be so the user can decide whether to keep
it. Order the table by severity (correctness first), but include every
category. If you found nothing wrong, say so — don't invent findings to fill
the table.

### 4. Fix (after approval)
Fix **incrementally**, one pattern or one file at a time, so each change is
reviewable — not one giant rewrite. After each fix state what changed and why.
Re-run tests if a test command is available. Touch only what the report listed
unless you find something new, in which case add it to the report rather than
silently fixing it.

## Pattern → file

### Creational (object creation)
| Pattern | File |
|---|---|
| Factory Method | `references/CREATIONAL/01-factory-method.md` |
| Abstract Factory | `references/CREATIONAL/02-abstract-factory.md` |
| Builder | `references/CREATIONAL/03-builder.md` |
| Prototype | `references/CREATIONAL/04-prototype.md` |
| Singleton | `references/CREATIONAL/05-singleton.md` |

### Structural (object composition)
| Pattern | File |
|---|---|
| Adapter | `references/STRUCTURAL/06-adapter.md` |
| Bridge | `references/STRUCTURAL/07-bridge.md` |
| Composite | `references/STRUCTURAL/08-composite.md` |
| Decorator | `references/STRUCTURAL/09-decorator.md` |
| Facade | `references/STRUCTURAL/10-facade.md` |
| Flyweight | `references/STRUCTURAL/11-flyweight.md` |
| Proxy | `references/STRUCTURAL/12-proxy.md` |

### Behavioral (communication & responsibility)
| Pattern | File |
|---|---|
| Chain of Responsibility | `references/BEHAVIORAL/13-chain-of-responsibility.md` |
| Command | `references/BEHAVIORAL/14-command.md` |
| Interpreter | `references/BEHAVIORAL/15-interpreter.md` |
| Iterator | `references/BEHAVIORAL/16-iterator.md` |
| Mediator | `references/BEHAVIORAL/17-mediator.md` |
| Memento | `references/BEHAVIORAL/18-memento.md` |
| Observer | `references/BEHAVIORAL/19-observer.md` |
| State | `references/BEHAVIORAL/20-state.md` |
| Strategy | `references/BEHAVIORAL/21-strategy.md` |
| Template Method | `references/BEHAVIORAL/22-template-method.md` |
| Visitor | `references/BEHAVIORAL/23-visitor.md` |

## Quick selection guide

- Decoupling object creation from client code → Factory Method (one product),
  Abstract Factory (families of products), Builder (complex multi-step
  construction), Prototype (cheap copying of expensive objects).
- Exactly one shared instance → Singleton (watch the global-state / testing cost).
- Make incompatible interfaces work together → Adapter. Simplify a complex
  subsystem → Facade.
- Add behavior at runtime without subclassing → Decorator. Control access
  (lazy load, caching, remote, auth) → Proxy.
- Tree / part-whole hierarchies → Composite. Decouple an abstraction from its
  implementation → Bridge. Many similar objects eating memory → Flyweight.
- Encapsulate requests, support undo/redo → Command. Multiple possible handlers
  for a request → Chain of Responsibility.
- React to state changes elsewhere → Observer. Behavior changes with internal
  state → State. Swappable algorithms → Strategy (composition) or
  Template Method (inheritance).
- Add operations to a class hierarchy without editing it → Visitor.
- Coordinate many objects without tight coupling → Mediator. Traverse a
  collection without exposing its internals → Iterator. Snapshot / restore
  state → Memento. Evaluate a grammar or DSL → Interpreter.

## Examples

Should trigger:
- "Explain the Observer pattern in Go" → explain-one-pattern format; read only
  the Observer file's Go section.
- "Should I use Strategy or State here?" → choosing-between format: comparison
  table, then one recommendation.
- "Is this a correct Singleton?" (with code) → review format: findings table.
- "Audit the whole codebase for design-pattern mistakes" → audit workflow:
  report first, fix only after approval.
- "Refactor this long if/else chain toward a pattern" → refactoring format.

Should NOT trigger (answer normally or defer to a debugging approach):
- "Why does this throw a NullPointerException?" — ordinary bug, no pattern angle.
- "Write a Python script to parse a CSV" — no pattern involved.
- General architecture or system-design questions unrelated to GoF patterns.

## Sources policy

When the user wants theoretical justification, definitions, trade-offs, or
citations, use the `## Sources` section of the relevant pattern file. Do not
invent citations. If a file lacks enough source information, say so rather than
filling the gap from memory.

## Final checks before answering

- Don't force a GoF pattern when a simpler design is better.
- Use only the requested language unless the user is comparing languages.
- Don't paste all eight language examples.
- Treat idiomatic language variants as correct, not as violations.
- When reviewing, keep reporting separate from fixing unless fixes were asked for.
- Keep examples minimal and runnable.
