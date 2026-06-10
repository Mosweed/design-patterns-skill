# Template Method Pattern

**Category:** Behavioral  
**Also Known As:** Template, Hollywood Principle ("Don't call us, we'll call you")

---

## Intent

Define the skeleton of an algorithm in a base class, deferring some steps to subclasses. Template Method lets subclasses redefine certain steps of an algorithm without changing the algorithm's overall structure.

---

## Problem It Solves

Suppose you are building a data-mining application that processes reports from different file formats — CSV, PDF, and DOCX. Each format requires its own parsing logic, but the high-level mining pipeline is identical:

1. Open the file
2. Parse raw data
3. Analyse the data
4. Generate a report
5. Close the file

Without a shared structure, each class duplicates the orchestration code. When you later need to add a caching step or a logging step, you must touch every class independently. Bugs creep in because the implementations inevitably drift.

The Template Method pattern lets you encode that invariant orchestration once — in a base class — and push only the format-specific parts into subclasses. Clients cannot reorder or skip the algorithm's stages; they can only fill in the blanks.

---

## Solution

Break the algorithm into individual steps. Encode each step as a method. Write a single **template method** in the abstract base class that calls these step-methods in the correct order. Mark steps that must be customised as `abstract`; give a sensible default (or a no-op) to optional **hook** steps that subclasses may — but need not — override.

Concrete subclasses implement (or override) only the steps they own. The skeleton never changes.

---

## Structure (ASCII diagram)

```
┌──────────────────────────────────────────────┐
│              AbstractClass                   │
├──────────────────────────────────────────────┤
│ + templateMethod()   ← final / sealed        │
│   ├── step1()        ← abstract              │
│   ├── step2()        ← abstract              │
│   ├── hook1()        ← optional (empty body) │
│   └── step3()        ← abstract              │
│                                              │
│ # step1()   : abstract                       │
│ # step2()   : abstract                       │
│ # hook1()   : virtual (no-op default)        │
│ # step3()   : abstract                       │
└──────────────────────────────────────────────┘
            ▲                    ▲
            │                    │
┌───────────────────┐  ┌───────────────────────┐
│  ConcreteClassA   │  │   ConcreteClassB       │
├───────────────────┤  ├───────────────────────┤
│ # step1() {...}   │  │ # step1() {...}        │
│ # step2() {...}   │  │ # step2() {...}        │
│ # step3() {...}   │  │ # hook1() {...}  ← opt │
└───────────────────┘  │ # step3() {...}        │
                       └───────────────────────┘
```

---

## Participants

| Participant | Role |
|---|---|
| **AbstractClass** | Declares abstract primitive operations and implements the template method that calls them in sequence. May also provide default (hook) implementations. |
| **ConcreteClass** | Implements the abstract primitive operations to carry out subclass-specific steps of the algorithm. Must not override `templateMethod` itself. |

---

## How It Works (step-by-step)

1. **Identify the invariant algorithm.** Find the sequence of steps that never changes across variants.
2. **Create the abstract base class.** Write the template method — usually `final` or not meant to be overridden — that calls each step in order.
3. **Declare abstract steps.** Any step whose implementation differs between variants becomes an abstract method on the base class.
4. **Add hooks.** Steps that are optional get a default (often empty) implementation; subclasses override them only when needed.
5. **Write concrete subclasses.** Each subclass fills in only the steps it owns. It inherits the orchestration for free.
6. **Client code works with the base type.** The client calls `templateMethod()` through an `AbstractClass` reference and never needs to know the concrete type.

---

## Code Examples

### Python

```python
"""
Real-world example: Database report exporter.

The pipeline (connect → query → transform → format → write → disconnect)
is always the same. The concrete classes handle specific output formats
(CSV and JSON). A hook lets subclasses add a header row when relevant.
"""

from __future__ import annotations
import csv
import io
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class SalesRecord:
    region: str
    product: str
    units_sold: int
    revenue: float


# Simulated database results
_FAKE_DB_ROWS = [
    SalesRecord("North", "Widget A", 120, 2400.00),
    SalesRecord("South", "Widget B", 85,  1700.00),
    SalesRecord("East",  "Widget A", 200, 4000.00),
    SalesRecord("West",  "Widget C", 60,  900.00),
]


class ReportExporter(ABC):
    """
    AbstractClass — defines the report-export pipeline.
    Subclasses must implement the abstract steps; the hook is optional.
    """

    # ------------------------------------------------------------------ #
    #  Template method — sealed by convention (prefix with __ or document) #
    # ------------------------------------------------------------------ #
    def export(self, output_path: str) -> None:
        """Run the full export pipeline."""
        print(f"[{self.__class__.__name__}] Starting export to '{output_path}'")
        connection = self._connect()
        try:
            raw_rows = self._fetch_data(connection)
            records   = self._transform(raw_rows)
            self._before_write(records)          # hook — optional
            content   = self._format(records)
            self._write(output_path, content)
        finally:
            self._disconnect(connection)
        print(f"[{self.__class__.__name__}] Export complete.")

    # ------------------------------------------------------------------ #
    #  Abstract primitive steps — subclasses MUST implement these          #
    # ------------------------------------------------------------------ #
    @abstractmethod
    def _connect(self) -> Any:
        """Establish a database connection and return it."""

    @abstractmethod
    def _fetch_data(self, connection: Any) -> list[dict]:
        """Execute the query and return raw rows as dicts."""

    @abstractmethod
    def _format(self, records: list[SalesRecord]) -> str | bytes:
        """Serialize records into the target format."""

    @abstractmethod
    def _write(self, path: str, content: str | bytes) -> None:
        """Persist the formatted content to disk."""

    # ------------------------------------------------------------------ #
    #  Concrete step with default implementation                           #
    # ------------------------------------------------------------------ #
    def _transform(self, raw_rows: list[dict]) -> list[SalesRecord]:
        """Convert raw dicts into typed SalesRecord objects."""
        return [SalesRecord(**row) for row in raw_rows]

    def _disconnect(self, connection: Any) -> None:
        """Close the database connection."""
        print(f"  Closing connection: {connection!r}")

    # ------------------------------------------------------------------ #
    #  Hook — empty by default, subclasses may override                   #
    # ------------------------------------------------------------------ #
    def _before_write(self, records: list[SalesRecord]) -> None:
        """Optional hook called after transformation, before formatting."""


# ------------------------------------------------------------------ #
#  ConcreteClass A — CSV exporter                                     #
# ------------------------------------------------------------------ #
class CsvReportExporter(ReportExporter):

    def _connect(self) -> str:
        conn = "sqlite://sales.db"
        print(f"  Connected to {conn}")
        return conn

    def _fetch_data(self, connection: str) -> list[dict]:
        # Simulate a SELECT query
        print(f"  Querying {connection} …")
        return [asdict(r) for r in _FAKE_DB_ROWS]

    def _format(self, records: list[SalesRecord]) -> str:
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=["region", "product", "units_sold", "revenue"],
        )
        writer.writeheader()
        for rec in records:
            writer.writerow(asdict(rec))
        return buf.getvalue()

    def _write(self, path: str, content: str) -> None:
        print(f"  Writing CSV ({len(content)} chars) → {path}")
        # with open(path, "w", newline="") as fh: fh.write(content)

    # Override the hook to log totals before writing
    def _before_write(self, records: list[SalesRecord]) -> None:
        total_units   = sum(r.units_sold for r in records)
        total_revenue = sum(r.revenue    for r in records)
        print(f"  [hook] Totals — units: {total_units}, revenue: ${total_revenue:,.2f}")


# ------------------------------------------------------------------ #
#  ConcreteClass B — JSON exporter                                    #
# ------------------------------------------------------------------ #
class JsonReportExporter(ReportExporter):

    def _connect(self) -> str:
        conn = "postgresql://analytics_db"
        print(f"  Connected to {conn}")
        return conn

    def _fetch_data(self, connection: str) -> list[dict]:
        print(f"  Querying {connection} …")
        return [asdict(r) for r in _FAKE_DB_ROWS]

    def _format(self, records: list[SalesRecord]) -> str:
        payload = {
            "report": "sales_summary",
            "records": [asdict(r) for r in records],
        }
        return json.dumps(payload, indent=2)

    def _write(self, path: str, content: str) -> None:
        print(f"  Writing JSON ({len(content)} chars) → {path}")
        # with open(path, "w") as fh: fh.write(content)


# ------------------------------------------------------------------ #
#  Client code                                                        #
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    exporters: list[ReportExporter] = [
        CsvReportExporter(),
        JsonReportExporter(),
    ]

    for exporter in exporters:
        exporter.export("/tmp/sales_report")
        print()
```

---

### Java

```java
/**
 * Real-world example: HTTP request processing pipeline.
 *
 * Every handler must: authenticate → validate → execute → respond.
 * Concrete handlers override only the steps specific to their resource.
 */

package patterns.templatemethod;

import java.util.Map;
import java.util.Optional;

// ---------------------------------------------------------------------------
// AbstractClass
// ---------------------------------------------------------------------------
public abstract class HttpRequestHandler {

    /** Template method — marked final so subclasses cannot reorder the pipeline. */
    public final String handle(Map<String, String> request) {
        System.out.println("[" + getClass().getSimpleName() + "] Handling request");

        Optional<String> authError = authenticate(request);
        if (authError.isPresent()) {
            return buildErrorResponse(401, authError.get());
        }

        Optional<String> validationError = validate(request);
        if (validationError.isPresent()) {
            return buildErrorResponse(400, validationError.get());
        }

        String result = execute(request);

        // Hook — subclasses may log, audit, or post-process
        afterExecute(request, result);

        return buildSuccessResponse(result);
    }

    // -------------------------------------------------------------------
    // Abstract primitive operations
    // -------------------------------------------------------------------
    /** Returns an error message if authentication fails, otherwise empty. */
    protected abstract Optional<String> authenticate(Map<String, String> request);

    /** Returns an error message if validation fails, otherwise empty. */
    protected abstract Optional<String> validate(Map<String, String> request);

    /** Core business logic — runs only if auth and validation pass. */
    protected abstract String execute(Map<String, String> request);

    // -------------------------------------------------------------------
    // Concrete steps with default implementation
    // -------------------------------------------------------------------
    protected String buildSuccessResponse(String body) {
        return "HTTP/1.1 200 OK\r\n\r\n" + body;
    }

    protected String buildErrorResponse(int status, String message) {
        return "HTTP/1.1 " + status + "\r\n\r\n{\"error\":\"" + message + "\"}";
    }

    // -------------------------------------------------------------------
    // Hook — no-op by default
    // -------------------------------------------------------------------
    protected void afterExecute(Map<String, String> request, String result) {
        // Subclasses may override to add auditing, metrics, etc.
    }
}

// ---------------------------------------------------------------------------
// ConcreteClass A — Handles /api/users/:id (token-authenticated)
// ---------------------------------------------------------------------------
class UserProfileHandler extends HttpRequestHandler {

    @Override
    protected Optional<String> authenticate(Map<String, String> request) {
        String token = request.getOrDefault("Authorization", "");
        if (!token.startsWith("Bearer ")) {
            return Optional.of("Missing or invalid bearer token");
        }
        return Optional.empty();
    }

    @Override
    protected Optional<String> validate(Map<String, String> request) {
        String userId = request.getOrDefault("userId", "");
        if (userId.isBlank()) {
            return Optional.of("userId path parameter is required");
        }
        try {
            Long.parseLong(userId);
        } catch (NumberFormatException e) {
            return Optional.of("userId must be a numeric value");
        }
        return Optional.empty();
    }

    @Override
    protected String execute(Map<String, String> request) {
        String userId = request.get("userId");
        // Simulate database lookup
        return "{\"id\":" + userId + ",\"name\":\"Alice\",\"email\":\"alice@example.com\"}";
    }

    @Override
    protected void afterExecute(Map<String, String> request, String result) {
        System.out.println("  [audit] User profile viewed for id=" + request.get("userId"));
    }
}

// ---------------------------------------------------------------------------
// ConcreteClass B — Handles /api/reports (API-key authenticated)
// ---------------------------------------------------------------------------
class ReportHandler extends HttpRequestHandler {

    private static final String VALID_API_KEY = "secret-key-42";

    @Override
    protected Optional<String> authenticate(Map<String, String> request) {
        String key = request.getOrDefault("X-Api-Key", "");
        if (!VALID_API_KEY.equals(key)) {
            return Optional.of("Invalid API key");
        }
        return Optional.empty();
    }

    @Override
    protected Optional<String> validate(Map<String, String> request) {
        String format = request.getOrDefault("format", "");
        if (!format.equals("csv") && !format.equals("json")) {
            return Optional.of("format must be 'csv' or 'json'");
        }
        return Optional.empty();
    }

    @Override
    protected String execute(Map<String, String> request) {
        String format = request.get("format");
        return format.equals("csv")
            ? "region,units\nNorth,120\nSouth,85"
            : "[{\"region\":\"North\",\"units\":120}]";
    }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------
class Main {
    public static void main(String[] args) {
        HttpRequestHandler userHandler   = new UserProfileHandler();
        HttpRequestHandler reportHandler = new ReportHandler();

        // Successful user profile request
        System.out.println(userHandler.handle(Map.of(
            "Authorization", "Bearer eyJ0...",
            "userId",        "42"
        )));

        System.out.println();

        // Failed report request (bad API key)
        System.out.println(reportHandler.handle(Map.of(
            "X-Api-Key", "wrong-key",
            "format",    "csv"
        )));
    }
}
```

---

### C++

```cpp
/**
 * Real-world example: build-system compiler pipeline.
 *
 * Steps: preprocess → compile → optimise → link → package.
 * GCC and Clang frontends share the structure but differ in flags/tools.
 */

#include <iostream>
#include <string>
#include <vector>

// ---------------------------------------------------------------------------
// AbstractClass
// ---------------------------------------------------------------------------
class CompilerPipeline {
public:
    // Template method — non-virtual so subclasses cannot reorder it
    void build(const std::vector<std::string>& sourceFiles,
               const std::string& outputName) {
        std::cout << "[" << name() << "] Starting build\n";
        preprocess(sourceFiles);
        compile(sourceFiles);
        if (shouldOptimise()) {         // hook — true by default
            optimise();
        }
        link(outputName);
        package(outputName);
        std::cout << "[" << name() << "] Build finished: " << outputName << "\n";
    }

    virtual ~CompilerPipeline() = default;

protected:
    // Name helper for logging
    virtual std::string name() const = 0;

    // Abstract primitive operations
    virtual void preprocess(const std::vector<std::string>& sources) = 0;
    virtual void compile(const std::vector<std::string>& sources) = 0;
    virtual void link(const std::string& output) = 0;
    virtual void package(const std::string& output) = 0;

    // Concrete step with default implementation
    virtual void optimise() {
        std::cout << "  [optimise] Running default optimiser (-O2)\n";
    }

    // Hook — subclasses may disable optimisation
    virtual bool shouldOptimise() const { return true; }
};

// ---------------------------------------------------------------------------
// ConcreteClass A — GCC pipeline
// ---------------------------------------------------------------------------
class GccPipeline : public CompilerPipeline {
protected:
    std::string name() const override { return "GCC"; }

    void preprocess(const std::vector<std::string>& sources) override {
        for (const auto& s : sources) {
            std::cout << "  [gcc-cpp] Preprocessing " << s << "\n";
        }
    }

    void compile(const std::vector<std::string>& sources) override {
        for (const auto& s : sources) {
            std::cout << "  [gcc] Compiling " << s << " → " << s << ".o\n";
        }
    }

    void optimise() override {
        std::cout << "  [gcc] Applying link-time optimisation (LTO)\n";
    }

    void link(const std::string& output) override {
        std::cout << "  [ld] Linking → " << output << "\n";
    }

    void package(const std::string& output) override {
        std::cout << "  [ar] Packaging " << output << " into libout.a\n";
    }
};

// ---------------------------------------------------------------------------
// ConcreteClass B — Clang pipeline (debug build, no optimisation)
// ---------------------------------------------------------------------------
class ClangDebugPipeline : public CompilerPipeline {
protected:
    std::string name() const override { return "Clang/Debug"; }

    void preprocess(const std::vector<std::string>& sources) override {
        for (const auto& s : sources) {
            std::cout << "  [clang-cpp] Preprocessing " << s << " (-DDEBUG)\n";
        }
    }

    void compile(const std::vector<std::string>& sources) override {
        for (const auto& s : sources) {
            std::cout << "  [clang] Compiling " << s
                      << " -g -O0 → " << s << ".o\n";
        }
    }

    // Hook override — skip optimisation in debug builds
    bool shouldOptimise() const override { return false; }

    void link(const std::string& output) override {
        std::cout << "  [lld] Linking (debug symbols) → " << output << "\n";
    }

    void package(const std::string& output) override {
        // Debug builds skip packaging
        std::cout << "  [skip] No packaging for debug target " << output << "\n";
    }
};

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------
int main() {
    std::vector<std::string> sources = {"main.cpp", "utils.cpp", "net.cpp"};

    GccPipeline gcc;
    gcc.build(sources, "myapp");

    std::cout << "\n";

    ClangDebugPipeline clangDebug;
    clangDebug.build(sources, "myapp_d");

    return 0;
}
```

---

### C#

```csharp
/**
 * Real-world example: e-commerce order processing pipeline.
 *
 * Every order follows: validate → reserve inventory → charge payment
 *                       → fulfil → notify customer.
 * Standard and subscription orders share the skeleton but differ
 * in how inventory is reserved and how notifications are sent.
 */

using System;
using System.Collections.Generic;

// ---------------------------------------------------------------------------
// Domain model
// ---------------------------------------------------------------------------
record OrderItem(string Sku, int Quantity, decimal UnitPrice);

class Order
{
    public Guid   Id        { get; } = Guid.NewGuid();
    public string Customer  { get; init; } = "";
    public string Email     { get; init; } = "";
    public List<OrderItem> Items { get; init; } = new();
    public decimal Total => Items.Sum(i => i.Quantity * i.UnitPrice);
}

// ---------------------------------------------------------------------------
// AbstractClass
// ---------------------------------------------------------------------------
abstract class OrderProcessor
{
    /// <summary>Template method — sealed to prevent reordering.</summary>
    public sealed void Process(Order order)
    {
        Console.WriteLine($"[{GetType().Name}] Processing order {order.Id}");

        if (!Validate(order))
        {
            Console.WriteLine("  Order validation failed. Aborting.");
            return;
        }

        ReserveInventory(order);
        ChargePayment(order);
        Fulfil(order);
        NotifyCustomer(order);      // hook — has a sensible default

        Console.WriteLine($"[{GetType().Name}] Order {order.Id} completed.\n");
    }

    // Abstract steps
    protected abstract bool Validate(Order order);
    protected abstract void ReserveInventory(Order order);
    protected abstract void ChargePayment(Order order);
    protected abstract void Fulfil(Order order);

    // Concrete step with default implementation (hook)
    protected virtual void NotifyCustomer(Order order)
    {
        Console.WriteLine($"  [email] Sending generic confirmation to {order.Email}");
    }
}

// ---------------------------------------------------------------------------
// ConcreteClass A — Standard one-off order
// ---------------------------------------------------------------------------
class StandardOrderProcessor : OrderProcessor
{
    protected override bool Validate(Order order)
    {
        if (order.Items.Count == 0)
        {
            Console.WriteLine("  Validation: no items in order.");
            return false;
        }
        Console.WriteLine($"  Validation: OK ({order.Items.Count} items, total ${order.Total:F2})");
        return true;
    }

    protected override void ReserveInventory(Order order)
    {
        foreach (var item in order.Items)
            Console.WriteLine($"  [warehouse] Reserved {item.Quantity}× {item.Sku}");
    }

    protected override void ChargePayment(Order order)
    {
        Console.WriteLine($"  [payment] Charged ${order.Total:F2} to card on file for {order.Customer}");
    }

    protected override void Fulfil(Order order)
    {
        Console.WriteLine($"  [shipping] Created shipping label for {order.Customer}");
    }

    // Override hook to include itemised receipt
    protected override void NotifyCustomer(Order order)
    {
        Console.WriteLine($"  [email] Sending itemised receipt to {order.Email}");
        foreach (var item in order.Items)
            Console.WriteLine($"    - {item.Sku} ×{item.Quantity} @ ${item.UnitPrice:F2}");
    }
}

// ---------------------------------------------------------------------------
// ConcreteClass B — Subscription renewal order
// ---------------------------------------------------------------------------
class SubscriptionOrderProcessor : OrderProcessor
{
    protected override bool Validate(Order order)
    {
        // Subscriptions are pre-authorised; lighter validation
        Console.WriteLine("  Validation: subscription pre-authorised — OK");
        return true;
    }

    protected override void ReserveInventory(Order order)
    {
        // Digital subscription — no physical inventory needed
        Console.WriteLine("  [inventory] Digital product — no reservation required");
    }

    protected override void ChargePayment(Order order)
    {
        Console.WriteLine($"  [payment] Auto-billed ${order.Total:F2} via saved payment method");
    }

    protected override void Fulfil(Order order)
    {
        Console.WriteLine($"  [licence] Extended subscription licence for {order.Customer} by 30 days");
    }

    // Uses the default NotifyCustomer (generic email) — no override needed
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------
class Program
{
    static void Main()
    {
        var standardOrder = new Order
        {
            Customer = "Bob Smith",
            Email    = "bob@example.com",
            Items    =
            {
                new OrderItem("WIDGET-A", 2, 29.99m),
                new OrderItem("GADGET-B", 1, 49.99m),
            }
        };

        var subscriptionOrder = new Order
        {
            Customer = "Carol Jones",
            Email    = "carol@example.com",
            Items    = { new OrderItem("PRO-PLAN-MONTHLY", 1, 19.99m) }
        };

        OrderProcessor processor = new StandardOrderProcessor();
        processor.Process(standardOrder);

        processor = new SubscriptionOrderProcessor();
        processor.Process(subscriptionOrder);
    }
}
```

---

### TypeScript

```typescript
/**
 * Real-world example: OAuth2 social-login flow.
 *
 * The OAuth2 dance is always: buildAuthUrl → exchangeCode → fetchUserProfile
 *                              → normaliseUser → upsertUser.
 * GitHub and Google differ in endpoints and response shapes.
 */

// ---------------------------------------------------------------------------
// Domain types
// ---------------------------------------------------------------------------
interface OAuthTokens {
  accessToken: string;
  refreshToken?: string;
  expiresIn: number;
}

interface NormalisedUser {
  provider: string;
  providerId: string;
  email: string;
  name: string;
  avatarUrl?: string;
}

// Simulated database
const userStore: Map<string, NormalisedUser> = new Map();

// ---------------------------------------------------------------------------
// AbstractClass
// ---------------------------------------------------------------------------
abstract class SocialAuthProvider {
  /** Template method — arrow function prevents accidental override. */
  async authenticate(code: string, state: string): Promise<NormalisedUser> {
    console.log(`[${this.providerName}] Starting OAuth flow`);

    this.verifyState(state); // hook — validates CSRF state token

    const tokens = await this.exchangeCode(code);
    console.log(`  Tokens received (expires in ${tokens.expiresIn}s)`);

    const raw = await this.fetchUserProfile(tokens.accessToken);
    const user = this.normaliseUser(raw);

    console.log(`  Normalised user: ${user.email} (${user.providerId})`);

    const saved = await this.upsertUser(user);
    await this.afterLogin(saved); // hook — send welcome email, log, etc.

    return saved;
  }

  // -----------------------------------------------------------------------
  // Abstract primitive operations
  // -----------------------------------------------------------------------
  protected abstract get providerName(): string;
  protected abstract exchangeCode(code: string): Promise<OAuthTokens>;
  protected abstract fetchUserProfile(accessToken: string): Promise<unknown>;
  protected abstract normaliseUser(raw: unknown): NormalisedUser;

  // -----------------------------------------------------------------------
  // Concrete step with default implementation
  // -----------------------------------------------------------------------
  protected async upsertUser(user: NormalisedUser): Promise<NormalisedUser> {
    const key = `${user.provider}:${user.providerId}`;
    userStore.set(key, user);
    console.log(`  User upserted to store with key "${key}"`);
    return user;
  }

  // -----------------------------------------------------------------------
  // Hooks — empty by default
  // -----------------------------------------------------------------------
  protected verifyState(state: string): void {
    // Default: no-op (subclasses may implement CSRF checks)
  }

  protected async afterLogin(user: NormalisedUser): Promise<void> {
    // Default: no-op
  }
}

// ---------------------------------------------------------------------------
// ConcreteClass A — GitHub OAuth2
// ---------------------------------------------------------------------------
interface GithubRawProfile {
  id: number;
  login: string;
  email: string;
  avatar_url: string;
}

class GithubAuthProvider extends SocialAuthProvider {
  protected get providerName() { return "GitHub"; }

  protected async exchangeCode(code: string): Promise<OAuthTokens> {
    console.log(`  POST https://github.com/login/oauth/access_token?code=${code}`);
    // Simulate API call
    return { accessToken: "gh_fake_token_abc", expiresIn: 28800 };
  }

  protected async fetchUserProfile(accessToken: string): Promise<GithubRawProfile> {
    console.log(`  GET https://api.github.com/user  (token: ${accessToken.slice(0, 8)}…)`);
    return {
      id: 1234567,
      login: "octocat",
      email: "octocat@github.com",
      avatar_url: "https://avatars.githubusercontent.com/u/1234567",
    };
  }

  protected normaliseUser(raw: unknown): NormalisedUser {
    const r = raw as GithubRawProfile;
    return {
      provider:   "github",
      providerId: String(r.id),
      email:      r.email,
      name:       r.login,
      avatarUrl:  r.avatar_url,
    };
  }

  // Override hook to verify CSRF state
  protected verifyState(state: string): void {
    if (!state || state.length < 8) {
      throw new Error("Invalid OAuth state — possible CSRF attack");
    }
    console.log("  State token verified");
  }
}

// ---------------------------------------------------------------------------
// ConcreteClass B — Google OAuth2
// ---------------------------------------------------------------------------
interface GoogleRawProfile {
  sub: string;
  email: string;
  name: string;
  picture: string;
}

class GoogleAuthProvider extends SocialAuthProvider {
  protected get providerName() { return "Google"; }

  protected async exchangeCode(code: string): Promise<OAuthTokens> {
    console.log(`  POST https://oauth2.googleapis.com/token?code=${code}`);
    return { accessToken: "ya29_fake_token_xyz", expiresIn: 3600, refreshToken: "1//refresh" };
  }

  protected async fetchUserProfile(accessToken: string): Promise<GoogleRawProfile> {
    console.log(`  GET https://www.googleapis.com/oauth2/v3/userinfo`);
    return {
      sub:     "109876543210",
      email:   "user@gmail.com",
      name:    "Jane Doe",
      picture: "https://lh3.googleusercontent.com/photo.jpg",
    };
  }

  protected normaliseUser(raw: unknown): NormalisedUser {
    const r = raw as GoogleRawProfile;
    return {
      provider:   "google",
      providerId: r.sub,
      email:      r.email,
      name:       r.name,
      avatarUrl:  r.picture,
    };
  }

  // Override afterLogin hook to send a welcome email on first sign-in
  protected async afterLogin(user: NormalisedUser): Promise<void> {
    console.log(`  [email] Sending welcome email to ${user.email}`);
  }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------
(async () => {
  const providers: SocialAuthProvider[] = [
    new GithubAuthProvider(),
    new GoogleAuthProvider(),
  ];

  for (const provider of providers) {
    const user = await provider.authenticate("auth_code_xyz", "csrf_state_token");
    console.log(`  Logged in as: ${user.name} <${user.email}>\n`);
  }
})();
```

---

### Go

```go
// Real-world example: data-pipeline ETL processor.
//
// Every ETL job follows: extract → validate → transform → load → summarise.
// Go lacks inheritance, so the Template Method pattern is implemented via
// embedding of a struct that holds function fields — a common Go idiom.
//
// An alternative idiomatic approach uses an interface + a runner function.
// Both are shown below.

package main

import (
	"fmt"
	"strings"
	"time"
)

// ---------------------------------------------------------------------------
// Domain types
// ---------------------------------------------------------------------------

// Record represents a generic key-value data row.
type Record map[string]any

// ETLResult summarises a completed job.
type ETLResult struct {
	Extracted  int
	Validated  int
	Loaded     int
	Duration   time.Duration
}

// ---------------------------------------------------------------------------
// "Abstract" interface — defines the primitive operations
// ---------------------------------------------------------------------------

// ETLSteps declares every customisable step of the pipeline.
// Concrete implementations provide only what differs.
type ETLSteps interface {
	Name() string
	Extract() ([]Record, error)
	ValidateRecord(r Record) bool
	Transform(r Record) Record
	Load(records []Record) error
	// OnSummary is a hook — called after load; implementors may ignore it.
	OnSummary(result ETLResult)
}

// ---------------------------------------------------------------------------
// Template function (replaces the template method in a base class)
// ---------------------------------------------------------------------------

// RunPipeline is the template method. It owns the algorithm's skeleton.
func RunPipeline(steps ETLSteps) error {
	start := time.Now()
	fmt.Printf("[%s] Pipeline starting\n", steps.Name())

	// Step 1: Extract
	raw, err := steps.Extract()
	if err != nil {
		return fmt.Errorf("extract: %w", err)
	}
	fmt.Printf("  Extracted %d records\n", len(raw))

	// Step 2: Validate
	var valid []Record
	for _, r := range raw {
		if steps.ValidateRecord(r) {
			valid = append(valid, r)
		}
	}
	fmt.Printf("  Valid records: %d / %d\n", len(valid), len(raw))

	// Step 3: Transform
	transformed := make([]Record, len(valid))
	for i, r := range valid {
		transformed[i] = steps.Transform(r)
	}

	// Step 4: Load
	if err := steps.Load(transformed); err != nil {
		return fmt.Errorf("load: %w", err)
	}

	// Step 5: Summary (hook)
	result := ETLResult{
		Extracted: len(raw),
		Validated: len(valid),
		Loaded:    len(transformed),
		Duration:  time.Since(start),
	}
	steps.OnSummary(result)

	fmt.Printf("[%s] Pipeline complete in %v\n\n", steps.Name(), result.Duration)
	return nil
}

// ---------------------------------------------------------------------------
// ConcreteClass A — CSV-to-PostgreSQL ETL
// ---------------------------------------------------------------------------

type CsvToPostgres struct{}

func (c *CsvToPostgres) Name() string { return "CSV→PostgreSQL" }

func (c *CsvToPostgres) Extract() ([]Record, error) {
	fmt.Println("  [extract] Reading customers.csv …")
	// Simulate parsed CSV rows
	return []Record{
		{"id": "1", "name": "Alice",   "email": "alice@example.com",  "age": "30"},
		{"id": "2", "name": "",        "email": "bad-email",           "age": "abc"},
		{"id": "3", "name": "Charlie", "email": "charlie@example.com", "age": "25"},
	}, nil
}

func (c *CsvToPostgres) ValidateRecord(r Record) bool {
	name, _ := r["name"].(string)
	email, _ := r["email"].(string)
	return name != "" && strings.Contains(email, "@")
}

func (c *CsvToPostgres) Transform(r Record) Record {
	// Normalise email to lowercase
	if email, ok := r["email"].(string); ok {
		r["email"] = strings.ToLower(email)
	}
	return r
}

func (c *CsvToPostgres) Load(records []Record) error {
	for _, r := range records {
		fmt.Printf("  [load] INSERT INTO customers VALUES (%v)\n", r)
	}
	return nil
}

// OnSummary hook — log to monitoring system
func (c *CsvToPostgres) OnSummary(result ETLResult) {
	rejected := result.Extracted - result.Validated
	fmt.Printf("  [monitor] ETL done — loaded=%d, rejected=%d\n",
		result.Loaded, rejected)
}

// ---------------------------------------------------------------------------
// ConcreteClass B — API-to-S3 ETL (hook not used)
// ---------------------------------------------------------------------------

type ApiToS3 struct{}

func (a *ApiToS3) Name() string { return "API→S3" }

func (a *ApiToS3) Extract() ([]Record, error) {
	fmt.Println("  [extract] GET https://api.example.com/events …")
	return []Record{
		{"event_id": "e1", "type": "click",    "user": "u99"},
		{"event_id": "e2", "type": "purchase", "user": "u42"},
	}, nil
}

func (a *ApiToS3) ValidateRecord(r Record) bool {
	_, hasID   := r["event_id"]
	_, hasType := r["type"]
	return hasID && hasType
}

func (a *ApiToS3) Transform(r Record) Record {
	// Add ingestion timestamp
	r["ingested_at"] = time.Now().UTC().Format(time.RFC3339)
	return r
}

func (a *ApiToS3) Load(records []Record) error {
	fmt.Printf("  [load] Writing %d records to s3://data-lake/events/\n", len(records))
	return nil
}

// OnSummary — no-op (no monitoring hook needed)
func (a *ApiToS3) OnSummary(_ ETLResult) {}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

func main() {
	jobs := []ETLSteps{
		&CsvToPostgres{},
		&ApiToS3{},
	}

	for _, job := range jobs {
		if err := RunPipeline(job); err != nil {
			fmt.Printf("Pipeline error: %v\n", err)
		}
	}
}
```

---

### PHP

```php
<?php

/**
 * Real-world example: CMS page rendering pipeline.
 *
 * Every page render: loadContent → resolveLayout → renderBody
 *                    → injectAssets → finalise.
 * BlogPage and LandingPage share the skeleton but differ in
 * how they load content and what assets they inject.
 */

declare(strict_types=1);

// ---------------------------------------------------------------------------
// AbstractClass
// ---------------------------------------------------------------------------
abstract class PageRenderer
{
    private string $renderedHtml = '';

    /**
     * Template method — final prevents reordering.
     */
    final public function render(string $slug): string
    {
        echo "[" . static::class . "] Rendering '$slug'\n";

        $content = $this->loadContent($slug);
        $layout  = $this->resolveLayout();
        $body    = $this->renderBody($content);

        if ($this->shouldCacheOutput()) {  // hook — true by default
            $this->cacheOutput($slug, $body);
        }

        $assets  = $this->injectAssets();
        $this->renderedHtml = $this->finalise($layout, $body, $assets);

        return $this->renderedHtml;
    }

    // -----------------------------------------------------------------------
    // Abstract primitive operations
    // -----------------------------------------------------------------------
    abstract protected function loadContent(string $slug): array;
    abstract protected function renderBody(array $content): string;
    abstract protected function injectAssets(): string;

    // -----------------------------------------------------------------------
    // Concrete steps with default implementation
    // -----------------------------------------------------------------------
    protected function resolveLayout(): string
    {
        return 'default';
    }

    protected function finalise(string $layout, string $body, string $assets): string
    {
        return <<<HTML
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8">{$assets}</head>
        <body data-layout="{$layout}">{$body}</body>
        </html>
        HTML;
    }

    protected function cacheOutput(string $slug, string $body): void
    {
        echo "  [cache] Stored rendered body for '$slug'\n";
    }

    // -----------------------------------------------------------------------
    // Hook — subclasses may disable caching
    // -----------------------------------------------------------------------
    protected function shouldCacheOutput(): bool
    {
        return true;
    }
}

// ---------------------------------------------------------------------------
// ConcreteClass A — Blog post page
// ---------------------------------------------------------------------------
class BlogPageRenderer extends PageRenderer
{
    protected function loadContent(string $slug): array
    {
        // Simulate CMS database lookup
        echo "  [db] SELECT * FROM posts WHERE slug = '$slug'\n";
        return [
            'title'      => 'Understanding Template Method',
            'body'       => '<p>The pattern defines a skeleton…</p>',
            'author'     => 'Jane Doe',
            'published'  => '2024-03-15',
            'tags'       => ['design-patterns', 'oop'],
        ];
    }

    protected function resolveLayout(): string
    {
        return 'blog-post';
    }

    protected function renderBody(array $content): string
    {
        $tags = implode(', ', $content['tags']);
        return <<<HTML
        <article>
          <h1>{$content['title']}</h1>
          <p class="meta">By {$content['author']} on {$content['published']}</p>
          {$content['body']}
          <p class="tags">Tags: {$tags}</p>
        </article>
        HTML;
    }

    protected function injectAssets(): string
    {
        return '<link rel="stylesheet" href="/css/blog.css">'
             . '<script src="/js/highlight.js"></script>';
    }
}

// ---------------------------------------------------------------------------
// ConcreteClass B — Marketing landing page (no caching, different layout)
// ---------------------------------------------------------------------------
class LandingPageRenderer extends PageRenderer
{
    protected function loadContent(string $slug): array
    {
        echo "  [api] GET https://cms.example.com/landing/$slug\n";
        return [
            'headline'   => 'Ship faster with WidgetPro',
            'subheadline'=> 'Trusted by 10,000+ teams',
            'cta_label'  => 'Start free trial',
            'cta_url'    => '/signup',
        ];
    }

    protected function resolveLayout(): string
    {
        return 'full-width';
    }

    protected function renderBody(array $content): string
    {
        return <<<HTML
        <section class="hero">
          <h1>{$content['headline']}</h1>
          <p>{$content['subheadline']}</p>
          <a class="btn-primary" href="{$content['cta_url']}">{$content['cta_label']}</a>
        </section>
        HTML;
    }

    protected function injectAssets(): string
    {
        return '<link rel="stylesheet" href="/css/landing.css">'
             . '<script src="/js/analytics.js" async></script>';
    }

    // Override hook — landing pages must never be cached (A/B testing)
    protected function shouldCacheOutput(): bool
    {
        echo "  [hook] Caching disabled for landing page\n";
        return false;
    }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------
$pages = [
    new BlogPageRenderer(),
    new LandingPageRenderer(),
];

foreach ($pages as $renderer) {
    $html = $renderer->render('example-slug');
    $preview = substr(strip_tags($html), 0, 80);
    echo "  Preview: " . trim($preview) . "…\n\n";
}
```

---

### Ruby

```ruby
# Real-world example: automated test reporter.
#
# Every test run: collect_results → filter_failures → compute_stats
#                 → format_report → deliver.
# JUnit XML and Markdown reporters share the pipeline structure but
# produce different output and deliver it differently.

# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------
TestCase = Struct.new(:name, :suite, :duration_ms, :status, :message, keyword_init: true)

SAMPLE_RESULTS = [
  TestCase.new(name: "user can log in",       suite: "AuthSpec",    duration_ms: 120, status: :passed),
  TestCase.new(name: "password is hashed",    suite: "AuthSpec",    duration_ms:  45, status: :passed),
  TestCase.new(name: "invalid token raises",  suite: "AuthSpec",    duration_ms:  15, status: :failed, message: "Expected TokenError"),
  TestCase.new(name: "cart totals correctly", suite: "CartSpec",    duration_ms: 200, status: :passed),
  TestCase.new(name: "discount applies",      suite: "CartSpec",    duration_ms:  88, status: :failed, message: "Expected 10.0, got 12.0"),
  TestCase.new(name: "stock decrements",      suite: "CartSpec",    duration_ms:  60, status: :skipped),
].freeze

# ---------------------------------------------------------------------------
# AbstractClass
# ---------------------------------------------------------------------------
class TestReporter
  # Template method — frozen to prevent override (Ruby idiom: raise in subclass)
  def generate_report(run_id)
    puts "[#{self.class.name}] Generating report for run #{run_id}"

    all_cases  = collect_results(run_id)
    failures   = filter_failures(all_cases)
    stats      = compute_stats(all_cases)
    body       = format_report(all_cases, failures, stats)

    before_deliver(run_id, body)        # hook
    deliver(run_id, body)
    after_deliver(run_id)               # hook

    puts "[#{self.class.name}] Done.\n\n"
  end

  private

  # --------------------------------------------------------------------------
  # Abstract primitive operations — subclasses MUST implement
  # --------------------------------------------------------------------------
  def format_report(all_cases, failures, stats)
    raise NotImplementedError, "#{self.class}#format_report not implemented"
  end

  def deliver(run_id, body)
    raise NotImplementedError, "#{self.class}#deliver not implemented"
  end

  # --------------------------------------------------------------------------
  # Concrete steps with default implementation
  # --------------------------------------------------------------------------
  def collect_results(_run_id)
    # In a real system this would query the test database
    puts "  Collecting test results…"
    SAMPLE_RESULTS
  end

  def filter_failures(all_cases)
    all_cases.select { |tc| tc.status == :failed }
  end

  def compute_stats(all_cases)
    {
      total:    all_cases.size,
      passed:   all_cases.count { |tc| tc.status == :passed  },
      failed:   all_cases.count { |tc| tc.status == :failed  },
      skipped:  all_cases.count { |tc| tc.status == :skipped },
      duration: all_cases.sum(&:duration_ms)
    }
  end

  # --------------------------------------------------------------------------
  # Hooks — no-op by default
  # --------------------------------------------------------------------------
  def before_deliver(run_id, body); end
  def after_deliver(run_id);        end
end

# ---------------------------------------------------------------------------
# ConcreteClass A — JUnit XML reporter (for CI systems)
# ---------------------------------------------------------------------------
class JUnitReporter < TestReporter
  private

  def format_report(all_cases, _failures, stats)
    suites = all_cases.group_by(&:suite)

    xml = +%Q[<?xml version="1.0" encoding="UTF-8"?>\n<testsuites>\n]
    suites.each do |suite, cases|
      xml << %Q[  <testsuite name="#{suite}" tests="#{cases.size}">\n]
      cases.each do |tc|
        xml << %Q[    <testcase name="#{tc.name}" time="#{tc.duration_ms / 1000.0}"]
        if tc.status == :failed
          xml << %Q[>\n      <failure message="#{tc.message}"/>\n    </testcase>\n]
        elsif tc.status == :skipped
          xml << %Q[>\n      <skipped/>\n    </testcase>\n]
        else
          xml << %Q[/>\n]
        end
      end
      xml << "  </testsuite>\n"
    end
    xml << "</testsuites>"
    xml
  end

  def deliver(run_id, body)
    path = "/tmp/junit-#{run_id}.xml"
    puts "  Writing JUnit XML to #{path} (#{body.length} chars)"
    # File.write(path, body)
  end

  # Override before_deliver hook to validate XML length
  def before_deliver(_run_id, body)
    puts "  [hook] XML size check: #{body.length} bytes — OK"
  end
end

# ---------------------------------------------------------------------------
# ConcreteClass B — Markdown reporter (for Slack / GitHub PR comments)
# ---------------------------------------------------------------------------
class MarkdownReporter < TestReporter
  private

  def format_report(all_cases, failures, stats)
    status_icon = stats[:failed] > 0 ? "FAIL" : "PASS"
    lines = [
      "## Test Report — #{status_icon}",
      "",
      "| Metric   | Value |",
      "|----------|-------|",
      "| Total    | #{stats[:total]}    |",
      "| Passed   | #{stats[:passed]}   |",
      "| Failed   | #{stats[:failed]}   |",
      "| Skipped  | #{stats[:skipped]}  |",
      "| Duration | #{stats[:duration]}ms |",
      "",
    ]

    unless failures.empty?
      lines << "### Failures"
      failures.each do |tc|
        lines << "- **#{tc.suite} / #{tc.name}**: #{tc.message}"
      end
    end

    lines.join("\n")
  end

  def deliver(run_id, body)
    puts "  Posting Markdown report to Slack channel #ci-reports"
    puts "  Preview:\n#{body.lines.first(5).join}"
    # SlackClient.post(channel: "#ci-reports", text: body)
  end

  # Override after_deliver hook to send DM on failure
  def after_deliver(_run_id)
    puts "  [hook] DM sent to on-call engineer"
  end
end

# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
reporters = [JUnitReporter.new, MarkdownReporter.new]
run_id    = "run-#{Time.now.to_i}"

reporters.each { |r| r.generate_report(run_id) }
```

---

## When To Use

- You have multiple classes that contain **almost identical algorithms with minor differences** in certain steps. Extract the shared skeleton into a base class and leave the varying steps to subclasses.
- You want to let clients **extend only particular steps** of an algorithm, not the overall structure. The template method locks in the order while abstract/hook methods open extension points.
- You need to **control extension points explicitly**: rather than allowing arbitrary overriding, the base class exposes only the steps it deems safe to customise.
- You are implementing a **framework or library** where you own the algorithm skeleton but third-party code must supply certain specialisations (e.g., a test runner calling user-defined `setUp` and `tearDown`).
- You want to apply the **Hollywood Principle** ("Don't call us, we'll call you"): the framework calls the subclass, not the other way around.

---

## Pros & Cons

### Pros

- **Eliminates duplication.** The invariant algorithm skeleton lives in exactly one place. Bug fixes and improvements propagate automatically to all concrete classes.
- **Controlled extension points.** Clients can override only the steps the designer intended — not the algorithm's overall flow.
- **Open/Closed Principle.** New variants are added by creating new concrete subclasses, without modifying the base class.
- **Hollywood Principle.** Inversion of control: the base class calls the subclass, reducing coupling between the algorithm orchestrator and its steps.

### Cons

- **Limited flexibility.** Clients are constrained by the skeleton. If a variant needs a radically different flow, the pattern can feel like a straitjacket — Strategy may be a better fit.
- **Liskov Substitution risk.** A subclass that suppresses a step (e.g., overrides a hook to do nothing when it should do something meaningful) can violate LSP and break callers that rely on that step's side effects.
- **Maintenance grows with step count.** Template methods with many steps become hard to read and maintain; understanding the full algorithm requires reading both the base and the concrete class simultaneously.
- **Deep inheritance hierarchies.** Overuse leads to multi-level inheritance chains that are difficult to navigate and test in isolation.

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Factory Method** | Factory Method is a specialisation of Template Method. The template method defines a creation algorithm; the factory method is one of its abstract steps. |
| **Strategy** | Both patterns let you vary part of an algorithm. Template Method uses **inheritance** and changes only specific steps of a fixed skeleton. Strategy uses **composition** and lets you swap the entire algorithm at runtime. Prefer Strategy when you need runtime flexibility; prefer Template Method when the skeleton must be enforced and extension points are known at design time. |

---

## Sources

- https://refactoring.guru/design-patterns/template-method
- https://sourcemaking.com/design_patterns/template_method
