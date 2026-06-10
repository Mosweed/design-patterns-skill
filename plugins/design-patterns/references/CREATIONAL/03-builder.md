# Builder Pattern

**Category:** Creational  
**Complexity:** ★★☆  
**Popularity:** ★★★

---

## Intent

Lets you construct complex objects step by step. The pattern allows you to produce different types and representations of an object using the same construction code, without exposing the internal details of how the object is assembled.

---

## Problem It Solves

Imagine you need to build a complex object like an HTTP request, a SQL query, a house, or a meal order. These objects can require dozens of configuration options — some mandatory, some optional, many interdependent.

**The telescoping constructor anti-pattern** emerges when you try to handle this with constructor overloading:

```
House(walls, roof)
House(walls, roof, windows)
House(walls, roof, windows, doors)
House(walls, roof, windows, doors, garage)
House(walls, roof, windows, doors, garage, pool)
```

This becomes unmanageable quickly. Callers must remember which positional argument means what, and you end up passing `null` for fields you do not need. Subclassing for each variant creates an explosion of classes.

**Secondary problems the Builder pattern addresses:**

- You want to create different representations of the same product (e.g., a wooden house vs. a glass house) using the same step-by-step process.
- Object construction involves multiple validation steps or side effects that must occur in a specific order.
- You need to reuse the same construction logic to build entirely different outputs (e.g., building a PDF report and an HTML report from the same data pipeline).

---

## Solution

Extract the object construction code out of its own class and move it to separate objects called **builders**. Organize the construction into a discrete set of steps (`buildWalls()`, `buildRoof()`, `addWindows()`, etc.).

To produce a product, you call only the steps you need. Crucially, you do not have to call all steps — only the ones relevant to your configuration.

A **Director** class is an optional layer that encapsulates common, reusable sequences of builder steps. The Director defines *what* to build (the recipe); the Builder defines *how* to build each piece. The client can use the Director's predefined recipes or drive the Builder manually for custom configurations.

---

## Structure (ASCII diagram)

```
  ┌─────────────┐         uses          ┌──────────────────┐
  │   Director  │ ─────────────────────▶│  Builder         │
  │─────────────│                       │  <<interface>>   │
  │ construct() │                       │──────────────────│
  └─────────────┘                       │ + reset()        │
         │                              │ + buildStepA()   │
         │                              │ + buildStepB()   │
         │                              │ + buildStepN()   │
         │                              └──────────────────┘
         │                                      △
         │                           ┌──────────┴──────────┐
         │                           │                     │
         │                 ┌──────────────────┐  ┌──────────────────┐
         │                 │ConcreteBuilder1  │  │ConcreteBuilder2  │
         │                 │──────────────────│  │──────────────────│
         │                 │ + buildStepA()   │  │ + buildStepA()   │
         │                 │ + buildStepB()   │  │ + buildStepB()   │
         │                 │ + buildStepN()   │  │ + buildStepN()   │
         │                 │ + getResult()    │  │ + getResult()    │
         │                 └──────────────────┘  └──────────────────┘
         │                          │                     │
         │                          ▼                     ▼
         │                 ┌──────────────────┐  ┌──────────────────┐
         └────────────────▶│    Product1      │  │    Product2      │
                           └──────────────────┘  └──────────────────┘

  Flow:
  Client ──creates──▶ ConcreteBuilder
  Client ──creates──▶ Director(builder)
  Client ──calls───▶ Director.construct()
                         │
                         ├──▶ builder.buildStepA()
                         ├──▶ builder.buildStepB()
                         └──▶ builder.buildStepN()
  Client ──calls───▶ builder.getResult() ──▶ Product
```

---

## Participants

| Participant | Role |
|---|---|
| **Builder** | Declares the construction steps that are common to all types of builders (interface or abstract class). |
| **ConcreteBuilder** | Provides specific implementations of the construction steps. May produce products that do not follow a common interface. Tracks the product being built and provides a method to retrieve it. |
| **Director** | Defines the order in which to call construction steps. Creates and reuses specific configurations of products. The Director is optional — the client can call builder steps directly. |
| **Product** | The resulting complex object. Products built by different concrete builders do not have to belong to the same class hierarchy. |

---

## How It Works (step-by-step)

1. **Define the Builder interface** with a method for each construction step that all representations of the product have in common.
2. **Create one or more ConcreteBuilder classes** that implement the Builder interface. Each ConcreteBuilder produces a different flavour of the product and tracks the assembly state internally.
3. **Define Product classes.** Products built by different builders need not share a common base class or interface — they can be entirely different types.
4. **(Optional) Create a Director class.** The Director encapsulates recipes — sequences of builder steps — for the most common product configurations. It takes a builder via its constructor or a setter so you can swap builders at runtime.
5. **In client code:**
   a. Create a ConcreteBuilder instance.
   b. Optionally create a Director and pass it the builder.
   c. Call `director.construct()` (or invoke builder steps manually).
   d. Retrieve the finished product from the builder via `getResult()` (or equivalent).
   e. To build a different variant, repeat with a different ConcreteBuilder.

---

## Code Examples

### Python

```python
"""
Builder Pattern — Python Example
Real-world use case: Building complex SQL SELECT queries programmatically.

A QueryBuilder allows clients to compose SELECT statements with optional
WHERE clauses, JOINs, ORDER BY, and LIMIT without string concatenation errors.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

@dataclass
class SqlQuery:
    """Represents a fully assembled SQL SELECT statement."""
    table: str
    columns: list[str] = field(default_factory=list)
    joins: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    order_by: Optional[str] = None
    limit: Optional[int] = None

    def to_sql(self) -> str:
        cols = ", ".join(self.columns) if self.columns else "*"
        sql = f"SELECT {cols} FROM {self.table}"

        for join in self.joins:
            sql += f"\n  {join}"

        if self.conditions:
            sql += "\nWHERE " + "\n  AND ".join(self.conditions)

        if self.order_by:
            sql += f"\nORDER BY {self.order_by}"

        if self.limit is not None:
            sql += f"\nLIMIT {self.limit}"

        return sql

    def __str__(self) -> str:
        return self.to_sql()


# ---------------------------------------------------------------------------
# Builder interface
# ---------------------------------------------------------------------------

class QueryBuilderInterface:
    """Declares all construction steps for a SQL query."""

    def reset(self, table: str) -> QueryBuilderInterface:
        raise NotImplementedError

    def select(self, *columns: str) -> QueryBuilderInterface:
        raise NotImplementedError

    def join(self, join_clause: str) -> QueryBuilderInterface:
        raise NotImplementedError

    def where(self, condition: str) -> QueryBuilderInterface:
        raise NotImplementedError

    def order_by(self, column: str, direction: str = "ASC") -> QueryBuilderInterface:
        raise NotImplementedError

    def limit(self, n: int) -> QueryBuilderInterface:
        raise NotImplementedError

    def build(self) -> SqlQuery:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Concrete Builder
# ---------------------------------------------------------------------------

class SelectQueryBuilder(QueryBuilderInterface):
    """Concrete builder that assembles a SqlQuery object step by step."""

    def __init__(self, table: str) -> None:
        self._query = SqlQuery(table=table)

    def reset(self, table: str) -> SelectQueryBuilder:
        self._query = SqlQuery(table=table)
        return self

    def select(self, *columns: str) -> SelectQueryBuilder:
        self._query.columns.extend(columns)
        return self  # fluent interface — enables method chaining

    def join(self, join_clause: str) -> SelectQueryBuilder:
        self._query.joins.append(join_clause)
        return self

    def where(self, condition: str) -> SelectQueryBuilder:
        self._query.conditions.append(condition)
        return self

    def order_by(self, column: str, direction: str = "ASC") -> SelectQueryBuilder:
        self._query.order_by = f"{column} {direction}"
        return self

    def limit(self, n: int) -> SelectQueryBuilder:
        self._query.limit = n
        return self

    def build(self) -> SqlQuery:
        """Return the finished query and reset internal state."""
        result = self._query
        self._query = SqlQuery(table=result.table)
        return result


# ---------------------------------------------------------------------------
# Director
# ---------------------------------------------------------------------------

class ReportDirector:
    """
    Encapsulates common query recipes used across the reporting module.
    The Director defines WHAT to build; the builder defines HOW.
    """

    def __init__(self, builder: QueryBuilderInterface) -> None:
        self._builder = builder

    def set_builder(self, builder: QueryBuilderInterface) -> None:
        self._builder = builder

    def build_top_customers_report(self) -> SqlQuery:
        """Recipe: top 10 customers by total order value."""
        return (
            self._builder
            .reset("customers")
            .select("customers.id", "customers.name", "SUM(orders.total) AS total_spent")
            .join("JOIN orders ON orders.customer_id = customers.id")
            .where("orders.status = 'completed'")
            .where("orders.created_at >= '2025-01-01'")
            .order_by("total_spent", "DESC")
            .limit(10)
            .build()
        )

    def build_inactive_users_report(self) -> SqlQuery:
        """Recipe: users who have not logged in for 90+ days."""
        return (
            self._builder
            .reset("users")
            .select("id", "email", "last_login_at")
            .where("last_login_at < NOW() - INTERVAL 90 DAY")
            .where("is_deleted = 0")
            .order_by("last_login_at", "ASC")
            .build()
        )


# ---------------------------------------------------------------------------
# Client code
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    builder = SelectQueryBuilder("customers")
    director = ReportDirector(builder)

    # Use a predefined Director recipe
    top_customers = director.build_top_customers_report()
    print("=== Top Customers Report ===")
    print(top_customers)
    print()

    inactive_users = director.build_inactive_users_report()
    print("=== Inactive Users Report ===")
    print(inactive_users)
    print()

    # Build a fully custom query without the Director
    custom_query = (
        SelectQueryBuilder("products")
        .select("id", "name", "price", "stock_count")
        .join("LEFT JOIN categories ON categories.id = products.category_id")
        .where("price BETWEEN 10.00 AND 50.00")
        .where("stock_count > 0")
        .order_by("price", "ASC")
        .limit(25)
        .build()
    )
    print("=== Custom Product Query ===")
    print(custom_query)
```

---

### Java

```java
/**
 * Builder Pattern — Java Example
 * Real-world use case: Building immutable HTTP Request objects.
 *
 * Demonstrates:
 *  - A fluent builder for a complex, immutable value object
 *  - A Director that encapsulates common API call recipes
 *  - Validation inside the builder's build() method
 */

import java.util.*;

// ---------------------------------------------------------------------------
// Product — immutable HTTP Request
// ---------------------------------------------------------------------------

public final class HttpRequest {

    public enum Method { GET, POST, PUT, PATCH, DELETE }

    private final Method method;
    private final String url;
    private final Map<String, String> headers;
    private final Map<String, String> queryParams;
    private final String body;
    private final int timeoutMs;
    private final boolean followRedirects;

    // Private constructor — only the Builder can instantiate this
    private HttpRequest(Builder builder) {
        this.method          = builder.method;
        this.url             = builder.url;
        this.headers         = Collections.unmodifiableMap(new LinkedHashMap<>(builder.headers));
        this.queryParams     = Collections.unmodifiableMap(new LinkedHashMap<>(builder.queryParams));
        this.body            = builder.body;
        this.timeoutMs       = builder.timeoutMs;
        this.followRedirects = builder.followRedirects;
    }

    // Getters
    public Method getMethod()           { return method; }
    public String getUrl()              { return url; }
    public Map<String, String> getHeaders()    { return headers; }
    public Map<String, String> getQueryParams(){ return queryParams; }
    public String getBody()             { return body; }
    public int getTimeoutMs()           { return timeoutMs; }
    public boolean isFollowRedirects()  { return followRedirects; }

    /** Reconstruct the full URL with query string appended. */
    public String toFullUrl() {
        if (queryParams.isEmpty()) return url;
        StringBuilder sb = new StringBuilder(url).append('?');
        queryParams.forEach((k, v) ->
            sb.append(urlEncode(k)).append('=').append(urlEncode(v)).append('&'));
        sb.setLength(sb.length() - 1); // trim trailing &
        return sb.toString();
    }

    private static String urlEncode(String s) {
        // Simplified — in production use URLEncoder.encode(s, StandardCharsets.UTF_8)
        return s.replace(" ", "%20");
    }

    @Override
    public String toString() {
        return String.format(
            "%s %s\nHeaders: %s\nBody: %s\nTimeout: %dms | Redirects: %b",
            method, toFullUrl(), headers, body == null ? "<none>" : body,
            timeoutMs, followRedirects
        );
    }

    // -----------------------------------------------------------------------
    // Concrete Builder (static inner class — Java idiom)
    // -----------------------------------------------------------------------

    public static final class Builder {

        // Required
        private final Method method;
        private final String url;

        // Optional with defaults
        private final Map<String, String> headers     = new LinkedHashMap<>();
        private final Map<String, String> queryParams = new LinkedHashMap<>();
        private String  body             = null;
        private int     timeoutMs        = 5_000;
        private boolean followRedirects  = true;

        public Builder(Method method, String url) {
            if (method == null) throw new IllegalArgumentException("Method is required");
            if (url == null || url.isBlank()) throw new IllegalArgumentException("URL is required");
            this.method = method;
            this.url    = url;
        }

        public Builder header(String name, String value) {
            this.headers.put(name, value);
            return this;
        }

        public Builder bearerToken(String token) {
            return header("Authorization", "Bearer " + token);
        }

        public Builder contentTypeJson() {
            return header("Content-Type", "application/json")
                   .header("Accept", "application/json");
        }

        public Builder queryParam(String name, String value) {
            this.queryParams.put(name, value);
            return this;
        }

        public Builder body(String body) {
            this.body = body;
            return this;
        }

        public Builder timeoutMs(int ms) {
            if (ms <= 0) throw new IllegalArgumentException("Timeout must be positive");
            this.timeoutMs = ms;
            return this;
        }

        public Builder followRedirects(boolean follow) {
            this.followRedirects = follow;
            return this;
        }

        /** Validates constraints and constructs the immutable HttpRequest. */
        public HttpRequest build() {
            // Validation: POST/PUT/PATCH should typically have a body
            if ((method == Method.POST || method == Method.PUT || method == Method.PATCH)
                    && (body == null || body.isBlank())) {
                System.err.println("[WARN] " + method + " request built without a body.");
            }
            return new HttpRequest(this);
        }
    }
}

// ---------------------------------------------------------------------------
// Director — common API call recipes
// ---------------------------------------------------------------------------

class ApiRequestDirector {

    private static final String BASE_URL   = "https://api.example.com/v1";
    private static final String AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9";

    /** Recipe: standard authenticated GET request with JSON accept header. */
    public HttpRequest buildGetRequest(String path, Map<String, String> params) {
        HttpRequest.Builder builder = new HttpRequest.Builder(HttpRequest.Method.GET, BASE_URL + path)
                .bearerToken(AUTH_TOKEN)
                .contentTypeJson()
                .timeoutMs(10_000);

        params.forEach(builder::queryParam);
        return builder.build();
    }

    /** Recipe: standard authenticated POST with JSON body. */
    public HttpRequest buildPostRequest(String path, String jsonBody) {
        return new HttpRequest.Builder(HttpRequest.Method.POST, BASE_URL + path)
                .bearerToken(AUTH_TOKEN)
                .contentTypeJson()
                .body(jsonBody)
                .timeoutMs(15_000)
                .build();
    }

    /** Recipe: webhook delivery — no auth, short timeout, no redirects. */
    public HttpRequest buildWebhookRequest(String webhookUrl, String payload) {
        return new HttpRequest.Builder(HttpRequest.Method.POST, webhookUrl)
                .header("Content-Type", "application/json")
                .header("X-Webhook-Source", "my-service")
                .body(payload)
                .timeoutMs(3_000)
                .followRedirects(false)
                .build();
    }
}

// ---------------------------------------------------------------------------
// Client code — main
// ---------------------------------------------------------------------------

class BuilderPatternDemo {

    public static void main(String[] args) {
        ApiRequestDirector director = new ApiRequestDirector();

        // Director-built GET
        Map<String, String> params = new LinkedHashMap<>();
        params.put("page", "1");
        params.put("per_page", "20");
        params.put("status", "active");
        HttpRequest getRequest = director.buildGetRequest("/users", params);
        System.out.println("=== Paginated Users GET ===");
        System.out.println(getRequest);
        System.out.println();

        // Director-built POST
        String userJson = "{\"name\":\"Alice\",\"email\":\"alice@example.com\",\"role\":\"admin\"}";
        HttpRequest postRequest = director.buildPostRequest("/users", userJson);
        System.out.println("=== Create User POST ===");
        System.out.println(postRequest);
        System.out.println();

        // Fully custom DELETE — no Director needed
        HttpRequest deleteRequest = new HttpRequest.Builder(
                HttpRequest.Method.DELETE, "https://api.example.com/v1/users/42")
            .bearerToken("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
            .header("X-Idempotency-Key", "delete-user-42-2025")
            .timeoutMs(8_000)
            .build();
        System.out.println("=== Delete User DELETE ===");
        System.out.println(deleteRequest);
    }
}
```

---

### C++

```cpp
/**
 * Builder Pattern — C++ Example
 * Real-world use case: Building Pizza orders in a restaurant system.
 *
 * Demonstrates:
 *  - Abstract Builder with pure virtual methods
 *  - Two ConcreteBuilders producing different product flavours
 *  - A Director encapsulating preset pizza recipes
 *  - Smart-pointer ownership semantics
 */

#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <sstream>
#include <iomanip>

// ---------------------------------------------------------------------------
// Product
// ---------------------------------------------------------------------------

class Pizza {
public:
    std::string  size;          // "small", "medium", "large"
    std::string  crust;         // "thin", "thick", "stuffed"
    std::string  sauce;         // "tomato", "white", "pesto"
    std::string  cheese;        // "mozzarella", "vegan", "none"
    std::vector<std::string> toppings;
    bool         extraCheese  = false;
    bool         wellDone      = false;
    double       price         = 0.0;

    std::string describe() const {
        std::ostringstream oss;
        oss << std::fixed << std::setprecision(2);
        oss << "Pizza [" << size << "]\n"
            << "  Crust   : " << crust << "\n"
            << "  Sauce   : " << sauce << "\n"
            << "  Cheese  : " << cheese
            << (extraCheese ? " (extra)" : "") << "\n"
            << "  Toppings: ";

        if (toppings.empty()) {
            oss << "none";
        } else {
            for (size_t i = 0; i < toppings.size(); ++i) {
                oss << toppings[i];
                if (i + 1 < toppings.size()) oss << ", ";
            }
        }

        oss << "\n"
            << "  Well done: " << (wellDone ? "yes" : "no") << "\n"
            << "  Price   : $" << price << "\n";
        return oss.str();
    }
};

// ---------------------------------------------------------------------------
// Abstract Builder
// ---------------------------------------------------------------------------

class PizzaBuilder {
public:
    virtual ~PizzaBuilder() = default;

    virtual void reset()                          = 0;
    virtual void setSize(const std::string& size) = 0;
    virtual void buildCrust()                     = 0;
    virtual void buildSauce()                     = 0;
    virtual void buildCheese()                    = 0;
    virtual void addToppings()                    = 0;
    virtual void calculatePrice()                 = 0;

    virtual std::unique_ptr<Pizza> getResult()    = 0;
};

// ---------------------------------------------------------------------------
// Concrete Builder 1 — Classic Italian Pizza
// ---------------------------------------------------------------------------

class ItalianPizzaBuilder : public PizzaBuilder {
    std::unique_ptr<Pizza> pizza_;

public:
    ItalianPizzaBuilder() { reset(); }

    void reset() override {
        pizza_ = std::make_unique<Pizza>();
    }

    void setSize(const std::string& size) override {
        pizza_->size = size;
    }

    void buildCrust() override {
        pizza_->crust = "thin";          // authentic Italian: always thin
    }

    void buildSauce() override {
        pizza_->sauce = "tomato";        // San Marzano tomato base
    }

    void buildCheese() override {
        pizza_->cheese = "mozzarella";
    }

    void addToppings() override {
        // Classic Margherita toppings
        pizza_->toppings = {"fresh basil", "olive oil drizzle"};
    }

    void calculatePrice() override {
        double base = 8.0;
        if      (pizza_->size == "medium") base = 12.0;
        else if (pizza_->size == "large")  base = 16.0;
        pizza_->price = base + pizza_->toppings.size() * 0.75;
    }

    std::unique_ptr<Pizza> getResult() override {
        auto result = std::move(pizza_);
        reset();
        return result;
    }
};

// ---------------------------------------------------------------------------
// Concrete Builder 2 — Vegan Pizza
// ---------------------------------------------------------------------------

class VeganPizzaBuilder : public PizzaBuilder {
    std::unique_ptr<Pizza> pizza_;

public:
    VeganPizzaBuilder() { reset(); }

    void reset() override {
        pizza_ = std::make_unique<Pizza>();
    }

    void setSize(const std::string& size) override {
        pizza_->size = size;
    }

    void buildCrust() override {
        pizza_->crust = "thick";         // whole-wheat thick crust
    }

    void buildSauce() override {
        pizza_->sauce = "pesto";         // dairy-free basil pesto
    }

    void buildCheese() override {
        pizza_->cheese = "vegan";        // cashew-based vegan cheese
    }

    void addToppings() override {
        pizza_->toppings = {
            "roasted bell peppers",
            "caramelised onions",
            "sun-dried tomatoes",
            "spinach"
        };
    }

    void calculatePrice() override {
        double base = 10.0;              // vegan ingredients cost more
        if      (pizza_->size == "medium") base = 14.0;
        else if (pizza_->size == "large")  base = 18.0;
        pizza_->price = base + pizza_->toppings.size() * 1.0;
    }

    std::unique_ptr<Pizza> getResult() override {
        auto result = std::move(pizza_);
        reset();
        return result;
    }
};

// ---------------------------------------------------------------------------
// Director — predefined pizza recipes
// ---------------------------------------------------------------------------

class PizzaDirector {
    PizzaBuilder* builder_;

public:
    explicit PizzaDirector(PizzaBuilder* builder) : builder_(builder) {}

    void setBuilder(PizzaBuilder* builder) { builder_ = builder; }

    /** Builds the simplest / smallest variant of a pizza. */
    void buildPersonalPizza() {
        builder_->reset();
        builder_->setSize("small");
        builder_->buildCrust();
        builder_->buildSauce();
        builder_->buildCheese();
        builder_->calculatePrice();
        // No toppings added — minimal build
    }

    /** Builds the full-featured large pizza with all toppings. */
    void buildFamilyPizza() {
        builder_->reset();
        builder_->setSize("large");
        builder_->buildCrust();
        builder_->buildSauce();
        builder_->buildCheese();
        builder_->addToppings();
        builder_->calculatePrice();
    }
};

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

int main() {
    ItalianPizzaBuilder italianBuilder;
    VeganPizzaBuilder   veganBuilder;
    PizzaDirector       director(&italianBuilder);

    // Classic Italian personal pizza
    director.buildPersonalPizza();
    auto personalItalian = italianBuilder.getResult();
    std::cout << "=== Personal Italian Pizza ===\n" << personalItalian->describe() << "\n";

    // Classic Italian family pizza
    director.buildFamilyPizza();
    auto familyItalian = italianBuilder.getResult();
    std::cout << "=== Family Italian Pizza ===\n" << familyItalian->describe() << "\n";

    // Vegan family pizza — swap builder, reuse same Director
    director.setBuilder(&veganBuilder);
    director.buildFamilyPizza();
    auto familyVegan = veganBuilder.getResult();
    std::cout << "=== Family Vegan Pizza ===\n" << familyVegan->describe() << "\n";

    // Custom order without Director — medium vegan, well done
    veganBuilder.reset();
    veganBuilder.setSize("medium");
    veganBuilder.buildCrust();
    veganBuilder.buildSauce();
    veganBuilder.buildCheese();
    veganBuilder.addToppings();
    veganBuilder.calculatePrice();
    auto customVegan = veganBuilder.getResult();
    customVegan->wellDone = true;
    std::cout << "=== Custom Medium Vegan (well done) ===\n" << customVegan->describe() << "\n";

    return 0;
}
```

---

### C#

```csharp
/**
 * Builder Pattern — C# Example
 * Real-world use case: Building email messages for a notification system.
 *
 * Demonstrates:
 *  - Fluent builder with method chaining
 *  - Validation in Build()
 *  - A Director encoding notification templates
 *  - C#-idiomatic immutable record for the product
 */

using System;
using System.Collections.Generic;
using System.Text;

// ---------------------------------------------------------------------------
// Product
// ---------------------------------------------------------------------------

public sealed class EmailMessage
{
    public string   From            { get; }
    public string[] To              { get; }
    public string[] Cc              { get; }
    public string   Subject         { get; }
    public string   HtmlBody        { get; }
    public string   PlainTextBody   { get; }
    public bool     IsHighPriority  { get; }
    public Dictionary<string, string> Headers { get; }

    // Internal constructor — only the Builder can create this
    internal EmailMessage(EmailMessageBuilder b)
    {
        From           = b.From;
        To             = b.To.ToArray();
        Cc             = b.Cc.ToArray();
        Subject        = b.Subject;
        HtmlBody       = b.HtmlBody;
        PlainTextBody  = b.PlainTextBody;
        IsHighPriority = b.IsHighPriority;
        Headers        = new Dictionary<string, string>(b.CustomHeaders);
    }

    public override string ToString()
    {
        var sb = new StringBuilder();
        sb.AppendLine($"From    : {From}");
        sb.AppendLine($"To      : {string.Join(", ", To)}");
        if (Cc.Length > 0)
            sb.AppendLine($"Cc      : {string.Join(", ", Cc)}");
        sb.AppendLine($"Subject : {Subject}");
        sb.AppendLine($"Priority: {(IsHighPriority ? "High" : "Normal")}");
        if (Headers.Count > 0)
        {
            sb.AppendLine("Headers :");
            foreach (var (k, v) in Headers)
                sb.AppendLine($"  {k}: {v}");
        }
        sb.AppendLine($"--- HTML Body ---\n{HtmlBody}");
        return sb.ToString();
    }
}

// ---------------------------------------------------------------------------
// Concrete Builder
// ---------------------------------------------------------------------------

public sealed class EmailMessageBuilder
{
    // Internal state — visible to EmailMessage constructor
    internal string   From           = "noreply@example.com";
    internal List<string> To         = new();
    internal List<string> Cc         = new();
    internal string   Subject        = string.Empty;
    internal string   HtmlBody       = string.Empty;
    internal string   PlainTextBody  = string.Empty;
    internal bool     IsHighPriority = false;
    internal Dictionary<string, string> CustomHeaders = new();

    public EmailMessageBuilder SetFrom(string from)
    {
        From = from ?? throw new ArgumentNullException(nameof(from));
        return this;
    }

    public EmailMessageBuilder AddTo(params string[] addresses)
    {
        To.AddRange(addresses);
        return this;
    }

    public EmailMessageBuilder AddCc(params string[] addresses)
    {
        Cc.AddRange(addresses);
        return this;
    }

    public EmailMessageBuilder SetSubject(string subject)
    {
        Subject = subject ?? throw new ArgumentNullException(nameof(subject));
        return this;
    }

    public EmailMessageBuilder SetHtmlBody(string html)
    {
        HtmlBody = html;
        return this;
    }

    public EmailMessageBuilder SetPlainTextBody(string text)
    {
        PlainTextBody = text;
        return this;
    }

    public EmailMessageBuilder MarkHighPriority()
    {
        IsHighPriority = true;
        return this;
    }

    public EmailMessageBuilder AddHeader(string name, string value)
    {
        CustomHeaders[name] = value;
        return this;
    }

    public EmailMessage Build()
    {
        // Validate required fields
        if (To.Count == 0)
            throw new InvalidOperationException("At least one recipient (To) is required.");

        if (string.IsNullOrWhiteSpace(Subject))
            throw new InvalidOperationException("Subject cannot be empty.");

        if (string.IsNullOrWhiteSpace(HtmlBody) && string.IsNullOrWhiteSpace(PlainTextBody))
            throw new InvalidOperationException("At least one body (HTML or plain text) must be set.");

        return new EmailMessage(this);
    }

    public void Reset()
    {
        From           = "noreply@example.com";
        To             = new List<string>();
        Cc             = new List<string>();
        Subject        = string.Empty;
        HtmlBody       = string.Empty;
        PlainTextBody  = string.Empty;
        IsHighPriority = false;
        CustomHeaders  = new Dictionary<string, string>();
    }
}

// ---------------------------------------------------------------------------
// Director — notification templates
// ---------------------------------------------------------------------------

public sealed class NotificationDirector
{
    private readonly EmailMessageBuilder _builder;
    private const string SupportEmail = "support@example.com";

    public NotificationDirector(EmailMessageBuilder builder) => _builder = builder;

    /// <summary>Builds a standard welcome email for a new user.</summary>
    public EmailMessage BuildWelcomeEmail(string userEmail, string userName)
    {
        _builder.Reset();
        return _builder
            .SetFrom(SupportEmail)
            .AddTo(userEmail)
            .SetSubject("Welcome to Example — get started today!")
            .SetHtmlBody($@"
                <h1>Hi {userName},</h1>
                <p>Your account is ready. <a href='https://example.com/dashboard'>Go to your dashboard</a>.</p>
                <p>The Example Team</p>")
            .SetPlainTextBody($"Hi {userName},\n\nYour account is ready.\nhttps://example.com/dashboard\n\nThe Example Team")
            .Build();
    }

    /// <summary>Builds an urgent security alert.</summary>
    public EmailMessage BuildSecurityAlert(string userEmail, string ipAddress)
    {
        _builder.Reset();
        return _builder
            .SetFrom(SupportEmail)
            .AddTo(userEmail)
            .AddCc("security-log@example.com")
            .SetSubject("[URGENT] New sign-in from unrecognised device")
            .SetHtmlBody($@"
                <h2 style='color:red'>Security Alert</h2>
                <p>We detected a new sign-in from IP <strong>{ipAddress}</strong>.</p>
                <p>If this was not you, <a href='https://example.com/account/lock'>lock your account immediately</a>.</p>")
            .MarkHighPriority()
            .AddHeader("X-Security-Alert", "true")
            .Build();
    }

    /// <summary>Builds a plain-text password reset email.</summary>
    public EmailMessage BuildPasswordReset(string userEmail, string resetLink)
    {
        _builder.Reset();
        return _builder
            .SetFrom(SupportEmail)
            .AddTo(userEmail)
            .SetSubject("Reset your Example password")
            .SetPlainTextBody(
                $"Click the link below to reset your password (expires in 1 hour):\n\n{resetLink}\n\n"
              + "If you did not request a reset, ignore this email.")
            .SetHtmlBody($"<p>Click <a href='{resetLink}'>here</a> to reset your password (expires in 1 hour).</p>")
            .Build();
    }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

class Program
{
    static void Main()
    {
        var builder  = new EmailMessageBuilder();
        var director = new NotificationDirector(builder);

        var welcome = director.BuildWelcomeEmail("alice@example.com", "Alice");
        Console.WriteLine("=== Welcome Email ===");
        Console.WriteLine(welcome);

        var alert = director.BuildSecurityAlert("alice@example.com", "203.0.113.42");
        Console.WriteLine("=== Security Alert ===");
        Console.WriteLine(alert);

        // Custom transactional email without the Director
        var invoice = new EmailMessageBuilder()
            .SetFrom("billing@example.com")
            .AddTo("alice@example.com")
            .SetSubject("Invoice #INV-2025-00421 — $149.00 due")
            .SetHtmlBody("<p>Your invoice is attached.</p>")
            .SetPlainTextBody("Your invoice #INV-2025-00421 for $149.00 is due on 2025-08-01.")
            .AddHeader("X-Invoice-Id", "INV-2025-00421")
            .Build();

        Console.WriteLine("=== Invoice Email ===");
        Console.WriteLine(invoice);
    }
}
```

---

### TypeScript

```typescript
/**
 * Builder Pattern — TypeScript Example
 * Real-world use case: Building configuration objects for a data pipeline.
 *
 * A PipelineBuilder constructs ETL (Extract–Transform–Load) pipeline configs
 * with sources, transformations, destinations, and retry policies.
 */

// ---------------------------------------------------------------------------
// Supporting types
// ---------------------------------------------------------------------------

type DataFormat = "csv" | "json" | "parquet" | "ndjson";

interface DataSource {
  type: "s3" | "postgres" | "http" | "local";
  uri: string;
  format: DataFormat;
  credentials?: Record<string, string>;
}

interface Transformation {
  name: string;
  type: "filter" | "map" | "aggregate" | "join" | "deduplicate";
  config: Record<string, unknown>;
}

interface DataDestination {
  type: "s3" | "bigquery" | "postgres" | "webhook";
  uri: string;
  format: DataFormat;
  writeMode: "overwrite" | "append" | "upsert";
  credentials?: Record<string, string>;
}

interface RetryPolicy {
  maxAttempts: number;
  backoffMs: number;
  backoffMultiplier: number;
}

// ---------------------------------------------------------------------------
// Product — immutable pipeline configuration
// ---------------------------------------------------------------------------

interface PipelineConfig {
  readonly name: string;
  readonly description: string;
  readonly sources: ReadonlyArray<DataSource>;
  readonly transformations: ReadonlyArray<Transformation>;
  readonly destination: DataDestination;
  readonly schedule: string | null;          // cron expression or null
  readonly retryPolicy: RetryPolicy;
  readonly notifyOnFailure: string[];
  readonly tags: Record<string, string>;
}

// ---------------------------------------------------------------------------
// Concrete Builder
// ---------------------------------------------------------------------------

class PipelineBuilder {
  private name = "";
  private description = "";
  private sources: DataSource[] = [];
  private transformations: Transformation[] = [];
  private destination: DataDestination | null = null;
  private schedule: string | null = null;
  private retryPolicy: RetryPolicy = {
    maxAttempts: 3,
    backoffMs: 1_000,
    backoffMultiplier: 2,
  };
  private notifyOnFailure: string[] = [];
  private tags: Record<string, string> = {};

  setName(name: string): this {
    this.name = name;
    return this;
  }

  setDescription(description: string): this {
    this.description = description;
    return this;
  }

  addSource(source: DataSource): this {
    this.sources.push(source);
    return this;
  }

  addTransformation(transformation: Transformation): this {
    this.transformations.push(transformation);
    return this;
  }

  setDestination(destination: DataDestination): this {
    this.destination = destination;
    return this;
  }

  setSchedule(cron: string): this {
    // Basic cron validation (5 fields)
    if (cron.trim().split(/\s+/).length !== 5) {
      throw new Error(`Invalid cron expression: "${cron}"`);
    }
    this.schedule = cron;
    return this;
  }

  setRetryPolicy(policy: Partial<RetryPolicy>): this {
    this.retryPolicy = { ...this.retryPolicy, ...policy };
    return this;
  }

  addFailureNotification(email: string): this {
    this.notifyOnFailure.push(email);
    return this;
  }

  addTag(key: string, value: string): this {
    this.tags[key] = value;
    return this;
  }

  reset(): this {
    this.name = "";
    this.description = "";
    this.sources = [];
    this.transformations = [];
    this.destination = null;
    this.schedule = null;
    this.retryPolicy = { maxAttempts: 3, backoffMs: 1_000, backoffMultiplier: 2 };
    this.notifyOnFailure = [];
    this.tags = {};
    return this;
  }

  build(): PipelineConfig {
    if (!this.name.trim()) throw new Error("Pipeline name is required.");
    if (this.sources.length === 0) throw new Error("At least one source is required.");
    if (!this.destination) throw new Error("A destination must be set.");

    return Object.freeze({
      name: this.name,
      description: this.description,
      sources: Object.freeze([...this.sources]),
      transformations: Object.freeze([...this.transformations]),
      destination: { ...this.destination },
      schedule: this.schedule,
      retryPolicy: { ...this.retryPolicy },
      notifyOnFailure: [...this.notifyOnFailure],
      tags: { ...this.tags },
    });
  }
}

// ---------------------------------------------------------------------------
// Director — common pipeline recipes
// ---------------------------------------------------------------------------

class DataOpsDirector {
  constructor(private builder: PipelineBuilder) {}

  setBuilder(builder: PipelineBuilder): void {
    this.builder = builder;
  }

  /** Daily user-activity ingestion from S3 into BigQuery. */
  buildDailyIngestionPipeline(): PipelineConfig {
    return this.builder
      .reset()
      .setName("daily-user-activity-ingestion")
      .setDescription("Ingests raw user activity logs from S3 and loads them into BigQuery.")
      .addSource({
        type: "s3",
        uri: "s3://raw-data/user-activity/",
        format: "ndjson",
        credentials: { role: "arn:aws:iam::123456789:role/data-pipeline" },
      })
      .addTransformation({
        name: "remove-bot-events",
        type: "filter",
        config: { condition: "event.user_agent NOT LIKE '%bot%'" },
      })
      .addTransformation({
        name: "enrich-with-geo",
        type: "map",
        config: { lookup: "ip-to-country", inputField: "ip_address", outputField: "country" },
      })
      .setDestination({
        type: "bigquery",
        uri: "project.dataset.user_activity",
        format: "parquet",
        writeMode: "append",
      })
      .setSchedule("0 2 * * *")  // 02:00 UTC daily
      .setRetryPolicy({ maxAttempts: 5, backoffMs: 5_000 })
      .addFailureNotification("data-ops@example.com")
      .addTag("team", "data-engineering")
      .addTag("env", "production")
      .build();
  }

  /** One-off full-table sync from Postgres to S3 (no schedule). */
  buildFullRefreshPipeline(table: string): PipelineConfig {
    return this.builder
      .reset()
      .setName(`full-refresh-${table}`)
      .setDescription(`Full table export of ${table} from Postgres to S3 as Parquet.`)
      .addSource({
        type: "postgres",
        uri: `postgresql://db.prod.internal:5432/app?table=${table}`,
        format: "csv",
        credentials: { secret: "prod/db/readonly" },
      })
      .addTransformation({
        name: "deduplicate-primary-key",
        type: "deduplicate",
        config: { key: "id" },
      })
      .setDestination({
        type: "s3",
        uri: `s3://exports/${table}/`,
        format: "parquet",
        writeMode: "overwrite",
      })
      .addTag("team", "data-engineering")
      .build();
  }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

const builder  = new PipelineBuilder();
const director = new DataOpsDirector(builder);

const dailyPipeline = director.buildDailyIngestionPipeline();
console.log("=== Daily Ingestion Pipeline ===");
console.log(JSON.stringify(dailyPipeline, null, 2));

const refreshPipeline = director.buildFullRefreshPipeline("orders");
console.log("\n=== Full Refresh Pipeline (orders) ===");
console.log(JSON.stringify(refreshPipeline, null, 2));

// Custom pipeline — no Director
const customPipeline = new PipelineBuilder()
  .setName("real-time-webhook-forwarder")
  .setDescription("Forwards filtered events to an external webhook in near-real-time.")
  .addSource({ type: "http", uri: "https://events.internal/stream", format: "ndjson" })
  .addTransformation({
    name: "filter-purchase-events",
    type: "filter",
    config: { condition: "event.type === 'purchase'" },
  })
  .setDestination({
    type: "webhook",
    uri: "https://partner.example.com/ingest",
    format: "json",
    writeMode: "append",
  })
  .setRetryPolicy({ maxAttempts: 10, backoffMs: 500, backoffMultiplier: 1.5 })
  .addFailureNotification("integrations@example.com")
  .build();

console.log("\n=== Custom Webhook Forwarder Pipeline ===");
console.log(JSON.stringify(customPipeline, null, 2));
```

---

### Go

```go
// Builder Pattern — Go Example
// Real-world use case: Building database connection pool configurations.
//
// Go does not have classical inheritance; the pattern is implemented via
// interfaces and structs with method chaining (returning *Builder for fluency).

package main

import (
	"errors"
	"fmt"
	"strings"
	"time"
)

// ---------------------------------------------------------------------------
// Product
// ---------------------------------------------------------------------------

// DBPoolConfig holds the immutable configuration for a database connection pool.
type DBPoolConfig struct {
	Driver          string
	Host            string
	Port            int
	Database        string
	Username        string
	Password        string
	SSLMode         string
	MinConnections  int
	MaxConnections  int
	MaxIdleTime     time.Duration
	ConnectTimeout  time.Duration
	QueryTimeout    time.Duration
	ReadReplicas    []string
	ApplicationName string
	Tags            map[string]string
}

// DSN assembles a PostgreSQL-style data source name.
func (c *DBPoolConfig) DSN() string {
	return fmt.Sprintf(
		"%s://%s:%s@%s:%d/%s?sslmode=%s&application_name=%s",
		c.Driver, c.Username, "****", c.Host, c.Port,
		c.Database, c.SSLMode, c.ApplicationName,
	)
}

func (c *DBPoolConfig) String() string {
	var sb strings.Builder
	sb.WriteString(fmt.Sprintf("Driver      : %s\n", c.Driver))
	sb.WriteString(fmt.Sprintf("DSN         : %s\n", c.DSN()))
	sb.WriteString(fmt.Sprintf("Pool        : min=%d max=%d\n", c.MinConnections, c.MaxConnections))
	sb.WriteString(fmt.Sprintf("Timeouts    : connect=%v query=%v idle=%v\n",
		c.ConnectTimeout, c.QueryTimeout, c.MaxIdleTime))
	sb.WriteString(fmt.Sprintf("SSL         : %s\n", c.SSLMode))
	if len(c.ReadReplicas) > 0 {
		sb.WriteString(fmt.Sprintf("Replicas    : %s\n", strings.Join(c.ReadReplicas, ", ")))
	}
	if len(c.Tags) > 0 {
		sb.WriteString("Tags        :\n")
		for k, v := range c.Tags {
			sb.WriteString(fmt.Sprintf("  %s = %s\n", k, v))
		}
	}
	return sb.String()
}

// ---------------------------------------------------------------------------
// Builder interface
// ---------------------------------------------------------------------------

type PoolConfigBuilder interface {
	SetCredentials(user, password string) PoolConfigBuilder
	SetHost(host string, port int) PoolConfigBuilder
	SetDatabase(name string) PoolConfigBuilder
	SetSSLMode(mode string) PoolConfigBuilder
	SetPoolSize(min, max int) PoolConfigBuilder
	SetConnectTimeout(d time.Duration) PoolConfigBuilder
	SetQueryTimeout(d time.Duration) PoolConfigBuilder
	SetMaxIdleTime(d time.Duration) PoolConfigBuilder
	AddReadReplica(host string) PoolConfigBuilder
	SetApplicationName(name string) PoolConfigBuilder
	AddTag(key, value string) PoolConfigBuilder
	Build() (*DBPoolConfig, error)
}

// ---------------------------------------------------------------------------
// Concrete Builder — PostgreSQL
// ---------------------------------------------------------------------------

type PostgresPoolBuilder struct {
	cfg DBPoolConfig
	err error // accumulate first validation error (fail-fast on Build)
}

func NewPostgresBuilder() *PostgresPoolBuilder {
	return &PostgresPoolBuilder{
		cfg: DBPoolConfig{
			Driver:          "postgres",
			Port:            5432,
			SSLMode:         "require",
			MinConnections:  2,
			MaxConnections:  10,
			MaxIdleTime:     10 * time.Minute,
			ConnectTimeout:  5 * time.Second,
			QueryTimeout:    30 * time.Second,
			ApplicationName: "app",
			Tags:            make(map[string]string),
		},
	}
}

func (b *PostgresPoolBuilder) SetCredentials(user, password string) PoolConfigBuilder {
	b.cfg.Username = user
	b.cfg.Password = password
	return b
}

func (b *PostgresPoolBuilder) SetHost(host string, port int) PoolConfigBuilder {
	b.cfg.Host = host
	b.cfg.Port = port
	return b
}

func (b *PostgresPoolBuilder) SetDatabase(name string) PoolConfigBuilder {
	b.cfg.Database = name
	return b
}

func (b *PostgresPoolBuilder) SetSSLMode(mode string) PoolConfigBuilder {
	valid := map[string]bool{"disable": true, "allow": true, "prefer": true,
		"require": true, "verify-ca": true, "verify-full": true}
	if !valid[mode] {
		b.err = fmt.Errorf("invalid SSL mode: %q", mode)
	}
	b.cfg.SSLMode = mode
	return b
}

func (b *PostgresPoolBuilder) SetPoolSize(min, max int) PoolConfigBuilder {
	if min < 1 || max < min {
		b.err = fmt.Errorf("invalid pool size: min=%d max=%d", min, max)
	}
	b.cfg.MinConnections = min
	b.cfg.MaxConnections = max
	return b
}

func (b *PostgresPoolBuilder) SetConnectTimeout(d time.Duration) PoolConfigBuilder {
	b.cfg.ConnectTimeout = d
	return b
}

func (b *PostgresPoolBuilder) SetQueryTimeout(d time.Duration) PoolConfigBuilder {
	b.cfg.QueryTimeout = d
	return b
}

func (b *PostgresPoolBuilder) SetMaxIdleTime(d time.Duration) PoolConfigBuilder {
	b.cfg.MaxIdleTime = d
	return b
}

func (b *PostgresPoolBuilder) AddReadReplica(host string) PoolConfigBuilder {
	b.cfg.ReadReplicas = append(b.cfg.ReadReplicas, host)
	return b
}

func (b *PostgresPoolBuilder) SetApplicationName(name string) PoolConfigBuilder {
	b.cfg.ApplicationName = name
	return b
}

func (b *PostgresPoolBuilder) AddTag(key, value string) PoolConfigBuilder {
	b.cfg.Tags[key] = value
	return b
}

func (b *PostgresPoolBuilder) Build() (*DBPoolConfig, error) {
	if b.err != nil {
		return nil, b.err
	}
	if b.cfg.Host == "" {
		return nil, errors.New("host is required")
	}
	if b.cfg.Database == "" {
		return nil, errors.New("database name is required")
	}
	if b.cfg.Username == "" {
		return nil, errors.New("username is required")
	}

	// Return a copy so the builder can be reused
	cfg := b.cfg
	cfg.Tags = make(map[string]string, len(b.cfg.Tags))
	for k, v := range b.cfg.Tags {
		cfg.Tags[k] = v
	}
	cfg.ReadReplicas = append([]string{}, b.cfg.ReadReplicas...)
	return &cfg, nil
}

// ---------------------------------------------------------------------------
// Director — environment-specific pool presets
// ---------------------------------------------------------------------------

type EnvDirector struct {
	builder PoolConfigBuilder
}

func NewEnvDirector(builder PoolConfigBuilder) *EnvDirector {
	return &EnvDirector{builder: builder}
}

// BuildProductionConfig creates a hardened, high-throughput production pool.
func (d *EnvDirector) BuildProductionConfig(host, db, user, pass string) (*DBPoolConfig, error) {
	return d.builder.
		SetHost(host, 5432).
		SetCredentials(user, pass).
		SetDatabase(db).
		SetSSLMode("verify-full").
		SetPoolSize(10, 100).
		SetConnectTimeout(3 * time.Second).
		SetQueryTimeout(60 * time.Second).
		SetMaxIdleTime(5 * time.Minute).
		AddReadReplica(strings.Replace(host, "primary", "replica-1", 1)).
		AddReadReplica(strings.Replace(host, "primary", "replica-2", 1)).
		SetApplicationName("myapp-prod").
		AddTag("env", "production").
		AddTag("team", "platform").
		Build()
}

// BuildDevelopmentConfig creates a permissive, low-resource dev pool.
func (d *EnvDirector) BuildDevelopmentConfig() (*DBPoolConfig, error) {
	return d.builder.
		SetHost("localhost", 5432).
		SetCredentials("dev_user", "dev_password").
		SetDatabase("myapp_dev").
		SetSSLMode("disable").
		SetPoolSize(1, 5).
		SetConnectTimeout(10 * time.Second).
		SetQueryTimeout(120 * time.Second).
		SetApplicationName("myapp-dev").
		AddTag("env", "development").
		Build()
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

func main() {
	builder  := NewPostgresBuilder()
	director := NewEnvDirector(builder)

	prodCfg, err := director.BuildProductionConfig(
		"primary.db.prod.internal", "myapp", "app_user", "s3cr3t",
	)
	if err != nil {
		fmt.Println("Error building prod config:", err)
	} else {
		fmt.Println("=== Production Pool Config ===")
		fmt.Println(prodCfg)
	}

	devCfg, err := director.BuildDevelopmentConfig()
	if err != nil {
		fmt.Println("Error building dev config:", err)
	} else {
		fmt.Println("=== Development Pool Config ===")
		fmt.Println(devCfg)
	}

	// Custom staging config — no Director
	stagingCfg, err := NewPostgresBuilder().
		SetHost("staging.db.internal", 5432).
		SetCredentials("staging_user", "staging_pass").
		SetDatabase("myapp_staging").
		SetSSLMode("require").
		SetPoolSize(5, 20).
		SetConnectTimeout(5 * time.Second).
		SetApplicationName("myapp-staging").
		AddTag("env", "staging").
		Build()

	if err != nil {
		fmt.Println("Error building staging config:", err)
	} else {
		fmt.Println("=== Staging Pool Config ===")
		fmt.Println(stagingCfg)
	}
}
```

---

### PHP

```php
<?php
/**
 * Builder Pattern — PHP Example
 * Real-world use case: Building PDF report objects for a reporting service.
 *
 * Demonstrates:
 *  - A fluent builder with method chaining
 *  - Two concrete builders: PdfReportBuilder and HtmlReportBuilder
 *  - A Director encoding common report recipes
 *  - PHP 8.1 enums and readonly properties
 */

declare(strict_types=1);

// ---------------------------------------------------------------------------
// Supporting types
// ---------------------------------------------------------------------------

enum PageSize: string
{
    case A4     = 'A4';
    case Letter = 'Letter';
    case Legal  = 'Legal';
}

enum Orientation: string
{
    case Portrait  = 'portrait';
    case Landscape = 'landscape';
}

// ---------------------------------------------------------------------------
// Products
// ---------------------------------------------------------------------------

final class PdfReport
{
    public function __construct(
        public readonly string      $title,
        public readonly string      $author,
        public readonly PageSize    $pageSize,
        public readonly Orientation $orientation,
        public readonly array       $sections,      // ['heading' => '', 'content' => '']
        public readonly array       $charts,        // chart identifiers
        public readonly bool        $hasTableOfContents,
        public readonly bool        $hasPageNumbers,
        public readonly string      $footerText,
        public readonly \DateTimeImmutable $generatedAt,
    ) {}

    public function describe(): string
    {
        $sectionTitles = array_column($this->sections, 'heading');
        return sprintf(
            "PDF Report: \"%s\" by %s\n"
          . "  Page    : %s %s\n"
          . "  Sections: %s\n"
          . "  Charts  : %s\n"
          . "  TOC     : %s | Page numbers: %s\n"
          . "  Footer  : %s\n"
          . "  Built   : %s",
            $this->title,
            $this->author,
            $this->pageSize->value,
            $this->orientation->value,
            implode(', ', $sectionTitles) ?: 'none',
            implode(', ', $this->charts) ?: 'none',
            $this->hasTableOfContents ? 'yes' : 'no',
            $this->hasPageNumbers ? 'yes' : 'no',
            $this->footerText,
            $this->generatedAt->format('Y-m-d H:i:s T'),
        );
    }
}

final class HtmlReport
{
    public function __construct(
        public readonly string $title,
        public readonly string $htmlContent,
        public readonly string $cssTheme,
        public readonly bool   $isResponsive,
    ) {}

    public function describe(): string
    {
        return sprintf(
            "HTML Report: \"%s\"\n  Theme: %s | Responsive: %s\n  Content length: %d chars",
            $this->title,
            $this->cssTheme,
            $this->isResponsive ? 'yes' : 'no',
            strlen($this->htmlContent),
        );
    }
}

// ---------------------------------------------------------------------------
// Builder interface
// ---------------------------------------------------------------------------

interface ReportBuilderInterface
{
    public function setTitle(string $title): static;
    public function setAuthor(string $author): static;
    public function addSection(string $heading, string $content): static;
    public function addChart(string $chartId): static;
    public function reset(): static;
}

// ---------------------------------------------------------------------------
// Concrete Builder 1 — PDF
// ---------------------------------------------------------------------------

final class PdfReportBuilder implements ReportBuilderInterface
{
    private string      $title       = 'Untitled Report';
    private string      $author      = 'System';
    private PageSize    $pageSize    = PageSize::A4;
    private Orientation $orientation = Orientation::Portrait;
    private array       $sections    = [];
    private array       $charts      = [];
    private bool        $toc         = false;
    private bool        $pageNumbers = true;
    private string      $footer      = '';

    public function setTitle(string $title): static
    {
        $this->title = $title;
        return $this;
    }

    public function setAuthor(string $author): static
    {
        $this->author = $author;
        return $this;
    }

    public function setPageSize(PageSize $size): static
    {
        $this->pageSize = $size;
        return $this;
    }

    public function setOrientation(Orientation $orientation): static
    {
        $this->orientation = $orientation;
        return $this;
    }

    public function addSection(string $heading, string $content): static
    {
        $this->sections[] = ['heading' => $heading, 'content' => $content];
        return $this;
    }

    public function addChart(string $chartId): static
    {
        $this->charts[] = $chartId;
        return $this;
    }

    public function enableTableOfContents(): static
    {
        $this->toc = true;
        return $this;
    }

    public function setFooter(string $text): static
    {
        $this->footer = $text;
        return $this;
    }

    public function reset(): static
    {
        $this->title       = 'Untitled Report';
        $this->author      = 'System';
        $this->pageSize    = PageSize::A4;
        $this->orientation = Orientation::Portrait;
        $this->sections    = [];
        $this->charts      = [];
        $this->toc         = false;
        $this->pageNumbers = true;
        $this->footer      = '';
        return $this;
    }

    public function build(): PdfReport
    {
        if (empty($this->title)) {
            throw new \InvalidArgumentException('Report title cannot be empty.');
        }

        return new PdfReport(
            title:              $this->title,
            author:             $this->author,
            pageSize:           $this->pageSize,
            orientation:        $this->orientation,
            sections:           $this->sections,
            charts:             $this->charts,
            hasTableOfContents: $this->toc,
            hasPageNumbers:     $this->pageNumbers,
            footerText:         $this->footer,
            generatedAt:        new \DateTimeImmutable(),
        );
    }
}

// ---------------------------------------------------------------------------
// Concrete Builder 2 — HTML
// ---------------------------------------------------------------------------

final class HtmlReportBuilder implements ReportBuilderInterface
{
    private string $title       = 'Untitled Report';
    private string $author      = 'System';
    private string $cssTheme    = 'default';
    private bool   $responsive  = true;
    private array  $sections    = [];

    public function setTitle(string $title): static
    {
        $this->title = $title;
        return $this;
    }

    public function setAuthor(string $author): static
    {
        $this->author = $author;
        return $this;
    }

    public function setCssTheme(string $theme): static
    {
        $this->cssTheme = $theme;
        return $this;
    }

    public function setResponsive(bool $responsive): static
    {
        $this->responsive = $responsive;
        return $this;
    }

    public function addSection(string $heading, string $content): static
    {
        $this->sections[] = ['heading' => $heading, 'content' => $content];
        return $this;
    }

    /** Not used for HTML reports, included to satisfy interface. */
    public function addChart(string $chartId): static
    {
        // Charts are embedded inline in HTML via script tags — no-op here
        return $this;
    }

    public function reset(): static
    {
        $this->title      = 'Untitled Report';
        $this->author     = 'System';
        $this->cssTheme   = 'default';
        $this->responsive = true;
        $this->sections   = [];
        return $this;
    }

    public function build(): HtmlReport
    {
        $html  = "<!DOCTYPE html>\n<html>\n<head>";
        $html .= "<meta charset='UTF-8'>";
        if ($this->responsive) {
            $html .= "<meta name='viewport' content='width=device-width, initial-scale=1'>";
        }
        $html .= "<title>{$this->title}</title></head>\n<body>\n";
        $html .= "<h1>{$this->title}</h1>\n<p><em>Author: {$this->author}</em></p>\n";

        foreach ($this->sections as $section) {
            $html .= "<section>\n<h2>{$section['heading']}</h2>\n<p>{$section['content']}</p>\n</section>\n";
        }

        $html .= "</body>\n</html>";

        return new HtmlReport(
            title:       $this->title,
            htmlContent: $html,
            cssTheme:    $this->cssTheme,
            isResponsive: $this->responsive,
        );
    }
}

// ---------------------------------------------------------------------------
// Director
// ---------------------------------------------------------------------------

final class FinancialReportDirector
{
    public function __construct(private ReportBuilderInterface $builder) {}

    public function setBuilder(ReportBuilderInterface $builder): void
    {
        $this->builder = $builder;
    }

    /** Recipe: standard quarterly financial report. */
    public function buildQuarterlyReport(string $quarter, string $year): mixed
    {
        $this->builder->reset()
            ->setTitle("Quarterly Financial Report — Q{$quarter} {$year}")
            ->setAuthor('Finance Department')
            ->addSection('Executive Summary', 'Revenue grew 12% YoY driven by new enterprise contracts.')
            ->addSection('Revenue Breakdown', 'SaaS: $4.2M | Services: $1.1M | Licensing: $0.3M')
            ->addSection('Expense Analysis',  'Total OpEx: $3.8M — 8% below budget.')
            ->addSection('Outlook',            "Q{$quarter} targets met. Raising full-year guidance by 5%.");

        if ($this->builder instanceof PdfReportBuilder) {
            $this->builder
                ->addChart("revenue-bar-chart-q{$quarter}")
                ->addChart("expense-pie-chart-q{$quarter}")
                ->enableTableOfContents()
                ->setFooter("Confidential — Q{$quarter} {$year} Financial Report");
        }

        return ($this->builder instanceof PdfReportBuilder)
            ? $this->builder->build()
            : $this->builder->build(); // returns HtmlReport for HtmlReportBuilder
    }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

$pdfBuilder  = new PdfReportBuilder();
$htmlBuilder = new HtmlReportBuilder();
$director    = new FinancialReportDirector($pdfBuilder);

// Build PDF quarterly report
$pdfReport = $director->buildQuarterlyReport('2', '2025');
echo "=== PDF Quarterly Report ===\n";
echo $pdfReport->describe() . "\n\n";

// Swap to HTML builder — same Director, different output
$director->setBuilder($htmlBuilder);
$htmlReport = $director->buildQuarterlyReport('2', '2025');
echo "=== HTML Quarterly Report ===\n";
echo $htmlReport->describe() . "\n\n";

// Custom one-off PDF without Director
$customPdf = (new PdfReportBuilder())
    ->setTitle('Infrastructure Capacity Planning 2026')
    ->setAuthor('Platform Engineering')
    ->setPageSize(PageSize::Letter)
    ->setOrientation(Orientation::Landscape)
    ->addSection('Current State',  'Hosting 420 microservices across 3 availability zones.')
    ->addSection('Projected Growth', '35% traffic increase expected by Q2 2026.')
    ->addChart('capacity-forecast-chart')
    ->enableTableOfContents()
    ->setFooter('Platform Engineering — Internal Use Only')
    ->build();

echo "=== Custom Capacity Report ===\n";
echo $customPdf->describe() . "\n";
```

---

### Ruby

```ruby
# Builder Pattern — Ruby Example
# Real-world use case: Building rich notification payloads for a push
# notification service (e.g., Firebase Cloud Messaging).
#
# Demonstrates:
#  - A fluent Ruby builder with method chaining
#  - A Director with template notification recipes
#  - Ruby-idiomatic use of symbols, hashes, and freeze for immutability

# ---------------------------------------------------------------------------
# Product — immutable push notification payload
# ---------------------------------------------------------------------------

class PushNotification
  attr_reader :title, :body, :icon, :sound, :badge_count,
              :deep_link, :image_url, :data, :ttl_seconds,
              :target_platform, :collapse_key, :priority

  def initialize(builder)
    @title           = builder.title
    @body            = builder.body
    @icon            = builder.icon
    @sound           = builder.sound
    @badge_count     = builder.badge_count
    @deep_link       = builder.deep_link
    @image_url       = builder.image_url
    @data            = builder.data.dup.freeze
    @ttl_seconds     = builder.ttl_seconds
    @target_platform = builder.target_platform
    @collapse_key    = builder.collapse_key
    @priority        = builder.priority
    freeze
  end

  def to_h
    {
      notification: {
        title: @title,
        body:  @body,
        icon:  @icon,
        sound: @sound,
        image: @image_url,
      }.compact,
      android: {
        priority:     @priority,
        ttl:          "#{@ttl_seconds}s",
        collapse_key: @collapse_key,
        notification: { badge_count: @badge_count },
      }.compact,
      apns: {
        payload: { aps: { badge: @badge_count, sound: @sound }.compact },
      },
      data: @data.merge(deep_link: @deep_link).compact,
      target_platform: @target_platform,
    }
  end

  def to_s
    lines = ["PushNotification:"]
    lines << "  Title    : #{@title}"
    lines << "  Body     : #{@body}"
    lines << "  Platform : #{@target_platform}"
    lines << "  Priority : #{@priority}"
    lines << "  Deep link: #{@deep_link}" if @deep_link
    lines << "  Image    : #{@image_url}" if @image_url
    lines << "  TTL      : #{@ttl_seconds}s"
    lines << "  Data     : #{@data}" unless @data.empty?
    lines.join("\n")
  end
end

# ---------------------------------------------------------------------------
# Concrete Builder
# ---------------------------------------------------------------------------

class PushNotificationBuilder
  attr_reader :title, :body, :icon, :sound, :badge_count,
              :deep_link, :image_url, :data, :ttl_seconds,
              :target_platform, :collapse_key, :priority

  def initialize
    reset
  end

  def reset
    @title           = nil
    @body            = nil
    @icon            = "ic_notification"
    @sound           = "default"
    @badge_count     = nil
    @deep_link       = nil
    @image_url       = nil
    @data            = {}
    @ttl_seconds     = 86_400   # 24 hours
    @target_platform = :all     # :ios, :android, :all
    @collapse_key    = nil
    @priority        = :high
    self
  end

  def set_title(title)
    @title = title
    self
  end

  def set_body(body)
    @body = body
    self
  end

  def set_icon(icon)
    @icon = icon
    self
  end

  def set_sound(sound)
    @sound = sound
    self
  end

  def set_badge(count)
    @badge_count = count
    self
  end

  def set_deep_link(url)
    @deep_link = url
    self
  end

  def set_image(url)
    @image_url = url
    self
  end

  def add_data(key, value)
    @data[key.to_s] = value.to_s
    self
  end

  def set_ttl(seconds)
    raise ArgumentError, "TTL must be positive" unless seconds.positive?
    @ttl_seconds = seconds
    self
  end

  def set_platform(platform)
    valid = %i[ios android all]
    raise ArgumentError, "Platform must be one of #{valid}" unless valid.include?(platform)
    @target_platform = platform
    self
  end

  def set_collapse_key(key)
    @collapse_key = key
    self
  end

  def set_priority(priority)
    valid = %i[normal high]
    raise ArgumentError, "Priority must be :normal or :high" unless valid.include?(priority)
    @priority = priority
    self
  end

  def build
    raise "Title is required"  if @title.nil? || @title.strip.empty?
    raise "Body is required"   if @body.nil?  || @body.strip.empty?

    PushNotification.new(self)
  end
end

# ---------------------------------------------------------------------------
# Director — notification campaign templates
# ---------------------------------------------------------------------------

class NotificationDirector
  def initialize(builder)
    @builder = builder
  end

  def set_builder(builder)
    @builder = builder
  end

  # Recipe: flash-sale marketing notification with image
  def build_flash_sale(product_name:, discount:, image_url:, deep_link:)
    @builder.reset
      .set_title("Flash Sale — #{discount}% OFF!")
      .set_body("#{product_name} is on sale for the next 3 hours only. Tap to grab yours!")
      .set_image(image_url)
      .set_deep_link(deep_link)
      .set_sound("cash_register.mp3")
      .set_priority(:high)
      .set_ttl(3 * 3600)                       # expires after 3 h
      .set_collapse_key("flash_sale")           # replace earlier sale notification
      .add_data("campaign_type", "flash_sale")
      .add_data("product", product_name)
      .build
  end

  # Recipe: silent data-only sync notification (no visible alert)
  def build_silent_sync(user_id:, resource:)
    @builder.reset
      .set_title("Data Sync")
      .set_body("Sync")                         # required but invisible to user
      .set_priority(:normal)
      .set_sound("none")
      .set_ttl(300)                             # 5 minutes — if not delivered, discard
      .set_platform(:android)
      .add_data("sync_resource", resource)
      .add_data("user_id", user_id.to_s)
      .build
  end

  # Recipe: order-status push
  def build_order_status(order_id:, status:, deep_link:)
    emoji = { "shipped" => "📦", "delivered" => "✅", "cancelled" => "❌" }
    label = emoji.fetch(status, "ℹ️")

    @builder.reset
      .set_title("#{label} Order ##{order_id} — #{status.capitalize}")
      .set_body("Your order status has been updated. Tap to view details.")
      .set_deep_link(deep_link)
      .set_priority(status == "cancelled" ? :high : :normal)
      .add_data("order_id", order_id.to_s)
      .add_data("status", status)
      .build
  end
end

# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

builder  = PushNotificationBuilder.new
director = NotificationDirector.new(builder)

# Marketing flash sale
sale_notification = director.build_flash_sale(
  product_name: "Sony WH-1000XM5 Headphones",
  discount:     30,
  image_url:    "https://cdn.example.com/promo/sony-xm5.jpg",
  deep_link:    "myapp://products/sony-wh1000xm5?promo=flash30"
)
puts "=== Flash Sale Notification ==="
puts sale_notification
puts

# Silent sync
sync_notification = director.build_silent_sync(user_id: 9_042, resource: "contacts")
puts "=== Silent Sync Notification ==="
puts sync_notification
puts

# Order status update
order_notification = director.build_order_status(
  order_id:  "ORD-20250712-88321",
  status:    "shipped",
  deep_link: "myapp://orders/ORD-20250712-88321"
)
puts "=== Order Status Notification ==="
puts order_notification
puts

# Custom notification without Director — two-factor auth alert
otp_notification = PushNotificationBuilder.new
  .set_title("Your verification code: 847 291")
  .set_body("This code expires in 10 minutes. Never share it with anyone.")
  .set_sound("otp_chime.mp3")
  .set_priority(:high)
  .set_ttl(600)
  .set_badge(1)
  .add_data("notification_type", "otp")
  .build

puts "=== OTP Notification ==="
puts otp_notification
```

---

## When To Use

Use the Builder pattern when:

- **You need to create different representations** of the same product (e.g., a wooden house and a glass house, or a PDF report and an HTML report) using the same step-by-step process.
- **Your constructor has many parameters**, especially optional ones. A builder gives each parameter a named, chainable setter instead of a positional argument.
- **Object construction must follow a specific sequence**, or steps have side effects / validations that must run in order.
- **You want to construct Composite trees or other recursive structures** incrementally, delegating each node's construction to a builder.
- **You need to defer or isolate construction complexity** from the rest of your business logic — the Director handles recipes, the Builder handles mechanics.

Do **not** use it when the object is simple or has only a few fields — a plain constructor or a simple factory method is sufficient and avoids the extra classes.

---

## Pros & Cons

### Pros

| | Detail |
|---|---|
| **Step-by-step construction** | You can defer construction steps, run them conditionally, or reorder them without changing the product class. |
| **Reuse of construction code** | The same Director recipes work with any conforming ConcreteBuilder, enabling different output formats from the same pipeline. |
| **Single Responsibility Principle** | Product assembly logic lives in the Builder, not in the product class itself. |
| **Isolation of complex construction** | Client code only sees the clean fluent API; the messy wiring is hidden inside the builder. |
| **Fine-grained control** | Unlike factories, which return a finished product in one call, builders let you inspect or modify intermediate states. |

### Cons

| | Detail |
|---|---|
| **Increased class count** | Each product variant needs its own ConcreteBuilder; adding a Director is a third new class. For simple objects this overhead is unjustified. |
| **Mutable intermediate state** | The builder holds partially-constructed state until `build()` is called. Misuse (e.g., sharing a builder across threads) can produce corrupt products. |
| **Discoverability** | New team members may not realise construction must be finalised with `build()`, leading to incomplete products. |

---

## Relations to Other Patterns

| Related Pattern | Relationship |
|---|---|
| **Factory Method** | The Builder's Director often uses a Factory Method to instantiate the right ConcreteBuilder. Factory Method produces a whole object in one call; Builder constructs it incrementally. |
| **Abstract Factory** | Both create families of related objects. Abstract Factory returns the product immediately; Builder focuses on step-by-step construction of a single complex object. |
| **Composite** | Builder is frequently used to construct Composite trees. Each `addComponent()` call on the builder adds a node to the tree, and `build()` returns the root. |
| **Singleton** | The Director is sometimes implemented as a Singleton, since only one Director per domain is usually required. |

---

## Sources

- https://refactoring.guru/design-patterns/builder
- https://sourcemaking.com/design_patterns/builder
