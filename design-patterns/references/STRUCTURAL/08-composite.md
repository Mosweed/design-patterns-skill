# Composite Pattern

**Category:** Structural
**Also Known As:** Object Tree

---

## Intent

Compose objects into tree structures to represent part-whole hierarchies. Composite lets clients treat individual objects (leaves) and compositions of objects (composites) uniformly through a shared interface.

---

## Problem It Solves

Consider an order-management system where an order can contain individual products or boxes. A box can contain more products and more boxes, nested to any depth. Calculating the total price of an order means recursively unwrapping every box and summing every product price.

Without the Composite pattern you are forced to write client code that constantly checks: "Is this thing a product or a box?" Every place that needs to calculate a total, render a tree, or perform any recursive operation must repeat that branching logic. Adding new container types breaks every such site.

The core problem: **your client must not need to distinguish between a leaf node and a branch node when traversing or operating on a tree structure.**

---

## Solution

Define a common `Component` interface that both leaves (e.g., `Product`) and branches (e.g., `Box`) implement. The interface exposes every operation the client needs — in the order example that is `get_price()`. 

- A `Product` (leaf) simply returns its own price.
- A `Box` (composite) iterates its children, calls `get_price()` on each, and returns the sum.

The client calls `get_price()` on the root and the tree recurses automatically. The client never knows — or cares — whether it received a single product or a deeply nested box.

---

## Structure (ASCII diagram)

```
         +------------------+
         |   <<interface>>  |
         |    Component     |
         |------------------|
         | + operation()    |
         +--------+---------+
                  |
        +---------+---------+
        |                   |
+-------+-------+   +-------+-------+
|     Leaf      |   |   Composite   |
|---------------|   |---------------|
| + operation() |   | - children[]  |
+---------------+   | + add()       |
                    | + remove()    |
                    | + operation() |---> calls operation()
                    +---------------+     on each child
                           |
              (children: Component[])
                     /          \
              Leaf ...        Composite ...
                                   |
                             Leaf ...
```

**Key relationships:**

- `Client` depends only on `Component`.
- `Composite` holds a list of `Component` references (its children).
- Both `Leaf` and `Composite` implement `Component`.
- The recursive call in `Composite.operation()` traverses the entire subtree transparently.

---

## Participants

| Participant | Role |
|---|---|
| **Component** | Declares the interface common to all elements (simple and complex). May optionally declare default child-management operations. |
| **Leaf** | A basic element with no children. Does the real work. |
| **Composite** | A container element that stores child `Component` references. Implements the `Component` operations by delegating to its children and aggregating results. |
| **Client** | Works with all elements through the `Component` interface. Never differentiates between a leaf and a composite. |

---

## How It Works (step-by-step)

1. **Define the Component interface.** Include every operation the client needs across the entire tree — e.g., `get_price()`, `display()`, `execute()`.
2. **Implement Leaf.** A leaf has no children. Its operation is concrete and terminal — it performs real work and returns a direct result.
3. **Implement Composite.** A composite stores a `children` collection of `Component` references. Its operation iterates children and aggregates their results (sum, concatenate, collect, etc.). Child management methods (`add`, `remove`, `get_child`) live here.
4. **Build the tree.** Client code (or a builder/factory) creates leaf and composite objects and assembles them by calling `composite.add(child)`.
5. **Invoke the operation on the root.** The client calls `root.operation()`. The call propagates recursively through the tree; each composite delegates to its children until leaves are reached.
6. **Add new types freely.** New leaf or composite types can be introduced without changing the client or existing components (Open/Closed Principle).

---

## Code Examples

### Python

```python
"""
Composite Pattern — File System Size Calculator
------------------------------------------------
Represents a file system where files are leaves and directories are composites.
The client can call .size() on any node — file or directory — uniformly.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List


# --------------------------------------------------------------------------
# Component
# --------------------------------------------------------------------------
class FileSystemNode(ABC):
    """Abstract component shared by files and directories."""

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def size(self) -> int:
        """Return total size in bytes."""

    @abstractmethod
    def display(self, indent: int = 0) -> None:
        """Pretty-print the node."""


# --------------------------------------------------------------------------
# Leaf
# --------------------------------------------------------------------------
class File(FileSystemNode):
    """A leaf node — a concrete file with a fixed size."""

    def __init__(self, name: str, size_bytes: int) -> None:
        super().__init__(name)
        self._size = size_bytes

    def size(self) -> int:
        return self._size

    def display(self, indent: int = 0) -> None:
        print(f"{'  ' * indent}[FILE] {self.name}  ({self._size:,} bytes)")


# --------------------------------------------------------------------------
# Composite
# --------------------------------------------------------------------------
class Directory(FileSystemNode):
    """A composite node — a directory that may contain files or sub-directories."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._children: List[FileSystemNode] = []

    def add(self, node: FileSystemNode) -> Directory:
        self._children.append(node)
        return self  # fluent API

    def remove(self, node: FileSystemNode) -> None:
        self._children.remove(node)

    def size(self) -> int:
        # Delegate to children and aggregate
        return sum(child.size() for child in self._children)

    def display(self, indent: int = 0) -> None:
        print(f"{'  ' * indent}[DIR ] {self.name}/  ({self.size():,} bytes)")
        for child in self._children:
            child.display(indent + 1)


# --------------------------------------------------------------------------
# Client code
# --------------------------------------------------------------------------
def main() -> None:
    # Build a realistic directory tree
    root = Directory("project")

    src = Directory("src")
    src.add(File("main.py", 4_200))
    src.add(File("utils.py", 8_700))

    tests = Directory("tests")
    tests.add(File("test_main.py", 3_100))
    tests.add(File("test_utils.py", 5_600))

    docs = Directory("docs")
    docs.add(File("README.md", 2_048))
    docs.add(File("API.md", 12_000))

    assets = Directory("assets")
    images = Directory("images")
    images.add(File("logo.png", 512_000))
    images.add(File("banner.jpg", 1_024_000))
    assets.add(images)
    assets.add(File("style.css", 7_300))

    root.add(src).add(tests).add(docs).add(assets)
    root.add(File("setup.py", 1_500))
    root.add(File("requirements.txt", 320))

    # Client treats root as a single node — no awareness of internal structure
    print("=== File System Tree ===")
    root.display()
    print(f"\nTotal project size: {root.size():,} bytes")

    # The client can also work with sub-trees uniformly
    print(f"\nSource size:  {src.size():,} bytes")
    print(f"Assets size:  {assets.size():,} bytes")
    print(f"Images size:  {images.size():,} bytes")


if __name__ == "__main__":
    main()
```

---

### Java

```java
/**
 * Composite Pattern — Organization Chart (Employee Hierarchy)
 *
 * Models a company org chart where managers are composites
 * and individual contributors are leaves.
 * The client can call getSalaryBudget() on any node uniformly.
 */

import java.util.ArrayList;
import java.util.List;

// --------------------------------------------------------------------------
// Component
// --------------------------------------------------------------------------
interface Employee {
    String getName();
    String getTitle();
    double getSalary();

    /** Total salary budget for this node and all its direct reports (recursive). */
    double getSalaryBudget();

    /** Display the org-chart subtree. */
    void display(int depth);
}

// --------------------------------------------------------------------------
// Leaf
// --------------------------------------------------------------------------
class IndividualContributor implements Employee {
    private final String name;
    private final String title;
    private final double salary;

    public IndividualContributor(String name, String title, double salary) {
        this.name   = name;
        this.title  = title;
        this.salary = salary;
    }

    @Override public String getName()  { return name; }
    @Override public String getTitle() { return title; }
    @Override public double getSalary() { return salary; }

    @Override
    public double getSalaryBudget() {
        // A leaf's budget is only its own salary
        return salary;
    }

    @Override
    public void display(int depth) {
        System.out.printf("%s- %s (%s) — $%,.0f%n",
                "  ".repeat(depth), name, title, salary);
    }
}

// --------------------------------------------------------------------------
// Composite
// --------------------------------------------------------------------------
class Manager implements Employee {
    private final String name;
    private final String title;
    private final double salary;
    private final List<Employee> reports = new ArrayList<>();

    public Manager(String name, String title, double salary) {
        this.name   = name;
        this.title  = title;
        this.salary = salary;
    }

    public void addReport(Employee e) { reports.add(e); }
    public void removeReport(Employee e) { reports.remove(e); }

    @Override public String getName()  { return name; }
    @Override public String getTitle() { return title; }
    @Override public double getSalary() { return salary; }

    @Override
    public double getSalaryBudget() {
        // Own salary + every direct and indirect report's salary
        double total = salary;
        for (Employee report : reports) {
            total += report.getSalaryBudget();
        }
        return total;
    }

    @Override
    public void display(int depth) {
        System.out.printf("%s+ %s (%s) — $%,.0f [budget: $%,.0f]%n",
                "  ".repeat(depth), name, title, salary, getSalaryBudget());
        for (Employee report : reports) {
            report.display(depth + 1);
        }
    }
}

// --------------------------------------------------------------------------
// Client
// --------------------------------------------------------------------------
public class CompositeDemo {
    public static void main(String[] args) {
        // Build the hierarchy
        Manager ceo = new Manager("Alice Chen", "CEO", 400_000);

        Manager cto = new Manager("Bob Martin", "CTO", 280_000);
        Manager cfo = new Manager("Carol Smith", "CFO", 270_000);
        Manager vp  = new Manager("Dave Kumar", "VP Engineering", 220_000);

        cto.addReport(vp);
        cto.addReport(new IndividualContributor("Eve Adams",   "Staff Engineer",  180_000));
        cto.addReport(new IndividualContributor("Frank Lee",   "Senior Engineer", 160_000));

        vp.addReport(new IndividualContributor("Grace Hall",   "Engineer II",     130_000));
        vp.addReport(new IndividualContributor("Henry Brown",  "Engineer I",      110_000));
        vp.addReport(new IndividualContributor("Iris White",   "Engineer I",      110_000));

        cfo.addReport(new IndividualContributor("Jack Green",  "Senior Analyst",  140_000));
        cfo.addReport(new IndividualContributor("Karen Black",  "Analyst",        105_000));

        ceo.addReport(cto);
        ceo.addReport(cfo);
        ceo.addReport(new IndividualContributor("Liam Gray",   "Executive Asst.", 85_000));

        // Client calls the same method regardless of depth
        System.out.println("=== Organization Chart ===");
        ceo.display(0);

        System.out.printf("%nTotal company salary budget: $%,.0f%n", ceo.getSalaryBudget());
        System.out.printf("Engineering budget:           $%,.0f%n", cto.getSalaryBudget());
        System.out.printf("Finance budget:               $%,.0f%n", cfo.getSalaryBudget());
    }
}
```

---

### C++

```cpp
/**
 * Composite Pattern — GUI Widget Rendering
 *
 * Models a UI where simple controls (Button, Label) are leaves
 * and containers (Panel, Window) are composites.
 * render() propagates through the entire tree uniformly.
 */

#include <algorithm>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

// --------------------------------------------------------------------------
// Component
// --------------------------------------------------------------------------
class Widget {
public:
    explicit Widget(std::string id) : id_(std::move(id)) {}
    virtual ~Widget() = default;

    const std::string& id() const { return id_; }

    virtual void render(int depth = 0) const = 0;
    virtual int  width()  const = 0;
    virtual int  height() const = 0;

    // Child management — only meaningful for composites;
    // leaves provide no-op defaults (transparent composite variant).
    virtual void add(std::shared_ptr<Widget> /*child*/) {}
    virtual void remove(const std::string& /*childId*/) {}

protected:
    std::string id_;

    static std::string indent(int depth) {
        return std::string(depth * 2, ' ');
    }
};

// --------------------------------------------------------------------------
// Leaves
// --------------------------------------------------------------------------
class Button : public Widget {
    std::string label_;
    int w_, h_;
public:
    Button(std::string id, std::string label, int w, int h)
        : Widget(std::move(id)), label_(std::move(label)), w_(w), h_(h) {}

    void render(int depth = 0) const override {
        std::cout << indent(depth)
                  << "[BUTTON id=" << id_ << "] \"" << label_
                  << "\" (" << w_ << "x" << h_ << ")\n";
    }
    int width()  const override { return w_; }
    int height() const override { return h_; }
};

class Label : public Widget {
    std::string text_;
    int fontSize_;
public:
    Label(std::string id, std::string text, int fontSize)
        : Widget(std::move(id)), text_(std::move(text)), fontSize_(fontSize) {}

    void render(int depth = 0) const override {
        std::cout << indent(depth)
                  << "[LABEL  id=" << id_ << "] \"" << text_
                  << "\" font=" << fontSize_ << "pt\n";
    }
    int width()  const override { return static_cast<int>(text_.size()) * fontSize_; }
    int height() const override { return fontSize_ + 4; }
};

class TextInput : public Widget {
    std::string placeholder_;
    int w_, h_;
public:
    TextInput(std::string id, std::string placeholder, int w, int h)
        : Widget(std::move(id)), placeholder_(std::move(placeholder)), w_(w), h_(h) {}

    void render(int depth = 0) const override {
        std::cout << indent(depth)
                  << "[INPUT  id=" << id_ << "] placeholder=\"" << placeholder_
                  << "\" (" << w_ << "x" << h_ << ")\n";
    }
    int width()  const override { return w_; }
    int height() const override { return h_; }
};

// --------------------------------------------------------------------------
// Composite
// --------------------------------------------------------------------------
class Panel : public Widget {
    std::vector<std::shared_ptr<Widget>> children_;
    int padding_;
public:
    Panel(std::string id, int padding = 8)
        : Widget(std::move(id)), padding_(padding) {}

    void add(std::shared_ptr<Widget> child) override {
        children_.push_back(std::move(child));
    }

    void remove(const std::string& childId) override {
        children_.erase(
            std::remove_if(children_.begin(), children_.end(),
                [&childId](const auto& w) { return w->id() == childId; }),
            children_.end());
    }

    void render(int depth = 0) const override {
        std::cout << indent(depth)
                  << "[PANEL  id=" << id_ << "] padding=" << padding_
                  << " children=" << children_.size() << "\n";
        for (const auto& child : children_) {
            child->render(depth + 1);
        }
    }

    int width() const override {
        int max_w = 0;
        for (const auto& c : children_) max_w = std::max(max_w, c->width());
        return max_w + 2 * padding_;
    }

    int height() const override {
        int total = 0;
        for (const auto& c : children_) total += c->height();
        return total + 2 * padding_;
    }
};

// --------------------------------------------------------------------------
// Client
// --------------------------------------------------------------------------
int main() {
    // Build a login form widget tree
    auto window = std::make_shared<Panel>("window", 16);

    auto header = std::make_shared<Panel>("header", 8);
    header->add(std::make_shared<Label>("title", "Sign In", 24));
    header->add(std::make_shared<Label>("subtitle", "Welcome back!", 14));

    auto form = std::make_shared<Panel>("form", 12);
    form->add(std::make_shared<Label>("lbl-email", "Email", 12));
    form->add(std::make_shared<TextInput>("inp-email", "you@example.com", 300, 36));
    form->add(std::make_shared<Label>("lbl-pass", "Password", 12));
    form->add(std::make_shared<TextInput>("inp-pass", "••••••••", 300, 36));

    auto actions = std::make_shared<Panel>("actions", 4);
    actions->add(std::make_shared<Button>("btn-login",  "Log In",        120, 40));
    actions->add(std::make_shared<Button>("btn-cancel", "Cancel",         80, 40));
    actions->add(std::make_shared<Button>("btn-forgot", "Forgot password?",160, 32));

    form->add(actions);
    window->add(header);
    window->add(form);

    // Client renders the entire tree with a single call
    std::cout << "=== UI Widget Tree ===\n";
    window->render();
    std::cout << "\nWindow computed size: "
              << window->width() << " x " << window->height() << " px\n";

    return 0;
}
```

---

### C#

```csharp
/**
 * Composite Pattern — Task Management (Project / Milestone / Task)
 *
 * A project contains milestones; milestones contain tasks.
 * Any node reports its total estimated hours uniformly.
 */

using System;
using System.Collections.Generic;

namespace CompositePattern
{
    // -----------------------------------------------------------------------
    // Component
    // -----------------------------------------------------------------------
    public interface IWorkItem
    {
        string Name        { get; }
        string Status      { get; }
        double EstimatedHours { get; }

        /// <summary>Total estimated hours for this item and all children.</summary>
        double TotalHours();

        void Display(int depth = 0);
    }

    // -----------------------------------------------------------------------
    // Leaf
    // -----------------------------------------------------------------------
    public sealed class Task : IWorkItem
    {
        public string Name            { get; }
        public string Status          { get; private set; }
        public double EstimatedHours  { get; }
        private readonly string _assignee;

        public Task(string name, string assignee, double estimatedHours, string status = "To Do")
        {
            Name           = name;
            _assignee      = assignee;
            EstimatedHours = estimatedHours;
            Status         = status;
        }

        public void Complete() => Status = "Done";

        // A task's total is just its own estimate
        public double TotalHours() => EstimatedHours;

        public void Display(int depth = 0)
        {
            var indent = new string(' ', depth * 3);
            Console.WriteLine(
                $"{indent}[TASK] {Name} | {_assignee} | {EstimatedHours}h | {Status}");
        }
    }

    // -----------------------------------------------------------------------
    // Composite
    // -----------------------------------------------------------------------
    public sealed class WorkGroup : IWorkItem
    {
        private readonly List<IWorkItem> _children = new();

        public string Name           { get; }
        public string Status         => DeriveStatus();
        public double EstimatedHours => TotalHours();

        public WorkGroup(string name) => Name = name;

        public void Add(IWorkItem item)    => _children.Add(item);
        public void Remove(IWorkItem item) => _children.Remove(item);

        // Aggregate total hours recursively
        public double TotalHours()
        {
            double total = 0;
            foreach (var child in _children)
                total += child.TotalHours();
            return total;
        }

        private string DeriveStatus()
        {
            bool allDone = true;
            bool anyInProgress = false;
            foreach (var child in _children)
            {
                if (child.Status != "Done")      allDone = false;
                if (child.Status == "In Progress") anyInProgress = true;
            }
            if (allDone)         return "Done";
            if (anyInProgress)   return "In Progress";
            return "To Do";
        }

        public void Display(int depth = 0)
        {
            var indent = new string(' ', depth * 3);
            Console.WriteLine(
                $"{indent}[GROUP] {Name} | Total: {TotalHours()}h | {Status}");
            foreach (var child in _children)
                child.Display(depth + 1);
        }
    }

    // -----------------------------------------------------------------------
    // Client
    // -----------------------------------------------------------------------
    internal class Program
    {
        static void Main()
        {
            // Build a sprint hierarchy
            var sprint = new WorkGroup("Sprint 14");

            var auth = new WorkGroup("Authentication Milestone");
            var t1 = new Task("Design OAuth flow",       "Alice",   4, "Done");
            var t2 = new Task("Implement login endpoint","Bob",     8, "Done");
            var t3 = new Task("Write auth unit tests",   "Carol",   6, "In Progress");
            var t4 = new Task("Security review",         "Dave",    4);
            auth.Add(t1); auth.Add(t2); auth.Add(t3); auth.Add(t4);

            var api = new WorkGroup("API Milestone");
            var t5 = new Task("Define OpenAPI spec",     "Eve",     3, "Done");
            var t6 = new Task("Implement CRUD endpoints","Frank",  16);
            var t7 = new Task("Integration tests",       "Grace",   8);

            var pagination = new WorkGroup("Pagination Sub-task");
            pagination.Add(new Task("Research cursor vs offset", "Henry",  2));
            pagination.Add(new Task("Implement pagination",      "Henry",  6));
            pagination.Add(new Task("Document pagination API",   "Iris",   2));

            api.Add(t5); api.Add(t6); api.Add(t7); api.Add(pagination);

            sprint.Add(auth);
            sprint.Add(api);
            sprint.Add(new Task("Deploy to staging", "Jack", 2));

            // Client uses the uniform interface at any level
            Console.WriteLine("=== Sprint Board ===");
            sprint.Display();

            Console.WriteLine($"\nSprint total estimate : {sprint.TotalHours()} hours");
            Console.WriteLine($"Auth milestone        : {auth.TotalHours()} hours  [{auth.Status}]");
            Console.WriteLine($"API milestone         : {api.TotalHours()} hours  [{api.Status}]");
            Console.WriteLine($"Pagination sub-tasks  : {pagination.TotalHours()} hours");
        }
    }
}
```

---

### TypeScript

```typescript
/**
 * Composite Pattern — E-commerce Order Pricing
 *
 * An order can contain individual products or gift boxes.
 * A gift box can contain products or more nested boxes.
 * Any node can report its total price and apply discounts uniformly.
 */

// --------------------------------------------------------------------------
// Component interface
// --------------------------------------------------------------------------
interface OrderComponent {
  readonly name: string;
  getPrice(): number;
  getDescription(): string;
  display(depth?: number): void;
}

// --------------------------------------------------------------------------
// Leaf — a single product
// --------------------------------------------------------------------------
class Product implements OrderComponent {
  constructor(
    public readonly name: string,
    private readonly price: number,
    private readonly sku: string,
  ) {}

  getPrice(): number {
    return this.price;
  }

  getDescription(): string {
    return `${this.name} [SKU: ${this.sku}] — $${this.price.toFixed(2)}`;
  }

  display(depth = 0): void {
    const indent = '  '.repeat(depth);
    console.log(`${indent}[PRODUCT] ${this.getDescription()}`);
  }
}

// --------------------------------------------------------------------------
// Composite — a box that can hold products or nested boxes
// --------------------------------------------------------------------------
class GiftBox implements OrderComponent {
  private children: OrderComponent[] = [];

  constructor(
    public readonly name: string,
    private readonly packagingCost: number = 2.99,
  ) {}

  add(component: OrderComponent): this {
    this.children.push(component);
    return this;
  }

  remove(component: OrderComponent): void {
    const idx = this.children.indexOf(component);
    if (idx !== -1) this.children.splice(idx, 1);
  }

  getPrice(): number {
    // Sum children + packaging cost
    const contentTotal = this.children.reduce(
      (sum, child) => sum + child.getPrice(),
      0,
    );
    return contentTotal + this.packagingCost;
  }

  getDescription(): string {
    return `${this.name} (${this.children.length} item(s)) — $${this.getPrice().toFixed(2)}`;
  }

  display(depth = 0): void {
    const indent = '  '.repeat(depth);
    console.log(
      `${indent}[BOX] ${this.name} | packaging $${this.packagingCost.toFixed(2)} | total $${this.getPrice().toFixed(2)}`,
    );
    for (const child of this.children) {
      child.display(depth + 1);
    }
  }
}

// --------------------------------------------------------------------------
// Discount decorator utility (works on any OrderComponent)
// --------------------------------------------------------------------------
class DiscountedComponent implements OrderComponent {
  constructor(
    private readonly wrapped: OrderComponent,
    private readonly discountPercent: number,
  ) {}

  get name(): string {
    return this.wrapped.name;
  }

  getPrice(): number {
    return this.wrapped.getPrice() * (1 - this.discountPercent / 100);
  }

  getDescription(): string {
    return `${this.wrapped.getDescription()} [${this.discountPercent}% OFF]`;
  }

  display(depth = 0): void {
    const indent = '  '.repeat(depth);
    console.log(
      `${indent}[DISCOUNTED -${this.discountPercent}%] base: $${this.wrapped.getPrice().toFixed(2)} -> $${this.getPrice().toFixed(2)}`,
    );
    this.wrapped.display(depth + 1);
  }
}

// --------------------------------------------------------------------------
// Client
// --------------------------------------------------------------------------
function main(): void {
  // Individual products
  const phone    = new Product('Smartphone Pro 15',  999.00, 'SPH-015');
  const charger  = new Product('USB-C Fast Charger',  29.99, 'CHG-USBC');
  const cable    = new Product('Braided Cable 2m',    14.99, 'CBL-2M');
  const earbuds  = new Product('Wireless Earbuds',   149.00, 'EAR-WL1');
  const case_    = new Product('Protective Case',     24.99, 'CSE-PRO');
  const screen   = new Product('Screen Protector',    12.99, 'SCR-TMP');

  // Nest: accessories box
  const accessoriesBox = new GiftBox('Accessories Bundle', 1.99);
  accessoriesBox.add(charger).add(cable).add(case_).add(screen);

  // Apply a 10% discount to earbuds
  const discountedEarbuds = new DiscountedComponent(earbuds, 10);

  // Top-level gift set
  const giftSet = new GiftBox('Premium Phone Gift Set', 4.99);
  giftSet.add(phone);
  giftSet.add(discountedEarbuds);
  giftSet.add(accessoriesBox);

  // The client calls getPrice() on the root — no tree-traversal logic needed
  console.log('=== Order Summary ===');
  giftSet.display();

  console.log(`\nAccessories box price : $${accessoriesBox.getPrice().toFixed(2)}`);
  console.log(`Gift set total        : $${giftSet.getPrice().toFixed(2)}`);
}

main();
```

---

### Go

```go
// Composite Pattern — Network Infrastructure Cost Calculator
//
// Models a data-center network where switches are composites
// and individual servers/devices are leaves.
// Any node reports its monthly cost uniformly.

package main

import (
	"fmt"
	"strings"
)

// --------------------------------------------------------------------------
// Component interface
// --------------------------------------------------------------------------
type NetworkNode interface {
	Name() string
	MonthlyCost() float64
	Display(depth int)
}

// --------------------------------------------------------------------------
// Leaf — a single server
// --------------------------------------------------------------------------
type Server struct {
	name     string
	cpuCores int
	ramGB    int
	cost     float64
}

func NewServer(name string, cpuCores, ramGB int, cost float64) *Server {
	return &Server{name: name, cpuCores: cpuCores, ramGB: ramGB, cost: cost}
}

func (s *Server) Name() string         { return s.name }
func (s *Server) MonthlyCost() float64 { return s.cost }
func (s *Server) Display(depth int) {
	indent := strings.Repeat("  ", depth)
	fmt.Printf("%s[SERVER] %s  CPU:%d  RAM:%dGB  $%.2f/mo\n",
		indent, s.name, s.cpuCores, s.ramGB, s.cost)
}

// Leaf — a network appliance (firewall, load balancer, etc.)
type Appliance struct {
	name       string
	applianceType string
	cost       float64
}

func NewAppliance(name, applianceType string, cost float64) *Appliance {
	return &Appliance{name: name, applianceType: applianceType, cost: cost}
}

func (a *Appliance) Name() string         { return a.name }
func (a *Appliance) MonthlyCost() float64 { return a.cost }
func (a *Appliance) Display(depth int) {
	indent := strings.Repeat("  ", depth)
	fmt.Printf("%s[%s] %s  $%.2f/mo\n",
		indent, strings.ToUpper(a.applianceType), a.name, a.cost)
}

// --------------------------------------------------------------------------
// Composite — a rack or cluster that groups network nodes
// --------------------------------------------------------------------------
type Rack struct {
	name     string
	location string
	children []NetworkNode
	rackCost float64 // monthly cost of the physical rack/PDU
}

func NewRack(name, location string, rackCost float64) *Rack {
	return &Rack{name: name, location: location, rackCost: rackCost}
}

func (r *Rack) Add(node NetworkNode) *Rack {
	r.children = append(r.children, node)
	return r
}

func (r *Rack) Name() string { return r.name }

func (r *Rack) MonthlyCost() float64 {
	total := r.rackCost
	for _, child := range r.children {
		total += child.MonthlyCost()
	}
	return total
}

func (r *Rack) Display(depth int) {
	indent := strings.Repeat("  ", depth)
	fmt.Printf("%s[RACK] %s @ %s  rack:$%.2f  total:$%.2f/mo\n",
		indent, r.name, r.location, r.rackCost, r.MonthlyCost())
	for _, child := range r.children {
		child.Display(depth + 1)
	}
}

// Composite — a data-center zone
type Zone struct {
	name     string
	children []NetworkNode
}

func NewZone(name string) *Zone { return &Zone{name: name} }

func (z *Zone) Add(node NetworkNode) *Zone {
	z.children = append(z.children, node)
	return z
}

func (z *Zone) Name() string { return z.name }

func (z *Zone) MonthlyCost() float64 {
	var total float64
	for _, child := range z.children {
		total += child.MonthlyCost()
	}
	return total
}

func (z *Zone) Display(depth int) {
	indent := strings.Repeat("  ", depth)
	fmt.Printf("%s[ZONE ] %s  total:$%.2f/mo\n",
		indent, z.name, z.MonthlyCost())
	for _, child := range z.children {
		child.Display(depth + 1)
	}
}

// --------------------------------------------------------------------------
// Client
// --------------------------------------------------------------------------
func main() {
	// Build network topology
	webRack := NewRack("web-rack-01", "Row A", 150.00)
	webRack.Add(NewServer("web-01", 8, 32, 320.00))
	webRack.Add(NewServer("web-02", 8, 32, 320.00))
	webRack.Add(NewServer("web-03", 8, 32, 320.00))
	webRack.Add(NewAppliance("lb-01", "Load Balancer", 200.00))

	dbRack := NewRack("db-rack-01", "Row B", 250.00)
	dbRack.Add(NewServer("db-primary", 32, 256, 1_200.00))
	dbRack.Add(NewServer("db-replica-01", 32, 256, 1_100.00))
	dbRack.Add(NewServer("db-replica-02", 32, 128, 900.00))

	securityRack := NewRack("sec-rack-01", "Row A", 100.00)
	securityRack.Add(NewAppliance("fw-01", "Firewall", 450.00))
	securityRack.Add(NewAppliance("ids-01", "IDS", 200.00))

	prodZone := NewZone("Production Zone")
	prodZone.Add(webRack)
	prodZone.Add(dbRack)
	prodZone.Add(securityRack)

	stagingRack := NewRack("staging-rack-01", "Row C", 100.00)
	stagingRack.Add(NewServer("staging-web", 4, 16, 120.00))
	stagingRack.Add(NewServer("staging-db", 8, 64, 280.00))

	stagingZone := NewZone("Staging Zone")
	stagingZone.Add(stagingRack)

	dataCenter := NewZone("US-East-1 Data Center")
	dataCenter.Add(prodZone)
	dataCenter.Add(stagingZone)

	// Client calls MonthlyCost() on any level — no traversal code needed
	fmt.Println("=== Infrastructure Cost Report ===")
	dataCenter.Display(0)

	fmt.Printf("\nTotal data center cost : $%.2f/mo\n", dataCenter.MonthlyCost())
	fmt.Printf("Production zone cost   : $%.2f/mo\n", prodZone.MonthlyCost())
	fmt.Printf("Staging zone cost      : $%.2f/mo\n", stagingZone.MonthlyCost())
	fmt.Printf("Web rack cost          : $%.2f/mo\n", webRack.MonthlyCost())
	fmt.Printf("Database rack cost     : $%.2f/mo\n", dbRack.MonthlyCost())
}
```

---

### PHP

```php
<?php
/**
 * Composite Pattern — Content Management System (CMS) Menu Builder
 *
 * A navigation menu contains menu items (leaves) and sub-menus (composites).
 * Any node can render itself and report its depth uniformly.
 */

declare(strict_types=1);

// --------------------------------------------------------------------------
// Component interface
// --------------------------------------------------------------------------
interface MenuComponent
{
    public function getLabel(): string;
    public function getUrl(): ?string;
    public function isVisible(): bool;
    public function render(int $depth = 0): string;
    public function countItems(): int;
}

// --------------------------------------------------------------------------
// Leaf — a single clickable menu item
// --------------------------------------------------------------------------
final class MenuItem implements MenuComponent
{
    public function __construct(
        private readonly string $label,
        private readonly string $url,
        private readonly bool   $visible = true,
        private readonly ?string $icon    = null,
    ) {}

    public function getLabel(): string  { return $this->label; }
    public function getUrl(): ?string   { return $this->url; }
    public function isVisible(): bool   { return $this->visible; }
    public function countItems(): int   { return 1; }

    public function render(int $depth = 0): string
    {
        if (!$this->visible) {
            return '';
        }
        $indent = str_repeat('  ', $depth);
        $icon   = $this->icon ? "[{$this->icon}] " : '';
        return "{$indent}<li><a href=\"{$this->url}\">{$icon}{$this->label}</a></li>\n";
    }
}

// --------------------------------------------------------------------------
// Composite — a menu group that may contain items or nested sub-menus
// --------------------------------------------------------------------------
final class SubMenu implements MenuComponent
{
    /** @var MenuComponent[] */
    private array $children = [];

    public function __construct(
        private readonly string $label,
        private readonly bool   $visible = true,
    ) {}

    public function add(MenuComponent $component): self
    {
        $this->children[] = $component;
        return $this;
    }

    public function remove(MenuComponent $component): void
    {
        $this->children = array_filter(
            $this->children,
            fn(MenuComponent $c) => $c !== $component,
        );
    }

    public function getLabel(): string  { return $this->label; }
    public function getUrl(): ?string   { return null; }
    public function isVisible(): bool   { return $this->visible; }

    public function countItems(): int
    {
        return array_sum(array_map(
            fn(MenuComponent $c) => $c->countItems(),
            $this->children,
        ));
    }

    public function render(int $depth = 0): string
    {
        if (!$this->visible) {
            return '';
        }

        $indent = str_repeat('  ', $depth);
        $html   = "{$indent}<li class=\"has-submenu\">\n";
        $html  .= "{$indent}  <span>{$this->label}</span>\n";
        $html  .= "{$indent}  <ul>\n";

        foreach ($this->children as $child) {
            $html .= $child->render($depth + 2);
        }

        $html .= "{$indent}  </ul>\n";
        $html .= "{$indent}</li>\n";

        return $html;
    }
}

// --------------------------------------------------------------------------
// Client — builds and renders the navigation tree
// --------------------------------------------------------------------------
function buildNavigation(): MenuComponent
{
    $nav = new SubMenu('Root Navigation');

    // Top-level items
    $nav->add(new MenuItem('Home', '/', true, 'house'));

    // Products sub-menu
    $products = new SubMenu('Products');
    $products
        ->add(new MenuItem('All Products',     '/products'))
        ->add(new MenuItem('New Arrivals',     '/products/new'))
        ->add(new MenuItem('Sale',             '/products/sale', true, 'tag'));

    $electronics = new SubMenu('Electronics');
    $electronics
        ->add(new MenuItem('Smartphones', '/products/electronics/phones'))
        ->add(new MenuItem('Laptops',     '/products/electronics/laptops'))
        ->add(new MenuItem('Accessories', '/products/electronics/accessories'));

    $clothing = new SubMenu('Clothing');
    $clothing
        ->add(new MenuItem('Men',    '/products/clothing/men'))
        ->add(new MenuItem('Women',  '/products/clothing/women'))
        ->add(new MenuItem('Kids',   '/products/clothing/kids'));

    $products->add($electronics)->add($clothing);
    $nav->add($products);

    // Blog sub-menu
    $blog = new SubMenu('Blog');
    $blog
        ->add(new MenuItem('Articles',  '/blog'))
        ->add(new MenuItem('Tutorials', '/blog/tutorials'))
        ->add(new MenuItem('News',      '/blog/news'));
    $nav->add($blog);

    // Hidden item (admin only)
    $nav->add(new MenuItem('Admin Panel', '/admin', false));

    $nav->add(new MenuItem('Contact', '/contact', true, 'envelope'));

    return $nav;
}

$navigation = buildNavigation();

echo "=== CMS Navigation Menu ===\n\n";
echo "<ul>\n";
echo $navigation->render(1);
echo "</ul>\n\n";

echo sprintf("Total visible items: %d\n", $navigation->countItems());
```

---

### Ruby

```ruby
# Composite Pattern — Report Generation System
#
# A report can contain sections (composites) and content blocks (leaves).
# Any node can render itself to HTML or plain text uniformly.

# --------------------------------------------------------------------------
# Component
# --------------------------------------------------------------------------
module ReportComponent
  def title
    raise NotImplementedError, "#{self.class}#title not implemented"
  end

  def word_count
    raise NotImplementedError, "#{self.class}#word_count not implemented"
  end

  def render_html(depth: 0)
    raise NotImplementedError, "#{self.class}#render_html not implemented"
  end

  def render_text(depth: 0)
    raise NotImplementedError, "#{self.class}#render_text not implemented"
  end
end

# --------------------------------------------------------------------------
# Leaves
# --------------------------------------------------------------------------
class Paragraph
  include ReportComponent

  attr_reader :title

  def initialize(content, title: nil)
    @content = content
    @title   = title
  end

  def word_count
    @content.split.length
  end

  def render_html(depth: 0)
    indent = '  ' * depth
    html   = ''
    html  += "#{indent}<h#{[depth + 1, 6].min}>#{@title}</h#{[depth + 1, 6].min}>\n" if @title
    html  += "#{indent}<p>#{@content}</p>\n"
    html
  end

  def render_text(depth: 0)
    indent = '  ' * depth
    text   = ''
    text  += "#{indent}#{@title.upcase}\n" if @title
    text  += "#{indent}#{@content}\n"
    text
  end
end

class CodeBlock
  include ReportComponent

  attr_reader :title

  def initialize(code, language: 'text', title: nil)
    @code     = code
    @language = language
    @title    = title
  end

  def word_count
    @code.split.length
  end

  def render_html(depth: 0)
    indent = '  ' * depth
    "#{indent}<pre><code class=\"language-#{@language}\">#{@code}</code></pre>\n"
  end

  def render_text(depth: 0)
    indent = '  ' * depth
    "#{indent}```#{@language}\n#{@code.gsub(/^/, indent)}\n#{indent}```\n"
  end
end

class Image
  include ReportComponent

  attr_reader :title

  def initialize(src, alt:, caption: nil, title: nil)
    @src     = src
    @alt     = alt
    @caption = caption
    @title   = title
  end

  def word_count
    (@caption || '').split.length
  end

  def render_html(depth: 0)
    indent = '  ' * depth
    html   = "#{indent}<figure>\n"
    html  += "#{indent}  <img src=\"#{@src}\" alt=\"#{@alt}\">\n"
    html  += "#{indent}  <figcaption>#{@caption}</figcaption>\n" if @caption
    html  += "#{indent}</figure>\n"
    html
  end

  def render_text(depth: 0)
    indent = '  ' * depth
    "#{indent}[IMAGE: #{@alt}]#{@caption ? " — #{@caption}" : ''}\n"
  end
end

# --------------------------------------------------------------------------
# Composite
# --------------------------------------------------------------------------
class Section
  include ReportComponent

  attr_reader :title

  def initialize(title)
    @title    = title
    @children = []
  end

  def add(component)
    @children << component
    self  # fluent API
  end

  def remove(component)
    @children.delete(component)
  end

  def word_count
    @children.sum(&:word_count)
  end

  def render_html(depth: 0)
    indent   = '  ' * depth
    heading  = [depth + 1, 6].min
    html     = "#{indent}<section>\n"
    html    += "#{indent}  <h#{heading}>#{@title}</h#{heading}>\n"
    @children.each { |child| html += child.render_html(depth: depth + 1) }
    html    += "#{indent}</section>\n"
    html
  end

  def render_text(depth: 0)
    indent  = '  ' * depth
    border  = '=' * (50 - depth * 2)
    text    = "#{indent}#{border}\n#{indent}#{@title.upcase}\n#{indent}#{border}\n"
    @children.each { |child| text += child.render_text(depth: depth + 1) }
    text
  end
end

# --------------------------------------------------------------------------
# Client
# --------------------------------------------------------------------------

# Build a technical report
report = Section.new('Ruby on Rails Performance Guide')

intro = Section.new('Introduction')
intro
  .add(Paragraph.new(
         'This guide covers proven techniques for improving Rails application performance ' \
         'in production environments. We will examine database optimization, caching ' \
         'strategies, and background job processing.',
         title: 'Overview'
       ))
  .add(Paragraph.new(
         'Performance tuning should always be driven by measurement. Profile first, ' \
         'then optimize the bottlenecks you actually have.',
         title: 'Philosophy'
       ))

database = Section.new('Database Optimization')
indexing  = Section.new('Indexing Strategies')
indexing
  .add(Paragraph.new(
         'Proper indexes are the single highest-impact change you can make to query performance. ' \
         'Use EXPLAIN ANALYZE to identify slow queries and missing indexes.'
       ))
  .add(CodeBlock.new(
         "# Add an index on a frequently queried column\nadd_index :orders, :status\n" \
         "# Composite index for common query pattern\nadd_index :orders, [:user_id, :created_at]",
         language: 'ruby',
         title:    'Migration Example'
       ))

n_plus_one = Section.new('Avoiding N+1 Queries')
n_plus_one
  .add(Paragraph.new('The N+1 query problem is the most common Rails performance mistake.'))
  .add(CodeBlock.new(
         "# Bad — N+1\nPosts.all.each { |post| puts post.author.name }\n\n" \
         "# Good — eager loading\nPosts.includes(:author).each { |post| puts post.author.name }",
         language: 'ruby'
       ))

database.add(indexing).add(n_plus_one)
database.add(Image.new(
               '/images/query-plan.png',
               alt:     'EXPLAIN ANALYZE output',
               caption: 'Figure 1: Query execution plan showing index scan'
             ))

caching = Section.new('Caching')
caching
  .add(Paragraph.new(
         'Rails ships with a flexible caching framework. Use fragment caching for views ' \
         'and low-level caching for expensive computations.',
         title: 'Overview'
       ))
  .add(CodeBlock.new(
         "# Fragment caching in a view\n<% cache @product do %>\n  <%= render @product %>\n<% end %>\n\n" \
         "# Low-level caching\nRails.cache.fetch('expensive_data', expires_in: 12.hours) do\n  ExpensiveService.compute\nend",
         language: 'ruby'
       ))

report.add(intro).add(database).add(caching)

# Client renders via the uniform interface
puts '=== Technical Report (HTML) ==='
puts report.render_html
puts "\n=== Technical Report (Plain Text) ==="
puts report.render_text
puts "\nTotal word count: #{report.word_count} words"
```

---

## When To Use

- **Tree-like object structures** — When your domain naturally forms a hierarchy (file systems, org charts, UI component trees, menus, bills of materials, XML/JSON documents, scene graphs, dependency trees).
- **Uniform treatment** — When client code must perform the same operations on both individual items and collections of items without branching. If you find yourself writing `if isinstance(obj, Container)` everywhere, the Composite pattern is the fix.
- **Recursive aggregation** — When a value must be computed by accumulating over an arbitrarily deep tree (total price, total size, total headcount, combined render output).
- **Open/Closed extensibility** — When you want to introduce new component types (new kinds of leaves or composites) without modifying existing client code or sibling classes.
- **Avoid** when the tree is always exactly one level deep — a flat collection is simpler. Avoid when leaf and composite operations are so different that forcing a shared interface requires dummy/unsupported methods in leaves.

---

## Pros & Cons

### Pros

| Benefit | Explanation |
|---|---|
| **Uniform interface** | Client code works with any node through the same interface, eliminating type checks. |
| **Recursive structures** | You can build arbitrarily deep trees and the pattern handles all recursion transparently. |
| **Open/Closed Principle** | New leaf or composite types can be added without touching the client or existing classes. |
| **Simplified client code** | Clients are freed from traversal and aggregation logic; that complexity lives inside the composite. |
| **Composability** | Subtrees can be reused, moved, or cloned as first-class objects. |

### Cons

| Drawback | Explanation |
|---|---|
| **Overgeneralized interface** | When leaves and composites have very different capabilities you must declare operations in the common interface that make no sense for some implementors (e.g., `add()`/`remove()` on a leaf), leading to empty or exception-throwing stubs. |
| **Type safety trade-off** | Making the interface fully uniform sometimes means sacrificing compile-time type safety (you cannot call `add()` through a `Component` reference without a cast in statically typed languages, unless you expose it in the interface). |
| **Difficult constraints** | Enforcing rules about which component types may contain which others (e.g., "a leaf cannot be a child of another leaf") requires extra validation logic not captured by the structure itself. |
| **Performance** | Deep trees with many small nodes can introduce overhead from virtual dispatch and memory allocation; for performance-critical paths, consider flattening. |

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Builder** | You can use Builder to construct complex Composite trees step by step, hiding the assembly logic from the client. |
| **Chain of Responsibility** | Handlers in a Chain of Responsibility are often part of a Composite tree; a request walks up the chain through parent composites. |
| **Decorator** | Both Decorator and Composite rely on recursive composition, but Decorator adds behavior to a single object while Composite aggregates children. They can be combined: a component can be both decorated and a composite. |
| **Flyweight** | Use Flyweight to share the leaf nodes of a Composite tree when there are many identical leaves (e.g., characters in a text editor), reducing memory. |
| **Iterator** | Iterator can be used to traverse a Composite tree without exposing its internal structure. |
| **Visitor** | Visitor lets you add operations to a Composite tree without modifying component classes — especially useful when the tree is stable but operations change frequently. |

---

## Sources

- https://refactoring.guru/design-patterns/composite
- https://sourcemaking.com/design_patterns/composite
