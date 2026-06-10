# State Pattern

**Category:** Behavioral  
**Also Known As:** Objects for States

---

## Intent

Lets an object alter its behavior when its internal state changes. The object will appear to change its class at runtime, because the behavior it exposes changes completely depending on which state object it is currently delegating to.

---

## Problem It Solves

Consider a vending machine, a traffic light, a TCP connection, or a document workflow. Each of these entities has a fixed set of states, and the operations they support behave differently in each state. The naive implementation handles this with cascading `if/else` or `switch` blocks scattered across every method:

```
// Naive approach — every method checks state manually
void insertCoin() {
    if (state == IDLE)        { ... }
    else if (state == HAS_COIN) { ... }
    else if (state == SOLD)    { ... }
    else if (state == EMPTY)   { ... }
}
```

Problems that arise:

- Adding a new state requires modifying **every** method that inspects the state flag.
- The context class grows into a monolith; individual state behaviors are invisible.
- Testing one state in isolation is difficult because all states live in the same class.
- The Open/Closed Principle is violated on every state change.

The State pattern eliminates all of these issues.

---

## Solution

Extract each state's behavior into its own class that implements a common `State` interface. The **Context** holds a reference to the current state object and delegates all state-sensitive calls to it. State objects may themselves trigger transitions by swapping the context's current state reference.

The calling code never sees the state switch; it always talks to the context through a stable interface.

---

## Structure

```
┌─────────────────────────────┐
│          Client             │
└─────────────┬───────────────┘
              │ uses
              ▼
┌─────────────────────────────┐        ┌──────────────────────┐
│          Context            │───────>│      <<State>>       │
│─────────────────────────────│        │──────────────────────│
│ - state: State              │        │ + handle(ctx)        │
│─────────────────────────────│        └──────────┬───────────┘
│ + request()                 │                   │ implements
│ + setState(s: State)        │         ┌─────────┴──────────┐
└─────────────────────────────┘         │                    │
                                ┌───────────────┐  ┌─────────────────┐
                                │ ConcreteStateA│  │ ConcreteStateB  │
                                │───────────────│  │─────────────────│
                                │ + handle(ctx) │  │ + handle(ctx)   │
                                └───────────────┘  └─────────────────┘
                                        │                    │
                                        └────────────────────┘
                                   (each may call ctx.setState()
                                    to trigger a transition)
```

**Key relationships:**

- `Context` aggregates one `State` at a time.
- `ConcreteState` classes know about the `Context` so they can trigger transitions.
- States can optionally know about other states (for transition targets) — or the context itself decides transitions.

---

## Participants

| Participant | Responsibility |
|---|---|
| **Context** | Maintains an instance of a `ConcreteState` subclass. Provides a `setState()` method (or equivalent) so state objects can change the current state. Delegates all state-sensitive requests to the current state. |
| **State** | Defines an interface for encapsulating the behavior associated with a particular state of the Context. |
| **ConcreteState** | Implements the behavior associated with one state of the Context. Each subclass knows how to handle the context's requests in its particular state and may trigger transitions. |

---

## How It Works

1. **Context is created** with an initial state (e.g., `IdleState`).
2. **Client calls a method** on the context (e.g., `context.insertCoin()`).
3. **Context delegates** the call to `currentState.insertCoin(this)`.
4. **ConcreteState handles** the request according to its own logic. It may:
   - Perform work and remain in the same state.
   - Call `context.setState(new OtherState())` to trigger a transition.
5. **Client calls the next method**; the context now delegates to the new state — different behavior, same context object.
6. Transitions can be triggered **by the state itself** (internal) or **by the context** based on state return values (external). Both styles are valid.

---

## Code Examples

### Python

```python
"""
Vending Machine — State Pattern (Python)

Models a simple vending machine with four states:
  Idle -> HasCoin -> Sold -> [back to Idle or SoldOut]

Run:  python vending_machine.py
"""

from __future__ import annotations
from abc import ABC, abstractmethod


# ---------------------------------------------------------------------------
# State interface
# ---------------------------------------------------------------------------

class VendingState(ABC):
    """Abstract base for all vending machine states."""

    @abstractmethod
    def insert_coin(self, machine: VendingMachine) -> None: ...

    @abstractmethod
    def eject_coin(self, machine: VendingMachine) -> None: ...

    @abstractmethod
    def select_item(self, machine: VendingMachine) -> None: ...

    @abstractmethod
    def dispense(self, machine: VendingMachine) -> None: ...

    def __str__(self) -> str:
        return self.__class__.__name__


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

class VendingMachine:
    """
    Context: delegates every user action to the current state object.
    """

    def __init__(self, item_count: int) -> None:
        self._idle_state = IdleState()
        self._has_coin_state = HasCoinState()
        self._sold_state = SoldState()
        self._sold_out_state = SoldOutState()

        self._item_count = item_count
        self._state: VendingState = self._sold_out_state if item_count == 0 else self._idle_state

    # --- public actions (delegated to current state) ---

    def insert_coin(self) -> None:
        print(f"[{self._state}] User inserts coin.")
        self._state.insert_coin(self)

    def eject_coin(self) -> None:
        print(f"[{self._state}] User ejects coin.")
        self._state.eject_coin(self)

    def select_item(self) -> None:
        print(f"[{self._state}] User selects item.")
        self._state.select_item(self)
        self._state.dispense(self)

    # --- state transition ---

    def set_state(self, state: VendingState) -> None:
        self._state = state

    # --- accessors used by states ---

    def release_item(self) -> None:
        if self._item_count > 0:
            self._item_count -= 1
            print("  >> Item dispensed! Enjoy.")

    @property
    def item_count(self) -> int:
        return self._item_count

    # --- convenient state references ---

    @property
    def idle_state(self) -> VendingState:
        return self._idle_state

    @property
    def has_coin_state(self) -> VendingState:
        return self._has_coin_state

    @property
    def sold_state(self) -> VendingState:
        return self._sold_state

    @property
    def sold_out_state(self) -> VendingState:
        return self._sold_out_state

    def __str__(self) -> str:
        return (
            f"VendingMachine(items={self._item_count}, "
            f"state={self._state})"
        )


# ---------------------------------------------------------------------------
# Concrete States
# ---------------------------------------------------------------------------

class IdleState(VendingState):
    """Machine is waiting — no coin inserted yet."""

    def insert_coin(self, machine: VendingMachine) -> None:
        print("  Coin accepted.")
        machine.set_state(machine.has_coin_state)

    def eject_coin(self, machine: VendingMachine) -> None:
        print("  No coin to eject.")

    def select_item(self, machine: VendingMachine) -> None:
        print("  Please insert a coin first.")

    def dispense(self, machine: VendingMachine) -> None:
        print("  No item dispensed — insert a coin.")


class HasCoinState(VendingState):
    """A coin has been inserted; waiting for item selection."""

    def insert_coin(self, machine: VendingMachine) -> None:
        print("  Coin already inserted. Only one coin accepted.")

    def eject_coin(self, machine: VendingMachine) -> None:
        print("  Coin returned.")
        machine.set_state(machine.idle_state)

    def select_item(self, machine: VendingMachine) -> None:
        print("  Item selected — dispensing...")
        machine.set_state(machine.sold_state)

    def dispense(self, machine: VendingMachine) -> None:
        print("  Select an item first.")


class SoldState(VendingState):
    """Item is being dispensed."""

    def insert_coin(self, machine: VendingMachine) -> None:
        print("  Please wait — dispensing in progress.")

    def eject_coin(self, machine: VendingMachine) -> None:
        print("  Cannot eject — already dispensing.")

    def select_item(self, machine: VendingMachine) -> None:
        print("  Already dispensing. Please wait.")

    def dispense(self, machine: VendingMachine) -> None:
        machine.release_item()
        if machine.item_count > 0:
            machine.set_state(machine.idle_state)
        else:
            print("  Machine is now empty.")
            machine.set_state(machine.sold_out_state)


class SoldOutState(VendingState):
    """No items remaining."""

    def insert_coin(self, machine: VendingMachine) -> None:
        print("  Machine is sold out. Coin returned.")

    def eject_coin(self, machine: VendingMachine) -> None:
        print("  No coin inserted.")

    def select_item(self, machine: VendingMachine) -> None:
        print("  Machine is sold out.")

    def dispense(self, machine: VendingMachine) -> None:
        print("  No items to dispense.")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    machine = VendingMachine(item_count=2)
    print(machine)

    print("\n--- Normal purchase ---")
    machine.insert_coin()
    machine.select_item()
    print(machine)

    print("\n--- Eject coin before selecting ---")
    machine.insert_coin()
    machine.eject_coin()

    print("\n--- Second purchase (empties machine) ---")
    machine.insert_coin()
    machine.select_item()
    print(machine)

    print("\n--- Try to use empty machine ---")
    machine.insert_coin()
```

---

### Java

```java
/**
 * TCP Connection — State Pattern (Java)
 *
 * Models the classic TCP state machine with three states:
 *   Closed -> Listen -> Established -> Closed
 *
 * Compile:  javac *.java
 * Run:      java TcpDemo
 */

// --- State interface ---

interface TcpState {
    void open(TcpConnection connection);
    void close(TcpConnection connection);
    void acknowledge(TcpConnection connection);
}

// --- Context ---

class TcpConnection {
    private TcpState state;

    // Keep references to all concrete states (flyweight style)
    private final TcpState closed      = new TcpClosed();
    private final TcpState listening   = new TcpListen();
    private final TcpState established = new TcpEstablished();

    public TcpConnection() {
        this.state = closed;
    }

    public void open()        { state.open(this); }
    public void close()       { state.close(this); }
    public void acknowledge() { state.acknowledge(this); }

    // Package-visible so concrete states can transition
    void setState(TcpState newState) {
        System.out.printf("  Transition: %s -> %s%n",
            state.getClass().getSimpleName(),
            newState.getClass().getSimpleName());
        this.state = newState;
    }

    TcpState getClosedState()      { return closed; }
    TcpState getListeningState()   { return listening; }
    TcpState getEstablishedState() { return established; }

    @Override
    public String toString() {
        return "TcpConnection[state=" + state.getClass().getSimpleName() + "]";
    }
}

// --- Concrete States ---

class TcpClosed implements TcpState {
    @Override
    public void open(TcpConnection conn) {
        System.out.println("  Socket opened — now listening for connections.");
        conn.setState(conn.getListeningState());
    }

    @Override
    public void close(TcpConnection conn) {
        System.out.println("  Connection already closed.");
    }

    @Override
    public void acknowledge(TcpConnection conn) {
        System.out.println("  Cannot acknowledge — connection is closed.");
    }
}

class TcpListen implements TcpState {
    @Override
    public void open(TcpConnection conn) {
        System.out.println("  Already listening.");
    }

    @Override
    public void close(TcpConnection conn) {
        System.out.println("  Stopped listening — socket closed.");
        conn.setState(conn.getClosedState());
    }

    @Override
    public void acknowledge(TcpConnection conn) {
        System.out.println("  SYN received — connection established.");
        conn.setState(conn.getEstablishedState());
    }
}

class TcpEstablished implements TcpState {
    @Override
    public void open(TcpConnection conn) {
        System.out.println("  Connection already established.");
    }

    @Override
    public void close(TcpConnection conn) {
        System.out.println("  FIN sent — connection closing.");
        conn.setState(conn.getClosedState());
    }

    @Override
    public void acknowledge(TcpConnection conn) {
        System.out.println("  ACK received — data transfer in progress.");
    }
}

// --- Demo ---

class TcpDemo {
    public static void main(String[] args) {
        TcpConnection conn = new TcpConnection();
        System.out.println(conn);

        System.out.println("\n--- Open connection ---");
        conn.open();
        System.out.println(conn);

        System.out.println("\n--- Client acknowledges (SYN-ACK) ---");
        conn.acknowledge();
        System.out.println(conn);

        System.out.println("\n--- Transfer data ---");
        conn.acknowledge();

        System.out.println("\n--- Close connection ---");
        conn.close();
        System.out.println(conn);

        System.out.println("\n--- Try to acknowledge on closed connection ---");
        conn.acknowledge();
    }
}
```

---

### C++

```cpp
/**
 * Traffic Light — State Pattern (C++)
 *
 * Simulates a traffic light cycling Red -> Green -> Yellow -> Red.
 * Each state knows its successor and triggers the transition automatically
 * after a specified duration (simulated here with a tick counter).
 *
 * Compile: g++ -std=c++17 -o traffic traffic_light.cpp
 */

#include <iostream>
#include <memory>
#include <string>

class TrafficLight;  // forward declaration

// ---------------------------------------------------------------------------
// State interface
// ---------------------------------------------------------------------------
class LightState {
public:
    virtual ~LightState() = default;
    virtual void enter(TrafficLight& light) = 0;   // called on transition in
    virtual void tick(TrafficLight& light) = 0;    // called each simulation step
    virtual std::string name() const = 0;
};

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------
class TrafficLight {
public:
    explicit TrafficLight(std::unique_ptr<LightState> initial);

    void setState(std::unique_ptr<LightState> newState);
    void tick();
    std::string currentStateName() const { return state_->name(); }

private:
    std::unique_ptr<LightState> state_;
};

// ---------------------------------------------------------------------------
// Concrete States (forward-declared implementations below)
// ---------------------------------------------------------------------------
class RedState;
class GreenState;
class YellowState;

// ---------------------------------------------------------------------------
// RedState: stops traffic; transitions to Green after 3 ticks
// ---------------------------------------------------------------------------
class RedState : public LightState {
public:
    void enter(TrafficLight& light) override {
        ticks_ = 0;
        std::cout << "  [RED]    Stop! Waiting for " << kDuration << " ticks.\n";
    }

    void tick(TrafficLight& light) override;  // defined after GreenState

    std::string name() const override { return "Red"; }

private:
    static constexpr int kDuration = 3;
    int ticks_ = 0;
};

// ---------------------------------------------------------------------------
// GreenState: allows traffic; transitions to Yellow after 4 ticks
// ---------------------------------------------------------------------------
class GreenState : public LightState {
public:
    void enter(TrafficLight& light) override {
        ticks_ = 0;
        std::cout << "  [GREEN]  Go! Allowing traffic for " << kDuration << " ticks.\n";
    }

    void tick(TrafficLight& light) override;

    std::string name() const override { return "Green"; }

private:
    static constexpr int kDuration = 4;
    int ticks_ = 0;
};

// ---------------------------------------------------------------------------
// YellowState: caution; transitions to Red after 1 tick
// ---------------------------------------------------------------------------
class YellowState : public LightState {
public:
    void enter(TrafficLight& light) override {
        ticks_ = 0;
        std::cout << "  [YELLOW] Caution! Preparing to stop.\n";
    }

    void tick(TrafficLight& light) override;

    std::string name() const override { return "Yellow"; }

private:
    static constexpr int kDuration = 1;
    int ticks_ = 0;
};

// ---------------------------------------------------------------------------
// TrafficLight implementation
// ---------------------------------------------------------------------------
TrafficLight::TrafficLight(std::unique_ptr<LightState> initial)
    : state_(std::move(initial)) {
    state_->enter(*this);
}

void TrafficLight::setState(std::unique_ptr<LightState> newState) {
    state_ = std::move(newState);
    state_->enter(*this);
}

void TrafficLight::tick() {
    state_->tick(*this);
}

// ---------------------------------------------------------------------------
// tick() implementations (need full type visibility)
// ---------------------------------------------------------------------------
void RedState::tick(TrafficLight& light) {
    if (++ticks_ >= kDuration) {
        light.setState(std::make_unique<GreenState>());
    }
}

void GreenState::tick(TrafficLight& light) {
    if (++ticks_ >= kDuration) {
        light.setState(std::make_unique<YellowState>());
    }
}

void YellowState::tick(TrafficLight& light) {
    if (++ticks_ >= kDuration) {
        light.setState(std::make_unique<RedState>());
    }
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------
int main() {
    TrafficLight light(std::make_unique<RedState>());

    std::cout << "\nRunning 18 simulation ticks:\n";
    for (int tick = 1; tick <= 18; ++tick) {
        std::cout << "Tick " << tick << " (current: " << light.currentStateName() << ")\n";
        light.tick();
    }

    return 0;
}
```

---

### C#

```csharp
/**
 * Document Workflow — State Pattern (C#)
 *
 * Models a document moving through an editorial pipeline:
 *   Draft -> ModerationReview -> Published  (or back to Draft)
 *
 * Run:  dotnet script document_workflow.cs
 *       -- or compile as a standard console application.
 */

using System;

namespace StatePattern
{
    // -----------------------------------------------------------------------
    // State interface
    // -----------------------------------------------------------------------
    public interface IDocumentState
    {
        void Edit(DocumentContext doc);
        void Submit(DocumentContext doc);
        void Approve(DocumentContext doc);
        void Reject(DocumentContext doc);
        void Publish(DocumentContext doc);
    }

    // -----------------------------------------------------------------------
    // Context
    // -----------------------------------------------------------------------
    public class DocumentContext
    {
        private IDocumentState _state;

        public string Title { get; }
        public string Content { get; set; }

        public DocumentContext(string title, string content)
        {
            Title   = title;
            Content = content;
            _state  = new DraftState();
            Console.WriteLine($"Document '{Title}' created in state: {_state.GetType().Name}");
        }

        public void TransitionTo(IDocumentState newState)
        {
            Console.WriteLine($"  >> Transition: {_state.GetType().Name} -> {newState.GetType().Name}");
            _state = newState;
        }

        // Actions delegated to current state
        public void Edit()    => _state.Edit(this);
        public void Submit()  => _state.Submit(this);
        public void Approve() => _state.Approve(this);
        public void Reject()  => _state.Reject(this);
        public void Publish() => _state.Publish(this);

        public override string ToString() =>
            $"Document['{Title}', state={_state.GetType().Name}]";
    }

    // -----------------------------------------------------------------------
    // Concrete States
    // -----------------------------------------------------------------------

    /// <summary>Author is writing or editing.</summary>
    public class DraftState : IDocumentState
    {
        public void Edit(DocumentContext doc)
        {
            Console.WriteLine("  Editing document content...");
        }

        public void Submit(DocumentContext doc)
        {
            Console.WriteLine("  Document submitted for moderation.");
            doc.TransitionTo(new ModerationState());
        }

        public void Approve(DocumentContext doc) =>
            Console.WriteLine("  Cannot approve — document is in draft.");

        public void Reject(DocumentContext doc) =>
            Console.WriteLine("  Nothing to reject — document is in draft.");

        public void Publish(DocumentContext doc) =>
            Console.WriteLine("  Cannot publish — document has not been reviewed.");
    }

    /// <summary>Document is under editorial review.</summary>
    public class ModerationState : IDocumentState
    {
        public void Edit(DocumentContext doc) =>
            Console.WriteLine("  Cannot edit — document is under moderation.");

        public void Submit(DocumentContext doc) =>
            Console.WriteLine("  Already submitted for moderation.");

        public void Approve(DocumentContext doc)
        {
            Console.WriteLine("  Document approved by moderator.");
            doc.TransitionTo(new ApprovedState());
        }

        public void Reject(DocumentContext doc)
        {
            Console.WriteLine("  Document rejected — returned to draft.");
            doc.TransitionTo(new DraftState());
        }

        public void Publish(DocumentContext doc) =>
            Console.WriteLine("  Cannot publish directly — must be approved first.");
    }

    /// <summary>Moderation passed; ready to publish.</summary>
    public class ApprovedState : IDocumentState
    {
        public void Edit(DocumentContext doc) =>
            Console.WriteLine("  Cannot edit an approved document — reject it first.");

        public void Submit(DocumentContext doc) =>
            Console.WriteLine("  Already approved.");

        public void Approve(DocumentContext doc) =>
            Console.WriteLine("  Already approved.");

        public void Reject(DocumentContext doc)
        {
            Console.WriteLine("  Approval revoked — document returned to draft.");
            doc.TransitionTo(new DraftState());
        }

        public void Publish(DocumentContext doc)
        {
            Console.WriteLine("  Document published successfully!");
            doc.TransitionTo(new PublishedState());
        }
    }

    /// <summary>Publicly available; read-only.</summary>
    public class PublishedState : IDocumentState
    {
        public void Edit(DocumentContext doc) =>
            Console.WriteLine("  Cannot edit a published document. Unpublish first.");

        public void Submit(DocumentContext doc) =>
            Console.WriteLine("  Already published.");

        public void Approve(DocumentContext doc) =>
            Console.WriteLine("  Already published.");

        public void Reject(DocumentContext doc) =>
            Console.WriteLine("  Cannot reject — document is live.");

        public void Publish(DocumentContext doc) =>
            Console.WriteLine("  Already published.");
    }

    // -----------------------------------------------------------------------
    // Demo
    // -----------------------------------------------------------------------
    class Program
    {
        static void Main()
        {
            var doc = new DocumentContext("Annual Report 2026", "Initial draft content.");

            Console.WriteLine("\n--- Author edits and submits ---");
            doc.Edit();
            doc.Submit();
            Console.WriteLine(doc);

            Console.WriteLine("\n--- Moderator rejects ---");
            doc.Reject();
            Console.WriteLine(doc);

            Console.WriteLine("\n--- Author revises and resubmits ---");
            doc.Edit();
            doc.Submit();

            Console.WriteLine("\n--- Moderator approves ---");
            doc.Approve();
            Console.WriteLine(doc);

            Console.WriteLine("\n--- Publish ---");
            doc.Publish();
            Console.WriteLine(doc);

            Console.WriteLine("\n--- Try to edit published document ---");
            doc.Edit();
        }
    }
}
```

---

### TypeScript

```typescript
/**
 * Order Fulfillment — State Pattern (TypeScript)
 *
 * Tracks an e-commerce order through:
 *   Pending -> Processing -> Shipped -> Delivered  (or Cancelled from early states)
 *
 * Run:  ts-node order_fulfillment.ts
 *       (or compile with tsc and run with node)
 */

// ---------------------------------------------------------------------------
// State interface
// ---------------------------------------------------------------------------
interface OrderState {
  confirm(order: Order): void;
  cancel(order: Order): void;
  ship(order: Order): void;
  deliver(order: Order): void;
  getLabel(): string;
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------
class Order {
  private state: OrderState;
  public readonly id: string;
  public readonly items: string[];

  constructor(id: string, items: string[]) {
    this.id = id;
    this.items = items;
    this.state = new PendingState();
    console.log(`Order ${this.id} created. State: ${this.state.getLabel()}`);
  }

  transitionTo(state: OrderState): void {
    console.log(
      `  [Order ${this.id}] ${this.state.getLabel()} -> ${state.getLabel()}`
    );
    this.state = state;
  }

  // Delegated actions
  confirm(): void  { this.state.confirm(this); }
  cancel(): void   { this.state.cancel(this); }
  ship(): void     { this.state.ship(this); }
  deliver(): void  { this.state.deliver(this); }

  status(): string {
    return `Order[${this.id}] | Status: ${this.state.getLabel()} | Items: ${this.items.join(', ')}`;
  }
}

// ---------------------------------------------------------------------------
// Concrete States
// ---------------------------------------------------------------------------

class PendingState implements OrderState {
  confirm(order: Order): void {
    console.log('  Payment confirmed — order moved to processing.');
    order.transitionTo(new ProcessingState());
  }

  cancel(order: Order): void {
    console.log('  Order cancelled before confirmation.');
    order.transitionTo(new CancelledState());
  }

  ship(order: Order): void {
    console.log('  Cannot ship — order not yet confirmed.');
  }

  deliver(order: Order): void {
    console.log('  Cannot deliver — order not yet confirmed.');
  }

  getLabel(): string { return 'Pending'; }
}

class ProcessingState implements OrderState {
  confirm(order: Order): void {
    console.log('  Order already confirmed and processing.');
  }

  cancel(order: Order): void {
    console.log('  Order cancelled during processing — refund initiated.');
    order.transitionTo(new CancelledState());
  }

  ship(order: Order): void {
    console.log('  Order packed and handed to courier.');
    order.transitionTo(new ShippedState());
  }

  deliver(order: Order): void {
    console.log('  Cannot deliver — order not yet shipped.');
  }

  getLabel(): string { return 'Processing'; }
}

class ShippedState implements OrderState {
  confirm(order: Order): void {
    console.log('  Order already confirmed.');
  }

  cancel(order: Order): void {
    console.log('  Cannot cancel — order already shipped. Initiate a return instead.');
  }

  ship(order: Order): void {
    console.log('  Order already shipped.');
  }

  deliver(order: Order): void {
    console.log('  Delivery confirmed by recipient.');
    order.transitionTo(new DeliveredState());
  }

  getLabel(): string { return 'Shipped'; }
}

class DeliveredState implements OrderState {
  confirm(order: Order): void {
    console.log('  Order complete — no further actions.');
  }

  cancel(order: Order): void {
    console.log('  Order delivered — cannot cancel. Please return the item.');
  }

  ship(order: Order): void {
    console.log('  Already delivered.');
  }

  deliver(order: Order): void {
    console.log('  Already delivered.');
  }

  getLabel(): string { return 'Delivered'; }
}

class CancelledState implements OrderState {
  confirm(order: Order): void {
    console.log('  Order was cancelled — cannot confirm.');
  }

  cancel(order: Order): void {
    console.log('  Already cancelled.');
  }

  ship(order: Order): void {
    console.log('  Order was cancelled — cannot ship.');
  }

  deliver(order: Order): void {
    console.log('  Order was cancelled — nothing to deliver.');
  }

  getLabel(): string { return 'Cancelled'; }
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

const order1 = new Order('ORD-001', ['Laptop', 'Mouse']);

console.log('\n--- Confirm and fulfil order ---');
order1.confirm();
order1.ship();
order1.deliver();
console.log(order1.status());

console.log('\n--- Attempt to cancel a delivered order ---');
order1.cancel();

const order2 = new Order('ORD-002', ['Headphones']);
console.log('\n--- Cancel order before confirmation ---');
order2.cancel();
console.log(order2.status());
order2.confirm(); // should fail gracefully
```

---

### Go

```go
// Turnstile — State Pattern (Go)
//
// Models a subway turnstile with two states: Locked and Unlocked.
// Events: coin insertion and arm push.
//
// Run: go run turnstile.go

package main

import "fmt"

// ---------------------------------------------------------------------------
// State interface
// ---------------------------------------------------------------------------

type TurnstileState interface {
	InsertCoin(t *Turnstile)
	Push(t *Turnstile)
	Name() string
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

type Turnstile struct {
	state    TurnstileState
	unlocked *UnlockedState
	locked   *LockedState
	coins    int
}

func NewTurnstile() *Turnstile {
	t := &Turnstile{
		unlocked: &UnlockedState{},
		locked:   &LockedState{},
	}
	t.state = t.locked // start locked
	return t
}

func (t *Turnstile) SetState(s TurnstileState) {
	fmt.Printf("  Transition: %s -> %s\n", t.state.Name(), s.Name())
	t.state = s
}

func (t *Turnstile) InsertCoin() {
	fmt.Printf("[%s] Coin inserted.\n", t.state.Name())
	t.state.InsertCoin(t)
}

func (t *Turnstile) Push() {
	fmt.Printf("[%s] Arm pushed.\n", t.state.Name())
	t.state.Push(t)
}

func (t *Turnstile) String() string {
	return fmt.Sprintf("Turnstile[state=%s, coins=%d]", t.state.Name(), t.coins)
}

// ---------------------------------------------------------------------------
// Concrete States
// ---------------------------------------------------------------------------

// LockedState — turnstile blocks passage; accepts coins.
type LockedState struct{}

func (s *LockedState) InsertCoin(t *Turnstile) {
	t.coins++
	fmt.Printf("  Coin accepted (total: %d). Turnstile unlocked.\n", t.coins)
	t.SetState(t.unlocked)
}

func (s *LockedState) Push(t *Turnstile) {
	fmt.Println("  Turnstile is locked. Please insert a coin.")
}

func (s *LockedState) Name() string { return "Locked" }

// UnlockedState — turnstile allows one passage.
type UnlockedState struct{}

func (s *UnlockedState) InsertCoin(t *Turnstile) {
	// Return coin — already unlocked
	fmt.Println("  Turnstile already unlocked. Coin returned.")
}

func (s *UnlockedState) Push(t *Turnstile) {
	fmt.Println("  Passage granted. Turnstile locks again.")
	t.SetState(t.locked)
}

func (s *UnlockedState) Name() string { return "Unlocked" }

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

func main() {
	t := NewTurnstile()
	fmt.Println(t)

	fmt.Println("\n--- Push locked turnstile ---")
	t.Push()

	fmt.Println("\n--- Insert coin ---")
	t.InsertCoin()
	fmt.Println(t)

	fmt.Println("\n--- Insert another coin while unlocked ---")
	t.InsertCoin()

	fmt.Println("\n--- Pass through ---")
	t.Push()
	fmt.Println(t)

	fmt.Println("\n--- Insert coin and pass twice ---")
	t.InsertCoin()
	t.Push()
	t.Push() // second push — locked again
}
```

---

### PHP

```php
<?php
/**
 * Bank Account — State Pattern (PHP)
 *
 * A bank account can be in one of three states:
 *   Active -> Overdrawn -> Frozen  (and back based on balance)
 *
 * Run:  php bank_account.php
 */

declare(strict_types=1);

// ---------------------------------------------------------------------------
// State interface
// ---------------------------------------------------------------------------

interface AccountState
{
    public function deposit(BankAccount $account, float $amount): void;
    public function withdraw(BankAccount $account, float $amount): void;
    public function freeze(BankAccount $account): void;
    public function getLabel(): string;
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

class BankAccount
{
    private AccountState $state;
    private float $balance;
    private string $owner;

    // Concrete state singletons held by the context
    private ActiveState    $activeState;
    private OverdrawnState $overdrawnState;
    private FrozenState    $frozenState;

    public function __construct(string $owner, float $initialBalance = 0.0)
    {
        $this->owner          = $owner;
        $this->balance        = $initialBalance;
        $this->activeState    = new ActiveState();
        $this->overdrawnState = new OverdrawnState();
        $this->frozenState    = new FrozenState();
        $this->state          = $this->activeState;

        echo "Account created for {$owner} with balance \${$initialBalance}.\n";
    }

    public function transitionTo(AccountState $state): void
    {
        echo "  >> State change: {$this->state->getLabel()} -> {$state->getLabel()}\n";
        $this->state = $state;
    }

    public function deposit(float $amount): void
    {
        echo "[{$this->state->getLabel()}] Deposit \${$amount}.\n";
        $this->state->deposit($this, $amount);
    }

    public function withdraw(float $amount): void
    {
        echo "[{$this->state->getLabel()}] Withdraw \${$amount}.\n";
        $this->state->withdraw($this, $amount);
    }

    public function freeze(): void
    {
        echo "[{$this->state->getLabel()}] Freeze account.\n";
        $this->state->freeze($this);
    }

    // Accessors used by states
    public function addToBalance(float $amount): void { $this->balance += $amount; }
    public function subtractFromBalance(float $amount): void { $this->balance -= $amount; }
    public function getBalance(): float { return $this->balance; }

    // State references
    public function getActiveState(): ActiveState       { return $this->activeState; }
    public function getOverdrawnState(): OverdrawnState { return $this->overdrawnState; }
    public function getFrozenState(): FrozenState       { return $this->frozenState; }

    public function __toString(): string
    {
        return "BankAccount[owner={$this->owner}, balance=\${$this->balance}, state={$this->state->getLabel()}]";
    }
}

// ---------------------------------------------------------------------------
// Concrete States
// ---------------------------------------------------------------------------

class ActiveState implements AccountState
{
    public function deposit(BankAccount $account, float $amount): void
    {
        $account->addToBalance($amount);
        echo "  Balance is now \${$account->getBalance()}.\n";
    }

    public function withdraw(BankAccount $account, float $amount): void
    {
        if ($amount > $account->getBalance()) {
            $account->subtractFromBalance($amount);
            echo "  Withdrawal causes overdraft. Balance: \${$account->getBalance()}.\n";
            $account->transitionTo($account->getOverdrawnState());
        } else {
            $account->subtractFromBalance($amount);
            echo "  Withdrawn. Balance: \${$account->getBalance()}.\n";
        }
    }

    public function freeze(BankAccount $account): void
    {
        echo "  Account frozen.\n";
        $account->transitionTo($account->getFrozenState());
    }

    public function getLabel(): string { return 'Active'; }
}

class OverdrawnState implements AccountState
{
    private const OVERDRAFT_FEE = 35.0;

    public function deposit(BankAccount $account, float $amount): void
    {
        $account->addToBalance($amount);
        echo "  Deposit received. Balance: \${$account->getBalance()}.\n";
        if ($account->getBalance() >= 0) {
            echo "  Account back in good standing.\n";
            $account->transitionTo($account->getActiveState());
        }
    }

    public function withdraw(BankAccount $account, float $amount): void
    {
        $fee = self::OVERDRAFT_FEE;
        echo "  Withdrawal denied (overdrawn). Overdraft fee of \${$fee} charged.\n";
        $account->subtractFromBalance($fee);
        echo "  Balance: \${$account->getBalance()}.\n";
    }

    public function freeze(BankAccount $account): void
    {
        echo "  Overdrawn account frozen due to inactivity.\n";
        $account->transitionTo($account->getFrozenState());
    }

    public function getLabel(): string { return 'Overdrawn'; }
}

class FrozenState implements AccountState
{
    public function deposit(BankAccount $account, float $amount): void
    {
        echo "  Account is frozen. Contact support to unfreeze.\n";
    }

    public function withdraw(BankAccount $account, float $amount): void
    {
        echo "  Account is frozen. Withdrawal denied.\n";
    }

    public function freeze(BankAccount $account): void
    {
        echo "  Account is already frozen.\n";
    }

    public function getLabel(): string { return 'Frozen'; }
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

$account = new BankAccount('Alice', 100.0);

echo "\n--- Normal deposit and withdrawal ---\n";
$account->deposit(50.0);
$account->withdraw(30.0);
echo $account . "\n";

echo "\n--- Overdraft scenario ---\n";
$account->withdraw(200.0);
echo $account . "\n";

echo "\n--- Try to withdraw while overdrawn ---\n";
$account->withdraw(10.0);

echo "\n--- Deposit to restore account ---\n";
$account->deposit(300.0);
echo $account . "\n";

echo "\n--- Freeze account ---\n";
$account->freeze();
$account->deposit(50.0);
echo $account . "\n";
```

---

### Ruby

```ruby
# Jukebox — State Pattern (Ruby)
#
# Models a jukebox that cycles through states:
#   Idle -> CoinInserted -> Playing -> Idle
#
# Run:  ruby jukebox.rb

# ---------------------------------------------------------------------------
# State base class (acts as interface with default "invalid" behaviour)
# ---------------------------------------------------------------------------

class JukeboxState
  def insert_coin(_jukebox)
    puts "  Action not valid in state: #{self.class.name}"
  end

  def select_song(_jukebox, _song)
    puts "  Action not valid in state: #{self.class.name}"
  end

  def song_finished(_jukebox)
    puts "  Action not valid in state: #{self.class.name}"
  end

  def eject_coin(_jukebox)
    puts "  Action not valid in state: #{self.class.name}"
  end

  def to_s
    self.class.name.gsub(/State$/, '')
  end
end

# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

class Jukebox
  attr_reader :current_song

  def initialize
    @idle_state         = IdleState.new
    @coin_inserted_state = CoinInsertedState.new
    @playing_state      = PlayingState.new

    @state        = @idle_state
    @current_song = nil
    puts "Jukebox ready. State: #{@state}"
  end

  def transition_to(state)
    puts "  [Jukebox] #{@state} -> #{state}"
    @state = state
  end

  def insert_coin
    puts "[#{@state}] insert_coin called."
    @state.insert_coin(self)
  end

  def select_song(song)
    puts "[#{@state}] select_song('#{song}') called."
    @state.select_song(self, song)
  end

  def song_finished
    puts "[#{@state}] song_finished called."
    @state.song_finished(self)
  end

  def eject_coin
    puts "[#{@state}] eject_coin called."
    @state.eject_coin(self)
  end

  def set_song(song)
    @current_song = song
  end

  # State references
  def idle_state          = @idle_state
  def coin_inserted_state = @coin_inserted_state
  def playing_state       = @playing_state

  def to_s
    "Jukebox[state=#{@state}, song=#{@current_song || 'none'}]"
  end
end

# ---------------------------------------------------------------------------
# Concrete States
# ---------------------------------------------------------------------------

class IdleState < JukeboxState
  def insert_coin(jukebox)
    puts "  Coin accepted!"
    jukebox.transition_to(jukebox.coin_inserted_state)
  end

  def eject_coin(_jukebox)
    puts "  No coin to eject."
  end
end

class CoinInsertedState < JukeboxState
  def insert_coin(_jukebox)
    puts "  Only one coin needed — coin returned."
  end

  def select_song(jukebox, song)
    puts "  '#{song}' selected — starting playback."
    jukebox.set_song(song)
    jukebox.transition_to(jukebox.playing_state)
  end

  def eject_coin(jukebox)
    puts "  Coin ejected."
    jukebox.transition_to(jukebox.idle_state)
  end
end

class PlayingState < JukeboxState
  def insert_coin(_jukebox)
    puts "  Already playing — coin returned."
  end

  def select_song(_jukebox, _song)
    puts "  Already playing. Please wait for current song to finish."
  end

  def song_finished(jukebox)
    puts "  '#{jukebox.current_song}' finished. Returning to idle."
    jukebox.set_song(nil)
    jukebox.transition_to(jukebox.idle_state)
  end
end

# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

box = Jukebox.new

puts "\n--- Normal play sequence ---"
box.insert_coin
box.select_song("Bohemian Rhapsody")
puts box
box.song_finished
puts box

puts "\n--- Eject coin before selecting ---"
box.insert_coin
box.eject_coin
puts box

puts "\n--- Try to select without coin ---"
box.select_song("Hotel California")

puts "\n--- Insert coin then try to insert again ---"
box.insert_coin
box.insert_coin
box.select_song("Stairway to Heaven")
box.song_finished
```

---

## When To Use

Use the State pattern when:

- **An object's behavior depends on its state** and it must change behavior at runtime depending on that state.
- **Operations have large, multi-part conditional statements** that depend on the object's state. These conditionals should be refactored into separate state classes.
- **States and transitions are numerous.** When you count more than three or four states, the conditional approach becomes unmanageable.
- **State-specific code changes frequently.** Isolating each state into its own class means changes to one state do not risk breaking another.
- **You need to model a finite state machine (FSM)** explicitly and keep it readable and extensible.

Do NOT use it when:

- The object has only two or three states that rarely change — a simple boolean or enum with a `switch` is perfectly readable and cheaper.
- The state transitions are trivially linear and will not grow.

---

## Pros & Cons

### Pros

| Benefit | Detail |
|---|---|
| **Single Responsibility Principle** | Each state's behavior lives in its own class, making it easy to locate and modify. |
| **Open/Closed Principle** | Add a new state without modifying existing states or the context — just create a new class. |
| **Eliminates conditionals** | Large `if/else` or `switch` chains in the context are replaced by polymorphic dispatch. |
| **Explicit transitions** | State transitions become first-class operations, making the FSM easier to audit. |
| **Easier testing** | Each state class can be unit-tested in isolation. |

### Cons

| Drawback | Detail |
|---|---|
| **Class proliferation** | Every state requires its own class, which can feel excessive for small machines. |
| **Overkill for simple FSMs** | If there are only two states, the extra abstraction adds complexity without benefit. |
| **Coupling between states** | Concrete states may need to know about each other (or the context) to trigger transitions, introducing coupling. |
| **Distributed logic** | Understanding the full state machine requires reading every state class, not just one file. |

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Strategy** | State and Strategy look identical structurally — both replace conditionals with polymorphism. The difference is **intent and who drives change**: Strategy lets the client swap algorithms explicitly; State transitions happen internally, often triggered by the state object itself. |
| **Bridge** | Both decouple abstraction from implementation, but Bridge is designed to vary both dimensions independently at design time, while State varies behavior at runtime based on internal condition. |
| **Singleton** | Concrete state objects often have no intrinsic state of their own (they use the context's data), making them safe to share as singletons. This avoids repeated instantiation on every transition and is a common optimization. |

---

## Sources

- https://refactoring.guru/design-patterns/state
- https://sourcemaking.com/design_patterns/state
