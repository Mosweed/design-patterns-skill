# Chain of Responsibility Pattern

**Category:** Behavioral  
**Also Known As:** CoR, Chain of Command

---

## Intent

Let you pass requests along a chain of handlers. Upon receiving a request, each handler decides either to process the request or to pass it to the next handler in the chain. The pattern decouples the sender of a request from its receivers by giving multiple objects a chance to handle the request.

---

## Problem It Solves

Consider a system where requests must pass through several validation or processing stages before reaching their final destination. For example, an HTTP request pipeline that must perform authentication, authorization, rate limiting, logging, and input validation — all in a specific order — before the actual business logic executes.

Naively, you might nest these checks inside one another or build one enormous class that handles every case. Both approaches produce tightly coupled, hard-to-maintain code:

- **Adding a new check** requires modifying existing code.
- **Reordering checks** means restructuring conditional logic throughout the codebase.
- **Disabling a check at runtime** is difficult or impossible.
- **Reusing individual checks** in different pipelines requires duplication.

The problem intensifies when the exact types of requests, or the sequence in which they must be processed, are not known until runtime.

---

## Solution

Transform each processing step into a stand-alone object called a **handler**. Each handler stores a reference to the next handler in the chain. When a request arrives, each handler:

1. Determines whether it can process the request.
2. If yes — processes it (and optionally passes it on).
3. If no — passes it unchanged to the next handler.

The chain can be assembled at runtime, giving you flexibility to reorder, add, or remove handlers without touching existing handler code. The client that sends the request only knows about the first link in the chain; the rest is transparent.

---

## Structure

```
  Client
    │
    ▼
┌──────────────────────────────────────────────────────┐
│  <<interface>>                                       │
│  Handler                                             │
│  ─────────────────────────────────────────────────  │
│  + set_next(handler: Handler): Handler               │
│  + handle(request): result                           │
└──────────────────────────────────────────────────────┘
           ▲
           │  implements
           │
┌──────────────────────────────────────────────────────┐
│  BaseHandler                                         │
│  ─────────────────────────────────────────────────  │
│  - next_handler: Handler                             │
│  ─────────────────────────────────────────────────  │
│  + set_next(handler: Handler): Handler               │
│  + handle(request): result  ──────────────────────► delegates to next_handler.handle(request)
└──────────────────────────────────────────────────────┘
           ▲
           │  extends
    ┌──────┴──────┐
    │             │
┌───────────┐  ┌───────────┐
│Concrete   │  │Concrete   │     ... more handlers
│Handler 1  │  │Handler 2  │
│           │  │           │
│+handle()  │  │+handle()  │
└───────────┘  └───────────┘

Request flow:
  Client ──► ConcreteHandler1 ──► ConcreteHandler2 ──► ConcreteHandler3 ──► (end / unhandled)
```

---

## Participants

| Participant | Role |
|---|---|
| **Handler** | Declares the interface for handling requests and (optionally) for setting the next handler. |
| **BaseHandler** | Optional abstract class that holds boilerplate: stores the next handler reference and forwards unhandled requests automatically. |
| **ConcreteHandler** | Contains the actual processing logic. Decides to handle or pass the request. May store state local to that check. |
| **Client** | Composes the chain (may be done in application configuration or a factory), then sends requests to the first handler. |

---

## How It Works

1. **Define the Handler interface** with at least two methods: `set_next(handler)` and `handle(request)`.
2. **Implement BaseHandler** (optional but common) to hold the `next` reference and provide a default `handle()` that forwards to the next link. Concrete handlers override only the behavior they need.
3. **Write ConcreteHandlers**, one per responsibility. Each either terminates processing or calls `super().handle(request)` / `next.handle(request)` to continue.
4. **Compose the chain** in client code (or a factory/DI container):
   ```
   handler_a.set_next(handler_b).set_next(handler_c)
   ```
5. **Send the request** to the first handler. The rest is automatic.
6. **Optionally** return a result from each handler so the client can detect whether any handler processed the request.

---

## Code Examples

### Python

```python
"""
Real-world example: HTTP middleware pipeline for a web API.

Simulates a chain that handles: rate limiting → authentication →
authorization → request logging → the actual business handler.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import time


# ── Domain objects ─────────────────────────────────────────────────────────

@dataclass
class HttpRequest:
    method: str
    path: str
    api_key: str
    user_role: str           # "admin", "editor", "viewer", "anonymous"
    body: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class HttpResponse:
    status: int
    body: str

    def is_success(self) -> bool:
        return 200 <= self.status < 300


# ── Handler interface ───────────────────────────────────────────────────────

class Middleware(ABC):
    """Abstract handler — every middleware link in the chain."""

    _next: Optional["Middleware"] = None

    def set_next(self, handler: "Middleware") -> "Middleware":
        self._next = handler
        return handler          # allows fluent chaining: a.set_next(b).set_next(c)

    def pass_to_next(self, request: HttpRequest) -> HttpResponse:
        if self._next:
            return self._next.handle(request)
        # End of chain — no handler processed it
        return HttpResponse(404, "No handler found for this request.")

    @abstractmethod
    def handle(self, request: HttpRequest) -> HttpResponse:
        ...


# ── Concrete handlers ───────────────────────────────────────────────────────

class RateLimiterMiddleware(Middleware):
    """Allows at most `max_requests` per `window_seconds` per API key."""

    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self._max = max_requests
        self._window = window_seconds
        self._log: dict[str, list[float]] = {}

    def handle(self, request: HttpRequest) -> HttpResponse:
        key = request.api_key
        now = time.time()
        window_start = now - self._window

        # Clean old entries
        self._log[key] = [t for t in self._log.get(key, []) if t > window_start]

        if len(self._log[key]) >= self._max:
            print(f"[RateLimiter] BLOCKED {key} — too many requests")
            return HttpResponse(429, "Too Many Requests")

        self._log[key].append(now)
        print(f"[RateLimiter] OK — {len(self._log[key])}/{self._max} requests used")
        return self.pass_to_next(request)


class AuthenticationMiddleware(Middleware):
    """Validates the API key against a known registry."""

    VALID_KEYS = {
        "key-admin-001": "admin",
        "key-editor-042": "editor",
        "key-viewer-099": "viewer",
    }

    def handle(self, request: HttpRequest) -> HttpResponse:
        if request.api_key not in self.VALID_KEYS:
            print(f"[Auth] REJECTED unknown API key: {request.api_key}")
            return HttpResponse(401, "Unauthorized — invalid API key")

        # Enrich request with the confirmed role
        request.user_role = self.VALID_KEYS[request.api_key]
        print(f"[Auth] OK — authenticated as role '{request.user_role}'")
        return self.pass_to_next(request)


class AuthorizationMiddleware(Middleware):
    """Ensures the caller has permission to perform the requested action."""

    # path prefix → minimum required role
    ROUTE_PERMISSIONS: dict[str, list[str]] = {
        "/admin":   ["admin"],
        "/articles": ["admin", "editor", "viewer"],
        "/publish":  ["admin", "editor"],
    }

    def handle(self, request: HttpRequest) -> HttpResponse:
        for prefix, allowed_roles in self.ROUTE_PERMISSIONS.items():
            if request.path.startswith(prefix):
                if request.user_role not in allowed_roles:
                    print(f"[Authz] DENIED — role '{request.user_role}' cannot access {request.path}")
                    return HttpResponse(403, "Forbidden")
                print(f"[Authz] OK — role '{request.user_role}' allowed on {request.path}")
                return self.pass_to_next(request)

        # Unknown route — let business handler decide
        return self.pass_to_next(request)


class LoggingMiddleware(Middleware):
    """Logs every request that passes through."""

    def handle(self, request: HttpRequest) -> HttpResponse:
        start = time.perf_counter()
        response = self.pass_to_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(
            f"[Logger] {request.method} {request.path} → "
            f"HTTP {response.status} ({elapsed_ms:.1f} ms)"
        )
        return response


class ArticleHandler(Middleware):
    """Business logic: serves articles."""

    def handle(self, request: HttpRequest) -> HttpResponse:
        if request.path.startswith("/articles"):
            print("[Articles] Processing article request...")
            return HttpResponse(200, '{"articles": ["Design Patterns 101", "Clean Code"]}')
        return self.pass_to_next(request)


class AdminHandler(Middleware):
    """Business logic: admin dashboard."""

    def handle(self, request: HttpRequest) -> HttpResponse:
        if request.path.startswith("/admin"):
            print("[Admin] Serving admin dashboard...")
            return HttpResponse(200, '{"dashboard": "metrics and controls"}')
        return self.pass_to_next(request)


# ── Client code ─────────────────────────────────────────────────────────────

def build_pipeline() -> Middleware:
    """Compose the middleware chain once at startup."""
    rate_limiter = RateLimiterMiddleware(max_requests=3, window_seconds=60)
    auth         = AuthenticationMiddleware()
    authz        = AuthorizationMiddleware()
    logger       = LoggingMiddleware()
    articles     = ArticleHandler()
    admin        = AdminHandler()

    rate_limiter.set_next(auth).set_next(authz).set_next(logger).set_next(articles).set_next(admin)
    return rate_limiter


def send(pipeline: Middleware, request: HttpRequest) -> None:
    print(f"\n{'='*60}")
    print(f"Request: {request.method} {request.path}  [key={request.api_key}]")
    print("-" * 60)
    response = pipeline.handle(request)
    print(f"Final response: HTTP {response.status} — {response.body}")


if __name__ == "__main__":
    pipeline = build_pipeline()

    # Scenario 1: valid admin accessing the admin dashboard
    send(pipeline, HttpRequest("GET", "/admin", api_key="key-admin-001", user_role=""))

    # Scenario 2: editor trying to access admin — should be forbidden
    send(pipeline, HttpRequest("GET", "/admin", api_key="key-editor-042", user_role=""))

    # Scenario 3: unknown API key — should be rejected
    send(pipeline, HttpRequest("GET", "/articles", api_key="bad-key", user_role=""))

    # Scenario 4: viewer accessing articles — should succeed
    send(pipeline, HttpRequest("GET", "/articles/42", api_key="key-viewer-099", user_role=""))
```

---

### Java

```java
/**
 * Real-world example: purchase approval chain in an enterprise system.
 *
 * Purchase requests are escalated through the hierarchy:
 *   Team Lead → Department Manager → Director → CFO
 * Each level can approve up to a certain dollar amount.
 */
package patterns.behavioral.cor;

import java.time.LocalDateTime;
import java.util.Objects;

// ── Domain ──────────────────────────────────────────────────────────────────

record PurchaseRequest(
    String id,
    String requester,
    String description,
    double amount,
    LocalDateTime submittedAt
) {}

record ApprovalResult(boolean approved, String approvedBy, String reason) {

    static ApprovalResult approve(String approver) {
        return new ApprovalResult(true, approver, "Within authority limit");
    }

    static ApprovalResult reject(String reason) {
        return new ApprovalResult(false, "REJECTED", reason);
    }

    static ApprovalResult escalated(String to) {
        return new ApprovalResult(false, "", "Escalated to " + to);
    }

    @Override
    public String toString() {
        return approved
            ? String.format("APPROVED by %s", approvedBy)
            : String.format("NOT APPROVED — %s", reason);
    }
}

// ── Handler interface ────────────────────────────────────────────────────────

interface Approver {
    Approver setNext(Approver next);
    ApprovalResult approve(PurchaseRequest request);
}

// ── Base handler ─────────────────────────────────────────────────────────────

abstract class BaseApprover implements Approver {

    private Approver next;

    @Override
    public Approver setNext(Approver next) {
        this.next = Objects.requireNonNull(next);
        return next;               // enables fluent chaining
    }

    /** Subclasses call this to continue the chain. */
    protected ApprovalResult passUp(PurchaseRequest request) {
        if (next != null) {
            return next.approve(request);
        }
        // Reached the top of the hierarchy with no approval
        return ApprovalResult.reject(
            String.format("Amount $%.2f exceeds maximum approval authority", request.amount())
        );
    }
}

// ── Concrete handlers ─────────────────────────────────────────────────────────

class TeamLead extends BaseApprover {
    private static final double LIMIT = 1_000.00;
    private final String name;

    TeamLead(String name) { this.name = name; }

    @Override
    public ApprovalResult approve(PurchaseRequest request) {
        System.out.printf("[TeamLead:%s] Reviewing $%.2f — limit $%.2f%n",
                          name, request.amount(), LIMIT);
        if (request.amount() <= LIMIT) {
            return ApprovalResult.approve(name + " (Team Lead)");
        }
        System.out.printf("[TeamLead:%s] Exceeds authority, escalating...%n", name);
        return passUp(request);
    }
}

class DepartmentManager extends BaseApprover {
    private static final double LIMIT = 10_000.00;
    private final String name;

    DepartmentManager(String name) { this.name = name; }

    @Override
    public ApprovalResult approve(PurchaseRequest request) {
        System.out.printf("[Manager:%s] Reviewing $%.2f — limit $%.2f%n",
                          name, request.amount(), LIMIT);
        if (request.amount() <= LIMIT) {
            return ApprovalResult.approve(name + " (Dept. Manager)");
        }
        System.out.printf("[Manager:%s] Exceeds authority, escalating...%n", name);
        return passUp(request);
    }
}

class Director extends BaseApprover {
    private static final double LIMIT = 50_000.00;
    private final String name;

    Director(String name) { this.name = name; }

    @Override
    public ApprovalResult approve(PurchaseRequest request) {
        System.out.printf("[Director:%s] Reviewing $%.2f — limit $%.2f%n",
                          name, request.amount(), LIMIT);
        if (request.amount() <= LIMIT) {
            return ApprovalResult.approve(name + " (Director)");
        }
        System.out.printf("[Director:%s] Exceeds authority, escalating to CFO...%n", name);
        return passUp(request);
    }
}

class CFO extends BaseApprover {
    private static final double LIMIT = 500_000.00;
    private final String name;

    CFO(String name) { this.name = name; }

    @Override
    public ApprovalResult approve(PurchaseRequest request) {
        System.out.printf("[CFO:%s] Final review of $%.2f%n", name, request.amount());
        if (request.amount() <= LIMIT) {
            return ApprovalResult.approve(name + " (CFO)");
        }
        // Even the CFO cannot approve — needs board vote
        return ApprovalResult.reject(
            String.format("$%.2f requires Board of Directors approval", request.amount())
        );
    }
}

// ── Client ────────────────────────────────────────────────────────────────────

public class PurchaseApprovalDemo {

    public static void main(String[] args) {
        // Compose the approval chain
        TeamLead      teamLead = new TeamLead("Alice");
        DepartmentManager mgr = new DepartmentManager("Bob");
        Director      director = new Director("Carol");
        CFO              cfo  = new CFO("Dave");

        teamLead.setNext(mgr).setNext(director).setNext(cfo);

        PurchaseRequest[] requests = {
            new PurchaseRequest("PR-001", "Eve",   "Office supplies",          750.00,   LocalDateTime.now()),
            new PurchaseRequest("PR-002", "Frank", "Conference sponsorship",  8_500.00,  LocalDateTime.now()),
            new PurchaseRequest("PR-003", "Grace", "Server infrastructure",  42_000.00,  LocalDateTime.now()),
            new PurchaseRequest("PR-004", "Hank",  "ERP software license",  200_000.00, LocalDateTime.now()),
            new PurchaseRequest("PR-005", "Iris",  "Acquisition deposit",   600_000.00, LocalDateTime.now()),
        };

        for (PurchaseRequest req : requests) {
            System.out.println("─".repeat(60));
            System.out.printf("Request %s: \"%s\" — $%.2f by %s%n",
                              req.id(), req.description(), req.amount(), req.requester());
            ApprovalResult result = teamLead.approve(req);
            System.out.println("Result: " + result);
            System.out.println();
        }
    }
}
```

---

### C++

```cpp
/**
 * Real-world example: technical support ticket escalation system.
 *
 * Level 1 support (FAQ bot) → Level 2 (help desk agent) →
 * Level 3 (senior engineer) → Level 4 (engineering team lead).
 *
 * Compiled with: g++ -std=c++20 -o support_chain support_chain.cpp
 */
#include <iostream>
#include <memory>
#include <string>
#include <vector>
#include <optional>

// ── Domain ────────────────────────────────────────────────────────────────────

enum class TicketPriority { LOW, MEDIUM, HIGH, CRITICAL };

std::string priority_label(TicketPriority p) {
    switch (p) {
        case TicketPriority::LOW:      return "LOW";
        case TicketPriority::MEDIUM:   return "MEDIUM";
        case TicketPriority::HIGH:     return "HIGH";
        case TicketPriority::CRITICAL: return "CRITICAL";
    }
    return "UNKNOWN";
}

struct SupportTicket {
    int         id;
    std::string customer;
    std::string description;
    TicketPriority priority;
    int         complexity;   // 1–10 scale
};

struct Resolution {
    bool        resolved;
    std::string resolved_by;
    std::string notes;
};

// ── Handler interface ─────────────────────────────────────────────────────────

class SupportHandler {
public:
    virtual ~SupportHandler() = default;

    SupportHandler* set_next(std::unique_ptr<SupportHandler> next) {
        next_ = std::move(next);
        return next_.get();
    }

    virtual Resolution handle(const SupportTicket& ticket) = 0;

protected:
    Resolution pass_to_next(const SupportTicket& ticket) {
        if (next_) {
            return next_->handle(ticket);
        }
        return { false, "UNRESOLVED", "No handler was able to resolve this ticket." };
    }

private:
    std::unique_ptr<SupportHandler> next_;
};

// ── Concrete handlers ─────────────────────────────────────────────────────────

class FAQBot : public SupportHandler {
public:
    Resolution handle(const SupportTicket& ticket) override {
        std::cout << "[L1-FAQBot] Checking knowledge base for ticket #" << ticket.id << "...\n";

        // Bot only handles simple, low-priority issues
        if (ticket.priority == TicketPriority::LOW && ticket.complexity <= 2) {
            std::cout << "[L1-FAQBot] Found matching FAQ article. Auto-resolving.\n";
            return { true, "FAQ Bot", "Resolved via FAQ article KB-4421." };
        }

        std::cout << "[L1-FAQBot] Cannot resolve — escalating to human agent.\n";
        return pass_to_next(ticket);
    }
};

class HelpDeskAgent : public SupportHandler {
    std::string name_;
public:
    explicit HelpDeskAgent(std::string name) : name_(std::move(name)) {}

    Resolution handle(const SupportTicket& ticket) override {
        std::cout << "[L2-HelpDesk:" << name_ << "] Reviewing ticket #" << ticket.id
                  << " (priority=" << priority_label(ticket.priority)
                  << ", complexity=" << ticket.complexity << ")\n";

        if (ticket.complexity <= 5 && ticket.priority != TicketPriority::CRITICAL) {
            std::cout << "[L2-HelpDesk:" << name_ << "] Resolved with standard procedure.\n";
            return { true, name_ + " (Help Desk)", "Applied standard troubleshooting steps." };
        }

        std::cout << "[L2-HelpDesk:" << name_ << "] Beyond my expertise — escalating to Senior Engineer.\n";
        return pass_to_next(ticket);
    }
};

class SeniorEngineer : public SupportHandler {
    std::string name_;
public:
    explicit SeniorEngineer(std::string name) : name_(std::move(name)) {}

    Resolution handle(const SupportTicket& ticket) override {
        std::cout << "[L3-SeniorEng:" << name_ << "] Deep-diving ticket #" << ticket.id << "...\n";

        if (ticket.priority != TicketPriority::CRITICAL && ticket.complexity <= 8) {
            std::cout << "[L3-SeniorEng:" << name_ << "] Root cause identified. Fix deployed.\n";
            return { true, name_ + " (Senior Engineer)", "Root cause analysis complete, hotfix applied." };
        }

        std::cout << "[L3-SeniorEng:" << name_ << "] Critical or extreme complexity — escalating to Team Lead.\n";
        return pass_to_next(ticket);
    }
};

class EngineeringTeamLead : public SupportHandler {
    std::string name_;
public:
    explicit EngineeringTeamLead(std::string name) : name_(std::move(name)) {}

    Resolution handle(const SupportTicket& ticket) override {
        std::cout << "[L4-TeamLead:" << name_ << "] War-room mode for ticket #" << ticket.id << ".\n";
        // Team lead handles everything that reaches them
        return { true, name_ + " (Team Lead)", "All-hands incident resolved. Post-mortem scheduled." };
    }
};

// ── Client ────────────────────────────────────────────────────────────────────

int main() {
    // Build the chain
    auto bot    = std::make_unique<FAQBot>();
    auto agent  = std::make_unique<HelpDeskAgent>("Sam");
    auto senior = std::make_unique<SeniorEngineer>("Morgan");
    auto lead   = std::make_unique<EngineeringTeamLead>("Jordan");

    // Keep a pointer to the head before ownership is transferred
    FAQBot* chain_head = bot.get();

    bot->set_next(std::move(agent))
       ->set_next(std::move(senior))
       ->set_next(std::move(lead));

    // Tickets to process
    std::vector<SupportTicket> tickets = {
        { 101, "Alice",   "How do I reset my password?",         TicketPriority::LOW,      1 },
        { 102, "Bob",     "Cannot export data to CSV",            TicketPriority::MEDIUM,   4 },
        { 103, "Carol",   "API returning 500 errors intermittently", TicketPriority::HIGH,  7 },
        { 104, "Dave",    "Production database offline",          TicketPriority::CRITICAL, 9 },
    };

    for (const auto& ticket : tickets) {
        std::cout << "\n" << std::string(60, '=') << "\n";
        std::cout << "Ticket #" << ticket.id << " from " << ticket.customer
                  << ": \"" << ticket.description << "\"\n";
        std::cout << std::string(60, '-') << "\n";

        Resolution res = chain_head->handle(ticket);

        std::cout << "\nOutcome: " << (res.resolved ? "RESOLVED" : "UNRESOLVED")
                  << " by " << res.resolved_by << "\n"
                  << "Notes:   " << res.notes << "\n";
    }

    return 0;
}
```

---

### C#

```csharp
/**
 * Real-world example: expense report approval pipeline.
 *
 * Expense claims route through: Finance Bot (auto-approve small amounts) →
 * Line Manager → Finance Controller → CFO.
 */
using System;
using System.Collections.Generic;

namespace ChainOfResponsibility;

// ── Domain ────────────────────────────────────────────────────────────────────

public record ExpenseClaim(
    string ClaimId,
    string Employee,
    string Category,
    decimal Amount,
    string Justification
);

public record ApprovalDecision(bool Approved, string ApprovedBy, string Comments)
{
    public override string ToString() =>
        Approved
            ? $"APPROVED by {ApprovedBy} — {Comments}"
            : $"DENIED — {Comments}";
}

// ── Handler interface ─────────────────────────────────────────────────────────

public interface IExpenseApprover
{
    IExpenseApprover SetNext(IExpenseApprover next);
    ApprovalDecision Evaluate(ExpenseClaim claim);
}

// ── Base handler ──────────────────────────────────────────────────────────────

public abstract class ExpenseApproverBase : IExpenseApprover
{
    private IExpenseApprover? _next;

    public IExpenseApprover SetNext(IExpenseApprover next)
    {
        _next = next;
        return next;   // fluent chaining
    }

    protected ApprovalDecision Escalate(ExpenseClaim claim)
    {
        if (_next is not null)
            return _next.Evaluate(claim);

        return new ApprovalDecision(false, "SYSTEM",
            $"Claim {claim.ClaimId} for ${claim.Amount:N2} exceeds all approval limits. " +
            "Board approval required.");
    }

    public abstract ApprovalDecision Evaluate(ExpenseClaim claim);
}

// ── Concrete handlers ─────────────────────────────────────────────────────────

/// <summary>Automatically approves routine, small-value claims.</summary>
public class FinanceBot : ExpenseApproverBase
{
    private const decimal Limit = 50m;

    private static readonly HashSet<string> RoutineCategories =
        new() { "Meals", "Transport", "Office Supplies" };

    public override ApprovalDecision Evaluate(ExpenseClaim claim)
    {
        Console.WriteLine($"  [FinanceBot] Checking claim {claim.ClaimId}: ${claim.Amount:N2}");

        if (claim.Amount <= Limit && RoutineCategories.Contains(claim.Category))
        {
            Console.WriteLine("  [FinanceBot] Auto-approved (routine, low-value).");
            return new ApprovalDecision(true, "Finance Bot",
                "Auto-approved: routine category, within bot limit.");
        }

        Console.WriteLine("  [FinanceBot] Requires human review — escalating.");
        return Escalate(claim);
    }
}

public class LineManager : ExpenseApproverBase
{
    private const decimal Limit = 500m;
    private readonly string _name;

    public LineManager(string name) => _name = name;

    public override ApprovalDecision Evaluate(ExpenseClaim claim)
    {
        Console.WriteLine($"  [LineManager:{_name}] Reviewing claim {claim.ClaimId}: ${claim.Amount:N2}");

        if (claim.Amount <= Limit)
        {
            Console.WriteLine($"  [LineManager:{_name}] Approved within manager limit.");
            return new ApprovalDecision(true, $"{_name} (Line Manager)",
                "Approved — within manager discretionary limit.");
        }

        Console.WriteLine($"  [LineManager:{_name}] Exceeds limit — escalating to Finance Controller.");
        return Escalate(claim);
    }
}

public class FinanceController : ExpenseApproverBase
{
    private const decimal Limit = 5_000m;
    private readonly string _name;

    public FinanceController(string name) => _name = name;

    public override ApprovalDecision Evaluate(ExpenseClaim claim)
    {
        Console.WriteLine($"  [FinanceCtrl:{_name}] Auditing claim {claim.ClaimId}: ${claim.Amount:N2}");

        // Finance controller also checks for policy compliance
        if (claim.Category == "Entertainment" && claim.Amount > 200m)
        {
            Console.WriteLine($"  [FinanceCtrl:{_name}] Entertainment expenses above $200 need CFO sign-off.");
            return Escalate(claim);
        }

        if (claim.Amount <= Limit)
        {
            Console.WriteLine($"  [FinanceCtrl:{_name}] Approved after audit.");
            return new ApprovalDecision(true, $"{_name} (Finance Controller)",
                "Approved after financial audit.");
        }

        Console.WriteLine($"  [FinanceCtrl:{_name}] Exceeds controller limit — escalating to CFO.");
        return Escalate(claim);
    }
}

public class CFO : ExpenseApproverBase
{
    private const decimal Limit = 100_000m;
    private readonly string _name;

    public CFO(string name) => _name = name;

    public override ApprovalDecision Evaluate(ExpenseClaim claim)
    {
        Console.WriteLine($"  [CFO:{_name}] Final review of claim {claim.ClaimId}: ${claim.Amount:N2}");

        if (claim.Amount <= Limit)
        {
            return new ApprovalDecision(true, $"{_name} (CFO)",
                "Approved at executive level.");
        }

        return Escalate(claim);   // will bubble up as "no handler"
    }
}

// ── Client ────────────────────────────────────────────────────────────────────

public class Program
{
    public static void Main()
    {
        // Compose the approval chain
        var bot        = new FinanceBot();
        var manager    = new LineManager("Priya");
        var controller = new FinanceController("Raj");
        var cfo        = new CFO("Leila");

        bot.SetNext(manager).SetNext(controller).SetNext(cfo);

        var claims = new List<ExpenseClaim>
        {
            new("EXP-001", "Tom",   "Transport",     35.00m,      "Taxi to client site"),
            new("EXP-002", "Sara",  "Office Supplies", 120.00m,   "Ergonomic keyboard"),
            new("EXP-003", "Mike",  "Entertainment", 450.00m,     "Client dinner"),
            new("EXP-004", "Nina",  "Training",      3_200.00m,   "AWS certification course"),
            new("EXP-005", "Omar",  "Equipment",    75_000.00m,   "High-performance workstation cluster"),
            new("EXP-006", "Yuki",  "Acquisition", 250_000.00m,   "IP licensing agreement"),
        };

        foreach (var claim in claims)
        {
            Console.WriteLine(new string('=', 60));
            Console.WriteLine($"Claim {claim.ClaimId}: \"{claim.Category}\" — ${claim.Amount:N2} ({claim.Employee})");
            Console.WriteLine(new string('-', 60));
            var decision = bot.Evaluate(claim);
            Console.WriteLine($"Decision: {decision}\n");
        }
    }
}
```

---

### TypeScript

```typescript
/**
 * Real-world example: Express-style middleware pipeline for form validation.
 *
 * A user registration form submission passes through:
 *   Schema validation → Sanitization → Duplicate-user check → Spam detection → Registration handler
 *
 * Run with: npx ts-node registration_pipeline.ts
 */

// ── Domain types ──────────────────────────────────────────────────────────────

interface RegistrationRequest {
  username: string;
  email: string;
  password: string;
  referralCode?: string;
  ipAddress: string;
}

interface ValidationResult {
  passed: boolean;
  errors: string[];
  sanitized?: RegistrationRequest;
}

// ── Handler interface ─────────────────────────────────────────────────────────

abstract class RegistrationHandler {
  private nextHandler: RegistrationHandler | null = null;

  setNext(handler: RegistrationHandler): RegistrationHandler {
    this.nextHandler = handler;
    return handler; // enables fluent chaining
  }

  protected passToNext(request: RegistrationRequest): ValidationResult {
    if (this.nextHandler) {
      return this.nextHandler.handle(request);
    }
    // End of successful chain
    return {
      passed: true,
      errors: [],
      sanitized: request,
    };
  }

  abstract handle(request: RegistrationRequest): ValidationResult;
}

// ── Concrete handlers ─────────────────────────────────────────────────────────

/** Validates that required fields are present and structurally correct. */
class SchemaValidationHandler extends RegistrationHandler {
  private readonly EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  private readonly MIN_PASSWORD_LENGTH = 8;

  handle(request: RegistrationRequest): ValidationResult {
    console.log("[SchemaValidation] Checking required fields...");
    const errors: string[] = [];

    if (!request.username || request.username.trim().length < 3) {
      errors.push("Username must be at least 3 characters.");
    }
    if (!request.email || !this.EMAIL_REGEX.test(request.email)) {
      errors.push("A valid email address is required.");
    }
    if (!request.password || request.password.length < this.MIN_PASSWORD_LENGTH) {
      errors.push(`Password must be at least ${this.MIN_PASSWORD_LENGTH} characters.`);
    }

    if (errors.length > 0) {
      console.log("[SchemaValidation] FAILED:", errors);
      return { passed: false, errors };
    }

    console.log("[SchemaValidation] OK");
    return this.passToNext(request);
  }
}

/** Strips dangerous characters and normalises input. */
class SanitizationHandler extends RegistrationHandler {
  handle(request: RegistrationRequest): ValidationResult {
    console.log("[Sanitization] Sanitising input...");

    const sanitized: RegistrationRequest = {
      ...request,
      // Trim whitespace and remove HTML tags
      username: request.username.trim().replace(/<[^>]*>/g, ""),
      email: request.email.trim().toLowerCase(),
      password: request.password, // passwords must not be altered
      ipAddress: request.ipAddress.trim(),
    };

    console.log("[Sanitization] OK — normalised email to:", sanitized.email);
    return this.passToNext(sanitized);
  }
}

/** Simulates checking whether the email is already registered. */
class DuplicateCheckHandler extends RegistrationHandler {
  private readonly existingEmails = new Set([
    "alice@example.com",
    "bob@example.com",
    "taken@domain.org",
  ]);

  handle(request: RegistrationRequest): ValidationResult {
    console.log("[DuplicateCheck] Checking for existing account...");

    if (this.existingEmails.has(request.email)) {
      const msg = `An account with email "${request.email}" already exists.`;
      console.log("[DuplicateCheck] FAILED:", msg);
      return { passed: false, errors: [msg] };
    }

    console.log("[DuplicateCheck] OK — email is available");
    return this.passToNext(request);
  }
}

/** Detects spam registrations based on IP reputation and patterns. */
class SpamDetectionHandler extends RegistrationHandler {
  private readonly blockedIPs = new Set(["192.168.1.100", "10.0.0.99"]);
  private readonly registrationCounts = new Map<string, number>([
    ["203.0.113.42", 50], // suspicious — 50 registrations today
  ]);
  private readonly RATE_LIMIT = 10;

  handle(request: RegistrationRequest): ValidationResult {
    console.log("[SpamDetection] Checking IP reputation...");

    if (this.blockedIPs.has(request.ipAddress)) {
      const msg = "Registration blocked: IP address is on the spam blocklist.";
      console.log("[SpamDetection] BLOCKED:", request.ipAddress);
      return { passed: false, errors: [msg] };
    }

    const count = this.registrationCounts.get(request.ipAddress) ?? 0;
    if (count >= this.RATE_LIMIT) {
      const msg = `Too many registrations from IP ${request.ipAddress} today.`;
      console.log("[SpamDetection] RATE LIMITED:", msg);
      return { passed: false, errors: [msg] };
    }

    console.log("[SpamDetection] OK — IP appears legitimate");
    return this.passToNext(request);
  }
}

/** Final handler: performs actual account creation. */
class AccountCreationHandler extends RegistrationHandler {
  private createdAccounts: RegistrationRequest[] = [];

  handle(request: RegistrationRequest): ValidationResult {
    console.log("[AccountCreation] Creating account for", request.email);
    // In a real app: hash the password and persist to DB
    this.createdAccounts.push(request);
    console.log(
      `[AccountCreation] Account created! Total accounts: ${this.createdAccounts.length}`
    );
    return { passed: true, errors: [], sanitized: request };
  }
}

// ── Client code ───────────────────────────────────────────────────────────────

function buildRegistrationPipeline(): RegistrationHandler {
  const schema      = new SchemaValidationHandler();
  const sanitize    = new SanitizationHandler();
  const duplicate   = new DuplicateCheckHandler();
  const spam        = new SpamDetectionHandler();
  const creation    = new AccountCreationHandler();

  schema.setNext(sanitize).setNext(duplicate).setNext(spam).setNext(creation);
  return schema;
}

function register(pipeline: RegistrationHandler, req: RegistrationRequest): void {
  console.log("\n" + "=".repeat(60));
  console.log(`Registering: ${req.email} from ${req.ipAddress}`);
  console.log("-".repeat(60));
  const result = pipeline.handle(req);
  if (result.passed) {
    console.log("Registration SUCCESSFUL");
  } else {
    console.log("Registration FAILED:");
    result.errors.forEach((e) => console.log(`  - ${e}`));
  }
}

const pipeline = buildRegistrationPipeline();

register(pipeline, {
  username: "johndoe",
  email: "john@example.com",
  password: "secureP@ss1",
  ipAddress: "198.51.100.1",
});

register(pipeline, {
  username: "jo",           // too short
  email: "invalid-email",
  password: "123",
  ipAddress: "198.51.100.2",
});

register(pipeline, {
  username: "alice_smith",
  email: "alice@example.com", // already registered
  password: "ValidPass99!",
  ipAddress: "198.51.100.3",
});

register(pipeline, {
  username: "spammer",
  email: "spam@evil.com",
  password: "ValidPass99!",
  ipAddress: "192.168.1.100", // blocked IP
});
```

---

### Go

```go
// Real-world example: logging middleware chain for an HTTP server.
//
// Each middleware wraps the next: RecoveryMiddleware → RequestID →
// RequestLogger → AuthMiddleware → RateLimiter → BusinessHandler
//
// Run: go run main.go

package main

import (
	"fmt"
	"math/rand"
	"strings"
	"time"
)

// ── Domain types ──────────────────────────────────────────────────────────────

// Context carries request data down the chain (simulates http.Request + response writer).
type Context struct {
	Method    string
	Path      string
	Headers   map[string]string
	RequestID string
	UserID    string
	StartTime time.Time

	// Response fields
	StatusCode int
	Body       string
}

func newContext(method, path string, headers map[string]string) *Context {
	return &Context{
		Method:    method,
		Path:      path,
		Headers:   headers,
		StartTime: time.Now(),
		StatusCode: 200,
	}
}

func (c *Context) respond(status int, body string) {
	c.StatusCode = status
	c.Body = body
}

// ── Handler interface ─────────────────────────────────────────────────────────

// Handler is the link type in the chain.
type Handler interface {
	Handle(ctx *Context)
}

// HandlerFunc allows plain functions to satisfy the Handler interface.
type HandlerFunc func(ctx *Context)

func (f HandlerFunc) Handle(ctx *Context) { f(ctx) }

// ── Middleware builder (wraps next with additional behaviour) ──────────────────

// RecoveryMiddleware catches panics and returns a 500 response.
func RecoveryMiddleware(next Handler) Handler {
	return HandlerFunc(func(ctx *Context) {
		defer func() {
			if r := recover(); r != nil {
				fmt.Printf("[Recovery] Panic recovered: %v\n", r)
				ctx.respond(500, "Internal Server Error")
			}
		}()
		next.Handle(ctx)
	})
}

// RequestIDMiddleware attaches a unique request identifier.
func RequestIDMiddleware(next Handler) Handler {
	return HandlerFunc(func(ctx *Context) {
		ctx.RequestID = fmt.Sprintf("req-%08x", rand.Uint32())
		fmt.Printf("[RequestID] Assigned ID: %s\n", ctx.RequestID)
		next.Handle(ctx)
	})
}

// LoggingMiddleware records method, path, status and duration.
func LoggingMiddleware(next Handler) Handler {
	return HandlerFunc(func(ctx *Context) {
		next.Handle(ctx)
		elapsed := time.Since(ctx.StartTime)
		fmt.Printf("[Logger] %s %s → HTTP %d (%s) [%s]\n",
			ctx.Method, ctx.Path, ctx.StatusCode, elapsed.Round(time.Microsecond), ctx.RequestID)
	})
}

// AuthMiddleware validates the Bearer token in the Authorization header.
func AuthMiddleware(next Handler) Handler {
	// token → userID mapping (in production this would verify JWTs)
	validTokens := map[string]string{
		"token-alice": "user-alice",
		"token-bob":   "user-bob",
	}

	return HandlerFunc(func(ctx *Context) {
		authHeader := ctx.Headers["Authorization"]
		if !strings.HasPrefix(authHeader, "Bearer ") {
			fmt.Println("[Auth] Missing or malformed Authorization header")
			ctx.respond(401, `{"error":"Unauthorized"}`)
			return
		}

		token := strings.TrimPrefix(authHeader, "Bearer ")
		userID, ok := validTokens[token]
		if !ok {
			fmt.Printf("[Auth] Invalid token: %s\n", token)
			ctx.respond(401, `{"error":"Invalid token"}`)
			return
		}

		ctx.UserID = userID
		fmt.Printf("[Auth] Authenticated user: %s\n", userID)
		next.Handle(ctx)
	})
}

// RateLimiterMiddleware allows 3 requests per user per window.
func RateLimiterMiddleware(next Handler) Handler {
	counts := map[string]int{}
	const limit = 3

	return HandlerFunc(func(ctx *Context) {
		counts[ctx.UserID]++
		if counts[ctx.UserID] > limit {
			fmt.Printf("[RateLimit] User %s has exceeded %d requests\n", ctx.UserID, limit)
			ctx.respond(429, `{"error":"Too Many Requests"}`)
			return
		}
		fmt.Printf("[RateLimit] User %s: %d/%d requests used\n", ctx.UserID, counts[ctx.UserID], limit)
		next.Handle(ctx)
	})
}

// ── Business handler (terminal handler) ───────────────────────────────────────

type Router struct {
	routes map[string]HandlerFunc
}

func NewRouter() *Router {
	r := &Router{routes: make(map[string]HandlerFunc)}

	r.routes["/api/profile"] = func(ctx *Context) {
		ctx.respond(200, fmt.Sprintf(`{"user":"%s","profile":"data here"}`, ctx.UserID))
	}
	r.routes["/api/settings"] = func(ctx *Context) {
		ctx.respond(200, `{"theme":"dark","notifications":true}`)
	}

	return r
}

func (r *Router) Handle(ctx *Context) {
	handler, ok := r.routes[ctx.Path]
	if !ok {
		ctx.respond(404, `{"error":"Not Found"}`)
		return
	}
	handler(ctx)
}

// ── Chain builder (wraps in reverse order) ───────────────────────────────────

func buildChain(router *Router) Handler {
	// Build inside-out: the innermost handler is the router,
	// and each middleware wraps around it.
	var h Handler = router
	h = RateLimiterMiddleware(h)
	h = AuthMiddleware(h)
	h = LoggingMiddleware(h)
	h = RequestIDMiddleware(h)
	h = RecoveryMiddleware(h)
	return h
}

// ── Main ──────────────────────────────────────────────────────────────────────

func simulate(chain Handler, method, path string, headers map[string]string) {
	fmt.Println("\n" + strings.Repeat("=", 60))
	fmt.Printf("Request: %s %s\n", method, path)
	fmt.Println(strings.Repeat("-", 60))
	ctx := newContext(method, path, headers)
	chain.Handle(ctx)
	fmt.Printf("Response body: %s\n", ctx.Body)
}

func main() {
	router := NewRouter()
	chain := buildChain(router)

	// Valid request
	simulate(chain, "GET", "/api/profile", map[string]string{
		"Authorization": "Bearer token-alice",
	})

	// Missing auth token
	simulate(chain, "GET", "/api/settings", map[string]string{})

	// Invalid token
	simulate(chain, "GET", "/api/profile", map[string]string{
		"Authorization": "Bearer bad-token",
	})

	// Rate limit: send 4 requests for the same user
	for i := 0; i < 4; i++ {
		simulate(chain, "GET", "/api/settings", map[string]string{
			"Authorization": "Bearer token-bob",
		})
	}
}
```

---

### PHP

```php
<?php
/**
 * Real-world example: content moderation pipeline for user-submitted posts.
 *
 * Submitted content passes through:
 *   ProfanityFilter → SpamDetector → LinkValidator → WordCountChecker → Publisher
 *
 * PHP 8.1+ (uses readonly properties and enums)
 * Run: php content_moderation.php
 */

declare(strict_types=1);

// ── Domain ────────────────────────────────────────────────────────────────────

enum ModerationStatus
{
    case Approved;
    case Rejected;
    case Pending;
}

final class UserPost
{
    public function __construct(
        public readonly string $id,
        public readonly string $author,
        public readonly string $title,
        public string          $content,   // mutable so sanitisers can clean it
    ) {}
}

final class ModerationResult
{
    public function __construct(
        public readonly ModerationStatus $status,
        public readonly string           $checkedBy,
        public readonly string           $reason,
    ) {}

    public function __toString(): string
    {
        return sprintf('[%s] via %s — %s',
            $this->status->name, $this->checkedBy, $this->reason);
    }
}

// ── Handler interface ─────────────────────────────────────────────────────────

interface ModerationHandler
{
    public function setNext(ModerationHandler $handler): ModerationHandler;
    public function handle(UserPost $post): ModerationResult;
}

// ── Abstract base ─────────────────────────────────────────────────────────────

abstract class AbstractModerationHandler implements ModerationHandler
{
    private ?ModerationHandler $next = null;

    public function setNext(ModerationHandler $handler): ModerationHandler
    {
        $this->next = $handler;
        return $handler; // fluent chaining
    }

    protected function passToNext(UserPost $post): ModerationResult
    {
        if ($this->next !== null) {
            return $this->next->handle($post);
        }

        // Default: if nothing rejected it, approve it
        return new ModerationResult(
            ModerationStatus::Approved,
            'System',
            'All checks passed.'
        );
    }
}

// ── Concrete handlers ─────────────────────────────────────────────────────────

final class ProfanityFilter extends AbstractModerationHandler
{
    private array $banned = ['badword1', 'badword2', 'offensive'];

    public function handle(UserPost $post): ModerationResult
    {
        echo "[ProfanityFilter] Scanning post {$post->id}...\n";

        foreach ($this->banned as $word) {
            if (stripos($post->content, $word) !== false) {
                // Replace rather than reject — warn if too many hits
                $post->content = str_ireplace($word, str_repeat('*', strlen($word)), $post->content);
                echo "[ProfanityFilter] Masked profanity: '$word'\n";
            }
        }

        // Count remaining masked words as a policy signal (simplified)
        $maskedCount = substr_count($post->content, '***');
        if ($maskedCount > 3) {
            echo "[ProfanityFilter] Too much profanity — REJECTING.\n";
            return new ModerationResult(
                ModerationStatus::Rejected,
                'ProfanityFilter',
                'Content contains excessive profanity.'
            );
        }

        echo "[ProfanityFilter] OK.\n";
        return $this->passToNext($post);
    }
}

final class SpamDetector extends AbstractModerationHandler
{
    private const MAX_URLS    = 5;
    private const MAX_CAPS_RATIO = 0.5;

    public function handle(UserPost $post): ModerationResult
    {
        echo "[SpamDetector] Analysing post {$post->id}...\n";

        // Detect excessive URLs
        $urlCount = preg_match_all('/https?:\/\/\S+/', $post->content);
        if ($urlCount > self::MAX_URLS) {
            echo "[SpamDetector] REJECTED — too many URLs ($urlCount).\n";
            return new ModerationResult(
                ModerationStatus::Rejected,
                'SpamDetector',
                "Post contains $urlCount URLs; maximum is " . self::MAX_URLS . '.'
            );
        }

        // Detect ALL CAPS abuse
        $letters    = preg_replace('/[^a-zA-Z]/', '', $post->content);
        $upperCount = strlen(preg_replace('/[^A-Z]/', '', $letters));
        $totalLetters = strlen($letters);

        if ($totalLetters > 20 && ($upperCount / $totalLetters) > self::MAX_CAPS_RATIO) {
            echo "[SpamDetector] REJECTED — excessive caps.\n";
            return new ModerationResult(
                ModerationStatus::Rejected,
                'SpamDetector',
                'Post appears to be shouting (excessive capitalisation).'
            );
        }

        echo "[SpamDetector] OK.\n";
        return $this->passToNext($post);
    }
}

final class LinkValidator extends AbstractModerationHandler
{
    private array $blockedDomains = ['malware.example', 'phishing.example', 'spam-site.net'];

    public function handle(UserPost $post): ModerationResult
    {
        echo "[LinkValidator] Validating links in post {$post->id}...\n";

        preg_match_all('/https?:\/\/([^\/\s]+)/', $post->content, $matches);
        $domains = $matches[1] ?? [];

        foreach ($domains as $domain) {
            if (in_array(strtolower($domain), $this->blockedDomains, true)) {
                echo "[LinkValidator] REJECTED — blocked domain: $domain.\n";
                return new ModerationResult(
                    ModerationStatus::Rejected,
                    'LinkValidator',
                    "Post contains a link to blocked domain: $domain."
                );
            }
        }

        echo "[LinkValidator] OK — " . count($domains) . " link(s) checked.\n";
        return $this->passToNext($post);
    }
}

final class WordCountChecker extends AbstractModerationHandler
{
    private const MIN_WORDS = 10;
    private const MAX_WORDS = 5000;

    public function handle(UserPost $post): ModerationResult
    {
        echo "[WordCountChecker] Counting words in post {$post->id}...\n";

        $wordCount = str_word_count($post->content);
        echo "[WordCountChecker] Word count: $wordCount\n";

        if ($wordCount < self::MIN_WORDS) {
            return new ModerationResult(
                ModerationStatus::Rejected,
                'WordCountChecker',
                "Post is too short ($wordCount words; minimum " . self::MIN_WORDS . ').'
            );
        }

        if ($wordCount > self::MAX_WORDS) {
            return new ModerationResult(
                ModerationStatus::Rejected,
                'WordCountChecker',
                "Post is too long ($wordCount words; maximum " . self::MAX_WORDS . ').'
            );
        }

        echo "[WordCountChecker] OK.\n";
        return $this->passToNext($post);
    }
}

final class Publisher extends AbstractModerationHandler
{
    private array $published = [];

    public function handle(UserPost $post): ModerationResult
    {
        $this->published[] = $post->id;
        echo "[Publisher] Post {$post->id} published! Total published: " . count($this->published) . "\n";
        return new ModerationResult(
            ModerationStatus::Approved,
            'Publisher',
            'Post successfully published.'
        );
    }
}

// ── Client ────────────────────────────────────────────────────────────────────

function buildModerationPipeline(): ModerationHandler
{
    $profanity  = new ProfanityFilter();
    $spam       = new SpamDetector();
    $links      = new LinkValidator();
    $wordCount  = new WordCountChecker();
    $publisher  = new Publisher();

    $profanity->setNext($spam)->setNext($links)->setNext($wordCount)->setNext($publisher);

    return $profanity;
}

$pipeline = buildModerationPipeline();

$posts = [
    new UserPost('post-001', 'Alice', 'My Travel Blog',
        'Visited Paris last week and it was absolutely wonderful! The food, the culture, ' .
        'the architecture — everything was amazing. Highly recommend the Louvre museum.'),

    new UserPost('post-002', 'Bob', 'Short post',
        'Cool story bro.'), // too short

    new UserPost('post-003', 'Carol', 'Free Money!!!',
        'CLICK HERE NOW TO GET FREE MONEY! VISIT http://spam-site.net TODAY! ' .
        'THIS AMAZING OFFER WON\'T LAST LONG! ACT IMMEDIATELY!'),

    new UserPost('post-004', 'Dave', 'Tech Review',
        'Spent a week testing this new framework. It has some offensive design choices ' .
        'in the API but overall the developer experience is solid. Performance benchmarks ' .
        'show a 40% improvement over the previous version.'),
];

foreach ($posts as $post) {
    echo "\n" . str_repeat('=', 60) . "\n";
    echo "Post '{$post->title}' by {$post->author} [{$post->id}]\n";
    echo str_repeat('-', 60) . "\n";
    $result = $pipeline->handle($post);
    echo "Moderation result: $result\n";
}
```

---

### Ruby

```ruby
# Real-world example: discount calculation pipeline for an e-commerce checkout.
#
# Discount rules are applied in order:
#   LoyaltyDiscount → SeasonalDiscount → CouponDiscount → BulkDiscount → PriceCalculator
#
# Each handler may reduce the price or simply pass the order along.
# Run: ruby discount_chain.rb

# ── Domain ────────────────────────────────────────────────────────────────────

Order = Struct.new(
  :id,
  :customer_tier,   # :bronze, :silver, :gold, :platinum
  :items,           # Array of { name:, qty:, unit_price: }
  :coupon_code,
  :applied_discounts,
  :final_price,
  keyword_init: true
) do
  def subtotal
    items.sum { |i| i[:qty] * i[:unit_price] }
  end
end

DiscountResult = Struct.new(:order, :message, keyword_init: true)

# ── Base handler ───────────────────────────────────────────────────────────────

class DiscountHandler
  def set_next(handler)
    @next_handler = handler
    handler # enables fluent chaining
  end

  def handle(order)
    if @next_handler
      @next_handler.handle(order)
    else
      DiscountResult.new(order: order, message: "All discounts applied.")
    end
  end

  protected

  def pass_to_next(order)
    if @next_handler
      @next_handler.handle(order)
    else
      DiscountResult.new(order: order, message: "Processing complete.")
    end
  end
end

# ── Concrete handlers ─────────────────────────────────────────────────────────

# Applies a percentage discount based on the customer's loyalty tier.
class LoyaltyDiscountHandler < DiscountHandler
  TIER_DISCOUNTS = {
    bronze:   0.00,
    silver:   0.05,
    gold:     0.10,
    platinum: 0.15
  }.freeze

  def handle(order)
    rate = TIER_DISCOUNTS[order.customer_tier] || 0.00
    if rate > 0
      discount = order.final_price * rate
      order.final_price -= discount
      order.applied_discounts << "Loyalty (#{order.customer_tier}): -$#{'%.2f' % discount}"
      puts "[LoyaltyDiscount] Applied #{(rate * 100).to_i}% loyalty discount: -$#{'%.2f' % discount}"
    else
      puts "[LoyaltyDiscount] No loyalty discount for tier: #{order.customer_tier}"
    end
    pass_to_next(order)
  end
end

# Applies a seasonal promotion (e.g., 20% off in December).
class SeasonalDiscountHandler < DiscountHandler
  def handle(order)
    month = Time.now.month
    if month == 12
      rate    = 0.20
      discount = order.final_price * rate
      order.final_price -= discount
      order.applied_discounts << "Seasonal (December sale): -$#{'%.2f' % discount}"
      puts "[SeasonalDiscount] December sale! Applied 20% off: -$#{'%.2f' % discount}"
    else
      puts "[SeasonalDiscount] No seasonal promotion this month (month=#{month})."
    end
    pass_to_next(order)
  end
end

# Validates and applies a coupon code.
class CouponDiscountHandler < DiscountHandler
  VALID_COUPONS = {
    "SAVE10"    => 0.10,
    "NEWUSER20" => 0.20,
    "FLASH5"    => 0.05
  }.freeze

  def handle(order)
    code = order.coupon_code&.upcase
    rate = VALID_COUPONS[code]

    if rate
      discount = order.final_price * rate
      order.final_price -= discount
      order.applied_discounts << "Coupon '#{code}': -$#{'%.2f' % discount}"
      puts "[CouponDiscount] Valid coupon '#{code}' — applied #{(rate * 100).to_i}%: -$#{'%.2f' % discount}"
    elsif code
      puts "[CouponDiscount] Invalid coupon code: '#{code}' — skipping."
    else
      puts "[CouponDiscount] No coupon provided."
    end

    pass_to_next(order)
  end
end

# Applies a bulk discount for large orders.
class BulkDiscountHandler < DiscountHandler
  THRESHOLDS = [
    { min_items: 20, rate: 0.15, label: "Bulk 15%" },
    { min_items: 10, rate: 0.08, label: "Bulk 8%"  },
    { min_items:  5, rate: 0.03, label: "Bulk 3%"  },
  ].freeze

  def handle(order)
    total_qty = order.items.sum { |i| i[:qty] }
    threshold = THRESHOLDS.find { |t| total_qty >= t[:min_items] }

    if threshold
      discount = order.final_price * threshold[:rate]
      order.final_price -= discount
      order.applied_discounts << "#{threshold[:label]} (#{total_qty} items): -$#{'%.2f' % discount}"
      puts "[BulkDiscount] #{total_qty} items — #{threshold[:label]}: -$#{'%.2f' % discount}"
    else
      puts "[BulkDiscount] Order has #{total_qty} item(s) — no bulk discount."
    end

    pass_to_next(order)
  end
end

# Terminal handler: prints the final price summary.
class PriceCalculator < DiscountHandler
  def handle(order)
    puts "[PriceCalculator] Finalising order #{order.id}..."
    DiscountResult.new(
      order: order,
      message: "Order #{order.id} finalised at $#{'%.2f' % order.final_price}."
    )
  end
end

# ── Chain builder ─────────────────────────────────────────────────────────────

def build_discount_pipeline
  loyalty   = LoyaltyDiscountHandler.new
  seasonal  = SeasonalDiscountHandler.new
  coupon    = CouponDiscountHandler.new
  bulk      = BulkDiscountHandler.new
  calculator = PriceCalculator.new

  loyalty.set_next(seasonal).set_next(coupon).set_next(bulk).set_next(calculator)
  loyalty
end

# ── Client ─────────────────────────────────────────────────────────────────────

def process_order(pipeline, order)
  order.final_price = order.subtotal
  order.applied_discounts = []

  puts "\n#{'=' * 60}"
  puts "Order #{order.id} | Customer tier: #{order.customer_tier} | Subtotal: $#{'%.2f' % order.subtotal}"
  puts "Coupon: #{order.coupon_code || 'none'}"
  puts '-' * 60

  result = pipeline.handle(order)

  puts "\n--- Summary ---"
  order.applied_discounts.each { |d| puts "  #{d}" }
  puts "  Final price: $#{'%.2f' % order.final_price}"
  puts result.message
end

pipeline = build_discount_pipeline

orders = [
  Order.new(
    id: "ORD-001",
    customer_tier: :gold,
    items: [
      { name: "Widget A", qty: 3, unit_price: 29.99 },
      { name: "Widget B", qty: 2, unit_price: 49.99 }
    ],
    coupon_code: "SAVE10"
  ),
  Order.new(
    id: "ORD-002",
    customer_tier: :bronze,
    items: [
      { name: "Gadget X", qty: 15, unit_price: 9.99 }
    ],
    coupon_code: nil
  ),
  Order.new(
    id: "ORD-003",
    customer_tier: :platinum,
    items: [
      { name: "Premium Package", qty: 1, unit_price: 199.00 }
    ],
    coupon_code: "NEWUSER20"
  ),
]

orders.each { |order| process_order(pipeline, order) }
```

---

## When To Use

Use Chain of Responsibility when:

- **The request type or handling sequence is unknown at compile time.** The chain can be configured at runtime, making it ideal for plugin-based architectures and middleware systems.
- **Several objects must have a chance to handle the same request.** You do not want to hard-code which object handles which request.
- **You need a specific execution order** for a set of handlers, and that order may change depending on configuration or environment.
- **You want to decouple the sender from the receiver.** The sender sends a request to the head of the chain, knowing nothing about how it will be processed.
- **The set of handlers should be composable and changeable at runtime.** Adding, removing, or reordering checks should require no changes to existing handler code.

Typical application areas:
- HTTP middleware pipelines (authentication, rate limiting, CORS, compression)
- Event-processing systems (DOM event bubbling follows this pattern)
- Logging frameworks (log level filtering across appenders)
- Purchase or document approval workflows
- Input validation and sanitisation pipelines
- Technical support escalation

---

## Pros & Cons

### Pros

| Benefit | Explanation |
|---|---|
| **Controlled ordering** | You explicitly define the sequence in which handlers execute. |
| **Single Responsibility Principle** | Each handler does exactly one thing, making classes small and focused. |
| **Open/Closed Principle** | New handlers can be inserted into the chain without modifying existing handlers or the client. |
| **Loose coupling** | The sender does not know which handler will process the request, and handlers do not know about each other beyond the `next` reference. |
| **Flexible chain composition** | Chains can be assembled differently for different contexts (e.g., a public API vs. an internal API) or altered at runtime. |

### Cons

| Drawback | Explanation |
|---|---|
| **Requests may go unhandled** | If no handler in the chain can process the request and there is no default fallback, the request is silently dropped. You must design the terminal condition carefully. |
| **Debugging difficulty** | Tracing which handler processed (or swallowed) a request requires good logging; otherwise the dynamic nature of the chain makes debugging opaque. |
| **Performance overhead** | Every request traverses the chain from the beginning, even if the matching handler is near the end. For high-throughput systems, measure the overhead. |
| **Ordering errors** | Incorrectly ordered handlers can introduce subtle bugs (e.g., authorising before authenticating). |

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Composite** | Chain of Responsibility is often used with Composite. When the handler is a leaf node in a composite tree, the request flows from child to parent, which is a natural chain. |
| **Command** | Command encapsulates a request as an object. Chain of Responsibility can be used to route Command objects through a sequence of processors. |
| **Decorator** | Decorator and Chain of Responsibility have similar structures — both rely on recursive composition. The key difference: Decorator always executes both the wrapper and the wrapped object; a CoR handler may short-circuit and *not* pass the request onward. |
| **Observer** | Observer notifies all registered listeners; Chain of Responsibility passes the request until *one* handler claims it (though some variants notify all). |

---

## Sources

- https://refactoring.guru/design-patterns/chain-of-responsibility
- https://sourcemaking.com/design_patterns/chain_of_responsibility
