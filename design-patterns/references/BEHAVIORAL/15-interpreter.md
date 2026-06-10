# Interpreter Pattern

**Category:** Behavioral
**Difficulty:** Advanced
**Also Known As:** Little Language

---

## Intent

Define a grammatical representation for a language and provide an interpreter to deal with that grammar. Given a language, define a representation for its grammar along with an interpreter that uses the representation to interpret sentences in the language.

---

## Problem It Solves

Some problems are best described in terms of a simple language with rules. Consider these scenarios:

- You need to evaluate boolean expressions built at runtime (e.g., from a config file or user input).
- You need a small query language to filter data without pulling in a full SQL engine.
- You need to parse and evaluate mathematical expressions stored as strings.
- You need to process regular-expression-like patterns for a specific, narrow domain.

In each case, the inputs are sentences in a small, well-defined grammar. Without the Interpreter pattern, you might write a tightly coupled, hard-to-extend parser with deeply nested conditionals. The Interpreter pattern gives you a composable, class-per-rule design where each grammar rule is an object, and parsing produces a tree of those objects that can be walked to produce a result.

---

## Solution

1. Define an `AbstractExpression` interface with an `interpret(context)` method.
2. For every **terminal** rule in the grammar (atoms that cannot be broken down further), create a `TerminalExpression` class.
3. For every **non-terminal** rule (rules composed of other rules), create a `NonTerminalExpression` class that holds child expressions and delegates to them.
4. A `Context` object carries information that is global to the interpretation (e.g., variable bindings, the input string being consumed).
5. The `Client` builds an **Abstract Syntax Tree (AST)** from these expression objects and then calls `interpret(context)` on the root.

---

## Structure (ASCII diagram)

```
         Client
           |
           | builds
           v
    +------+------+
    |    Context  |          (global interpretation state)
    +-------------+

    <<interface>>
  AbstractExpression
  +interpret(ctx)
        /\
       /  \
      /    \
     v      v
Terminal  NonTerminal
Expression  Expression
            +children: AbstractExpression[]
            +interpret(ctx)
              -> calls children.interpret(ctx)
              -> combines results

Example AST for "(salary > 50000) AND (department == 'Engineering')":

              AndExpression
             /             \
    GreaterThanExpr      EqualsExpr
    /         \           /       \
Variable    Literal   Variable   Literal
"salary"   50000   "dept"   "Engineering"
```

---

## Participants

| Participant | Role |
|---|---|
| **AbstractExpression** | Declares the `interpret(context)` interface that all concrete nodes implement. |
| **TerminalExpression** | Implements `interpret` for terminals in the grammar (leaves of the AST). Has no children. |
| **NonTerminalExpression** | Implements `interpret` for grammar rules that compose other rules. Holds references to child `AbstractExpression` objects. |
| **Context** | Contains information that is global to the interpreter — e.g., a variable name-to-value map, or a remaining input string. |
| **Client** | Builds (or receives) the AST and invokes `interpret`. May use a small parser to construct the tree from a string. |

---

## How It Works (step-by-step)

1. **Model the grammar.** Write down the BNF or grammar rules for your mini-language. Identify terminals (literals, variable names, operators) and non-terminals (compound expressions).
2. **Create one class per rule.** Every terminal rule becomes a `TerminalExpression`; every non-terminal becomes a `NonTerminalExpression`.
3. **Define a shared `interpret(context)` method.** Each class implements this method to perform its specific role: a literal returns its value, an AND node evaluates both children and returns their conjunction, etc.
4. **Set up the Context.** Populate the context with any data the expressions need at interpretation time (variable bindings, current position in the input, etc.).
5. **Build the AST.** The client (often with a small recursive-descent parser) constructs a tree of expression objects.
6. **Call `interpret` on the root.** The result propagates up from leaves to the root, combining results according to each non-terminal's logic.
7. **Optionally extend.** Add new expression types (new grammar rules) without modifying existing classes — open/closed principle applies cleanly here.

---

## Code Examples

### Python

```python
"""
Interpreter Pattern — Python
Real-world use case: A simple boolean query engine for filtering employee records.

Grammar:
    expr   ::= term ( 'AND' term | 'OR' term )*
    term   ::= 'NOT' term | comparison | '(' expr ')'
    comparison ::= field operator value
    field  ::= identifier
    operator ::= '>' | '<' | '==' | '>='| '<='| '!='
    value  ::= number | string

Usage: evaluate rule strings against a dict of employee attributes.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

class Context:
    """Holds the current record being evaluated."""

    def __init__(self, record: dict[str, Any]) -> None:
        self.record = record

    def get(self, field: str) -> Any:
        return self.record[field]


# ---------------------------------------------------------------------------
# Abstract Expression
# ---------------------------------------------------------------------------

class Expression(ABC):
    @abstractmethod
    def interpret(self, ctx: Context) -> bool:
        ...


# ---------------------------------------------------------------------------
# Terminal Expressions
# ---------------------------------------------------------------------------

class ComparisonExpression(Expression):
    """Evaluates a single field op value comparison."""

    OPS = {
        ">":  lambda a, b: a > b,
        "<":  lambda a, b: a < b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }

    def __init__(self, field: str, op: str, value: Any) -> None:
        if op not in self.OPS:
            raise ValueError(f"Unknown operator: {op}")
        self.field = field
        self.op = op
        self.value = value

    def interpret(self, ctx: Context) -> bool:
        actual = ctx.get(self.field)
        return self.OPS[self.op](actual, self.value)

    def __repr__(self) -> str:
        return f"({self.field} {self.op} {self.value!r})"


# ---------------------------------------------------------------------------
# Non-Terminal Expressions
# ---------------------------------------------------------------------------

class AndExpression(Expression):
    """Non-terminal: left AND right — both must be True."""

    def __init__(self, left: Expression, right: Expression) -> None:
        self.left = left
        self.right = right

    def interpret(self, ctx: Context) -> bool:
        return self.left.interpret(ctx) and self.right.interpret(ctx)

    def __repr__(self) -> str:
        return f"({self.left} AND {self.right})"


class OrExpression(Expression):
    """Non-terminal: left OR right — at least one must be True."""

    def __init__(self, left: Expression, right: Expression) -> None:
        self.left = left
        self.right = right

    def interpret(self, ctx: Context) -> bool:
        return self.left.interpret(ctx) or self.right.interpret(ctx)

    def __repr__(self) -> str:
        return f"({self.left} OR {self.right})"


class NotExpression(Expression):
    """Non-terminal: NOT expr — negates the child."""

    def __init__(self, expr: Expression) -> None:
        self.expr = expr

    def interpret(self, ctx: Context) -> bool:
        return not self.expr.interpret(ctx)

    def __repr__(self) -> str:
        return f"(NOT {self.expr})"


# ---------------------------------------------------------------------------
# Client: simple builder — in production you would have a real parser
# ---------------------------------------------------------------------------

def build_senior_engineering_rule() -> Expression:
    """
    Build the AST for:
        (department == 'Engineering') AND (salary >= 90000) AND (NOT (level == 'Junior'))
    """
    in_engineering = ComparisonExpression("department", "==", "Engineering")
    high_salary    = ComparisonExpression("salary", ">=", 90_000)
    is_junior      = ComparisonExpression("level", "==", "Junior")

    return AndExpression(
        AndExpression(in_engineering, high_salary),
        NotExpression(is_junior),
    )


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    employees = [
        {"name": "Alice",   "department": "Engineering", "salary": 120_000, "level": "Senior"},
        {"name": "Bob",     "department": "Engineering", "salary": 65_000,  "level": "Junior"},
        {"name": "Carol",   "department": "Marketing",   "salary": 95_000,  "level": "Senior"},
        {"name": "Dave",    "department": "Engineering", "salary": 110_000, "level": "Mid"},
        {"name": "Eve",     "department": "Engineering", "salary": 85_000,  "level": "Senior"},
    ]

    rule = build_senior_engineering_rule()
    print(f"Rule: {rule}\n")

    print("Matching employees (senior engineers earning >= $90k):")
    for emp in employees:
        ctx = Context(emp)
        if rule.interpret(ctx):
            print(f"  - {emp['name']} ({emp['level']}, ${emp['salary']:,})")

    # Output:
    # Matching employees (senior engineers earning >= $90k):
    #   - Alice (Senior, $120,000)
    #   - Dave  (Mid,    $110,000)
```

---

### Java

```java
/**
 * Interpreter Pattern — Java
 * Real-world use case: A mini expression language for firewall rule evaluation.
 *
 * Grammar:
 *   rule   ::= expr ('AND' expr | 'OR' expr)*
 *   expr   ::= 'NOT' expr | condition
 *   condition ::= field op value
 *   field  ::= 'src_ip' | 'dst_port' | 'protocol' | ...
 *   op     ::= '==' | '!=' | '>' | '<'
 *   value  ::= string | number
 */

import java.util.*;

// ---------------------------------------------------------------------------
// Context — represents an incoming network packet
// ---------------------------------------------------------------------------
class PacketContext {
    private final Map<String, Object> attributes;

    public PacketContext(Map<String, Object> attributes) {
        this.attributes = Collections.unmodifiableMap(attributes);
    }

    public Object get(String field) {
        if (!attributes.containsKey(field)) {
            throw new IllegalArgumentException("Unknown field: " + field);
        }
        return attributes.get(field);
    }
}

// ---------------------------------------------------------------------------
// Abstract Expression
// ---------------------------------------------------------------------------
interface FirewallExpression {
    /** Returns true if this rule allows (or matches) the packet. */
    boolean interpret(PacketContext ctx);
}

// ---------------------------------------------------------------------------
// Terminal Expressions
// ---------------------------------------------------------------------------
class FieldEqualsExpression implements FirewallExpression {
    private final String field;
    private final Object expectedValue;

    public FieldEqualsExpression(String field, Object expectedValue) {
        this.field = field;
        this.expectedValue = expectedValue;
    }

    @Override
    public boolean interpret(PacketContext ctx) {
        return Objects.equals(ctx.get(field), expectedValue);
    }

    @Override
    public String toString() {
        return field + " == " + expectedValue;
    }
}

class FieldGreaterThanExpression implements FirewallExpression {
    private final String field;
    private final int threshold;

    public FieldGreaterThanExpression(String field, int threshold) {
        this.field = field;
        this.threshold = threshold;
    }

    @Override
    public boolean interpret(PacketContext ctx) {
        Object val = ctx.get(field);
        if (!(val instanceof Integer)) {
            throw new IllegalStateException("Field " + field + " is not numeric");
        }
        return (Integer) val > threshold;
    }

    @Override
    public String toString() {
        return field + " > " + threshold;
    }
}

// ---------------------------------------------------------------------------
// Non-Terminal Expressions
// ---------------------------------------------------------------------------
class AndExpression implements FirewallExpression {
    private final FirewallExpression left;
    private final FirewallExpression right;

    public AndExpression(FirewallExpression left, FirewallExpression right) {
        this.left = left;
        this.right = right;
    }

    @Override
    public boolean interpret(PacketContext ctx) {
        return left.interpret(ctx) && right.interpret(ctx);
    }

    @Override
    public String toString() {
        return "(" + left + " AND " + right + ")";
    }
}

class OrExpression implements FirewallExpression {
    private final FirewallExpression left;
    private final FirewallExpression right;

    public OrExpression(FirewallExpression left, FirewallExpression right) {
        this.left = left;
        this.right = right;
    }

    @Override
    public boolean interpret(PacketContext ctx) {
        return left.interpret(ctx) || right.interpret(ctx);
    }

    @Override
    public String toString() {
        return "(" + left + " OR " + right + ")";
    }
}

class NotExpression implements FirewallExpression {
    private final FirewallExpression inner;

    public NotExpression(FirewallExpression inner) {
        this.inner = inner;
    }

    @Override
    public boolean interpret(PacketContext ctx) {
        return !inner.interpret(ctx);
    }

    @Override
    public String toString() {
        return "(NOT " + inner + ")";
    }
}

// ---------------------------------------------------------------------------
// Client / Demo
// ---------------------------------------------------------------------------
public class InterpreterDemo {

    /**
     * Build the AST for:
     *   (protocol == "TCP") AND (dst_port > 1024) AND (NOT (src_ip == "10.0.0.1"))
     * — Allow TCP packets to high ports not coming from a blocked IP.
     */
    static FirewallExpression buildAllowRule() {
        FirewallExpression isTcp       = new FieldEqualsExpression("protocol", "TCP");
        FirewallExpression highPort    = new FieldGreaterThanExpression("dst_port", 1024);
        FirewallExpression blockedIp   = new FieldEqualsExpression("src_ip", "10.0.0.1");
        FirewallExpression notBlocked  = new NotExpression(blockedIp);

        return new AndExpression(new AndExpression(isTcp, highPort), notBlocked);
    }

    public static void main(String[] args) {
        FirewallExpression rule = buildAllowRule();
        System.out.println("Firewall rule: " + rule);
        System.out.println();

        List<Map<String, Object>> packets = List.of(
            Map.of("protocol", "TCP",  "dst_port", 8080, "src_ip", "192.168.1.5"),  // ALLOW
            Map.of("protocol", "TCP",  "dst_port", 8080, "src_ip", "10.0.0.1"),     // DENY (blocked IP)
            Map.of("protocol", "UDP",  "dst_port", 53,   "src_ip", "192.168.1.5"),  // DENY (not TCP)
            Map.of("protocol", "TCP",  "dst_port", 80,   "src_ip", "192.168.1.5"),  // DENY (low port <=1024)
            Map.of("protocol", "TCP",  "dst_port", 443,  "src_ip", "172.16.0.99")   // ALLOW
        );

        for (Map<String, Object> pkt : packets) {
            PacketContext ctx = new PacketContext(pkt);
            String verdict = rule.interpret(ctx) ? "ALLOW" : "DENY ";
            System.out.printf("%s  src=%-15s proto=%-4s port=%d%n",
                verdict, pkt.get("src_ip"), pkt.get("protocol"), pkt.get("dst_port"));
        }
    }
}
```

---

### C++

```cpp
/**
 * Interpreter Pattern — C++17
 * Real-world use case: A simple arithmetic expression evaluator
 * with variable bindings (like a spreadsheet formula engine).
 *
 * Grammar:
 *   expr   ::= term (('+' | '-') term)*
 *   term   ::= factor (('*' | '/') factor)*
 *   factor ::= NUMBER | IDENTIFIER | '(' expr ')'
 */

#include <iostream>
#include <memory>
#include <string>
#include <unordered_map>
#include <stdexcept>

// ---------------------------------------------------------------------------
// Context — variable name -> value
// ---------------------------------------------------------------------------
class Context {
public:
    void set(const std::string& name, double value) {
        variables_[name] = value;
    }

    double get(const std::string& name) const {
        auto it = variables_.find(name);
        if (it == variables_.end()) {
            throw std::runtime_error("Undefined variable: " + name);
        }
        return it->second;
    }

private:
    std::unordered_map<std::string, double> variables_;
};

// ---------------------------------------------------------------------------
// Abstract Expression
// ---------------------------------------------------------------------------
class Expression {
public:
    virtual ~Expression() = default;
    virtual double interpret(const Context& ctx) const = 0;
    virtual std::string toString() const = 0;
};

using ExprPtr = std::unique_ptr<Expression>;

// ---------------------------------------------------------------------------
// Terminal Expressions
// ---------------------------------------------------------------------------

// A numeric literal: 42, 3.14
class NumberExpression : public Expression {
public:
    explicit NumberExpression(double value) : value_(value) {}

    double interpret(const Context& /*ctx*/) const override {
        return value_;
    }

    std::string toString() const override {
        return std::to_string(value_);
    }

private:
    double value_;
};

// A variable reference: x, total, taxRate
class VariableExpression : public Expression {
public:
    explicit VariableExpression(std::string name) : name_(std::move(name)) {}

    double interpret(const Context& ctx) const override {
        return ctx.get(name_);
    }

    std::string toString() const override {
        return name_;
    }

private:
    std::string name_;
};

// ---------------------------------------------------------------------------
// Non-Terminal Expressions
// ---------------------------------------------------------------------------

class BinaryExpression : public Expression {
public:
    BinaryExpression(ExprPtr left, char op, ExprPtr right)
        : left_(std::move(left)), op_(op), right_(std::move(right)) {}

    double interpret(const Context& ctx) const override {
        double l = left_->interpret(ctx);
        double r = right_->interpret(ctx);
        switch (op_) {
            case '+': return l + r;
            case '-': return l - r;
            case '*': return l * r;
            case '/':
                if (r == 0.0) throw std::runtime_error("Division by zero");
                return l / r;
            default:
                throw std::runtime_error(std::string("Unknown operator: ") + op_);
        }
    }

    std::string toString() const override {
        return "(" + left_->toString() + " " + op_ + " " + right_->toString() + ")";
    }

private:
    ExprPtr left_;
    char    op_;
    ExprPtr right_;
};

class UnaryMinusExpression : public Expression {
public:
    explicit UnaryMinusExpression(ExprPtr operand) : operand_(std::move(operand)) {}

    double interpret(const Context& ctx) const override {
        return -operand_->interpret(ctx);
    }

    std::string toString() const override {
        return "(-" + operand_->toString() + ")";
    }

private:
    ExprPtr operand_;
};

// ---------------------------------------------------------------------------
// Client: build and evaluate spreadsheet-like formulas
// ---------------------------------------------------------------------------
int main() {
    Context ctx;
    ctx.set("price",    29.99);
    ctx.set("quantity", 5.0);
    ctx.set("taxRate",  0.08);
    ctx.set("discount", 10.0);

    // Formula: (price * quantity) - discount + ((price * quantity) * taxRate)
    //          i.e., subtotal - discount + tax

    auto price    = std::make_unique<VariableExpression>("price");
    auto quantity = std::make_unique<VariableExpression>("quantity");
    auto discount = std::make_unique<VariableExpression>("discount");
    auto taxRate  = std::make_unique<VariableExpression>("taxRate");

    // subtotal = price * quantity
    auto subtotal = std::make_unique<BinaryExpression>(
        std::make_unique<VariableExpression>("price"), '*',
        std::make_unique<VariableExpression>("quantity")
    );

    // tax = subtotal * taxRate  (need a second subtotal node — expressions are consumed by move)
    auto subtotal2 = std::make_unique<BinaryExpression>(
        std::make_unique<VariableExpression>("price"), '*',
        std::make_unique<VariableExpression>("quantity")
    );
    auto tax = std::make_unique<BinaryExpression>(
        std::move(subtotal2), '*',
        std::make_unique<VariableExpression>("taxRate")
    );

    // total = (subtotal - discount) + tax
    auto afterDiscount = std::make_unique<BinaryExpression>(
        std::move(subtotal), '-',
        std::make_unique<VariableExpression>("discount")
    );
    auto total = std::make_unique<BinaryExpression>(
        std::move(afterDiscount), '+',
        std::move(tax)
    );

    std::cout << "Formula: " << total->toString() << "\n";
    std::cout << "Variables:\n";
    std::cout << "  price    = 29.99\n";
    std::cout << "  quantity = 5\n";
    std::cout << "  discount = 10.00\n";
    std::cout << "  taxRate  = 0.08\n\n";

    double result = total->interpret(ctx);
    std::cout << "Total = $" << result << "\n";
    // Expected: (29.99*5) - 10 + (29.99*5*0.08) = 149.95 - 10 + 11.996 = 151.946

    return 0;
}
```

---

### C#

```csharp
/**
 * Interpreter Pattern — C#
 * Real-world use case: A DSL for constructing database-style WHERE clause filters
 * applied in-memory to a collection of objects (like LINQ expression trees but
 * hand-rolled to illustrate the pattern).
 *
 * Grammar:
 *   filter  ::= clause ('AND' clause | 'OR' clause)*
 *   clause  ::= 'NOT' clause | comparison
 *   comparison ::= FIELD OP VALUE
 */

using System;
using System.Collections.Generic;

// ---------------------------------------------------------------------------
// Context — the object currently being evaluated
// ---------------------------------------------------------------------------
record Product(string Name, string Category, decimal Price, int Stock);

class EvalContext
{
    public Product Current { get; }
    public EvalContext(Product p) => Current = p;
}

// ---------------------------------------------------------------------------
// Abstract Expression
// ---------------------------------------------------------------------------
interface IFilterExpression
{
    bool Interpret(EvalContext ctx);
}

// ---------------------------------------------------------------------------
// Terminal Expressions
// ---------------------------------------------------------------------------
class CategoryEquals : IFilterExpression
{
    private readonly string _category;
    public CategoryEquals(string category) => _category = category;

    public bool Interpret(EvalContext ctx) =>
        string.Equals(ctx.Current.Category, _category, StringComparison.OrdinalIgnoreCase);

    public override string ToString() => $"Category == \"{_category}\"";
}

class PriceBelow : IFilterExpression
{
    private readonly decimal _max;
    public PriceBelow(decimal max) => _max = max;

    public bool Interpret(EvalContext ctx) => ctx.Current.Price < _max;

    public override string ToString() => $"Price < {_max}";
}

class InStock : IFilterExpression
{
    public bool Interpret(EvalContext ctx) => ctx.Current.Stock > 0;
    public override string ToString() => "Stock > 0";
}

// ---------------------------------------------------------------------------
// Non-Terminal Expressions
// ---------------------------------------------------------------------------
class AndFilter : IFilterExpression
{
    private readonly IFilterExpression _left, _right;
    public AndFilter(IFilterExpression left, IFilterExpression right)
        => (_left, _right) = (left, right);

    public bool Interpret(EvalContext ctx) =>
        _left.Interpret(ctx) && _right.Interpret(ctx);

    public override string ToString() => $"({_left} AND {_right})";
}

class OrFilter : IFilterExpression
{
    private readonly IFilterExpression _left, _right;
    public OrFilter(IFilterExpression left, IFilterExpression right)
        => (_left, _right) = (left, right);

    public bool Interpret(EvalContext ctx) =>
        _left.Interpret(ctx) || _right.Interpret(ctx);

    public override string ToString() => $"({_left} OR {_right})";
}

class NotFilter : IFilterExpression
{
    private readonly IFilterExpression _inner;
    public NotFilter(IFilterExpression inner) => _inner = inner;

    public bool Interpret(EvalContext ctx) => !_inner.Interpret(ctx);

    public override string ToString() => $"(NOT {_inner})";
}

// ---------------------------------------------------------------------------
// Client / Demo
// ---------------------------------------------------------------------------
class Program
{
    static void Main()
    {
        var products = new List<Product>
        {
            new("Laptop",      "Electronics", 999.99m,  15),
            new("Headphones",  "Electronics", 79.99m,    0),  // out of stock
            new("Coffee Mug",  "Kitchen",     12.50m,   50),
            new("Mechanical Keyboard", "Electronics", 149.99m, 8),
            new("Blender",     "Kitchen",     89.00m,    3),
            new("USB Hub",     "Electronics", 29.99m,   20),
        };

        // Build filter:  (Category == "Electronics" AND Price < 200) AND Stock > 0
        IFilterExpression filter = new AndFilter(
            new AndFilter(
                new CategoryEquals("Electronics"),
                new PriceBelow(200m)
            ),
            new InStock()
        );

        Console.WriteLine($"Filter: {filter}");
        Console.WriteLine();
        Console.WriteLine("Matching products:");

        foreach (var product in products)
        {
            var ctx = new EvalContext(product);
            if (filter.Interpret(ctx))
            {
                Console.WriteLine($"  {product.Name,-25} ${product.Price,8:F2}  stock={product.Stock}");
            }
        }

        Console.WriteLine();

        // Build a second filter: (Category == "Kitchen") OR (Price < 30)
        IFilterExpression bargainFilter = new OrFilter(
            new CategoryEquals("Kitchen"),
            new PriceBelow(30m)
        );

        Console.WriteLine($"Filter: {bargainFilter}");
        Console.WriteLine();
        Console.WriteLine("Matching products:");

        foreach (var product in products)
        {
            var ctx = new EvalContext(product);
            if (bargainFilter.Interpret(ctx))
            {
                Console.WriteLine($"  {product.Name,-25} ${product.Price,8:F2}");
            }
        }
    }
}
```

---

### TypeScript

```typescript
/**
 * Interpreter Pattern — TypeScript
 * Real-world use case: A permission/policy rule engine for a multi-tenant SaaS.
 * Policies are stored in JSON and evaluated at runtime.
 *
 * Grammar:
 *   policy  ::= rule ('AND' rule | 'OR' rule)*
 *   rule    ::= 'NOT' rule | condition
 *   condition ::= 'hasRole' ROLE
 *               | 'hasPermission' PERM
 *               | 'ownsResource' RESOURCE_TYPE
 *               | 'subscriptionTier' '>=' TIER
 */

// ---------------------------------------------------------------------------
// Context — the current user request being evaluated
// ---------------------------------------------------------------------------
interface UserContext {
  userId: string;
  roles: string[];
  permissions: string[];
  ownedResourceTypes: string[];
  subscriptionTier: number; // 1=Free, 2=Pro, 3=Enterprise
}

// ---------------------------------------------------------------------------
// Abstract Expression
// ---------------------------------------------------------------------------
interface PolicyExpression {
  interpret(ctx: UserContext): boolean;
  toString(): string;
}

// ---------------------------------------------------------------------------
// Terminal Expressions
// ---------------------------------------------------------------------------

class HasRole implements PolicyExpression {
  constructor(private readonly role: string) {}

  interpret(ctx: UserContext): boolean {
    return ctx.roles.includes(this.role);
  }

  toString(): string {
    return `hasRole("${this.role}")`;
  }
}

class HasPermission implements PolicyExpression {
  constructor(private readonly permission: string) {}

  interpret(ctx: UserContext): boolean {
    return ctx.permissions.includes(this.permission);
  }

  toString(): string {
    return `hasPermission("${this.permission}")`;
  }
}

class OwnsResource implements PolicyExpression {
  constructor(private readonly resourceType: string) {}

  interpret(ctx: UserContext): boolean {
    return ctx.ownedResourceTypes.includes(this.resourceType);
  }

  toString(): string {
    return `ownsResource("${this.resourceType}")`;
  }
}

class MinimumTier implements PolicyExpression {
  constructor(private readonly requiredTier: number) {}

  interpret(ctx: UserContext): boolean {
    return ctx.subscriptionTier >= this.requiredTier;
  }

  toString(): string {
    const names: Record<number, string> = { 1: "Free", 2: "Pro", 3: "Enterprise" };
    return `tier >= ${names[this.requiredTier] ?? this.requiredTier}`;
  }
}

// ---------------------------------------------------------------------------
// Non-Terminal Expressions
// ---------------------------------------------------------------------------

class AndPolicy implements PolicyExpression {
  constructor(
    private readonly left: PolicyExpression,
    private readonly right: PolicyExpression
  ) {}

  interpret(ctx: UserContext): boolean {
    return this.left.interpret(ctx) && this.right.interpret(ctx);
  }

  toString(): string {
    return `(${this.left} AND ${this.right})`;
  }
}

class OrPolicy implements PolicyExpression {
  constructor(
    private readonly left: PolicyExpression,
    private readonly right: PolicyExpression
  ) {}

  interpret(ctx: UserContext): boolean {
    return this.left.interpret(ctx) || this.right.interpret(ctx);
  }

  toString(): string {
    return `(${this.left} OR ${this.right})`;
  }
}

class NotPolicy implements PolicyExpression {
  constructor(private readonly inner: PolicyExpression) {}

  interpret(ctx: UserContext): boolean {
    return !this.inner.interpret(ctx);
  }

  toString(): string {
    return `(NOT ${this.inner})`;
  }
}

// ---------------------------------------------------------------------------
// Policy registry — maps feature names to expressions
// ---------------------------------------------------------------------------
const policies: Record<string, PolicyExpression> = {
  // Access the admin dashboard: must be admin AND at least Pro tier
  "admin.dashboard": new AndPolicy(
    new HasRole("admin"),
    new MinimumTier(2)
  ),

  // Export data: either have export permission, OR be an Enterprise admin
  "data.export": new OrPolicy(
    new HasPermission("data:export"),
    new AndPolicy(new HasRole("admin"), new MinimumTier(3))
  ),

  // Delete own posts: have the permission AND own the resource
  "post.delete": new AndPolicy(
    new HasPermission("post:delete"),
    new OwnsResource("post")
  ),
};

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------
const users: Array<{ name: string; ctx: UserContext }> = [
  {
    name: "Alice (Enterprise Admin)",
    ctx: {
      userId: "u1",
      roles: ["admin", "user"],
      permissions: ["data:export", "post:delete"],
      ownedResourceTypes: ["post", "comment"],
      subscriptionTier: 3,
    },
  },
  {
    name: "Bob (Pro User)",
    ctx: {
      userId: "u2",
      roles: ["user"],
      permissions: ["post:delete"],
      ownedResourceTypes: ["post"],
      subscriptionTier: 2,
    },
  },
  {
    name: "Carol (Free User)",
    ctx: {
      userId: "u3",
      roles: ["user"],
      permissions: [],
      ownedResourceTypes: [],
      subscriptionTier: 1,
    },
  },
];

console.log("Policy Evaluation Results:\n");

for (const { name, ctx } of users) {
  console.log(`  ${name}`);
  for (const [feature, policy] of Object.entries(policies)) {
    const allowed = policy.interpret(ctx) ? "ALLOW" : "DENY ";
    console.log(`    [${allowed}] ${feature}`);
  }
  console.log();
}
```

---

### Go

```go
// Interpreter Pattern — Go
// Real-world use case: A log filtering DSL that parses and evaluates
// simple filter expressions against structured log entries.
//
// Grammar:
//   expr   ::= term ('AND' term | 'OR' term)*
//   term   ::= 'NOT' term | comparison
//   comparison ::= FIELD OP VALUE
//   FIELD  ::= "level" | "service" | "status_code" | "latency_ms"
//   OP     ::= "==" | "!=" | ">" | "<" | ">="

package main

import (
	"fmt"
	"strings"
)

// ---------------------------------------------------------------------------
// Context — a single log entry
// ---------------------------------------------------------------------------

type LogEntry struct {
	Level      string // "DEBUG", "INFO", "WARN", "ERROR"
	Service    string
	StatusCode int
	LatencyMs  int
	Message    string
}

// ---------------------------------------------------------------------------
// Abstract Expression interface
// ---------------------------------------------------------------------------

type Expression interface {
	Interpret(entry LogEntry) bool
	String() string
}

// ---------------------------------------------------------------------------
// Terminal Expressions
// ---------------------------------------------------------------------------

// LevelEquals matches log entries by severity level.
type LevelEquals struct{ Level string }

func (e LevelEquals) Interpret(entry LogEntry) bool {
	return strings.EqualFold(entry.Level, e.Level)
}
func (e LevelEquals) String() string { return fmt.Sprintf(`level == %q`, e.Level) }

// ServiceEquals matches log entries by service name.
type ServiceEquals struct{ Service string }

func (e ServiceEquals) Interpret(entry LogEntry) bool {
	return strings.EqualFold(entry.Service, e.Service)
}
func (e ServiceEquals) String() string { return fmt.Sprintf(`service == %q`, e.Service) }

// StatusCodeAbove matches entries where the HTTP status code exceeds a threshold.
type StatusCodeAbove struct{ Threshold int }

func (e StatusCodeAbove) Interpret(entry LogEntry) bool {
	return entry.StatusCode > e.Threshold
}
func (e StatusCodeAbove) String() string {
	return fmt.Sprintf("status_code > %d", e.Threshold)
}

// LatencyAbove matches entries where latency exceeds a threshold (ms).
type LatencyAbove struct{ ThresholdMs int }

func (e LatencyAbove) Interpret(entry LogEntry) bool {
	return entry.LatencyMs > e.ThresholdMs
}
func (e LatencyAbove) String() string {
	return fmt.Sprintf("latency_ms > %d", e.ThresholdMs)
}

// ---------------------------------------------------------------------------
// Non-Terminal Expressions
// ---------------------------------------------------------------------------

type AndExpression struct{ Left, Right Expression }

func (e AndExpression) Interpret(entry LogEntry) bool {
	return e.Left.Interpret(entry) && e.Right.Interpret(entry)
}
func (e AndExpression) String() string {
	return fmt.Sprintf("(%s AND %s)", e.Left, e.Right)
}

type OrExpression struct{ Left, Right Expression }

func (e OrExpression) Interpret(entry LogEntry) bool {
	return e.Left.Interpret(entry) || e.Right.Interpret(entry)
}
func (e OrExpression) String() string {
	return fmt.Sprintf("(%s OR %s)", e.Left, e.Right)
}

type NotExpression struct{ Inner Expression }

func (e NotExpression) Interpret(entry LogEntry) bool {
	return !e.Inner.Interpret(entry)
}
func (e NotExpression) String() string {
	return fmt.Sprintf("(NOT %s)", e.Inner)
}

// ---------------------------------------------------------------------------
// Client: build and apply log filters
// ---------------------------------------------------------------------------

func main() {
	logs := []LogEntry{
		{Level: "ERROR",  Service: "payment-svc",   StatusCode: 500, LatencyMs: 320,  Message: "Internal server error"},
		{Level: "WARN",   Service: "auth-svc",       StatusCode: 429, LatencyMs: 85,   Message: "Rate limit exceeded"},
		{Level: "INFO",   Service: "payment-svc",   StatusCode: 200, LatencyMs: 1500, Message: "Payment processed (slow)"},
		{Level: "ERROR",  Service: "auth-svc",       StatusCode: 401, LatencyMs: 12,   Message: "Invalid token"},
		{Level: "DEBUG",  Service: "inventory-svc",  StatusCode: 200, LatencyMs: 5,    Message: "Cache hit"},
		{Level: "ERROR",  Service: "payment-svc",   StatusCode: 503, LatencyMs: 2100, Message: "Service unavailable"},
	}

	// Filter 1: Errors from payment-svc
	errorPayments := AndExpression{
		Left:  LevelEquals{Level: "ERROR"},
		Right: ServiceEquals{Service: "payment-svc"},
	}

	// Filter 2: Slow responses (>1000ms) OR server errors (status >= 500)
	alertFilter := OrExpression{
		Left:  LatencyAbove{ThresholdMs: 1000},
		Right: StatusCodeAbove{Threshold: 499},
	}

	filters := []Expression{errorPayments, alertFilter}
	labels := []string{"payment-svc errors", "alert: slow or 5xx"}

	for i, filter := range filters {
		fmt.Printf("Filter [%s]: %s\n", labels[i], filter)
		fmt.Println("Matches:")
		for _, entry := range logs {
			if filter.Interpret(entry) {
				fmt.Printf("  [%s] %s (%d, %dms) — %s\n",
					entry.Level, entry.Service, entry.StatusCode, entry.LatencyMs, entry.Message)
			}
		}
		fmt.Println()
	}
}
```

---

### PHP

```php
<?php
/**
 * Interpreter Pattern — PHP 8.1
 * Real-world use case: A coupon/discount eligibility engine.
 * Business rules are composed from primitive conditions and evaluated
 * against a shopping cart at checkout.
 *
 * Grammar:
 *   rule    ::= condition ('AND' condition | 'OR' condition)*
 *   condition ::= 'NOT' condition
 *               | 'cartTotal' '>=' AMOUNT
 *               | 'itemCount' '>=' COUNT
 *               | 'hasCategory' CATEGORY
 *               | 'isFirstOrder'
 *               | 'memberSince' '>=' DAYS
 */

declare(strict_types=1);

// ---------------------------------------------------------------------------
// Context — the current checkout session
// ---------------------------------------------------------------------------

final class CartContext
{
    public function __construct(
        public readonly float  $cartTotal,
        public readonly int    $itemCount,
        public readonly array  $categories,     // e.g. ['electronics', 'accessories']
        public readonly bool   $isFirstOrder,
        public readonly int    $memberSinceDays,
    ) {}
}

// ---------------------------------------------------------------------------
// Abstract Expression
// ---------------------------------------------------------------------------

interface DiscountExpression
{
    public function interpret(CartContext $ctx): bool;
    public function __toString(): string;
}

// ---------------------------------------------------------------------------
// Terminal Expressions
// ---------------------------------------------------------------------------

final class CartTotalAtLeast implements DiscountExpression
{
    public function __construct(private readonly float $minimum) {}

    public function interpret(CartContext $ctx): bool
    {
        return $ctx->cartTotal >= $this->minimum;
    }

    public function __toString(): string
    {
        return "cartTotal >= {$this->minimum}";
    }
}

final class ItemCountAtLeast implements DiscountExpression
{
    public function __construct(private readonly int $minimum) {}

    public function interpret(CartContext $ctx): bool
    {
        return $ctx->itemCount >= $this->minimum;
    }

    public function __toString(): string
    {
        return "itemCount >= {$this->minimum}";
    }
}

final class HasCategory implements DiscountExpression
{
    public function __construct(private readonly string $category) {}

    public function interpret(CartContext $ctx): bool
    {
        return in_array(strtolower($this->category), array_map('strtolower', $ctx->categories), true);
    }

    public function __toString(): string
    {
        return "hasCategory(\"{$this->category}\")";
    }
}

final class IsFirstOrder implements DiscountExpression
{
    public function interpret(CartContext $ctx): bool
    {
        return $ctx->isFirstOrder;
    }

    public function __toString(): string
    {
        return 'isFirstOrder';
    }
}

final class MemberSinceAtLeast implements DiscountExpression
{
    public function __construct(private readonly int $days) {}

    public function interpret(CartContext $ctx): bool
    {
        return $ctx->memberSinceDays >= $this->days;
    }

    public function __toString(): string
    {
        return "memberSince >= {$this->days} days";
    }
}

// ---------------------------------------------------------------------------
// Non-Terminal Expressions
// ---------------------------------------------------------------------------

final class AndRule implements DiscountExpression
{
    public function __construct(
        private readonly DiscountExpression $left,
        private readonly DiscountExpression $right,
    ) {}

    public function interpret(CartContext $ctx): bool
    {
        return $this->left->interpret($ctx) && $this->right->interpret($ctx);
    }

    public function __toString(): string
    {
        return "({$this->left} AND {$this->right})";
    }
}

final class OrRule implements DiscountExpression
{
    public function __construct(
        private readonly DiscountExpression $left,
        private readonly DiscountExpression $right,
    ) {}

    public function interpret(CartContext $ctx): bool
    {
        return $this->left->interpret($ctx) || $this->right->interpret($ctx);
    }

    public function __toString(): string
    {
        return "({$this->left} OR {$this->right})";
    }
}

final class NotRule implements DiscountExpression
{
    public function __construct(private readonly DiscountExpression $inner) {}

    public function interpret(CartContext $ctx): bool
    {
        return !$this->inner->interpret($ctx);
    }

    public function __toString(): string
    {
        return "(NOT {$this->inner})";
    }
}

// ---------------------------------------------------------------------------
// Coupon registry & demo
// ---------------------------------------------------------------------------

$coupons = [
    'WELCOME10' => new IsFirstOrder(),
    'BIGSPENDER' => new CartTotalAtLeast(200.0),
    'LOYAL30' => new AndRule(
        new MemberSinceAtLeast(365),
        new CartTotalAtLeast(100.0),
    ),
    'ELECTRONICS_BUNDLE' => new AndRule(
        new HasCategory('electronics'),
        new ItemCountAtLeast(3),
    ),
    'SPRING_SALE' => new OrRule(
        new CartTotalAtLeast(150.0),
        new AndRule(new HasCategory('clothing'), new ItemCountAtLeast(2)),
    ),
];

$carts = [
    'Alice (new user, $250 cart, 4 electronics)' => new CartContext(
        cartTotal: 250.0,
        itemCount: 4,
        categories: ['electronics', 'accessories'],
        isFirstOrder: true,
        memberSinceDays: 1,
    ),
    'Bob (loyal, $120 cart, 1 book)' => new CartContext(
        cartTotal: 120.0,
        itemCount: 1,
        categories: ['books'],
        isFirstOrder: false,
        memberSinceDays: 400,
    ),
    'Carol ($80 cart, 3 clothing items)' => new CartContext(
        cartTotal: 80.0,
        itemCount: 3,
        categories: ['clothing'],
        isFirstOrder: false,
        memberSinceDays: 90,
    ),
];

foreach ($carts as $description => $cart) {
    echo "Customer: {$description}\n";
    foreach ($coupons as $code => $rule) {
        $eligible = $rule->interpret($cart) ? 'ELIGIBLE' : 'NOT ELIGIBLE';
        echo "  [{$eligible}] {$code}\n";
    }
    echo "\n";
}
```

---

### Ruby

```ruby
# Interpreter Pattern — Ruby
# Real-world use case: A content moderation rule engine.
# Moderation rules are composed and evaluated against submitted posts.
#
# Grammar:
#   rule     ::= clause ('AND' clause | 'OR' clause)*
#   clause   ::= 'NOT' clause | condition
#   condition ::= 'contains_word' WORD
#               | 'word_count' OP NUMBER
#               | 'has_link'
#               | 'from_new_account'
#               | 'spam_score' OP NUMBER

# ---------------------------------------------------------------------------
# Context — a submitted post
# ---------------------------------------------------------------------------
Post = Struct.new(:body, :word_count, :has_link, :account_age_days, :spam_score, keyword_init: true) do
  def contains_word?(word)
    body.downcase.split(/\W+/).include?(word.downcase)
  end
end

# ---------------------------------------------------------------------------
# Abstract Expression (module mixin in Ruby style)
# ---------------------------------------------------------------------------
module ModerationExpression
  def interpret(post) = raise NotImplementedError, "#{self.class}#interpret not implemented"
end

# ---------------------------------------------------------------------------
# Terminal Expressions
# ---------------------------------------------------------------------------
class ContainsWord
  include ModerationExpression

  def initialize(word) = @word = word

  def interpret(post) = post.contains_word?(@word)

  def to_s = "contains_word(\"#{@word}\")"
end

class WordCountAbove
  include ModerationExpression

  def initialize(threshold) = @threshold = threshold

  def interpret(post) = post.word_count > @threshold

  def to_s = "word_count > #{@threshold}"
end

class HasLink
  include ModerationExpression

  def interpret(post) = post.has_link

  def to_s = "has_link"
end

class FromNewAccount
  include ModerationExpression

  def initialize(max_days: 30) = @max_days = max_days

  def interpret(post) = post.account_age_days <= @max_days

  def to_s = "account_age <= #{@max_days} days"
end

class SpamScoreAbove
  include ModerationExpression

  def initialize(threshold) = @threshold = threshold

  def interpret(post) = post.spam_score > @threshold

  def to_s = "spam_score > #{@threshold}"
end

# ---------------------------------------------------------------------------
# Non-Terminal Expressions
# ---------------------------------------------------------------------------
class AndRule
  include ModerationExpression

  def initialize(left, right) = (@left, @right = left, right)

  def interpret(post) = @left.interpret(post) && @right.interpret(post)

  def to_s = "(#{@left} AND #{@right})"
end

class OrRule
  include ModerationExpression

  def initialize(left, right) = (@left, @right = left, right)

  def interpret(post) = @left.interpret(post) || @right.interpret(post)

  def to_s = "(#{@left} OR #{@right})"
end

class NotRule
  include ModerationExpression

  def initialize(inner) = @inner = inner

  def interpret(post) = !@inner.interpret(post)

  def to_s = "(NOT #{@inner})"
end

# ---------------------------------------------------------------------------
# Client: moderation rules and demo posts
# ---------------------------------------------------------------------------

# Rule: Flag if spam score is high OR (new account AND has a link)
spam_rule = OrRule.new(
  SpamScoreAbove.new(0.7),
  AndRule.new(FromNewAccount.new(max_days: 7), HasLink.new)
)

# Rule: Flag if post contains a banned word AND is not from an established account
banned_word_rule = AndRule.new(
  OrRule.new(ContainsWord.new("casino"), ContainsWord.new("pharma")),
  NotRule.new(OrRule.new(
    # Established accounts (>90 days) get a pass on borderline words
    # This shows deep composition is straightforward
    SpamScoreAbove.new(0.5),
    FromNewAccount.new(max_days: 0)  # never matches (age > 0 always for any post)
  ))
)

rules = {
  "Spam detection" => spam_rule,
  "Banned words"   => banned_word_rule,
}

posts = [
  Post.new(body: "Win big at casino! Click here", word_count: 6,   has_link: true,  account_age_days: 3,   spam_score: 0.85),
  Post.new(body: "Check out my new blog post",    word_count: 7,   has_link: true,  account_age_days: 5,   spam_score: 0.2),
  Post.new(body: "Hello everyone, new here!",     word_count: 4,   has_link: false, account_age_days: 2,   spam_score: 0.1),
  Post.new(body: "Buy pharma supplies cheap",     word_count: 4,   has_link: false, account_age_days: 200, spam_score: 0.4),
  Post.new(body: "Great article on Ruby patterns", word_count: 5,  has_link: false, account_age_days: 730, spam_score: 0.05),
]

puts "Content Moderation Results\n\n"

posts.each_with_index do |post, i|
  puts "Post #{i + 1}: \"#{post.body}\""
  rules.each do |name, rule|
    result = rule.interpret(post) ? "FLAG" : "PASS"
    puts "  [#{result}] #{name}"
  end
  puts
end
```

---

## When To Use

- **Interpreting a simple language:** You have a mini-language (search queries, filter expressions, configuration DSLs, mathematical formulas, boolean rule engines) and need to parse and evaluate sentences at runtime.
- **Grammar is small and stable:** The Interpreter pattern maps one class to one grammar rule. If the grammar has dozens of rules, the class count becomes unwieldy — use a parser generator (ANTLR, PLY, yacc) instead.
- **Efficiency is not critical:** Because each node is a separate object and traversal involves virtual dispatch, the pattern is slower than a compiled or optimized interpreter. It is ideal for configurations, rules, or expressions evaluated infrequently.
- **You need easy extensibility:** Adding a new kind of expression (new grammar rule) only requires adding one class without touching existing code.
- **Validation and querying:** Rules that validate data records, filter log lines, check permissions, or evaluate coupon conditions are natural fits.

**Avoid when:**
- The grammar is complex (many rules, operator precedence, lookahead). Use a dedicated parser generator.
- Performance is critical and expressions are evaluated millions of times per second.
- The grammar changes very frequently — class proliferation makes large grammars painful to maintain.

---

## Pros & Cons

### Pros

- **Easy to extend the grammar.** Adding a new expression type is as simple as creating a new class implementing the `AbstractExpression` interface. Existing classes are untouched (Open/Closed Principle).
- **Grammar is explicit and readable.** Each class corresponds directly to a grammar rule, making the structure self-documenting.
- **Easy to add new interpretations.** You can create multiple `interpret`-like methods (e.g., `prettyPrint`, `toSQL`, `validate`) by adding new methods or using the Visitor pattern alongside Interpreter.
- **Composable by design.** Non-terminal expressions hold references to other expressions, naturally forming a Composite tree. Complex rules are built from simple, tested pieces.
- **Testable in isolation.** Each expression class is independent and can be unit-tested with a simple context object.

### Cons

- **Class proliferation.** Each grammar rule demands its own class. A grammar with 30 rules means 30+ classes, which can become difficult to navigate and maintain.
- **Complex grammars are hard to maintain.** As the grammar grows, the hierarchy of classes grows too, and the relationships between non-terminals become intricate.
- **Requires grammar understanding upfront.** Building the AST manually (or writing a parser to do so) demands a solid grasp of the grammar's structure; mistakes cascade through the tree.
- **Not efficient for large inputs.** Walking a tree of objects with virtual dispatch is considerably slower than table-driven or compiled interpreters.

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Composite** | The AST is a direct application of Composite. Non-terminal expressions are composites; terminal expressions are leaves. The Interpreter pattern is essentially Composite enriched with an `interpret` operation. |
| **Flyweight** | Terminal expressions (especially literals shared across many places in the grammar, like the number `0` or the boolean `true`) can be shared using Flyweight to reduce memory usage when building large ASTs. |
| **Iterator** | Iterators can be used to traverse the AST — for example, to print all terminal nodes, collect variable names, or validate the structure before interpretation. |
| **Visitor** | Adding many different operations to the expression classes (e.g., type-checking, optimization, code generation, pretty-printing) without modifying them is a textbook Visitor use case. The Visitor can traverse the AST and perform the operation externally. |

---

## Sources

- https://refactoring.guru/design-patterns/interpreter
- https://sourcemaking.com/design_patterns/interpreter
