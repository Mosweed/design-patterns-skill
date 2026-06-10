# Modern Alternatives to GoF Patterns

GoF (1994) was written for C++ and Smalltalk — languages without first-class
functions, built-in iteration protocols, events, or pattern matching. Modern
languages absorbed many patterns into features. This file supports two
judgments:

1. **Review:** is this code an *idiomatic variant* (correct) or a *broken
   pattern* (finding)? See SKILL.md, "Deviation vs idiomatic variant".
2. **Advice:** would the full GoF class hierarchy be over-engineering here?

Each section states what the language feature replaces, shows the minimal
form, and names the one case where the full GoF form still earns its keep.

---

## Strategy

A Strategy interface with one method is just a function type. Python callables,
JS functions, C# delegates / `Func<T,R>`, Java lambdas implementing a
functional interface, and Go function values all let the Context hold a
function instead of an object hierarchy — same interchangeability, no classes.

```python
def by_price(p): return p.price
products.sort(key=by_price)          # the key callable IS the strategy
```

```csharp
decimal Checkout(Func<decimal, decimal> discount, decimal total)
    => discount(total);
```

The full GoF form is still right when a strategy carries **state or multiple
related methods** (e.g. `estimate()` + `execute()` + configuration), where a
bag of loose functions would lose cohesion.

## Command

A command is "a request reified as a value". A closure capturing its arguments
does that in one line — `button.on_click(lambda: doc.save())` — so most
callback-style Command uses need no class.

```javascript
const queue = [];
queue.push(() => sendEmail(user));   // closure = command object
queue.forEach(cmd => cmd());
```

You still need the object form when the command must do more than execute:
**undo/redo** (the object stores inverse state), **queuing with inspection**
(priority, deduplication, logging by name), or **serialization** across a
process boundary — closures can't be persisted or introspected.

## Template Method

Template Method fixes an algorithm skeleton in a base class and lets subclasses
fill in steps via inheritance. Higher-order functions do the same with
composition: pass the variable steps in as parameters instead of overriding
abstract methods.

```python
def run_report(fetch, render):       # skeleton with injected steps
    data = fetch()
    validate(data)
    return render(data)
```

This avoids the fragile-base-class problem and is testable without
subclassing. Inheritance-based Template Method still makes sense when there
are **many interdependent steps sharing protected state**, or in a framework
where subclassing is the established extension point.

## Iterator

Every mainstream language ships the Iterator pattern as a protocol: Python
`__iter__`/`__next__` and generators, JS `Symbol.iterator` and generator
functions, C# `IEnumerable<T>` with `yield return`, Java `Iterable` and
Streams, Go `range` (and since Go 1.23, range-over-func iterators). Writing a
hand-rolled `hasNext()/next()` class in these languages is a smell, not rigor.

```csharp
IEnumerable<Node> Walk(Node n) {
    yield return n;
    foreach (var c in n.Children) foreach (var d in Walk(c)) yield return d;
}
```

A custom iterator object is only warranted when the protocol can't express the
need: **external iteration with explicit control** (pause, bidirectional,
multiple independent cursors over one mutable collection) or interop with an
API that demands a concrete iterator type.

## Observer

The subscribe/notify machinery is stdlib in most ecosystems: C# `event` with
multicast delegates, JS `EventTarget` in the browser and `EventEmitter` in
Node, Rx/observables for composable streams, and signals in modern frontend
frameworks (fine-grained reactive subscriptions). These handle attach, detach,
and dispatch so you don't maintain a listener list by hand.

```csharp
public event EventHandler<OrderPlaced> OrderPlaced;   // GoF Subject in one line
```

Hand-rolling Observer still makes sense when you need behavior the built-in
doesn't give: **ordered or prioritized notification, weak references to avoid
the lapsed-listener leak, synchronous veto semantics**, or a language (Go,
C++) with no standard event facility.

## Singleton

A module is a singleton: Python modules are initialized once and cached in
`sys.modules`; a JS/TS module's top-level scope runs once per process. An
exported instance gives you "exactly one" with zero ceremony.

```typescript
// config.ts — module scope runs once; every importer shares this instance
export const config = loadConfig();
```

A DI container with singleton lifetime is usually better than either: the
single-instance decision lives in composition wiring, not in the class, so
tests can substitute a fake without monkey-patching a global. Reserve the
classic `getInstance()` Singleton for cases with **no module system and no DI**
(small scripts, constrained embedded code) — and even then watch the
global-state cost flagged in the Singleton file.

## Prototype

Prototype exists because C++ couldn't copy an object without knowing its
concrete class. Modern copy facilities cover most of it: Python
`copy.copy`/`copy.deepcopy`, JS `structuredClone` and spread syntax
(`{ ...obj, name: "new" }` — shallow), C# record `with`-expressions, or a
serialization round-trip for a guaranteed deep copy.

```csharp
var draft = order with { Status = Status.Draft };   // copy + tweak, no clone()
```

A real `clone()` hierarchy is still right when copies must be made
**polymorphically through a base reference** with per-class control over what
is deep-copied, shared, or reset (caches, handles, IDs) — generic copiers
can't make those choices.

## Builder

Builder's original job — simulating optional and named parameters — is a
language feature now: Python keyword arguments and `@dataclass`, C# object
initializers and records, Kotlin/Python default values, JS object literals.

```python
@dataclass
class Server:
    host: str
    port: int = 8080
    tls: bool = True

srv = Server(host="api.local", port=9000)   # no builder needed
```

A real Builder still earns its keep in three cases: **many cross-field
invariants** validated once at `build()`, **staged construction** where steps
must happen in order or accumulate (e.g. assembling a query), and producing an
**immutable object** in a language without named arguments (Java). If the
builder just mirrors fields with `withX` setters and no validation, it's
ceremony.

## Factory Method

The pattern's core is "return an interface, hide the concrete type" — a plain
function does that. The GoF subclass-overrides-creation structure is the heavy
form, needed only when creation varies by subclass of an existing hierarchy.

```go
func NewStore(dsn string) (Store, error) {   // returns interface, picks impl
    if strings.HasPrefix(dsn, "postgres://") { return newPgStore(dsn) }
    return newMemStore(), nil
}
```

Keep the class-based form when a **framework base class performs an algorithm
and subclasses must supply the product** (the creator and the template method
are intertwined) — that coupling is the one thing a free function can't model.

## Decorator (pattern) vs language "decorators"

Name collision: the GoF Decorator wraps an *object* behind the same interface,
stackable at runtime per instance. Python `@decorator` syntax and JS/TS
decorators wrap a *function or class at definition time*; React HOCs and
middleware wrap functions. Related idea (transparent wrapping), different
mechanics (definition-time vs runtime, function vs object).

```python
@cache                       # wraps the function once, for all callers
def price(sku): ...
```

A function decorator applies to every call site uniformly; the GoF form lets
you wrap *some instances* and compose wrappers dynamically
(`Encrypted(Compressed(file))`). Use the object form when wrapping must be
**per-instance and decided at runtime**; don't flag a Python `@decorator` as a
malformed GoF Decorator — it's a different construct that happens to share the
name.

## Chain of Responsibility

Middleware pipelines are this pattern shipped as infrastructure: Express,
ASP.NET Core, and Rack all pass a request through an ordered list of handlers,
each deciding to act, short-circuit, or call `next`. A hand-built
`setNext()` linked list duplicates what the framework already provides.

```javascript
app.use(auth);        // each middleware: handle, or pass to next()
app.use(rateLimit);
app.use(routes);
```

Build the chain yourself only when **handlers are assembled dynamically at
runtime** outside any framework, or when links need non-linear behavior
(re-routing, retry with a different successor) that a flat pipeline can't
express.

## Visitor

Visitor exists to add operations to a closed class hierarchy without editing
it, using double dispatch. Languages with sum types replace it with exhaustive
pattern matching: Rust `match` over enums, Scala/Kotlin sealed classes, C#
switch patterns, TypeScript discriminated unions. The compiler's
exhaustiveness check replaces the "every visitor must handle every node"
guarantee.

```typescript
type Shape = { kind: "circle"; r: number } | { kind: "rect"; w: number; h: number };
function area(s: Shape): number {
    switch (s.kind) {
        case "circle": return Math.PI * s.r ** 2;
        case "rect":   return s.w * s.h;
    }   // compiler errors if a variant is unhandled
}
```

Classic double-dispatch Visitor is still needed when the hierarchy is **open
and owned by someone else** (you can't seal it or add a `kind` tag), or in
languages (Java pre-sealed-classes, C++) where matching on concrete type means
fragile `instanceof` cascades with no exhaustiveness check.

## Flyweight

Flyweight's sharing of intrinsic state is often already done for you: string
interning in Java/C#/Python, small-integer caching, `functools.lru_cache`
memoizing constructed objects, and object pools in game engines and DB
drivers.

```python
@lru_cache(maxsize=None)
def glyph(char: str, font: str) -> Glyph:   # one shared instance per key
    return Glyph(char, font)
```

The deliberate GoF form — an explicit factory plus a strict intrinsic/extrinsic
state split — is still warranted when memory pressure is the *design driver*
(millions of fine-grained objects) and you must **prove** sharing, control
eviction, or pass extrinsic state into every operation rather than store it.

---

## How to use this when reviewing

An idiomatic replacement from this file is **not** a deviation. Per SKILL.md's
rule, the test is whether the code still achieves what the pattern is *for*.
Flag it only when the modern shortcut silently drops a guarantee the pattern
exists to provide — and name the lost guarantee. Examples:

- A closure used as a Command is fine — unless the feature spec needs undo or
  a persisted queue, which the closure cannot give.
- A C# `event` is a correct Observer — unless listeners leak because nothing
  ever unsubscribes (the lapsed-listener pitfall applies either way).
- Keyword arguments instead of a Builder are fine — unless cross-field
  invariants now go unvalidated.
- A `switch` over a discriminated union replaces Visitor — unless the union is
  not exhaustively checked and new variants fall through silently.

When advising on new code, prefer the smallest construct in this file that
meets the actual requirements; reach for the full GoF hierarchy only when one
of the "still the right call" conditions above is genuinely present.

## Sources

- Gamma, E., Helm, R., Johnson, R., Vlissides, J. (1994). *Design Patterns:
  Elements of Reusable Object-Oriented Software.* Addison-Wesley.
- Official language documentation for the features cited: Python (data model,
  `copy`, `functools`, dataclasses), ECMAScript/MDN (iterators, modules,
  spread, `structuredClone`, EventTarget), C# (delegates, events,
  `IEnumerable`/`yield`, records, pattern matching), Java (lambdas, Streams,
  sealed classes), Go (range, range-over-func in Go 1.23), Rust (`match`),
  TypeScript (discriminated unions).
