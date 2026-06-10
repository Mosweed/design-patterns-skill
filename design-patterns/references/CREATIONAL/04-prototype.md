# Prototype Pattern

**Category:** Creational  
**Also Known As:** Clone

---

## Intent

Lets you copy existing objects without making your code dependent on their concrete classes. The pattern delegates the cloning process to the actual objects that are being cloned, declaring a common interface for all objects that support cloning.

---

## Problem It Solves

Suppose you have an object and you want to produce an exact copy of it. How would you do it? First, you have to create a new object of the same class. Then you have to go through all the fields of the original object and copy their values over to the new object.

This approach has two major problems:

1. **Private fields are invisible.** Not all objects can be copied that way because some of the object's fields may be private and not visible from outside of the object itself.

2. **Class dependency.** You need to know the object's class in order to create a duplicate, making your code dependent on that class. If the extra dependency does not scare you, there is another catch. Sometimes you only know the interface that the object follows, but not its concrete class — for example, when a parameter in a method accepts any objects that follow some interface.

---

## Solution

The Prototype pattern delegates the cloning process to the actual objects being cloned. The pattern declares a common interface for all objects that support cloning. This interface lets you clone an object without coupling your code to the class of that object. Usually, such an interface contains just a single `clone` method.

The implementation of the `clone` method is very similar in all classes. The method creates an object of the current class and carries over all of the field values of the old object into the new one. You can even copy private fields because most programming languages let objects access private fields of other objects that belong to the same class.

An object that supports cloning is called a **prototype**. When your objects have dozens of fields and hundreds of possible configurations, cloning them might serve as an alternative to subclassing.

A **Prototype Registry** provides an easy way to access frequently-used prototypes. It stores a set of pre-built objects that are ready to be copied. The simplest prototype registry is a name-to-prototype hash map.

---

## Structure

```
+-------------------+
|   <<interface>>   |
|     Prototype     |
+-------------------+
| + clone(): self   |
+-------------------+
         ^
         |
         +------------------------------+
         |                              |
+-------------------+        +--------------------+
| ConcretePrototype1|        | ConcretePrototype2 |
+-------------------+        +--------------------+
| - field1          |        | - field2           |
+-------------------+        +--------------------+
| + clone(): self   |        | + clone(): self    |
| + getField1()     |        | + getField2()      |
+-------------------+        +--------------------+


+------------------------+
|   PrototypeRegistry    |
+------------------------+
| - items: Map<str, P>   |
+------------------------+
| + addItem(id, proto)   |
| + getById(id): Proto   |
+------------------------+
         |
         | uses
         v
+-------------------+
|      Client       |
+-------------------+
| + businessLogic() |
+-------------------+
```

**Shallow vs Deep Clone:**

```
Shallow Clone:                      Deep Clone:
+----------+                        +----------+
| Original |---> [ref object A]     | Original |---> [ref object A]
+----------+                        +----------+
| Clone    |---> [ref object A]     | Clone    |---> [ref object A']  (new copy)
+----------+  (same reference!)     +----------+
```

---

## Participants

| Participant | Role |
|---|---|
| **Prototype** | Declares the interface for cloning itself. Typically a single `clone()` method. |
| **ConcretePrototype** | Implements the operation for cloning itself. Handles copying of field values, including deep copying of nested objects when necessary. |
| **PrototypeRegistry** (optional) | Maintains a registry of available prototypes. Clients can retrieve copies of frequently-used objects without knowing their concrete classes. |
| **Client** | Creates a new object by asking a prototype to clone itself. The client is decoupled from concrete classes. |

---

## How It Works

1. **Define the Prototype interface** — Create an interface (or abstract class) with a `clone()` method. All clonable objects must implement this interface.

2. **Implement `clone()` in each class** — Each concrete class implements `clone()` by:
   - Creating a new instance of itself (often using a copy constructor or language-native cloning)
   - Copying all fields from `this` into the new instance
   - For fields that reference other objects, decide between shallow copy (copy the reference) or deep copy (clone the nested object too)

3. **(Optional) Set up a Prototype Registry** — Pre-configure a set of commonly-used objects and store them in a registry keyed by name or ID. This avoids hardcoding object configurations throughout the codebase.

4. **Client requests a clone** — Instead of calling `new ConcreteClass(...)`, the client calls `prototype.clone()`. The client does not need to know the concrete type.

5. **Customize after cloning** — After cloning, the client can tweak a few fields on the new object without affecting the original, avoiding full re-initialization.

---

## Code Examples

### Python

```python
"""
Prototype Pattern — Python Example
Use case: Game character configuration system.

In a role-playing game, characters share many attributes (base stats, equipment
templates). Instead of re-initializing each character from scratch, we clone a
prototype and adjust only what differs.
"""

from __future__ import annotations
import copy
from abc import ABC, abstractmethod
from typing import Dict, List


class CharacterPrototype(ABC):
    """Abstract prototype interface declaring the clone method."""

    @abstractmethod
    def clone(self) -> CharacterPrototype:
        pass

    @abstractmethod
    def describe(self) -> str:
        pass


class Equipment:
    """Represents equipment that a character carries — used to demonstrate deep copy."""

    def __init__(self, name: str, power: int):
        self.name = name
        self.power = power

    def __repr__(self) -> str:
        return f"Equipment({self.name!r}, power={self.power})"


class GameCharacter(CharacterPrototype):
    """
    Concrete prototype representing a game character.

    Implements deep cloning so that modifying the clone's equipment
    does not affect the original prototype.
    """

    def __init__(self, name: str, char_class: str, level: int,
                 stats: Dict[str, int], equipment: List[Equipment]):
        self.name = name
        self.char_class = char_class
        self.level = level
        self.stats = stats                  # dict — needs deep copy
        self.equipment = equipment          # list of objects — needs deep copy

    def clone(self) -> GameCharacter:
        """
        Perform a deep copy so the clone is fully independent.
        Python's copy.deepcopy handles nested mutable structures automatically.
        """
        return copy.deepcopy(self)

    def describe(self) -> str:
        equip_names = [e.name for e in self.equipment]
        return (
            f"[{self.char_class}] {self.name} (Lv.{self.level}) | "
            f"STR={self.stats['str']} INT={self.stats['int']} | "
            f"Equipment: {equip_names}"
        )


class CharacterRegistry:
    """
    Prototype Registry — stores pre-built character templates.
    Clients can clone named templates instead of building characters from scratch.
    """

    def __init__(self):
        self._templates: Dict[str, GameCharacter] = {}

    def register(self, key: str, character: GameCharacter) -> None:
        self._templates[key] = character

    def get(self, key: str) -> GameCharacter:
        if key not in self._templates:
            raise ValueError(f"No prototype registered under key: {key!r}")
        # Always return a fresh clone — never the original template
        return self._templates[key].clone()

    def list_templates(self) -> List[str]:
        return list(self._templates.keys())


# ---------------------------------------------------------------------------
# Setup: build the prototype registry
# ---------------------------------------------------------------------------

def build_registry() -> CharacterRegistry:
    registry = CharacterRegistry()

    warrior_proto = GameCharacter(
        name="Warrior Template",
        char_class="Warrior",
        level=1,
        stats={"str": 15, "dex": 10, "int": 5, "con": 14},
        equipment=[
            Equipment("Iron Sword", power=25),
            Equipment("Wooden Shield", power=10),
        ],
    )

    mage_proto = GameCharacter(
        name="Mage Template",
        char_class="Mage",
        level=1,
        stats={"str": 5, "dex": 8, "int": 18, "con": 7},
        equipment=[
            Equipment("Oak Staff", power=20),
            Equipment("Spellbook", power=15),
        ],
    )

    rogue_proto = GameCharacter(
        name="Rogue Template",
        char_class="Rogue",
        level=1,
        stats={"str": 10, "dex": 18, "int": 10, "con": 9},
        equipment=[
            Equipment("Dagger", power=18),
            Equipment("Lockpicks", power=0),
        ],
    )

    registry.register("warrior", warrior_proto)
    registry.register("mage", mage_proto)
    registry.register("rogue", rogue_proto)
    return registry


# ---------------------------------------------------------------------------
# Client code
# ---------------------------------------------------------------------------

def main():
    registry = build_registry()

    print("=== Available character templates ===")
    print(registry.list_templates())
    print()

    # Clone a warrior and customise — the original template is untouched
    hero = registry.get("warrior")
    hero.name = "Aldric"
    hero.level = 10
    hero.stats["str"] += 5          # battle-hardened
    hero.equipment.append(Equipment("Dragon Helm", power=40))

    # Clone a second warrior — completely independent
    grunt = registry.get("warrior")
    grunt.name = "Foot Soldier"
    grunt.level = 3

    print("=== Characters created from Warrior template ===")
    print(hero.describe())
    print(grunt.describe())
    print()

    # Verify deep copy: modifying hero's equipment does NOT affect grunt
    assert grunt.equipment[0].name == "Iron Sword", "Deep copy failed!"
    assert len(grunt.equipment) == 2, "Deep copy failed — shared list!"
    print("Deep copy verified: hero and grunt have independent equipment lists.")

    print()
    mage = registry.get("mage")
    mage.name = "Seraphina"
    mage.level = 15
    mage.stats["int"] += 7
    print("=== Mage ===")
    print(mage.describe())


if __name__ == "__main__":
    main()
```

---

### Java

```java
/**
 * Prototype Pattern — Java Example
 * Use case: Document template system for a word processor.
 *
 * Documents (reports, letters, invoices) share complex formatting, headers,
 * and section structures. Cloning a template is far cheaper than rebuilding
 * a document from scratch via an elaborate construction process.
 */

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

// ---------------------------------------------------------------------------
// Prototype interface
// ---------------------------------------------------------------------------

interface DocumentPrototype extends Cloneable {
    DocumentPrototype clone();
    void render();
}

// ---------------------------------------------------------------------------
// Value objects
// ---------------------------------------------------------------------------

class TextStyle {
    private final String fontFamily;
    private final int fontSize;
    private final boolean bold;

    public TextStyle(String fontFamily, int fontSize, boolean bold) {
        this.fontFamily = fontFamily;
        this.fontSize = fontSize;
        this.bold = bold;
    }

    // Deep copy constructor
    public TextStyle(TextStyle other) {
        this.fontFamily = other.fontFamily;
        this.fontSize = other.fontSize;
        this.bold = other.bold;
    }

    @Override
    public String toString() {
        return fontFamily + " " + fontSize + "pt" + (bold ? " [Bold]" : "");
    }
}

class Section {
    private String title;
    private String content;

    public Section(String title, String content) {
        this.title = title;
        this.content = content;
    }

    // Deep copy constructor
    public Section(Section other) {
        this.title = other.title;
        this.content = other.content;
    }

    public void setContent(String content) { this.content = content; }
    public String getTitle() { return title; }

    @Override
    public String toString() {
        return "  [" + title + "]: " + content;
    }
}

// ---------------------------------------------------------------------------
// Concrete prototype: BusinessDocument
// ---------------------------------------------------------------------------

class BusinessDocument implements DocumentPrototype {
    private String documentType;
    private String author;
    private TextStyle headerStyle;
    private TextStyle bodyStyle;
    private List<Section> sections;
    private Map<String, String> metadata;

    public BusinessDocument(String documentType, String author,
                            TextStyle headerStyle, TextStyle bodyStyle) {
        this.documentType = documentType;
        this.author = author;
        this.headerStyle = headerStyle;
        this.bodyStyle = bodyStyle;
        this.sections = new ArrayList<>();
        this.metadata = new HashMap<>();
    }

    /**
     * Copy constructor for deep cloning.
     * Each mutable field gets its own independent copy.
     */
    private BusinessDocument(BusinessDocument other) {
        this.documentType = other.documentType;
        this.author = other.author;
        this.headerStyle = new TextStyle(other.headerStyle);   // deep copy
        this.bodyStyle = new TextStyle(other.bodyStyle);       // deep copy

        // Deep copy of sections list
        this.sections = new ArrayList<>();
        for (Section s : other.sections) {
            this.sections.add(new Section(s));
        }

        // Deep copy of metadata map (String values are immutable, so this suffices)
        this.metadata = new HashMap<>(other.metadata);
    }

    @Override
    public BusinessDocument clone() {
        return new BusinessDocument(this);
    }

    public void addSection(String title, String content) {
        sections.add(new Section(title, content));
    }

    public void setAuthor(String author) { this.author = author; }
    public void setDocumentType(String type) { this.documentType = type; }
    public void addMetadata(String key, String value) { metadata.put(key, value); }

    public Section getSection(int index) { return sections.get(index); }

    @Override
    public void render() {
        System.out.println("╔══════════════════════════════════════════╗");
        System.out.println("  Document Type : " + documentType);
        System.out.println("  Author        : " + author);
        System.out.println("  Header Style  : " + headerStyle);
        System.out.println("  Body Style    : " + bodyStyle);
        System.out.println("  Metadata      : " + metadata);
        System.out.println("  Sections:");
        for (Section s : sections) {
            System.out.println(s);
        }
        System.out.println("╚══════════════════════════════════════════╝");
    }
}

// ---------------------------------------------------------------------------
// Prototype Registry
// ---------------------------------------------------------------------------

class DocumentRegistry {
    private final Map<String, DocumentPrototype> prototypes = new HashMap<>();

    public void register(String key, DocumentPrototype prototype) {
        prototypes.put(key, prototype);
    }

    /** Always returns a clone — never the internal prototype itself. */
    public DocumentPrototype get(String key) {
        DocumentPrototype proto = prototypes.get(key);
        if (proto == null) {
            throw new IllegalArgumentException("Unknown document template: " + key);
        }
        return proto.clone();
    }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

public class PrototypePatternDemo {

    public static void main(String[] args) {
        // --- Build templates ---
        TextStyle reportHeader = new TextStyle("Times New Roman", 18, true);
        TextStyle reportBody   = new TextStyle("Times New Roman", 12, false);

        BusinessDocument reportTemplate = new BusinessDocument(
            "Annual Report", "Template Author", reportHeader, reportBody
        );
        reportTemplate.addSection("Executive Summary", "<placeholder>");
        reportTemplate.addSection("Financial Results", "<placeholder>");
        reportTemplate.addSection("Outlook",           "<placeholder>");
        reportTemplate.addMetadata("confidential", "true");
        reportTemplate.addMetadata("revision", "1");

        TextStyle letterHeader = new TextStyle("Arial", 14, true);
        TextStyle letterBody   = new TextStyle("Arial", 11, false);

        BusinessDocument letterTemplate = new BusinessDocument(
            "Business Letter", "Template Author", letterHeader, letterBody
        );
        letterTemplate.addSection("Salutation",  "Dear Sir/Madam,");
        letterTemplate.addSection("Body",        "<placeholder>");
        letterTemplate.addSection("Closing",     "Yours faithfully,");

        // --- Register templates ---
        DocumentRegistry registry = new DocumentRegistry();
        registry.register("annual-report", reportTemplate);
        registry.register("business-letter", letterTemplate);

        // --- Client: create Q1 report by cloning the template ---
        BusinessDocument q1Report = (BusinessDocument) registry.get("annual-report");
        q1Report.setAuthor("Alice Johnson");
        q1Report.setDocumentType("Q1 2026 Financial Report");
        q1Report.getSection(0).setContent("Revenue grew 18% YoY...");
        q1Report.getSection(1).setContent("Net income: $4.2M");
        q1Report.getSection(2).setContent("Targeting 25% growth in Q2.");
        q1Report.addMetadata("revision", "3");

        // --- Client: create a letter by cloning the template ---
        BusinessDocument partnerLetter = (BusinessDocument) registry.get("business-letter");
        partnerLetter.setAuthor("Bob Smith");
        partnerLetter.getSection(0).setContent("Dear Mr. Garcia,");
        partnerLetter.getSection(1).setContent("We are pleased to announce our partnership...");

        System.out.println("=== Q1 Report ===");
        q1Report.render();

        System.out.println("\n=== Partner Letter ===");
        partnerLetter.render();

        // Verify the original template was not mutated
        System.out.println("\n=== Original Report Template (unchanged) ===");
        reportTemplate.render();
    }
}
```

---

### C++

```cpp
/**
 * Prototype Pattern — C++ Example
 * Use case: GUI widget theming system.
 *
 * A UI framework ships a set of base-themed widgets. Application code
 * clones these prototypes and adjusts only the properties it cares about,
 * rather than constructing fully-styled widgets every time.
 */

#include <iostream>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>
#include <stdexcept>

// ---------------------------------------------------------------------------
// Colour value type
// ---------------------------------------------------------------------------

struct Color {
    uint8_t r, g, b, a;

    Color(uint8_t r = 0, uint8_t g = 0, uint8_t b = 0, uint8_t a = 255)
        : r(r), g(g), b(b), a(a) {}

    std::string toString() const {
        return "rgba(" + std::to_string(r) + "," +
                         std::to_string(g) + "," +
                         std::to_string(b) + "," +
                         std::to_string(static_cast<int>(a)) + ")";
    }
};

// ---------------------------------------------------------------------------
// Prototype interface
// ---------------------------------------------------------------------------

class WidgetPrototype {
public:
    virtual ~WidgetPrototype() = default;

    /** Returns a heap-allocated deep copy owned by the caller. */
    virtual std::unique_ptr<WidgetPrototype> clone() const = 0;
    virtual void render() const = 0;

    virtual void setLabel(const std::string& label) = 0;
    virtual void setPosition(int x, int y) = 0;
};

// ---------------------------------------------------------------------------
// Concrete prototype: Button
// ---------------------------------------------------------------------------

class Button : public WidgetPrototype {
public:
    Button(std::string label,
           Color background,
           Color foreground,
           int borderRadius,
           int paddingX,
           int paddingY)
        : label_(std::move(label))
        , background_(background)
        , foreground_(foreground)
        , borderRadius_(borderRadius)
        , paddingX_(paddingX)
        , paddingY_(paddingY)
        , x_(0), y_(0)
    {}

    // Copy constructor performs a deep copy (all members are value types here)
    Button(const Button&) = default;

    std::unique_ptr<WidgetPrototype> clone() const override {
        return std::make_unique<Button>(*this);   // uses copy constructor
    }

    void setLabel(const std::string& label) override { label_ = label; }
    void setPosition(int x, int y) override { x_ = x; y_ = y; }
    void setBackground(Color c) { background_ = c; }
    void setBorderRadius(int r) { borderRadius_ = r; }

    void render() const override {
        std::cout << "[Button] \"" << label_ << "\"\n"
                  << "  Position   : (" << x_ << ", " << y_ << ")\n"
                  << "  Background : " << background_.toString() << "\n"
                  << "  Foreground : " << foreground_.toString() << "\n"
                  << "  Radius     : " << borderRadius_ << "px\n"
                  << "  Padding    : " << paddingX_ << "px / " << paddingY_ << "px\n";
    }

private:
    std::string label_;
    Color background_;
    Color foreground_;
    int borderRadius_;
    int paddingX_;
    int paddingY_;
    int x_, y_;
};

// ---------------------------------------------------------------------------
// Concrete prototype: InputField
// ---------------------------------------------------------------------------

class InputField : public WidgetPrototype {
public:
    InputField(std::string placeholder,
               Color borderColor,
               Color backgroundColor,
               int width,
               int height)
        : placeholder_(std::move(placeholder))
        , label_("Input")
        , borderColor_(borderColor)
        , backgroundColor_(backgroundColor)
        , width_(width)
        , height_(height)
        , x_(0), y_(0)
    {}

    InputField(const InputField&) = default;

    std::unique_ptr<WidgetPrototype> clone() const override {
        return std::make_unique<InputField>(*this);
    }

    void setLabel(const std::string& label) override { label_ = label; }
    void setPosition(int x, int y) override { x_ = x; y_ = y; }
    void setPlaceholder(const std::string& ph) { placeholder_ = ph; }
    void setWidth(int w) { width_ = w; }

    void render() const override {
        std::cout << "[InputField] \"" << label_ << "\"\n"
                  << "  Placeholder : " << placeholder_ << "\n"
                  << "  Position    : (" << x_ << ", " << y_ << ")\n"
                  << "  Border      : " << borderColor_.toString() << "\n"
                  << "  Background  : " << backgroundColor_.toString() << "\n"
                  << "  Size        : " << width_ << "x" << height_ << "\n";
    }

private:
    std::string placeholder_;
    std::string label_;
    Color borderColor_;
    Color backgroundColor_;
    int width_, height_;
    int x_, y_;
};

// ---------------------------------------------------------------------------
// Prototype Registry
// ---------------------------------------------------------------------------

class WidgetRegistry {
public:
    void registerWidget(const std::string& key,
                        std::unique_ptr<WidgetPrototype> proto) {
        prototypes_[key] = std::move(proto);
    }

    std::unique_ptr<WidgetPrototype> create(const std::string& key) const {
        auto it = prototypes_.find(key);
        if (it == prototypes_.end()) {
            throw std::invalid_argument("Unknown widget prototype: " + key);
        }
        return it->second->clone();
    }

private:
    std::unordered_map<std::string,
                       std::unique_ptr<WidgetPrototype>> prototypes_;
};

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

int main() {
    // --- Define theme prototypes ---
    WidgetRegistry registry;

    // Dark-theme primary button
    registry.registerWidget("btn-primary-dark", std::make_unique<Button>(
        "Click Me",
        Color{59, 130, 246},    // blue background
        Color{255, 255, 255},   // white text
        8,                      // border radius
        16, 8                   // padding
    ));

    // Dark-theme secondary button (danger)
    registry.registerWidget("btn-danger-dark", std::make_unique<Button>(
        "Delete",
        Color{239, 68, 68},     // red background
        Color{255, 255, 255},
        6,
        12, 6
    ));

    // Standard text input
    registry.registerWidget("input-text", std::make_unique<InputField>(
        "Enter value...",
        Color{209, 213, 219},   // gray border
        Color{255, 255, 255},   // white bg
        240,
        40
    ));

    // --- Build a login form by cloning prototypes ---

    auto usernameField = registry.create("input-text");
    usernameField->setLabel("Username");
    usernameField->setPosition(100, 200);

    // Downcast to access InputField-specific API
    auto* uf = dynamic_cast<InputField*>(usernameField.get());
    if (uf) uf->setPlaceholder("Enter your username");

    auto passwordField = registry.create("input-text");
    passwordField->setLabel("Password");
    passwordField->setPosition(100, 260);

    auto loginBtn = registry.create("btn-primary-dark");
    loginBtn->setLabel("Sign In");
    loginBtn->setPosition(100, 320);

    auto cancelBtn = registry.create("btn-danger-dark");
    cancelBtn->setLabel("Cancel");
    cancelBtn->setPosition(220, 320);

    // --- Render the form ---
    std::cout << "=== Login Form Widgets ===\n\n";
    usernameField->render();
    std::cout << "\n";
    passwordField->render();
    std::cout << "\n";
    loginBtn->render();
    std::cout << "\n";
    cancelBtn->render();

    std::cout << "\nAll widgets created via prototype cloning.\n";
    return 0;
}
```

---

### C#

```csharp
/**
 * Prototype Pattern — C# Example
 * Use case: Report configuration cloning in a business intelligence tool.
 *
 * BI dashboards share complex filter sets, column configurations, and
 * formatting rules. Cloning a base report gives users a starting point
 * they can personalise without affecting shared templates.
 */

using System;
using System.Collections.Generic;
using System.Linq;

namespace PrototypePattern
{
    // ---------------------------------------------------------------------------
    // Prototype interface
    // ---------------------------------------------------------------------------

    public interface IReportPrototype
    {
        IReportPrototype Clone();
        void Display();
    }

    // ---------------------------------------------------------------------------
    // Value types / sub-objects
    // ---------------------------------------------------------------------------

    public class ColumnConfig
    {
        public string Name { get; set; }
        public int Width { get; set; }
        public bool Visible { get; set; }
        public string Alignment { get; set; }

        public ColumnConfig(string name, int width, bool visible, string alignment)
        {
            Name = name; Width = width; Visible = visible; Alignment = alignment;
        }

        // Copy constructor for deep cloning
        public ColumnConfig(ColumnConfig other)
        {
            Name = other.Name;
            Width = other.Width;
            Visible = other.Visible;
            Alignment = other.Alignment;
        }

        public override string ToString() =>
            $"  Column[{Name}] w={Width} visible={Visible} align={Alignment}";
    }

    public class FilterRule
    {
        public string Field { get; set; }
        public string Operator { get; set; }
        public string Value { get; set; }

        public FilterRule(string field, string op, string value)
        {
            Field = field; Operator = op; Value = value;
        }

        public FilterRule(FilterRule other)
        {
            Field = other.Field; Operator = other.Operator; Value = other.Value;
        }

        public override string ToString() => $"  Filter: {Field} {Operator} {Value}";
    }

    // ---------------------------------------------------------------------------
    // Concrete prototype: DashboardReport
    // ---------------------------------------------------------------------------

    public class DashboardReport : IReportPrototype
    {
        public string Name { get; set; }
        public string Owner { get; set; }
        public string DataSource { get; set; }
        public List<ColumnConfig> Columns { get; private set; }
        public List<FilterRule> Filters { get; private set; }
        public Dictionary<string, string> ChartSettings { get; private set; }

        public DashboardReport(string name, string owner, string dataSource)
        {
            Name = name;
            Owner = owner;
            DataSource = dataSource;
            Columns = new List<ColumnConfig>();
            Filters = new List<FilterRule>();
            ChartSettings = new Dictionary<string, string>();
        }

        // Private copy constructor — used only by Clone()
        private DashboardReport(DashboardReport other)
        {
            Name = other.Name;
            Owner = other.Owner;
            DataSource = other.DataSource;

            // Deep copy each collection
            Columns = other.Columns.Select(c => new ColumnConfig(c)).ToList();
            Filters = other.Filters.Select(f => new FilterRule(f)).ToList();
            ChartSettings = new Dictionary<string, string>(other.ChartSettings);
        }

        public IReportPrototype Clone() => new DashboardReport(this);

        public void AddColumn(ColumnConfig col) => Columns.Add(col);
        public void AddFilter(FilterRule filter) => Filters.Add(filter);
        public void SetChartSetting(string key, string value) => ChartSettings[key] = value;

        public void Display()
        {
            Console.WriteLine($"╔══ Report: {Name} ══╗");
            Console.WriteLine($"  Owner      : {Owner}");
            Console.WriteLine($"  DataSource : {DataSource}");
            Console.WriteLine("  Columns:");
            foreach (var col in Columns) Console.WriteLine(col);
            Console.WriteLine("  Filters:");
            foreach (var f in Filters) Console.WriteLine(f);
            Console.WriteLine("  Chart Settings:");
            foreach (var kv in ChartSettings)
                Console.WriteLine($"  {kv.Key} = {kv.Value}");
            Console.WriteLine();
        }
    }

    // ---------------------------------------------------------------------------
    // Prototype Registry
    // ---------------------------------------------------------------------------

    public class ReportRegistry
    {
        private readonly Dictionary<string, IReportPrototype> _prototypes = new();

        public void Register(string key, IReportPrototype prototype)
            => _prototypes[key] = prototype;

        public IReportPrototype Get(string key)
        {
            if (!_prototypes.TryGetValue(key, out var proto))
                throw new KeyNotFoundException($"Report template not found: {key}");
            return proto.Clone();
        }
    }

    // ---------------------------------------------------------------------------
    // Entry point
    // ---------------------------------------------------------------------------

    class Program
    {
        static void Main(string[] args)
        {
            // --- Build the sales report template ---
            var salesTemplate = new DashboardReport(
                "Sales Overview Template", "System", "sales_db");

            salesTemplate.AddColumn(new ColumnConfig("Order ID",   80,  true,  "center"));
            salesTemplate.AddColumn(new ColumnConfig("Product",    160, true,  "left"));
            salesTemplate.AddColumn(new ColumnConfig("Region",     100, true,  "left"));
            salesTemplate.AddColumn(new ColumnConfig("Revenue",    100, true,  "right"));
            salesTemplate.AddColumn(new ColumnConfig("Cost",       100, false, "right"));
            salesTemplate.AddFilter(new FilterRule("Status", "==", "Closed"));
            salesTemplate.SetChartSetting("type", "bar");
            salesTemplate.SetChartSetting("colorScheme", "blue");

            var registry = new ReportRegistry();
            registry.Register("sales-overview", salesTemplate);

            // --- Alice clones the template for her EMEA report ---
            var aliceReport = (DashboardReport)registry.Get("sales-overview");
            aliceReport.Name  = "EMEA Q2 Sales — Alice";
            aliceReport.Owner = "Alice";
            aliceReport.AddFilter(new FilterRule("Region", "==", "EMEA"));
            aliceReport.AddFilter(new FilterRule("Quarter", "==", "Q2"));
            // Show cost column for Alice's view
            aliceReport.Columns.First(c => c.Name == "Cost").Visible = true;

            // --- Bob clones the template for his APAC report ---
            var bobReport = (DashboardReport)registry.Get("sales-overview");
            bobReport.Name  = "APAC Annual Sales — Bob";
            bobReport.Owner = "Bob";
            bobReport.AddFilter(new FilterRule("Region", "==", "APAC"));
            bobReport.SetChartSetting("type", "line");

            Console.WriteLine("=== Alice's Report ===");
            aliceReport.Display();

            Console.WriteLine("=== Bob's Report ===");
            bobReport.Display();

            // The original template must remain unchanged
            Console.WriteLine("=== Original Template (must be unchanged) ===");
            salesTemplate.Display();

            // Assert deep copy: Alice's column mutation did not affect template
            bool templateCostVisible = salesTemplate.Columns.First(c => c.Name == "Cost").Visible;
            Console.WriteLine($"Template 'Cost' column still hidden: {!templateCostVisible}");
            Console.WriteLine($"Template filter count still 1: {salesTemplate.Filters.Count == 1}");
        }
    }
}
```

---

### TypeScript

```typescript
/**
 * Prototype Pattern — TypeScript Example
 * Use case: Email campaign template engine.
 *
 * Marketing teams design master email templates. Campaign managers clone
 * a template, swap in personalised content, and schedule sends — without
 * modifying the master template stored in the registry.
 */

// ---------------------------------------------------------------------------
// Prototype interface
// ---------------------------------------------------------------------------

interface Cloneable<T> {
  clone(): T;
}

// ---------------------------------------------------------------------------
// Value types
// ---------------------------------------------------------------------------

interface TextBlock {
  id: string;
  content: string;
  style: {
    fontFamily: string;
    fontSize: number;
    color: string;
    bold: boolean;
  };
}

interface ImageBlock {
  id: string;
  src: string;
  alt: string;
  width: number;
  height: number;
}

type Block = TextBlock | ImageBlock;

interface RecipientSegment {
  name: string;
  filter: Record<string, string>;
}

// ---------------------------------------------------------------------------
// Concrete prototype: EmailCampaign
// ---------------------------------------------------------------------------

class EmailCampaign implements Cloneable<EmailCampaign> {
  public name: string;
  public subjectLine: string;
  public senderName: string;
  public senderEmail: string;
  public blocks: Block[];
  public segment: RecipientSegment;
  public scheduledAt: Date | null;
  public trackingParams: Map<string, string>;

  constructor(
    name: string,
    subjectLine: string,
    senderName: string,
    senderEmail: string,
    segment: RecipientSegment
  ) {
    this.name = name;
    this.subjectLine = subjectLine;
    this.senderName = senderName;
    this.senderEmail = senderEmail;
    this.blocks = [];
    this.segment = segment;
    this.scheduledAt = null;
    this.trackingParams = new Map();
  }

  /**
   * Deep clone: all nested objects are independently copied.
   * Modifications to the clone never affect the original.
   */
  clone(): EmailCampaign {
    const copy = new EmailCampaign(
      this.name,
      this.subjectLine,
      this.senderName,
      this.senderEmail,
      // Deep-copy the segment and its nested filter object
      {
        name: this.segment.name,
        filter: { ...this.segment.filter },
      }
    );

    // Deep-copy each block (style objects are plain value objects)
    copy.blocks = this.blocks.map((block) => {
      if ("style" in block) {
        return {
          ...block,
          style: { ...block.style },
        } as TextBlock;
      }
      return { ...block } as ImageBlock;
    });

    copy.scheduledAt = this.scheduledAt ? new Date(this.scheduledAt) : null;
    copy.trackingParams = new Map(this.trackingParams);

    return copy;
  }

  addBlock(block: Block): this {
    this.blocks.push(block);
    return this;
  }

  setTracking(key: string, value: string): this {
    this.trackingParams.set(key, value);
    return this;
  }

  schedule(date: Date): this {
    this.scheduledAt = date;
    return this;
  }

  display(): void {
    console.log(`\n== Campaign: ${this.name} ==`);
    console.log(`  Subject  : ${this.subjectLine}`);
    console.log(`  Sender   : ${this.senderName} <${this.senderEmail}>`);
    console.log(`  Segment  : ${this.segment.name}`, this.segment.filter);
    console.log(`  Blocks   : ${this.blocks.length}`);
    this.blocks.forEach((b, i) => {
      if ("content" in b) {
        console.log(`    [${i}] Text: "${b.content.substring(0, 40)}..."`);
      } else {
        console.log(`    [${i}] Image: ${b.src}`);
      }
    });
    console.log(
      `  Scheduled: ${this.scheduledAt?.toISOString() ?? "not scheduled"}`
    );
    console.log(`  Tracking :`, Object.fromEntries(this.trackingParams));
  }
}

// ---------------------------------------------------------------------------
// Prototype Registry
// ---------------------------------------------------------------------------

class CampaignRegistry {
  private readonly templates = new Map<string, EmailCampaign>();

  register(key: string, template: EmailCampaign): void {
    this.templates.set(key, template);
  }

  /** Always returns a fresh clone, never the stored prototype. */
  get(key: string): EmailCampaign {
    const proto = this.templates.get(key);
    if (!proto) throw new Error(`No campaign template registered as "${key}"`);
    return proto.clone();
  }

  listTemplates(): string[] {
    return [...this.templates.keys()];
  }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

function main(): void {
  // --- Build master templates ---
  const registry = new CampaignRegistry();

  const newsletterMaster = new EmailCampaign(
    "Monthly Newsletter Template",
    "{{Month}} Updates from Acme Corp",
    "Acme Newsletter",
    "newsletter@acme.com",
    { name: "All Subscribers", filter: { subscribed: "true" } }
  );

  newsletterMaster
    .addBlock({
      id: "header",
      src: "https://cdn.acme.com/newsletter-header.png",
      alt: "Newsletter Header",
      width: 600,
      height: 200,
    })
    .addBlock({
      id: "intro",
      content: "Welcome to this month's edition of the Acme newsletter...",
      style: {
        fontFamily: "Arial",
        fontSize: 16,
        color: "#333333",
        bold: false,
      },
    })
    .addBlock({
      id: "cta",
      content: "Read more on our blog →",
      style: {
        fontFamily: "Arial",
        fontSize: 14,
        color: "#2563eb",
        bold: true,
      },
    })
    .setTracking("utm_source", "email")
    .setTracking("utm_medium", "newsletter");

  registry.register("newsletter", newsletterMaster);

  // --- Campaign manager clones newsletter template for June ---
  const juneCampaign = registry.get("newsletter");
  juneCampaign.name = "June 2026 Newsletter";
  juneCampaign.subjectLine = "June Updates from Acme Corp";
  juneCampaign.segment = { name: "Premium Subscribers", filter: { tier: "premium" } };
  juneCampaign.setTracking("utm_campaign", "june-2026");
  juneCampaign.schedule(new Date("2026-06-15T09:00:00Z"));

  // Swap the intro text specifically for June
  const introBlock = juneCampaign.blocks[1] as TextBlock;
  introBlock.content = "Welcome to June's edition — summer specials inside!";

  // --- Another manager clones for a flash-sale campaign ---
  const flashSale = registry.get("newsletter");
  flashSale.name = "Flash Sale Alert";
  flashSale.subjectLine = "48-Hour Flash Sale — 40% OFF Everything!";
  flashSale.senderName = "Acme Deals";
  flashSale.senderEmail = "deals@acme.com";
  flashSale.setTracking("utm_campaign", "flash-sale-june");
  flashSale.schedule(new Date("2026-06-10T12:00:00Z"));

  // --- Display results ---
  juneCampaign.display();
  flashSale.display();

  // Verify the master template was not mutated
  console.log("\n-- Master template subject (must still have {{Month}}):");
  console.log(" ", newsletterMaster.subjectLine);
  console.log("-- Master template segment (must be 'All Subscribers'):");
  console.log(" ", newsletterMaster.segment.name);

  console.log("\nAvailable templates:", registry.listTemplates());
}

main();
```

---

### Go

```go
// Prototype Pattern — Go Example
// Use case: Network packet builder for a protocol testing tool.
//
// A test harness needs to generate thousands of slightly-varied network
// packets (TCP, UDP, ICMP). Each packet type has a complex set of header
// fields. Cloning prototype packets and tweaking specific fields is far
// cleaner than rebuilding packets from scratch each time.

package main

import (
	"fmt"
	"net"
	"time"
)

// ---------------------------------------------------------------------------
// Prototype interface
// ---------------------------------------------------------------------------

// PacketPrototype is the cloneable interface all packet types implement.
type PacketPrototype interface {
	Clone() PacketPrototype
	Describe() string
	SetPayload(data []byte)
}

// ---------------------------------------------------------------------------
// Concrete prototype: TCPPacket
// ---------------------------------------------------------------------------

// TCPFlags models the TCP control bits.
type TCPFlags struct {
	SYN bool
	ACK bool
	FIN bool
	RST bool
	PSH bool
}

// TCPOptions holds optional TCP header fields.
type TCPOptions struct {
	WindowScale      uint8
	MaxSegmentSize   uint16
	TimestampEnabled bool
}

// TCPPacket is a concrete prototype representing a TCP segment.
type TCPPacket struct {
	SrcIP      net.IP
	DstIP      net.IP
	SrcPort    uint16
	DstPort    uint16
	SeqNum     uint32
	AckNum     uint32
	Flags      TCPFlags
	WindowSize uint16
	Options    TCPOptions
	Payload    []byte
	CreatedAt  time.Time
}

// Clone returns a deep copy of the TCPPacket.
// All slices and nested structs are duplicated so the clone is fully independent.
func (p *TCPPacket) Clone() PacketPrototype {
	clone := *p // shallow copy of all value fields

	// Deep-copy IP address slices
	clone.SrcIP = make(net.IP, len(p.SrcIP))
	copy(clone.SrcIP, p.SrcIP)

	clone.DstIP = make(net.IP, len(p.DstIP))
	copy(clone.DstIP, p.DstIP)

	// Deep-copy payload
	if p.Payload != nil {
		clone.Payload = make([]byte, len(p.Payload))
		copy(clone.Payload, p.Payload)
	}

	// TCPOptions and TCPFlags are value types — copied by the struct copy above.
	clone.CreatedAt = time.Now()
	return &clone
}

func (p *TCPPacket) SetPayload(data []byte) {
	p.Payload = make([]byte, len(data))
	copy(p.Payload, data)
}

func (p *TCPPacket) Describe() string {
	return fmt.Sprintf(
		"TCP  %s:%d -> %s:%d  seq=%d ack=%d  SYN=%v ACK=%v FIN=%v  "+
			"window=%d  payload=%d bytes  created=%s",
		p.SrcIP, p.SrcPort,
		p.DstIP, p.DstPort,
		p.SeqNum, p.AckNum,
		p.Flags.SYN, p.Flags.ACK, p.Flags.FIN,
		p.WindowSize,
		len(p.Payload),
		p.CreatedAt.Format(time.RFC3339),
	)
}

// ---------------------------------------------------------------------------
// Concrete prototype: UDPPacket
// ---------------------------------------------------------------------------

type UDPPacket struct {
	SrcIP     net.IP
	DstIP     net.IP
	SrcPort   uint16
	DstPort   uint16
	Payload   []byte
	CreatedAt time.Time
}

func (p *UDPPacket) Clone() PacketPrototype {
	clone := *p

	clone.SrcIP = make(net.IP, len(p.SrcIP))
	copy(clone.SrcIP, p.SrcIP)

	clone.DstIP = make(net.IP, len(p.DstIP))
	copy(clone.DstIP, p.DstIP)

	if p.Payload != nil {
		clone.Payload = make([]byte, len(p.Payload))
		copy(clone.Payload, p.Payload)
	}

	clone.CreatedAt = time.Now()
	return &clone
}

func (p *UDPPacket) SetPayload(data []byte) {
	p.Payload = make([]byte, len(data))
	copy(p.Payload, data)
}

func (p *UDPPacket) Describe() string {
	return fmt.Sprintf(
		"UDP  %s:%d -> %s:%d  payload=%d bytes  created=%s",
		p.SrcIP, p.SrcPort,
		p.DstIP, p.DstPort,
		len(p.Payload),
		p.CreatedAt.Format(time.RFC3339),
	)
}

// ---------------------------------------------------------------------------
// Prototype Registry
// ---------------------------------------------------------------------------

// PacketRegistry stores named packet prototypes for reuse.
type PacketRegistry struct {
	prototypes map[string]PacketPrototype
}

func NewPacketRegistry() *PacketRegistry {
	return &PacketRegistry{prototypes: make(map[string]PacketPrototype)}
}

func (r *PacketRegistry) Register(key string, proto PacketPrototype) {
	r.prototypes[key] = proto
}

// Build always returns a fresh clone — the stored prototype is never mutated.
func (r *PacketRegistry) Build(key string) (PacketPrototype, error) {
	proto, ok := r.prototypes[key]
	if !ok {
		return nil, fmt.Errorf("unknown packet prototype: %q", key)
	}
	return proto.Clone(), nil
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

func main() {
	registry := NewPacketRegistry()

	// --- Register TCP SYN prototype (typical connection initiation) ---
	tcpSYNProto := &TCPPacket{
		SrcIP:      net.ParseIP("10.0.0.1"),
		DstIP:      net.ParseIP("10.0.0.2"),
		SrcPort:    0, // will be randomised per packet
		DstPort:    80,
		SeqNum:     0,
		AckNum:     0,
		Flags:      TCPFlags{SYN: true},
		WindowSize: 65535,
		Options: TCPOptions{
			WindowScale:      7,
			MaxSegmentSize:   1460,
			TimestampEnabled: true,
		},
		CreatedAt: time.Now(),
	}
	registry.Register("tcp-syn", tcpSYNProto)

	// --- Register UDP DNS query prototype ---
	udpDNSProto := &UDPPacket{
		SrcIP:     net.ParseIP("192.168.1.10"),
		DstIP:     net.ParseIP("8.8.8.8"),
		SrcPort:   0, // ephemeral
		DstPort:   53,
		CreatedAt: time.Now(),
	}
	registry.Register("udp-dns", udpDNSProto)

	// --- Generate 3 varied TCP SYN packets ---
	fmt.Println("=== Generated TCP SYN Packets ===")
	for i := 0; i < 3; i++ {
		pkt, err := registry.Build("tcp-syn")
		if err != nil {
			panic(err)
		}
		tcpPkt := pkt.(*TCPPacket)
		tcpPkt.SrcPort = uint16(49152 + i) // unique ephemeral port
		tcpPkt.SeqNum = uint32(1000 * (i + 1))
		fmt.Println(tcpPkt.Describe())
	}

	// --- Generate 2 UDP DNS packets ---
	fmt.Println("\n=== Generated UDP DNS Packets ===")
	dnsPayload1 := []byte{0x00, 0x01, 0x01, 0x00} // query for "example.com"
	dnsPayload2 := []byte{0x00, 0x02, 0x01, 0x00} // query for "google.com"

	for i, payload := range [][]byte{dnsPayload1, dnsPayload2} {
		pkt, err := registry.Build("udp-dns")
		if err != nil {
			panic(err)
		}
		udpPkt := pkt.(*UDPPacket)
		udpPkt.SrcPort = uint16(33000 + i)
		udpPkt.SetPayload(payload)
		fmt.Println(udpPkt.Describe())
	}

	// --- Verify deep copy: original prototypes are unmodified ---
	fmt.Println("\n=== Prototype Integrity Check ===")
	origTCP := tcpSYNProto
	fmt.Printf("TCP proto SrcPort still 0: %v\n", origTCP.SrcPort == 0)
	fmt.Printf("TCP proto SeqNum still 0 : %v\n", origTCP.SeqNum == 0)
}
```

---

### PHP

```php
<?php

/**
 * Prototype Pattern — PHP Example
 * Use case: Product catalogue with configurable product variants.
 *
 * An e-commerce platform has base product definitions (base price, images,
 * shipping class). Merchants create variants (size, colour, material) by
 * cloning the base product and overriding only the differing attributes,
 * rather than re-entering all shared data.
 */

declare(strict_types=1);

// ---------------------------------------------------------------------------
// Value objects
// ---------------------------------------------------------------------------

class Dimension
{
    public function __construct(
        public readonly float $length,
        public readonly float $width,
        public readonly float $height,
        public readonly string $unit = 'cm'
    ) {}

    public function __toString(): string
    {
        return "{$this->length}×{$this->width}×{$this->height} {$this->unit}";
    }
}

class PricingTier
{
    public function __construct(
        public readonly string $currency,
        public float $basePrice,
        public float $salePrice = 0.0
    ) {}

    public function __clone()
    {
        // PricingTier is a simple value object; nothing special needed.
        // PHP clones scalar properties automatically.
    }

    public function __toString(): string
    {
        $sale = $this->salePrice > 0 ? " (sale: {$this->salePrice})" : '';
        return "{$this->currency} {$this->basePrice}{$sale}";
    }
}

// ---------------------------------------------------------------------------
// Prototype interface (PHP uses __clone() convention but we add an explicit method)
// ---------------------------------------------------------------------------

interface ProductPrototype
{
    public function cloneProduct(): static;
    public function display(): void;
}

// ---------------------------------------------------------------------------
// Concrete prototype: Product
// ---------------------------------------------------------------------------

class Product implements ProductPrototype
{
    public string $sku;
    public string $name;
    public string $category;
    public string $brand;
    public string $description;
    public Dimension $dimension;
    public float $weightKg;
    public PricingTier $pricing;
    /** @var string[] */
    public array $imageUrls;
    /** @var array<string, string> */
    public array $attributes;
    public string $shippingClass;
    public bool $active;

    public function __construct(
        string $sku,
        string $name,
        string $category,
        string $brand,
        string $description,
        Dimension $dimension,
        float $weightKg,
        PricingTier $pricing,
        string $shippingClass = 'standard'
    ) {
        $this->sku          = $sku;
        $this->name         = $name;
        $this->category     = $category;
        $this->brand        = $brand;
        $this->description  = $description;
        $this->dimension    = $dimension;
        $this->weightKg     = $weightKg;
        $this->pricing      = $pricing;
        $this->shippingClass = $shippingClass;
        $this->imageUrls    = [];
        $this->attributes   = [];
        $this->active       = true;
    }

    /**
     * PHP's __clone() is called automatically when clone $obj is used.
     * We perform deep copies of all nested objects here.
     */
    public function __clone()
    {
        // Clone nested objects so they are independent
        $this->dimension = clone $this->dimension;
        $this->pricing   = clone $this->pricing;
        // Arrays of scalars are copied by value in PHP — no extra work needed
    }

    public function cloneProduct(): static
    {
        return clone $this;
    }

    public function addImage(string $url): static
    {
        $this->imageUrls[] = $url;
        return $this;
    }

    public function setAttribute(string $key, string $value): static
    {
        $this->attributes[$key] = $value;
        return $this;
    }

    public function display(): void
    {
        echo "┌─────────────────────────────────────────┐\n";
        echo "  SKU       : {$this->sku}\n";
        echo "  Name      : {$this->name}\n";
        echo "  Brand     : {$this->brand}\n";
        echo "  Category  : {$this->category}\n";
        echo "  Pricing   : {$this->pricing}\n";
        echo "  Dimension : {$this->dimension}\n";
        echo "  Weight    : {$this->weightKg} kg\n";
        echo "  Shipping  : {$this->shippingClass}\n";
        echo "  Active    : " . ($this->active ? 'Yes' : 'No') . "\n";
        echo "  Images    : " . implode(', ', $this->imageUrls) . "\n";
        echo "  Attributes:\n";
        foreach ($this->attributes as $k => $v) {
            echo "    {$k}: {$v}\n";
        }
        echo "└─────────────────────────────────────────┘\n";
    }
}

// ---------------------------------------------------------------------------
// Prototype Registry
// ---------------------------------------------------------------------------

class ProductRegistry
{
    /** @var array<string, ProductPrototype> */
    private array $prototypes = [];

    public function register(string $key, ProductPrototype $product): void
    {
        $this->prototypes[$key] = $product;
    }

    public function create(string $key): ProductPrototype
    {
        if (!isset($this->prototypes[$key])) {
            throw new \InvalidArgumentException("Unknown product prototype: {$key}");
        }
        return $this->prototypes[$key]->cloneProduct();
    }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

// Base T-shirt product definition
$baseShirt = new Product(
    sku:          'SHIRT-BASE',
    name:         'Classic Cotton T-Shirt',
    category:     'Apparel',
    brand:        'AcmeFashion',
    description:  'Comfortable 100% organic cotton t-shirt.',
    dimension:    new Dimension(30, 25, 2),
    weightKg:     0.25,
    pricing:      new PricingTier('USD', 29.99),
    shippingClass: 'lightweight'
);

$baseShirt
    ->addImage('https://cdn.acme.com/shirts/base-front.jpg')
    ->addImage('https://cdn.acme.com/shirts/base-back.jpg')
    ->setAttribute('material', '100% Organic Cotton')
    ->setAttribute('care', 'Machine wash cold');

$registry = new ProductRegistry();
$registry->register('shirt-base', $baseShirt);

// --- Create size variants by cloning ---

$shirtSmallRed = $registry->create('shirt-base');
$shirtSmallRed->sku  = 'SHIRT-S-RED';
$shirtSmallRed->name = 'Classic Cotton T-Shirt — Small / Red';
$shirtSmallRed->setAttribute('size', 'S');
$shirtSmallRed->setAttribute('colour', 'Red');
$shirtSmallRed->pricing->basePrice = 29.99;

$shirtLargeBlue = $registry->create('shirt-base');
$shirtLargeBlue->sku  = 'SHIRT-L-BLUE';
$shirtLargeBlue->name = 'Classic Cotton T-Shirt — Large / Blue';
$shirtLargeBlue->setAttribute('size', 'L');
$shirtLargeBlue->setAttribute('colour', 'Blue');
$shirtLargeBlue->weightKg = 0.28; // slightly heavier
$shirtLargeBlue->pricing->basePrice = 32.99;

// Limited edition variant with sale price
$shirtXLBlackSale = $registry->create('shirt-base');
$shirtXLBlackSale->sku  = 'SHIRT-XL-BLK-SALE';
$shirtXLBlackSale->name = 'Classic Cotton T-Shirt — XL / Black (SALE)';
$shirtXLBlackSale->setAttribute('size', 'XL');
$shirtXLBlackSale->setAttribute('colour', 'Black');
$shirtXLBlackSale->pricing->basePrice = 34.99;
$shirtXLBlackSale->pricing->salePrice = 24.99;

echo "=== Small / Red ===\n";
$shirtSmallRed->display();

echo "\n=== Large / Blue ===\n";
$shirtLargeBlue->display();

echo "\n=== XL / Black (Sale) ===\n";
$shirtXLBlackSale->display();

// Verify the base prototype is unaffected
echo "\n=== Base Prototype (must be unchanged) ===\n";
$baseShirt->display();

echo "\nBase prototype price unchanged: " .
    ($baseShirt->pricing->basePrice === 29.99 ? 'YES' : 'NO') . "\n";
echo "Base prototype has no colour attribute: " .
    (!isset($baseShirt->attributes['colour']) ? 'YES' : 'NO') . "\n";
```

---

### Ruby

```ruby
# Prototype Pattern — Ruby Example
# Use case: Configuration profiles for a CI/CD pipeline runner.
#
# A CI system ships default pipeline configurations (build, test, deploy
# stages). Teams clone these base configurations and override only the
# steps relevant to their project, without altering the shared defaults.

require 'date'

# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

# Represents a single pipeline step (immutable-ish value object).
Step = Struct.new(:name, :command, :timeout_seconds, :allow_failure,
                  keyword_init: true) do
  def to_s
    flag = allow_failure ? ' [allow_failure]' : ''
    "    Step[#{name}]: `#{command}` (timeout: #{timeout_seconds}s)#{flag}"
  end
end

# Environment variable definition.
EnvVar = Struct.new(:key, :value, keyword_init: true) do
  def to_s
    "#{key}=#{value}"
  end
end

# ---------------------------------------------------------------------------
# Prototype: PipelineConfig
# ---------------------------------------------------------------------------

class PipelineConfig
  attr_accessor :name, :description, :image, :cache_paths,
                :before_script, :stages, :env_vars, :artifact_paths,
                :timeout_minutes, :tags, :created_at

  def initialize(name:, description:, image:, timeout_minutes: 60)
    @name             = name
    @description      = description
    @image            = image
    @timeout_minutes  = timeout_minutes
    @cache_paths      = []
    @before_script    = []
    @stages           = {}       # { stage_name => [Step, ...] }
    @env_vars         = []
    @artifact_paths   = []
    @tags             = []
    @created_at       = Date.today
  end

  # Deep clone — Ruby's Object#dup only does a shallow copy,
  # so we manually deep-copy every mutable structure.
  def clone_config
    copy = self.class.new(
      name:            @name,
      description:     @description,
      image:           @image,
      timeout_minutes: @timeout_minutes
    )

    copy.cache_paths   = @cache_paths.dup
    copy.before_script = @before_script.dup
    copy.env_vars      = @env_vars.map { |e| EnvVar.new(key: e.key, value: e.value) }
    copy.artifact_paths = @artifact_paths.dup
    copy.tags          = @tags.dup

    # Deep-copy the stages hash (each value is an array of Step structs)
    copy.stages = @stages.transform_values do |steps|
      steps.map { |s| Step.new(name: s.name, command: s.command,
                               timeout_seconds: s.timeout_seconds,
                               allow_failure: s.allow_failure) }
    end

    copy.created_at = Date.today
    copy
  end

  def add_stage(name, steps)
    @stages[name] = steps
    self
  end

  def add_env(key, value)
    @env_vars << EnvVar.new(key: key, value: value)
    self
  end

  def display
    puts "╔══════════════════════════════════════════╗"
    puts "  Pipeline : #{@name}"
    puts "  Image    : #{@image}"
    puts "  Timeout  : #{@timeout_minutes} min"
    puts "  Tags     : #{@tags.join(', ')}"
    puts "  Env Vars : #{@env_vars.map(&:to_s).join(', ')}"
    puts "  Cache    : #{@cache_paths.join(', ')}"
    puts "  Stages   :"
    @stages.each do |stage, steps|
      puts "  [#{stage}]"
      steps.each { |s| puts s }
    end
    puts "  Artifacts: #{@artifact_paths.join(', ')}"
    puts "╚══════════════════════════════════════════╝"
  end
end

# ---------------------------------------------------------------------------
# Prototype Registry
# ---------------------------------------------------------------------------

class PipelineRegistry
  def initialize
    @prototypes = {}
  end

  def register(key, config)
    @prototypes[key] = config
  end

  # Returns a fresh deep clone — the stored prototype is never mutated.
  def build(key)
    proto = @prototypes[key]
    raise ArgumentError, "Unknown pipeline template: #{key.inspect}" unless proto
    proto.clone_config
  end

  def templates
    @prototypes.keys
  end
end

# ---------------------------------------------------------------------------
# Set up the registry with base templates
# ---------------------------------------------------------------------------

registry = PipelineRegistry.new

# -- Node.js base template --
node_base = PipelineConfig.new(
  name:            'Node.js Base Template',
  description:     'Standard Node.js CI pipeline',
  image:           'node:20-alpine',
  timeout_minutes: 45
)
node_base
  .add_env('NODE_ENV', 'ci')
  .add_env('CI', 'true')

node_base.cache_paths    = ['node_modules/', '.npm/']
node_base.artifact_paths = ['dist/', 'coverage/']
node_base.tags           = ['linux', 'docker']
node_base.before_script  = ['npm ci --prefer-offline']
node_base.add_stage('build', [
  Step.new(name: 'compile', command: 'npm run build',    timeout_seconds: 300, allow_failure: false),
  Step.new(name: 'lint',    command: 'npm run lint',     timeout_seconds: 120, allow_failure: false)
])
node_base.add_stage('test', [
  Step.new(name: 'unit',    command: 'npm test',         timeout_seconds: 300, allow_failure: false),
  Step.new(name: 'coverage',command: 'npm run coverage', timeout_seconds: 300, allow_failure: true)
])

registry.register('node-base', node_base)

# ---------------------------------------------------------------------------
# Client code — create project-specific pipelines by cloning
# ---------------------------------------------------------------------------

# --- Team A: Frontend SPA project ---
spa_pipeline = registry.build('node-base')
spa_pipeline.name  = 'Frontend SPA — CI Pipeline'
spa_pipeline.image = 'node:20-bullseye'  # needs more tools
spa_pipeline.add_env('BUILD_TARGET', 'production')
spa_pipeline.add_stage('deploy', [
  Step.new(name: 'upload-cdn',    command: 'aws s3 sync dist/ s3://my-bucket/',
           timeout_seconds: 180, allow_failure: false),
  Step.new(name: 'invalidate-cf', command: 'aws cloudfront create-invalidation --paths "/*"',
           timeout_seconds: 60,  allow_failure: true)
])
spa_pipeline.artifact_paths << 'dist/'

# --- Team B: API service — adds extra security scan stage ---
api_pipeline = registry.build('node-base')
api_pipeline.name  = 'API Service — CI Pipeline'
api_pipeline.timeout_minutes = 60
api_pipeline.add_env('DATABASE_URL', '$SECRET_DB_URL')
api_pipeline.add_stage('security', [
  Step.new(name: 'audit',   command: 'npm audit --audit-level=high',
           timeout_seconds: 120, allow_failure: false),
  Step.new(name: 'sast',    command: 'npx semgrep --config=auto src/',
           timeout_seconds: 240, allow_failure: true)
])

# --- Display ---
puts '=== Frontend SPA Pipeline ==='
spa_pipeline.display

puts "\n=== API Service Pipeline ==="
api_pipeline.display

# --- Verify base template was not mutated ---
puts "\n=== Base Template Integrity ==="
puts "Stage count still 2 (build + test): #{node_base.stages.size == 2}"
puts "No 'deploy' stage in base: #{!node_base.stages.key?('deploy')}"
puts "No 'DATABASE_URL' env in base: #{node_base.env_vars.none? { |e| e.key == 'DATABASE_URL' }}"
puts "\nAvailable templates: #{registry.templates.inspect}"
```

---

## When To Use

**Use the Prototype pattern when:**

- **You want to avoid coupling to concrete classes.** Your code should work with objects through an interface, and you do not want (or are not able) to depend on concrete implementations at compile time. The pattern lets you produce copies of an object using only the prototype interface.

- **Reducing subclass explosion.** Instead of creating a hierarchy of factory subclasses just to instantiate objects with various configurations, you can create a set of pre-built prototypes with different configurations and clone the appropriate one.

- **Expensive object initialisation.** When creating a new object is computationally expensive (e.g., requires a database query, file I/O, or complex calculation), cloning a pre-built instance is far cheaper than re-running the initialisation logic.

- **Objects with many optional configuration fields.** Rather than providing a dozen constructors or a builder per variant, you define a few sensible prototypes and let clients clone-and-adjust.

- **Runtime composition is needed.** The set of available classes is only known at runtime (e.g., loaded from plug-ins). A registry populated at startup with prototype instances handles this elegantly.

---

## Pros & Cons

### Pros

| Benefit | Detail |
|---|---|
| **No coupling to concrete classes** | You clone objects through the prototype interface and never reference their concrete type in client code. |
| **Eliminate repeated initialisation** | Expensive setup (DB queries, file parsing, API calls) is done once on the prototype; clones are cheap. |
| **Alternative to subclassing** | Avoids factorial growth of subclass hierarchies to represent every combination of attributes. |
| **Pre-configured object palette** | A prototype registry provides a catalogue of ready-to-use object variants without complex factory logic. |
| **Runtime flexibility** | New object "types" can be introduced at runtime by registering new prototypes — no code changes required. |

### Cons

| Drawback | Detail |
|---|---|
| **Deep cloning can be complex** | Objects with circular references (A references B which references A) require careful, hand-rolled cloning logic — naive deep-copy approaches fail or infinitely recurse. |
| **Every class must implement clone** | Adding cloning support to pre-existing classes that do not expose their internal state is difficult or impossible. |
| **Hidden mutation risk** | If a shallow copy is used when a deep copy was intended, mutations to the clone silently affect the prototype — a subtle, hard-to-debug bug. |
| **Inconsistent language support** | Some languages have built-in cloning (Java's `Cloneable`, PHP's `__clone`, Python's `copy` module) but they behave inconsistently regarding depth, requiring developer vigilance. |

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Abstract Factory** | Abstract Factory classes are often implemented using a set of Prototype objects. The factory clones a prototype when asked to create an object, rather than instantiating a concrete class. |
| **Command** | The Command pattern can use Prototype to save a history of commands. A copy of the command object (with its state at the time of execution) can be stored for undo operations. |
| **Composite** | Designs that use Composite heavily often benefit from Prototype, because cloning a complex tree structure (instead of reconstructing it) is usually simpler. |
| **Decorator** | Designs that use Decorator can use Prototype to clone a fully-decorated object as a starting point, rather than layering decorators again from scratch. |
| **Memento** | Prototype can be simpler than Memento for saving state, as long as the object's state does not need to be decoupled from the object itself. When the state snapshot needs to be opaque, Memento is the better choice. |

---

## Sources

- https://refactoring.guru/design-patterns/prototype
- https://sourcemaking.com/design_patterns/prototype
