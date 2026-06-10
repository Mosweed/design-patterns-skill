# Observer Pattern

**Category:** Behavioral  
**Also Known As:** Event-Subscriber, Listener, Dependents

---

## Intent

Define a one-to-many dependency between objects so that when one object (the **publisher/subject**) changes state, all its dependents (**subscribers/observers**) are notified and updated automatically. This establishes a subscription mechanism that lets multiple objects watch and react to events produced by another object without tightly coupling them together.

---

## Problem It Solves

Imagine you are building a stock-market dashboard. A `StockFeed` object fetches live price data. Several components — a chart widget, an alert system, a portfolio calculator, and a logging service — all need to react whenever prices change.

A naive approach wires the `StockFeed` directly to each consumer:

```
StockFeed.update() {
    chart.refresh(price);
    alertSystem.check(price);
    portfolio.recalculate(price);
    logger.record(price);
}
```

This creates tight coupling: the publisher must know every consumer at compile time; adding or removing a consumer means editing the publisher; consumers cannot opt in or out at runtime; and unit-testing the publisher forces instantiating every downstream object.

The problem, stated generally:

- One object changes state and **must** inform other objects.
- You do **not** know beforehand how many objects want to be notified.
- The set of interested objects **changes dynamically** at runtime.
- The publisher should remain **independent** of what the subscribers do with the notification.

---

## Solution

1. Extract a **Subscriber** (Observer) interface with a single notification method (e.g., `update(event)`).
2. Give the **Publisher** (Subject) a list of subscriber references and three operations: `subscribe()`, `unsubscribe()`, and `notify()`.
3. When the publisher's state changes it calls `notify()`, which iterates the list and calls `update()` on every subscriber.
4. Each **ConcreteSubscriber** implements the interface and reacts to notifications in its own way.
5. Subscribers can attach and detach themselves at runtime; the publisher never imports or references concrete subscriber classes.

---

## Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                         «interface»                             │
│                          Subscriber                             │
│─────────────────────────────────────────────────────────────────│
│  + update(context: EventData)                                   │
└─────────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
┌────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│ConcreteSubscr. │  │ConcreteSubscr.  │  │  ConcreteSubscr.    │
│      A         │  │      B          │  │       C             │
│────────────────│  │─────────────────│  │─────────────────────│
│ - ownState     │  │ - ownState      │  │ - ownState          │
│────────────────│  │─────────────────│  │─────────────────────│
│ + update(...)  │  │ + update(...)   │  │ + update(...)       │
└────────────────┘  └─────────────────┘  └─────────────────────┘


┌──────────────────────────────────────────────────────────────────┐
│                    Publisher (Subject)                           │
│──────────────────────────────────────────────────────────────────│
│  - subscribers: List<Subscriber>                                 │
│  - state: Any                                                    │
│──────────────────────────────────────────────────────────────────│
│  + subscribe(s: Subscriber)    ──────────────────────────────►  │
│  + unsubscribe(s: Subscriber)  adds / removes from list         │
│  + notify()                    iterates list → calls update()   │
│  + changeState(newState)       mutates state, then calls notify │
└──────────────────────────────────────────────────────────────────┘

Relationship:
  Publisher  ──────────────────────────────► «interface» Subscriber
  (holds list)                               (calls update on each)
```

---

## Participants

| Participant | Role |
|---|---|
| **Publisher / Subject** | Owns the list of subscribers. Provides `subscribe()` / `unsubscribe()` / `notify()`. Changes its own state and triggers notification. |
| **Subscriber / Observer** | Interface (or abstract class) declaring the `update()` method. Decouples the publisher from concrete types. |
| **ConcreteSubscriber** | Implements the `Subscriber` interface. Performs an action in response to the notification. Optionally queries the publisher for details. |
| **Client** | Creates publishers and subscribers, then wires them together by calling `subscribe()`. |

---

## How It Works

1. **Initialization** — The client creates a Publisher and one or more ConcreteSubscriber objects.
2. **Subscription** — Each subscriber that wishes to receive events calls `publisher.subscribe(self)`. The publisher appends the subscriber to its internal list.
3. **State change** — Something triggers a state change in the publisher (user action, timer, incoming network data, etc.).
4. **Notification dispatch** — The publisher calls its own `notify()` method, which loops through every subscriber in the list and calls `subscriber.update(eventData)`.
5. **Subscriber reaction** — Each ConcreteSubscriber's `update()` executes its own logic: refresh a UI widget, send an email, write to a log, recalculate a value, etc.
6. **Unsubscription** — At any point a subscriber can call `publisher.unsubscribe(self)` to stop receiving future notifications. The publisher removes it from the list.
7. **No mutual knowledge** — The publisher never imports or references ConcreteSubscriber classes. Subscribers know only about the publisher's public interface (or a shared event object). Both sides depend on the abstraction only.

---

## Code Examples

### Python

```python
"""
Real-world example: E-commerce order system.

An Order acts as the publisher. Multiple services (email notifier,
inventory manager, analytics tracker) subscribe to order-status events.
New services can be plugged in without touching Order.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List


# ---------------------------------------------------------------------------
# Event data
# ---------------------------------------------------------------------------

class OrderStatus(Enum):
    PLACED = auto()
    PAID = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()


@dataclass
class OrderEvent:
    order_id: str
    status: OrderStatus
    customer_email: str
    total_amount: float
    items: List[str]


# ---------------------------------------------------------------------------
# Subscriber interface
# ---------------------------------------------------------------------------

class OrderObserver(ABC):
    """All services that react to order events implement this interface."""

    @abstractmethod
    def on_order_event(self, event: OrderEvent) -> None: ...


# ---------------------------------------------------------------------------
# Publisher
# ---------------------------------------------------------------------------

class Order:
    """
    Represents an e-commerce order.
    Acts as the publisher: maintains a list of observers and notifies them
    whenever the order status changes.
    """

    def __init__(self, order_id: str, customer_email: str) -> None:
        self._order_id = order_id
        self._customer_email = customer_email
        self._status = OrderStatus.PLACED
        self._items: List[str] = []
        self._total: float = 0.0
        self._observers: List[OrderObserver] = []

    # --- subscription management -------------------------------------------

    def subscribe(self, observer: OrderObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: OrderObserver) -> None:
        self._observers.remove(observer)

    def _notify(self) -> None:
        event = OrderEvent(
            order_id=self._order_id,
            status=self._status,
            customer_email=self._customer_email,
            total_amount=self._total,
            items=list(self._items),
        )
        for observer in self._observers:
            observer.on_order_event(event)

    # --- business operations -----------------------------------------------

    def add_item(self, item: str, price: float) -> None:
        self._items.append(item)
        self._total += price

    def mark_paid(self) -> None:
        self._status = OrderStatus.PAID
        self._notify()

    def mark_shipped(self) -> None:
        self._status = OrderStatus.SHIPPED
        self._notify()

    def mark_delivered(self) -> None:
        self._status = OrderStatus.DELIVERED
        self._notify()

    def cancel(self) -> None:
        self._status = OrderStatus.CANCELLED
        self._notify()


# ---------------------------------------------------------------------------
# Concrete subscribers
# ---------------------------------------------------------------------------

class EmailNotificationService(OrderObserver):
    """Sends transactional emails to the customer on status changes."""

    def on_order_event(self, event: OrderEvent) -> None:
        templates = {
            OrderStatus.PAID: "Your payment has been received. Thank you!",
            OrderStatus.SHIPPED: "Great news — your order is on its way!",
            OrderStatus.DELIVERED: "Your order has been delivered. Enjoy!",
            OrderStatus.CANCELLED: "Your order has been cancelled.",
        }
        message = templates.get(event.status)
        if message:
            print(
                f"[EMAIL] → {event.customer_email} | Order #{event.order_id} | "
                f"{message}"
            )


class InventoryService(OrderObserver):
    """Adjusts warehouse stock when an order is placed or cancelled."""

    def on_order_event(self, event: OrderEvent) -> None:
        if event.status == OrderStatus.PAID:
            print(
                f"[INVENTORY] Reserving stock for order #{event.order_id}: "
                + ", ".join(event.items)
            )
        elif event.status == OrderStatus.CANCELLED:
            print(
                f"[INVENTORY] Releasing stock for cancelled order #{event.order_id}"
            )


class AnalyticsService(OrderObserver):
    """Records conversion and revenue events for business reporting."""

    def on_order_event(self, event: OrderEvent) -> None:
        if event.status == OrderStatus.PAID:
            print(
                f"[ANALYTICS] Revenue event: order #{event.order_id} "
                f"— ${event.total_amount:.2f} recorded."
            )
        elif event.status == OrderStatus.DELIVERED:
            print(
                f"[ANALYTICS] Delivery confirmed for order #{event.order_id}."
            )


class FraudDetectionService(OrderObserver):
    """Flags high-value orders for manual review."""

    THRESHOLD = 500.0

    def on_order_event(self, event: OrderEvent) -> None:
        if event.status == OrderStatus.PAID and event.total_amount > self.THRESHOLD:
            print(
                f"[FRAUD] ⚠ High-value order #{event.order_id} "
                f"(${event.total_amount:.2f}) queued for review."
            )


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

def main() -> None:
    order = Order(order_id="ORD-9821", customer_email="alice@example.com")
    order.add_item("Mechanical Keyboard", 149.99)
    order.add_item("USB-C Hub", 59.99)
    order.add_item("Monitor Stand", 89.99)
    order.add_item("Webcam Pro", 229.99)

    # Wire up all services — Order knows nothing about their internals
    email_svc = EmailNotificationService()
    inventory_svc = InventoryService()
    analytics_svc = AnalyticsService()
    fraud_svc = FraudDetectionService()

    for svc in (email_svc, inventory_svc, analytics_svc, fraud_svc):
        order.subscribe(svc)

    print("=== Order paid ===")
    order.mark_paid()

    print("\n=== Order shipped ===")
    order.mark_shipped()

    # Fraud detection no longer needed after shipping — unsubscribe at runtime
    order.unsubscribe(fraud_svc)

    print("\n=== Order delivered ===")
    order.mark_delivered()


if __name__ == "__main__":
    main()
```

---

### Java

```java
/**
 * Real-world example: Weather Station
 *
 * A WeatherStation (publisher) measures temperature, humidity, and pressure.
 * Multiple display panels (subscribers) update themselves whenever new sensor
 * readings arrive. New display types can be added without modifying the station.
 */

import java.util.ArrayList;
import java.util.List;

// ---------------------------------------------------------------------------
// Event data (immutable record)
// ---------------------------------------------------------------------------

record WeatherReading(double temperatureCelsius, double humidityPercent, double pressureHpa) {

    public double temperatureFahrenheit() {
        return temperatureCelsius * 9.0 / 5.0 + 32.0;
    }

    public String comfortLevel() {
        if (humidityPercent > 70 && temperatureCelsius > 28) return "Uncomfortable";
        if (humidityPercent < 30 && temperatureCelsius < 5)  return "Dry & Cold";
        return "Comfortable";
    }
}

// ---------------------------------------------------------------------------
// Subscriber interface
// ---------------------------------------------------------------------------

interface WeatherObserver {
    void onWeatherUpdate(WeatherReading reading);
}

// ---------------------------------------------------------------------------
// Publisher interface (optional but recommended for testability)
// ---------------------------------------------------------------------------

interface WeatherPublisher {
    void addObserver(WeatherObserver observer);
    void removeObserver(WeatherObserver observer);
    void notifyObservers();
}

// ---------------------------------------------------------------------------
// Concrete publisher
// ---------------------------------------------------------------------------

class WeatherStation implements WeatherPublisher {

    private final String stationId;
    private final List<WeatherObserver> observers = new ArrayList<>();
    private WeatherReading latestReading;

    public WeatherStation(String stationId) {
        this.stationId = stationId;
    }

    @Override
    public void addObserver(WeatherObserver observer) {
        observers.add(observer);
    }

    @Override
    public void removeObserver(WeatherObserver observer) {
        observers.remove(observer);
    }

    @Override
    public void notifyObservers() {
        for (WeatherObserver observer : observers) {
            observer.onWeatherUpdate(latestReading);
        }
    }

    /** Called by sensor hardware (or simulation) with a fresh reading. */
    public void recordReading(double tempC, double humidity, double pressure) {
        this.latestReading = new WeatherReading(tempC, humidity, pressure);
        System.out.printf("%n[%s] New sensor data: %.1f°C, %.0f%% RH, %.1f hPa%n",
                stationId, tempC, humidity, pressure);
        notifyObservers();
    }

    public String getStationId() { return stationId; }
}

// ---------------------------------------------------------------------------
// Concrete subscribers
// ---------------------------------------------------------------------------

class CurrentConditionsDisplay implements WeatherObserver {

    @Override
    public void onWeatherUpdate(WeatherReading r) {
        System.out.printf(
            "  [Current Conditions] %.1f°C (%.1f°F) | Humidity: %.0f%% | %s%n",
            r.temperatureCelsius(), r.temperatureFahrenheit(),
            r.humidityPercent(), r.comfortLevel()
        );
    }
}

class StatisticsDisplay implements WeatherObserver {

    private double minTemp = Double.MAX_VALUE;
    private double maxTemp = Double.MIN_VALUE;
    private double totalTemp = 0;
    private int readingCount = 0;

    @Override
    public void onWeatherUpdate(WeatherReading r) {
        double t = r.temperatureCelsius();
        minTemp = Math.min(minTemp, t);
        maxTemp = Math.max(maxTemp, t);
        totalTemp += t;
        readingCount++;
        System.out.printf(
            "  [Statistics] Min: %.1f°C | Avg: %.1f°C | Max: %.1f°C (over %d readings)%n",
            minTemp, totalTemp / readingCount, maxTemp, readingCount
        );
    }
}

class StormAlertSystem implements WeatherObserver {

    private static final double STORM_PRESSURE_THRESHOLD = 980.0;
    private static final double HIGH_WIND_HUMIDITY       = 90.0;

    @Override
    public void onWeatherUpdate(WeatherReading r) {
        if (r.pressureHpa() < STORM_PRESSURE_THRESHOLD && r.humidityPercent() > HIGH_WIND_HUMIDITY) {
            System.out.printf(
                "  [STORM ALERT] ⚠ Severe conditions detected! Pressure: %.1f hPa, RH: %.0f%%%n",
                r.pressureHpa(), r.humidityPercent()
            );
        }
    }
}

class ForecastDisplay implements WeatherObserver {

    private double previousPressure = 0;

    @Override
    public void onWeatherUpdate(WeatherReading r) {
        String forecast;
        if (previousPressure == 0) {
            forecast = "Collecting baseline data...";
        } else if (r.pressureHpa() > previousPressure) {
            forecast = "Improving weather ahead.";
        } else if (r.pressureHpa() < previousPressure) {
            forecast = "Watch out — weather may worsen.";
        } else {
            forecast = "More of the same.";
        }
        previousPressure = r.pressureHpa();
        System.out.println("  [Forecast] " + forecast);
    }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

public class WeatherStationDemo {

    public static void main(String[] args) {
        WeatherStation station = new WeatherStation("STATION-NYC-001");

        CurrentConditionsDisplay currentDisplay = new CurrentConditionsDisplay();
        StatisticsDisplay        statsDisplay   = new StatisticsDisplay();
        StormAlertSystem         alertSystem    = new StormAlertSystem();
        ForecastDisplay          forecastDisplay = new ForecastDisplay();

        station.addObserver(currentDisplay);
        station.addObserver(statsDisplay);
        station.addObserver(alertSystem);
        station.addObserver(forecastDisplay);

        // Simulate sensor readings over time
        station.recordReading(22.5, 58.0, 1013.2);
        station.recordReading(21.0, 63.0, 1008.5);
        station.recordReading(18.3, 80.0, 995.1);

        // Remove forecast display — maintenance mode
        System.out.println("\n--- Forecast display taken offline ---");
        station.removeObserver(forecastDisplay);

        // Storm conditions
        station.recordReading(15.0, 92.0, 975.4);
    }
}
```

---

### C++

```cpp
/**
 * Real-world example: GUI Event System
 *
 * A Button widget is the publisher. Multiple handlers (logger, sound player,
 * network reporter) subscribe to click events. Demonstrates modern C++
 * with smart pointers and type-safe event data.
 */

#include <algorithm>
#include <functional>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

// ---------------------------------------------------------------------------
// Event data
// ---------------------------------------------------------------------------

struct ClickEvent {
    std::string widget_id;
    int         x;
    int         y;
    int         click_count;  // 1 = single, 2 = double
};

// ---------------------------------------------------------------------------
// Subscriber interface
// ---------------------------------------------------------------------------

class ClickListener {
public:
    virtual ~ClickListener() = default;
    virtual void on_click(const ClickEvent& event) = 0;
};

// ---------------------------------------------------------------------------
// Publisher base (reusable mixin)
// ---------------------------------------------------------------------------

template <typename EventT, typename ListenerT>
class EventSource {
public:
    void subscribe(std::shared_ptr<ListenerT> listener) {
        listeners_.push_back(listener);
    }

    void unsubscribe(std::shared_ptr<ListenerT> listener) {
        listeners_.erase(
            std::remove_if(listeners_.begin(), listeners_.end(),
                [&](const std::weak_ptr<ListenerT>& wp) {
                    auto sp = wp.lock();
                    return !sp || sp == listener;
                }),
            listeners_.end()
        );
    }

protected:
    void notify(const EventT& event) {
        // Iterate a copy so listeners can safely unsubscribe during notification
        auto snapshot = listeners_;
        for (auto& wp : snapshot) {
            if (auto sp = wp.lock()) {
                sp->on_click(event);
            }
        }
    }

private:
    std::vector<std::weak_ptr<ListenerT>> listeners_;
};

// ---------------------------------------------------------------------------
// Concrete publisher
// ---------------------------------------------------------------------------

class Button : public EventSource<ClickEvent, ClickListener> {
public:
    explicit Button(std::string id) : id_(std::move(id)) {}

    /** Simulate a mouse click at (x, y). */
    void click(int x, int y, int click_count = 1) {
        std::cout << "\n[Button:" << id_ << "] Clicked at ("
                  << x << ", " << y << ")"
                  << (click_count == 2 ? " [DOUBLE]" : "") << "\n";
        notify(ClickEvent{id_, x, y, click_count});
    }

    const std::string& id() const { return id_; }

private:
    std::string id_;
};

// ---------------------------------------------------------------------------
// Concrete subscribers
// ---------------------------------------------------------------------------

class AuditLogger : public ClickListener {
public:
    void on_click(const ClickEvent& e) override {
        std::cout << "  [AuditLogger] Event recorded: widget=" << e.widget_id
                  << " pos=(" << e.x << "," << e.y << ")"
                  << " clicks=" << e.click_count << "\n";
    }
};

class SoundPlayer : public ClickListener {
public:
    void on_click(const ClickEvent& e) override {
        std::string sound = (e.click_count == 2) ? "double_click.wav" : "click.wav";
        std::cout << "  [SoundPlayer] Playing: " << sound << "\n";
    }
};

class NetworkReporter : public ClickListener {
public:
    explicit NetworkReporter(std::string endpoint)
        : endpoint_(std::move(endpoint)) {}

    void on_click(const ClickEvent& e) override {
        std::cout << "  [NetworkReporter] POST " << endpoint_
                  << " → { widget: \"" << e.widget_id
                  << "\", x: " << e.x << ", y: " << e.y << " }\n";
    }

private:
    std::string endpoint_;
};

class TooltipHider : public ClickListener {
public:
    void on_click(const ClickEvent& /*e*/) override {
        std::cout << "  [TooltipHider] Active tooltip dismissed.\n";
    }
};

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

int main() {
    auto submit_btn = std::make_shared<Button>("submit");
    auto cancel_btn = std::make_shared<Button>("cancel");

    auto logger   = std::make_shared<AuditLogger>();
    auto sound    = std::make_shared<SoundPlayer>();
    auto reporter = std::make_shared<NetworkReporter>("https://telemetry.example.com/events");
    auto tooltip  = std::make_shared<TooltipHider>();

    // Both buttons share the same logger and tooltip hider
    submit_btn->subscribe(logger);
    submit_btn->subscribe(sound);
    submit_btn->subscribe(reporter);
    submit_btn->subscribe(tooltip);

    cancel_btn->subscribe(logger);
    cancel_btn->subscribe(tooltip);

    submit_btn->click(120, 45);
    submit_btn->click(120, 45, 2);  // double-click

    cancel_btn->click(80, 45);

    // Telemetry disabled (e.g., user opted out)
    std::cout << "\n--- User opted out of telemetry ---\n";
    submit_btn->unsubscribe(reporter);
    submit_btn->click(120, 45);

    return 0;
}
```

---

### C#

```csharp
/**
 * Real-world example: Stock Price Alert System
 *
 * A StockMarket acts as publisher. Traders and automated bots subscribe to
 * receive price-change notifications. Uses C# events and delegates
 * (the idiomatic C# Observer implementation) alongside a manual interface
 * version for comparison.
 *
 * Compile: dotnet script StockAlert.csx  (or include in a standard project)
 */

using System;
using System.Collections.Generic;

// ---------------------------------------------------------------------------
// Event data
// ---------------------------------------------------------------------------

public class StockPriceChangedEventArgs : EventArgs
{
    public string   Symbol        { get; init; }
    public decimal  OldPrice      { get; init; }
    public decimal  NewPrice      { get; init; }
    public DateTime Timestamp     { get; init; }

    public decimal ChangePercent =>
        OldPrice == 0 ? 0 : Math.Round((NewPrice - OldPrice) / OldPrice * 100, 2);
}

// ---------------------------------------------------------------------------
// Publisher
// ---------------------------------------------------------------------------

public class StockMarket
{
    // C# idiomatic: use event + EventHandler<T>
    public event EventHandler<StockPriceChangedEventArgs>? PriceChanged;

    private readonly Dictionary<string, decimal> _prices = new();

    public void UpdatePrice(string symbol, decimal newPrice)
    {
        _prices.TryGetValue(symbol, out decimal oldPrice);
        _prices[symbol] = newPrice;

        Console.WriteLine($"\n[Market] {symbol}: {oldPrice:C} → {newPrice:C}");

        // Fire the event — .NET runtime notifies all subscribers
        PriceChanged?.Invoke(this, new StockPriceChangedEventArgs
        {
            Symbol    = symbol,
            OldPrice  = oldPrice,
            NewPrice  = newPrice,
            Timestamp = DateTime.UtcNow,
        });
    }

    public decimal GetPrice(string symbol) =>
        _prices.TryGetValue(symbol, out var p) ? p : 0m;
}

// ---------------------------------------------------------------------------
// Concrete subscribers (implemented as classes with methods)
// ---------------------------------------------------------------------------

public class TraderAlertService
{
    private readonly string _traderId;
    private readonly Dictionary<string, decimal> _watchlist;

    public TraderAlertService(string traderId, Dictionary<string, decimal> watchlist)
    {
        _traderId  = traderId;
        _watchlist = watchlist;
    }

    public void OnPriceChanged(object? sender, StockPriceChangedEventArgs e)
    {
        if (_watchlist.TryGetValue(e.Symbol, out decimal targetPrice))
        {
            string direction = e.NewPrice > e.OldPrice ? "▲" : "▼";
            Console.WriteLine(
                $"  [Trader:{_traderId}] {e.Symbol} {direction} {e.ChangePercent:+0.00;-0.00}% " +
                $"(target: {targetPrice:C}, current: {e.NewPrice:C})"
            );
            if (e.NewPrice <= targetPrice)
                Console.WriteLine($"  [Trader:{_traderId}] *** BUY SIGNAL for {e.Symbol}! ***");
        }
    }
}

public class RiskManagementSystem
{
    private const decimal DropThreshold = -5.0m;

    public void OnPriceChanged(object? sender, StockPriceChangedEventArgs e)
    {
        if (e.ChangePercent <= DropThreshold)
        {
            Console.WriteLine(
                $"  [RiskMgmt] ⚠ CIRCUIT BREAKER: {e.Symbol} dropped {e.ChangePercent:0.00}% " +
                $"at {e.Timestamp:HH:mm:ss}Z — halting related orders."
            );
        }
    }
}

public class MarketDataRecorder
{
    private readonly List<StockPriceChangedEventArgs> _history = new();

    public void OnPriceChanged(object? sender, StockPriceChangedEventArgs e)
    {
        _history.Add(e);
        Console.WriteLine(
            $"  [Recorder] Logged tick #{_history.Count}: {e.Symbol} @ {e.NewPrice:C}"
        );
    }

    public IReadOnlyList<StockPriceChangedEventArgs> History => _history;
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

public class Program
{
    public static void Main()
    {
        var market = new StockMarket();

        // --- Subscribers ---
        var aliceWatchlist = new Dictionary<string, decimal>
        {
            ["AAPL"] = 170.00m,
            ["MSFT"] = 310.00m,
        };
        var alice   = new TraderAlertService("Alice", aliceWatchlist);
        var risk    = new RiskManagementSystem();
        var recorder = new MarketDataRecorder();

        // Wire up using C# event subscription syntax
        market.PriceChanged += alice.OnPriceChanged;
        market.PriceChanged += risk.OnPriceChanged;
        market.PriceChanged += recorder.OnPriceChanged;

        // Simulate market activity
        market.UpdatePrice("AAPL", 175.50m);
        market.UpdatePrice("MSFT", 315.20m);
        market.UpdatePrice("AAPL", 169.80m);  // Alice's buy signal

        // Simulate a crash scenario
        market.UpdatePrice("TSLA", 800.00m);
        market.UpdatePrice("TSLA", 754.00m);  // > 5% drop → risk alert

        // Alice logs off — unsubscribe at runtime
        Console.WriteLine("\n--- Alice goes offline ---");
        market.PriceChanged -= alice.OnPriceChanged;

        market.UpdatePrice("MSFT", 308.00m);

        Console.WriteLine($"\n[Recorder] Total ticks recorded: {recorder.History.Count}");
    }
}
```

---

### TypeScript

```typescript
/**
 * Real-world example: Real-time Collaborative Document Editor
 *
 * A Document acts as the publisher. Multiple clients (cursor tracker,
 * version history, spell checker, auto-save) subscribe to document-change
 * events. Demonstrates typed generics and a clean unsubscribe token pattern.
 */

// ---------------------------------------------------------------------------
// Generic event emitter (reusable Observer infrastructure)
// ---------------------------------------------------------------------------

type Listener<T> = (event: T) => void;

/** Returns an unsubscribe function (token pattern — no need to pass the listener back). */
type Unsubscribe = () => void;

class EventEmitter<Events extends Record<string, unknown>> {
  private listeners: {
    [K in keyof Events]?: Set<Listener<Events[K]>>;
  } = {};

  on<K extends keyof Events>(eventName: K, listener: Listener<Events[K]>): Unsubscribe {
    if (!this.listeners[eventName]) {
      this.listeners[eventName] = new Set();
    }
    this.listeners[eventName]!.add(listener);
    return () => this.off(eventName, listener);
  }

  off<K extends keyof Events>(eventName: K, listener: Listener<Events[K]>): void {
    this.listeners[eventName]?.delete(listener);
  }

  protected emit<K extends keyof Events>(eventName: K, event: Events[K]): void {
    this.listeners[eventName]?.forEach((listener) => listener(event));
  }
}

// ---------------------------------------------------------------------------
// Domain types
// ---------------------------------------------------------------------------

interface TextChange {
  position: number;
  inserted: string;
  deleted: string;
  authorId: string;
  timestamp: Date;
}

interface CursorPosition {
  authorId: string;
  line: number;
  column: number;
}

interface DocumentEvents {
  change:  TextChange;
  cursor:  CursorPosition;
  save:    { documentId: string; version: number };
  close:   { documentId: string };
}

// ---------------------------------------------------------------------------
// Publisher
// ---------------------------------------------------------------------------

class CollaborativeDocument extends EventEmitter<DocumentEvents> {
  private _content: string;
  private _version: number = 0;
  private _saveTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(
    public readonly id: string,
    initialContent = ""
  ) {
    super();
    this._content = initialContent;
  }

  get content(): string { return this._content; }
  get version(): number { return this._version; }

  applyChange(change: Omit<TextChange, "timestamp">): void {
    // Apply the text mutation
    this._content =
      this._content.slice(0, change.position) +
      change.inserted +
      this._content.slice(change.position + change.deleted.length);

    this._version++;

    // Notify all change subscribers
    this.emit("change", { ...change, timestamp: new Date() });

    // Debounced auto-save: notify after 2 s of inactivity
    if (this._saveTimer) clearTimeout(this._saveTimer);
    this._saveTimer = setTimeout(() => {
      this.emit("save", { documentId: this.id, version: this._version });
    }, 2000);
  }

  moveCursor(authorId: string, line: number, column: number): void {
    this.emit("cursor", { authorId, line, column });
  }

  close(): void {
    if (this._saveTimer) clearTimeout(this._saveTimer);
    this.emit("close", { documentId: this.id });
  }
}

// ---------------------------------------------------------------------------
// Concrete subscribers
// ---------------------------------------------------------------------------

class VersionHistoryService {
  private history: TextChange[] = [];

  subscribe(doc: CollaborativeDocument): Unsubscribe {
    return doc.on("change", (change) => {
      this.history.push(change);
      console.log(
        `  [VersionHistory] Rev ${this.history.length}: ` +
        `@${change.authorId} inserted "${change.inserted}" ` +
        `deleted "${change.deleted}" at pos ${change.position}`
      );
    });
  }

  getHistory(): TextChange[] { return [...this.history]; }
}

class SpellCheckService {
  private static readonly KNOWN_TYPOS: Record<string, string> = {
    teh: "the",
    recieve: "receive",
    seperate: "separate",
  };

  subscribe(doc: CollaborativeDocument): Unsubscribe {
    return doc.on("change", (change) => {
      const words = change.inserted.toLowerCase().split(/\s+/);
      for (const word of words) {
        const suggestion = SpellCheckService.KNOWN_TYPOS[word];
        if (suggestion) {
          console.log(
            `  [SpellCheck] Possible typo: "${word}" → did you mean "${suggestion}"?`
          );
        }
      }
    });
  }
}

class CursorOverlayService {
  private cursors: Map<string, CursorPosition> = new Map();

  subscribe(doc: CollaborativeDocument): Unsubscribe {
    return doc.on("cursor", (pos) => {
      this.cursors.set(pos.authorId, pos);
      console.log(
        `  [CursorOverlay] ${pos.authorId} → line ${pos.line}, col ${pos.column} ` +
        `(${this.cursors.size} active cursors)`
      );
    });
  }
}

class AutoSaveService {
  subscribe(doc: CollaborativeDocument): Unsubscribe {
    const unsubSave = doc.on("save", ({ documentId, version }) => {
      console.log(
        `  [AutoSave] Document "${documentId}" saved — version ${version} persisted to cloud.`
      );
    });
    const unsubClose = doc.on("close", ({ documentId }) => {
      console.log(`  [AutoSave] Document "${documentId}" closed. Flushing buffer.`);
    });
    return () => { unsubSave(); unsubClose(); };
  }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

(function main() {
  const doc = new CollaborativeDocument("doc-42", "Hello world");

  const versionSvc = new VersionHistoryService();
  const spellCheck = new SpellCheckService();
  const cursorSvc  = new CursorOverlayService();
  const autoSave   = new AutoSaveService();

  // Subscribe and keep unsubscribe tokens
  const unsubVersion  = versionSvc.subscribe(doc);
  const unsubSpell    = spellCheck.subscribe(doc);
  const unsubCursor   = cursorSvc.subscribe(doc);
  const unsubAutoSave = autoSave.subscribe(doc);

  console.log("\n=== User Alice starts editing ===");
  doc.moveCursor("alice", 1, 6);
  doc.applyChange({ position: 6, inserted: "beautiful ", deleted: "", authorId: "alice" });

  console.log("\n=== User Bob joins and edits ===");
  doc.moveCursor("bob", 1, 11);
  doc.applyChange({ position: 11, inserted: "teh world", deleted: "world", authorId: "bob" });

  console.log("\n=== Spell checker detects typo ===");
  // (already printed above by SpellCheckService)

  console.log("\n=== Spell checker goes offline ===");
  unsubSpell();

  doc.applyChange({ position: 0, inserted: "My ", deleted: "", authorId: "alice" });

  console.log(`\nFinal document: "${doc.content}"`);

  // Cleanup
  unsubVersion();
  unsubCursor();
  unsubAutoSave();
  doc.close();
})();
```

---

### Go

```go
// Real-world example: CI/CD Pipeline Notifier
//
// A Pipeline (publisher) runs build stages and emits lifecycle events.
// Multiple sinks (Slack notifier, email digest, metrics collector,
// deployment trigger) subscribe to events. Demonstrates idiomatic Go
// using channels and interfaces.

package main

import (
	"fmt"
	"strings"
	"sync"
	"time"
)

// ---------------------------------------------------------------------------
// Event types
// ---------------------------------------------------------------------------

type PipelineStatus string

const (
	StatusStarted  PipelineStatus = "STARTED"
	StatusPassed   PipelineStatus = "PASSED"
	StatusFailed   PipelineStatus = "FAILED"
	StatusCancelled PipelineStatus = "CANCELLED"
)

type PipelineEvent struct {
	PipelineID string
	Branch     string
	CommitSHA  string
	Author     string
	Stage      string
	Status     PipelineStatus
	Duration   time.Duration
	Error      string
	Timestamp  time.Time
}

// ---------------------------------------------------------------------------
// Observer interface
// ---------------------------------------------------------------------------

// PipelineObserver is implemented by any service that reacts to pipeline events.
type PipelineObserver interface {
	OnPipelineEvent(event PipelineEvent)
}

// ---------------------------------------------------------------------------
// Publisher
// ---------------------------------------------------------------------------

// Pipeline represents a CI/CD pipeline run.
type Pipeline struct {
	mu          sync.RWMutex
	id          string
	branch      string
	commitSHA   string
	author      string
	observers   []PipelineObserver
}

func NewPipeline(id, branch, commitSHA, author string) *Pipeline {
	return &Pipeline{
		id:        id,
		branch:    branch,
		commitSHA: commitSHA,
		author:    author,
	}
}

func (p *Pipeline) Subscribe(obs PipelineObserver) {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.observers = append(p.observers, obs)
}

func (p *Pipeline) Unsubscribe(obs PipelineObserver) {
	p.mu.Lock()
	defer p.mu.Unlock()
	filtered := p.observers[:0]
	for _, o := range p.observers {
		if o != obs {
			filtered = append(filtered, o)
		}
	}
	p.observers = filtered
}

func (p *Pipeline) notify(event PipelineEvent) {
	p.mu.RLock()
	snapshot := make([]PipelineObserver, len(p.observers))
	copy(snapshot, p.observers)
	p.mu.RUnlock()

	for _, obs := range snapshot {
		obs.OnPipelineEvent(event)
	}
}

// Run simulates executing pipeline stages.
func (p *Pipeline) Run(stages []string) {
	p.notify(PipelineEvent{
		PipelineID: p.id,
		Branch:     p.branch,
		CommitSHA:  p.commitSHA,
		Author:     p.author,
		Status:     StatusStarted,
		Timestamp:  time.Now(),
	})

	start := time.Now()
	for _, stage := range stages {
		fmt.Printf("\n[Pipeline:%s] Running stage: %s\n", p.id, stage)
		time.Sleep(50 * time.Millisecond) // simulate work

		// Simulate a test failure
		status := StatusPassed
		errMsg := ""
		if stage == "integration-tests" && strings.Contains(p.branch, "bugfix") {
			status = StatusFailed
			errMsg = "TestUserAuth: connection timeout after 30s"
		}

		p.notify(PipelineEvent{
			PipelineID: p.id,
			Branch:     p.branch,
			CommitSHA:  p.commitSHA,
			Author:     p.author,
			Stage:      stage,
			Status:     status,
			Duration:   time.Since(start),
			Error:      errMsg,
			Timestamp:  time.Now(),
		})

		if status == StatusFailed {
			return
		}
	}
}

// ---------------------------------------------------------------------------
// Concrete observers
// ---------------------------------------------------------------------------

// SlackNotifier posts messages to a Slack channel.
type SlackNotifier struct {
	channel string
}

func (s *SlackNotifier) OnPipelineEvent(e PipelineEvent) {
	switch e.Status {
	case StatusStarted:
		fmt.Printf("  [Slack#%s] :rocket: Pipeline %s started on %s by %s\n",
			s.channel, e.PipelineID, e.Branch, e.Author)
	case StatusPassed:
		if e.Stage != "" {
			fmt.Printf("  [Slack#%s] :white_check_mark: Stage %q passed (%.0fms)\n",
				s.channel, e.Stage, float64(e.Duration.Milliseconds()))
		}
	case StatusFailed:
		fmt.Printf("  [Slack#%s] :x: FAILURE in stage %q: %s\n",
			s.channel, e.Stage, e.Error)
	}
}

// MetricsCollector records pipeline durations for Prometheus/Grafana.
type MetricsCollector struct {
	mu       sync.Mutex
	stageDurations map[string][]time.Duration
}

func NewMetricsCollector() *MetricsCollector {
	return &MetricsCollector{stageDurations: make(map[string][]time.Duration)}
}

func (m *MetricsCollector) OnPipelineEvent(e PipelineEvent) {
	if e.Stage == "" {
		return
	}
	m.mu.Lock()
	m.stageDurations[e.Stage] = append(m.stageDurations[e.Stage], e.Duration)
	m.mu.Unlock()
	fmt.Printf("  [Metrics] stage=%q status=%s duration=%dms\n",
		e.Stage, e.Status, e.Duration.Milliseconds())
}

// DeploymentTrigger kicks off a production deployment on a successful pipeline.
type DeploymentTrigger struct {
	environment string
}

func (d *DeploymentTrigger) OnPipelineEvent(e PipelineEvent) {
	if e.Status == StatusPassed && e.Branch == "main" && e.Stage == "docker-build" {
		fmt.Printf("  [Deploy] Triggering deployment to %s for commit %s\n",
			d.environment, e.CommitSHA[:7])
	}
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

func main() {
	stages := []string{"lint", "unit-tests", "integration-tests", "docker-build"}

	// --- Successful pipeline on main ---
	fmt.Println("=== Pipeline: main branch ===")
	mainPipeline := NewPipeline("pipeline-101", "main", "a3f9c12e45b", "carol")

	slack   := &SlackNotifier{channel: "ci-alerts"}
	metrics := NewMetricsCollector()
	deploy  := &DeploymentTrigger{environment: "production"}

	mainPipeline.Subscribe(slack)
	mainPipeline.Subscribe(metrics)
	mainPipeline.Subscribe(deploy)

	mainPipeline.Run(stages)

	// --- Failing pipeline on a bugfix branch ---
	fmt.Println("\n\n=== Pipeline: bugfix/auth-timeout branch ===")
	fixPipeline := NewPipeline("pipeline-102", "bugfix/auth-timeout", "b7d1e09f33c", "dave")

	fixPipeline.Subscribe(slack)
	fixPipeline.Subscribe(metrics)
	// No deployment trigger for feature branches

	fixPipeline.Run(stages)
}
```

---

### PHP

```php
<?php

/**
 * Real-world example: User Activity Feed System
 *
 * A UserAccount (publisher) emits events when user actions occur (login,
 * profile update, password change). Multiple services (security auditor,
 * activity feed, notification center) react independently.
 *
 * Demonstrates PHP SPL SplObserver/SplSubject interfaces (built-in Observer).
 */

declare(strict_types=1);

// ---------------------------------------------------------------------------
// Event data
// ---------------------------------------------------------------------------

enum UserActionType: string
{
    case LOGIN           = 'login';
    case LOGOUT          = 'logout';
    case PASSWORD_CHANGE = 'password_change';
    case PROFILE_UPDATE  = 'profile_update';
    case FAILED_LOGIN    = 'failed_login';
}

class UserEvent
{
    public function __construct(
        public readonly string         $userId,
        public readonly string         $username,
        public readonly UserActionType $action,
        public readonly string         $ipAddress,
        public readonly \DateTimeImmutable $occurredAt,
        public readonly array          $metadata = [],
    ) {}
}

// ---------------------------------------------------------------------------
// Publisher (Subject)
// ---------------------------------------------------------------------------

class UserAccount implements \SplSubject
{
    /** @var \SplObjectStorage<\SplObserver, null> */
    private \SplObjectStorage $observers;
    private ?UserEvent $lastEvent = null;

    private string $id;
    private string $username;
    private int    $failedLoginAttempts = 0;

    public function __construct(string $id, string $username)
    {
        $this->id        = $id;
        $this->username  = $username;
        $this->observers = new \SplObjectStorage();
    }

    // --- SplSubject interface -----------------------------------------------

    public function attach(\SplObserver $observer): void
    {
        $this->observers->attach($observer);
    }

    public function detach(\SplObserver $observer): void
    {
        $this->observers->detach($observer);
    }

    public function notify(): void
    {
        foreach ($this->observers as $observer) {
            $observer->update($this);
        }
    }

    // --- Public accessor for observers -------------------------------------

    public function getLastEvent(): ?UserEvent
    {
        return $this->lastEvent;
    }

    // --- Business actions --------------------------------------------------

    public function login(string $ipAddress): void
    {
        $this->failedLoginAttempts = 0;
        $this->lastEvent = new UserEvent(
            userId:     $this->id,
            username:   $this->username,
            action:     UserActionType::LOGIN,
            ipAddress:  $ipAddress,
            occurredAt: new \DateTimeImmutable(),
        );
        echo "\n[UserAccount:{$this->username}] Logged in from {$ipAddress}\n";
        $this->notify();
    }

    public function recordFailedLogin(string $ipAddress): void
    {
        $this->failedLoginAttempts++;
        $this->lastEvent = new UserEvent(
            userId:     $this->id,
            username:   $this->username,
            action:     UserActionType::FAILED_LOGIN,
            ipAddress:  $ipAddress,
            occurredAt: new \DateTimeImmutable(),
            metadata:   ['attempt' => $this->failedLoginAttempts],
        );
        echo "\n[UserAccount:{$this->username}] Failed login #{$this->failedLoginAttempts} from {$ipAddress}\n";
        $this->notify();
    }

    public function changePassword(string $ipAddress): void
    {
        $this->lastEvent = new UserEvent(
            userId:     $this->id,
            username:   $this->username,
            action:     UserActionType::PASSWORD_CHANGE,
            ipAddress:  $ipAddress,
            occurredAt: new \DateTimeImmutable(),
        );
        echo "\n[UserAccount:{$this->username}] Password changed from {$ipAddress}\n";
        $this->notify();
    }

    public function updateProfile(array $changes, string $ipAddress): void
    {
        $this->lastEvent = new UserEvent(
            userId:     $this->id,
            username:   $this->username,
            action:     UserActionType::PROFILE_UPDATE,
            ipAddress:  $ipAddress,
            occurredAt: new \DateTimeImmutable(),
            metadata:   $changes,
        );
        echo "\n[UserAccount:{$this->username}] Profile updated\n";
        $this->notify();
    }
}

// ---------------------------------------------------------------------------
// Concrete observers
// ---------------------------------------------------------------------------

class SecurityAuditService implements \SplObserver
{
    private const MAX_FAILED_ATTEMPTS = 3;
    private array $log = [];

    public function update(\SplSubject $subject): void
    {
        /** @var UserAccount $subject */
        $event = $subject->getLastEvent();
        if ($event === null) return;

        $entry = sprintf(
            '[%s] user=%s action=%s ip=%s',
            $event->occurredAt->format('Y-m-d H:i:s'),
            $event->username,
            $event->action->value,
            $event->ipAddress,
        );
        $this->log[] = $entry;

        echo "  [SecurityAudit] {$entry}\n";

        if (
            $event->action === UserActionType::FAILED_LOGIN &&
            ($event->metadata['attempt'] ?? 0) >= self::MAX_FAILED_ATTEMPTS
        ) {
            echo "  [SecurityAudit] ⚠ ACCOUNT LOCKOUT triggered for {$event->username}!\n";
        }
    }

    public function getLog(): array { return $this->log; }
}

class ActivityFeedService implements \SplObserver
{
    private array $feed = [];

    public function update(\SplSubject $subject): void
    {
        /** @var UserAccount $subject */
        $event = $subject->getLastEvent();
        if ($event === null) return;

        $humanActions = [
            UserActionType::LOGIN->value           => 'signed in',
            UserActionType::LOGOUT->value          => 'signed out',
            UserActionType::PASSWORD_CHANGE->value => 'changed their password',
            UserActionType::PROFILE_UPDATE->value  => 'updated their profile',
        ];

        $description = $humanActions[$event->action->value] ?? 'performed an action';
        $feedItem    = "{$event->username} {$description}.";
        $this->feed[] = $feedItem;

        echo "  [ActivityFeed] Added: {$feedItem}\n";
    }

    public function getFeed(): array { return $this->feed; }
}

class NotificationCenterService implements \SplObserver
{
    public function update(\SplSubject $subject): void
    {
        /** @var UserAccount $subject */
        $event = $subject->getLastEvent();
        if ($event === null) return;

        match ($event->action) {
            UserActionType::PASSWORD_CHANGE => $this->send(
                $event->username,
                'Security alert: your password was changed.',
                'If this was not you, contact support immediately.'
            ),
            UserActionType::LOGIN when $this->isUnusualIp($event->ipAddress) => $this->send(
                $event->username,
                'New sign-in detected.',
                "Sign-in from IP {$event->ipAddress}."
            ),
            default => null,
        };
    }

    private function send(string $user, string $subject, string $body): void
    {
        echo "  [Notifications] → {$user}: \"{$subject}\" — {$body}\n";
    }

    private function isUnusualIp(string $ip): bool
    {
        // Simplified: flag non-private IPs as unusual
        return !str_starts_with($ip, '192.168.');
    }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

$account = new UserAccount('usr-001', 'john.doe');

$security      = new SecurityAuditService();
$activityFeed  = new ActivityFeedService();
$notifications = new NotificationCenterService();

$account->attach($security);
$account->attach($activityFeed);
$account->attach($notifications);

$account->login('192.168.1.10');
$account->updateProfile(['bio' => 'Software Engineer'], '192.168.1.10');
$account->changePassword('203.0.113.42');  // unusual IP + password change

echo "\n--- Brute-force attempt ---\n";
$account->recordFailedLogin('198.51.100.7');
$account->recordFailedLogin('198.51.100.7');
$account->recordFailedLogin('198.51.100.7');

echo "\n--- Activity feed has " . count($activityFeed->getFeed()) . " entries ---\n";
echo "--- Security log has " . count($security->getLog()) . " entries ---\n";
```

---

### Ruby

```ruby
# Real-world example: IoT Smart Home Hub
#
# A SmartHomeSensor (publisher) emits readings from temperature, motion, and
# door sensors. Multiple automations (thermostat, security camera, lighting)
# subscribe and react independently. Demonstrates Ruby's idiomatic Observer
# using the stdlib Observable module as well as a manual implementation.

require 'observer'
require 'time'

# ---------------------------------------------------------------------------
# Event data
# ---------------------------------------------------------------------------

SensorReading = Struct.new(
  :sensor_id,
  :sensor_type,
  :value,
  :unit,
  :location,
  :timestamp,
  keyword_init: true
) do
  def to_s
    "[#{timestamp.strftime('%H:%M:%S')}] #{sensor_id} (#{location}): " \
    "#{value} #{unit}"
  end
end

# ---------------------------------------------------------------------------
# Publisher — includes Ruby's built-in Observable module
# ---------------------------------------------------------------------------

class SmartHomeSensor
  include Observable

  attr_reader :sensor_id, :sensor_type, :location

  THRESHOLDS = {
    temperature: { min: 16.0, max: 28.0 },
    motion:      { active: true },
    door:        { open: true }
  }.freeze

  def initialize(sensor_id:, sensor_type:, location:)
    @sensor_id   = sensor_id
    @sensor_type = sensor_type
    @location    = location
  end

  # Called by sensor hardware or simulation
  def record_reading(value, unit: default_unit)
    reading = SensorReading.new(
      sensor_id:   @sensor_id,
      sensor_type: @sensor_type,
      value:       value,
      unit:        unit,
      location:    @location,
      timestamp:   Time.now
    )
    puts "\n[Sensor] #{reading}"
    changed                    # marks Observable as dirty
    notify_observers(reading)  # calls update(reading) on each observer
  end

  private

  def default_unit
    case @sensor_type
    when :temperature then '°C'
    when :motion      then 'active'
    when :door        then 'state'
    else ''
    end
  end
end

# ---------------------------------------------------------------------------
# Concrete observers
# ---------------------------------------------------------------------------

class ThermostatController
  TARGET_TEMP = 21.0

  def update(reading)
    return unless reading.sensor_type == :temperature

    if reading.value.to_f < 18.0
      puts "  [Thermostat] It's #{reading.value}°C in #{reading.location} — " \
           "heating activated to reach #{TARGET_TEMP}°C."
    elsif reading.value.to_f > 26.0
      puts "  [Thermostat] It's #{reading.value}°C in #{reading.location} — " \
           "A/C activated."
    else
      puts "  [Thermostat] #{reading.location} temperature OK (#{reading.value}°C)."
    end
  end
end

class SecurityCamera
  def initialize(recording_path: '/recordings')
    @recording_path = recording_path
    @recording      = false
  end

  def update(reading)
    case reading.sensor_type
    when :motion
      if reading.value == 'active' && !@recording
        @recording = true
        puts "  [Camera] Motion in #{reading.location}! " \
             "Recording → #{@recording_path}/#{reading.sensor_id}_#{reading.timestamp.to_i}.mp4"
      elsif reading.value == 'inactive' && @recording
        @recording = false
        puts "  [Camera] Motion cleared in #{reading.location}. Saving clip."
      end
    when :door
      if reading.value == 'open'
        puts "  [Camera] Door opened in #{reading.location} — snapping entry photo."
      end
    end
  end
end

class SmartLightingSystem
  SCENE_MAP = {
    morning: { brightness: 70,  color: 'warm_white' },
    evening: { brightness: 40,  color: 'warm_amber' },
    alert:   { brightness: 100, color: 'red' }
  }.freeze

  def update(reading)
    case reading.sensor_type
    when :motion
      scene = hour_to_scene
      if reading.value == 'active'
        puts "  [Lighting] Motion in #{reading.location}: " \
             "lights → #{scene[:brightness]}% #{scene[:color]}"
      else
        puts "  [Lighting] No motion in #{reading.location}: auto-off in 5 min."
      end
    when :door
      if reading.value == 'open'
        puts "  [Lighting] Entry detected in #{reading.location}: welcome lighting on."
      end
    end
  end

  private

  def hour_to_scene
    h = Time.now.hour
    h < 12 ? SCENE_MAP[:morning] : SCENE_MAP[:evening]
  end
end

class EventLogger
  def initialize
    @events = []
  end

  def update(reading)
    @events << reading
    puts "  [Logger] Stored event ##{@events.size}: #{reading.sensor_id}"
  end

  def summary
    puts "\n=== Event Log Summary ==="
    @events.group_by(&:sensor_type).each do |type, readings|
      puts "  #{type}: #{readings.size} reading(s)"
    end
  end
end

# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

def main
  # Create sensors
  living_room_temp  = SmartHomeSensor.new(sensor_id: 'TMP-LR-01', sensor_type: :temperature, location: 'Living Room')
  front_door_motion = SmartHomeSensor.new(sensor_id: 'MOT-FD-01', sensor_type: :motion,      location: 'Front Door')
  front_door_sensor = SmartHomeSensor.new(sensor_id: 'DOR-FD-01', sensor_type: :door,        location: 'Front Door')

  # Create observers
  thermostat = ThermostatController.new
  camera     = SecurityCamera.new(recording_path: '/var/recordings')
  lighting   = SmartLightingSystem.new
  logger     = EventLogger.new

  # Wire up — each sensor gets only relevant observers
  living_room_temp.add_observer(thermostat)
  living_room_temp.add_observer(logger)

  front_door_motion.add_observer(camera)
  front_door_motion.add_observer(lighting)
  front_door_motion.add_observer(logger)

  front_door_sensor.add_observer(camera)
  front_door_sensor.add_observer(lighting)
  front_door_sensor.add_observer(logger)

  # Simulate sensor readings
  puts "=== Morning scenario ==="
  living_room_temp.record_reading(16.5)      # Too cold → thermostat
  front_door_motion.record_reading('active') # Someone at the door
  front_door_sensor.record_reading('open')   # Door opened
  front_door_motion.record_reading('inactive')

  puts "\n=== Afternoon scenario ==="
  living_room_temp.record_reading(22.3)      # All good

  puts "\n=== Hot evening ==="
  living_room_temp.record_reading(27.1)      # Too hot → A/C

  # Thermostat maintenance: temporarily remove from all sensors
  puts "\n--- Thermostat going offline for calibration ---"
  living_room_temp.delete_observer(thermostat)
  living_room_temp.record_reading(18.0)      # No thermostat response

  logger.summary
end

main
```

---

## When To Use

**Use Observer when:**

- Changes to the state of one object require changing other objects, and you do not know at compile time how many objects need to change or which ones they are.
- Some objects need to watch others **only for a limited time** or only in specific circumstances (they can subscribe and unsubscribe dynamically).
- Objects should be able to notify other objects **without making assumptions** about who those objects are — you want to avoid tight coupling between sender and receivers.
- You are implementing distributed event handling, publish-subscribe systems, or push-based data streams (UI reactivity, real-time dashboards, messaging queues, IoT pipelines).
- You need to model the **Model-View separation**: the model notifies views of data changes, and views render without the model knowing about them.

**Do NOT use Observer when:**

- The notification chain is deep or recursive and could cause stack-overflow or hard-to-trace bugs.
- Notification order is critical to correctness — Observer does not guarantee order.
- Subscribers need to return values to the publisher (consider a different pattern like Command or Strategy).
- Simple synchronous procedure calls are sufficient — Observer adds complexity without benefit for small, stable dependency graphs.

---

## Pros & Cons

### Pros

| Benefit | Explanation |
|---|---|
| **Open/Closed Principle** | Add new subscriber types without modifying the publisher. |
| **Loose coupling** | Publisher and subscriber know each other only through a narrow interface. They can vary independently. |
| **Dynamic relationships** | Subscribers can attach and detach at runtime; relationships are not hard-coded. |
| **Broadcast communication** | One change in the publisher automatically propagates to all interested parties with no extra orchestration code. |
| **Separation of concerns** | Each subscriber handles one specific reaction; no single class grows bloated with every possible side effect. |

### Cons

| Drawback | Explanation |
|---|---|
| **Non-deterministic notification order** | Subscribers are typically notified in the order they subscribed, which may be arbitrary. Avoid logic that depends on ordering. |
| **Unexpected updates** | Subscribers can trigger further state changes, causing cascade notifications that are difficult to trace or debug. |
| **Memory leaks** | Forgetting to unsubscribe keeps the publisher holding a reference to the subscriber, preventing garbage collection (common in GUI frameworks). |
| **Performance at scale** | Notifying thousands of subscribers synchronously can become a bottleneck. Asynchronous variants add complexity. |
| **Hidden dependencies** | Relationships set up at runtime are invisible in the source code, making the system harder to reason about statically. |

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Chain of Responsibility** | Both pass a request along a series of handlers. Chain of Responsibility lets handlers choose to process or pass on; in Observer all subscribers receive the notification (no passing). |
| **Command** | Commands can be used to parameterize the action taken when a notification arrives (subscribe with a command instead of a raw callback). This is how GUI button listeners often work. |
| **Mediator** | Both reduce direct connections between objects, but they do it differently. Mediator is a hub — components communicate through it. Observer is a broadcast — publisher has no knowledge of what subscribers do with the notification. You can implement a Mediator using Observer internally. |
| **Strategy** | Subscribers are a form of Strategy: each implements the same interface but encapsulates different behavior. The difference is intent — Strategy swaps the algorithm used by one object; Observer fans out notifications to many objects. |

---

## Sources

- https://refactoring.guru/design-patterns/observer
- https://sourcemaking.com/design_patterns/observer
