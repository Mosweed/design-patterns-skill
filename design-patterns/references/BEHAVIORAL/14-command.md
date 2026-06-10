# Command Pattern

**Category:** Behavioral
**Also Known As:** Action, Transaction

---

## Intent

Turns a request into a stand-alone object that contains all information about the request. This transformation lets you pass requests as method arguments, delay or queue request execution, and support undoable operations.

---

## Problem It Solves

Imagine building a GUI application with a toolbar full of buttons. Each button triggers a different operation — save, open, copy, paste, undo. A naive approach hard-codes each operation directly into the button's click handler. This creates several painful problems:

- **Tight coupling:** The GUI layer directly knows about business logic classes (Editor, File, Network). Changing any business logic forces GUI changes.
- **No undo/redo:** There is nowhere to store the history of operations or the state needed to reverse them.
- **No deferred execution:** You cannot queue operations, schedule them for later, or serialize them for remote execution.
- **Code duplication:** The same "save" logic might be triggered from a toolbar button, a keyboard shortcut, and a menu item — three places to update whenever it changes.

The core tension: **the object that initiates an action (sender) should not need to know the object that actually performs it (receiver).**

---

## Solution

Extract the request details — method, arguments, and the receiver object — into a dedicated **Command** class with a single `execute()` method. Each concrete command knows which receiver to call and with what parameters.

- The **Sender** (e.g., a Button) stores a reference to a Command object and triggers `execute()` — it does not do the actual work.
- The **Receiver** (e.g., Editor, FileSystem) contains the business logic and does the real work when invoked by the command.
- The **Client** creates concrete command instances, wires them to receivers, and assigns them to senders.

This indirection decouples senders from receivers and makes commands first-class objects that can be stored, passed, queued, logged, and reversed.

---

## Structure (ASCII diagram)

```
 +-----------+          +------------------+
 |  Client   |          |    Invoker       |
 |           |          |  (e.g. Button,   |
 |  creates  |          |   Scheduler)     |
 |  and wires|          |                  |
 |  commands |          |  -command: Cmd   |
 +-----------+          |  +setCommand()   |
       |                |  +executeAction()|
       |                +--------+---------+
       |                         |
       |                         | calls execute()
       |                         v
       |                +------------------+
       |                |  <<interface>>   |
       |                |    Command       |
       |                |                  |
       |                |  +execute()      |
       |                |  +undo()         |
       |                +--------+---------+
       |                         |
       |          +--------------+--------------+
       |          |                             |
       |   +------+----------+    +-------------+------+
       |   | ConcreteCommand1|    | ConcreteCommand2   |
       |   |                 |    |                    |
       +-->| -receiver: Rcv  |    | -receiver: Rcv     |
           | -backup: State  |    | -backup: State     |
           | +execute()      |    | +execute()         |
           | +undo()         |    | +undo()            |
           +------+----------+    +-------------+------+
                  |                             |
                  | calls action()              |
                  v                             v
           +------------------+        +------------------+
           |    Receiver      |        |    Receiver      |
           | (e.g. Editor,    |        | (e.g. FileSystem)|
           |  TextBuffer)     |        |                  |
           | +action()        |        | +action()        |
           +------------------+        +------------------+
```

---

## Participants

| Participant         | Role                                                                                                           |
|---------------------|----------------------------------------------------------------------------------------------------------------|
| **Invoker/Sender**  | Triggers the command. Holds a reference to a Command object. Never communicates with the receiver directly.    |
| **Command**         | Interface (or abstract class) declaring the `execute()` and optionally `undo()` methods.                       |
| **ConcreteCommand** | Implements Command. Binds a Receiver to a specific action. May save state needed for undo.                     |
| **Receiver**        | The object that contains the actual business logic. Any class can serve as a receiver.                         |
| **Client**          | Creates ConcreteCommand instances, supplies them with a Receiver, and registers them with Invokers.            |

---

## How It Works (step-by-step)

1. **Client** instantiates a `ConcreteCommand`, passing it the target `Receiver` (and any required arguments).
2. **Client** registers the command with an `Invoker` via `setCommand()` or similar.
3. Later, when the user interacts with the Invoker (e.g., clicks a button), the Invoker calls `command.execute()`.
4. The `ConcreteCommand` optionally saves the receiver's current state (for undo), then calls the appropriate method on the `Receiver`.
5. The `Receiver` performs the actual work.
6. For **undo**, the Invoker calls `command.undo()`. The `ConcreteCommand` uses its saved backup state to restore the `Receiver` to its previous state.
7. Commands can be stored in a history stack to support multi-level undo/redo.
8. Commands can be serialized and sent across a network, saved to disk, or placed in a queue for deferred execution.

---

## Code Examples

### Python

```python
"""
Command Pattern — Text Editor with Undo/Redo

Real-world scenario: A simple text editor where users can type text,
delete text, and undo/redo those operations. Commands encapsulate each
editing action, enabling an unlimited undo/redo history stack.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Receiver — contains the actual editing business logic
# ---------------------------------------------------------------------------

class TextBuffer:
    """The receiver: manages the raw text content."""

    def __init__(self) -> None:
        self._content: str = ""

    @property
    def content(self) -> str:
        return self._content

    def insert(self, position: int, text: str) -> None:
        self._content = self._content[:position] + text + self._content[position:]

    def delete(self, position: int, length: int) -> str:
        """Deletes `length` characters at `position`. Returns the deleted text."""
        deleted = self._content[position : position + length]
        self._content = self._content[:position] + self._content[position + length :]
        return deleted

    def __repr__(self) -> str:
        return f"TextBuffer({self._content!r})"


# ---------------------------------------------------------------------------
# Command interface
# ---------------------------------------------------------------------------

class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        ...

    @abstractmethod
    def undo(self) -> None:
        ...


# ---------------------------------------------------------------------------
# Concrete Commands
# ---------------------------------------------------------------------------

class InsertTextCommand(Command):
    """Inserts text at a given position."""

    def __init__(self, buffer: TextBuffer, position: int, text: str) -> None:
        self._buffer = buffer
        self._position = position
        self._text = text

    def execute(self) -> None:
        self._buffer.insert(self._position, self._text)

    def undo(self) -> None:
        # Undo insert = delete the same range we inserted
        self._buffer.delete(self._position, len(self._text))


class DeleteTextCommand(Command):
    """Deletes a range of text."""

    def __init__(self, buffer: TextBuffer, position: int, length: int) -> None:
        self._buffer = buffer
        self._position = position
        self._length = length
        self._deleted_text: str = ""  # saved for undo

    def execute(self) -> None:
        self._deleted_text = self._buffer.delete(self._position, self._length)

    def undo(self) -> None:
        # Undo delete = re-insert the saved text
        self._buffer.insert(self._position, self._deleted_text)


class ReplaceTextCommand(Command):
    """Replaces a range of text with new content (composed from Insert + Delete)."""

    def __init__(self, buffer: TextBuffer, position: int, length: int, new_text: str) -> None:
        self._delete_cmd = DeleteTextCommand(buffer, position, length)
        self._insert_cmd = InsertTextCommand(buffer, position, new_text)

    def execute(self) -> None:
        self._delete_cmd.execute()
        self._insert_cmd.execute()

    def undo(self) -> None:
        # Undo in reverse order
        self._insert_cmd.undo()
        self._delete_cmd.undo()


# ---------------------------------------------------------------------------
# Invoker — the editor controller that manages history
# ---------------------------------------------------------------------------

class Editor:
    """
    Invoker: Executes commands and maintains a history stack
    for unlimited undo/redo.
    """

    def __init__(self, buffer: TextBuffer) -> None:
        self._buffer = buffer
        self._history: list[Command] = []
        self._redo_stack: list[Command] = []

    def execute(self, command: Command) -> None:
        command.execute()
        self._history.append(command)
        # Any new action clears the redo stack
        self._redo_stack.clear()
        print(f"  Buffer: {self._buffer.content!r}")

    def undo(self) -> None:
        if not self._history:
            print("  Nothing to undo.")
            return
        command = self._history.pop()
        command.undo()
        self._redo_stack.append(command)
        print(f"  [UNDO] Buffer: {self._buffer.content!r}")

    def redo(self) -> None:
        if not self._redo_stack:
            print("  Nothing to redo.")
            return
        command = self._redo_stack.pop()
        command.execute()
        self._history.append(command)
        print(f"  [REDO] Buffer: {self._buffer.content!r}")


# ---------------------------------------------------------------------------
# Client code
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    buf = TextBuffer()
    editor = Editor(buf)

    print("=== Text Editor with Undo/Redo ===\n")

    print("1. Insert 'Hello, World!'")
    editor.execute(InsertTextCommand(buf, 0, "Hello, World!"))

    print("2. Insert ' Python' after 'Hello,'")
    editor.execute(InsertTextCommand(buf, 6, " Python"))

    print("3. Delete ' Python' (7 chars at position 6)")
    editor.execute(DeleteTextCommand(buf, 6, 7))

    print("4. Replace 'World' with 'Command Pattern'")
    editor.execute(ReplaceTextCommand(buf, 7, 5, "Command Pattern"))

    print("\n--- Undo last 2 actions ---")
    editor.undo()
    editor.undo()

    print("\n--- Redo 1 action ---")
    editor.redo()
```

---

### Java

```java
/**
 * Command Pattern — Smart Home Automation System
 *
 * Real-world scenario: A smart home controller where a single remote can
 * control lights, a thermostat, and a security system. Each button press
 * is a Command object. The remote supports undo for each slot.
 */

import java.util.*;

// ---------------------------------------------------------------------------
// Command interface
// ---------------------------------------------------------------------------
interface Command {
    void execute();
    void undo();
    String description();
}

// ---------------------------------------------------------------------------
// Receivers — actual devices with business logic
// ---------------------------------------------------------------------------
class Light {
    private final String location;
    private boolean on = false;
    private int brightness = 100; // percent

    public Light(String location) { this.location = location; }

    public void turnOn()  { on = true;  System.out.printf("  [%s Light] ON  (brightness: %d%%)%n", location, brightness); }
    public void turnOff() { on = false; System.out.printf("  [%s Light] OFF%n", location); }
    public void dim(int level) {
        brightness = level;
        System.out.printf("  [%s Light] Dimmed to %d%%%n", location, brightness);
    }
    public int getBrightness() { return brightness; }
    public boolean isOn() { return on; }
}

class Thermostat {
    private int temperature = 20; // Celsius

    public void setTemperature(int temp) {
        System.out.printf("  [Thermostat] Temperature set to %d°C%n", temp);
        this.temperature = temp;
    }
    public int getTemperature() { return temperature; }
}

class SecuritySystem {
    private boolean armed = false;

    public void arm()   { armed = true;  System.out.println("  [Security] System ARMED"); }
    public void disarm(){ armed = false; System.out.println("  [Security] System DISARMED"); }
    public boolean isArmed() { return armed; }
}

// ---------------------------------------------------------------------------
// Concrete Commands
// ---------------------------------------------------------------------------
class LightOnCommand implements Command {
    private final Light light;
    private int previousBrightness;
    private boolean wasOn;

    public LightOnCommand(Light light) { this.light = light; }

    @Override public void execute() {
        wasOn = light.isOn();
        previousBrightness = light.getBrightness();
        light.turnOn();
    }
    @Override public void undo() {
        if (!wasOn) light.turnOff();
        else light.dim(previousBrightness);
    }
    @Override public String description() { return "Turn Light On"; }
}

class LightDimCommand implements Command {
    private final Light light;
    private final int targetBrightness;
    private int previousBrightness;

    public LightDimCommand(Light light, int targetBrightness) {
        this.light = light;
        this.targetBrightness = targetBrightness;
    }

    @Override public void execute() {
        previousBrightness = light.getBrightness();
        light.dim(targetBrightness);
    }
    @Override public void undo() { light.dim(previousBrightness); }
    @Override public String description() { return "Dim Light to " + targetBrightness + "%"; }
}

class ThermostatCommand implements Command {
    private final Thermostat thermostat;
    private final int targetTemp;
    private int previousTemp;

    public ThermostatCommand(Thermostat thermostat, int targetTemp) {
        this.thermostat = thermostat;
        this.targetTemp = targetTemp;
    }

    @Override public void execute() {
        previousTemp = thermostat.getTemperature();
        thermostat.setTemperature(targetTemp);
    }
    @Override public void undo() { thermostat.setTemperature(previousTemp); }
    @Override public String description() { return "Set Thermostat to " + targetTemp + "°C"; }
}

class SecurityArmCommand implements Command {
    private final SecuritySystem system;

    public SecurityArmCommand(SecuritySystem system) { this.system = system; }

    @Override public void execute() { system.arm(); }
    @Override public void undo()    { system.disarm(); }
    @Override public String description() { return "Arm Security System"; }
}

/** Macro command: executes multiple commands as a single action. */
class MacroCommand implements Command {
    private final String name;
    private final List<Command> commands;

    public MacroCommand(String name, List<Command> commands) {
        this.name = name;
        this.commands = new ArrayList<>(commands);
    }

    @Override public void execute() {
        System.out.println("  [Macro: " + name + "] Executing...");
        commands.forEach(Command::execute);
    }
    @Override public void undo() {
        System.out.println("  [Macro: " + name + "] Undoing...");
        // Undo in reverse order
        ListIterator<Command> it = commands.listIterator(commands.size());
        while (it.hasPrevious()) it.previous().undo();
    }
    @Override public String description() { return "Macro: " + name; }
}

/** No-op command — safe default for unassigned remote slots. */
class NoCommand implements Command {
    @Override public void execute() { System.out.println("  [Remote] No command assigned."); }
    @Override public void undo()    {}
    @Override public String description() { return "(none)"; }
}

// ---------------------------------------------------------------------------
// Invoker — the smart home remote
// ---------------------------------------------------------------------------
class SmartRemote {
    private static final int SLOTS = 5;
    private final Command[] onCommands  = new Command[SLOTS];
    private final Command[] offCommands = new Command[SLOTS];
    private final Deque<Command> history = new ArrayDeque<>();

    public SmartRemote() {
        Command noOp = new NoCommand();
        Arrays.fill(onCommands,  noOp);
        Arrays.fill(offCommands, noOp);
    }

    public void setCommand(int slot, Command on, Command off) {
        onCommands[slot]  = on;
        offCommands[slot] = off;
    }

    public void pressOn(int slot) {
        System.out.printf("%nButton %d ON — %s%n", slot, onCommands[slot].description());
        onCommands[slot].execute();
        history.push(onCommands[slot]);
    }

    public void pressOff(int slot) {
        System.out.printf("%nButton %d OFF — %s%n", slot, offCommands[slot].description());
        offCommands[slot].execute();
        history.push(offCommands[slot]);
    }

    public void pressUndo() {
        if (history.isEmpty()) { System.out.println("\n[Remote] Nothing to undo."); return; }
        Command last = history.pop();
        System.out.printf("%n[UNDO] Reversing: %s%n", last.description());
        last.undo();
    }

    public void printLayout() {
        System.out.println("\n=== Remote Layout ===");
        for (int i = 0; i < SLOTS; i++) {
            System.out.printf("  Slot %d: ON=%-30s  OFF=%s%n",
                i, onCommands[i].description(), offCommands[i].description());
        }
    }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------
public class SmartHomeDemo {
    public static void main(String[] args) {
        // Receivers
        Light livingRoomLight = new Light("Living Room");
        Light bedroomLight    = new Light("Bedroom");
        Thermostat thermostat = new Thermostat();
        SecuritySystem security = new SecuritySystem();

        // Remote (Invoker)
        SmartRemote remote = new SmartRemote();

        // Wire commands to slots
        remote.setCommand(0,
            new LightOnCommand(livingRoomLight),
            new LightDimCommand(livingRoomLight, 10));

        remote.setCommand(1,
            new LightOnCommand(bedroomLight),
            new LightDimCommand(bedroomLight, 30));

        remote.setCommand(2,
            new ThermostatCommand(thermostat, 22),
            new ThermostatCommand(thermostat, 18));

        remote.setCommand(3,
            new SecurityArmCommand(security),
            new SecurityArmCommand(security)); // undo = disarm

        // "Good Night" macro: arm security + dim lights + lower thermostat
        Command goodNight = new MacroCommand("Good Night", List.of(
            new LightDimCommand(livingRoomLight, 5),
            new LightDimCommand(bedroomLight, 0),
            new ThermostatCommand(thermostat, 17),
            new SecurityArmCommand(security)
        ));
        remote.setCommand(4, goodNight, goodNight);

        remote.printLayout();

        System.out.println("\n=== Demo ===");
        remote.pressOn(0);
        remote.pressOn(2);
        remote.pressOn(3);
        remote.pressUndo();        // undo arm
        remote.pressOn(4);         // good night macro
        remote.pressUndo();        // undo macro
    }
}
```

---

### C++

```cpp
/**
 * Command Pattern — Task Queue / Job Scheduler
 *
 * Real-world scenario: A simple job scheduler that queues file operations
 * (copy, move, delete) for deferred or batch execution. Operations support
 * undo via a history stack.
 */

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <stack>
#include <queue>
#include <memory>
#include <functional>
#include <filesystem>

namespace fs = std::filesystem;

// ---------------------------------------------------------------------------
// Command interface
// ---------------------------------------------------------------------------
class Command {
public:
    virtual ~Command() = default;
    virtual void execute() = 0;
    virtual void undo() = 0;
    virtual std::string description() const = 0;
};

using CommandPtr = std::unique_ptr<Command>;

// ---------------------------------------------------------------------------
// Receiver — wraps filesystem operations
// ---------------------------------------------------------------------------
class FileSystem {
public:
    void copyFile(const fs::path& src, const fs::path& dst) {
        fs::copy_file(src, dst, fs::copy_options::overwrite_existing);
        std::cout << "  [FS] Copied: " << src << " -> " << dst << "\n";
    }

    void moveFile(const fs::path& src, const fs::path& dst) {
        fs::rename(src, dst);
        std::cout << "  [FS] Moved:  " << src << " -> " << dst << "\n";
    }

    void deleteFile(const fs::path& path) {
        fs::remove(path);
        std::cout << "  [FS] Deleted: " << path << "\n";
    }

    void createFile(const fs::path& path, const std::string& content = "") {
        std::ofstream ofs(path);
        ofs << content;
        std::cout << "  [FS] Created: " << path << "\n";
    }

    std::string readFile(const fs::path& path) {
        std::ifstream ifs(path);
        std::ostringstream ss;
        ss << ifs.rdbuf();
        return ss.str();
    }
};

// ---------------------------------------------------------------------------
// Concrete Commands
// ---------------------------------------------------------------------------
class CopyFileCommand : public Command {
    FileSystem& fs_;
    fs::path src_, dst_;
public:
    CopyFileCommand(FileSystem& fs, fs::path src, fs::path dst)
        : fs_(fs), src_(std::move(src)), dst_(std::move(dst)) {}

    void execute() override { fs_.copyFile(src_, dst_); }
    void undo()    override { fs::remove(dst_); std::cout << "  [UNDO] Removed copy: " << dst_ << "\n"; }
    std::string description() const override {
        return "Copy " + src_.string() + " -> " + dst_.string();
    }
};

class MoveFileCommand : public Command {
    FileSystem& fs_;
    fs::path src_, dst_;
public:
    MoveFileCommand(FileSystem& fs, fs::path src, fs::path dst)
        : fs_(fs), src_(std::move(src)), dst_(std::move(dst)) {}

    void execute() override { fs_.moveFile(src_, dst_); }
    void undo()    override { fs_.moveFile(dst_, src_); std::cout << "  [UNDO] Moved back\n"; }
    std::string description() const override {
        return "Move " + src_.string() + " -> " + dst_.string();
    }
};

class DeleteFileCommand : public Command {
    FileSystem& fs_;
    fs::path path_;
    std::string backup_;          // save content for undo
    fs::path backupPath_;
public:
    DeleteFileCommand(FileSystem& fs, fs::path path)
        : fs_(fs), path_(std::move(path)), backupPath_(path_.string() + ".bak") {}

    void execute() override {
        // Save backup before deleting
        backup_ = fs_.readFile(path_);
        fs_.copyFile(path_, backupPath_);
        fs_.deleteFile(path_);
    }
    void undo() override {
        fs_.moveFile(backupPath_, path_);
        std::cout << "  [UNDO] Restored: " << path_ << "\n";
    }
    std::string description() const override { return "Delete " + path_.string(); }
};

/** Batch command: executes a list of commands atomically (all-or-nothing style). */
class BatchCommand : public Command {
    std::string name_;
    std::vector<CommandPtr> commands_;
    std::vector<Command*>   executed_; // track which ran (for partial undo)
public:
    BatchCommand(std::string name) : name_(std::move(name)) {}

    void add(CommandPtr cmd) { commands_.push_back(std::move(cmd)); }

    void execute() override {
        executed_.clear();
        std::cout << "  [Batch: " << name_ << "] Start\n";
        for (auto& cmd : commands_) {
            cmd->execute();
            executed_.push_back(cmd.get());
        }
        std::cout << "  [Batch: " << name_ << "] Done\n";
    }

    void undo() override {
        std::cout << "  [Batch: " << name_ << "] Undo\n";
        for (auto it = executed_.rbegin(); it != executed_.rend(); ++it)
            (*it)->undo();
        executed_.clear();
    }

    std::string description() const override { return "Batch[" + name_ + "]"; }
};

// ---------------------------------------------------------------------------
// Invoker — job scheduler with history and queue
// ---------------------------------------------------------------------------
class JobScheduler {
    std::queue<CommandPtr>  pending_;
    std::stack<Command*>    history_;
    std::vector<CommandPtr> store_;   // owns all commands after scheduling
public:
    void schedule(CommandPtr cmd) {
        std::cout << "  [Scheduler] Queued: " << cmd->description() << "\n";
        pending_.push(std::move(cmd));
    }

    void runAll() {
        std::cout << "\n  [Scheduler] Running " << pending_.size() << " job(s)...\n";
        while (!pending_.empty()) {
            auto& cmd = pending_.front();
            cmd->execute();
            history_.push(cmd.get());
            store_.push_back(std::move(cmd));
            pending_.pop();
        }
    }

    void undoLast() {
        if (history_.empty()) { std::cout << "  [Scheduler] Nothing to undo.\n"; return; }
        history_.top()->undo();
        history_.pop();
    }
};

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------
int main() {
    using namespace std::string_literals;

    FileSystem fileSystem;
    JobScheduler scheduler;

    // Set up test files
    fileSystem.createFile("/tmp/cmd_report.txt",  "Sales report Q1 2025\n");
    fileSystem.createFile("/tmp/cmd_invoice.txt", "Invoice #1042\n");

    std::cout << "\n=== Scheduling Jobs ===\n";
    scheduler.schedule(std::make_unique<CopyFileCommand>(
        fileSystem, "/tmp/cmd_report.txt", "/tmp/cmd_report_backup.txt"));

    scheduler.schedule(std::make_unique<MoveFileCommand>(
        fileSystem, "/tmp/cmd_invoice.txt", "/tmp/cmd_archive_invoice.txt"));

    // Batch: archive multiple files
    auto batch = std::make_unique<BatchCommand>("Archive");
    batch->add(std::make_unique<CopyFileCommand>(
        fileSystem, "/tmp/cmd_report.txt", "/tmp/cmd_report_archive.txt"));
    batch->add(std::make_unique<DeleteFileCommand>(
        fileSystem, "/tmp/cmd_report.txt"));
    scheduler.schedule(std::move(batch));

    std::cout << "\n=== Running All Jobs ===\n";
    scheduler.runAll();

    std::cout << "\n=== Undo Last Job (Batch) ===\n";
    scheduler.undoLast();

    std::cout << "\n=== Undo Move ===\n";
    scheduler.undoLast();

    return 0;
}
```

---

### C#

```csharp
/**
 * Command Pattern — Restaurant Order Management System
 *
 * Real-world scenario: A restaurant POS (Point of Sale) system where waiters
 * send orders to the kitchen. Orders can be placed, cancelled (undo), and
 * re-ordered (redo). The kitchen receives commands and processes them.
 */

using System;
using System.Collections.Generic;

// ---------------------------------------------------------------------------
// Command interface
// ---------------------------------------------------------------------------
public interface ICommand
{
    void Execute();
    void Undo();
    string Description { get; }
}

// ---------------------------------------------------------------------------
// Receivers — kitchen stations
// ---------------------------------------------------------------------------
public class Kitchen
{
    private readonly string _station;
    private readonly List<string> _activeOrders = new();

    public Kitchen(string station) => _station = station;

    public void PrepareItem(string item)
    {
        _activeOrders.Add(item);
        Console.WriteLine($"  [{_station}] Preparing: {item}");
    }

    public void CancelItem(string item)
    {
        if (_activeOrders.Remove(item))
            Console.WriteLine($"  [{_station}] Cancelled: {item}");
        else
            Console.WriteLine($"  [{_station}] Item not found (already done?): {item}");
    }

    public void PrintQueue()
    {
        Console.WriteLine($"  [{_station}] Queue: [{string.Join(", ", _activeOrders)}]");
    }
}

public class Bar
{
    private readonly List<string> _drinks = new();

    public void MixDrink(string drink)
    {
        _drinks.Add(drink);
        Console.WriteLine($"  [Bar] Mixing: {drink}");
    }

    public void CancelDrink(string drink)
    {
        _drinks.Remove(drink);
        Console.WriteLine($"  [Bar] Cancelled drink: {drink}");
    }
}

// ---------------------------------------------------------------------------
// Concrete Commands
// ---------------------------------------------------------------------------
public class OrderFoodCommand : ICommand
{
    private readonly Kitchen _kitchen;
    private readonly string _item;

    public OrderFoodCommand(Kitchen kitchen, string item)
    {
        _kitchen = kitchen;
        _item = item;
    }

    public void Execute() => _kitchen.PrepareItem(_item);
    public void Undo()    => _kitchen.CancelItem(_item);
    public string Description => $"Order food: {_item}";
}

public class OrderDrinkCommand : ICommand
{
    private readonly Bar _bar;
    private readonly string _drink;

    public OrderDrinkCommand(Bar bar, string drink)
    {
        _bar = bar;
        _drink = drink;
    }

    public void Execute() => _bar.MixDrink(_drink);
    public void Undo()    => _bar.CancelDrink(_drink);
    public string Description => $"Order drink: {_drink}";
}

/// <summary>Composite: sends multiple items in one go.</summary>
public class TableOrderCommand : ICommand
{
    private readonly string _tableId;
    private readonly List<ICommand> _items;

    public TableOrderCommand(string tableId, IEnumerable<ICommand> items)
    {
        _tableId = tableId;
        _items = new List<ICommand>(items);
    }

    public void Execute()
    {
        Console.WriteLine($"\n  [Table {_tableId}] Order received:");
        foreach (var item in _items) item.Execute();
    }

    public void Undo()
    {
        Console.WriteLine($"\n  [Table {_tableId}] Order cancelled:");
        for (int i = _items.Count - 1; i >= 0; i--)
            _items[i].Undo();
    }

    public string Description => $"Table {_tableId} full order ({_items.Count} items)";
}

// ---------------------------------------------------------------------------
// Invoker — waiter's order pad (POS terminal)
// ---------------------------------------------------------------------------
public class OrderPad
{
    private readonly Stack<ICommand> _history  = new();
    private readonly Stack<ICommand> _redoStack = new();

    public void PlaceOrder(ICommand command)
    {
        Console.WriteLine($"\n[POS] Placing: {command.Description}");
        command.Execute();
        _history.Push(command);
        _redoStack.Clear();
    }

    public void CancelLast()
    {
        if (_history.Count == 0) { Console.WriteLine("[POS] Nothing to cancel."); return; }
        var cmd = _history.Pop();
        Console.WriteLine($"\n[POS] Cancelling: {cmd.Description}");
        cmd.Undo();
        _redoStack.Push(cmd);
    }

    public void Redo()
    {
        if (_redoStack.Count == 0) { Console.WriteLine("[POS] Nothing to redo."); return; }
        var cmd = _redoStack.Pop();
        Console.WriteLine($"\n[POS] Re-placing: {cmd.Description}");
        cmd.Execute();
        _history.Push(cmd);
    }

    public void PrintHistory()
    {
        Console.WriteLine("\n[POS] Order history:");
        int i = 1;
        foreach (var cmd in _history)
            Console.WriteLine($"  {i++}. {cmd.Description}");
    }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------
class Program
{
    static void Main()
    {
        var hotKitchen = new Kitchen("Hot Kitchen");
        var coldKitchen = new Kitchen("Cold Kitchen");
        var bar = new Bar();
        var pos = new OrderPad();

        Console.WriteLine("=== Restaurant POS Demo ===");

        // Individual orders
        pos.PlaceOrder(new OrderFoodCommand(hotKitchen, "Grilled Salmon"));
        pos.PlaceOrder(new OrderDrinkCommand(bar, "Mojito"));
        pos.PlaceOrder(new OrderFoodCommand(coldKitchen, "Caesar Salad"));

        // Composite table order
        var tableOrder = new TableOrderCommand("12", new ICommand[]
        {
            new OrderFoodCommand(hotKitchen, "Ribeye Steak"),
            new OrderFoodCommand(coldKitchen, "Bruschetta"),
            new OrderDrinkCommand(bar, "Red Wine"),
        });
        pos.PlaceOrder(tableOrder);

        pos.PrintHistory();

        Console.WriteLine("\n--- Cancel last order (Table 12) ---");
        pos.CancelLast();

        Console.WriteLine("\n--- Redo Table 12 order ---");
        pos.Redo();

        Console.WriteLine("\n--- Cancel individual drink ---");
        pos.CancelLast();
        pos.CancelLast();

        pos.PrintHistory();
    }
}
```

---

### TypeScript

```typescript
/**
 * Command Pattern — HTTP Request Pipeline with Retry & Rollback
 *
 * Real-world scenario: An API client that wraps HTTP requests as Command
 * objects. Commands can be queued for offline-then-sync scenarios, retried
 * on failure, and rolled back when part of a transaction fails.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface ApiResponse<T = unknown> {
  status: number;
  data: T;
}

// ---------------------------------------------------------------------------
// Command interface
// ---------------------------------------------------------------------------
interface Command<TResult = void> {
  execute(): Promise<TResult>;
  undo(): Promise<void>;
  readonly description: string;
  readonly retryCount: number;
}

// ---------------------------------------------------------------------------
// Receiver — raw HTTP transport
// ---------------------------------------------------------------------------
class HttpClient {
  private readonly baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async get<T>(path: string): Promise<ApiResponse<T>> {
    console.log(`  [HTTP] GET ${this.baseUrl}${path}`);
    // Simulated response for demo purposes
    return { status: 200, data: { id: 1, path } as unknown as T };
  }

  async post<T>(path: string, body: unknown): Promise<ApiResponse<T>> {
    console.log(`  [HTTP] POST ${this.baseUrl}${path}`, JSON.stringify(body));
    return { status: 201, data: { id: Date.now(), ...body as object } as unknown as T };
  }

  async put<T>(path: string, body: unknown): Promise<ApiResponse<T>> {
    console.log(`  [HTTP] PUT ${this.baseUrl}${path}`, JSON.stringify(body));
    return { status: 200, data: body as unknown as T };
  }

  async delete(path: string): Promise<void> {
    console.log(`  [HTTP] DELETE ${this.baseUrl}${path}`);
  }
}

// ---------------------------------------------------------------------------
// Concrete Commands
// ---------------------------------------------------------------------------
class CreateUserCommand implements Command<{ id: number; name: string; email: string }> {
  readonly description: string;
  readonly retryCount = 3;
  private createdId?: number;

  constructor(
    private readonly client: HttpClient,
    private readonly payload: { name: string; email: string }
  ) {
    this.description = `Create user: ${payload.email}`;
  }

  async execute() {
    const res = await this.client.post<{ id: number; name: string; email: string }>(
      "/users",
      this.payload
    );
    this.createdId = res.data.id;
    console.log(`  [CreateUser] Created with ID=${this.createdId}`);
    return res.data;
  }

  async undo() {
    if (this.createdId !== undefined) {
      await this.client.delete(`/users/${this.createdId}`);
      console.log(`  [CreateUser UNDO] Deleted user ID=${this.createdId}`);
    }
  }
}

class UpdateUserCommand implements Command {
  readonly description: string;
  readonly retryCount = 3;
  private previousData?: unknown;

  constructor(
    private readonly client: HttpClient,
    private readonly userId: number,
    private readonly updates: Record<string, unknown>
  ) {
    this.description = `Update user #${userId}`;
  }

  async execute() {
    // Fetch current state for undo snapshot
    const current = await this.client.get(`/users/${this.userId}`);
    this.previousData = current.data;

    await this.client.put(`/users/${this.userId}`, this.updates);
    console.log(`  [UpdateUser] Updated user #${this.userId}`);
  }

  async undo() {
    if (this.previousData) {
      await this.client.put(`/users/${this.userId}`, this.previousData);
      console.log(`  [UpdateUser UNDO] Reverted user #${this.userId}`);
    }
  }
}

class SendEmailCommand implements Command {
  readonly description: string;
  readonly retryCount = 5; // Email delivery warrants more retries
  private messageId?: string;

  constructor(
    private readonly client: HttpClient,
    private readonly to: string,
    private readonly subject: string
  ) {
    this.description = `Send email to ${to}: "${subject}"`;
  }

  async execute() {
    const res = await this.client.post<{ messageId: string }>("/emails/send", {
      to: this.to,
      subject: this.subject,
    });
    this.messageId = res.data.messageId;
    console.log(`  [SendEmail] Sent, messageId=${this.messageId}`);
  }

  async undo() {
    // Some email APIs support recall within a time window
    if (this.messageId) {
      await this.client.delete(`/emails/${this.messageId}`);
      console.log(`  [SendEmail UNDO] Recalled message ${this.messageId}`);
    }
  }
}

// ---------------------------------------------------------------------------
// Invoker — command queue with retry and transaction support
// ---------------------------------------------------------------------------
class ApiCommandQueue {
  private queue: Command[] = [];
  private history: Command[] = [];

  enqueue(command: Command): void {
    console.log(`  [Queue] Enqueued: ${command.description}`);
    this.queue.push(command);
  }

  async flush(): Promise<void> {
    console.log(`\n  [Queue] Flushing ${this.queue.length} command(s)...`);

    while (this.queue.length > 0) {
      const cmd = this.queue.shift()!;
      await this.executeWithRetry(cmd);
      this.history.push(cmd);
    }
  }

  private async executeWithRetry(cmd: Command, attempt = 1): Promise<void> {
    try {
      await cmd.execute();
    } catch (err) {
      if (attempt <= cmd.retryCount) {
        console.warn(`  [Queue] Retry ${attempt}/${cmd.retryCount} for: ${cmd.description}`);
        await new Promise((r) => setTimeout(r, 100 * attempt)); // back-off
        return this.executeWithRetry(cmd, attempt + 1);
      }
      throw err;
    }
  }

  async undoLast(): Promise<void> {
    const cmd = this.history.pop();
    if (!cmd) { console.log("  [Queue] Nothing to undo."); return; }
    console.log(`\n  [Queue UNDO] Reversing: ${cmd.description}`);
    await cmd.undo();
  }

  async rollback(): Promise<void> {
    console.log(`\n  [Queue] Rolling back ${this.history.length} command(s)...`);
    while (this.history.length > 0) {
      await this.undoLast();
    }
  }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------
(async () => {
  const client = new HttpClient("https://api.example.com");
  const queue = new ApiCommandQueue();

  console.log("=== API Request Pipeline Demo ===\n");

  console.log("--- Queuing operations ---");
  queue.enqueue(new CreateUserCommand(client, { name: "Alice", email: "alice@example.com" }));
  queue.enqueue(new UpdateUserCommand(client, 42, { role: "admin" }));
  queue.enqueue(new SendEmailCommand(client, "alice@example.com", "Welcome to the platform!"));

  await queue.flush();

  console.log("\n--- Undo last action (email recall) ---");
  await queue.undoLast();

  console.log("\n--- Full rollback ---");
  await queue.rollback();
})();
```

---

### Go

```go
// Command Pattern — Database Migration Runner
//
// Real-world scenario: A database migration tool that represents each
// migration as a Command with Up (execute) and Down (undo) methods.
// A Runner applies or rolls back migrations in order.

package main

import (
	"fmt"
	"strings"
	"time"
)

// ---------------------------------------------------------------------------
// Command interface
// ---------------------------------------------------------------------------

// Migration is the Command interface.
type Migration interface {
	Up() error
	Down() error
	Version() string
	Description() string
}

// ---------------------------------------------------------------------------
// Receiver — simulated database connection
// ---------------------------------------------------------------------------

type Database struct {
	name    string
	tables  map[string][]string // table name -> column definitions
	indexes map[string]string   // index name -> table
	applied []string            // log of applied SQL statements
}

func NewDatabase(name string) *Database {
	return &Database{
		name:    name,
		tables:  make(map[string][]string),
		indexes: make(map[string]string),
	}
}

func (db *Database) CreateTable(table string, cols ...string) error {
	if _, exists := db.tables[table]; exists {
		return fmt.Errorf("table %q already exists", table)
	}
	db.tables[table] = cols
	stmt := fmt.Sprintf("CREATE TABLE %s (%s)", table, strings.Join(cols, ", "))
	db.applied = append(db.applied, stmt)
	fmt.Printf("  [DB:%s] %s\n", db.name, stmt)
	return nil
}

func (db *Database) DropTable(table string) error {
	if _, exists := db.tables[table]; !exists {
		return fmt.Errorf("table %q does not exist", table)
	}
	delete(db.tables, table)
	stmt := fmt.Sprintf("DROP TABLE %s", table)
	db.applied = append(db.applied, stmt)
	fmt.Printf("  [DB:%s] %s\n", db.name, stmt)
	return nil
}

func (db *Database) AddColumn(table, colDef string) error {
	if _, exists := db.tables[table]; !exists {
		return fmt.Errorf("table %q does not exist", table)
	}
	db.tables[table] = append(db.tables[table], colDef)
	stmt := fmt.Sprintf("ALTER TABLE %s ADD COLUMN %s", table, colDef)
	db.applied = append(db.applied, stmt)
	fmt.Printf("  [DB:%s] %s\n", db.name, stmt)
	return nil
}

func (db *Database) DropColumn(table, col string) error {
	stmt := fmt.Sprintf("ALTER TABLE %s DROP COLUMN %s", table, col)
	db.applied = append(db.applied, stmt)
	fmt.Printf("  [DB:%s] %s\n", db.name, stmt)
	return nil
}

func (db *Database) CreateIndex(index, table, col string) error {
	db.indexes[index] = table
	stmt := fmt.Sprintf("CREATE INDEX %s ON %s(%s)", index, table, col)
	db.applied = append(db.applied, stmt)
	fmt.Printf("  [DB:%s] %s\n", db.name, stmt)
	return nil
}

func (db *Database) DropIndex(index string) error {
	delete(db.indexes, index)
	stmt := fmt.Sprintf("DROP INDEX %s", index)
	db.applied = append(db.applied, stmt)
	fmt.Printf("  [DB:%s] %s\n", db.name, stmt)
	return nil
}

func (db *Database) PrintSchema() {
	fmt.Printf("\n  [DB:%s] Current Schema:\n", db.name)
	for table, cols := range db.tables {
		fmt.Printf("    Table: %s\n      Columns: %s\n", table, strings.Join(cols, ", "))
	}
	if len(db.indexes) > 0 {
		fmt.Printf("    Indexes: %v\n", db.indexes)
	}
}

// ---------------------------------------------------------------------------
// Concrete Commands (Migrations)
// ---------------------------------------------------------------------------

// CreateUsersTableMigration creates the users table.
type CreateUsersTableMigration struct {
	db *Database
}

func (m *CreateUsersTableMigration) Version() string     { return "001" }
func (m *CreateUsersTableMigration) Description() string { return "Create users table" }

func (m *CreateUsersTableMigration) Up() error {
	return m.db.CreateTable("users",
		"id BIGINT PRIMARY KEY AUTO_INCREMENT",
		"email VARCHAR(255) NOT NULL UNIQUE",
		"password_hash VARCHAR(255) NOT NULL",
		"created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
	)
}

func (m *CreateUsersTableMigration) Down() error {
	return m.db.DropTable("users")
}

// AddUserProfileMigration adds profile columns to users.
type AddUserProfileMigration struct {
	db *Database
}

func (m *AddUserProfileMigration) Version() string     { return "002" }
func (m *AddUserProfileMigration) Description() string { return "Add profile columns to users" }

func (m *AddUserProfileMigration) Up() error {
	if err := m.db.AddColumn("users", "display_name VARCHAR(100)"); err != nil {
		return err
	}
	return m.db.AddColumn("users", "avatar_url TEXT")
}

func (m *AddUserProfileMigration) Down() error {
	if err := m.db.DropColumn("users", "avatar_url"); err != nil {
		return err
	}
	return m.db.DropColumn("users", "display_name")
}

// CreatePostsTableMigration creates the posts table with an index.
type CreatePostsTableMigration struct {
	db *Database
}

func (m *CreatePostsTableMigration) Version() string     { return "003" }
func (m *CreatePostsTableMigration) Description() string { return "Create posts table + index" }

func (m *CreatePostsTableMigration) Up() error {
	if err := m.db.CreateTable("posts",
		"id BIGINT PRIMARY KEY AUTO_INCREMENT",
		"user_id BIGINT NOT NULL REFERENCES users(id)",
		"title VARCHAR(500) NOT NULL",
		"body TEXT",
		"published_at TIMESTAMP",
	); err != nil {
		return err
	}
	return m.db.CreateIndex("idx_posts_user_id", "posts", "user_id")
}

func (m *CreatePostsTableMigration) Down() error {
	if err := m.db.DropIndex("idx_posts_user_id"); err != nil {
		return err
	}
	return m.db.DropTable("posts")
}

// ---------------------------------------------------------------------------
// Invoker — migration runner
// ---------------------------------------------------------------------------

type AppliedRecord struct {
	version   string
	migration Migration
	appliedAt time.Time
}

type MigrationRunner struct {
	db      *Database
	applied []AppliedRecord
}

func NewMigrationRunner(db *Database) *MigrationRunner {
	return &MigrationRunner{db: db}
}

// Migrate applies all provided migrations in order.
func (r *MigrationRunner) Migrate(migrations ...Migration) error {
	for _, m := range migrations {
		fmt.Printf("\n[Runner] Applying %s: %s\n", m.Version(), m.Description())
		if err := m.Up(); err != nil {
			return fmt.Errorf("migration %s failed: %w", m.Version(), err)
		}
		r.applied = append(r.applied, AppliedRecord{
			version:   m.Version(),
			migration: m,
			appliedAt: time.Now(),
		})
	}
	return nil
}

// Rollback reverses the last N applied migrations.
func (r *MigrationRunner) Rollback(steps int) error {
	if steps > len(r.applied) {
		steps = len(r.applied)
	}
	for i := 0; i < steps; i++ {
		rec := r.applied[len(r.applied)-1]
		r.applied = r.applied[:len(r.applied)-1]
		fmt.Printf("\n[Runner] Rolling back %s: %s\n", rec.version, rec.migration.Description())
		if err := rec.migration.Down(); err != nil {
			return fmt.Errorf("rollback %s failed: %w", rec.version, err)
		}
	}
	return nil
}

func (r *MigrationRunner) Status() {
	fmt.Println("\n[Runner] Applied migrations:")
	for _, rec := range r.applied {
		fmt.Printf("  v%s — %s (at %s)\n", rec.version, rec.migration.Description(),
			rec.appliedAt.Format(time.RFC3339))
	}
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

func main() {
	db := NewDatabase("app_production")
	runner := NewMigrationRunner(db)

	fmt.Println("=== Database Migration Runner ===")

	// Apply all migrations
	err := runner.Migrate(
		&CreateUsersTableMigration{db},
		&AddUserProfileMigration{db},
		&CreatePostsTableMigration{db},
	)
	if err != nil {
		fmt.Printf("Migration failed: %v\n", err)
		return
	}

	db.PrintSchema()
	runner.Status()

	fmt.Println("\n--- Rolling back last 2 migrations ---")
	if err := runner.Rollback(2); err != nil {
		fmt.Printf("Rollback failed: %v\n", err)
	}

	db.PrintSchema()
	runner.Status()
}
```

---

### PHP

```php
<?php
/**
 * Command Pattern — Shopping Cart with Undo
 *
 * Real-world scenario: An e-commerce shopping cart where each user action
 * (add item, remove item, apply coupon) is a Command. The cart supports
 * undoing recent operations, enabling a "revert last change" feature.
 */

declare(strict_types=1);

// ---------------------------------------------------------------------------
// Command interface
// ---------------------------------------------------------------------------
interface Command
{
    public function execute(): void;
    public function undo(): void;
    public function getDescription(): string;
}

// ---------------------------------------------------------------------------
// Receiver — the actual cart storage and pricing logic
// ---------------------------------------------------------------------------
class ShoppingCart
{
    /** @var array<string, array{name: string, price: float, qty: int}> */
    private array $items = [];
    private ?string $couponCode = null;
    private float $discountPercent = 0.0;

    public function addItem(string $sku, string $name, float $price, int $qty = 1): void
    {
        if (isset($this->items[$sku])) {
            $this->items[$sku]['qty'] += $qty;
        } else {
            $this->items[$sku] = ['name' => $name, 'price' => $price, 'qty' => $qty];
        }
        echo "  [Cart] Added {$qty}x {$name} (SKU: {$sku}) @ \${$price}\n";
    }

    public function removeItem(string $sku, int $qty = 1): bool
    {
        if (!isset($this->items[$sku])) {
            echo "  [Cart] SKU {$sku} not in cart.\n";
            return false;
        }
        $this->items[$sku]['qty'] -= $qty;
        if ($this->items[$sku]['qty'] <= 0) {
            unset($this->items[$sku]);
        }
        echo "  [Cart] Removed {$qty}x SKU {$sku}\n";
        return true;
    }

    public function applyCoupon(string $code, float $discountPercent): void
    {
        $this->couponCode      = $code;
        $this->discountPercent = $discountPercent;
        echo "  [Cart] Coupon '{$code}' applied — {$discountPercent}% off\n";
    }

    public function removeCoupon(): void
    {
        echo "  [Cart] Coupon '{$this->couponCode}' removed\n";
        $this->couponCode      = null;
        $this->discountPercent = 0.0;
    }

    public function getItemQty(string $sku): int
    {
        return $this->items[$sku]['qty'] ?? 0;
    }

    public function hasCoupon(): bool
    {
        return $this->couponCode !== null;
    }

    public function total(): float
    {
        $subtotal = array_sum(array_map(
            fn($item) => $item['price'] * $item['qty'],
            $this->items
        ));
        return $subtotal * (1 - $this->discountPercent / 100);
    }

    public function printSummary(): void
    {
        echo "\n  === Cart Summary ===\n";
        foreach ($this->items as $sku => $item) {
            $line = $item['price'] * $item['qty'];
            echo "  {$item['name']} x{$item['qty']} = \${$line}\n";
        }
        if ($this->couponCode) {
            echo "  Coupon: {$this->couponCode} (-{$this->discountPercent}%)\n";
        }
        echo "  Total: \$" . number_format($this->total(), 2) . "\n";
        echo "  ===================\n";
    }
}

// ---------------------------------------------------------------------------
// Concrete Commands
// ---------------------------------------------------------------------------
class AddItemCommand implements Command
{
    public function __construct(
        private readonly ShoppingCart $cart,
        private readonly string $sku,
        private readonly string $name,
        private readonly float $price,
        private int $qty = 1
    ) {}

    public function execute(): void
    {
        $this->cart->addItem($this->sku, $this->name, $this->price, $this->qty);
    }

    public function undo(): void
    {
        $this->cart->removeItem($this->sku, $this->qty);
    }

    public function getDescription(): string
    {
        return "Add {$this->qty}x {$this->name} to cart";
    }
}

class RemoveItemCommand implements Command
{
    private int $actualQtyRemoved = 0;

    public function __construct(
        private readonly ShoppingCart $cart,
        private readonly string $sku,
        private readonly string $name,
        private readonly float $price,
        private readonly int $qty = 1
    ) {}

    public function execute(): void
    {
        $this->actualQtyRemoved = $this->qty;
        $this->cart->removeItem($this->sku, $this->qty);
    }

    public function undo(): void
    {
        // Restore the removed quantity
        $this->cart->addItem($this->sku, $this->name, $this->price, $this->actualQtyRemoved);
    }

    public function getDescription(): string
    {
        return "Remove {$this->qty}x SKU {$this->sku} from cart";
    }
}

class ApplyCouponCommand implements Command
{
    private bool $hadPreviousCoupon = false;

    public function __construct(
        private readonly ShoppingCart $cart,
        private readonly string $code,
        private readonly float $discountPercent
    ) {}

    public function execute(): void
    {
        $this->hadPreviousCoupon = $this->cart->hasCoupon();
        $this->cart->applyCoupon($this->code, $this->discountPercent);
    }

    public function undo(): void
    {
        $this->cart->removeCoupon();
    }

    public function getDescription(): string
    {
        return "Apply coupon '{$this->code}' ({$this->discountPercent}% off)";
    }
}

// ---------------------------------------------------------------------------
// Invoker — cart controller / session manager
// ---------------------------------------------------------------------------
class CartController
{
    /** @var Command[] */
    private array $history = [];

    public function __construct(private readonly ShoppingCart $cart) {}

    public function execute(Command $command): void
    {
        echo "\n[Action] " . $command->getDescription() . "\n";
        $command->execute();
        $this->history[] = $command;
    }

    public function undo(): void
    {
        if (empty($this->history)) {
            echo "\n[Controller] Nothing to undo.\n";
            return;
        }
        $command = array_pop($this->history);
        echo "\n[UNDO] Reversing: " . $command->getDescription() . "\n";
        $command->undo();
    }

    public function printHistory(): void
    {
        echo "\n[Controller] Action history:\n";
        foreach ($this->history as $i => $cmd) {
            echo '  ' . ($i + 1) . '. ' . $cmd->getDescription() . "\n";
        }
    }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

$cart       = new ShoppingCart();
$controller = new CartController($cart);

echo "=== E-Commerce Cart Demo ===\n";

$controller->execute(new AddItemCommand($cart, 'SKU-001', 'Wireless Headphones', 79.99));
$controller->execute(new AddItemCommand($cart, 'SKU-002', 'USB-C Hub',          34.99, 2));
$controller->execute(new AddItemCommand($cart, 'SKU-003', 'Laptop Stand',       49.99));
$controller->execute(new ApplyCouponCommand($cart, 'SAVE15', 15.0));

$cart->printSummary();

echo "\n--- Undo coupon ---\n";
$controller->undo();
$cart->printSummary();

echo "\n--- Undo adding laptop stand ---\n";
$controller->undo();

echo "\n--- Remove 1 USB-C Hub ---\n";
$controller->execute(new RemoveItemCommand($cart, 'SKU-002', 'USB-C Hub', 34.99, 1));

echo "\n--- Undo the removal ---\n";
$controller->undo();

$cart->printSummary();
$controller->printHistory();
```

---

### Ruby

```ruby
# Command Pattern — Home Automation with Scheduled Scenes
#
# Real-world scenario: A smart home app where "scenes" are macro commands
# composed of individual device actions. Scenes can be triggered on a
# schedule and undone if a mistake is made.

# ---------------------------------------------------------------------------
# Command interface (mixin)
# ---------------------------------------------------------------------------
module Command
  def execute
    raise NotImplementedError, "#{self.class}#execute not implemented"
  end

  def undo
    raise NotImplementedError, "#{self.class}#undo not implemented"
  end

  def description
    self.class.name
  end
end

# ---------------------------------------------------------------------------
# Receivers — smart home devices
# ---------------------------------------------------------------------------
class SmartLight
  attr_reader :name, :on, :brightness, :color

  def initialize(name)
    @name       = name
    @on         = false
    @brightness = 100
    @color      = "white"
  end

  def turn_on
    @on = true
    puts "  [#{@name}] ON (#{@brightness}% #{@color})"
  end

  def turn_off
    @on = false
    puts "  [#{@name}] OFF"
  end

  def set_brightness(level)
    @brightness = level
    puts "  [#{@name}] Brightness -> #{level}%"
  end

  def set_color(color)
    @color = color
    puts "  [#{@name}] Color -> #{color}"
  end
end

class SmartSpeaker
  attr_reader :playing, :volume, :track

  def initialize(name)
    @name    = name
    @playing = false
    @volume  = 50
    @track   = nil
  end

  def play(track)
    @playing = true
    @track   = track
    puts "  [#{@name}] Playing: #{track} @ vol #{@volume}"
  end

  def stop
    @playing = false
    puts "  [#{@name}] Stopped"
  end

  def set_volume(level)
    @volume = level
    puts "  [#{@name}] Volume -> #{level}"
  end
end

class Thermostat
  attr_reader :temperature

  def initialize
    @temperature = 20
  end

  def set_temperature(temp)
    @temperature = temp
    puts "  [Thermostat] Temperature -> #{temp}°C"
  end
end

# ---------------------------------------------------------------------------
# Concrete Commands
# ---------------------------------------------------------------------------
class LightOnCommand
  include Command

  def initialize(light)
    @light          = light
    @previous_state = nil
  end

  def execute
    @previous_state = { on: @light.on, brightness: @light.brightness }
    @light.turn_on
  end

  def undo
    if @previous_state && !@previous_state[:on]
      @light.turn_off
    end
  end

  def description = "Turn #{@light.name} ON"
end

class LightColorCommand
  include Command

  def initialize(light, color, brightness)
    @light      = light
    @color      = color
    @brightness = brightness
    @prev_color = nil
    @prev_bright = nil
  end

  def execute
    @prev_color  = @light.color
    @prev_bright = @light.brightness
    @light.set_color(@color)
    @light.set_brightness(@brightness)
  end

  def undo
    @light.set_color(@prev_color)   if @prev_color
    @light.set_brightness(@prev_bright) if @prev_bright
  end

  def description = "Set #{@light.name} to #{@color} @ #{@brightness}%"
end

class SpeakerPlayCommand
  include Command

  def initialize(speaker, track, volume)
    @speaker     = speaker
    @track       = track
    @volume      = volume
    @prev_playing = false
    @prev_track   = nil
    @prev_volume  = nil
  end

  def execute
    @prev_playing = @speaker.playing
    @prev_track   = @speaker.track
    @prev_volume  = @speaker.volume
    @speaker.set_volume(@volume)
    @speaker.play(@track)
  end

  def undo
    if !@prev_playing
      @speaker.stop
    else
      @speaker.set_volume(@prev_volume)
      @speaker.play(@prev_track)
    end
  end

  def description = "Play '#{@track}' on speaker"
end

class ThermostatCommand
  include Command

  def initialize(thermostat, temperature)
    @thermostat  = thermostat
    @temperature = temperature
    @prev_temp   = nil
  end

  def execute
    @prev_temp = @thermostat.temperature
    @thermostat.set_temperature(@temperature)
  end

  def undo
    @thermostat.set_temperature(@prev_temp) if @prev_temp
  end

  def description = "Set thermostat to #{@temperature}°C"
end

# Composite: a "scene" groups multiple commands
class Scene
  include Command

  attr_reader :name

  def initialize(name, *commands)
    @name     = name
    @commands = commands
  end

  def execute
    puts "  [Scene: #{@name}] Activating..."
    @commands.each(&:execute)
  end

  def undo
    puts "  [Scene: #{@name}] Deactivating..."
    @commands.reverse_each(&:undo)
  end

  def description = "Scene: #{@name}"
end

# ---------------------------------------------------------------------------
# Invoker — smart home hub with history and scheduling
# ---------------------------------------------------------------------------
class SmartHub
  def initialize
    @history  = []
    @schedule = {} # time_key -> Command
  end

  def run(command)
    puts "\n[Hub] #{command.description}"
    command.execute
    @history.push(command)
  end

  def undo_last
    if @history.empty?
      puts "\n[Hub] Nothing to undo."
      return
    end
    cmd = @history.pop
    puts "\n[Hub UNDO] #{cmd.description}"
    cmd.undo
  end

  def schedule_at(time_label, command)
    @schedule[time_label] = command
    puts "[Hub] Scheduled '#{command.description}' at #{time_label}"
  end

  def trigger_scheduled(time_label)
    cmd = @schedule[time_label]
    if cmd
      puts "\n[Hub] Triggering scheduled: #{time_label}"
      run(cmd)
    else
      puts "[Hub] No command scheduled at #{time_label}"
    end
  end

  def history_log
    puts "\n[Hub] Command history:"
    @history.each_with_index { |cmd, i| puts "  #{i + 1}. #{cmd.description}" }
  end
end

# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
living_light  = SmartLight.new("Living Room Light")
bedroom_light = SmartLight.new("Bedroom Light")
speaker       = SmartSpeaker.new("Sonos One")
thermostat    = Thermostat.new

hub = SmartHub.new

puts "=== Smart Home Hub Demo ===\n"

# Define scenes
movie_scene = Scene.new("Movie Night",
  LightColorCommand.new(living_light, "warm amber", 20),
  LightOnCommand.new(living_light),
  ThermostatCommand.new(thermostat, 21),
  SpeakerPlayCommand.new(speaker, "Cinematic Ambience", 30)
)

morning_scene = Scene.new("Good Morning",
  LightColorCommand.new(living_light, "cool white", 100),
  LightOnCommand.new(living_light),
  ThermostatCommand.new(thermostat, 20),
  SpeakerPlayCommand.new(speaker, "Morning Mix", 50)
)

# Schedule scenes
hub.schedule_at("07:00", morning_scene)
hub.schedule_at("20:00", movie_scene)

# Trigger manually
hub.trigger_scheduled("07:00")
hub.trigger_scheduled("20:00")

puts "\n--- Undo Movie Night scene ---"
hub.undo_last

hub.history_log
```

---

## When To Use

Use the Command pattern when:

- **Parametrizing objects with operations.** You need to pass operations as arguments to other methods, store them in data structures, or dynamically swap behaviors at runtime (e.g., assigning different actions to toolbar buttons).

- **Queuing, scheduling, or remote execution.** Operations need to be placed into a job queue, executed at a specific time, sent to a remote service, or serialized and persisted to disk (e.g., a task queue, a cron-like scheduler, or a transactional log).

- **Implementing reversible operations (undo/redo).** Your application requires undo/redo. By saving a history of executed Command objects (and optionally saving state snapshots inside them), you can reverse any action. Most text editors, photo editors, and IDEs implement undo this way.

- **Implementing transactional behavior.** A sequence of operations must succeed as a whole. If any step fails, all previous steps must be rolled back — as in database migration systems or multi-step API workflows.

- **Logging and auditing.** You need a durable log of every action taken, with the ability to replay them — for example, replaying operations after a system crash or auditing changes for compliance.

**Do NOT use** when operations are simple, one-off, and never need to be queued, undone, or passed around — the extra indirection adds complexity without benefit.

---

## Pros & Cons

### Pros

| Benefit                         | Detail                                                                                                            |
|---------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Single Responsibility**       | Request logic is decoupled from sending and receiving objects. Each class does one thing.                         |
| **Open/Closed Principle**       | Add new commands without modifying existing senders or receivers.                                                 |
| **Undo/Redo**                   | Commands can store the state needed to reverse themselves, enabling arbitrarily deep history stacks.              |
| **Deferred / Queued Execution** | Commands are objects — they can be serialized, stored in a queue, and executed later or remotely.                 |
| **Composability (Macros)**      | Combine simple commands into complex composite commands (the Composite design pattern applied to commands).        |
| **Logging & Replay**            | Persist the command log; replay it to reconstruct state after a crash or for auditing.                            |

### Cons

| Drawback                       | Detail                                                                                                             |
|--------------------------------|--------------------------------------------------------------------------------------------------------------------|
| **Increased complexity**       | Introduces a new layer of classes between senders and receivers. Simple operations may not justify the overhead.   |
| **Class proliferation**        | Each distinct operation becomes its own class, which can lead to many small classes in large systems.              |
| **Undo state management**      | Storing enough state to support undo can be tricky; deep object graphs may require Memento for correct snapshots.  |

---

## Relations to Other Patterns

| Pattern                  | Relationship                                                                                                                                      |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| **Chain of Responsibility** | Both route requests, but CoR passes the request along a chain until a handler consumes it; Command maps a request to a single specific handler. |
| **Memento**              | Used together with Command to implement undo: Command performs the action; Memento saves the receiver's pre-action state for rollback.            |
| **Observer**             | Observers can trigger Commands in response to events, separating event notification from the action taken.                                        |
| **Prototype**            | Command history requires storing copies of commands. Commands that are complex objects can be cloned with Prototype before being pushed to history.|
| **Strategy**             | Both encapsulate an algorithm behind an interface, but Strategy varies *how* something is done; Command encapsulates *what* is done (the request itself), who does it, and when. Strategy objects rarely need undo; Command objects often do. |
| **Visitor**              | Both represent operations on objects. Visitor is designed to apply an operation across an object structure; Command wraps a single request for deferred, undoable, or queued execution. |
| **Composite**            | Macro commands are Composite Commands — a tree of Commands that execute as one unit, applying the Composite structural pattern to behavioral commands. |

---

## Sources

- https://refactoring.guru/design-patterns/command
- https://sourcemaking.com/design_patterns/command
