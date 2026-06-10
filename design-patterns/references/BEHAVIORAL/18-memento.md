# Memento Pattern

**Category:** Behavioral
**Also known as:** Snapshot, Token

---

## Intent

The Memento pattern lets you save and restore the previous state of an object without revealing the details of its implementation. It externalizes an object's internal state so it can be restored later, all while keeping that state encapsulated and hidden from the outside world.

---

## Problem It Solves

Imagine you are building a text editor with an undo feature. To roll back operations, you need to capture the editor's state before each change. The naive approach is to read all the editor's fields directly and copy them somewhere. However, this tightly couples the undo logic to the editor's private internals. Every time the editor changes its fields, the undo code must change too — a classic encapsulation violation.

The core tension:

- You **must** snapshot the object's state to support undo/redo.
- You **must not** expose private implementation details to outside code.
- Direct field access breaks encapsulation and creates tight coupling.
- Serializing to a generic format (e.g., JSON dict) loses type safety and leaks structure.

---

## Solution

Delegate state-saving responsibility **to the object itself**:

1. The **Originator** knows its own internal state and is the only class that can produce a valid snapshot (a **Memento**).
2. The **Memento** stores a copy of the Originator's state. Its data is opaque to everyone except the Originator — other classes can hold it but not read it.
3. The **Caretaker** manages the history of Mementos (e.g., a stack). It knows *when* to save or restore state, but *never* inspects the contents of a Memento.

Mementos are treated as **immutable value objects** — once created, their contents never change.

---

## Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client / Caretaker                      │
│                                                                 │
│   history: Memento[]                                            │
│                                                                 │
│   save()    ──────────────────────────────────────────────────► │
│   undo()    ◄────────────────────────────────────────────────── │
└────────────────────┬────────────────────────────────────────────┘
                     │  uses
                     ▼
        ┌────────────────────────┐
        │       Originator       │
        │                        │
        │  - state               │
        │                        │
        │  + save(): Memento     │──────────────────────┐
        │  + restore(m: Memento) │◄─────────────────────┤
        └────────────────────────┘                      │ creates /
                                                        │ reads
                                              ┌─────────▼──────────┐
                                              │       Memento       │
                                              │                     │
                                              │  - state  (private) │
                                              │                     │
                                              │  + getState()       │
                                              │    (only Originator │
                                              │     can call this)  │
                                              └─────────────────────┘

Flow:
  Caretaker calls originator.save()  → Originator returns new Memento
  Caretaker stores Memento in stack
  On undo: Caretaker pops Memento, calls originator.restore(memento)
  Originator reads Memento's state and applies it to itself
```

---

## Participants

| Role | Responsibility |
|---|---|
| **Originator** | The object whose state needs snapshotting. Creates Mementos from its current state; restores its state from a given Memento. |
| **Memento** | A value object that stores a snapshot of the Originator's state. Exposes a narrow interface to the Caretaker (metadata only) and a wide interface to the Originator (full state access). |
| **Caretaker** | Manages the history of Mementos. Decides when to save and when to restore. Never reads or modifies the Memento's contents. |

---

## How It Works

1. **Before a risky operation**, the Caretaker asks the Originator to save its state: `memento = originator.save()`.
2. The **Originator** creates a new Memento, copies its current internal state into it, and returns it.
3. The **Caretaker** pushes the Memento onto its history stack.
4. The **operation executes**; the Originator's state may now change.
5. **To undo**, the Caretaker pops the most recent Memento from the stack.
6. The Caretaker passes the Memento back to the Originator: `originator.restore(memento)`.
7. The **Originator** reads the state from the Memento and applies it to itself — state is rolled back.
8. The Memento object is discarded after restoration (or kept for redo).

Key invariant: **The Caretaker never inspects or modifies the Memento's payload.** It only moves Mementos around.

---

## Code Examples

### Python

```python
"""
Real-world example: A drawing canvas application with full undo/redo support.
The canvas can have shapes added or removed, and the user can undo any number
of changes to revert to a previous canvas state.
"""

from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Domain objects stored inside the canvas
# ---------------------------------------------------------------------------

@dataclass
class Shape:
    kind: str        # 'rect', 'circle', 'line'
    x: float
    y: float
    color: str
    label: str = ""

    def __str__(self) -> str:
        return f"{self.kind}({self.label or self.color} @{self.x},{self.y})"


# ---------------------------------------------------------------------------
# Memento — opaque snapshot; only Canvas (Originator) should read .state
# ---------------------------------------------------------------------------

class CanvasMemento:
    """Immutable snapshot of Canvas state.

    The Caretaker can read the description (metadata) but must not
    access or mutate _state directly.
    """

    def __init__(self, shapes: List[Shape], description: str) -> None:
        # Deep-copy so later mutations to the canvas cannot affect this snapshot
        self._state: List[Shape] = deepcopy(shapes)
        self._description: str = description

    # Wide interface — only used by Canvas (Originator)
    def _get_state(self) -> List[Shape]:
        return deepcopy(self._state)

    # Narrow interface — safe for the Caretaker to call
    @property
    def description(self) -> str:
        return self._description

    def __repr__(self) -> str:
        return f"Memento({self._description!r}, shapes={len(self._state)})"


# ---------------------------------------------------------------------------
# Originator — the Canvas itself
# ---------------------------------------------------------------------------

class Canvas:
    """Drawing canvas that acts as the Originator."""

    def __init__(self) -> None:
        self._shapes: List[Shape] = []

    # --- Mutation operations ---

    def add_shape(self, shape: Shape) -> None:
        self._shapes.append(shape)
        print(f"  Canvas: added {shape}")

    def remove_last_shape(self) -> Optional[Shape]:
        if not self._shapes:
            print("  Canvas: nothing to remove")
            return None
        removed = self._shapes.pop()
        print(f"  Canvas: removed {removed}")
        return removed

    def move_shape(self, label: str, dx: float, dy: float) -> None:
        for shape in self._shapes:
            if shape.label == label:
                shape.x += dx
                shape.y += dy
                print(f"  Canvas: moved '{label}' by ({dx}, {dy})")
                return
        print(f"  Canvas: shape '{label}' not found")

    # --- Memento interface ---

    def save(self, description: str = "") -> CanvasMemento:
        """Create a snapshot of the current canvas state."""
        return CanvasMemento(self._shapes, description)

    def restore(self, memento: CanvasMemento) -> None:
        """Restore the canvas to the state captured in the given memento."""
        # Access the wide interface — Canvas is the only class that does this
        self._shapes = memento._get_state()
        print(f"  Canvas: restored to '{memento.description}'")

    def render(self) -> None:
        print(f"  Canvas [{len(self._shapes)} shapes]: "
              + ", ".join(str(s) for s in self._shapes) if self._shapes else "  Canvas: (empty)")


# ---------------------------------------------------------------------------
# Caretaker — manages the undo/redo stacks
# ---------------------------------------------------------------------------

class DrawingHistory:
    """Caretaker that provides undo/redo for a Canvas."""

    def __init__(self, canvas: Canvas) -> None:
        self._canvas = canvas
        self._undo_stack: List[CanvasMemento] = []
        self._redo_stack: List[CanvasMemento] = []

    def checkpoint(self, description: str = "") -> None:
        """Save the current canvas state before a change."""
        m = self._canvas.save(description)
        self._undo_stack.append(m)
        # A new action clears the redo stack
        self._redo_stack.clear()
        print(f"[History] checkpoint saved: {m}")

    def undo(self) -> bool:
        if not self._undo_stack:
            print("[History] nothing to undo")
            return False
        # Save current state for redo
        self._redo_stack.append(self._canvas.save("(redo point)"))
        memento = self._undo_stack.pop()
        self._canvas.restore(memento)
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            print("[History] nothing to redo")
            return False
        self._undo_stack.append(self._canvas.save("(undo point)"))
        memento = self._redo_stack.pop()
        self._canvas.restore(memento)
        return True

    def print_history(self) -> None:
        print(f"[History] undo stack ({len(self._undo_stack)}): "
              + str([m.description for m in self._undo_stack]))
        print(f"[History] redo stack ({len(self._redo_stack)}): "
              + str([m.description for m in self._redo_stack]))


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    canvas = Canvas()
    history = DrawingHistory(canvas)

    print("\n--- Add first shape ---")
    history.checkpoint("before adding red circle")
    canvas.add_shape(Shape("circle", 10, 20, "red", "sun"))

    print("\n--- Add second shape ---")
    history.checkpoint("before adding blue rect")
    canvas.add_shape(Shape("rect", 50, 60, "blue", "sky"))

    print("\n--- Move sun ---")
    history.checkpoint("before moving sun")
    canvas.move_shape("sun", 5, -3)

    print("\n--- Current state ---")
    canvas.render()
    history.print_history()

    print("\n--- Undo move ---")
    history.undo()
    canvas.render()

    print("\n--- Undo add blue rect ---")
    history.undo()
    canvas.render()

    print("\n--- Redo add blue rect ---")
    history.redo()
    canvas.render()

    print("\n--- Undo all the way back ---")
    history.undo()
    history.undo()
    canvas.render()
```

---

### Java

```java
/**
 * Real-world example: A rich-text editor with undo/redo support.
 *
 * The editor tracks text content, cursor position, and formatting state.
 * The Memento is implemented as a nested class so only the Originator
 * (TextEditor) can access its internals — idiomatic Java encapsulation.
 */

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Objects;

// ─────────────────────────────────────────────────────────────────────────────
// Originator: TextEditor
// ─────────────────────────────────────────────────────────────────────────────
public class TextEditor {

    private StringBuilder content;
    private int cursorPosition;
    private boolean boldActive;
    private boolean italicActive;

    public TextEditor() {
        this.content = new StringBuilder();
        this.cursorPosition = 0;
        this.boldActive = false;
        this.italicActive = false;
    }

    // ── Editing operations ───────────────────────────────────────────────────

    public void type(String text) {
        content.insert(cursorPosition, text);
        cursorPosition += text.length();
        System.out.printf("  Editor: typed \"%s\"%n", text);
    }

    public void moveCursor(int position) {
        this.cursorPosition = Math.max(0, Math.min(position, content.length()));
        System.out.printf("  Editor: cursor at %d%n", cursorPosition);
    }

    public void deleteBack(int count) {
        int start = Math.max(0, cursorPosition - count);
        content.delete(start, cursorPosition);
        cursorPosition = start;
        System.out.printf("  Editor: deleted %d char(s)%n", count);
    }

    public void toggleBold() {
        boldActive = !boldActive;
        System.out.printf("  Editor: bold %s%n", boldActive ? "ON" : "OFF");
    }

    public void toggleItalic() {
        italicActive = !italicActive;
        System.out.printf("  Editor: italic %s%n", italicActive ? "ON" : "OFF");
    }

    // ── Memento interface ────────────────────────────────────────────────────

    /** Save current state as an opaque snapshot. */
    public EditorMemento save(String label) {
        return new EditorMemento(
                content.toString(),
                cursorPosition,
                boldActive,
                italicActive,
                label
        );
    }

    /** Restore state from a snapshot. */
    public void restore(EditorMemento memento) {
        this.content       = new StringBuilder(memento.savedContent);
        this.cursorPosition = memento.savedCursor;
        this.boldActive     = memento.savedBold;
        this.italicActive   = memento.savedItalic;
        System.out.printf("  Editor: restored to [%s]%n", memento.getLabel());
    }

    public void printState() {
        System.out.printf("  Editor state: \"%s\" | cursor=%d | bold=%b | italic=%b%n",
                content, cursorPosition, boldActive, italicActive);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Nested Memento class — private fields accessible only to TextEditor
    // ─────────────────────────────────────────────────────────────────────────
    public static final class EditorMemento {
        // Package-private fields so TextEditor (same file) can read them;
        // external classes get only the label via the public getter.
        private final String savedContent;
        private final int    savedCursor;
        private final boolean savedBold;
        private final boolean savedItalic;
        private final String label;

        private EditorMemento(String content, int cursor,
                              boolean bold, boolean italic, String label) {
            this.savedContent = Objects.requireNonNull(content);
            this.savedCursor  = cursor;
            this.savedBold    = bold;
            this.savedItalic  = italic;
            this.label        = label;
        }

        /** Narrow interface available to the Caretaker. */
        public String getLabel() { return label; }

        @Override
        public String toString() {
            return String.format("Memento[%s, chars=%d]", label, savedContent.length());
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Caretaker: EditorHistory
    // ─────────────────────────────────────────────────────────────────────────
    public static class EditorHistory {
        private final TextEditor editor;
        private final Deque<EditorMemento> undoStack = new ArrayDeque<>();
        private final Deque<EditorMemento> redoStack = new ArrayDeque<>();

        public EditorHistory(TextEditor editor) {
            this.editor = editor;
        }

        public void checkpoint(String label) {
            EditorMemento m = editor.save(label);
            undoStack.push(m);
            redoStack.clear();
            System.out.printf("[History] checkpoint: %s%n", m);
        }

        public boolean undo() {
            if (undoStack.isEmpty()) {
                System.out.println("[History] nothing to undo");
                return false;
            }
            redoStack.push(editor.save("(redo point)"));
            editor.restore(undoStack.pop());
            return true;
        }

        public boolean redo() {
            if (redoStack.isEmpty()) {
                System.out.println("[History] nothing to redo");
                return false;
            }
            undoStack.push(editor.save("(undo point)"));
            editor.restore(redoStack.pop());
            return true;
        }

        public void printStacks() {
            System.out.printf("[History] undo=%d, redo=%d%n",
                    undoStack.size(), redoStack.size());
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Demo
    // ─────────────────────────────────────────────────────────────────────────
    public static void main(String[] args) {
        TextEditor editor = new TextEditor();
        EditorHistory history = new EditorHistory(editor);

        System.out.println("\n--- Type 'Hello' ---");
        history.checkpoint("before Hello");
        editor.type("Hello");

        System.out.println("\n--- Type ', World' ---");
        history.checkpoint("before , World");
        editor.type(", World");

        System.out.println("\n--- Enable bold, type '!' ---");
        history.checkpoint("before bold !");
        editor.toggleBold();
        editor.type("!");

        System.out.println("\n--- Current state ---");
        editor.printState();
        history.printStacks();

        System.out.println("\n--- Undo bold ---");
        history.undo();
        editor.printState();

        System.out.println("\n--- Undo ', World' ---");
        history.undo();
        editor.printState();

        System.out.println("\n--- Redo ---");
        history.redo();
        editor.printState();
    }
}
```

---

### C++

```cpp
/**
 * Real-world example: Game character state with save/load checkpoints.
 *
 * A player character accumulates health, mana, experience, and inventory.
 * The game saves a checkpoint before entering a boss fight. If the player
 * dies, the game restores the last checkpoint automatically.
 */

#include <iostream>
#include <memory>
#include <stack>
#include <string>
#include <vector>
#include <sstream>

// ─────────────────────────────────────────────────────────────────────────────
// Memento — value object; only Character should construct/read it
// ─────────────────────────────────────────────────────────────────────────────
class CharacterMemento {
public:
    // Metadata accessible to the Caretaker
    const std::string& label() const { return label_; }

    // Only Character should call these (friend relationship enforces this)
    int         getHealth()      const { return health_; }
    int         getMana()        const { return mana_; }
    int         getExperience()  const { return experience_; }
    const std::vector<std::string>& getInventory() const { return inventory_; }

private:
    // Only Character can construct a Memento
    friend class Character;

    CharacterMemento(int hp, int mp, int xp,
                     std::vector<std::string> inv, std::string lbl)
        : health_(hp), mana_(mp), experience_(xp),
          inventory_(std::move(inv)), label_(std::move(lbl)) {}

    int health_;
    int mana_;
    int experience_;
    std::vector<std::string> inventory_;
    std::string label_;
};

// ─────────────────────────────────────────────────────────────────────────────
// Originator: Character
// ─────────────────────────────────────────────────────────────────────────────
class Character {
public:
    Character(const std::string& name, int hp, int mp)
        : name_(name), health_(hp), maxHealth_(hp),
          mana_(mp), experience_(0) {}

    // ── Game actions ──────────────────────────────────────────────────────────

    void takeDamage(int dmg) {
        health_ = std::max(0, health_ - dmg);
        std::cout << "  " << name_ << ": took " << dmg << " damage, HP=" << health_ << "\n";
    }

    void heal(int amount) {
        health_ = std::min(maxHealth_, health_ + amount);
        std::cout << "  " << name_ << ": healed " << amount << " HP, HP=" << health_ << "\n";
    }

    void spendMana(int amount) {
        mana_ = std::max(0, mana_ - amount);
        std::cout << "  " << name_ << ": spent " << amount << " mana, MP=" << mana_ << "\n";
    }

    void gainExperience(int xp) {
        experience_ += xp;
        std::cout << "  " << name_ << ": +" << xp << " XP, total=" << experience_ << "\n";
    }

    void pickUpItem(const std::string& item) {
        inventory_.push_back(item);
        std::cout << "  " << name_ << ": picked up '" << item << "'\n";
    }

    bool isAlive() const { return health_ > 0; }

    // ── Memento interface ─────────────────────────────────────────────────────

    std::shared_ptr<CharacterMemento> save(const std::string& label) const {
        // Use private constructor via friend
        return std::shared_ptr<CharacterMemento>(
            new CharacterMemento(health_, mana_, experience_, inventory_, label));
    }

    void restore(const std::shared_ptr<CharacterMemento>& memento) {
        health_     = memento->getHealth();
        mana_       = memento->getMana();
        experience_ = memento->getExperience();
        inventory_  = memento->getInventory();
        std::cout << "  " << name_ << ": restored to checkpoint '" << memento->label() << "'\n";
    }

    void printStatus() const {
        std::ostringstream inv;
        for (const auto& item : inventory_) inv << item << " ";
        std::cout << "  [" << name_ << "] HP=" << health_ << "/" << maxHealth_
                  << " MP=" << mana_ << " XP=" << experience_
                  << " Inventory: [" << inv.str() << "]\n";
    }

    const std::string& name() const { return name_; }

private:
    std::string name_;
    int health_;
    int maxHealth_;
    int mana_;
    int experience_;
    std::vector<std::string> inventory_;
};

// ─────────────────────────────────────────────────────────────────────────────
// Caretaker: SaveManager
// ─────────────────────────────────────────────────────────────────────────────
class SaveManager {
public:
    explicit SaveManager(Character& character) : character_(character) {}

    void save(const std::string& label) {
        auto m = character_.save(label);
        checkpoints_.push(m);
        std::cout << "[SaveManager] checkpoint saved: '" << label << "'\n";
    }

    bool loadLast() {
        if (checkpoints_.empty()) {
            std::cout << "[SaveManager] no checkpoints available\n";
            return false;
        }
        character_.restore(checkpoints_.top());
        checkpoints_.pop();
        return true;
    }

    std::size_t checkpointCount() const { return checkpoints_.size(); }

private:
    Character& character_;
    std::stack<std::shared_ptr<CharacterMemento>> checkpoints_;
};

// ─────────────────────────────────────────────────────────────────────────────
// Demo
// ─────────────────────────────────────────────────────────────────────────────
int main() {
    Character hero("Aragorn", 100, 50);
    SaveManager saves(hero);

    std::cout << "\n--- Start of dungeon ---\n";
    hero.pickUpItem("Torch");
    hero.pickUpItem("Health Potion");
    saves.save("dungeon-entrance");
    hero.printStatus();

    std::cout << "\n--- Fight goblins ---\n";
    hero.takeDamage(15);
    hero.gainExperience(120);
    hero.pickUpItem("Rusty Sword");
    saves.save("after-goblins");
    hero.printStatus();

    std::cout << "\n--- Boss fight (risky!) ---\n";
    saves.save("before-boss");
    hero.spendMana(30);
    hero.takeDamage(80);  // ouch
    hero.printStatus();

    if (!hero.isAlive() || hero.name() == "Aragorn") {  // demo trigger
        std::cout << "\n--- Hero defeated! Reloading last checkpoint ---\n";
        saves.loadLast();
        hero.printStatus();
    }

    std::cout << "\n--- Checkpoints remaining: " << saves.checkpointCount() << " ---\n";
    return 0;
}
```

---

### C#

```csharp
/**
 * Real-world example: A configuration editor for an application.
 *
 * Users can edit network, display, and audio settings. Each change is
 * checkpointed so the user can revert to a previous configuration via
 * an undo operation or "restore defaults" flow.
 */

using System;
using System.Collections.Generic;
using System.Text.Json;

namespace MementoPattern
{
    // ─────────────────────────────────────────────────────────────────────────
    // State data transferred inside the Memento (a value record)
    // ─────────────────────────────────────────────────────────────────────────
    internal sealed record ConfigSnapshot(
        string Host,
        int Port,
        int DisplayWidth,
        int DisplayHeight,
        bool FullScreen,
        int AudioVolume,
        bool AudioMuted
    );

    // ─────────────────────────────────────────────────────────────────────────
    // Memento — opaque to everything except ConfigEditor
    // ─────────────────────────────────────────────────────────────────────────
    public sealed class ConfigMemento
    {
        // Internal state is hidden from the Caretaker
        internal ConfigSnapshot Snapshot { get; }

        // Narrow public interface for the Caretaker
        public string Label { get; }
        public DateTime SavedAt { get; }

        internal ConfigMemento(ConfigSnapshot snapshot, string label)
        {
            Snapshot = snapshot;
            Label    = label;
            SavedAt  = DateTime.UtcNow;
        }

        public override string ToString() =>
            $"Memento[{Label}, saved {SavedAt:HH:mm:ss}]";
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Originator: ConfigEditor
    // ─────────────────────────────────────────────────────────────────────────
    public class ConfigEditor
    {
        // Network
        public string Host { get; private set; } = "localhost";
        public int    Port { get; private set; } = 8080;

        // Display
        public int  DisplayWidth  { get; private set; } = 1920;
        public int  DisplayHeight { get; private set; } = 1080;
        public bool FullScreen    { get; private set; } = false;

        // Audio
        public int  AudioVolume { get; private set; } = 75;
        public bool AudioMuted  { get; private set; } = false;

        // ── Setters ───────────────────────────────────────────────────────────

        public void SetNetwork(string host, int port)
        {
            Host = host;
            Port = port;
            Console.WriteLine($"  Config: network set to {host}:{port}");
        }

        public void SetDisplay(int width, int height, bool fullScreen)
        {
            DisplayWidth  = width;
            DisplayHeight = height;
            FullScreen    = fullScreen;
            Console.WriteLine($"  Config: display {width}x{height}, fullscreen={fullScreen}");
        }

        public void SetAudio(int volume, bool muted)
        {
            AudioVolume = volume;
            AudioMuted  = muted;
            Console.WriteLine($"  Config: audio volume={volume}, muted={muted}");
        }

        // ── Memento interface ─────────────────────────────────────────────────

        public ConfigMemento Save(string label)
        {
            var snapshot = new ConfigSnapshot(
                Host, Port, DisplayWidth, DisplayHeight, FullScreen, AudioVolume, AudioMuted);
            return new ConfigMemento(snapshot, label);
        }

        public void Restore(ConfigMemento memento)
        {
            var s = memento.Snapshot;   // internal access
            Host          = s.Host;
            Port          = s.Port;
            DisplayWidth  = s.DisplayWidth;
            DisplayHeight = s.DisplayHeight;
            FullScreen    = s.FullScreen;
            AudioVolume   = s.AudioVolume;
            AudioMuted    = s.AudioMuted;
            Console.WriteLine($"  Config: restored to [{memento.Label}]");
        }

        public void Print()
        {
            Console.WriteLine(
                $"  Config => Network: {Host}:{Port} | " +
                $"Display: {DisplayWidth}x{DisplayHeight} FS={FullScreen} | " +
                $"Audio: vol={AudioVolume} muted={AudioMuted}");
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Caretaker: ConfigHistory
    // ─────────────────────────────────────────────────────────────────────────
    public class ConfigHistory
    {
        private readonly ConfigEditor _editor;
        private readonly Stack<ConfigMemento> _undoStack = new();
        private readonly Stack<ConfigMemento> _redoStack = new();

        public ConfigHistory(ConfigEditor editor) => _editor = editor;

        public void Checkpoint(string label)
        {
            var m = _editor.Save(label);
            _undoStack.Push(m);
            _redoStack.Clear();
            Console.WriteLine($"[History] Checkpoint: {m}");
        }

        public bool Undo()
        {
            if (_undoStack.Count == 0) { Console.WriteLine("[History] Nothing to undo"); return false; }
            _redoStack.Push(_editor.Save("(redo point)"));
            _editor.Restore(_undoStack.Pop());
            return true;
        }

        public bool Redo()
        {
            if (_redoStack.Count == 0) { Console.WriteLine("[History] Nothing to redo"); return false; }
            _undoStack.Push(_editor.Save("(undo point)"));
            _editor.Restore(_redoStack.Pop());
            return true;
        }

        public void PrintStacks() =>
            Console.WriteLine($"[History] undo={_undoStack.Count}, redo={_redoStack.Count}");
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Demo
    // ─────────────────────────────────────────────────────────────────────────
    class Program
    {
        static void Main()
        {
            var editor  = new ConfigEditor();
            var history = new ConfigHistory(editor);

            Console.WriteLine("\n--- Change network settings ---");
            history.Checkpoint("default config");
            editor.SetNetwork("prod.example.com", 443);

            Console.WriteLine("\n--- Change display to 4K fullscreen ---");
            history.Checkpoint("after network change");
            editor.SetDisplay(3840, 2160, true);

            Console.WriteLine("\n--- Mute audio ---");
            history.Checkpoint("after display change");
            editor.SetAudio(0, true);

            Console.WriteLine("\n--- Current state ---");
            editor.Print();
            history.PrintStacks();

            Console.WriteLine("\n--- Undo mute ---");
            history.Undo();
            editor.Print();

            Console.WriteLine("\n--- Undo display change ---");
            history.Undo();
            editor.Print();

            Console.WriteLine("\n--- Redo display change ---");
            history.Redo();
            editor.Print();
        }
    }
}
```

---

### TypeScript

```typescript
/**
 * Real-world example: A form wizard with multi-step undo support.
 *
 * A user fills out a multi-step registration form. At each step they can
 * go "Back" to undo their most recent changes without losing progress
 * made in earlier steps.
 */

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface FormState {
  // Step 1 — personal info
  firstName: string;
  lastName: string;
  email: string;
  // Step 2 — address
  street: string;
  city: string;
  country: string;
  // Step 3 — preferences
  newsletter: boolean;
  plan: "free" | "pro" | "enterprise";
}

// ─────────────────────────────────────────────────────────────────────────────
// Memento — opaque snapshot; symbol key hides state from external code
// ─────────────────────────────────────────────────────────────────────────────

const STATE_KEY = Symbol("mementoState");

class FormMemento {
  private readonly [STATE_KEY]: Readonly<FormState>;
  public readonly label: string;
  public readonly savedAt: Date;

  /** Only FormWizard should call this constructor. */
  constructor(state: FormState, label: string) {
    // Freeze so the snapshot is truly immutable
    this[STATE_KEY] = Object.freeze({ ...state });
    this.label = label;
    this.savedAt = new Date();
  }

  /** Package-private accessor — TypeScript cannot enforce this at runtime,
   *  but by convention only FormWizard (originator) calls it. */
  _getState(): Readonly<FormState> {
    return this[STATE_KEY];
  }

  toString(): string {
    return `Memento[${this.label} @ ${this.savedAt.toISOString()}]`;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Originator: FormWizard
// ─────────────────────────────────────────────────────────────────────────────

class FormWizard {
  private state: FormState = {
    firstName: "",
    lastName: "",
    email: "",
    street: "",
    city: "",
    country: "",
    newsletter: false,
    plan: "free",
  };

  // ── Field setters ──────────────────────────────────────────────────────────

  fillPersonalInfo(firstName: string, lastName: string, email: string): void {
    this.state = { ...this.state, firstName, lastName, email };
    console.log(`  Form: personal info → ${firstName} ${lastName} <${email}>`);
  }

  fillAddress(street: string, city: string, country: string): void {
    this.state = { ...this.state, street, city, country };
    console.log(`  Form: address → ${street}, ${city}, ${country}`);
  }

  fillPreferences(newsletter: boolean, plan: FormState["plan"]): void {
    this.state = { ...this.state, newsletter, plan };
    console.log(`  Form: preferences → newsletter=${newsletter}, plan=${plan}`);
  }

  // ── Memento interface ──────────────────────────────────────────────────────

  save(label: string): FormMemento {
    return new FormMemento(this.state, label);
  }

  restore(memento: FormMemento): void {
    // Access wide interface — only the originator does this
    this.state = { ...memento._getState() };
    console.log(`  Form: restored to [${memento.label}]`);
  }

  printState(): void {
    console.log("  Form state:", JSON.stringify(this.state, null, 2));
  }

  getState(): Readonly<FormState> {
    return Object.freeze({ ...this.state });
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Caretaker: FormHistory
// ─────────────────────────────────────────────────────────────────────────────

class FormHistory {
  private undoStack: FormMemento[] = [];
  private redoStack: FormMemento[] = [];

  constructor(private readonly wizard: FormWizard) {}

  checkpoint(label: string): void {
    const m = this.wizard.save(label);
    this.undoStack.push(m);
    this.redoStack = [];
    console.log(`[History] checkpoint: ${m}`);
  }

  undo(): boolean {
    if (this.undoStack.length === 0) {
      console.log("[History] nothing to undo");
      return false;
    }
    this.redoStack.push(this.wizard.save("(redo point)"));
    const m = this.undoStack.pop()!;
    this.wizard.restore(m);
    return true;
  }

  redo(): boolean {
    if (this.redoStack.length === 0) {
      console.log("[History] nothing to redo");
      return false;
    }
    this.undoStack.push(this.wizard.save("(undo point)"));
    const m = this.redoStack.pop()!;
    this.wizard.restore(m);
    return true;
  }

  get stackSizes() {
    return { undo: this.undoStack.length, redo: this.redoStack.length };
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Demo
// ─────────────────────────────────────────────────────────────────────────────

const wizard  = new FormWizard();
const history = new FormHistory(wizard);

console.log("\n--- Step 1: Personal info ---");
history.checkpoint("blank form");
wizard.fillPersonalInfo("Alice", "Smith", "alice@example.com");

console.log("\n--- Step 2: Address ---");
history.checkpoint("after personal info");
wizard.fillAddress("123 Maple St", "Springfield", "US");

console.log("\n--- Step 3: Preferences ---");
history.checkpoint("after address");
wizard.fillPreferences(true, "pro");

console.log("\n--- User goes back (undo preferences) ---");
history.undo();
wizard.printState();

console.log("\n--- User goes back again (undo address) ---");
history.undo();
wizard.printState();

console.log("\n--- User re-fills address differently ---");
history.checkpoint("after second undo");
wizard.fillAddress("99 Oak Ave", "Shelbyville", "US");

console.log("\n--- Stack sizes:", history.stackSizes);
wizard.printState();
```

---

### Go

```go
// Real-world example: A pipeline builder where users construct a data
// processing pipeline step by step and can undo any configuration change.

package main

import (
	"fmt"
	"strings"
)

// ─────────────────────────────────────────────────────────────────────────────
// Memento — unexported struct; only Pipeline (same package) constructs it
// ─────────────────────────────────────────────────────────────────────────────

type pipelineState struct {
	source      string
	steps       []string
	destination string
	maxWorkers  int
	retryCount  int
}

// PipelineMemento is the exported token the Caretaker holds.
// Its internal state is hidden behind an unexported field.
type PipelineMemento struct {
	state pipelineState // unexported — Caretaker cannot read this
	label string
}

// Label is the only thing the Caretaker may read.
func (m *PipelineMemento) Label() string { return m.label }

func (m *PipelineMemento) String() string {
	return fmt.Sprintf("Memento[%s, steps=%d]", m.label, len(m.state.steps))
}

// ─────────────────────────────────────────────────────────────────────────────
// Originator: Pipeline
// ─────────────────────────────────────────────────────────────────────────────

type Pipeline struct {
	source      string
	steps       []string
	destination string
	maxWorkers  int
	retryCount  int
}

func NewPipeline() *Pipeline {
	return &Pipeline{maxWorkers: 4, retryCount: 3}
}

// ── Configuration methods ─────────────────────────────────────────────────────

func (p *Pipeline) SetSource(source string) {
	p.source = source
	fmt.Printf("  Pipeline: source = %q\n", source)
}

func (p *Pipeline) AddStep(step string) {
	p.steps = append(p.steps, step)
	fmt.Printf("  Pipeline: added step %q\n", step)
}

func (p *Pipeline) RemoveLastStep() {
	if len(p.steps) == 0 {
		fmt.Println("  Pipeline: no steps to remove")
		return
	}
	removed := p.steps[len(p.steps)-1]
	p.steps = p.steps[:len(p.steps)-1]
	fmt.Printf("  Pipeline: removed step %q\n", removed)
}

func (p *Pipeline) SetDestination(dest string) {
	p.destination = dest
	fmt.Printf("  Pipeline: destination = %q\n", dest)
}

func (p *Pipeline) SetWorkers(n int) {
	p.maxWorkers = n
	fmt.Printf("  Pipeline: maxWorkers = %d\n", n)
}

func (p *Pipeline) SetRetry(n int) {
	p.retryCount = n
	fmt.Printf("  Pipeline: retryCount = %d\n", n)
}

// ── Memento interface ─────────────────────────────────────────────────────────

// Save creates a snapshot of the pipeline's current configuration.
func (p *Pipeline) Save(label string) *PipelineMemento {
	// Copy the slice so future mutations do not affect the snapshot
	stepsCopy := make([]string, len(p.steps))
	copy(stepsCopy, p.steps)

	return &PipelineMemento{
		state: pipelineState{
			source:      p.source,
			steps:       stepsCopy,
			destination: p.destination,
			maxWorkers:  p.maxWorkers,
			retryCount:  p.retryCount,
		},
		label: label,
	}
}

// Restore applies the snapshot back to the pipeline.
func (p *Pipeline) Restore(m *PipelineMemento) {
	s := m.state // direct struct access — same package
	stepsCopy := make([]string, len(s.steps))
	copy(stepsCopy, s.steps)

	p.source      = s.source
	p.steps       = stepsCopy
	p.destination = s.destination
	p.maxWorkers  = s.maxWorkers
	p.retryCount  = s.retryCount

	fmt.Printf("  Pipeline: restored to [%s]\n", m.label)
}

func (p *Pipeline) Print() {
	fmt.Printf("  Pipeline => src=%q  steps=[%s]  dst=%q  workers=%d  retry=%d\n",
		p.source, strings.Join(p.steps, " → "), p.destination,
		p.maxWorkers, p.retryCount)
}

// ─────────────────────────────────────────────────────────────────────────────
// Caretaker: PipelineHistory
// ─────────────────────────────────────────────────────────────────────────────

type PipelineHistory struct {
	pipeline  *Pipeline
	undoStack []*PipelineMemento
	redoStack []*PipelineMemento
}

func NewPipelineHistory(p *Pipeline) *PipelineHistory {
	return &PipelineHistory{pipeline: p}
}

func (h *PipelineHistory) Checkpoint(label string) {
	m := h.pipeline.Save(label)
	h.undoStack = append(h.undoStack, m)
	h.redoStack = nil // clear redo on new action
	fmt.Printf("[History] checkpoint: %s\n", m)
}

func (h *PipelineHistory) Undo() bool {
	if len(h.undoStack) == 0 {
		fmt.Println("[History] nothing to undo")
		return false
	}
	h.redoStack = append(h.redoStack, h.pipeline.Save("(redo point)"))
	last := h.undoStack[len(h.undoStack)-1]
	h.undoStack = h.undoStack[:len(h.undoStack)-1]
	h.pipeline.Restore(last)
	return true
}

func (h *PipelineHistory) Redo() bool {
	if len(h.redoStack) == 0 {
		fmt.Println("[History] nothing to redo")
		return false
	}
	h.undoStack = append(h.undoStack, h.pipeline.Save("(undo point)"))
	last := h.redoStack[len(h.redoStack)-1]
	h.redoStack = h.redoStack[:len(h.redoStack)-1]
	h.pipeline.Restore(last)
	return true
}

// ─────────────────────────────────────────────────────────────────────────────
// Demo
// ─────────────────────────────────────────────────────────────────────────────

func main() {
	pipeline := NewPipeline()
	history  := NewPipelineHistory(pipeline)

	fmt.Println("\n--- Configure source ---")
	history.Checkpoint("empty pipeline")
	pipeline.SetSource("s3://raw-events/")

	fmt.Println("\n--- Add processing steps ---")
	history.Checkpoint("source set")
	pipeline.AddStep("parse-json")
	pipeline.AddStep("filter-nulls")
	pipeline.AddStep("enrich-geo")

	fmt.Println("\n--- Set destination and tune workers ---")
	history.Checkpoint("steps added")
	pipeline.SetDestination("kafka://enriched-events")
	pipeline.SetWorkers(16)
	pipeline.SetRetry(5)

	fmt.Println("\n--- Current state ---")
	pipeline.Print()

	fmt.Println("\n--- Undo worker tuning ---")
	history.Undo()
	pipeline.Print()

	fmt.Println("\n--- Undo steps ---")
	history.Undo()
	pipeline.Print()

	fmt.Println("\n--- Redo steps ---")
	history.Redo()
	pipeline.Print()
}
```

---

### PHP

```php
<?php
/**
 * Real-world example: A shopping cart with item management and undo support.
 *
 * Users add/remove items and apply coupon codes. An undo button reverts
 * the most recent cart change — useful if a user accidentally removes an item.
 */

declare(strict_types=1);

// ─────────────────────────────────────────────────────────────────────────────
// Value objects
// ─────────────────────────────────────────────────────────────────────────────

final class CartItem
{
    public function __construct(
        public readonly string $sku,
        public readonly string $name,
        public readonly float  $price,
        public int             $quantity,
    ) {}

    public function subtotal(): float
    {
        return $this->price * $this->quantity;
    }

    public function __clone()
    {
        // Primitive properties copy fine; nothing to override here
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Memento — only ShoppingCart can construct/read it
// ─────────────────────────────────────────────────────────────────────────────

final class CartMemento
{
    /** @var CartItem[] */
    private array $items;
    private ?string $couponCode;
    private float $discountRate;
    private string $label;

    // Private constructor — only ShoppingCart calls this (via a static factory trick)
    private function __construct(
        array $items,
        ?string $couponCode,
        float $discountRate,
        string $label
    ) {
        // Deep copy items so originator mutations don't affect snapshot
        $this->items        = array_map(fn($i) => clone $i, $items);
        $this->couponCode   = $couponCode;
        $this->discountRate = $discountRate;
        $this->label        = $label;
    }

    /** Factory used only by ShoppingCart (same file, simulated package access). */
    public static function _create(
        array $items,
        ?string $couponCode,
        float $discountRate,
        string $label
    ): self {
        return new self($items, $couponCode, $discountRate, $label);
    }

    // ── Narrow interface for Caretaker ────────────────────────────────────────

    public function getLabel(): string { return $this->label; }

    public function __toString(): string
    {
        return sprintf('Memento[%s, %d items]', $this->label, count($this->items));
    }

    // ── Wide interface for ShoppingCart (Originator) ──────────────────────────

    /** @return CartItem[] */
    public function _getItems(): array        { return $this->items; }
    public function _getCouponCode(): ?string { return $this->couponCode; }
    public function _getDiscountRate(): float { return $this->discountRate; }
}

// ─────────────────────────────────────────────────────────────────────────────
// Originator: ShoppingCart
// ─────────────────────────────────────────────────────────────────────────────

class ShoppingCart
{
    /** @var CartItem[] */
    private array $items = [];
    private ?string $couponCode  = null;
    private float   $discountRate = 0.0;

    // ── Cart operations ───────────────────────────────────────────────────────

    public function addItem(CartItem $item): void
    {
        foreach ($this->items as $existing) {
            if ($existing->sku === $item->sku) {
                $existing->quantity += $item->quantity;
                echo "  Cart: increased qty of '{$item->name}' to {$existing->quantity}\n";
                return;
            }
        }
        $this->items[] = $item;
        echo "  Cart: added '{$item->name}' x{$item->quantity} @ \${$item->price}\n";
    }

    public function removeItem(string $sku): void
    {
        foreach ($this->items as $k => $item) {
            if ($item->sku === $sku) {
                echo "  Cart: removed '{$item->name}'\n";
                unset($this->items[$k]);
                $this->items = array_values($this->items);
                return;
            }
        }
        echo "  Cart: SKU '$sku' not found\n";
    }

    public function applyCoupon(string $code, float $rate): void
    {
        $this->couponCode   = $code;
        $this->discountRate = $rate;
        echo "  Cart: coupon '$code' applied ({$rate}% off)\n";
    }

    public function removeCoupon(): void
    {
        $this->couponCode   = null;
        $this->discountRate = 0.0;
        echo "  Cart: coupon removed\n";
    }

    public function total(): float
    {
        $subtotal = array_sum(array_map(fn($i) => $i->subtotal(), $this->items));
        return round($subtotal * (1 - $this->discountRate / 100), 2);
    }

    // ── Memento interface ─────────────────────────────────────────────────────

    public function save(string $label): CartMemento
    {
        return CartMemento::_create(
            $this->items,
            $this->couponCode,
            $this->discountRate,
            $label
        );
    }

    public function restore(CartMemento $memento): void
    {
        // Access wide interface — only ShoppingCart does this
        $this->items        = array_map(fn($i) => clone $i, $memento->_getItems());
        $this->couponCode   = $memento->_getCouponCode();
        $this->discountRate = $memento->_getDiscountRate();
        echo "  Cart: restored to [{$memento->getLabel()}]\n";
    }

    public function print(): void
    {
        echo "  Cart: " . count($this->items) . " item(s), ";
        foreach ($this->items as $item) {
            echo "{$item->name}x{$item->quantity} ";
        }
        $coupon = $this->couponCode ? " [coupon: {$this->couponCode}]" : "";
        echo "| total=\${$this->total()}{$coupon}\n";
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Caretaker: CartHistory
// ─────────────────────────────────────────────────────────────────────────────

class CartHistory
{
    /** @var CartMemento[] */
    private array $undoStack = [];
    /** @var CartMemento[] */
    private array $redoStack = [];

    public function __construct(private ShoppingCart $cart) {}

    public function checkpoint(string $label): void
    {
        $m = $this->cart->save($label);
        $this->undoStack[] = $m;
        $this->redoStack   = [];
        echo "[History] checkpoint: $m\n";
    }

    public function undo(): bool
    {
        if (empty($this->undoStack)) {
            echo "[History] nothing to undo\n";
            return false;
        }
        $this->redoStack[] = $this->cart->save('(redo point)');
        $memento = array_pop($this->undoStack);
        $this->cart->restore($memento);
        return true;
    }

    public function redo(): bool
    {
        if (empty($this->redoStack)) {
            echo "[History] nothing to redo\n";
            return false;
        }
        $this->undoStack[] = $this->cart->save('(undo point)');
        $memento = array_pop($this->redoStack);
        $this->cart->restore($memento);
        return true;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Demo
// ─────────────────────────────────────────────────────────────────────────────

$cart    = new ShoppingCart();
$history = new CartHistory($cart);

echo "\n--- Add items ---\n";
$history->checkpoint('empty cart');
$cart->addItem(new CartItem('SKU-001', 'Wireless Headphones', 79.99, 1));
$cart->addItem(new CartItem('SKU-002', 'USB-C Cable',          9.99, 2));

echo "\n--- Apply coupon ---\n";
$history->checkpoint('items added');
$cart->applyCoupon('SAVE10', 10.0);

echo "\n--- Remove an item by mistake ---\n";
$history->checkpoint('coupon applied');
$cart->removeItem('SKU-001');
$cart->print();

echo "\n--- Undo accidental removal ---\n";
$history->undo();
$cart->print();

echo "\n--- Undo coupon ---\n";
$history->undo();
$cart->print();

echo "\n--- Redo coupon ---\n";
$history->redo();
$cart->print();
```

---

### Ruby

```ruby
# Real-world example: A document editor that tracks a document's text
# and metadata, supporting multi-level undo and redo operations.

# ─────────────────────────────────────────────────────────────────────────────
# Memento — frozen value object; internal state hidden via a closure trick
# ─────────────────────────────────────────────────────────────────────────────

class DocumentMemento
  attr_reader :label, :created_at

  def initialize(content, metadata, label)
    # Freeze the copies so nobody can mutate the snapshot
    state = { content: content.dup.freeze, metadata: metadata.dup.freeze }.freeze

    # Expose state only through a lambda — closures restrict access better than
    # private methods in Ruby (any caller can send :private_method).
    @_reader = lambda { state }
    @label   = label.freeze
    @created_at = Time.now.freeze
  end

  def to_s
    "Memento[#{@label}, #{@created_at.strftime('%H:%M:%S')}]"
  end

  # Semi-private: only DocumentEditor calls this method by convention.
  # Prefixed with underscore to signal it is not for external callers.
  def _state
    @_reader.call
  end
end

# ─────────────────────────────────────────────────────────────────────────────
# Originator: DocumentEditor
# ─────────────────────────────────────────────────────────────────────────────

class DocumentEditor
  attr_reader :title

  def initialize(title)
    @title    = title
    @content  = ""
    @metadata = { author: "", tags: [], word_count: 0 }
  end

  # ── Editing operations ─────────────────────────────────────────────────────

  def write(text)
    @content += text
    @metadata[:word_count] = @content.split.size
    puts "  Editor: wrote #{text.length} chars, total words=#{@metadata[:word_count]}"
  end

  def delete_last(n_chars)
    @content = @content[0...-n_chars] || ""
    @metadata[:word_count] = @content.split.size
    puts "  Editor: deleted #{n_chars} chars"
  end

  def set_author(name)
    @metadata[:author] = name
    puts "  Editor: author set to '#{name}'"
  end

  def add_tag(tag)
    @metadata[:tags] = (@metadata[:tags] + [tag]).uniq
    puts "  Editor: added tag '#{tag}'"
  end

  def remove_tag(tag)
    @metadata[:tags] = @metadata[:tags].reject { |t| t == tag }
    puts "  Editor: removed tag '#{tag}'"
  end

  # ── Memento interface ──────────────────────────────────────────────────────

  def save(label = "")
    DocumentMemento.new(@content.dup, @metadata.dup, label)
  end

  def restore(memento)
    state = memento._state          # wide interface — only editor calls this
    @content  = state[:content].dup
    raw_meta  = state[:metadata]
    @metadata = {
      author:     raw_meta[:author].dup,
      tags:       raw_meta[:tags].dup,
      word_count: raw_meta[:word_count]
    }
    puts "  Editor: restored to [#{memento.label}]"
  end

  def print_state
    puts "  Doc '#{@title}': words=#{@metadata[:word_count]} " \
         "author='#{@metadata[:author]}' " \
         "tags=#{@metadata[:tags]} " \
         "content=#{@content[0, 40].inspect}#{'...' if @content.length > 40}"
  end
end

# ─────────────────────────────────────────────────────────────────────────────
# Caretaker: DocumentHistory
# ─────────────────────────────────────────────────────────────────────────────

class DocumentHistory
  def initialize(editor)
    @editor     = editor
    @undo_stack = []
    @redo_stack = []
  end

  def checkpoint(label = "")
    m = @editor.save(label)
    @undo_stack.push(m)
    @redo_stack.clear
    puts "[History] checkpoint: #{m}"
  end

  def undo
    if @undo_stack.empty?
      puts "[History] nothing to undo"
      return false
    end
    @redo_stack.push(@editor.save("(redo point)"))
    @editor.restore(@undo_stack.pop)
    true
  end

  def redo
    if @redo_stack.empty?
      puts "[History] nothing to redo"
      return false
    end
    @undo_stack.push(@editor.save("(undo point)"))
    @editor.restore(@redo_stack.pop)
    true
  end

  def stacks
    puts "[History] undo=#{@undo_stack.size}, redo=#{@redo_stack.size}"
  end
end

# ─────────────────────────────────────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────────────────────────────────────

editor  = DocumentEditor.new("Design Patterns Overview")
history = DocumentHistory.new(editor)

puts "\n--- Set author ---"
history.checkpoint("blank document")
editor.set_author("Alice")

puts "\n--- Write introduction ---"
history.checkpoint("author set")
editor.write("Design patterns are reusable solutions to common software problems. ")
editor.add_tag("architecture")
editor.add_tag("patterns")

puts "\n--- Write body ---"
history.checkpoint("introduction written")
editor.write("They are categorized into creational, structural, and behavioral patterns.")
editor.add_tag("oop")

puts "\n--- Current state ---"
editor.print_state
history.stacks

puts "\n--- Undo body ---"
history.undo
editor.print_state

puts "\n--- Undo introduction ---"
history.undo
editor.print_state

puts "\n--- Redo introduction ---"
history.redo
editor.print_state
```

---

## When To Use

Use the Memento pattern when:

- You need to implement **undo/redo** functionality and want to preserve encapsulation of the object being snapshotted.
- You want to produce **point-in-time snapshots** of an object so it can be restored to a prior state (e.g., save games, checkpoints, transaction rollback).
- **Direct access to the object's fields** would violate encapsulation or expose implementation details to unrelated classes (e.g., the undo manager should not know about editor internals).
- The **state is complex enough** that it cannot be easily reconstructed from a simple log of operations, making a full snapshot more practical than command-based undo.
- You want the Caretaker code to remain **simple and decoupled** — it should not need to understand the snapshots it manages.

Avoid it when:

- The state object is very large and snapshots would be too expensive — consider a diff-based (Command) approach instead.
- The language does not enforce access control well enough to keep Mementos truly opaque (though convention can substitute for enforcement).

---

## Pros & Cons

### Pros

- **Preserves encapsulation**: The Originator's internal structure is never exposed to external classes. The Caretaker handles Mementos as opaque tokens.
- **Simplifies Caretaker code**: The Caretaker does not need to know anything about the Originator's state format — it just stores and returns Mementos.
- **Clean undo/redo**: Producing and restoring full snapshots is straightforward and reliable compared to reverse-engineering operations.
- **Single-responsibility**: State-saving logic lives in the Originator, not scattered across callers.

### Cons

- **Memory consumption**: If clients create Mementos too frequently, or if the object's state is large, the application can consume excessive RAM. Mementos for a large object held for a long history can become a memory bottleneck.
- **Caretaker lifecycle management**: The Caretaker must track when Mementos are no longer needed and destroy them (or the Originator must do so) to prevent memory leaks, especially if the Originator's lifecycle is complex.
- **Weak encapsulation in dynamic languages**: Languages like Python, Ruby, and JavaScript cannot truly restrict access to an object's fields. The pattern relies on convention (prefixing with `_`) rather than enforced access control, so a careless caller can still inspect or mutate Memento state.
- **Serialization complexity**: If the Originator contains references to external objects (e.g., open file handles, database connections), those cannot be meaningfully snapshotted and must be handled separately.
- **Shallow vs. deep copy pitfalls**: Implementors must be careful to deep-copy mutable nested structures; a shallow copy creates hidden aliasing bugs where modifying the Originator retroactively changes past snapshots.

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Command** | Command records *what operation* was performed (and how to reverse it), while Memento records *the full state* before the operation. They are complementary: Commands can use Mementos internally to implement undo by snapshotting state rather than computing an inverse operation. |
| **Iterator** | Iterator traverses a collection; Memento can capture the Iterator's current traversal position so iteration can resume from a saved point. They compose naturally in collection-processing pipelines. |
| **Prototype** | Prototype clones an object (typically to create a new, independent copy for use). Memento similarly copies state, but the copy is stored for later restoration rather than used as a working object. Prototype can be used to implement Memento when the Originator already supports cloning. |

---

## Sources

- https://refactoring.guru/design-patterns/memento
- https://sourcemaking.com/design_patterns/memento
