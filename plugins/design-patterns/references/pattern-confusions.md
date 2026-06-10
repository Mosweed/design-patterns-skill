# Pattern Confusions

Load this file when the user asks a **comparison or selection** question — "Strategy
or State?", "is this an Adapter or a Facade?", "do I need a Factory here?". It covers
the classic mix-ups so you can answer without loading multiple 1,000+ line pattern
files. The per-pattern files remain the **source of truth** for implementation detail,
code examples, and citations — read them only when the user moves from *choosing* a
pattern to *implementing* one.

The recurring lesson: most of these patterns have near-identical class diagrams
(a wrapper holding a reference, a context delegating to an interface). **They differ
by intent, not by structure.** Decide by asking what problem the code is solving,
never by matching shapes.

---

## Strategy vs State

Both put behavior behind an interface and delegate from a context — the diagrams are
the same. The difference is **who drives the change**. In Strategy, the *client*
picks an algorithm and the strategies are independent of each other; swapping one is
a configuration decision. In State, the *object itself* changes behavior as its
internal state transitions; the state objects typically know about each other and
trigger the next transition. Strategy is "plug in an algorithm"; State is "a state
machine implemented as objects".

| Pattern | Core intent | Coupling/structure cue | Choose it when |
|---|---|---|---|
| Strategy | Make algorithms interchangeable | Strategies don't know each other; client injects one | The variation is an external choice (config, user input) |
| State | Let an object alter behavior when its state changes | States reference/create each other; context's `setState` is called *from inside* a state | Behavior depends on a lifecycle: Draft → Published, Connected → Closed |

**Tell-tale question:** who chooses the behavior — the client (Strategy), or the
object itself as a result of transitions (State)?

Full treatment: `BEHAVIORAL/21-strategy.md`, `BEHAVIORAL/20-state.md`.

---

## The four wrappers: Adapter vs Bridge vs Decorator vs Proxy

All four wrap an object and forward calls; all four diagrams are "class holds a
reference, delegates". Distinguish by intent. **Adapter** changes an object's
*interface* to one the client already expects — it exists because two interfaces
don't match. **Bridge** splits one class hierarchy into two (abstraction and
implementation) *up front, by design*, so both can evolve independently.
**Decorator** keeps the *same* interface but adds responsibilities, and decorators
stack recursively. **Proxy** also keeps the same interface but *controls access* —
lazy loading, caching, auth, remoting — adding no new behavior the client asked for.

Two quick discriminators: Adapter is the only one whose wrapper interface *differs*
from the wrappee's. Decorator vs Proxy: with Decorator the *client* composes the
wrappers and may stack several; with Proxy the wrapping is usually invisible to the
client and the proxy often manages the lifecycle of its subject.

| Pattern | Core intent | Coupling/structure cue | Choose it when |
|---|---|---|---|
| Adapter | Convert an existing interface to the one clients expect | Wrapper interface ≠ wrappee interface; applied retroactively | You must reuse a class whose interface doesn't fit |
| Bridge | Decouple abstraction from implementation so both vary | Two parallel hierarchies designed together from the start | You face a class explosion across two independent dimensions (Shape × Renderer) |
| Decorator | Add responsibilities dynamically, same interface | Wrappers stack; client builds the onion | You'd otherwise subclass for every feature combination |
| Proxy | Control access to an object, same interface | Wrapping transparent to client; proxy may create/cache the real subject | You need lazy init, caching, access control, or a remote stand-in |

**Tell-tale question:** does the wrapper change the interface (Adapter), add behavior
the client opts into (Decorator), gate access transparently (Proxy), or separate two
hierarchies designed to vary independently (Bridge)?

Full treatment: `STRUCTURAL/06-adapter.md`, `STRUCTURAL/07-bridge.md`,
`STRUCTURAL/09-decorator.md`, `STRUCTURAL/12-proxy.md`.

---

## Factory Method vs Abstract Factory vs Builder

**Factory Method** is one overridable method that subclasses implement to decide
which single product to create — the variation point is inheritance. **Abstract
Factory** is an *object* with several create methods that produces a whole *family*
of related products that must be used together (a consistent theme/platform).
**Builder** is about *one* complex object assembled in steps — many optional parts,
ordering constraints, or several representations from the same construction process.

Don't reach for any of them by default. If construction is a single `new` with a few
arguments and there is no polymorphic variation, **a plain constructor or a module-
level function is enough** — a `make_user()` function in Python or a static factory
function in Go is not a GoF pattern and doesn't need to be. Introduce Factory Method
only when *which* class gets instantiated must vary; Abstract Factory only when
products come in enforced families; Builder only when the telescoping-constructor
problem is real.

| Pattern | Core intent | Coupling/structure cue | Choose it when |
|---|---|---|---|
| Factory Method | Defer the choice of *one* product class to subclasses | One `create()` hook overridden per subclass | Framework/base class can't know the concrete type |
| Abstract Factory | Create *families* of related products consistently | An interface with multiple `createX()` methods; swap the whole factory | Products must match each other (Mac widgets vs Win widgets) |
| Builder | Construct one complex object step by step | Fluent steps + a final `build()`; same steps, different representations | Many optional parameters or multi-step assembly |
| Plain function/constructor | Just create the object | No hierarchy, no variation | One concrete type, simple arguments — most of the time |

**Tell-tale question:** is the variation *which class* (Factory Method), *which
family of classes* (Abstract Factory), or *how one object is assembled* (Builder) —
or is there no variation at all (plain constructor)?

Full treatment: `CREATIONAL/01-factory-method.md`, `CREATIONAL/02-abstract-factory.md`,
`CREATIONAL/03-builder.md`.

---

## Observer vs Mediator vs Pub-Sub/event-bus

**Observer** is a one-to-many dependency: subscribers register *directly with a
specific subject* and get notified when it changes — the subject knows its observer
list. **Mediator** centralizes many-to-many communication: colleagues talk only to
the mediator, which encodes the *interaction logic* between them; it's about
eliminating a web of mutual references. **Pub-Sub / event bus** (not a GoF pattern,
but constantly confused with both) inserts a broker and topic names between
publishers and subscribers, so neither side knows the other exists at all — maximum
decoupling, but the control flow becomes implicit and hard to trace.

Note: a Mediator is often *implemented* using Observer (colleagues notify the
mediator via events), which is why the two blur. The distinction stands: Observer
distributes *notifications*; Mediator owns *coordination logic*.

| Pattern | Core intent | Coupling/structure cue | Choose it when |
|---|---|---|---|
| Observer | Notify dependents when one subject changes | Subscribers register on the subject itself | Concrete objects need to react to one known source |
| Mediator | Centralize complex interaction logic between peers | Colleagues hold a mediator reference, never each other | N components with tangled mutual calls (dialog widgets) |
| Pub-Sub / event bus | Fully decouple senders from receivers via a broker | Topic/event names; neither side references the other | Cross-module or cross-process events; sender can't know receivers |

**Tell-tale question:** does the notifier know its listeners (Observer), does a
central object *decide what happens next* (Mediator), or does an anonymous broker
route by topic (Pub-Sub)?

Full treatment: `BEHAVIORAL/19-observer.md`, `BEHAVIORAL/17-mediator.md`.

---

## Composite vs Decorator

Both rely on recursive composition against a common interface, so their diagrams
look related — Decorator is essentially a degenerate Composite with exactly one
child. But the intents diverge completely. **Composite** models a *part-whole tree*
so clients can treat a leaf and a group uniformly (`Shape` vs `GroupOfShapes`); its
point is uniform treatment of hierarchies. **Decorator** wraps exactly one object to
*add responsibilities*; its point is feature extension without subclassing. A
Composite aggregates results from many children; a Decorator augments the result of
its single wrappee.

| Pattern | Core intent | Coupling/structure cue | Choose it when |
|---|---|---|---|
| Composite | Treat individual objects and compositions uniformly | Node holds *many* children; operations recurse over all | The domain is genuinely a tree (UI, files, org chart, AST) |
| Decorator | Add behavior to one object dynamically | Wrapper holds exactly *one* wrappee; behavior added before/after delegating | You need stackable optional features |

**Tell-tale question:** is the object a *container of many* whose operation
aggregates children (Composite), or a *skin over one* that enriches its behavior
(Decorator)?

Full treatment: `STRUCTURAL/08-composite.md`, `STRUCTURAL/09-decorator.md`.

---

## Command vs Strategy

Both encapsulate "something callable" in an object with one main method. **Strategy**
encapsulates *how* to do one job — interchangeable algorithms for the same task,
chosen for their different trade-offs, executed immediately by the context.
**Command** encapsulates *a request itself* — what to do, on which receiver, with
which arguments — so the request becomes a first-class object you can queue, log,
schedule, send across a boundary, and **undo**. A Strategy rarely carries its own
arguments; a Command is a frozen invocation.

| Pattern | Core intent | Coupling/structure cue | Choose it when |
|---|---|---|---|
| Strategy | Swap the algorithm for one task | Context calls `strategy.execute(data)` now; data flows in at call time | Same job, different ways of doing it |
| Command | Reify a request as an object | Command bundles receiver + args; invoker stores/queues it; often `undo()` | You need undo/redo, queues, macros, scheduling, audit logs |

**Tell-tale question:** would it ever make sense to store this object in a history
list, queue, or log and run/undo it later? Yes → Command. No, it's just "which
algorithm" → Strategy.

Full treatment: `BEHAVIORAL/14-command.md`, `BEHAVIORAL/21-strategy.md`.

---

## Template Method vs Strategy

Same goal — vary parts of an algorithm — solved with opposite mechanisms. **Template
Method** uses *inheritance*: a base class fixes the algorithm's skeleton and
subclasses override individual steps; the variation is decided at compile time and
you customize *parts* of the flow. **Strategy** uses *composition*: the whole
algorithm is an injected object, swappable at runtime, and the context's flow doesn't
change. Template Method couples variants to the base class (fragile-base-class risk);
Strategy keeps them independent at the cost of more objects and wiring.

| Pattern | Core intent | Coupling/structure cue | Choose it when |
|---|---|---|---|
| Template Method | Fix an algorithm skeleton, let subclasses fill in steps | Abstract base; `final` template calls protected hooks | Variants share most of the flow and differ in a few steps; runtime swapping not needed |
| Strategy | Swap the entire algorithm via an injected object | Context holds a strategy field; setter/constructor injection | Variants must change at runtime or stay decoupled from a class hierarchy |

**Tell-tale question:** do you vary *steps inside a fixed skeleton via subclassing*
(Template Method) or *the whole algorithm via an injected object* (Strategy)?

Full treatment: `BEHAVIORAL/22-template-method.md`, `BEHAVIORAL/21-strategy.md`.

---

## Facade vs Adapter vs Mediator

All three "sit in front of" other objects. **Facade** offers a *simplified* entry
point to a whole subsystem — it defines a new, smaller interface for convenience,
and the subsystem doesn't know the facade exists; clients may still bypass it.
**Adapter** makes one object conform to an interface the client *already requires* —
it doesn't simplify, it *translates*, usually wrapping a single class. **Mediator**
is bidirectional: the components it coordinates *know about and call back into* the
mediator; communication flows through the hub by design, not merely for convenience.

| Pattern | Core intent | Coupling/structure cue | Choose it when |
|---|---|---|---|
| Facade | Simplify access to a complex subsystem | One-way: facade calls subsystem; subsystem unaware; clients may bypass | You want an easy front door for the common use cases |
| Adapter | Match an existing object to a required interface | Target interface dictated by the client; typically wraps one object | Interfaces don't fit and you can't change either side |
| Mediator | Centralize peer-to-peer interaction logic | Two-way: colleagues hold a mediator reference and notify it | Components shouldn't reference each other directly |

**Tell-tale question:** does the front object exist to *simplify* (Facade), to
*conform to a pre-existing interface* (Adapter), or do the hidden objects *talk back
to it* as their coordinator (Mediator)?

Full treatment: `STRUCTURAL/10-facade.md`, `STRUCTURAL/06-adapter.md`,
`BEHAVIORAL/17-mediator.md`.

---

## Chain of Responsibility vs Decorator

Both build a linked sequence of same-interface objects where each delegates to the
next — structurally near-twins. **Chain of Responsibility** routes a *request* along
handlers until one takes responsibility; any handler may **stop the chain**, and
"nobody handled it" is a legal outcome. **Decorator** layers *behavior*: every
wrapper is expected to call through to its wrappee, all layers run, and breaking the
chain would be a bug. CoR is about *finding the right handler*; Decorator is about
*accumulating effects*.

```text
CoR:        auth -> rate-limit -> validate   (any link may stop and answer)
Decorator:  compress(encrypt(buffer(file)))  (every layer always runs)
```

| Pattern | Core intent | Coupling/structure cue | Choose it when |
|---|---|---|---|
| Chain of Responsibility | Find a handler; decouple sender from receiver | Handlers may short-circuit; order = priority; unhandled is allowed | Several candidate processors, each deciding to act or pass |
| Decorator | Stack behaviors on one object | Every wrapper delegates inward; all layers execute | Composable add-on features over a core operation |

**Tell-tale question:** is a link *allowed to stop the traversal and own the request*
(Chain of Responsibility), or must every layer run as part of the result (Decorator)?

Full treatment: `BEHAVIORAL/13-chain-of-responsibility.md`, `STRUCTURAL/09-decorator.md`.

---

## Prototype vs Factory Method

Both let client code obtain new objects without naming concrete classes. **Factory
Method** creates from scratch via a subclass-overridden hook — the variation lives in
a *class hierarchy of creators*. **Prototype** creates by *copying a pre-configured
instance* — the variation lives in *objects*, not classes: register differently
configured prototypes and clone the one you need. Prefer Prototype when
initialization is expensive or when configurations are data (built at runtime), and
Factory Method when the creator hierarchy already exists or compile-time variation is
natural. Prototype's cost: implementing `clone()` correctly, especially deep-vs-
shallow copies of referenced objects.

| Pattern | Core intent | Coupling/structure cue | Choose it when |
|---|---|---|---|
| Prototype | New objects by cloning configured exemplars | `clone()`/`copy()`; a registry of prototype instances | Expensive construction, or variants defined by configuration/data |
| Factory Method | New objects via an overridable creation hook | Creator subclasses, each binding one product class | Variants are distinct classes known at compile time |

**Tell-tale question:** does a new instance come from *copying a configured object*
(Prototype) or from *a subclass deciding which class to instantiate* (Factory Method)?

Full treatment: `CREATIONAL/04-prototype.md`, `CREATIONAL/01-factory-method.md`.

---

## Singleton vs static class vs dependency injection

Three answers to "there should be one of these". **Singleton** is an *instance* with
enforced single-ness and global access — it can implement interfaces, be lazily
initialized, and carry state, but it hides dependencies and makes tests order-
dependent. A **static class** (or module of free functions) is fine for *stateless*
utilities — no instance, no polymorphism, no lifecycle; the moment it holds mutable
state it inherits all of Singleton's problems with none of its flexibility.
**Dependency injection** drops the global-access half entirely: create one instance
at the composition root and *pass it in*; "exactly one" becomes a wiring decision,
not a class-enforced property. In modern, test-driven codebases DI is the default
answer; classic Singleton survives mainly for true process-wide resources (logger,
config cache) where threading discipline is handled.

| Approach | Core intent | Coupling/structure cue | Choose it when |
|---|---|---|---|
| Singleton | One instance + global access point, enforced by the class | `getInstance()`, private constructor, static field | A genuine process-wide resource; lazy init or an interface is needed |
| Static class / module functions | Namespace stateless helpers | No instance, no state, no interface | Pure functions (math, formatting) — nothing to mock or swap |
| Dependency injection | One instance by *convention*, passed explicitly | Constructor parameters; a composition root or container wires it | Almost always — you want testability and visible dependencies |

**Tell-tale question:** does the *class itself* need to enforce and expose the single
instance globally (Singleton), or can the application simply create one and inject it
(DI)? If there's no state at all, neither — use a static/module function.

Full treatment: `CREATIONAL/05-singleton.md`.

---

## Sources

- Gamma, Helm, Johnson, Vlissides, *Design Patterns: Elements of Reusable
  Object-Oriented Software*, Addison-Wesley, 1994 — especially each pattern's
  "Related Patterns" subsection and the "Discussion of Creational Patterns" and
  case-study comparisons, which are the original intent-level treatment of these
  overlaps.
- refactoring.guru, "Relations with Other Patterns" sections of the individual
  pattern pages and the dedicated comparison notes (e.g. Adapter vs Bridge vs
  Decorator vs Proxy, Strategy vs State, Command vs Strategy).
- The `## Relations to Other Patterns` and `## Sources` sections of the per-pattern
  files in this repository, which carry the detailed, per-pattern citations.
