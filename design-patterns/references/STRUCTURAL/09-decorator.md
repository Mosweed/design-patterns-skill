# Decorator Pattern

**Category:** Structural
**Also Known As:** Wrapper

---

## Intent

Attach new behaviors to objects dynamically by placing them inside special wrapper objects that contain those behaviors. Decorators provide a flexible alternative to subclassing for extending functionality.

---

## Problem It Solves

Imagine you are building a notification system. You start with a basic `Notifier` class that sends an email. Then requirements grow: some users want SMS alerts, some want Slack messages, some want all three, others want email + Slack but no SMS.

Using inheritance naively produces a combinatorial explosion:

- `EmailNotifier`
- `SMSNotifier`
- `SlackNotifier`
- `EmailSMSNotifier`
- `EmailSlackNotifier`
- `SMSSLackNotifier`
- `EmailSMSSlackNotifier`

Add one more channel and the number of subclasses doubles again. This approach is brittle, hard to maintain, and violates the Open/Closed Principle.

The core problems inheritance cannot elegantly solve here are:

1. Behavior must be chosen and combined **at runtime**, not compile time.
2. Each combination requires a new concrete class.
3. Adding a new channel requires modifying every existing combination subclass.

---

## Solution

Instead of subclassing, **wrap** the target object inside decorator objects that share its interface:

1. Define a `Component` interface that both the real object and all decorators implement.
2. Create a `ConcreteComponent` — the real object doing the base work.
3. Create a `BaseDecorator` that holds a reference to a `Component` and delegates all calls to it.
4. Create `ConcreteDecorator` subclasses that override selected methods, add their behavior, then call `super` (or the wrapped component) to preserve the chain.
5. At runtime, stack decorators around the component in any order and combination.

The client only ever interacts with the `Component` interface, so decorators are invisible to it.

---

## Structure

```
         <<interface>>
          Component
         +operation()
              ^
              |
    __________|___________
    |                    |
ConcreteComponent    BaseDecorator
+operation()         -wrappee: Component
                     +BaseDecorator(c: Component)
                     +operation()
                          ^
               ___________|___________
               |                     |
    ConcreteDecoratorA     ConcreteDecoratorB
    -addedState            +operation()
    +operation()           +extraBehavior()
    +addedBehavior()

Flow of a decorated call:

  Client
    |
    v
ConcreteDecoratorB.operation()
    |  (adds behavior before/after)
    v
ConcreteDecoratorA.operation()
    |  (adds behavior before/after)
    v
ConcreteComponent.operation()
    |  (does actual work)
    v
  result bubbles back up the chain
```

---

## Participants

| Participant | Role |
|---|---|
| **Component** | Interface (or abstract class) that defines the common contract for both the real object and decorators. |
| **ConcreteComponent** | The base object. Implements `Component`. Provides the default behavior that can be extended. |
| **BaseDecorator** | Abstract class implementing `Component`. Holds a reference to a wrapped `Component` and delegates all calls to it. |
| **ConcreteDecorator** | Extends `BaseDecorator`. Adds extra state or behavior before/after delegating to the wrapped component. |
| **Client** | Composes decorators and interacts only through the `Component` interface. |

---

## How It Works

1. **Define the interface.** All participants — real component and every decorator — must implement the same `Component` interface so they are interchangeable.

2. **Implement the ConcreteComponent.** This is the object whose behavior you want to extend. It does the core work without knowing anything about decorators.

3. **Implement BaseDecorator.** It stores a reference (`wrappee`) to a `Component`. Every method delegates to `wrappee.method()`. This gives decorators a no-op baseline.

4. **Implement ConcreteDecorators.** Each overrides the method it wants to extend. It calls the parent (which calls the wrappee), and adds its own behavior before or after that call.

5. **Stack at runtime.** The client wraps the component with as many decorators as needed:
   ```
   component = new ConcreteComponent()
   component = new LoggingDecorator(component)
   component = new CompressionDecorator(component)
   component = new EncryptionDecorator(component)
   ```
   Each call to `component.operation()` now travels through Encryption → Compression → Logging → ConcreteComponent and back.

6. **Use through the interface.** Because every layer implements `Component`, the client treats the outermost decorator exactly like the raw object.

---

## Code Examples

### Python

```python
"""
Real-world example: HTTP request pipeline.

Decorators add authentication, logging, retry logic, and caching
to an HTTP client without modifying the base client class.
"""

from __future__ import annotations
import time
import hashlib
import json
from abc import ABC, abstractmethod
from typing import Any


# ─── Component Interface ───────────────────────────────────────────────────────

class HttpClient(ABC):
    """Common interface for HTTP clients and all decorators."""

    @abstractmethod
    def get(self, url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        """Perform an HTTP GET request and return a response dict."""


# ─── ConcreteComponent ─────────────────────────────────────────────────────────

class BaseHttpClient(HttpClient):
    """Minimal HTTP client that actually makes network requests."""

    def get(self, url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        # In a real implementation this would use urllib or requests.
        # We simulate a response here for self-contained demonstration.
        print(f"[BaseHttpClient] GET {url}")
        return {
            "status": 200,
            "url": url,
            "body": {"message": "Hello from server", "timestamp": time.time()},
            "headers": {"Content-Type": "application/json"},
        }


# ─── BaseDecorator ─────────────────────────────────────────────────────────────

class HttpClientDecorator(HttpClient):
    """Maintains a reference to a wrapped HttpClient and delegates to it."""

    def __init__(self, wrappee: HttpClient) -> None:
        self._wrappee = wrappee

    def get(self, url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        return self._wrappee.get(url, headers)


# ─── ConcreteDecorators ────────────────────────────────────────────────────────

class AuthDecorator(HttpClientDecorator):
    """Injects a Bearer token into every request header."""

    def __init__(self, wrappee: HttpClient, token: str) -> None:
        super().__init__(wrappee)
        self._token = token

    def get(self, url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        headers = dict(headers or {})
        headers["Authorization"] = f"Bearer {self._token}"
        print(f"[AuthDecorator] Injecting token into headers")
        return super().get(url, headers)


class LoggingDecorator(HttpClientDecorator):
    """Logs request and response metadata."""

    def get(self, url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        start = time.perf_counter()
        print(f"[LoggingDecorator] --> GET {url}")
        response = super().get(url, headers)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"[LoggingDecorator] <-- {response['status']} in {elapsed:.2f}ms")
        return response


class RetryDecorator(HttpClientDecorator):
    """Retries failed requests up to `max_retries` times with exponential backoff."""

    def __init__(self, wrappee: HttpClient, max_retries: int = 3) -> None:
        super().__init__(wrappee)
        self._max_retries = max_retries

    def get(self, url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                response = super().get(url, headers)
                if response.get("status", 0) >= 500:
                    raise RuntimeError(f"Server error: {response['status']}")
                return response
            except Exception as exc:
                last_error = exc
                wait = 2 ** (attempt - 1)
                print(f"[RetryDecorator] Attempt {attempt} failed: {exc}. Retrying in {wait}s...")
                time.sleep(wait)
        raise RuntimeError(f"All {self._max_retries} retries exhausted") from last_error


class CachingDecorator(HttpClientDecorator):
    """Caches GET responses in memory using the URL as the cache key."""

    def __init__(self, wrappee: HttpClient, ttl_seconds: float = 60.0) -> None:
        super().__init__(wrappee)
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}

    def _cache_key(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    def get(self, url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        key = self._cache_key(url)
        now = time.time()
        if key in self._cache:
            stored_at, cached_response = self._cache[key]
            if now - stored_at < self._ttl:
                print(f"[CachingDecorator] Cache HIT for {url}")
                return cached_response
        print(f"[CachingDecorator] Cache MISS for {url}")
        response = super().get(url, headers)
        self._cache[key] = (now, response)
        return response


# ─── Client Code ───────────────────────────────────────────────────────────────

def build_client(token: str) -> HttpClient:
    """
    Compose a fully-featured HTTP client from decorators.
    Order matters: outermost decorator runs first.
    """
    client: HttpClient = BaseHttpClient()
    client = AuthDecorator(client, token=token)
    client = RetryDecorator(client, max_retries=3)
    client = CachingDecorator(client, ttl_seconds=30.0)
    client = LoggingDecorator(client)
    return client


if __name__ == "__main__":
    api_url = "https://api.example.com/users"
    client = build_client(token="secret-api-token-xyz")

    print("=== First request (cache miss) ===")
    resp = client.get(api_url)
    print(f"Response status: {resp['status']}\n")

    print("=== Second request (cache hit) ===")
    resp = client.get(api_url)
    print(f"Response status: {resp['status']}\n")
```

---

### Java

```java
/**
 * Real-world example: Text processing pipeline for a document export system.
 *
 * Decorators apply Markdown-to-HTML conversion, syntax highlighting,
 * line numbering, and word-wrap to a raw text source — in any combination.
 */

// ─── Component Interface ───────────────────────────────────────────────────────

interface TextRenderer {
    String render(String input);
}

// ─── ConcreteComponent ─────────────────────────────────────────────────────────

class PlainTextRenderer implements TextRenderer {
    @Override
    public String render(String input) {
        // Simply returns the input wrapped in a <pre> block.
        return "<pre>" + escapeHtml(input) + "</pre>";
    }

    private String escapeHtml(String text) {
        return text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;");
    }
}

// ─── BaseDecorator ─────────────────────────────────────────────────────────────

abstract class TextRendererDecorator implements TextRenderer {
    protected final TextRenderer wrappee;

    protected TextRendererDecorator(TextRenderer wrappee) {
        this.wrappee = wrappee;
    }

    @Override
    public String render(String input) {
        return wrappee.render(input);
    }
}

// ─── ConcreteDecorators ────────────────────────────────────────────────────────

/** Adds line numbers to each line of the rendered output. */
class LineNumberDecorator extends TextRendererDecorator {

    public LineNumberDecorator(TextRenderer wrappee) {
        super(wrappee);
    }

    @Override
    public String render(String input) {
        String[] lines = input.split("\n", -1);
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < lines.length; i++) {
            sb.append(String.format("%4d | %s%n", i + 1, lines[i]));
        }
        return wrappee.render(sb.toString());
    }
}

/** Wraps long lines at a configurable column width. */
class WordWrapDecorator extends TextRendererDecorator {
    private final int columnWidth;

    public WordWrapDecorator(TextRenderer wrappee, int columnWidth) {
        super(wrappee);
        this.columnWidth = columnWidth;
    }

    @Override
    public String render(String input) {
        StringBuilder result = new StringBuilder();
        for (String paragraph : input.split("\n", -1)) {
            result.append(wrapParagraph(paragraph)).append("\n");
        }
        return wrappee.render(result.toString().stripTrailing());
    }

    private String wrapParagraph(String text) {
        if (text.length() <= columnWidth) return text;
        StringBuilder sb = new StringBuilder();
        int start = 0;
        while (start < text.length()) {
            int end = Math.min(start + columnWidth, text.length());
            if (end < text.length()) {
                int lastSpace = text.lastIndexOf(' ', end);
                if (lastSpace > start) end = lastSpace;
            }
            if (sb.length() > 0) sb.append("\n");
            sb.append(text, start, end).append(end < text.length() ? " ↩" : "");
            start = (end < text.length() && text.charAt(end) == ' ') ? end + 1 : end;
        }
        return sb.toString();
    }
}

/** Surrounds the rendered output in an HTML document boilerplate. */
class HtmlDocumentDecorator extends TextRendererDecorator {
    private final String title;

    public HtmlDocumentDecorator(TextRenderer wrappee, String title) {
        super(wrappee);
        this.title = title;
    }

    @Override
    public String render(String input) {
        String body = wrappee.render(input);
        return "<!DOCTYPE html>\n<html>\n<head><title>" + title + "</title></head>\n"
             + "<body>\n" + body + "\n</body>\n</html>";
    }
}

/** Highlights occurrences of a keyword with a <mark> tag. */
class KeywordHighlightDecorator extends TextRendererDecorator {
    private final String keyword;

    public KeywordHighlightDecorator(TextRenderer wrappee, String keyword) {
        super(wrappee);
        this.keyword = keyword;
    }

    @Override
    public String render(String input) {
        // Mark before rendering so the inner renderer can escape normally.
        String highlighted = input.replace(keyword, "[[MARK]]" + keyword + "[[/MARK]]");
        String rendered = wrappee.render(highlighted);
        return rendered.replace("[[MARK]]", "<mark>").replace("[[/MARK]]", "</mark>");
    }
}

// ─── Client Code ───────────────────────────────────────────────────────────────

public class DecoratorDemo {

    public static void main(String[] args) {
        String sourceCode =
            "public class Hello {\n" +
            "    public static void main(String[] args) {\n" +
            "        System.out.println(\"Hello, Decorator!\");\n" +
            "    }\n" +
            "}";

        // Build pipeline: wrap, highlight keyword, add line numbers, wrap in HTML document.
        TextRenderer renderer =
            new HtmlDocumentDecorator(
                new KeywordHighlightDecorator(
                    new LineNumberDecorator(
                        new WordWrapDecorator(
                            new PlainTextRenderer(),
                            80
                        )
                    ),
                    "Decorator"
                ),
                "Code Viewer"
            );

        String output = renderer.render(sourceCode);
        System.out.println(output);

        System.out.println("\n--- Plain renderer (no decorators) ---");
        TextRenderer plain = new PlainTextRenderer();
        System.out.println(plain.render("Hello, world!"));
    }
}
```

---

### C++

```cpp
/**
 * Real-world example: Data stream processing.
 *
 * Decorators layer compression, encryption, and Base64 encoding
 * on top of a raw file-writing stream. Each decorator is stackable
 * in any order.
 */

#include <iostream>
#include <string>
#include <memory>
#include <algorithm>
#include <sstream>
#include <iomanip>

// ─── Component Interface ───────────────────────────────────────────────────────

class DataStream {
public:
    virtual ~DataStream() = default;
    virtual void write(const std::string& data) = 0;
    virtual std::string read() const = 0;
};

// ─── ConcreteComponent ─────────────────────────────────────────────────────────

class FileDataStream : public DataStream {
    std::string filename_;
    std::string buffer_;
public:
    explicit FileDataStream(std::string filename)
        : filename_(std::move(filename)) {}

    void write(const std::string& data) override {
        std::cout << "[FileDataStream] Writing " << data.size()
                  << " bytes to '" << filename_ << "'\n";
        buffer_ = data;   // Simulate file write.
    }

    std::string read() const override {
        std::cout << "[FileDataStream] Reading from '" << filename_ << "'\n";
        return buffer_;
    }
};

// ─── BaseDecorator ─────────────────────────────────────────────────────────────

class DataStreamDecorator : public DataStream {
protected:
    std::unique_ptr<DataStream> wrappee_;
public:
    explicit DataStreamDecorator(std::unique_ptr<DataStream> wrappee)
        : wrappee_(std::move(wrappee)) {}

    void write(const std::string& data) override {
        wrappee_->write(data);
    }

    std::string read() const override {
        return wrappee_->read();
    }
};

// ─── ConcreteDecorators ────────────────────────────────────────────────────────

/** Simulates run-length encoding compression. */
class CompressionDecorator : public DataStreamDecorator {
public:
    explicit CompressionDecorator(std::unique_ptr<DataStream> wrappee)
        : DataStreamDecorator(std::move(wrappee)) {}

    void write(const std::string& data) override {
        std::cout << "[CompressionDecorator] Compressing data...\n";
        wrappee_->write(compress(data));
    }

    std::string read() const override {
        return decompress(wrappee_->read());
    }

private:
    // Minimal run-length encoding: "aaabbc" -> "3a2b1c"
    static std::string compress(const std::string& data) {
        if (data.empty()) return {};
        std::ostringstream out;
        char prev = data[0];
        int count = 1;
        for (size_t i = 1; i < data.size(); ++i) {
            if (data[i] == prev) {
                ++count;
            } else {
                out << count << prev;
                prev = data[i];
                count = 1;
            }
        }
        out << count << prev;
        return out.str();
    }

    static std::string decompress(const std::string& data) {
        std::string out;
        size_t i = 0;
        while (i < data.size()) {
            std::string numStr;
            while (i < data.size() && std::isdigit(static_cast<unsigned char>(data[i])))
                numStr += data[i++];
            if (i < data.size() && !numStr.empty())
                out.append(std::stoi(numStr), data[i++]);
        }
        return out;
    }
};

/** Simulates XOR-based encryption (for demonstration only — not production-safe). */
class EncryptionDecorator : public DataStreamDecorator {
    char key_;
public:
    explicit EncryptionDecorator(std::unique_ptr<DataStream> wrappee, char key = 0x5A)
        : DataStreamDecorator(std::move(wrappee)), key_(key) {}

    void write(const std::string& data) override {
        std::cout << "[EncryptionDecorator] Encrypting data...\n";
        wrappee_->write(xorCipher(data));
    }

    std::string read() const override {
        return xorCipher(wrappee_->read());  // XOR is its own inverse.
    }

private:
    std::string xorCipher(const std::string& data) const {
        std::string out = data;
        for (char& c : out) c ^= key_;
        return out;
    }
};

/** Wraps data in a simple hex encoding. */
class HexEncodingDecorator : public DataStreamDecorator {
public:
    explicit HexEncodingDecorator(std::unique_ptr<DataStream> wrappee)
        : DataStreamDecorator(std::move(wrappee)) {}

    void write(const std::string& data) override {
        std::cout << "[HexEncodingDecorator] Hex-encoding data...\n";
        wrappee_->write(toHex(data));
    }

    std::string read() const override {
        return fromHex(wrappee_->read());
    }

private:
    static std::string toHex(const std::string& data) {
        std::ostringstream oss;
        for (unsigned char c : data)
            oss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(c);
        return oss.str();
    }

    static std::string fromHex(const std::string& hex) {
        std::string out;
        for (size_t i = 0; i + 1 < hex.size(); i += 2)
            out += static_cast<char>(std::stoi(hex.substr(i, 2), nullptr, 16));
        return out;
    }
};

// ─── Client Code ───────────────────────────────────────────────────────────────

int main() {
    const std::string originalData = "Hello, Decorator Pattern!";

    std::cout << "=== Building decorated stream: File <- Encrypt <- Compress <- HexEncode ===\n\n";

    auto stream =
        std::make_unique<HexEncodingDecorator>(
            std::make_unique<CompressionDecorator>(
                std::make_unique<EncryptionDecorator>(
                    std::make_unique<FileDataStream>("output.dat")
                )
            )
        );

    std::cout << "Original data: \"" << originalData << "\"\n\n";
    stream->write(originalData);

    std::cout << "\n=== Reading back through the same stack ===\n";
    std::string recovered = stream->read();
    std::cout << "Recovered data: \"" << recovered << "\"\n";

    return 0;
}
```

---

### C#

```csharp
/**
 * Real-world example: E-commerce order pricing pipeline.
 *
 * Decorators apply discounts, taxes, and shipping costs to a base
 * order total without modifying the Order class. New pricing rules
 * can be stacked or removed at runtime (e.g. seasonal promotions).
 */

using System;
using System.Collections.Generic;

// ─── Component Interface ───────────────────────────────────────────────────────

public interface IOrderPricer
{
    decimal GetTotal();
    string GetDescription();
}

// ─── ConcreteComponent ─────────────────────────────────────────────────────────

public class Order : IOrderPricer
{
    private readonly List<(string Name, decimal Price)> _items = new();

    public void AddItem(string name, decimal price) => _items.Add((name, price));

    public decimal GetTotal() => _items.Count == 0 ? 0m : _items.Sum(i => i.Price);

    public string GetDescription()
    {
        if (_items.Count == 0) return "Empty order";
        return string.Join(", ", _items.ConvertAll(i => $"{i.Name} (${i.Price:F2})"));
    }
}

// ─── BaseDecorator ─────────────────────────────────────────────────────────────

public abstract class OrderPricerDecorator : IOrderPricer
{
    protected readonly IOrderPricer _wrappee;

    protected OrderPricerDecorator(IOrderPricer wrappee)
        => _wrappee = wrappee;

    public virtual decimal GetTotal() => _wrappee.GetTotal();
    public virtual string GetDescription() => _wrappee.GetDescription();
}

// ─── ConcreteDecorators ────────────────────────────────────────────────────────

/// <summary>Applies a flat percentage discount.</summary>
public class PercentageDiscountDecorator : OrderPricerDecorator
{
    private readonly decimal _discountPercent;
    private readonly string _label;

    public PercentageDiscountDecorator(IOrderPricer wrappee, decimal percent, string label)
        : base(wrappee)
    {
        _discountPercent = percent;
        _label = label;
    }

    public override decimal GetTotal()
    {
        decimal subtotal = _wrappee.GetTotal();
        decimal discount = subtotal * (_discountPercent / 100m);
        return subtotal - discount;
    }

    public override string GetDescription()
        => $"{_wrappee.GetDescription()}\n  - {_label}: -{_discountPercent}%";
}

/// <summary>Applies flat-amount loyalty reward deduction (min 0).</summary>
public class LoyaltyRewardDecorator : OrderPricerDecorator
{
    private readonly decimal _rewardAmount;

    public LoyaltyRewardDecorator(IOrderPricer wrappee, decimal rewardAmount)
        : base(wrappee) => _rewardAmount = rewardAmount;

    public override decimal GetTotal()
        => Math.Max(0m, _wrappee.GetTotal() - _rewardAmount);

    public override string GetDescription()
        => $"{_wrappee.GetDescription()}\n  - Loyalty reward: -${_rewardAmount:F2}";
}

/// <summary>Adds sales tax as a percentage of the current total.</summary>
public class TaxDecorator : OrderPricerDecorator
{
    private readonly decimal _taxRate;
    private readonly string _region;

    public TaxDecorator(IOrderPricer wrappee, decimal taxRate, string region)
        : base(wrappee)
    {
        _taxRate = taxRate;
        _region = region;
    }

    public override decimal GetTotal()
    {
        decimal subtotal = _wrappee.GetTotal();
        return subtotal + subtotal * (_taxRate / 100m);
    }

    public override string GetDescription()
        => $"{_wrappee.GetDescription()}\n  + {_region} tax: +{_taxRate}%";
}

/// <summary>Adds a flat or weight-based shipping fee.</summary>
public class ShippingDecorator : OrderPricerDecorator
{
    private readonly decimal _flatFee;
    private readonly string _carrier;

    public ShippingDecorator(IOrderPricer wrappee, decimal flatFee, string carrier)
        : base(wrappee)
    {
        _flatFee = flatFee;
        _carrier = carrier;
    }

    public override decimal GetTotal() => _wrappee.GetTotal() + _flatFee;

    public override string GetDescription()
        => $"{_wrappee.GetDescription()}\n  + {_carrier} shipping: +${_flatFee:F2}";
}

// ─── Client Code ───────────────────────────────────────────────────────────────

class Program
{
    static void Main()
    {
        var order = new Order();
        order.AddItem("Mechanical Keyboard", 129.99m);
        order.AddItem("USB-C Hub", 49.99m);
        order.AddItem("Monitor Stand", 39.99m);

        Console.WriteLine("=== Standard checkout (tax + shipping) ===");
        IOrderPricer standardPricer =
            new ShippingDecorator(
                new TaxDecorator(order, taxRate: 8.5m, region: "CA"),
                flatFee: 9.99m,
                carrier: "UPS Ground"
            );
        PrintReceipt(standardPricer);

        Console.WriteLine("\n=== Black Friday checkout (20% off + loyalty + tax + free shipping) ===");
        IOrderPricer blackFridayPricer =
            new TaxDecorator(
                new LoyaltyRewardDecorator(
                    new PercentageDiscountDecorator(order, percent: 20m, label: "Black Friday"),
                    rewardAmount: 10m
                ),
                taxRate: 8.5m,
                region: "CA"
            );
        PrintReceipt(blackFridayPricer);
    }

    static void PrintReceipt(IOrderPricer pricer)
    {
        Console.WriteLine(pricer.GetDescription());
        Console.WriteLine(new string('-', 50));
        Console.WriteLine($"  TOTAL: ${pricer.GetTotal():F2}");
    }
}
```

---

### TypeScript

```typescript
/**
 * Real-world example: Middleware pipeline for an Express-like web framework.
 *
 * Decorators add rate limiting, authentication, input validation,
 * and response caching to a route handler — composable at runtime.
 */

// ─── Types ─────────────────────────────────────────────────────────────────────

interface Request {
  method: string;
  path: string;
  headers: Record<string, string>;
  body?: unknown;
  userId?: string;
}

interface Response {
  status: number;
  body: unknown;
  headers: Record<string, string>;
}

// ─── Component Interface ───────────────────────────────────────────────────────

interface RequestHandler {
  handle(req: Request): Promise<Response>;
}

// ─── ConcreteComponent ─────────────────────────────────────────────────────────

/** Actual business logic: returns a list of user profiles. */
class UserProfileHandler implements RequestHandler {
  async handle(req: Request): Promise<Response> {
    console.log(`[UserProfileHandler] Processing ${req.method} ${req.path}`);
    // Simulate DB fetch.
    const users = [
      { id: req.userId, name: "Alice Doe", email: "alice@example.com" },
    ];
    return {
      status: 200,
      body: { data: users },
      headers: { "Content-Type": "application/json" },
    };
  }
}

// ─── BaseDecorator ─────────────────────────────────────────────────────────────

abstract class HandlerDecorator implements RequestHandler {
  constructor(protected readonly wrappee: RequestHandler) {}

  async handle(req: Request): Promise<Response> {
    return this.wrappee.handle(req);
  }
}

// ─── ConcreteDecorators ────────────────────────────────────────────────────────

/** Validates the Authorization header and extracts userId. */
class AuthMiddleware extends HandlerDecorator {
  private readonly validTokens = new Map<string, string>([
    ["token-alice-123", "user-1"],
    ["token-bob-456", "user-2"],
  ]);

  async handle(req: Request): Promise<Response> {
    const authHeader = req.headers["authorization"] ?? "";
    const token = authHeader.replace(/^Bearer\s+/i, "");

    if (!token || !this.validTokens.has(token)) {
      console.log("[AuthMiddleware] Unauthorized request rejected");
      return { status: 401, body: { error: "Unauthorized" }, headers: {} };
    }

    console.log("[AuthMiddleware] Token valid, attaching userId");
    const enrichedReq: Request = { ...req, userId: this.validTokens.get(token) };
    return super.handle(enrichedReq);
  }
}

/** Blocks requests that exceed a per-IP rate limit. */
class RateLimiterMiddleware extends HandlerDecorator {
  private readonly counts = new Map<string, { count: number; windowStart: number }>();
  private readonly maxRequests: number;
  private readonly windowMs: number;

  constructor(wrappee: RequestHandler, maxRequests = 10, windowMs = 60_000) {
    super(wrappee);
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
  }

  async handle(req: Request): Promise<Response> {
    const ip = req.headers["x-forwarded-for"] ?? "unknown";
    const now = Date.now();
    const entry = this.counts.get(ip) ?? { count: 0, windowStart: now };

    if (now - entry.windowStart > this.windowMs) {
      entry.count = 0;
      entry.windowStart = now;
    }

    entry.count++;
    this.counts.set(ip, entry);

    if (entry.count > this.maxRequests) {
      console.log(`[RateLimiter] IP ${ip} exceeded limit (${entry.count}/${this.maxRequests})`);
      return {
        status: 429,
        body: { error: "Too Many Requests" },
        headers: { "Retry-After": String(Math.ceil(this.windowMs / 1000)) },
      };
    }

    console.log(`[RateLimiter] IP ${ip}: ${entry.count}/${this.maxRequests} requests`);
    return super.handle(req);
  }
}

/** Caches identical requests for a configurable TTL. */
class CacheMiddleware extends HandlerDecorator {
  private readonly store = new Map<string, { expires: number; response: Response }>();
  private readonly ttlMs: number;

  constructor(wrappee: RequestHandler, ttlMs = 5_000) {
    super(wrappee);
    this.ttlMs = ttlMs;
  }

  async handle(req: Request): Promise<Response> {
    const key = `${req.method}:${req.path}:${req.userId ?? "anon"}`;
    const cached = this.store.get(key);
    if (cached && Date.now() < cached.expires) {
      console.log(`[CacheMiddleware] Cache HIT for ${key}`);
      return { ...cached.response, headers: { ...cached.response.headers, "X-Cache": "HIT" } };
    }
    console.log(`[CacheMiddleware] Cache MISS for ${key}`);
    const response = await super.handle(req);
    this.store.set(key, { expires: Date.now() + this.ttlMs, response });
    return response;
  }
}

/** Logs request and response summary. */
class LoggingMiddleware extends HandlerDecorator {
  async handle(req: Request): Promise<Response> {
    const start = performance.now();
    console.log(`[Logger] --> ${req.method} ${req.path}`);
    const response = await super.handle(req);
    const ms = (performance.now() - start).toFixed(2);
    console.log(`[Logger] <-- ${response.status} (${ms}ms)`);
    return response;
  }
}

// ─── Composition Root ──────────────────────────────────────────────────────────

async function main(): Promise<void> {
  // Build handler chain: outermost runs first.
  const handler: RequestHandler =
    new LoggingMiddleware(
      new RateLimiterMiddleware(
        new AuthMiddleware(
          new CacheMiddleware(
            new UserProfileHandler(),
            5_000
          )
        ),
        10, 60_000
      )
    );

  const req: Request = {
    method: "GET",
    path: "/api/users/me",
    headers: {
      authorization: "Bearer token-alice-123",
      "x-forwarded-for": "192.168.1.1",
      "content-type": "application/json",
    },
  };

  console.log("=== Request 1 (cold cache) ===");
  const r1 = await handler.handle(req);
  console.log("Response:", JSON.stringify(r1.body), "\n");

  console.log("=== Request 2 (warm cache) ===");
  const r2 = await handler.handle(req);
  console.log("Response:", JSON.stringify(r2.body), "\n");

  console.log("=== Request 3 (bad token) ===");
  const r3 = await handler.handle({ ...req, headers: { ...req.headers, authorization: "Bearer bad-token" } });
  console.log("Response:", JSON.stringify(r3.body), "\n");
}

main().catch(console.error);
```

---

### Go

```go
// Real-world example: Database query pipeline.
//
// Decorators layer logging, caching, metrics collection, and
// circuit-breaking around a core database query executor.
// Go uses interfaces and struct embedding rather than class hierarchies.

package main

import (
	"errors"
	"fmt"
	"sync"
	"time"
)

// ─── Component Interface ───────────────────────────────────────────────────────

// QueryResult represents a simplified DB query result.
type QueryResult struct {
	Rows  []map[string]any
	Count int
}

// QueryExecutor is the component interface all decorators and the real DB must satisfy.
type QueryExecutor interface {
	Execute(query string, args ...any) (*QueryResult, error)
}

// ─── ConcreteComponent ─────────────────────────────────────────────────────────

// DatabaseExecutor is the real executor that talks to the database.
type DatabaseExecutor struct {
	dsn string
}

func NewDatabaseExecutor(dsn string) *DatabaseExecutor {
	return &DatabaseExecutor{dsn: dsn}
}

func (d *DatabaseExecutor) Execute(query string, args ...any) (*QueryResult, error) {
	// Simulate a DB call with artificial latency.
	time.Sleep(5 * time.Millisecond)
	fmt.Printf("[DB] Executing: %q with args %v\n", query, args)
	return &QueryResult{
		Rows:  []map[string]any{{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}},
		Count: 2,
	}, nil
}

// ─── ConcreteDecorators ────────────────────────────────────────────────────────

// LoggingDecorator logs every query and its execution time.
type LoggingDecorator struct {
	wrappee QueryExecutor
}

func WithLogging(e QueryExecutor) QueryExecutor {
	return &LoggingDecorator{wrappee: e}
}

func (l *LoggingDecorator) Execute(query string, args ...any) (*QueryResult, error) {
	start := time.Now()
	fmt.Printf("[Logging] --> %q\n", query)
	result, err := l.wrappee.Execute(query, args...)
	elapsed := time.Since(start)
	if err != nil {
		fmt.Printf("[Logging] <-- ERROR after %s: %v\n", elapsed, err)
	} else {
		fmt.Printf("[Logging] <-- OK (%d rows) in %s\n", result.Count, elapsed)
	}
	return result, err
}

// CachingDecorator caches results keyed by the raw query string.
type CachingDecorator struct {
	wrappee QueryExecutor
	mu      sync.RWMutex
	cache   map[string]*cachedEntry
	ttl     time.Duration
}

type cachedEntry struct {
	result    *QueryResult
	expiresAt time.Time
}

func WithCaching(e QueryExecutor, ttl time.Duration) QueryExecutor {
	return &CachingDecorator{wrappee: e, cache: make(map[string]*cachedEntry), ttl: ttl}
}

func (c *CachingDecorator) Execute(query string, args ...any) (*QueryResult, error) {
	key := fmt.Sprintf("%s|%v", query, args)

	c.mu.RLock()
	entry, ok := c.cache[key]
	c.mu.RUnlock()

	if ok && time.Now().Before(entry.expiresAt) {
		fmt.Printf("[Cache] HIT for %q\n", query)
		return entry.result, nil
	}

	fmt.Printf("[Cache] MISS for %q\n", query)
	result, err := c.wrappee.Execute(query, args...)
	if err == nil {
		c.mu.Lock()
		c.cache[key] = &cachedEntry{result: result, expiresAt: time.Now().Add(c.ttl)}
		c.mu.Unlock()
	}
	return result, err
}

// CircuitBreakerDecorator stops forwarding requests after consecutive failures.
type CircuitBreakerDecorator struct {
	wrappee     QueryExecutor
	mu          sync.Mutex
	failures    int
	threshold   int
	openUntil   time.Time
	resetAfter  time.Duration
}

func WithCircuitBreaker(e QueryExecutor, threshold int, resetAfter time.Duration) QueryExecutor {
	return &CircuitBreakerDecorator{
		wrappee: e, threshold: threshold, resetAfter: resetAfter,
	}
}

func (cb *CircuitBreakerDecorator) Execute(query string, args ...any) (*QueryResult, error) {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	if time.Now().Before(cb.openUntil) {
		fmt.Printf("[CircuitBreaker] OPEN — rejecting request\n")
		return nil, errors.New("circuit breaker open")
	}

	result, err := cb.wrappee.Execute(query, args...)
	if err != nil {
		cb.failures++
		fmt.Printf("[CircuitBreaker] failure %d/%d\n", cb.failures, cb.threshold)
		if cb.failures >= cb.threshold {
			cb.openUntil = time.Now().Add(cb.resetAfter)
			fmt.Printf("[CircuitBreaker] TRIPPED — open until %s\n", cb.openUntil.Format(time.Kitchen))
		}
		return nil, err
	}

	cb.failures = 0
	return result, nil
}

// ─── Client Code ───────────────────────────────────────────────────────────────

func main() {
	// Compose: DB <- CircuitBreaker <- Cache <- Logging
	executor := WithLogging(
		WithCaching(
			WithCircuitBreaker(
				NewDatabaseExecutor("postgres://localhost:5432/mydb"),
				3,
				30*time.Second,
			),
			10*time.Second,
		),
	)

	query := "SELECT id, name FROM users WHERE active = $1"

	fmt.Println("=== Query 1 (cache miss) ===")
	result, err := executor.Execute(query, true)
	if err == nil {
		fmt.Printf("Got %d rows\n\n", result.Count)
	}

	fmt.Println("=== Query 2 (cache hit) ===")
	result, err = executor.Execute(query, true)
	if err == nil {
		fmt.Printf("Got %d rows\n\n", result.Count)
	}

	fmt.Println("=== Different query (cache miss) ===")
	result, err = executor.Execute("SELECT COUNT(*) FROM orders", nil)
	if err == nil {
		fmt.Printf("Got %d rows\n\n", result.Count)
	}
}
```

---

### PHP

```php
<?php
/**
 * Real-world example: File storage service with pluggable behaviors.
 *
 * Decorators add encryption, compression, and audit logging to a
 * local file storage backend. New backends (S3, GCS) can be dropped in
 * without changing decorator code.
 */

declare(strict_types=1);

// ─── Component Interface ───────────────────────────────────────────────────────

interface StorageService
{
    public function store(string $key, string $content): bool;
    public function retrieve(string $key): string;
    public function delete(string $key): bool;
}

// ─── ConcreteComponent ─────────────────────────────────────────────────────────

class LocalStorageService implements StorageService
{
    private string $baseDir;
    private array $inMemoryStore = []; // Simulate filesystem in memory.

    public function __construct(string $baseDir = '/tmp/storage')
    {
        $this->baseDir = $baseDir;
    }

    public function store(string $key, string $content): bool
    {
        echo "[LocalStorage] Storing '{$key}' (" . strlen($content) . " bytes)\n";
        $this->inMemoryStore[$key] = $content;
        return true;
    }

    public function retrieve(string $key): string
    {
        if (!isset($this->inMemoryStore[$key])) {
            throw new \RuntimeException("Key not found: {$key}");
        }
        echo "[LocalStorage] Retrieving '{$key}'\n";
        return $this->inMemoryStore[$key];
    }

    public function delete(string $key): bool
    {
        unset($this->inMemoryStore[$key]);
        echo "[LocalStorage] Deleted '{$key}'\n";
        return true;
    }
}

// ─── BaseDecorator ─────────────────────────────────────────────────────────────

abstract class StorageDecorator implements StorageService
{
    public function __construct(protected StorageService $wrappee) {}

    public function store(string $key, string $content): bool
    {
        return $this->wrappee->store($key, $content);
    }

    public function retrieve(string $key): string
    {
        return $this->wrappee->retrieve($key);
    }

    public function delete(string $key): bool
    {
        return $this->wrappee->delete($key);
    }
}

// ─── ConcreteDecorators ────────────────────────────────────────────────────────

/**
 * Compresses content using gzip before storing; decompresses on retrieval.
 */
class CompressionStorageDecorator extends StorageDecorator
{
    public function store(string $key, string $content): bool
    {
        $compressed = gzcompress($content, 9);
        echo "[Compression] " . strlen($content) . " bytes -> " . strlen($compressed) . " bytes\n";
        return $this->wrappee->store($key, $compressed);
    }

    public function retrieve(string $key): string
    {
        $compressed = $this->wrappee->retrieve($key);
        return gzuncompress($compressed);
    }
}

/**
 * Encrypts content using AES-256-CBC before storing.
 */
class EncryptionStorageDecorator extends StorageDecorator
{
    private string $key;
    private string $cipher = 'AES-256-CBC';

    public function __construct(StorageService $wrappee, string $passphrase)
    {
        parent::__construct($wrappee);
        // Derive a 256-bit key from the passphrase.
        $this->key = hash('sha256', $passphrase, true);
    }

    public function store(string $key, string $content): bool
    {
        $iv = openssl_random_pseudo_bytes(openssl_cipher_iv_length($this->cipher));
        $encrypted = openssl_encrypt($content, $this->cipher, $this->key, OPENSSL_RAW_DATA, $iv);
        $payload = base64_encode($iv . $encrypted);
        echo "[Encryption] Content encrypted\n";
        return $this->wrappee->store($key, $payload);
    }

    public function retrieve(string $key): string
    {
        $payload = base64_decode($this->wrappee->retrieve($key));
        $ivLength = openssl_cipher_iv_length($this->cipher);
        $iv = substr($payload, 0, $ivLength);
        $encrypted = substr($payload, $ivLength);
        $decrypted = openssl_decrypt($encrypted, $this->cipher, $this->key, OPENSSL_RAW_DATA, $iv);
        echo "[Encryption] Content decrypted\n";
        return $decrypted;
    }
}

/**
 * Writes an audit log entry for every storage operation.
 */
class AuditLogStorageDecorator extends StorageDecorator
{
    private array $auditLog = [];

    public function store(string $key, string $content): bool
    {
        $result = $this->wrappee->store($key, $content);
        $this->log('STORE', $key, $result);
        return $result;
    }

    public function retrieve(string $key): string
    {
        $content = $this->wrappee->retrieve($key);
        $this->log('RETRIEVE', $key, true);
        return $content;
    }

    public function delete(string $key): bool
    {
        $result = $this->wrappee->delete($key);
        $this->log('DELETE', $key, $result);
        return $result;
    }

    public function getAuditLog(): array
    {
        return $this->auditLog;
    }

    private function log(string $operation, string $key, bool $success): void
    {
        $entry = [
            'timestamp' => date('c'),
            'operation' => $operation,
            'key' => $key,
            'success' => $success,
        ];
        $this->auditLog[] = $entry;
        echo "[AuditLog] {$entry['timestamp']} | {$operation} '{$key}' | " . ($success ? 'OK' : 'FAILED') . "\n";
    }
}

// ─── Client Code ───────────────────────────────────────────────────────────────

$backend = new LocalStorageService();

$auditDecorator = new AuditLogStorageDecorator(
    new EncryptionStorageDecorator(
        new CompressionStorageDecorator($backend),
        'super-secret-passphrase'
    )
);

$documentContent = str_repeat("The Decorator pattern is powerful. ", 100);

echo "=== Storing document ===\n";
$auditDecorator->store('documents/report-2025.txt', $documentContent);

echo "\n=== Retrieving document ===\n";
$retrieved = $auditDecorator->retrieve('documents/report-2025.txt');
echo "Content matches: " . ($retrieved === $documentContent ? 'YES' : 'NO') . "\n";

echo "\n=== Deleting document ===\n";
$auditDecorator->delete('documents/report-2025.txt');

echo "\n=== Audit Log ===\n";
foreach ($auditDecorator->getAuditLog() as $entry) {
    printf("  [%s] %s '%s' -> %s\n",
        $entry['timestamp'], $entry['operation'], $entry['key'],
        $entry['success'] ? 'OK' : 'FAILED');
}
```

---

### Ruby

```ruby
# Real-world example: Report generation pipeline.
#
# Decorators apply filtering, sorting, formatting, and export wrapping
# to a base report data source. Decorators are composed at runtime
# based on user preferences.

# ─── Component Interface (via duck typing / module) ───────────────────────────

module ReportSource
  # Returns an array of row hashes.
  def rows
    raise NotImplementedError, "#{self.class}#rows not implemented"
  end

  def column_names
    raise NotImplementedError, "#{self.class}#column_names not implemented"
  end
end

# ─── ConcreteComponent ────────────────────────────────────────────────────────

class SalesDataSource
  include ReportSource

  SAMPLE_DATA = [
    { id: 1, product: "Widget A", region: "North", revenue: 15_200.50, units: 304 },
    { id: 2, product: "Widget B", region: "South", revenue: 8_900.00,  units: 178 },
    { id: 3, product: "Gadget X", region: "North", revenue: 32_100.75, units:  89 },
    { id: 4, product: "Gadget Y", region: "East",  revenue: 4_500.25,  units: 225 },
    { id: 5, product: "Widget A", region: "East",  revenue: 11_750.00, units: 235 },
    { id: 6, product: "Gadget X", region: "West",  revenue: 28_450.00, units:  79 },
  ].freeze

  def rows
    puts "[SalesDataSource] Fetching raw sales data (#{SAMPLE_DATA.size} rows)"
    SAMPLE_DATA.map(&:dup)
  end

  def column_names
    %i[id product region revenue units]
  end
end

# ─── BaseDecorator ────────────────────────────────────────────────────────────

class ReportDecorator
  include ReportSource

  def initialize(wrappee)
    @wrappee = wrappee
  end

  def rows
    @wrappee.rows
  end

  def column_names
    @wrappee.column_names
  end
end

# ─── ConcreteDecorators ───────────────────────────────────────────────────────

# Filters rows by a given column/value predicate.
class FilterDecorator < ReportDecorator
  def initialize(wrappee, column:, value:)
    super(wrappee)
    @column = column
    @value  = value
  end

  def rows
    filtered = @wrappee.rows.select { |row| row[@column].to_s == @value.to_s }
    puts "[FilterDecorator] #{@column}=#{@value}: #{filtered.size} rows remaining"
    filtered
  end
end

# Sorts rows by a column (ascending or descending).
class SortDecorator < ReportDecorator
  def initialize(wrappee, column:, direction: :asc)
    super(wrappee)
    @column    = column
    @direction = direction
  end

  def rows
    sorted = @wrappee.rows.sort_by { |row| row[@column] }
    sorted.reverse! if @direction == :desc
    puts "[SortDecorator] Sorted by #{@column} #{@direction}"
    sorted
  end
end

# Adds a computed :total_per_unit column to each row.
class ComputedColumnsDecorator < ReportDecorator
  def rows
    @wrappee.rows.map do |row|
      row.merge(revenue_per_unit: (row[:revenue] / row[:units]).round(2))
    end
  end

  def column_names
    super + [:revenue_per_unit]
  end
end

# Formats numeric columns for human-readable display.
class FormattingDecorator < ReportDecorator
  def rows
    @wrappee.rows.map do |row|
      row.merge(
        revenue:          format("$%,.2f", row[:revenue]),
        revenue_per_unit: row[:revenue_per_unit] ? format("$%.2f", row[:revenue_per_unit]) : "N/A"
      )
    end
  end
end

# Renders the report as a simple ASCII table.
class AsciiTableDecorator < ReportDecorator
  def render
    data = rows
    cols = column_names
    widths = cols.map { |c| [c.to_s.length, *data.map { |r| r[c].to_s.length }].max }

    separator = widths.map { |w| "-" * (w + 2) }.join("+")
    header    = cols.each_with_index.map { |c, i| " #{c.to_s.ljust(widths[i])} " }.join("|")

    puts "+#{separator}+"
    puts "|#{header}|"
    puts "+#{separator}+"
    data.each do |row|
      line = cols.each_with_index.map { |c, i| " #{row[c].to_s.ljust(widths[i])} " }.join("|")
      puts "|#{line}|"
    end
    puts "+#{separator}+"
    puts "#{data.size} row(s)"
  end
end

# ─── Client Code ─────────────────────────────────────────────────────────────

puts "=== North Region Report — sorted by revenue desc, with computed columns ==="
report =
  AsciiTableDecorator.new(
    FormattingDecorator.new(
      SortDecorator.new(
        ComputedColumnsDecorator.new(
          FilterDecorator.new(
            SalesDataSource.new,
            column: :region,
            value: "North"
          )
        ),
        column: :revenue,
        direction: :desc
      )
    )
  )
puts ""
report.render

puts "\n=== All Products — sorted by units asc (no filter, no formatting) ==="
plain_report =
  AsciiTableDecorator.new(
    SortDecorator.new(
      SalesDataSource.new,
      column: :units,
      direction: :asc
    )
  )
puts ""
plain_report.render
```

---

## When To Use

Use the Decorator pattern when:

- **Runtime behavior extension is needed.** You want to add responsibilities to individual objects dynamically and transparently, without affecting other objects of the same class.
- **Inheritance is impractical.** The number of feature combinations would cause a class explosion (e.g., `LoggedAuthenticatedCachingRetryingHttpClient` as a single subclass).
- **The Open/Closed Principle must be respected.** You want to extend the system by adding new decorators, not by modifying existing classes.
- **Optional features are layered.** Features are optional, independently useful, and can be combined in arbitrary order (e.g., compression + encryption, or encryption alone, or neither).
- **Legacy class behavior needs extending** without access to its source code. Wrapping preserves the existing interface.
- **Middleware pipelines.** HTTP middleware stacks, data stream processors, logging/auditing layers, and permission checks are natural fits.

Do **not** use when:

- The set of behaviors is fixed at design time — a simpler subclass or strategy pattern is cleaner.
- Decorator order matters in complex, hard-to-document ways — the stack can become fragile.
- You need to remove a specific behavior from the middle of the stack at runtime — this requires reconstructing the chain.

---

## Pros & Cons

### Pros

| Benefit | Explanation |
|---|---|
| Extend behavior without subclassing | Attach new behaviors to objects at runtime using composition rather than inheritance. |
| Combine behaviors freely | Any permutation of decorators can be stacked without combinatorial class explosion. |
| Single Responsibility Principle | Each decorator class handles exactly one cross-cutting concern. |
| Open/Closed Principle | New behaviors are added by writing new decorator classes, not modifying existing ones. |
| Runtime flexibility | The same object can be decorated differently across different code paths. |

### Cons

| Drawback | Explanation |
|---|---|
| Hard to remove a specific wrapper | To remove a decorator from the middle of the stack, the entire chain must be reconstructed. |
| Order dependency is implicit | Some behaviors are sensitive to stack order (e.g., compress-then-encrypt vs. encrypt-then-compress), but the interface gives no hint. |
| Many small classes | Each decorator is its own class, which can make the codebase harder to navigate. |
| Ugly initialization code | Deeply nested constructor calls (`new D(new C(new B(new A())))`) can be hard to read; builders or fluent APIs help. |
| Debugging difficulty | A stack trace through 5 layers of decorators is harder to follow than a single class. |

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Adapter** | Adapter changes the interface of an object; Decorator enhances an object while keeping its interface identical. |
| **Composite** | Decorator is a Composite with only one child. Both use recursive composition, but Composite aggregates, while Decorator adds behavior. |
| **Proxy** | Proxy controls access to an object; Decorator adds behavior to it. Proxy usually manages the lifecycle of the service object, while Decorator never does. Both share the same interface as the wrapped object. |
| **Chain of Responsibility** | Both use recursive composition of handlers. In Chain of Responsibility, handlers can break the chain; in Decorator, every decorator calls the next link (no short-circuiting of the core behavior, though a decorator can override the result). |
| **Strategy** | Strategy changes the guts of an object (algorithm), Decorator changes its skin (additional behavior around the same algorithm). They complement each other: a Decorator can wrap an object whose internal strategy is swappable. |

---

## Sources

- https://refactoring.guru/design-patterns/decorator
- https://sourcemaking.com/design_patterns/decorator
