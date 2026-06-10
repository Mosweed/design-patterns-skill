# Strategy Pattern

**Category:** Behavioral
**Also Known As:** Policy

---

## Intent

Define a family of algorithms, encapsulate each one in a dedicated class, and make their instances interchangeable. Strategy lets the algorithm vary independently from the clients that use it.

---

## Problem It Solves

You have an object that must perform some work — sorting, payment processing, route finding, compression, validation — but the exact algorithm or behavior needs to vary:

- At **runtime**, depending on user input or configuration.
- Across **different deployments**, without touching client code.
- When a **growing list of conditionals** (`if payment == "paypal" ... elif payment == "stripe" ...`) is making a single class bloated and fragile.
- When subclassing to swap behaviors leads to an **explosion of subclasses** that differ only in one method.

The naive approach (giant `if/else` or inheritance) violates the Open/Closed Principle: every new algorithm forces you to modify existing, tested code.

---

## Solution

Extract each variant behavior into its own **ConcreteStrategy** class, all implementing a common **Strategy** interface. The **Context** class holds a reference to a strategy object and delegates the behavioral work to it. The client decides which strategy to inject — either at construction time or later via a setter — without knowing the internal details of any strategy.

The Context is no longer responsible for choosing how to execute a task; it only knows *that* a task must be executed and calls the strategy to do it.

---

## Structure (ASCII diagram)

```
  ┌──────────────────────────────────┐
  │            Client                │
  └──────────────┬───────────────────┘
                 │ creates & configures
                 ▼
  ┌──────────────────────────────────┐
  │            Context               │
  │  - strategy: Strategy            │
  │  + setStrategy(Strategy)         │
  │  + executeOperation()            │
  └──────────────┬───────────────────┘
                 │ delegates to
                 ▼
  ┌──────────────────────────────────┐
  │         <<interface>>            │
  │            Strategy              │
  │  + execute(data): result         │
  └────────┬─────────────┬───────────┘
           │             │
           ▼             ▼
  ┌─────────────┐  ┌─────────────────┐
  │ ConcreteA   │  │  ConcreteB      │
  │ + execute() │  │  + execute()    │
  └─────────────┘  └─────────────────┘
```

---

## Participants

| Participant | Role |
|---|---|
| **Context** | Maintains a reference to a Strategy. Exposes a method to set or swap the strategy. Delegates the algorithm call to the strategy object rather than implementing it directly. |
| **Strategy** | Declares the interface common to all supported algorithms. The Context uses this interface to call the algorithm defined by a ConcreteStrategy. |
| **ConcreteStrategy** | Implements a specific variant of the algorithm using the Strategy interface. Each class is self-contained and independently testable. |
| **Client** | Creates a ConcreteStrategy object and passes it to the Context. May swap strategies at runtime as needed. |

---

## How It Works (step-by-step)

1. **Identify the varying behavior** in your class — the part that changes across use cases or changes at runtime.
2. **Define a Strategy interface** that captures the signature of the varying behavior (e.g., `sort(data)`, `pay(amount)`, `compress(file)`).
3. **Create ConcreteStrategy classes**, one per variant, each fully encapsulating its algorithm.
4. **Modify the Context** to hold a `Strategy` reference instead of implementing the algorithm inline. Add a constructor parameter or setter to inject the strategy.
5. **Delegate** from the Context's operation method to `this.strategy.execute(...)`.
6. **The Client** selects and injects the appropriate ConcreteStrategy. At runtime the client (or another part of the application) can call the Context's setter to swap to a different strategy without modifying the Context.

---

## Code Examples

### Python

```python
"""
Real-world example: E-commerce order shipping cost calculator.

Different shipping carriers (Standard, Express, Overnight) each have
their own pricing algorithm. The Order (Context) delegates to whichever
strategy is currently configured, allowing the user to compare rates
or switch carriers at checkout.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Package:
    weight_kg: float        # weight in kilograms
    length_cm: float
    width_cm: float
    height_cm: float
    destination_zone: int   # 1 = local, 2 = regional, 3 = national, 4 = international

    @property
    def volume_cm3(self) -> float:
        return self.length_cm * self.width_cm * self.height_cm

    @property
    def dimensional_weight_kg(self) -> float:
        """Carriers often charge by dimensional weight if it exceeds actual weight."""
        return self.volume_cm3 / 5000.0

    @property
    def billable_weight_kg(self) -> float:
        return max(self.weight_kg, self.dimensional_weight_kg)


# ---------------------------------------------------------------------------
# Strategy interface
# ---------------------------------------------------------------------------

class ShippingStrategy(ABC):
    """Common interface for all shipping cost calculators."""

    @abstractmethod
    def calculate_cost(self, package: Package) -> float:
        """Return the shipping cost in USD."""

    @abstractmethod
    def estimated_days(self, package: Package) -> int:
        """Return estimated delivery days."""

    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this strategy."""


# ---------------------------------------------------------------------------
# Concrete strategies
# ---------------------------------------------------------------------------

class StandardShipping(ShippingStrategy):
    """Ground shipping — cheapest, slowest."""

    BASE_RATE = 5.00          # USD flat fee
    RATE_PER_KG = 0.50        # per billable kg
    ZONE_MULTIPLIER = {1: 1.0, 2: 1.2, 3: 1.5, 4: 2.5}

    def calculate_cost(self, package: Package) -> float:
        zone_mult = self.ZONE_MULTIPLIER.get(package.destination_zone, 2.5)
        return (self.BASE_RATE + self.RATE_PER_KG * package.billable_weight_kg) * zone_mult

    def estimated_days(self, package: Package) -> int:
        days_by_zone = {1: 3, 2: 5, 3: 7, 4: 14}
        return days_by_zone.get(package.destination_zone, 14)

    def name(self) -> str:
        return "Standard Ground Shipping"


class ExpressShipping(ShippingStrategy):
    """Two-day air shipping."""

    BASE_RATE = 15.00
    RATE_PER_KG = 1.20
    ZONE_MULTIPLIER = {1: 1.0, 2: 1.1, 3: 1.3, 4: 2.0}

    def calculate_cost(self, package: Package) -> float:
        zone_mult = self.ZONE_MULTIPLIER.get(package.destination_zone, 2.0)
        return (self.BASE_RATE + self.RATE_PER_KG * package.billable_weight_kg) * zone_mult

    def estimated_days(self, package: Package) -> int:
        days_by_zone = {1: 1, 2: 2, 3: 2, 4: 5}
        return days_by_zone.get(package.destination_zone, 5)

    def name(self) -> str:
        return "Express 2-Day Air"


class OvernightShipping(ShippingStrategy):
    """Next-business-day delivery, premium price."""

    BASE_RATE = 30.00
    RATE_PER_KG = 2.50
    ZONE_MULTIPLIER = {1: 1.0, 2: 1.0, 3: 1.2, 4: 3.0}

    def calculate_cost(self, package: Package) -> float:
        zone_mult = self.ZONE_MULTIPLIER.get(package.destination_zone, 3.0)
        return (self.BASE_RATE + self.RATE_PER_KG * package.billable_weight_kg) * zone_mult

    def estimated_days(self, package: Package) -> int:
        days_by_zone = {1: 1, 2: 1, 3: 1, 4: 2}
        return days_by_zone.get(package.destination_zone, 2)

    def name(self) -> str:
        return "Overnight Priority"


class FreeShipping(ShippingStrategy):
    """Promotional free shipping (fulfilled by standard ground internally)."""

    def calculate_cost(self, package: Package) -> float:
        return 0.00

    def estimated_days(self, package: Package) -> int:
        # Same transit time as standard, just no charge to the customer
        return StandardShipping().estimated_days(package)

    def name(self) -> str:
        return "Free Shipping (Promotion)"


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

class ShoppingCart:
    """
    The Context. Holds a shipping strategy and delegates cost calculation
    to it. The strategy can be changed at any point before checkout.
    """

    def __init__(self, strategy: ShippingStrategy) -> None:
        self._strategy = strategy
        self._items: List[str] = []

    def set_shipping_strategy(self, strategy: ShippingStrategy) -> None:
        """Allow the customer to switch shipping method at any time."""
        print(f"  [Cart] Shipping method changed to: {strategy.name()}")
        self._strategy = strategy

    def add_item(self, item: str) -> None:
        self._items.append(item)

    def get_shipping_quote(self, package: Package) -> dict:
        """Return a shipping quote using the current strategy."""
        cost = self._strategy.calculate_cost(package)
        days = self._strategy.estimated_days(package)
        return {
            "method": self._strategy.name(),
            "cost_usd": round(cost, 2),
            "estimated_days": days,
        }

    def compare_all_rates(self, package: Package) -> List[dict]:
        """
        Compare quotes from every available carrier — useful for a
        'Choose your shipping' UI step at checkout.
        """
        strategies: List[ShippingStrategy] = [
            StandardShipping(),
            ExpressShipping(),
            OvernightShipping(),
        ]
        return [
            {
                "method": s.name(),
                "cost_usd": round(s.calculate_cost(package), 2),
                "estimated_days": s.estimated_days(package),
            }
            for s in strategies
        ]


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # A 3 kg package shipping nationally (zone 3)
    pkg = Package(
        weight_kg=3.0,
        length_cm=40,
        width_cm=30,
        height_cm=20,
        destination_zone=3,
    )

    # Start with standard shipping
    cart = ShoppingCart(strategy=StandardShipping())
    cart.add_item("Wireless Keyboard")
    cart.add_item("USB Hub")

    print("=== Shipping Rate Comparison ===")
    for quote in cart.compare_all_rates(pkg):
        print(f"  {quote['method']:<30} ${quote['cost_usd']:>6.2f}  ({quote['estimated_days']} days)")

    print()
    print("=== Customer Selects Express ===")
    cart.set_shipping_strategy(ExpressShipping())
    q = cart.get_shipping_quote(pkg)
    print(f"  Final method : {q['method']}")
    print(f"  Cost         : ${q['cost_usd']:.2f}")
    print(f"  Arrival in   : {q['estimated_days']} business day(s)")

    print()
    print("=== Promotion Applied: Free Shipping ===")
    cart.set_shipping_strategy(FreeShipping())
    q = cart.get_shipping_quote(pkg)
    print(f"  Cost: ${q['cost_usd']:.2f}  |  Still arrives in ~{q['estimated_days']} days")
```

---

### Java

```java
/**
 * Real-world example: Text compression pipeline.
 *
 * A FileArchiver (Context) can compress files using different algorithms
 * (GZIP, BZIP2, LZ4, or no compression). The strategy is injected at
 * construction and can be swapped at runtime — for instance, choosing
 * LZ4 for speed on large logs, or BZIP2 for maximum ratio on archives.
 */

import java.util.HashMap;
import java.util.Map;

// ---------------------------------------------------------------------------
// Strategy interface
// ---------------------------------------------------------------------------

interface CompressionStrategy {
    /** Compress the given data and return the compressed bytes. */
    byte[] compress(byte[] data);

    /** Decompress the given data and return the original bytes. */
    byte[] decompress(byte[] data);

    /** Return the file extension associated with this format (e.g. ".gz"). */
    String fileExtension();

    /** Human-readable name. */
    String algorithmName();
}

// ---------------------------------------------------------------------------
// Concrete strategies
// ---------------------------------------------------------------------------

/** Simulated GZIP: good balance of speed and compression ratio. */
class GzipStrategy implements CompressionStrategy {

    @Override
    public byte[] compress(byte[] data) {
        // Production code would use java.util.zip.GZIPOutputStream
        System.out.printf("  [GZIP] Compressing %d bytes...%n", data.length);
        // Simulate ~60% compression ratio for demo purposes
        int compressedLength = Math.max(1, (int)(data.length * 0.40));
        byte[] result = new byte[compressedLength];
        System.out.printf("  [GZIP] Result: %d bytes (ratio %.1f%%)%n",
                compressedLength, (1.0 - (double)compressedLength / data.length) * 100);
        return result;
    }

    @Override
    public byte[] decompress(byte[] data) {
        System.out.printf("  [GZIP] Decompressing %d bytes...%n", data.length);
        byte[] result = new byte[data.length * 2]; // restore original size (simplified)
        System.out.printf("  [GZIP] Restored: %d bytes%n", result.length);
        return result;
    }

    @Override public String fileExtension() { return ".gz"; }
    @Override public String algorithmName() { return "GZIP"; }
}

/** Simulated BZIP2: slower but achieves higher compression ratios. */
class Bzip2Strategy implements CompressionStrategy {

    @Override
    public byte[] compress(byte[] data) {
        System.out.printf("  [BZIP2] Compressing %d bytes (slower, better ratio)...%n", data.length);
        int compressedLength = Math.max(1, (int)(data.length * 0.30));
        byte[] result = new byte[compressedLength];
        System.out.printf("  [BZIP2] Result: %d bytes (ratio %.1f%%)%n",
                compressedLength, (1.0 - (double)compressedLength / data.length) * 100);
        return result;
    }

    @Override
    public byte[] decompress(byte[] data) {
        System.out.printf("  [BZIP2] Decompressing %d bytes...%n", data.length);
        byte[] result = new byte[data.length * 3];
        System.out.printf("  [BZIP2] Restored: %d bytes%n", result.length);
        return result;
    }

    @Override public String fileExtension() { return ".bz2"; }
    @Override public String algorithmName() { return "BZIP2"; }
}

/** Simulated LZ4: ultra-fast, modest ratio — ideal for real-time logging. */
class Lz4Strategy implements CompressionStrategy {

    @Override
    public byte[] compress(byte[] data) {
        System.out.printf("  [LZ4] Compressing %d bytes (ultra-fast)...%n", data.length);
        int compressedLength = Math.max(1, (int)(data.length * 0.55));
        byte[] result = new byte[compressedLength];
        System.out.printf("  [LZ4] Result: %d bytes (ratio %.1f%%)%n",
                compressedLength, (1.0 - (double)compressedLength / data.length) * 100);
        return result;
    }

    @Override
    public byte[] decompress(byte[] data) {
        System.out.printf("  [LZ4] Decompressing %d bytes (instant)...%n", data.length);
        byte[] result = new byte[(int)(data.length / 0.55)];
        System.out.printf("  [LZ4] Restored: %d bytes%n", result.length);
        return result;
    }

    @Override public String fileExtension() { return ".lz4"; }
    @Override public String algorithmName() { return "LZ4"; }
}

/** No-op strategy — stores files uncompressed. */
class NoCompressionStrategy implements CompressionStrategy {

    @Override
    public byte[] compress(byte[] data) {
        System.out.printf("  [None] Storing %d bytes uncompressed.%n", data.length);
        return data.clone();
    }

    @Override
    public byte[] decompress(byte[] data) {
        return data.clone();
    }

    @Override public String fileExtension() { return ""; }
    @Override public String algorithmName() { return "No Compression"; }
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

class FileArchiver {
    private CompressionStrategy strategy;
    private final Map<String, byte[]> archive = new HashMap<>();

    public FileArchiver(CompressionStrategy strategy) {
        this.strategy = strategy;
        System.out.println("[Archiver] Initialized with: " + strategy.algorithmName());
    }

    /** Hot-swap compression strategy at runtime. */
    public void setStrategy(CompressionStrategy strategy) {
        System.out.println("[Archiver] Switching strategy to: " + strategy.algorithmName());
        this.strategy = strategy;
    }

    public void addFile(String filename, byte[] content) {
        System.out.printf("%n[Archiver] Adding '%s' (%d bytes)%n", filename, content.length);
        byte[] compressed = strategy.compress(content);
        String storedName = filename + strategy.fileExtension();
        archive.put(storedName, compressed);
        System.out.printf("[Archiver] Stored as '%s'%n", storedName);
    }

    public byte[] extractFile(String storedName) {
        byte[] compressed = archive.get(storedName);
        if (compressed == null) throw new IllegalArgumentException("File not found: " + storedName);
        System.out.printf("%n[Archiver] Extracting '%s'%n", storedName);
        return strategy.decompress(compressed);
    }

    public void listContents() {
        System.out.println("\n[Archiver] Archive contents:");
        archive.forEach((name, data) ->
                System.out.printf("  %-40s %d bytes%n", name, data.length));
    }
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

public class StrategyPatternDemo {

    public static void main(String[] args) {
        // Simulate file content (1 MB log file)
        byte[] logFile    = new byte[1_000_000];
        byte[] configFile = new byte[5_000];
        byte[] imageFile  = new byte[500_000];

        System.out.println("=== Strategy Pattern — File Compression Demo ===");

        // Start with GZIP for general-purpose archiving
        FileArchiver archiver = new FileArchiver(new GzipStrategy());
        archiver.addFile("app.log", logFile);
        archiver.addFile("config.yaml", configFile);

        // Switch to BZIP2 for a large binary that benefits from higher ratio
        archiver.setStrategy(new Bzip2Strategy());
        archiver.addFile("database_dump.sql", logFile);

        // Images are already compressed — use no-op strategy
        archiver.setStrategy(new NoCompressionStrategy());
        archiver.addFile("photo.jpg", imageFile);

        archiver.listContents();

        // Extract a file
        archiver.setStrategy(new GzipStrategy());
        byte[] recovered = archiver.extractFile("app.log.gz");
        System.out.printf("%n[Demo] Recovered %d bytes from 'app.log.gz'%n", recovered.length);
    }
}
```

---

### C++

```cpp
/**
 * Real-world example: Investment portfolio rebalancing strategies.
 *
 * A Portfolio (Context) can rebalance its holdings using different
 * strategies: conservative (bonds-heavy), aggressive (equities-heavy),
 * or equal-weight. The strategy can be changed whenever market conditions
 * or investor risk appetite changes — without modifying Portfolio.
 */

#include <iostream>
#include <iomanip>
#include <map>
#include <memory>
#include <string>
#include <vector>

// ---------------------------------------------------------------------------
// Data types
// ---------------------------------------------------------------------------

struct Holding {
    std::string ticker;
    double      current_weight; // percentage of portfolio (0-100)
};

using Allocations = std::map<std::string, double>; // ticker -> target weight %

// ---------------------------------------------------------------------------
// Strategy interface
// ---------------------------------------------------------------------------

class RebalancingStrategy {
public:
    virtual ~RebalancingStrategy() = default;

    /**
     * Given the current holdings, compute target allocations.
     * Returns a map of ticker -> target weight (must sum to 100).
     */
    virtual Allocations compute_targets(const std::vector<Holding>& holdings) const = 0;

    virtual std::string name() const = 0;
};

// ---------------------------------------------------------------------------
// Concrete strategies
// ---------------------------------------------------------------------------

/** Conservative: 60% bonds / 30% large-cap equities / 10% cash. */
class ConservativeStrategy : public RebalancingStrategy {
public:
    Allocations compute_targets(const std::vector<Holding>& holdings) const override {
        Allocations targets;
        // Fixed allocation regardless of current weights
        targets["BND"]  = 40.0;  // Total bond market ETF
        targets["GOVT"] = 20.0;  // Government bonds
        targets["VTI"]  = 20.0;  // US total stock market
        targets["VEA"]  = 10.0;  // Developed markets
        targets["CASH"] = 10.0;  // Money market / cash
        return targets;
    }

    std::string name() const override { return "Conservative (60/30/10)"; }
};

/** Aggressive: 80% equities globally / 20% alternatives. */
class AggressiveGrowthStrategy : public RebalancingStrategy {
public:
    Allocations compute_targets(const std::vector<Holding>& holdings) const override {
        Allocations targets;
        targets["VTI"]  = 40.0;  // US stocks
        targets["VEA"]  = 20.0;  // Developed markets
        targets["VWO"]  = 20.0;  // Emerging markets
        targets["QQQ"]  = 15.0;  // Nasdaq-100 (tech tilt)
        targets["BND"]  =  5.0;  // Minimal bond allocation
        return targets;
    }

    std::string name() const override { return "Aggressive Growth (80/20)"; }
};

/** Equal-weight: distribute evenly across all existing holdings. */
class EqualWeightStrategy : public RebalancingStrategy {
public:
    Allocations compute_targets(const std::vector<Holding>& holdings) const override {
        Allocations targets;
        if (holdings.empty()) return targets;

        double equal_share = 100.0 / static_cast<double>(holdings.size());
        for (const auto& h : holdings) {
            targets[h.ticker] = equal_share;
        }
        return targets;
    }

    std::string name() const override { return "Equal-Weight"; }
};

/** Risk-parity: weight inversely proportional to simulated volatility. */
class RiskParityStrategy : public RebalancingStrategy {
    // Simulated annualised volatility for known tickers
    static std::map<std::string, double> volatility_lookup() {
        return {
            {"VTI",  0.15}, {"VEA",  0.16}, {"VWO",  0.20},
            {"BND",  0.05}, {"GOVT", 0.04}, {"QQQ",  0.22},
            {"CASH", 0.01}, {"GOLD", 0.14},
        };
    }

public:
    Allocations compute_targets(const std::vector<Holding>& holdings) const override {
        auto vol_map = volatility_lookup();
        Allocations inv_vol;
        double total_inv_vol = 0.0;

        for (const auto& h : holdings) {
            double vol = vol_map.count(h.ticker) ? vol_map[h.ticker] : 0.18;
            double inv = 1.0 / vol;
            inv_vol[h.ticker] = inv;
            total_inv_vol += inv;
        }

        Allocations targets;
        for (const auto& [ticker, inv] : inv_vol) {
            targets[ticker] = (inv / total_inv_vol) * 100.0;
        }
        return targets;
    }

    std::string name() const override { return "Risk-Parity"; }
};

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

class Portfolio {
    std::string                        name_;
    std::unique_ptr<RebalancingStrategy> strategy_;
    std::vector<Holding>               holdings_;
    double                             total_value_usd_;

public:
    Portfolio(std::string name,
              std::unique_ptr<RebalancingStrategy> strategy,
              double total_value_usd)
        : name_(std::move(name))
        , strategy_(std::move(strategy))
        , total_value_usd_(total_value_usd)
    {}

    void set_strategy(std::unique_ptr<RebalancingStrategy> strategy) {
        std::cout << "  [" << name_ << "] Switching to strategy: "
                  << strategy->name() << "\n";
        strategy_ = std::move(strategy);
    }

    void add_holding(const std::string& ticker, double current_weight) {
        holdings_.push_back({ticker, current_weight});
    }

    void rebalance() {
        std::cout << "\n--- Rebalancing '" << name_
                  << "' using [" << strategy_->name() << "] ---\n";

        Allocations targets = strategy_->compute_targets(holdings_);

        std::cout << std::fixed << std::setprecision(2);
        std::cout << std::left
                  << std::setw(8)  << "Ticker"
                  << std::setw(14) << "Current %"
                  << std::setw(14) << "Target %"
                  << std::setw(14) << "Delta %"
                  << "Trade ($)\n";
        std::cout << std::string(60, '-') << "\n";

        for (const auto& h : holdings_) {
            double target  = targets.count(h.ticker) ? targets[h.ticker] : 0.0;
            double delta   = target - h.current_weight;
            double trade   = (delta / 100.0) * total_value_usd_;

            std::cout << std::setw(8)  << h.ticker
                      << std::setw(14) << h.current_weight
                      << std::setw(14) << target
                      << std::setw(14) << delta
                      << "$" << trade << "\n";
        }

        // New tickers introduced by the strategy that aren't in current holdings
        for (const auto& [ticker, weight] : targets) {
            bool exists = false;
            for (const auto& h : holdings_) { if (h.ticker == ticker) { exists = true; break; } }
            if (!exists) {
                double trade = (weight / 100.0) * total_value_usd_;
                std::cout << std::setw(8)  << ticker
                          << std::setw(14) << 0.0
                          << std::setw(14) << weight
                          << std::setw(14) << weight
                          << "$" << trade << " (NEW)\n";
            }
        }
    }
};

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

int main() {
    std::cout << "=== Strategy Pattern — Portfolio Rebalancer ===\n";

    Portfolio portfolio("Retirement Fund",
                        std::make_unique<ConservativeStrategy>(),
                        500'000.0);

    portfolio.add_holding("VTI",  35.0);
    portfolio.add_holding("BND",  30.0);
    portfolio.add_holding("VEA",  20.0);
    portfolio.add_holding("CASH", 15.0);

    // Initial rebalance with conservative strategy
    portfolio.rebalance();

    // Investor decides to take more risk — swap strategy at runtime
    portfolio.set_strategy(std::make_unique<AggressiveGrowthStrategy>());
    portfolio.rebalance();

    // Use risk-parity for a more scientific approach
    portfolio.set_strategy(std::make_unique<RiskParityStrategy>());
    portfolio.rebalance();

    return 0;
}
```

---

### C#

```csharp
/**
 * Real-world example: Discount calculation engine for an e-commerce platform.
 *
 * Depending on the user's membership tier, active promotions, or time of year,
 * the CheckoutService (Context) applies a different DiscountStrategy.
 * Strategies are injected via DI — new promotions require no changes to
 * CheckoutService or the pricing engine.
 */

using System;
using System.Collections.Generic;

// ---------------------------------------------------------------------------
// Models
// ---------------------------------------------------------------------------

public class CartItem
{
    public string Name     { get; init; } = string.Empty;
    public decimal Price   { get; init; }
    public int Quantity    { get; init; }
    public string Category { get; init; } = string.Empty;
    public decimal Subtotal => Price * Quantity;
}

public class DiscountResult
{
    public string StrategyName   { get; init; } = string.Empty;
    public decimal OriginalTotal { get; init; }
    public decimal DiscountAmount { get; init; }
    public decimal FinalTotal    => OriginalTotal - DiscountAmount;
    public decimal DiscountPct   => OriginalTotal > 0
        ? Math.Round(DiscountAmount / OriginalTotal * 100, 1)
        : 0;
}

// ---------------------------------------------------------------------------
// Strategy interface
// ---------------------------------------------------------------------------

public interface IDiscountStrategy
{
    string Name { get; }

    /// <summary>
    /// Compute the discount to apply to the given cart items.
    /// Returns the discount amount (not the final price).
    /// </summary>
    decimal ComputeDiscount(IReadOnlyList<CartItem> items);
}

// ---------------------------------------------------------------------------
// Concrete strategies
// ---------------------------------------------------------------------------

/// <summary>No discount — regular customers.</summary>
public class NoDiscountStrategy : IDiscountStrategy
{
    public string Name => "Standard Pricing";
    public decimal ComputeDiscount(IReadOnlyList<CartItem> items) => 0m;
}

/// <summary>Flat percentage off the entire order — e.g., loyalty members.</summary>
public class PercentageDiscountStrategy : IDiscountStrategy
{
    private readonly decimal _percentage;

    public PercentageDiscountStrategy(decimal percentage)
    {
        if (percentage < 0 || percentage > 100)
            throw new ArgumentOutOfRangeException(nameof(percentage));
        _percentage = percentage;
    }

    public string Name => $"{_percentage}% Off Everything";

    public decimal ComputeDiscount(IReadOnlyList<CartItem> items)
    {
        decimal total = 0m;
        foreach (var item in items) total += item.Subtotal;
        return Math.Round(total * (_percentage / 100m), 2);
    }
}

/// <summary>Buy-one-get-one-free on the cheapest qualifying item in each pair.</summary>
public class Bogo50Strategy : IDiscountStrategy
{
    public string Name => "Buy One Get One 50% Off";

    public decimal ComputeDiscount(IReadOnlyList<CartItem> items)
    {
        decimal discount = 0m;
        foreach (var item in items)
        {
            // Every second unit is 50% off
            int freePairs = item.Quantity / 2;
            discount += freePairs * item.Price * 0.50m;
        }
        return Math.Round(discount, 2);
    }
}

/// <summary>Category-specific discount — e.g., 20% off all Electronics.</summary>
public class CategoryDiscountStrategy : IDiscountStrategy
{
    private readonly string _category;
    private readonly decimal _percentage;

    public CategoryDiscountStrategy(string category, decimal percentage)
    {
        _category   = category;
        _percentage = percentage;
    }

    public string Name => $"{_percentage}% Off {_category}";

    public decimal ComputeDiscount(IReadOnlyList<CartItem> items)
    {
        decimal discount = 0m;
        foreach (var item in items)
        {
            if (string.Equals(item.Category, _category, StringComparison.OrdinalIgnoreCase))
                discount += item.Subtotal * (_percentage / 100m);
        }
        return Math.Round(discount, 2);
    }
}

/// <summary>Tiered volume discount — more items = bigger percentage off.</summary>
public class VolumeDiscountStrategy : IDiscountStrategy
{
    // (minimumSubtotal, discountPct) — evaluated highest-first
    private static readonly (decimal Threshold, decimal Pct)[] Tiers =
    {
        (500m, 15m),
        (200m, 10m),
        (100m,  5m),
    };

    public string Name => "Volume Discount (5/10/15%)";

    public decimal ComputeDiscount(IReadOnlyList<CartItem> items)
    {
        decimal total = 0m;
        foreach (var item in items) total += item.Subtotal;

        foreach (var (threshold, pct) in Tiers)
        {
            if (total >= threshold)
                return Math.Round(total * (pct / 100m), 2);
        }
        return 0m;
    }
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

public class CheckoutService
{
    private IDiscountStrategy _strategy;

    public CheckoutService(IDiscountStrategy strategy)
    {
        _strategy = strategy;
    }

    /// <summary>Hot-swap the discount strategy (e.g., when a coupon code is applied).</summary>
    public void ApplyPromotion(IDiscountStrategy strategy)
    {
        Console.WriteLine($"  [Checkout] Promotion applied: {strategy.Name}");
        _strategy = strategy;
    }

    public DiscountResult ProcessCart(IReadOnlyList<CartItem> items)
    {
        decimal original = 0m;
        foreach (var item in items) original += item.Subtotal;

        decimal discount = _strategy.ComputeDiscount(items);

        return new DiscountResult
        {
            StrategyName  = _strategy.Name,
            OriginalTotal = original,
            DiscountAmount = discount,
        };
    }
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

class Program
{
    static void PrintResult(DiscountResult r)
    {
        Console.WriteLine($"  Strategy      : {r.StrategyName}");
        Console.WriteLine($"  Original total: ${r.OriginalTotal:F2}");
        Console.WriteLine($"  Discount      : -${r.DiscountAmount:F2} ({r.DiscountPct}%)");
        Console.WriteLine($"  You pay       : ${r.FinalTotal:F2}");
    }

    static void Main()
    {
        var cart = new List<CartItem>
        {
            new() { Name = "Laptop",       Price = 999.99m, Quantity = 1, Category = "Electronics" },
            new() { Name = "HDMI Cable",   Price =  19.99m, Quantity = 3, Category = "Electronics" },
            new() { Name = "Office Chair", Price = 249.99m, Quantity = 1, Category = "Furniture"   },
            new() { Name = "Notebook",     Price =   4.99m, Quantity = 5, Category = "Stationery"  },
        };

        Console.WriteLine("=== Strategy Pattern — Checkout Discount Engine ===\n");

        var checkout = new CheckoutService(new NoDiscountStrategy());

        Console.WriteLine("--- Scenario 1: Guest customer (no discount) ---");
        PrintResult(checkout.ProcessCart(cart));

        Console.WriteLine("\n--- Scenario 2: Loyalty member (10% off) ---");
        checkout.ApplyPromotion(new PercentageDiscountStrategy(10m));
        PrintResult(checkout.ProcessCart(cart));

        Console.WriteLine("\n--- Scenario 3: Flash sale — 25% off Electronics ---");
        checkout.ApplyPromotion(new CategoryDiscountStrategy("Electronics", 25m));
        PrintResult(checkout.ProcessCart(cart));

        Console.WriteLine("\n--- Scenario 4: Volume order (auto-tier) ---");
        checkout.ApplyPromotion(new VolumeDiscountStrategy());
        PrintResult(checkout.ProcessCart(cart));

        Console.WriteLine("\n--- Scenario 5: BOGO 50% weekend promo ---");
        checkout.ApplyPromotion(new Bogo50Strategy());
        PrintResult(checkout.ProcessCart(cart));
    }
}
```

---

### TypeScript

```typescript
/**
 * Real-world example: Authentication system supporting multiple providers.
 *
 * An AuthService (Context) can authenticate users via Local (email/password),
 * OAuth (Google, GitHub), or API-key strategies. New providers are added by
 * implementing AuthStrategy — zero changes to AuthService required.
 */

// ---------------------------------------------------------------------------
// Models
// ---------------------------------------------------------------------------

interface Credentials {
  [key: string]: string | undefined;
}

interface AuthResult {
  success: boolean;
  userId?: string;
  displayName?: string;
  provider: string;
  token?: string;
  error?: string;
}

// ---------------------------------------------------------------------------
// Strategy interface
// ---------------------------------------------------------------------------

interface AuthStrategy {
  readonly providerName: string;
  authenticate(credentials: Credentials): Promise<AuthResult>;
}

// ---------------------------------------------------------------------------
// Concrete strategies
// ---------------------------------------------------------------------------

/** Local email + bcrypt-hashed password authentication. */
class LocalAuthStrategy implements AuthStrategy {
  readonly providerName = "Local";

  // Simulated user store (production: database query + bcrypt compare)
  private readonly users = new Map([
    ["alice@example.com", { passwordHash: "hashed_password_1", id: "usr_001", name: "Alice" }],
    ["bob@example.com",   { passwordHash: "hashed_password_2", id: "usr_002", name: "Bob"   }],
  ]);

  async authenticate(credentials: Credentials): Promise<AuthResult> {
    const { email, password } = credentials;

    if (!email || !password) {
      return { success: false, provider: this.providerName, error: "Email and password required." };
    }

    const user = this.users.get(email);
    if (!user) {
      return { success: false, provider: this.providerName, error: "No account found for that email." };
    }

    // Simulate bcrypt compare (always succeeds for demo)
    const valid = password.length >= 6; // simplified check
    if (!valid) {
      return { success: false, provider: this.providerName, error: "Invalid credentials." };
    }

    return {
      success: true,
      userId: user.id,
      displayName: user.name,
      provider: this.providerName,
      token: `local_jwt_${user.id}_${Date.now()}`,
    };
  }
}

/** Google OAuth 2.0 — exchanges an auth code for a profile. */
class GoogleOAuthStrategy implements AuthStrategy {
  readonly providerName = "Google";

  constructor(private readonly clientId: string, private readonly clientSecret: string) {}

  async authenticate(credentials: Credentials): Promise<AuthResult> {
    const { code } = credentials;

    if (!code) {
      return { success: false, provider: this.providerName, error: "OAuth authorization code required." };
    }

    // Simulate token exchange with Google's endpoint
    console.log(`  [Google] Exchanging auth code with client_id=${this.clientId}...`);
    await this.simulateNetworkDelay(120);

    if (code === "invalid") {
      return { success: false, provider: this.providerName, error: "Invalid or expired authorization code." };
    }

    return {
      success: true,
      userId: "google_sub_12345",
      displayName: "Charlie (Google)",
      provider: this.providerName,
      token: `google_access_token_${Date.now()}`,
    };
  }

  private simulateNetworkDelay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

/** API-key based authentication for machine-to-machine requests. */
class ApiKeyStrategy implements AuthStrategy {
  readonly providerName = "API Key";

  // Simulated key store (production: Redis / DB lookup + rate-limit check)
  private readonly validKeys = new Map([
    ["key_prod_abc123", { ownerId: "svc_reporting", scope: "read:reports" }],
    ["key_prod_def456", { ownerId: "svc_billing",   scope: "write:invoices" }],
  ]);

  async authenticate(credentials: Credentials): Promise<AuthResult> {
    const { apiKey } = credentials;

    if (!apiKey) {
      return { success: false, provider: this.providerName, error: "API key header missing." };
    }

    const keyRecord = this.validKeys.get(apiKey);
    if (!keyRecord) {
      return { success: false, provider: this.providerName, error: "Invalid or revoked API key." };
    }

    return {
      success: true,
      userId: keyRecord.ownerId,
      displayName: `Service: ${keyRecord.ownerId}`,
      provider: this.providerName,
      token: apiKey, // API keys are self-contained
    };
  }
}

/** SAML-based SSO for enterprise clients. */
class SamlSsoStrategy implements AuthStrategy {
  readonly providerName = "SAML SSO";

  constructor(private readonly idpEntityId: string) {}

  async authenticate(credentials: Credentials): Promise<AuthResult> {
    const { samlResponse } = credentials;

    if (!samlResponse) {
      return { success: false, provider: this.providerName, error: "SAML response XML required." };
    }

    // Simulate XML signature verification and attribute extraction
    console.log(`  [SAML] Verifying assertion from IdP: ${this.idpEntityId}`);

    const email = "enterprise.user@corp.example.com"; // extracted from assertion
    return {
      success: true,
      userId: "saml_uid_789",
      displayName: `Enterprise User (${email})`,
      provider: this.providerName,
      token: `saml_session_${Date.now()}`,
    };
  }
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

class AuthService {
  private strategy: AuthStrategy;
  private readonly auditLog: Array<{ timestamp: Date; provider: string; success: boolean }> = [];

  constructor(defaultStrategy: AuthStrategy) {
    this.strategy = defaultStrategy;
  }

  /** Switch provider — e.g., after detecting the user's email domain for SSO. */
  setStrategy(strategy: AuthStrategy): void {
    console.log(`  [AuthService] Using provider: ${strategy.providerName}`);
    this.strategy = strategy;
  }

  async login(credentials: Credentials): Promise<AuthResult> {
    const result = await this.strategy.authenticate(credentials);

    // Audit logging — completely decoupled from which strategy ran
    this.auditLog.push({
      timestamp: new Date(),
      provider:  result.provider,
      success:   result.success,
    });

    return result;
  }

  printAuditLog(): void {
    console.log("\n=== Audit Log ===");
    for (const entry of this.auditLog) {
      const status = entry.success ? "SUCCESS" : "FAILURE";
      console.log(`  [${entry.timestamp.toISOString()}] ${entry.provider}: ${status}`);
    }
  }
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  console.log("=== Strategy Pattern — Authentication Service ===\n");

  const authService = new AuthService(new LocalAuthStrategy());

  // 1. Local login
  console.log("--- Local Login (valid) ---");
  authService.setStrategy(new LocalAuthStrategy());
  let result = await authService.login({ email: "alice@example.com", password: "securePass" });
  console.log(`  Result: ${result.success ? "OK" : "FAIL"} — ${result.displayName ?? result.error}`);

  // 2. Local login with wrong password
  console.log("\n--- Local Login (bad password) ---");
  result = await authService.login({ email: "alice@example.com", password: "123" });
  console.log(`  Result: ${result.success ? "OK" : "FAIL"} — ${result.error}`);

  // 3. Switch to Google OAuth
  console.log("\n--- Google OAuth ---");
  authService.setStrategy(new GoogleOAuthStrategy("client_id_123", "client_secret_456"));
  result = await authService.login({ code: "google_auth_code_xyz" });
  console.log(`  Result: ${result.success ? "OK" : "FAIL"} — ${result.displayName}`);

  // 4. API key for a microservice
  console.log("\n--- API Key (machine-to-machine) ---");
  authService.setStrategy(new ApiKeyStrategy());
  result = await authService.login({ apiKey: "key_prod_abc123" });
  console.log(`  Result: ${result.success ? "OK" : "FAIL"} — ${result.displayName}`);

  // 5. Invalid API key
  console.log("\n--- API Key (revoked) ---");
  result = await authService.login({ apiKey: "key_revoked_xyz" });
  console.log(`  Result: ${result.success ? "OK" : "FAIL"} — ${result.error}`);

  // 6. SAML SSO for an enterprise domain
  console.log("\n--- SAML SSO (enterprise) ---");
  authService.setStrategy(new SamlSsoStrategy("https://idp.corp.example.com"));
  result = await authService.login({ samlResponse: "<SAMLResponse>...</SAMLResponse>" });
  console.log(`  Result: ${result.success ? "OK" : "FAIL"} — ${result.displayName}`);

  authService.printAuditLog();
}

main().catch(console.error);
```

---

### Go

```go
// Real-world example: Log output formatter for a structured logging library.
//
// A Logger (Context) can format log entries as plain text, JSON, or
// logfmt (key=value pairs). The formatter (strategy) is injected at
// construction and may be hot-swapped — useful when the same logger
// must write to a human-readable console in development but emit JSON
// to stdout for a log aggregator in production.

package main

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// ---------------------------------------------------------------------------
// Models
// ---------------------------------------------------------------------------

// Level represents a log severity level.
type Level int

const (
	DEBUG Level = iota
	INFO
	WARN
	ERROR
)

func (l Level) String() string {
	return [...]string{"DEBUG", "INFO", "WARN", "ERROR"}[l]
}

// Entry is a structured log record before formatting.
type Entry struct {
	Timestamp time.Time
	Level     Level
	Message   string
	Fields    map[string]any
}

// ---------------------------------------------------------------------------
// Strategy interface
// ---------------------------------------------------------------------------

// Formatter defines the strategy interface for log entry formatting.
type Formatter interface {
	Format(entry Entry) string
	ContentType() string // e.g. "text/plain", "application/json"
}

// ---------------------------------------------------------------------------
// Concrete strategies
// ---------------------------------------------------------------------------

// TextFormatter renders log entries in a human-friendly, coloured format.
type TextFormatter struct {
	UseColor bool
}

func (f TextFormatter) Format(entry Entry) string {
	levelStr := entry.Level.String()
	if f.UseColor {
		colors := map[Level]string{
			DEBUG: "\033[36m", // cyan
			INFO:  "\033[32m", // green
			WARN:  "\033[33m", // yellow
			ERROR: "\033[31m", // red
		}
		reset := "\033[0m"
		levelStr = colors[entry.Level] + levelStr + reset
	}

	ts := entry.Timestamp.Format("2006-01-02 15:04:05.000")
	var sb strings.Builder
	fmt.Fprintf(&sb, "%s [%s] %s", ts, levelStr, entry.Message)

	for k, v := range entry.Fields {
		fmt.Fprintf(&sb, " %s=%v", k, v)
	}
	return sb.String()
}

func (f TextFormatter) ContentType() string { return "text/plain" }

// JSONFormatter renders log entries as newline-delimited JSON (NDJSON).
type JSONFormatter struct {
	PrettyPrint bool
}

func (f JSONFormatter) Format(entry Entry) string {
	record := map[string]any{
		"time":    entry.Timestamp.UTC().Format(time.RFC3339Nano),
		"level":   entry.Level.String(),
		"message": entry.Message,
	}
	for k, v := range entry.Fields {
		record[k] = v
	}

	var data []byte
	var err error
	if f.PrettyPrint {
		data, err = json.MarshalIndent(record, "", "  ")
	} else {
		data, err = json.Marshal(record)
	}
	if err != nil {
		return fmt.Sprintf(`{"error":"marshal failed: %s"}`, err)
	}
	return string(data)
}

func (f JSONFormatter) ContentType() string { return "application/json" }

// LogfmtFormatter renders entries in the logfmt key=value format.
// See: https://brandur.org/logfmt
type LogfmtFormatter struct{}

func (f LogfmtFormatter) Format(entry Entry) string {
	var parts []string
	parts = append(parts, fmt.Sprintf("time=%s", entry.Timestamp.UTC().Format(time.RFC3339)))
	parts = append(parts, fmt.Sprintf("level=%s", strings.ToLower(entry.Level.String())))
	parts = append(parts, fmt.Sprintf("msg=%q", entry.Message))

	for k, v := range entry.Fields {
		switch val := v.(type) {
		case string:
			parts = append(parts, fmt.Sprintf("%s=%q", k, val))
		default:
			parts = append(parts, fmt.Sprintf("%s=%v", k, val))
		}
	}
	return strings.Join(parts, " ")
}

func (f LogfmtFormatter) ContentType() string { return "text/plain" }

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

// Logger is the context. It holds a Formatter and writes formatted entries
// to an output sink (here, stdout for simplicity).
type Logger struct {
	formatter Formatter
	minLevel  Level
	fields    map[string]any // base fields attached to every entry
}

// NewLogger creates a Logger with the given formatter.
func NewLogger(formatter Formatter, minLevel Level) *Logger {
	return &Logger{
		formatter: formatter,
		minLevel:  minLevel,
		fields:    make(map[string]any),
	}
}

// SetFormatter hot-swaps the output formatter.
func (l *Logger) SetFormatter(f Formatter) {
	l.formatter = f
	l.log(INFO, "Formatter changed", map[string]any{"content_type": f.ContentType()})
}

// WithField returns a new Logger that always includes the given field.
func (l *Logger) WithField(key string, value any) *Logger {
	newFields := make(map[string]any, len(l.fields)+1)
	for k, v := range l.fields {
		newFields[k] = v
	}
	newFields[key] = value
	return &Logger{formatter: l.formatter, minLevel: l.minLevel, fields: newFields}
}

func (l *Logger) log(level Level, msg string, extra map[string]any) {
	if level < l.minLevel {
		return
	}

	merged := make(map[string]any, len(l.fields)+len(extra))
	for k, v := range l.fields {
		merged[k] = v
	}
	for k, v := range extra {
		merged[k] = v
	}

	entry := Entry{
		Timestamp: time.Now(),
		Level:     level,
		Message:   msg,
		Fields:    merged,
	}
	fmt.Println(l.formatter.Format(entry))
}

func (l *Logger) Debug(msg string, fields ...map[string]any) {
	var f map[string]any
	if len(fields) > 0 {
		f = fields[0]
	}
	l.log(DEBUG, msg, f)
}

func (l *Logger) Info(msg string, fields ...map[string]any) {
	var f map[string]any
	if len(fields) > 0 {
		f = fields[0]
	}
	l.log(INFO, msg, f)
}

func (l *Logger) Warn(msg string, fields ...map[string]any) {
	var f map[string]any
	if len(fields) > 0 {
		f = fields[0]
	}
	l.log(WARN, msg, f)
}

func (l *Logger) Error(msg string, fields ...map[string]any) {
	var f map[string]any
	if len(fields) > 0 {
		f = fields[0]
	}
	l.log(ERROR, msg, f)
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

func main() {
	fmt.Println("=== Strategy Pattern — Pluggable Log Formatter ===\n")

	// Development: human-readable text with colour
	log := NewLogger(TextFormatter{UseColor: false}, DEBUG)
	log.Info("Server starting", map[string]any{"port": 8080, "env": "development"})
	log.Debug("Database connection pool initialised", map[string]any{"pool_size": 10})

	// Attach a persistent request_id to a derived logger
	reqLog := log.WithField("request_id", "req_abc123")
	reqLog.Info("Handling HTTP request", map[string]any{"method": "GET", "path": "/api/users"})
	reqLog.Warn("Rate limit approaching", map[string]any{"remaining": 5})
	reqLog.Error("Upstream timeout", map[string]any{"upstream": "payments-svc", "latency_ms": 5002})

	fmt.Println("\n--- Switching to JSON formatter (production mode) ---")
	log.SetFormatter(JSONFormatter{PrettyPrint: false})
	log.Info("Deployment complete", map[string]any{"version": "v2.3.1", "commit": "a1b2c3d"})
	log.Error("Disk usage critical", map[string]any{"used_pct": 91.5, "volume": "/data"})

	fmt.Println("\n--- Switching to logfmt formatter (log aggregator) ---")
	log.SetFormatter(LogfmtFormatter{})
	log.Info("Cache warmed", map[string]any{"keys": 42000, "duration_ms": 380})
}
```

---

### PHP

```php
<?php
/**
 * Real-world example: Payment processing gateway.
 *
 * A PaymentProcessor (Context) can process transactions via Stripe,
 * PayPal, or a bank transfer. Each provider has its own API, fee
 * structure, and error handling — encapsulated in its own strategy.
 * The Context remains unchanged when a new payment provider is added.
 */

declare(strict_types=1);

// ---------------------------------------------------------------------------
// Models
// ---------------------------------------------------------------------------

final class Money
{
    public function __construct(
        public readonly float  $amount,
        public readonly string $currency = 'USD',
    ) {}

    public function formatted(): string
    {
        return number_format($this->amount, 2) . ' ' . $this->currency;
    }
}

final class PaymentResult
{
    public function __construct(
        public readonly bool   $success,
        public readonly string $transactionId,
        public readonly string $provider,
        public readonly Money  $charged,
        public readonly float  $fee,
        public readonly string $message,
    ) {}
}

// ---------------------------------------------------------------------------
// Strategy interface
// ---------------------------------------------------------------------------

interface PaymentStrategy
{
    public function getName(): string;

    /**
     * Process a payment and return a PaymentResult.
     * Throws \RuntimeException on unrecoverable failure.
     */
    public function processPayment(Money $amount, array $details): PaymentResult;

    /** Return the processing fee for a given amount (in the same currency). */
    public function calculateFee(Money $amount): float;
}

// ---------------------------------------------------------------------------
// Concrete strategies
// ---------------------------------------------------------------------------

final class StripeStrategy implements PaymentStrategy
{
    private const PERCENTAGE_FEE = 0.029; // 2.9%
    private const FIXED_FEE      = 0.30;  // $0.30 per transaction

    public function __construct(private readonly string $apiKey) {}

    public function getName(): string { return 'Stripe'; }

    public function processPayment(Money $amount, array $details): PaymentResult
    {
        $cardNumber = $details['card_number'] ?? '';
        echo "  [Stripe] Charging card ending in " . substr($cardNumber, -4) . "...\n";

        // Simulate Stripe API call
        if ($amount->amount <= 0) {
            throw new \RuntimeException('Amount must be positive.');
        }

        $fee = $this->calculateFee($amount);
        $txId = 'ch_' . bin2hex(random_bytes(8));

        echo "  [Stripe] Transaction {$txId} approved.\n";

        return new PaymentResult(
            success:       true,
            transactionId: $txId,
            provider:      $this->getName(),
            charged:       $amount,
            fee:           $fee,
            message:       'Payment successful',
        );
    }

    public function calculateFee(Money $amount): float
    {
        return round($amount->amount * self::PERCENTAGE_FEE + self::FIXED_FEE, 2);
    }
}

final class PayPalStrategy implements PaymentStrategy
{
    private const PERCENTAGE_FEE = 0.0349; // 3.49%
    private const FIXED_FEE      = 0.49;

    public function __construct(
        private readonly string $clientId,
        private readonly string $clientSecret,
    ) {}

    public function getName(): string { return 'PayPal'; }

    public function processPayment(Money $amount, array $details): PaymentResult
    {
        $email = $details['paypal_email'] ?? 'unknown@example.com';
        echo "  [PayPal] Requesting payment from account: {$email}...\n";

        // Simulate PayPal REST API — capture order
        $fee  = $this->calculateFee($amount);
        $txId = 'PAYID-' . strtoupper(bin2hex(random_bytes(6)));

        echo "  [PayPal] Capture {$txId} completed.\n";

        return new PaymentResult(
            success:       true,
            transactionId: $txId,
            provider:      $this->getName(),
            charged:       $amount,
            fee:           $fee,
            message:       'PayPal capture successful',
        );
    }

    public function calculateFee(Money $amount): float
    {
        return round($amount->amount * self::PERCENTAGE_FEE + self::FIXED_FEE, 2);
    }
}

final class BankTransferStrategy implements PaymentStrategy
{
    private const FLAT_FEE = 1.50; // Low fixed fee, no percentage

    public function getName(): string { return 'Bank Transfer (ACH)'; }

    public function processPayment(Money $amount, array $details): PaymentResult
    {
        $account = $details['account_number'] ?? '****';
        $routing = $details['routing_number'] ?? '****';
        echo "  [ACH] Initiating transfer from account {$account} / routing {$routing}...\n";

        if ($amount->amount < 1.00) {
            throw new \RuntimeException('ACH minimum transfer is $1.00.');
        }

        $txId = 'ACH' . date('Ymd') . rand(10000, 99999);
        echo "  [ACH] Transfer {$txId} queued (1-3 business days).\n";

        return new PaymentResult(
            success:       true,
            transactionId: $txId,
            provider:      $this->getName(),
            charged:       $amount,
            fee:           self::FLAT_FEE,
            message:       'ACH transfer initiated — funds will settle in 1-3 business days',
        );
    }

    public function calculateFee(Money $amount): float
    {
        return self::FLAT_FEE;
    }
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

final class PaymentProcessor
{
    private PaymentStrategy $strategy;
    private array $receiptLog = [];

    public function __construct(PaymentStrategy $strategy)
    {
        $this->strategy = $strategy;
    }

    public function setStrategy(PaymentStrategy $strategy): void
    {
        echo "\n  [Processor] Switching payment provider to: {$strategy->getName()}\n";
        $this->strategy = $strategy;
    }

    public function charge(Money $amount, array $details): PaymentResult
    {
        $fee   = $this->strategy->calculateFee($amount);
        $total = new Money($amount->amount + $fee, $amount->currency);

        echo "\n[Processor] Charging {$amount->formatted()} (+ fee {$fee}) via {$this->strategy->getName()}\n";

        $result = $this->strategy->processPayment($amount, $details);
        $this->receiptLog[] = $result;

        return $result;
    }

    public function compareFees(Money $amount, array $strategies): void
    {
        echo "\n[Processor] Fee comparison for {$amount->formatted()}:\n";
        foreach ($strategies as $s) {
            $fee = $s->calculateFee($amount);
            printf("  %-25s fee: $%.2f\n", $s->getName(), $fee);
        }
    }

    public function printReceipts(): void
    {
        echo "\n=== Transaction History ===\n";
        foreach ($this->receiptLog as $r) {
            $status = $r->success ? 'OK' : 'FAIL';
            printf(
                "  [%s] %s | %s | Charged: %s | Fee: $%.2f\n",
                $status,
                $r->transactionId,
                $r->provider,
                $r->charged->formatted(),
                $r->fee,
            );
        }
    }
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

echo "=== Strategy Pattern — Payment Processing Gateway ===\n";

$stripe  = new StripeStrategy(apiKey: 'sk_live_...');
$paypal  = new PayPalStrategy(clientId: 'AaBb...', clientSecret: 'XxYy...');
$ach     = new BankTransferStrategy();

$processor = new PaymentProcessor($stripe);

// Compare fees before the customer chooses
$amount = new Money(199.99);
$processor->compareFees($amount, [$stripe, $paypal, $ach]);

// Customer selects Stripe
$result = $processor->charge(
    $amount,
    ['card_number' => '4242424242424242', 'cvv' => '123'],
);
echo "  Receipt: {$result->message} (ID: {$result->transactionId})\n";

// Customer switches to PayPal for a second purchase
$processor->setStrategy($paypal);
$result = $processor->charge(
    new Money(49.00),
    ['paypal_email' => 'customer@example.com'],
);
echo "  Receipt: {$result->message} (ID: {$result->transactionId})\n";

// Large B2B invoice — use bank transfer to minimise fees
$processor->setStrategy($ach);
$result = $processor->charge(
    new Money(12500.00),
    ['account_number' => '123456789', 'routing_number' => '021000021'],
);
echo "  Receipt: {$result->message}\n";

$processor->printReceipts();
```

---

### Ruby

```ruby
# Real-world example: Report export engine.
#
# A ReportExporter (Context) can render the same data to PDF, CSV, HTML,
# or JSON. The format is chosen at runtime — for example, based on a
# user's "Download As" selection in a web application. Adding a new
# format requires only a new strategy class; the exporter never changes.

require 'json'
require 'time'

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

SalesRecord = Struct.new(:date, :product, :region, :units, :revenue, keyword_init: true)

# ---------------------------------------------------------------------------
# Strategy interface (duck-typed in Ruby, documented as a module contract)
# ---------------------------------------------------------------------------

module ExportStrategy
  # @param data [Array<SalesRecord>]
  # @param title [String]
  # @return [String] the formatted output
  def export(data, title:)
    raise NotImplementedError, "#{self.class}#export not implemented"
  end

  def file_extension
    raise NotImplementedError
  end

  def mime_type
    raise NotImplementedError
  end
end

# ---------------------------------------------------------------------------
# Concrete strategies
# ---------------------------------------------------------------------------

class CsvExportStrategy
  include ExportStrategy

  SEPARATOR = ','

  def export(data, title:)
    rows = []
    rows << "# #{title}"
    rows << "# Generated: #{Time.now.utc.iso8601}"
    rows << ['Date', 'Product', 'Region', 'Units', 'Revenue'].join(SEPARATOR)

    data.each do |r|
      rows << [r.date, r.product, r.region, r.units, format('%.2f', r.revenue)].join(SEPARATOR)
    end

    # Summary row
    total_units   = data.sum(&:units)
    total_revenue = data.sum(&:revenue)
    rows << ['TOTAL', '', '', total_units, format('%.2f', total_revenue)].join(SEPARATOR)

    rows.join("\n")
  end

  def file_extension = '.csv'
  def mime_type      = 'text/csv'
end

class JsonExportStrategy
  include ExportStrategy

  def export(data, title:)
    payload = {
      title:      title,
      generated:  Time.now.utc.iso8601,
      record_count: data.size,
      totals: {
        units:   data.sum(&:units),
        revenue: data.sum(&:revenue).round(2)
      },
      records: data.map do |r|
        { date: r.date, product: r.product, region: r.region,
          units: r.units, revenue: r.revenue.round(2) }
      end
    }
    JSON.pretty_generate(payload)
  end

  def file_extension = '.json'
  def mime_type      = 'application/json'
end

class HtmlExportStrategy
  include ExportStrategy

  def export(data, title:)
    total_units   = data.sum(&:units)
    total_revenue = data.sum(&:revenue)

    rows = data.map do |r|
      <<~ROW
        <tr>
          <td>#{escape(r.date)}</td>
          <td>#{escape(r.product)}</td>
          <td>#{escape(r.region)}</td>
          <td style="text-align:right">#{r.units}</td>
          <td style="text-align:right">$#{'%.2f' % r.revenue}</td>
        </tr>
      ROW
    end.join

    <<~HTML
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <title>#{escape(title)}</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 2rem; }
          h1   { color: #333; }
          table { border-collapse: collapse; width: 100%; }
          th, td { border: 1px solid #ccc; padding: 0.5rem 0.75rem; }
          th   { background: #4a90d9; color: #fff; }
          tr:nth-child(even) { background: #f5f5f5; }
          .total td { font-weight: bold; background: #e0f0e0; }
        </style>
      </head>
      <body>
        <h1>#{escape(title)}</h1>
        <p>Generated: #{Time.now.utc.strftime('%Y-%m-%d %H:%M UTC')}</p>
        <table>
          <thead>
            <tr><th>Date</th><th>Product</th><th>Region</th>
                <th>Units</th><th>Revenue</th></tr>
          </thead>
          <tbody>
            #{rows}
          </tbody>
          <tfoot>
            <tr class="total">
              <td colspan="3">TOTAL</td>
              <td style="text-align:right">#{total_units}</td>
              <td style="text-align:right">$#{'%.2f' % total_revenue}</td>
            </tr>
          </tfoot>
        </table>
      </body>
      </html>
    HTML
  end

  def file_extension = '.html'
  def mime_type      = 'text/html'

  private

  def escape(str)
    str.to_s
       .gsub('&', '&amp;')
       .gsub('<', '&lt;')
       .gsub('>', '&gt;')
       .gsub('"', '&quot;')
  end
end

class MarkdownExportStrategy
  include ExportStrategy

  def export(data, title:)
    header = "# #{title}\n\n_Generated: #{Time.now.utc.iso8601}_\n\n"

    col_w = [8, 20, 12, 7, 12] # approx column widths
    sep   = col_w.map { |w| '-' * w }.join(' | ')

    table_header = "| %-#{col_w[0]}s | %-#{col_w[1]}s | %-#{col_w[2]}s | %#{col_w[3]}s | %#{col_w[4]}s |" %
                   %w[Date Product Region Units Revenue]
    table_sep    = "|#{sep.split(' | ').map { |s| '-' + s + '-' }.join('|')}|"

    rows = data.map do |r|
      "| %-#{col_w[0]}s | %-#{col_w[1]}s | %-#{col_w[2]}s | %#{col_w[3]}d | %#{col_w[4]}s |" %
        [r.date, r.product, r.region, r.units, "$#{'%.2f' % r.revenue}"]
    end

    total_row = "| %-#{col_w[0]}s | %-#{col_w[1]}s | %-#{col_w[2]}s | %#{col_w[3]}d | %#{col_w[4]}s |" %
                ['TOTAL', '', '', data.sum(&:units), "$#{'%.2f' % data.sum(&:revenue)}"]

    [header, table_header, table_sep, *rows, table_sep, total_row].join("\n")
  end

  def file_extension = '.md'
  def mime_type      = 'text/markdown'
end

# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

class ReportExporter
  def initialize(strategy)
    @strategy = strategy
  end

  # Allow swapping format without recreating the exporter
  def set_format(strategy)
    puts "  [Exporter] Format switched to: #{strategy.class.name}"
    @strategy = strategy
  end

  def export(data, title:, output_path: nil)
    output   = @strategy.export(data, title: title)
    filename = output_path || "report#{@strategy.file_extension}"

    # In a real app: File.write(filename, output)
    preview = output.lines.first(6).join
    puts "\n[Exporter] Wrote #{output.bytesize} bytes to '#{filename}' (#{@strategy.mime_type})"
    puts "  Preview (first 6 lines):"
    preview.each_line { |l| puts "    #{l.chomp}" }
    output
  end
end

# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

puts "=== Strategy Pattern — Report Export Engine ===\n"

sales_data = [
  SalesRecord.new(date: '2026-01-15', product: 'Widget Pro',    region: 'North America', units: 120,  revenue: 5_880.00),
  SalesRecord.new(date: '2026-01-22', product: 'Gadget Lite',   region: 'Europe',        units:  85,  revenue: 2_550.00),
  SalesRecord.new(date: '2026-02-03', product: 'Widget Pro',    region: 'Asia Pacific',  units: 200,  revenue: 9_800.00),
  SalesRecord.new(date: '2026-02-18', product: 'Super Doohickey',region: 'North America',units:  45,  revenue: 6_750.00),
  SalesRecord.new(date: '2026-03-07', product: 'Gadget Lite',   region: 'Europe',        units: 310,  revenue: 9_300.00),
]

exporter = ReportExporter.new(CsvExportStrategy.new)
exporter.export(sales_data, title: 'Q1 2026 Sales Report', output_path: 'q1_sales.csv')

exporter.set_format(JsonExportStrategy.new)
exporter.export(sales_data, title: 'Q1 2026 Sales Report', output_path: 'q1_sales.json')

exporter.set_format(HtmlExportStrategy.new)
exporter.export(sales_data, title: 'Q1 2026 Sales Report', output_path: 'q1_sales.html')

exporter.set_format(MarkdownExportStrategy.new)
exporter.export(sales_data, title: 'Q1 2026 Sales Report', output_path: 'q1_sales.md')
```

---

## When To Use

Use the Strategy pattern when:

- **Multiple variants of an algorithm exist** and you need to switch between them at runtime (e.g., different sorting algorithms, payment providers, serialisation formats).
- **A class contains a large conditional block** (`if/switch`) that selects between variants of the same operation — extract each branch into its own strategy.
- **Different clients need different behavior** from the same class, but the surrounding logic is identical.
- **Algorithms use data that clients should not know about** — encapsulating them hides implementation details behind a clean interface.
- **Inheritance is creating an explosion of subclasses** just to vary one behavior — Strategy replaces vertical inheritance with horizontal composition.
- **You want to unit-test algorithms in isolation** — each ConcreteStrategy can be tested independently without involving the Context.
- **New behaviors must be added without modifying existing code** — each new algorithm is a new class, satisfying the Open/Closed Principle.

---

## Pros & Cons

### Pros

| Benefit | Detail |
|---|---|
| **Runtime algorithm swapping** | Change behavior without restarting or redeploying — swap a strategy object at any point. |
| **Encapsulation of implementation details** | Clients depend only on the Strategy interface, not on how any specific algorithm works. |
| **Composition over inheritance** | Replaces a deep, fragile inheritance hierarchy with a flat set of sibling strategy classes. |
| **Open/Closed Principle** | Add new algorithms by adding new classes; existing code is untouched. |
| **Eliminates conditionals** | Removes scattered `if/switch` logic from the Context, replacing it with polymorphism. |
| **Independent testability** | Each ConcreteStrategy is a standalone class — easy to unit-test in isolation with mock inputs. |
| **Single Responsibility** | The Context handles orchestration; each Strategy handles exactly one algorithm variant. |

### Cons

| Drawback | Detail |
|---|---|
| **Overkill for few, stable variants** | If you have only two algorithms that never change, an interface + two classes adds unnecessary ceremony. |
| **Client must know strategies** | The caller must understand the differences between strategies to select the right one — this can leak implementation knowledge. |
| **Increased number of classes** | Each algorithm becomes a class; in large systems this can proliferate files. |
| **Stateless vs. stateful strategies** | Sharing a strategy instance across multiple contexts can cause subtle bugs if the strategy holds mutable state. |
| **Data passing overhead** | The Context may need to pass a lot of data into the strategy's method, or expose internal state, to give the strategy what it needs. |

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Bridge** | Both separate an abstraction from its implementation. Bridge is structural: it decouples a class hierarchy. Strategy is behavioral: it decouples a single behavior (the algorithm) from the object that uses it. |
| **Command** | Command wraps a request (including its receiver and parameters) as an object — it is about *what* to do. Strategy wraps an interchangeable algorithm — it is about *how* to do it. Commands are often stored for undo/redo; strategies are swapped for polymorphic behavior. |
| **State** | State and Strategy share the same structure (a context holding a reference to one of several sibling classes). The key difference is intent: State objects are aware of each other and trigger transitions; strategies are completely independent and know nothing of one another. |
| **Template Method** | Both define a skeleton for an algorithm. Template Method uses *inheritance* — the invariant steps are in a base class and subclasses override the variable steps. Strategy uses *composition* — the entire algorithm is delegated to an injected strategy object, allowing runtime replacement. |
| **Decorator** | Decorator adds responsibilities to an object dynamically by wrapping it. Strategy replaces an algorithm entirely. You can combine them: a Strategy that is itself a Decorator, adding cross-cutting concerns (logging, caching) to another strategy. |

---

## Sources

- https://refactoring.guru/design-patterns/strategy
- https://sourcemaking.com/design_patterns/strategy
