# Visitor Pattern

**Category:** Behavioral  
**Also known as:** Double Dispatch

---

## Intent

Let you separate algorithms from the objects on which they operate. Define a new operation without changing the classes of the elements on which it operates, by placing the new behavior inside a separate object called a *visitor*.

---

## Problem It Solves

Imagine you have a complex object tree — say, an AST (Abstract Syntax Tree), a file-system hierarchy, or a graph of geometric shapes. You need to run several unrelated operations on every node in that structure: serialization, pretty-printing, validation, code generation, and so on.

Adding each operation directly to every node class would:

- Violate the **Single Responsibility Principle** — node classes accumulate unrelated logic.
- Violate the **Open/Closed Principle** — adding a new operation requires touching every class.
- Create a maintenance nightmare when the number of operations grows.

You want the object structure to remain stable while operations can vary freely and independently.

---

## Solution

1. Declare a **Visitor** interface that has a `visit` method for every concrete element class in the hierarchy.
2. Add an `accept(visitor)` method to every element class. The method does nothing but call `visitor.visit(this)` — passing itself to the visitor.
3. Create **ConcreteVisitor** classes that implement the Visitor interface. Each visitor encapsulates one algorithm; each `visit` overload handles one element type.
4. The **ObjectStructure** (a collection, composite, or tree) provides a way to iterate over its elements and call `accept` on each.

The key insight is **double dispatch**: the final method executed depends on both the runtime type of the visitor *and* the runtime type of the element. Normal method calls in most languages dispatch only on the receiver's type; the `accept` trick achieves the second dispatch.

---

## Structure (ASCII diagram)

```
┌──────────────────────────────────────────────────────────────────────┐
│                         «interface»                                  │
│                           Visitor                                    │
│──────────────────────────────────────────────────────────────────────│
│  + visitConcreteElementA(e: ConcreteElementA)                        │
│  + visitConcreteElementB(e: ConcreteElementB)                        │
└───────────────────────┬──────────────────────────────────────────────┘
                        │ implements
          ┌─────────────┴──────────────┐
          │                            │
┌─────────▼──────────┐      ┌──────────▼─────────┐
│  ConcreteVisitorA  │      │  ConcreteVisitorB   │
│────────────────────│      │────────────────────-│
│ + visitElemA(...)  │      │ + visitElemA(...)   │
│ + visitElemB(...)  │      │ + visitElemB(...)   │
└────────────────────┘      └─────────────────────┘

┌───────────────────────────────────────┐
│           «interface»                 │
│             Element                   │
│───────────────────────────────────────│
│  + accept(v: Visitor)                 │
└──────────────┬────────────────────────┘
               │ implements
   ┌───────────┴────────────┐
   │                        │
┌──▼──────────────┐   ┌─────▼───────────┐
│ ConcreteElementA│   │ ConcreteElementB │
│─────────────────│   │─────────────────│
│ + accept(v)     │   │ + accept(v)     │
│   v.visitA(this)│   │   v.visitB(this)│
│ + specificOpA() │   │ + specificOpB() │
└─────────────────┘   └─────────────────┘

┌──────────────────────────────┐
│       ObjectStructure        │
│──────────────────────────────│
│  elements: List<Element>     │
│  + accept(v: Visitor)        │  ──► iterates and calls element.accept(v)
└──────────────────────────────┘
```

---

## Participants

| Participant | Role |
|---|---|
| **Visitor** | Interface declaring `visit` methods for each concrete element type. |
| **ConcreteVisitor** | Implements the Visitor interface. Each class encapsulates one algorithm. Maintains local state accumulated during traversal. |
| **Element** | Interface declaring `accept(visitor)` which every concrete element must implement. |
| **ConcreteElement** | Implements `accept` by calling the matching `visit` method on the visitor, passing `this`. |
| **ObjectStructure** | Holds or iterates the element collection (composite tree, list, graph). Provides a high-level `accept` or `traverse` method to drive the traversal. |

---

## How It Works (step-by-step)

1. The client creates one or more **ConcreteVisitor** objects (e.g., `XmlExportVisitor`, `JsonExportVisitor`).
2. The client (or an **ObjectStructure**) iterates over each element in the hierarchy and calls `element.accept(visitor)`.
3. The element's `accept` method calls `visitor.visitConcreteElementX(this)`. This is the *second dispatch* — the correct overload is chosen based on the static type visible inside `accept`.
4. Inside the visitor's `visit` method, the visitor has access to the element's public API. It performs its algorithm and may accumulate results in its own fields.
5. After traversal, the client retrieves results directly from the visitor object.
6. To add a new operation, create a new ConcreteVisitor without touching any element class.
7. To add a new element type, implement `accept` in the new element *and* add a new `visit` method to every existing visitor — this is the main drawback.

---

## Code Examples

### Python

```python
"""
Visitor Pattern — Abstract Syntax Tree (AST) Evaluator and Pretty-Printer.

We model a simple arithmetic expression AST and apply two visitors:
  1. EvaluatorVisitor  — computes the numeric result.
  2. PrettyPrintVisitor — renders the expression as a human-readable string.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Visitor interface
# ---------------------------------------------------------------------------

class ExprVisitor(ABC):
    """Visitor interface — one visit method per concrete node type."""

    @abstractmethod
    def visit_number(self, node: "NumberNode") -> object:
        ...

    @abstractmethod
    def visit_binary_op(self, node: "BinaryOpNode") -> object:
        ...

    @abstractmethod
    def visit_unary_op(self, node: "UnaryOpNode") -> object:
        ...


# ---------------------------------------------------------------------------
# Element interface & concrete elements
# ---------------------------------------------------------------------------

class ExprNode(ABC):
    """Base element interface."""

    @abstractmethod
    def accept(self, visitor: ExprVisitor) -> object:
        ...


@dataclass
class NumberNode(ExprNode):
    """Leaf node — holds a numeric literal."""
    value: float

    def accept(self, visitor: ExprVisitor) -> object:
        return visitor.visit_number(self)


@dataclass
class BinaryOpNode(ExprNode):
    """Interior node — binary operation (+, -, *, /)."""
    operator: str  # '+' | '-' | '*' | '/'
    left: ExprNode
    right: ExprNode

    def accept(self, visitor: ExprVisitor) -> object:
        return visitor.visit_binary_op(self)


@dataclass
class UnaryOpNode(ExprNode):
    """Interior node — unary operation (currently only negation)."""
    operator: str  # '-'
    operand: ExprNode

    def accept(self, visitor: ExprVisitor) -> object:
        return visitor.visit_unary_op(self)


# ---------------------------------------------------------------------------
# Concrete Visitor 1 — Evaluator
# ---------------------------------------------------------------------------

class EvaluatorVisitor(ExprVisitor):
    """Walks the AST and computes the numeric value of the expression."""

    def visit_number(self, node: NumberNode) -> float:
        return node.value

    def visit_binary_op(self, node: BinaryOpNode) -> float:
        left_val = node.left.accept(self)
        right_val = node.right.accept(self)
        match node.operator:
            case '+': return left_val + right_val
            case '-': return left_val - right_val
            case '*': return left_val * right_val
            case '/':
                if right_val == 0:
                    raise ZeroDivisionError("Division by zero in expression.")
                return left_val / right_val
            case _:
                raise ValueError(f"Unknown operator: {node.operator}")

    def visit_unary_op(self, node: UnaryOpNode) -> float:
        operand_val = node.operand.accept(self)
        if node.operator == '-':
            return -operand_val
        raise ValueError(f"Unknown unary operator: {node.operator}")


# ---------------------------------------------------------------------------
# Concrete Visitor 2 — Pretty-Printer
# ---------------------------------------------------------------------------

class PrettyPrintVisitor(ExprVisitor):
    """Walks the AST and produces a human-readable infix string."""

    def visit_number(self, node: NumberNode) -> str:
        # Drop unnecessary trailing zeros
        return str(int(node.value)) if node.value == int(node.value) else str(node.value)

    def visit_binary_op(self, node: BinaryOpNode) -> str:
        left_str = node.left.accept(self)
        right_str = node.right.accept(self)
        return f"({left_str} {node.operator} {right_str})"

    def visit_unary_op(self, node: UnaryOpNode) -> str:
        operand_str = node.operand.accept(self)
        return f"({node.operator}{operand_str})"


# ---------------------------------------------------------------------------
# Concrete Visitor 3 — Variable Collector (demonstrates state accumulation)
# ---------------------------------------------------------------------------

class DepthCounterVisitor(ExprVisitor):
    """Counts the maximum depth of the AST."""

    def visit_number(self, node: NumberNode) -> int:
        return 1

    def visit_binary_op(self, node: BinaryOpNode) -> int:
        return 1 + max(node.left.accept(self), node.right.accept(self))

    def visit_unary_op(self, node: UnaryOpNode) -> int:
        return 1 + node.operand.accept(self)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Build AST for: (3 + 4) * -(2 - 1)
    #
    #        *
    #       / \
    #      +   neg
    #     / \   \
    #    3   4   -
    #            / \
    #           2   1

    ast = BinaryOpNode(
        operator='*',
        left=BinaryOpNode('+', NumberNode(3), NumberNode(4)),
        right=UnaryOpNode('-', BinaryOpNode('-', NumberNode(2), NumberNode(1))),
    )

    evaluator = EvaluatorVisitor()
    printer   = PrettyPrintVisitor()
    depth     = DepthCounterVisitor()

    result     = ast.accept(evaluator)
    expression = ast.accept(printer)
    max_depth  = ast.accept(depth)

    print(f"Expression : {expression}")
    print(f"Result     : {result}")
    print(f"AST depth  : {max_depth}")
    # Expression : ((3 + 4) * (-(2 - 1)))
    # Result     : -7.0
    # AST depth  : 4
```

---

### Java

```java
/**
 * Visitor Pattern — Document export pipeline.
 *
 * A document consists of different block elements: headings, paragraphs,
 * and code blocks. Two visitors export the document to HTML and Markdown.
 */

import java.util.ArrayList;
import java.util.List;

// ---------------------------------------------------------------------------
// Visitor interface
// ---------------------------------------------------------------------------

interface DocumentVisitor {
    String visitHeading(Heading heading);
    String visitParagraph(Paragraph paragraph);
    String visitCodeBlock(CodeBlock codeBlock);
}

// ---------------------------------------------------------------------------
// Element interface & concrete elements
// ---------------------------------------------------------------------------

interface DocElement {
    /** Calls the correct visit method and returns the visitor's output. */
    String accept(DocumentVisitor visitor);
}

class Heading implements DocElement {
    private final int level;   // 1–6
    private final String text;

    public Heading(int level, String text) {
        this.level = level;
        this.text  = text;
    }

    public int    getLevel() { return level; }
    public String getText()  { return text;  }

    @Override
    public String accept(DocumentVisitor visitor) {
        return visitor.visitHeading(this);
    }
}

class Paragraph implements DocElement {
    private final String text;

    public Paragraph(String text) { this.text = text; }

    public String getText() { return text; }

    @Override
    public String accept(DocumentVisitor visitor) {
        return visitor.visitParagraph(this);
    }
}

class CodeBlock implements DocElement {
    private final String language;
    private final String code;

    public CodeBlock(String language, String code) {
        this.language = language;
        this.code     = code;
    }

    public String getLanguage() { return language; }
    public String getCode()     { return code;     }

    @Override
    public String accept(DocumentVisitor visitor) {
        return visitor.visitCodeBlock(this);
    }
}

// ---------------------------------------------------------------------------
// Object structure — a document holds a list of elements
// ---------------------------------------------------------------------------

class Document {
    private final List<DocElement> elements = new ArrayList<>();

    public void add(DocElement element) { elements.add(element); }

    /** Run a visitor over every element and concatenate results. */
    public String export(DocumentVisitor visitor) {
        StringBuilder sb = new StringBuilder();
        for (DocElement element : elements) {
            sb.append(element.accept(visitor)).append("\n");
        }
        return sb.toString().stripTrailing();
    }
}

// ---------------------------------------------------------------------------
// Concrete Visitor 1 — HTML exporter
// ---------------------------------------------------------------------------

class HtmlExportVisitor implements DocumentVisitor {

    @Override
    public String visitHeading(Heading h) {
        int lvl = h.getLevel();
        return String.format("<h%d>%s</h%d>", lvl, escape(h.getText()), lvl);
    }

    @Override
    public String visitParagraph(Paragraph p) {
        return "<p>" + escape(p.getText()) + "</p>";
    }

    @Override
    public String visitCodeBlock(CodeBlock cb) {
        return String.format(
            "<pre><code class=\"language-%s\">%s</code></pre>",
            cb.getLanguage(), escape(cb.getCode())
        );
    }

    private String escape(String s) {
        return s.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;");
    }
}

// ---------------------------------------------------------------------------
// Concrete Visitor 2 — Markdown exporter
// ---------------------------------------------------------------------------

class MarkdownExportVisitor implements DocumentVisitor {

    @Override
    public String visitHeading(Heading h) {
        return "#".repeat(h.getLevel()) + " " + h.getText();
    }

    @Override
    public String visitParagraph(Paragraph p) {
        return p.getText();
    }

    @Override
    public String visitCodeBlock(CodeBlock cb) {
        return String.format("```%s\n%s\n```", cb.getLanguage(), cb.getCode());
    }
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

public class VisitorDemo {

    public static void main(String[] args) {
        Document doc = new Document();
        doc.add(new Heading(1, "Visitor Pattern in Java"));
        doc.add(new Paragraph("The Visitor pattern separates algorithms from object structures."));
        doc.add(new Heading(2, "Quick Example"));
        doc.add(new CodeBlock("java", "System.out.println(\"Hello, Visitor!\");"));
        doc.add(new Paragraph("Now export the same document to two formats without touching element classes."));

        System.out.println("=== HTML ===");
        System.out.println(doc.export(new HtmlExportVisitor()));

        System.out.println("\n=== Markdown ===");
        System.out.println(doc.export(new MarkdownExportVisitor()));
    }
}
```

---

### C++

```cpp
/**
 * Visitor Pattern — File-system node metrics.
 *
 * A file-system tree contains Files and Directories. Two visitors:
 *   1. SizeCalculatorVisitor  — sums up total bytes.
 *   2. InventoryVisitor       — lists every file with its path.
 */

#include <algorithm>
#include <iostream>
#include <memory>
#include <numeric>
#include <string>
#include <vector>

// Forward declarations
class File;
class Directory;

// ---------------------------------------------------------------------------
// Visitor interface
// ---------------------------------------------------------------------------

class FsVisitor {
public:
    virtual ~FsVisitor() = default;
    virtual void visitFile(const File& file)           = 0;
    virtual void visitDirectory(const Directory& dir)  = 0;
};

// ---------------------------------------------------------------------------
// Element interface
// ---------------------------------------------------------------------------

class FsNode {
public:
    virtual ~FsNode() = default;
    virtual void accept(FsVisitor& visitor) const = 0;
    virtual const std::string& name() const       = 0;
};

// ---------------------------------------------------------------------------
// Concrete elements
// ---------------------------------------------------------------------------

class File : public FsNode {
public:
    File(std::string name, std::size_t size)
        : name_(std::move(name)), size_(size) {}

    void accept(FsVisitor& visitor) const override {
        visitor.visitFile(*this);
    }

    const std::string& name() const override { return name_; }
    std::size_t        size() const          { return size_; }

private:
    std::string name_;
    std::size_t size_;  // bytes
};

class Directory : public FsNode {
public:
    explicit Directory(std::string name) : name_(std::move(name)) {}

    void addChild(std::shared_ptr<FsNode> child) {
        children_.push_back(std::move(child));
    }

    void accept(FsVisitor& visitor) const override {
        visitor.visitDirectory(*this);
        // Composite: propagate to children
        for (const auto& child : children_) {
            child->accept(visitor);
        }
    }

    const std::string&                          name()     const override { return name_;    }
    const std::vector<std::shared_ptr<FsNode>>& children() const         { return children_; }

private:
    std::string                          name_;
    std::vector<std::shared_ptr<FsNode>> children_;
};

// ---------------------------------------------------------------------------
// Concrete Visitor 1 — Size calculator
// ---------------------------------------------------------------------------

class SizeCalculatorVisitor : public FsVisitor {
public:
    void visitFile(const File& file) override {
        totalBytes_ += file.size();
        fileCount_++;
    }

    void visitDirectory(const Directory& /*dir*/) override {
        dirCount_++;
    }

    void report() const {
        std::cout << "Directories : " << dirCount_  << "\n"
                  << "Files       : " << fileCount_ << "\n"
                  << "Total size  : " << totalBytes_ << " bytes ("
                  << (totalBytes_ / 1024.0) << " KB)\n";
    }

private:
    std::size_t totalBytes_ = 0;
    int         fileCount_  = 0;
    int         dirCount_   = 0;
};

// ---------------------------------------------------------------------------
// Concrete Visitor 2 — Inventory lister
// ---------------------------------------------------------------------------

class InventoryVisitor : public FsVisitor {
public:
    void visitFile(const File& file) override {
        std::string path = currentPath_ + "/" + file.name();
        std::cout << "[FILE] " << path
                  << "  (" << file.size() << " B)\n";
    }

    void visitDirectory(const Directory& dir) override {
        currentPath_ += "/" + dir.name();
        std::cout << "[DIR ] " << currentPath_ << "\n";
    }

private:
    std::string currentPath_;
};

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

int main() {
    // Build a small file-system tree
    auto root = std::make_shared<Directory>("project");

    auto src = std::make_shared<Directory>("src");
    src->addChild(std::make_shared<File>("main.cpp",    4096));
    src->addChild(std::make_shared<File>("visitor.hpp", 2048));
    src->addChild(std::make_shared<File>("utils.cpp",   1024));

    auto docs = std::make_shared<Directory>("docs");
    docs->addChild(std::make_shared<File>("README.md",  512));
    docs->addChild(std::make_shared<File>("design.pdf", 204800));

    root->addChild(src);
    root->addChild(docs);
    root->addChild(std::make_shared<File>("CMakeLists.txt", 768));

    // Visitor 1
    std::cout << "=== Size Report ===\n";
    SizeCalculatorVisitor sizeCalc;
    root->accept(sizeCalc);
    sizeCalc.report();

    // Visitor 2
    std::cout << "\n=== Inventory ===\n";
    InventoryVisitor inventory;
    root->accept(inventory);

    return 0;
}
```

---

### C#

```csharp
/**
 * Visitor Pattern — Tax calculation for an e-commerce order.
 *
 * An order contains different line-item types: physical goods, digital goods,
 * and services. Two visitors apply different tax rules to each type.
 */

using System;
using System.Collections.Generic;

// ---------------------------------------------------------------------------
// Visitor interface
// ---------------------------------------------------------------------------

public interface IOrderItemVisitor
{
    decimal VisitPhysicalGood(PhysicalGood item);
    decimal VisitDigitalGood(DigitalGood item);
    decimal VisitService(ServiceItem item);
}

// ---------------------------------------------------------------------------
// Element interface & concrete elements
// ---------------------------------------------------------------------------

public interface IOrderItem
{
    string  Name        { get; }
    decimal UnitPrice   { get; }
    int     Quantity    { get; }

    /// <summary>Dispatches to the correct visitor method.</summary>
    decimal Accept(IOrderItemVisitor visitor);
}

public record PhysicalGood(string Name, decimal UnitPrice, int Quantity, decimal WeightKg)
    : IOrderItem
{
    public decimal Accept(IOrderItemVisitor visitor) => visitor.VisitPhysicalGood(this);
}

public record DigitalGood(string Name, decimal UnitPrice, int Quantity)
    : IOrderItem
{
    public decimal Accept(IOrderItemVisitor visitor) => visitor.VisitDigitalGood(this);
}

public record ServiceItem(string Name, decimal UnitPrice, int Quantity, bool IsRecurring)
    : IOrderItem
{
    public decimal Accept(IOrderItemVisitor visitor) => visitor.VisitService(this);
}

// ---------------------------------------------------------------------------
// Object structure — shopping order
// ---------------------------------------------------------------------------

public class Order
{
    private readonly List<IOrderItem> _items = new();

    public void Add(IOrderItem item) => _items.Add(item);

    /// <summary>Run a visitor over all items and return the aggregate result.</summary>
    public decimal CalculateWith(IOrderItemVisitor visitor)
    {
        decimal total = 0m;
        foreach (var item in _items)
            total += item.Accept(visitor);
        return total;
    }

    public void PrintSummary(IOrderItemVisitor taxVisitor, string label)
    {
        Console.WriteLine($"\n--- {label} ---");
        decimal grandTotal = 0m;
        foreach (var item in _items)
        {
            decimal tax      = item.Accept(taxVisitor);
            decimal subtotal = item.UnitPrice * item.Quantity;
            Console.WriteLine($"  {item.Name,-30} qty={item.Quantity}  " +
                              $"subtotal={subtotal:C}  tax={tax:C}");
            grandTotal += tax;
        }
        Console.WriteLine($"  {'Total Tax',-30}              {grandTotal:C}");
    }
}

// ---------------------------------------------------------------------------
// Concrete Visitor 1 — Standard tax (US domestic)
// ---------------------------------------------------------------------------

public class UsTaxVisitor : IOrderItemVisitor
{
    private const decimal PhysicalRate = 0.08m;   // 8 % sales tax
    private const decimal DigitalRate  = 0.06m;   // 6 % digital goods tax
    private const decimal ServiceRate  = 0.00m;   // services exempt

    public decimal VisitPhysicalGood(PhysicalGood item) =>
        item.UnitPrice * item.Quantity * PhysicalRate;

    public decimal VisitDigitalGood(DigitalGood item) =>
        item.UnitPrice * item.Quantity * DigitalRate;

    public decimal VisitService(ServiceItem item) =>
        item.UnitPrice * item.Quantity * ServiceRate;
}

// ---------------------------------------------------------------------------
// Concrete Visitor 2 — EU VAT
// ---------------------------------------------------------------------------

public class EuVatVisitor : IOrderItemVisitor
{
    private const decimal PhysicalRate  = 0.20m;  // 20 % VAT
    private const decimal DigitalRate   = 0.20m;  // digital services same rate
    private const decimal ServiceRate   = 0.20m;  // services also 20 %

    public decimal VisitPhysicalGood(PhysicalGood item) =>
        item.UnitPrice * item.Quantity * PhysicalRate;

    public decimal VisitDigitalGood(DigitalGood item) =>
        item.UnitPrice * item.Quantity * DigitalRate;

    public decimal VisitService(ServiceItem item) =>
        item.UnitPrice * item.Quantity * ServiceRate;
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

class Program
{
    static void Main()
    {
        var order = new Order();
        order.Add(new PhysicalGood("Mechanical Keyboard", 149.99m, 1, 1.2m));
        order.Add(new DigitalGood ("IDE License",          89.00m, 2));
        order.Add(new ServiceItem ("Annual Support Plan",  49.99m, 1, isRecurring: true));
        order.Add(new PhysicalGood("USB-C Hub",            39.99m, 3, 0.3m));

        order.PrintSummary(new UsTaxVisitor(), "US Tax Calculation");
        order.PrintSummary(new EuVatVisitor(), "EU VAT Calculation");
    }
}
```

---

### TypeScript

```typescript
/**
 * Visitor Pattern — CSS/HTML element validator.
 *
 * A UI component tree contains Buttons, TextInputs, and Container nodes.
 * Two visitors run over the tree:
 *   1. AccessibilityAuditVisitor — checks ARIA attributes and labels.
 *   2. StyleLintVisitor          — validates that required CSS properties are set.
 */

// ---------------------------------------------------------------------------
// Visitor interface
// ---------------------------------------------------------------------------

interface UiVisitor {
  visitButton(node: ButtonNode): AuditFinding[];
  visitTextInput(node: TextInputNode): AuditFinding[];
  visitContainer(node: ContainerNode): AuditFinding[];
}

interface AuditFinding {
  severity: "error" | "warning" | "info";
  message: string;
  nodeId: string;
}

// ---------------------------------------------------------------------------
// Element interface & concrete elements
// ---------------------------------------------------------------------------

interface UiNode {
  id: string;
  accept(visitor: UiVisitor): AuditFinding[];
}

class ButtonNode implements UiNode {
  constructor(
    public readonly id: string,
    public readonly label: string | null,
    public readonly ariaLabel: string | null,
    public readonly style: Record<string, string>,
    public readonly disabled: boolean = false
  ) {}

  accept(visitor: UiVisitor): AuditFinding[] {
    return visitor.visitButton(this);
  }
}

class TextInputNode implements UiNode {
  constructor(
    public readonly id: string,
    public readonly placeholder: string,
    public readonly associatedLabelId: string | null,
    public readonly style: Record<string, string>,
    public readonly required: boolean = false
  ) {}

  accept(visitor: UiVisitor): AuditFinding[] {
    return visitor.visitTextInput(this);
  }
}

class ContainerNode implements UiNode {
  public children: UiNode[] = [];

  constructor(
    public readonly id: string,
    public readonly role: string | null,
    public readonly style: Record<string, string>
  ) {}

  addChild(child: UiNode): this {
    this.children.push(child);
    return this;
  }

  accept(visitor: UiVisitor): AuditFinding[] {
    // First audit this node, then recurse into children.
    const findings = visitor.visitContainer(this);
    for (const child of this.children) {
      findings.push(...child.accept(visitor));
    }
    return findings;
  }
}

// ---------------------------------------------------------------------------
// Concrete Visitor 1 — Accessibility audit
// ---------------------------------------------------------------------------

class AccessibilityAuditVisitor implements UiVisitor {
  visitButton(node: ButtonNode): AuditFinding[] {
    const findings: AuditFinding[] = [];

    if (!node.label && !node.ariaLabel) {
      findings.push({
        severity: "error",
        message: "Button has neither a visible label nor an aria-label.",
        nodeId: node.id,
      });
    }

    if (node.disabled && !node.ariaLabel) {
      findings.push({
        severity: "warning",
        message: "Disabled button should have aria-label to explain why it is disabled.",
        nodeId: node.id,
      });
    }

    return findings;
  }

  visitTextInput(node: TextInputNode): AuditFinding[] {
    const findings: AuditFinding[] = [];

    if (!node.associatedLabelId) {
      findings.push({
        severity: "error",
        message: "TextInput is not associated with a <label> element.",
        nodeId: node.id,
      });
    }

    if (node.required && !node.placeholder.toLowerCase().includes("required")) {
      findings.push({
        severity: "info",
        message: "Required field — consider indicating 'required' in placeholder or label.",
        nodeId: node.id,
      });
    }

    return findings;
  }

  visitContainer(node: ContainerNode): AuditFinding[] {
    const findings: AuditFinding[] = [];

    if (!node.role) {
      findings.push({
        severity: "warning",
        message: "Container has no ARIA role — screen readers may not understand its purpose.",
        nodeId: node.id,
      });
    }

    return findings;
  }
}

// ---------------------------------------------------------------------------
// Concrete Visitor 2 — Style linter
// ---------------------------------------------------------------------------

class StyleLintVisitor implements UiVisitor {
  private requiredButtonProps  = ["background-color", "color", "border-radius"];
  private requiredInputProps   = ["border", "padding", "font-size"];
  private requiredContainerProps = ["display"];

  private checkMissingProps(
    style: Record<string, string>,
    required: string[],
    nodeId: string
  ): AuditFinding[] {
    return required
      .filter((prop) => !style[prop])
      .map((prop) => ({
        severity: "warning" as const,
        message: `Missing required CSS property: "${prop}".`,
        nodeId,
      }));
  }

  visitButton(node: ButtonNode): AuditFinding[] {
    return this.checkMissingProps(node.style, this.requiredButtonProps, node.id);
  }

  visitTextInput(node: TextInputNode): AuditFinding[] {
    return this.checkMissingProps(node.style, this.requiredInputProps, node.id);
  }

  visitContainer(node: ContainerNode): AuditFinding[] {
    return this.checkMissingProps(node.style, this.requiredContainerProps, node.id);
  }
}

// ---------------------------------------------------------------------------
// Helper — run an audit and print a formatted report
// ---------------------------------------------------------------------------

function runAudit(root: UiNode, visitor: UiVisitor, name: string): void {
  const findings = root.accept(visitor);
  console.log(`\n=== ${name} ===`);
  if (findings.length === 0) {
    console.log("  No issues found.");
    return;
  }
  for (const f of findings) {
    const icon = f.severity === "error" ? "✗" : f.severity === "warning" ? "⚠" : "ℹ";
    console.log(`  [${icon}] (${f.nodeId}) ${f.message}`);
  }
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

const form = new ContainerNode("form-root", "form", { display: "flex" });

form.addChild(
  new TextInputNode(
    "email-input",
    "Enter email",
    "email-label",     // correctly associated
    { border: "1px solid #ccc", padding: "8px", "font-size": "14px" },
    true               // required
  )
);

form.addChild(
  new TextInputNode(
    "phone-input",
    "Phone number",
    null,              // missing label association — a11y error
    { border: "1px solid #ccc" }  // missing padding & font-size
  )
);

form.addChild(
  new ButtonNode(
    "submit-btn",
    "Submit",
    null,
    { "background-color": "#007bff", color: "#fff", "border-radius": "4px" }
  )
);

form.addChild(
  new ButtonNode(
    "reset-btn",
    null,             // no label — a11y error
    null,
    { "background-color": "#6c757d" },  // missing color & border-radius
    true
  )
);

runAudit(form, new AccessibilityAuditVisitor(), "Accessibility Audit");
runAudit(form, new StyleLintVisitor(),          "Style Lint");
```

---

### Go

```go
// Visitor Pattern — Serialization of a configuration tree.
//
// A config tree contains StringValue, IntValue, BoolValue, and Section nodes.
// Two visitors serialize the tree to JSON and to INI format.

package main

import (
	"fmt"
	"strings"
)

// ---------------------------------------------------------------------------
// Visitor interface
// ---------------------------------------------------------------------------

type ConfigVisitor interface {
	VisitStringValue(node *StringValue) string
	VisitIntValue(node *IntValue) string
	VisitBoolValue(node *BoolValue) string
	VisitSection(node *Section) string
}

// ---------------------------------------------------------------------------
// Element interface & concrete elements
// ---------------------------------------------------------------------------

type ConfigNode interface {
	Key() string
	Accept(v ConfigVisitor) string
}

// StringValue leaf
type StringValue struct {
	key   string
	Value string
}

func NewStringValue(key, value string) *StringValue { return &StringValue{key: key, Value: value} }
func (n *StringValue) Key() string                  { return n.key }
func (n *StringValue) Accept(v ConfigVisitor) string { return v.VisitStringValue(n) }

// IntValue leaf
type IntValue struct {
	key   string
	Value int
}

func NewIntValue(key string, value int) *IntValue { return &IntValue{key: key, Value: value} }
func (n *IntValue) Key() string                   { return n.key }
func (n *IntValue) Accept(v ConfigVisitor) string  { return v.VisitIntValue(n) }

// BoolValue leaf
type BoolValue struct {
	key   string
	Value bool
}

func NewBoolValue(key string, value bool) *BoolValue { return &BoolValue{key: key, Value: value} }
func (n *BoolValue) Key() string                     { return n.key }
func (n *BoolValue) Accept(v ConfigVisitor) string    { return v.VisitBoolValue(n) }

// Section (composite) — contains other nodes
type Section struct {
	key      string
	children []ConfigNode
}

func NewSection(key string) *Section { return &Section{key: key} }
func (n *Section) Key() string       { return n.key }
func (n *Section) Add(child ConfigNode) { n.children = append(n.children, child) }
func (n *Section) Children() []ConfigNode { return n.children }
func (n *Section) Accept(v ConfigVisitor) string { return v.VisitSection(n) }

// ---------------------------------------------------------------------------
// Concrete Visitor 1 — JSON serializer
// ---------------------------------------------------------------------------

type JSONVisitor struct {
	indent int
}

func (v *JSONVisitor) pad() string { return strings.Repeat("  ", v.indent) }

func (v *JSONVisitor) VisitStringValue(n *StringValue) string {
	return fmt.Sprintf("%q: %q", n.Key(), n.Value)
}

func (v *JSONVisitor) VisitIntValue(n *IntValue) string {
	return fmt.Sprintf("%q: %d", n.Key(), n.Value)
}

func (v *JSONVisitor) VisitBoolValue(n *BoolValue) string {
	return fmt.Sprintf("%q: %v", n.Key(), n.Value)
}

func (v *JSONVisitor) VisitSection(n *Section) string {
	v.indent++
	parts := make([]string, 0, len(n.Children()))
	for _, child := range n.Children() {
		parts = append(parts, v.pad()+child.Accept(v))
	}
	v.indent--
	inner := strings.Join(parts, ",\n")
	return fmt.Sprintf("%q: {\n%s\n%s}", n.Key(), inner, v.pad())
}

// ---------------------------------------------------------------------------
// Concrete Visitor 2 — INI serializer
// ---------------------------------------------------------------------------

type INIVisitor struct {
	currentSection string
	lines          []string
}

func (v *INIVisitor) VisitStringValue(n *StringValue) string {
	line := fmt.Sprintf("%s = %s", n.Key(), n.Value)
	v.lines = append(v.lines, line)
	return line
}

func (v *INIVisitor) VisitIntValue(n *IntValue) string {
	line := fmt.Sprintf("%s = %d", n.Key(), n.Value)
	v.lines = append(v.lines, line)
	return line
}

func (v *INIVisitor) VisitBoolValue(n *BoolValue) string {
	val := "false"
	if n.Value {
		val = "true"
	}
	line := fmt.Sprintf("%s = %s", n.Key(), val)
	v.lines = append(v.lines, line)
	return line
}

func (v *INIVisitor) VisitSection(n *Section) string {
	prev := v.currentSection
	v.currentSection = n.Key()
	v.lines = append(v.lines, fmt.Sprintf("[%s]", n.Key()))
	for _, child := range n.Children() {
		child.Accept(v)
	}
	v.currentSection = prev
	v.lines = append(v.lines, "") // blank line between sections
	return strings.Join(v.lines, "\n")
}

func (v *INIVisitor) Result() string { return strings.Join(v.lines, "\n") }

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

func main() {
	// Build a configuration tree
	root := NewSection("config")

	database := NewSection("database")
	database.Add(NewStringValue("host", "localhost"))
	database.Add(NewIntValue("port", 5432))
	database.Add(NewStringValue("name", "myapp_db"))
	database.Add(NewBoolValue("ssl", true))

	server := NewSection("server")
	server.Add(NewStringValue("host", "0.0.0.0"))
	server.Add(NewIntValue("port", 8080))
	server.Add(NewBoolValue("debug", false))

	root.Add(database)
	root.Add(server)

	// JSON output
	jsonVisitor := &JSONVisitor{}
	fmt.Println("=== JSON ===")
	fmt.Println("{")
	for _, child := range root.Children() {
		fmt.Println("  " + child.Accept(jsonVisitor))
	}
	fmt.Println("}")

	// INI output
	iniVisitor := &INIVisitor{}
	for _, child := range root.Children() {
		child.Accept(iniVisitor)
	}
	fmt.Println("\n=== INI ===")
	fmt.Println(iniVisitor.Result())
}
```

---

### PHP

```php
<?php
/**
 * Visitor Pattern — Invoice renderer.
 *
 * An invoice contains line items of different types: ProductLine, DiscountLine,
 * and TaxLine. Two visitors render the invoice:
 *   1. PlainTextRenderer — produces a terminal-friendly text table.
 *   2. HtmlRenderer      — produces an HTML <table>.
 */

declare(strict_types=1);

// ---------------------------------------------------------------------------
// Visitor interface
// ---------------------------------------------------------------------------

interface InvoiceVisitor
{
    public function visitProductLine(ProductLine $line): string;
    public function visitDiscountLine(DiscountLine $line): string;
    public function visitTaxLine(TaxLine $line): string;
}

// ---------------------------------------------------------------------------
// Element interface & concrete elements
// ---------------------------------------------------------------------------

interface InvoiceLine
{
    public function getDescription(): string;
    public function getAmount(): float;
    public function accept(InvoiceVisitor $visitor): string;
}

final class ProductLine implements InvoiceLine
{
    public function __construct(
        private readonly string $sku,
        private readonly string $description,
        private readonly int    $quantity,
        private readonly float  $unitPrice
    ) {}

    public function getSku(): string       { return $this->sku;       }
    public function getQuantity(): int     { return $this->quantity;   }
    public function getUnitPrice(): float  { return $this->unitPrice;  }
    public function getDescription(): string { return $this->description; }
    public function getAmount(): float     { return $this->quantity * $this->unitPrice; }

    public function accept(InvoiceVisitor $visitor): string
    {
        return $visitor->visitProductLine($this);
    }
}

final class DiscountLine implements InvoiceLine
{
    public function __construct(
        private readonly string $reason,
        private readonly float  $amount   // negative value
    ) {}

    public function getDescription(): string { return "Discount: {$this->reason}"; }
    public function getAmount(): float       { return $this->amount; }

    public function accept(InvoiceVisitor $visitor): string
    {
        return $visitor->visitDiscountLine($this);
    }
}

final class TaxLine implements InvoiceLine
{
    public function __construct(
        private readonly string $taxName,
        private readonly float  $rate,
        private readonly float  $baseAmount
    ) {}

    public function getTaxName(): string  { return $this->taxName;   }
    public function getRate(): float      { return $this->rate;       }
    public function getDescription(): string { return "{$this->taxName} ({$this->rate}%)"; }
    public function getAmount(): float    { return round($this->baseAmount * $this->rate / 100, 2); }

    public function accept(InvoiceVisitor $visitor): string
    {
        return $visitor->visitTaxLine($this);
    }
}

// ---------------------------------------------------------------------------
// Object structure — Invoice
// ---------------------------------------------------------------------------

final class Invoice
{
    /** @var InvoiceLine[] */
    private array $lines = [];

    public function __construct(
        private readonly string $invoiceNumber,
        private readonly string $customerName
    ) {}

    public function addLine(InvoiceLine $line): void
    {
        $this->lines[] = $line;
    }

    public function getInvoiceNumber(): string  { return $this->invoiceNumber; }
    public function getCustomerName(): string   { return $this->customerName;  }

    /** @return InvoiceLine[] */
    public function getLines(): array { return $this->lines; }

    public function getTotal(): float
    {
        return array_sum(array_map(fn($l) => $l->getAmount(), $this->lines));
    }

    public function render(InvoiceVisitor $visitor): string
    {
        $rows = array_map(fn($line) => $line->accept($visitor), $this->lines);
        return implode("\n", $rows);
    }
}

// ---------------------------------------------------------------------------
// Concrete Visitor 1 — Plain-text renderer
// ---------------------------------------------------------------------------

final class PlainTextRenderer implements InvoiceVisitor
{
    private function row(string $desc, string $amount): string
    {
        return sprintf("  %-40s %10s", $desc, $amount);
    }

    public function visitProductLine(ProductLine $line): string
    {
        $detail = "{$line->getDescription()} (x{$line->getQuantity()} @ \${$line->getUnitPrice()})";
        return $this->row($detail, '$' . number_format($line->getAmount(), 2));
    }

    public function visitDiscountLine(DiscountLine $line): string
    {
        return $this->row($line->getDescription(), '-$' . number_format(abs($line->getAmount()), 2));
    }

    public function visitTaxLine(TaxLine $line): string
    {
        return $this->row($line->getDescription(), '$' . number_format($line->getAmount(), 2));
    }
}

// ---------------------------------------------------------------------------
// Concrete Visitor 2 — HTML renderer
// ---------------------------------------------------------------------------

final class HtmlRenderer implements InvoiceVisitor
{
    private function tr(string $desc, float $amount, string $class = ''): string
    {
        $cls = $class ? " class=\"{$class}\"" : '';
        $formatted = ($amount < 0 ? '-' : '') . '$' . number_format(abs($amount), 2);
        return "<tr{$cls}><td>" . htmlspecialchars($desc) . "</td><td>{$formatted}</td></tr>";
    }

    public function visitProductLine(ProductLine $line): string
    {
        $desc = "{$line->getDescription()} &times; {$line->getQuantity()}";
        return $this->tr($desc, $line->getAmount(), 'product');
    }

    public function visitDiscountLine(DiscountLine $line): string
    {
        return $this->tr($line->getDescription(), $line->getAmount(), 'discount');
    }

    public function visitTaxLine(TaxLine $line): string
    {
        return $this->tr($line->getDescription(), $line->getAmount(), 'tax');
    }
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

$invoice = new Invoice('INV-2024-0042', 'Acme Corporation');
$invoice->addLine(new ProductLine('KB-001', 'Mechanical Keyboard',    2, 149.99));
$invoice->addLine(new ProductLine('MN-007', '4K Monitor',             1, 399.00));
$invoice->addLine(new DiscountLine('Loyalty discount 10%',           -69.90));
$invoice->addLine(new TaxLine('VAT', 20.0, $invoice->getTotal() + 69.90));

// Plain-text
echo "=== Plain Text Invoice ===\n";
echo "Invoice: {$invoice->getInvoiceNumber()}  Customer: {$invoice->getCustomerName()}\n";
echo str_repeat('-', 55) . "\n";
echo $invoice->render(new PlainTextRenderer()) . "\n";
echo str_repeat('-', 55) . "\n";
echo sprintf("  %-40s %10s\n", 'TOTAL', '$' . number_format($invoice->getTotal(), 2));

// HTML
echo "\n=== HTML Invoice ===\n";
echo "<table>\n";
echo "  <caption>Invoice {$invoice->getInvoiceNumber()} — {$invoice->getCustomerName()}</caption>\n";
echo $invoice->render(new HtmlRenderer()) . "\n";
echo sprintf(
    "  <tr class=\"total\"><td><strong>Total</strong></td><td>%s</td></tr>\n",
    '$' . number_format($invoice->getTotal(), 2)
);
echo "</table>\n";
```

---

### Ruby

```ruby
# Visitor Pattern — Shape area/perimeter calculator and SVG renderer.
#
# A drawing canvas contains Circles, Rectangles, and Triangles.
# Two visitors process the shapes:
#   1. MetricsVisitor — computes area and perimeter.
#   2. SvgVisitor     — renders each shape as an SVG element string.

require 'bigdecimal'
require 'bigdecimal/util'

# ---------------------------------------------------------------------------
# Visitor interface (duck-typed in Ruby; documented for clarity)
# ---------------------------------------------------------------------------
# Expected methods:
#   visit_circle(shape)
#   visit_rectangle(shape)
#   visit_triangle(shape)

# ---------------------------------------------------------------------------
# Element base + concrete shapes
# ---------------------------------------------------------------------------

class Shape
  attr_reader :id, :fill, :stroke

  def initialize(id, fill: '#cce', stroke: '#333')
    @id     = id
    @fill   = fill
    @stroke = stroke
  end

  # Subclasses must implement: accept(visitor)
end

class Circle < Shape
  attr_reader :cx, :cy, :radius

  def initialize(id, cx:, cy:, radius:, **opts)
    super(id, **opts)
    @cx     = cx
    @cy     = cy
    @radius = radius
  end

  def accept(visitor)
    visitor.visit_circle(self)
  end
end

class Rectangle < Shape
  attr_reader :x, :y, :width, :height

  def initialize(id, x:, y:, width:, height:, **opts)
    super(id, **opts)
    @x      = x
    @y      = y
    @width  = width
    @height = height
  end

  def accept(visitor)
    visitor.visit_rectangle(self)
  end
end

class Triangle < Shape
  # Defined by three vertices: [[x1,y1],[x2,y2],[x3,y3]]
  attr_reader :vertices

  def initialize(id, vertices:, **opts)
    super(id, **opts)
    raise ArgumentError, 'Triangle requires exactly 3 vertices' unless vertices.size == 3
    @vertices = vertices
  end

  def accept(visitor)
    visitor.visit_triangle(self)
  end
end

# ---------------------------------------------------------------------------
# Object structure — a drawing canvas
# ---------------------------------------------------------------------------

class Canvas
  def initialize
    @shapes = []
  end

  def add(shape)
    @shapes << shape
    self
  end

  def each(&block)
    @shapes.each(&block)
  end

  # Run visitor over all shapes; return array of results
  def accept(visitor)
    @shapes.map { |s| s.accept(visitor) }
  end
end

# ---------------------------------------------------------------------------
# Concrete Visitor 1 — Metrics (area + perimeter)
# ---------------------------------------------------------------------------

class MetricsVisitor
  ShapeMetrics = Struct.new(:id, :area, :perimeter)

  def visit_circle(shape)
    r   = shape.radius.to_f
    ShapeMetrics.new(
      shape.id,
      (Math::PI * r * r).round(4),
      (2 * Math::PI * r).round(4)
    )
  end

  def visit_rectangle(shape)
    w, h = shape.width.to_f, shape.height.to_f
    ShapeMetrics.new(shape.id, (w * h).round(4), (2 * (w + h)).round(4))
  end

  def visit_triangle(shape)
    pts  = shape.vertices
    # Area via shoelace formula
    area = (
      pts[0][0] * (pts[1][1] - pts[2][1]) +
      pts[1][0] * (pts[2][1] - pts[0][1]) +
      pts[2][0] * (pts[0][1] - pts[1][1])
    ).abs / 2.0

    # Perimeter = sum of side lengths
    perim = (0..2).sum do |i|
      x1, y1 = pts[i]
      x2, y2 = pts[(i + 1) % 3]
      Math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    end

    ShapeMetrics.new(shape.id, area.round(4), perim.round(4))
  end
end

# ---------------------------------------------------------------------------
# Concrete Visitor 2 — SVG renderer
# ---------------------------------------------------------------------------

class SvgVisitor
  def visit_circle(shape)
    %(<circle id="#{shape.id}" cx="#{shape.cx}" cy="#{shape.cy}" ) +
      %(r="#{shape.radius}" fill="#{shape.fill}" stroke="#{shape.stroke}" stroke-width="2"/>)
  end

  def visit_rectangle(shape)
    %(<rect id="#{shape.id}" x="#{shape.x}" y="#{shape.y}" ) +
      %(width="#{shape.width}" height="#{shape.height}" ) +
      %(fill="#{shape.fill}" stroke="#{shape.stroke}" stroke-width="2"/>)
  end

  def visit_triangle(shape)
    pts_str = shape.vertices.map { |x, y| "#{x},#{y}" }.join(' ')
    %(<polygon id="#{shape.id}" points="#{pts_str}" ) +
      %(fill="#{shape.fill}" stroke="#{shape.stroke}" stroke-width="2"/>)
  end
end

# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

canvas = Canvas.new
canvas
  .add(Circle.new('c1',    cx: 100, cy: 100, radius: 50,  fill: '#fdd'))
  .add(Rectangle.new('r1', x: 200,  y: 50,  width: 120, height: 80, fill: '#dfd'))
  .add(Triangle.new('t1',  vertices: [[350, 130], [400, 50], [450, 130]], fill: '#ddf'))

puts '=== Metrics ==='
metrics_visitor = MetricsVisitor.new
canvas.accept(metrics_visitor).each do |m|
  puts "  #{m.id}: area=#{m.area}  perimeter=#{m.perimeter}"
end

puts "\n=== SVG Output ==="
puts '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="200">'
svg_visitor = SvgVisitor.new
canvas.accept(svg_visitor).each { |line| puts "  #{line}" }
puts '</svg>'
```

---

## When To Use

- **You need to perform many distinct, unrelated operations** on all elements of a complex object structure (tree, graph, composite) without polluting their classes with that logic.
- **The element hierarchy is stable** but you frequently add new operations. Adding a visitor is far cheaper than modifying every element class.
- **You want to accumulate state across a traversal** — a visitor object can collect results (totals, lists, statistics) as it visits each element, something that is awkward to do with methods scattered across element classes.
- **Business logic needs to be grouped by operation**, not by element type. Having one class represent one operation (e.g., `TaxCalculator`, `HtmlExporter`) is cleaner than having tax logic and export logic interleaved inside every element.
- **Elements expose enough public interface** for visitors to do their work without needing private access.

---

## Pros & Cons

### Pros

| Benefit | Detail |
|---|---|
| **Open/Closed Principle** | Add new operations by creating new visitors — existing element classes are untouched. |
| **Single Responsibility Principle** | Each visitor class encapsulates exactly one algorithm, keeping it cohesive and easy to test. |
| **State accumulation** | A visitor can build up cumulative results (counts, totals, rendered output) across the full traversal in its own fields. |
| **Separation of concerns** | Algorithmic details live in visitors; structural details live in elements. Neither leaks into the other. |

### Cons

| Drawback | Detail |
|---|---|
| **Fragile on element changes** | Adding or removing a concrete element class requires updating *every* visitor — the interface breaks. |
| **Encapsulation may be broken** | Visitors need access to element internals to do useful work. If those internals are private, you must expose them (widening the public API) or use friend/package-private mechanisms. |
| **Awkward in languages without overloading** | Languages without method overloading (or without clean double-dispatch) require workarounds such as reflection, type switches, or manually named methods. |
| **Increased number of classes** | Each new operation demands a new class, which can bloat the codebase if operations are many. |

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Command** | Both encapsulate an operation in an object. Command targets a *single* receiver; Visitor targets *many* heterogeneous receivers via double dispatch. |
| **Composite** | Visitor is frequently used *together with* Composite. The Composite's recursive `accept` drives the traversal; the Visitor defines what to do at each node. |
| **Interpreter** | Visitor can be used to implement evaluation or transformation passes over an Interpreter's AST — each grammar rule is a node type, each semantic action is a visitor. |
| **Iterator** | Iterator abstracts *how* you traverse a collection; Visitor abstracts *what* you do at each element. They can be combined: an iterator drives the loop, a visitor processes each item. |

---

## Sources

- https://refactoring.guru/design-patterns/visitor
- https://sourcemaking.com/design_patterns/visitor
