# Factory Method Pattern

**Category:** Creational
**Also Known As:** Virtual Constructor

---

## Intent

Define an interface for creating an object, but let subclasses decide which class to instantiate. Factory Method lets a class defer instantiation to subclasses.

---

## Problem It Solves

A class cannot anticipate the type of objects it must create, or a framework needs to standardize the architectural model for a range of applications while allowing individual applications to define their own domain objects and instantiate them. Specifically:

- A class cannot know ahead of time the exact types and dependencies of the objects it should work with.
- You want subclasses to specify the objects a parent class creates.
- You want to provide users of a library or framework with a way to extend its internal components.
- You want to reuse existing objects rather than rebuilding them each time (e.g., connection pooling), and the selection logic is complex enough to warrant encapsulation.

Without the pattern, you end up with `if/else` or `switch` blocks inside the creator that must be updated every time a new product type is introduced — violating the Open/Closed Principle.

---

## Solution

Introduce a **factory method** — a method whose sole responsibility is to produce product objects. The base Creator class declares this method as abstract (or with a default implementation), and each ConcreteCreator overrides it to return a different type of ConcreteProduct. The rest of the Creator's code calls the factory method wherever it needs a product, so the product type is determined at runtime by whichever subclass is in use.

---

## Structure

```
         ┌───────────────────────────┐
         │       <<abstract>>        │
         │          Creator          │
         │───────────────────────────│
         │ + someOperation(): void   │
         │ + createProduct(): Product│  ← factory method (abstract or default)
         └────────────┬──────────────┘
                      │ inherits
          ┌───────────┴────────────┐
          │                        │
┌─────────▼──────────┐   ┌─────────▼──────────┐
│  ConcreteCreatorA  │   │  ConcreteCreatorB  │
│────────────────────│   │────────────────────│
│ + createProduct()  │   │ + createProduct()  │
│   : Product        │   │   : Product        │
└─────────┬──────────┘   └─────────┬──────────┘
          │ returns                 │ returns
          │                        │
┌─────────▼──────────┐   ┌─────────▼──────────┐
│  ConcreteProductA  │   │  ConcreteProductB  │
│────────────────────│   │────────────────────│
│ + doStuff(): void  │   │ + doStuff(): void  │
└────────────────────┘   └────────────────────┘
          │                        │
          └──────────┬─────────────┘
                     │ implements
          ┌──────────▼─────────────┐
          │   <<interface>>        │
          │       Product          │
          │────────────────────────│
          │ + doStuff(): void      │
          └────────────────────────┘
```

---

## Participants

| Participant | Role |
|---|---|
| **Creator** | Declares the factory method that returns `Product` objects. May provide a default implementation that returns a default `ConcreteProduct`. Calls the factory method to create products in its business logic. |
| **ConcreteCreator** | Overrides the factory method to return a specific `ConcreteProduct` instance. |
| **Product** | Defines the interface common to all objects the factory method can produce. |
| **ConcreteProduct** | Implements the `Product` interface. Created by the corresponding `ConcreteCreator`. |

---

## How It Works

1. The **client** works with a `Creator` reference (usually obtained via dependency injection or configuration).
2. The client calls a method on the `Creator` — this method internally calls `createProduct()` to get the product object it needs.
3. The **factory method** `createProduct()` is overridden in each `ConcreteCreator` to instantiate the appropriate `ConcreteProduct`.
4. The returned object is typed as `Product` (the interface), so the rest of the creator's logic is decoupled from concrete types.
5. To add a new product, you create a new `ConcreteProduct` and a new `ConcreteCreator` — existing code is untouched.

---

## Code Examples

### Python

```python
"""
Real-world example: Cross-platform UI button rendering.
A dialog framework needs to render buttons, but the button type
(Web vs Windows) depends on which platform the dialog runs on.
"""

from __future__ import annotations
from abc import ABC, abstractmethod


# ── Product Interface ────────────────────────────────────────────────────────

class Button(ABC):
    """Common interface for all buttons."""

    @abstractmethod
    def render(self) -> None:
        """Render the button on screen."""

    @abstractmethod
    def on_click(self, handler: callable) -> None:
        """Bind a click handler."""


# ── Concrete Products ────────────────────────────────────────────────────────

class WindowsButton(Button):
    def __init__(self, label: str) -> None:
        self._label = label
        self._handler: callable | None = None

    def render(self) -> None:
        print(f"[Windows] Rendering native Win32 button: <{self._label}>")

    def on_click(self, handler: callable) -> None:
        self._handler = handler
        print(f"[Windows] Bound click handler to Win32 button '{self._label}'")


class WebButton(Button):
    def __init__(self, label: str) -> None:
        self._label = label
        self._handler: callable | None = None

    def render(self) -> None:
        print(f"[Web] Rendering HTML button: <button>{self._label}</button>")

    def on_click(self, handler: callable) -> None:
        self._handler = handler
        print(f"[Web] Bound addEventListener('click') to '{self._label}'")


class MacOSButton(Button):
    def __init__(self, label: str) -> None:
        self._label = label
        self._handler: callable | None = None

    def render(self) -> None:
        print(f"[macOS] Rendering NSButton: [{self._label}]")

    def on_click(self, handler: callable) -> None:
        self._handler = handler
        print(f"[macOS] Bound target-action to NSButton '{self._label}'")


# ── Creator (Abstract) ───────────────────────────────────────────────────────

class Dialog(ABC):
    """
    Creator class.  The factory method `create_button` is abstract; subclasses
    decide which concrete Button to create.  The `render` method uses the
    factory method, so it works with any Button type without knowing specifics.
    """

    @abstractmethod
    def create_button(self, label: str) -> Button:
        """Factory method — override in subclasses."""

    def render(self) -> None:
        """Template method that uses the factory method internally."""
        ok_btn = self.create_button("OK")
        cancel_btn = self.create_button("Cancel")

        ok_btn.render()
        ok_btn.on_click(lambda: print("  -> OK clicked"))

        cancel_btn.render()
        cancel_btn.on_click(lambda: print("  -> Cancel clicked"))


# ── Concrete Creators ────────────────────────────────────────────────────────

class WindowsDialog(Dialog):
    def create_button(self, label: str) -> Button:
        return WindowsButton(label)


class WebDialog(Dialog):
    def create_button(self, label: str) -> Button:
        return WebButton(label)


class MacOSDialog(Dialog):
    def create_button(self, label: str) -> Button:
        return MacOSButton(label)


# ── Client Code ──────────────────────────────────────────────────────────────

def get_dialog(platform: str) -> Dialog:
    """
    In a real application this selection might be driven by environment
    detection, config files, or dependency injection.
    """
    creators = {
        "windows": WindowsDialog,
        "web": WebDialog,
        "macos": MacOSDialog,
    }
    cls = creators.get(platform.lower())
    if cls is None:
        raise ValueError(f"Unknown platform: {platform!r}")
    return cls()


if __name__ == "__main__":
    import sys

    platform = sys.argv[1] if len(sys.argv) > 1 else "web"
    print(f"=== Running on platform: {platform} ===\n")

    dialog = get_dialog(platform)
    dialog.render()
```

---

### Java

```java
/**
 * Real-world example: Payment processor factory.
 * An e-commerce platform supports multiple payment gateways (Stripe, PayPal,
 * Square). Each gateway has different SDK calls, but the order service only
 * depends on the PaymentProcessor interface.
 */
package patterns.factory;

import java.math.BigDecimal;
import java.util.Map;
import java.util.UUID;

// ── Product Interface ────────────────────────────────────────────────────────

interface PaymentProcessor {
    /**
     * Charge the customer and return a transaction ID.
     *
     * @param amount      amount to charge
     * @param currency    ISO 4217 currency code, e.g. "USD"
     * @param token       payment token from the frontend (card nonce, etc.)
     * @return            unique transaction identifier
     */
    String charge(BigDecimal amount, String currency, String token);

    /**
     * Refund a previously captured transaction.
     *
     * @param transactionId the ID returned by {@link #charge}
     * @param amount        partial or full refund amount
     */
    void refund(String transactionId, BigDecimal amount);
}

// ── Concrete Products ────────────────────────────────────────────────────────

class StripeProcessor implements PaymentProcessor {
    private final String apiKey;

    StripeProcessor(String apiKey) {
        this.apiKey = apiKey;
    }

    @Override
    public String charge(BigDecimal amount, String currency, String token) {
        // In production this would call stripe-java SDK
        String txId = "stripe_" + UUID.randomUUID();
        System.out.printf("[Stripe] Charged %s %s via token %s -> txId: %s%n",
                amount, currency, token, txId);
        return txId;
    }

    @Override
    public void refund(String transactionId, String amount) {
        // stripe.refunds.create(...)
        System.out.printf("[Stripe] Refunded %s for txId: %s%n", amount, transactionId);
    }
}

class PayPalProcessor implements PaymentProcessor {
    private final String clientId;
    private final String secret;

    PayPalProcessor(String clientId, String secret) {
        this.clientId = clientId;
        this.secret = secret;
    }

    @Override
    public String charge(BigDecimal amount, String currency, String token) {
        String txId = "pp_" + UUID.randomUUID();
        System.out.printf("[PayPal] Charged %s %s via order token %s -> txId: %s%n",
                amount, currency, token, txId);
        return txId;
    }

    @Override
    public void refund(String transactionId, String amount) {
        System.out.printf("[PayPal] Refunded %s for txId: %s%n", amount, transactionId);
    }
}

class SquareProcessor implements PaymentProcessor {
    private final String locationId;

    SquareProcessor(String locationId) {
        this.locationId = locationId;
    }

    @Override
    public String charge(BigDecimal amount, String currency, String token) {
        String txId = "sq_" + UUID.randomUUID();
        System.out.printf("[Square] Charged %s %s at location %s -> txId: %s%n",
                amount, currency, locationId, txId);
        return txId;
    }

    @Override
    public void refund(String transactionId, String amount) {
        System.out.printf("[Square] Refunded %s for txId: %s%n", amount, transactionId);
    }
}

// ── Creator (Abstract) ───────────────────────────────────────────────────────

abstract class PaymentGateway {
    /** Factory method — subclasses return the appropriate processor. */
    protected abstract PaymentProcessor createProcessor();

    /**
     * High-level operation that uses the factory method.
     * The order service calls this; it never references concrete processors.
     */
    public String processOrder(String orderId, BigDecimal total,
                               String currency, String paymentToken) {
        PaymentProcessor processor = createProcessor();
        System.out.printf("Processing order %s for %s %s%n", orderId, total, currency);
        String txId = processor.charge(total, currency, paymentToken);
        System.out.printf("Order %s committed. Transaction: %s%n", orderId, txId);
        return txId;
    }

    public void issueRefund(String transactionId, BigDecimal amount) {
        PaymentProcessor processor = createProcessor();
        processor.refund(transactionId, amount.toString());
    }
}

// ── Concrete Creators ────────────────────────────────────────────────────────

class StripeGateway extends PaymentGateway {
    private final String apiKey;

    StripeGateway(String apiKey) {
        this.apiKey = apiKey;
    }

    @Override
    protected PaymentProcessor createProcessor() {
        return new StripeProcessor(apiKey);
    }
}

class PayPalGateway extends PaymentGateway {
    private final String clientId;
    private final String secret;

    PayPalGateway(String clientId, String secret) {
        this.clientId = clientId;
        this.secret = secret;
    }

    @Override
    protected PaymentProcessor createProcessor() {
        return new PayPalProcessor(clientId, secret);
    }
}

class SquareGateway extends PaymentGateway {
    private final String locationId;

    SquareGateway(String locationId) {
        this.locationId = locationId;
    }

    @Override
    protected PaymentProcessor createProcessor() {
        return new SquareProcessor(locationId);
    }
}

// ── Client Code ──────────────────────────────────────────────────────────────

public class FactoryMethodDemo {
    /** Reads gateway type from configuration and returns the right creator. */
    static PaymentGateway resolveGateway(String provider, Map<String, String> config) {
        return switch (provider.toLowerCase()) {
            case "stripe"  -> new StripeGateway(config.get("stripe.key"));
            case "paypal"  -> new PayPalGateway(config.get("paypal.clientId"),
                                                config.get("paypal.secret"));
            case "square"  -> new SquareGateway(config.get("square.locationId"));
            default        -> throw new IllegalArgumentException("Unknown provider: " + provider);
        };
    }

    public static void main(String[] args) {
        Map<String, String> config = Map.of(
                "stripe.key",         "sk_test_abc123",
                "paypal.clientId",    "client_xyz",
                "paypal.secret",      "secret_xyz",
                "square.locationId",  "loc_789"
        );

        // Swap the provider string to switch gateways — no other code changes.
        PaymentGateway gateway = resolveGateway("stripe", config);

        String txId = gateway.processOrder("order-001", new BigDecimal("99.99"),
                                           "USD", "tok_visa_4242");
        gateway.issueRefund(txId, new BigDecimal("99.99"));
    }
}
```

---

### C++

```cpp
/**
 * Real-world example: Cross-platform file system logger.
 * A logging subsystem writes log entries to different backends
 * (file on Linux, Windows Event Log, syslog on macOS/Unix).
 * The application code uses LoggerFactory without knowing which
 * concrete logger is created.
 */

#include <iostream>
#include <fstream>
#include <string>
#include <memory>
#include <stdexcept>
#include <chrono>
#include <sstream>

// ── Product Interface ────────────────────────────────────────────────────────

class Logger {
public:
    virtual ~Logger() = default;

    virtual void info(const std::string& message)  = 0;
    virtual void warn(const std::string& message)  = 0;
    virtual void error(const std::string& message) = 0;

protected:
    static std::string timestamp() {
        using namespace std::chrono;
        auto now = system_clock::now();
        auto t   = system_clock::to_time_t(now);
        std::ostringstream oss;
        oss << std::ctime(&t);
        std::string s = oss.str();
        // Remove trailing newline from ctime
        if (!s.empty() && s.back() == '\n') s.pop_back();
        return s;
    }
};

// ── Concrete Products ────────────────────────────────────────────────────────

class FileLogger : public Logger {
public:
    explicit FileLogger(const std::string& path)
        : file_(path, std::ios::app) {
        if (!file_.is_open()) {
            throw std::runtime_error("Cannot open log file: " + path);
        }
    }

    void info(const std::string& msg) override {
        write("INFO ", msg);
    }
    void warn(const std::string& msg) override {
        write("WARN ", msg);
    }
    void error(const std::string& msg) override {
        write("ERROR", msg);
    }

private:
    std::ofstream file_;

    void write(const std::string& level, const std::string& msg) {
        file_ << "[" << timestamp() << "] [" << level << "] " << msg << "\n";
        file_.flush();
    }
};

class ConsoleLogger : public Logger {
public:
    void info(const std::string& msg) override {
        std::cout << "\033[32m[INFO ]\033[0m " << msg << "\n";
    }
    void warn(const std::string& msg) override {
        std::cout << "\033[33m[WARN ]\033[0m " << msg << "\n";
    }
    void error(const std::string& msg) override {
        std::cerr << "\033[31m[ERROR]\033[0m " << msg << "\n";
    }
};

class SyslogLogger : public Logger {
public:
    explicit SyslogLogger(const std::string& app_name)
        : app_name_(app_name) {}

    void info(const std::string& msg) override {
        // Real impl would call ::openlog / ::syslog
        std::cout << "<syslog> " << app_name_ << " INFO: " << msg << "\n";
    }
    void warn(const std::string& msg) override {
        std::cout << "<syslog> " << app_name_ << " WARN: " << msg << "\n";
    }
    void error(const std::string& msg) override {
        std::cout << "<syslog> " << app_name_ << " ERROR: " << msg << "\n";
    }

private:
    std::string app_name_;
};

// ── Creator (Abstract) ───────────────────────────────────────────────────────

class LoggerFactory {
public:
    virtual ~LoggerFactory() = default;

    /** Factory method. */
    virtual std::unique_ptr<Logger> createLogger() = 0;

    /**
     * High-level convenience: log application startup information.
     * Uses the factory method — works with any Logger.
     */
    void logStartup(const std::string& app_name, const std::string& version) {
        auto logger = createLogger();
        logger->info("=== " + app_name + " v" + version + " starting ===");
        logger->info("Logger backend: " + backendName());
    }

    virtual std::string backendName() const = 0;
};

// ── Concrete Creators ────────────────────────────────────────────────────────

class FileLoggerFactory : public LoggerFactory {
public:
    explicit FileLoggerFactory(std::string path) : path_(std::move(path)) {}

    std::unique_ptr<Logger> createLogger() override {
        return std::make_unique<FileLogger>(path_);
    }

    std::string backendName() const override { return "File(" + path_ + ")"; }

private:
    std::string path_;
};

class ConsoleLoggerFactory : public LoggerFactory {
public:
    std::unique_ptr<Logger> createLogger() override {
        return std::make_unique<ConsoleLogger>();
    }
    std::string backendName() const override { return "Console"; }
};

class SyslogLoggerFactory : public LoggerFactory {
public:
    explicit SyslogLoggerFactory(std::string app) : app_name_(std::move(app)) {}

    std::unique_ptr<Logger> createLogger() override {
        return std::make_unique<SyslogLogger>(app_name_);
    }
    std::string backendName() const override { return "Syslog"; }

private:
    std::string app_name_;
};

// ── Client Code ──────────────────────────────────────────────────────────────

std::unique_ptr<LoggerFactory> makeFactory(const std::string& backend) {
    if (backend == "file")    return std::make_unique<FileLoggerFactory>("app.log");
    if (backend == "console") return std::make_unique<ConsoleLoggerFactory>();
    if (backend == "syslog")  return std::make_unique<SyslogLoggerFactory>("my-app");
    throw std::invalid_argument("Unknown backend: " + backend);
}

int main() {
    auto factory = makeFactory("console");
    factory->logStartup("MyApp", "2.4.1");

    auto logger = factory->createLogger();
    logger->info("Connected to database.");
    logger->warn("Disk usage above 80%.");
    logger->error("Failed to send email notification.");

    return 0;
}
```

---

### C#

```csharp
/**
 * Real-world example: Document exporter factory.
 * A reporting module can export reports to PDF, Excel, or CSV.
 * Each format has its own rendering logic, but the Report class
 * only works with the IDocumentExporter interface.
 */

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace DesignPatterns.FactoryMethod
{
    // ── Product Interface ────────────────────────────────────────────────────

    public interface IDocumentExporter
    {
        /// <summary>Export a table of data and return the file path written.</summary>
        string Export(string title, IEnumerable<string[]> rows, string outputDir);
    }

    // ── Concrete Products ────────────────────────────────────────────────────

    public sealed class CsvExporter : IDocumentExporter
    {
        public string Export(string title, IEnumerable<string[]> rows, string outputDir)
        {
            string path = Path.Combine(outputDir, $"{Sanitize(title)}.csv");
            using var writer = new StreamWriter(path, append: false, Encoding.UTF8);

            writer.WriteLine($"# {title}");
            foreach (var row in rows)
                writer.WriteLine(string.Join(",", row));

            Console.WriteLine($"[CSV] Written to: {path}");
            return path;
        }
    }

    public sealed class ExcelExporter : IDocumentExporter
    {
        public string Export(string title, IEnumerable<string[]> rows, string outputDir)
        {
            // Real implementation would use ClosedXML or EPPlus
            string path = Path.Combine(outputDir, $"{Sanitize(title)}.xlsx");
            Console.WriteLine($"[Excel] Would write workbook to: {path}");
            Console.WriteLine($"[Excel] Sheet name: {title}");
            foreach (var row in rows)
                Console.WriteLine($"  Row: {string.Join(" | ", row)}");
            return path;
        }
    }

    public sealed class PdfExporter : IDocumentExporter
    {
        public string Export(string title, IEnumerable<string[]> rows, string outputDir)
        {
            // Real implementation would use iTextSharp or PdfSharp
            string path = Path.Combine(outputDir, $"{Sanitize(title)}.pdf");
            Console.WriteLine($"[PDF] Would render PDF to: {path}");
            Console.WriteLine($"[PDF] Title: {title}");
            return path;
        }
    }

    // ── Creator (Abstract) ───────────────────────────────────────────────────

    public abstract class ReportExporterFactory
    {
        /// <summary>Factory method — override to return a concrete exporter.</summary>
        protected abstract IDocumentExporter CreateExporter();

        /// <summary>
        /// Template method: validates output directory, then delegates
        /// the actual export to whichever exporter the subclass creates.
        /// </summary>
        public string ExportReport(string title, IEnumerable<string[]> rows,
                                    string outputDir = ".")
        {
            if (!Directory.Exists(outputDir))
                Directory.CreateDirectory(outputDir);

            Console.WriteLine($"\nExporting report: \"{title}\"");
            IDocumentExporter exporter = CreateExporter();
            return exporter.Export(title, rows, outputDir);
        }
    }

    // ── Concrete Creators ────────────────────────────────────────────────────

    public sealed class CsvReportFactory : ReportExporterFactory
    {
        protected override IDocumentExporter CreateExporter() => new CsvExporter();
    }

    public sealed class ExcelReportFactory : ReportExporterFactory
    {
        protected override IDocumentExporter CreateExporter() => new ExcelExporter();
    }

    public sealed class PdfReportFactory : ReportExporterFactory
    {
        protected override IDocumentExporter CreateExporter() => new PdfExporter();
    }

    // ── Helper ───────────────────────────────────────────────────────────────

    static file class StringExt
    {
        internal static string Sanitize(string s) =>
            string.Concat(s.Split(Path.GetInvalidFileNameChars()));
    }

    // ── Client Code ──────────────────────────────────────────────────────────

    public static class Program
    {
        public static void Main(string[] args)
        {
            var salesData = new List<string[]>
            {
                new[] { "Region",  "Q1",    "Q2",    "Q3",    "Q4"    },
                new[] { "North",   "12000", "15300", "13400", "17800" },
                new[] { "South",   "9800",  "10200", "11000", "12500" },
                new[] { "East",    "14000", "13700", "15600", "16900" },
                new[] { "West",    "11200", "11900", "12800", "14100" },
            };

            // Swap factory to change output format — client code unchanged
            ReportExporterFactory factory = args.Length > 0
                ? args[0] switch
                {
                    "excel" => new ExcelReportFactory(),
                    "pdf"   => new PdfReportFactory(),
                    _       => new CsvReportFactory(),
                }
                : new CsvReportFactory();

            string outputPath = factory.ExportReport(
                title: "Annual Sales Report 2025",
                rows: salesData,
                outputDir: Path.GetTempPath()
            );

            Console.WriteLine($"Report saved to: {outputPath}");
        }
    }
}

file static class Sanitize
{
    public static string Sanitize(string title) =>
        string.Concat(title.Split(Path.GetInvalidFileNameChars()));
}
```

---

### TypeScript

```typescript
/**
 * Real-world example: Notification sender factory.
 * A notification service must send alerts via Email, SMS, or Push
 * depending on user preferences. Each channel has its own SDK/API.
 */

// ── Product Interface ────────────────────────────────────────────────────────

interface NotificationResult {
  channel: string;
  recipient: string;
  messageId: string;
  sentAt: Date;
}

interface NotificationSender {
  send(recipient: string, subject: string, body: string): Promise<NotificationResult>;
}

// ── Concrete Products ────────────────────────────────────────────────────────

class EmailSender implements NotificationSender {
  constructor(
    private readonly smtpHost: string,
    private readonly fromAddress: string
  ) {}

  async send(recipient: string, subject: string, body: string): Promise<NotificationResult> {
    // Real impl: nodemailer / AWS SES / SendGrid SDK call
    const messageId = `email-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    console.log(`[Email] SMTP(${this.smtpHost}) from ${this.fromAddress}`);
    console.log(`  To: ${recipient}`);
    console.log(`  Subject: ${subject}`);
    console.log(`  Body: ${body.slice(0, 60)}...`);
    return { channel: "email", recipient, messageId, sentAt: new Date() };
  }
}

class SmsSender implements NotificationSender {
  constructor(
    private readonly apiKey: string,
    private readonly fromNumber: string
  ) {}

  async send(recipient: string, _subject: string, body: string): Promise<NotificationResult> {
    // Real impl: Twilio / Vonage SDK call
    const messageId = `sms-${Date.now()}`;
    console.log(`[SMS] From ${this.fromNumber} to ${recipient}`);
    console.log(`  Message: ${body.slice(0, 160)}`);
    return { channel: "sms", recipient, messageId, sentAt: new Date() };
  }
}

class PushSender implements NotificationSender {
  constructor(private readonly fcmServerKey: string) {}

  async send(recipient: string, subject: string, body: string): Promise<NotificationResult> {
    // Real impl: Firebase Admin SDK
    const messageId = `push-${Date.now()}`;
    console.log(`[Push] FCM to device token ${recipient.slice(0, 12)}...`);
    console.log(`  Title: ${subject}`);
    console.log(`  Body: ${body.slice(0, 100)}`);
    return { channel: "push", recipient, messageId, sentAt: new Date() };
  }
}

// ── Creator (Abstract) ───────────────────────────────────────────────────────

abstract class NotificationChannel {
  /** Factory method — subclasses return the appropriate sender. */
  protected abstract createSender(): NotificationSender;

  /**
   * High-level operation: validates input and delegates to the sender.
   * Never references a concrete class.
   */
  async notify(
    recipient: string,
    subject: string,
    body: string
  ): Promise<NotificationResult> {
    if (!recipient) throw new Error("Recipient must not be empty.");
    if (!body)      throw new Error("Notification body must not be empty.");

    const sender = this.createSender();
    const result = await sender.send(recipient, subject, body);

    console.log(`\nNotification sent [${result.channel}] messageId=${result.messageId}`);
    return result;
  }
}

// ── Concrete Creators ────────────────────────────────────────────────────────

class EmailChannel extends NotificationChannel {
  constructor(private smtpHost: string, private from: string) {
    super();
  }
  protected createSender(): NotificationSender {
    return new EmailSender(this.smtpHost, this.from);
  }
}

class SmsChannel extends NotificationChannel {
  constructor(private apiKey: string, private fromNumber: string) {
    super();
  }
  protected createSender(): NotificationSender {
    return new SmsSender(this.apiKey, this.fromNumber);
  }
}

class PushChannel extends NotificationChannel {
  constructor(private fcmKey: string) {
    super();
  }
  protected createSender(): NotificationSender {
    return new PushSender(this.fcmKey);
  }
}

// ── Client Code ──────────────────────────────────────────────────────────────

type ChannelType = "email" | "sms" | "push";

function buildChannel(type: ChannelType): NotificationChannel {
  switch (type) {
    case "email":
      return new EmailChannel("smtp.example.com", "noreply@example.com");
    case "sms":
      return new SmsChannel("twilio_key_xyz", "+15550001111");
    case "push":
      return new PushChannel("fcm_server_key_abc");
    default:
      throw new Error(`Unsupported channel: ${type}`);
  }
}

(async () => {
  const channelType: ChannelType = (process.argv[2] as ChannelType) ?? "email";
  const channel = buildChannel(channelType);

  await channel.notify(
    channelType === "email" ? "alice@example.com"
    : channelType === "sms" ? "+15559876543"
    : "device_token_abc123def456",
    "Your order has shipped",
    "Great news! Your order #ORD-20251209 has been shipped and will arrive by Thursday."
  );
})();
```

---

### Go

```go
// Real-world example: Database connection factory.
// An application supports PostgreSQL, MySQL, and SQLite.
// The repository layer works only with the DB interface;
// the concrete driver is chosen at startup from configuration.

package main

import (
	"errors"
	"fmt"
	"time"
)

// ── Product Interface ────────────────────────────────────────────────────────

// DB represents a generic database connection.
type DB interface {
	Query(sql string, args ...any) ([]map[string]any, error)
	Execute(sql string, args ...any) (int64, error)
	Close() error
	DriverName() string
}

// ── Concrete Products ────────────────────────────────────────────────────────

// PostgresDB simulates a PostgreSQL connection.
type PostgresDB struct {
	dsn    string
	closed bool
}

func (p *PostgresDB) Query(sql string, args ...any) ([]map[string]any, error) {
	if p.closed {
		return nil, errors.New("connection closed")
	}
	fmt.Printf("[Postgres] QUERY: %s args=%v\n", sql, args)
	// Simulated result set
	return []map[string]any{{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}}, nil
}

func (p *PostgresDB) Execute(sql string, args ...any) (int64, error) {
	if p.closed {
		return 0, errors.New("connection closed")
	}
	fmt.Printf("[Postgres] EXEC: %s args=%v\n", sql, args)
	return 1, nil
}

func (p *PostgresDB) Close() error {
	p.closed = true
	fmt.Println("[Postgres] Connection closed.")
	return nil
}

func (p *PostgresDB) DriverName() string { return "postgres" }

// MySQLDB simulates a MySQL connection.
type MySQLDB struct {
	dsn    string
	closed bool
}

func (m *MySQLDB) Query(sql string, args ...any) ([]map[string]any, error) {
	if m.closed {
		return nil, errors.New("connection closed")
	}
	fmt.Printf("[MySQL] QUERY: %s args=%v\n", sql, args)
	return []map[string]any{{"id": 10, "email": "carol@example.com"}}, nil
}

func (m *MySQLDB) Execute(sql string, args ...any) (int64, error) {
	if m.closed {
		return 0, errors.New("connection closed")
	}
	fmt.Printf("[MySQL] EXEC: %s args=%v\n", sql, args)
	return 1, nil
}

func (m *MySQLDB) Close() error {
	m.closed = true
	fmt.Println("[MySQL] Connection closed.")
	return nil
}

func (m *MySQLDB) DriverName() string { return "mysql" }

// SQLiteDB simulates an in-process SQLite connection.
type SQLiteDB struct {
	filePath string
	closed   bool
}

func (s *SQLiteDB) Query(sql string, args ...any) ([]map[string]any, error) {
	if s.closed {
		return nil, errors.New("connection closed")
	}
	fmt.Printf("[SQLite] QUERY: %s args=%v\n", sql, args)
	return []map[string]any{{"setting": "theme", "value": "dark"}}, nil
}

func (s *SQLiteDB) Execute(sql string, args ...any) (int64, error) {
	if s.closed {
		return 0, errors.New("connection closed")
	}
	fmt.Printf("[SQLite] EXEC: %s args=%v\n", sql, args)
	return 1, nil
}

func (s *SQLiteDB) Close() error {
	s.closed = true
	fmt.Println("[SQLite] File handle released.")
	return nil
}

func (s *SQLiteDB) DriverName() string { return "sqlite3" }

// ── Creator (Abstract via struct embedding) ──────────────────────────────────

// DBFactory defines the factory method interface.
// In Go, we favour an interface for the creator role rather than
// embedding a base struct, as it is idiomatic.
type DBFactory interface {
	// CreateDB is the factory method — returns a ready-to-use DB connection.
	CreateDB() (DB, error)
	// DriverName exposes which driver this factory targets.
	DriverName() string
}

// BaseFactory holds the retry/timeout logic shared by all concrete factories.
type BaseFactory struct {
	MaxRetries int
	Timeout    time.Duration
}

func (b *BaseFactory) openWithRetry(open func() (DB, error)) (DB, error) {
	var (
		db  DB
		err error
	)
	for attempt := 1; attempt <= b.MaxRetries; attempt++ {
		db, err = open()
		if err == nil {
			return db, nil
		}
		fmt.Printf("  attempt %d/%d failed: %v\n", attempt, b.MaxRetries, err)
		time.Sleep(50 * time.Millisecond)
	}
	return nil, fmt.Errorf("all %d attempts failed: %w", b.MaxRetries, err)
}

// ── Concrete Creators ────────────────────────────────────────────────────────

type PostgresFactory struct {
	BaseFactory
	DSN string
}

func (f *PostgresFactory) CreateDB() (DB, error) {
	return f.openWithRetry(func() (DB, error) {
		fmt.Printf("[PostgresFactory] Opening connection to %s\n", f.DSN)
		return &PostgresDB{dsn: f.DSN}, nil
	})
}

func (f *PostgresFactory) DriverName() string { return "postgres" }

type MySQLFactory struct {
	BaseFactory
	DSN string
}

func (f *MySQLFactory) CreateDB() (DB, error) {
	return f.openWithRetry(func() (DB, error) {
		fmt.Printf("[MySQLFactory] Opening connection to %s\n", f.DSN)
		return &MySQLDB{dsn: f.DSN}, nil
	})
}

func (f *MySQLFactory) DriverName() string { return "mysql" }

type SQLiteFactory struct {
	BaseFactory
	FilePath string
}

func (f *SQLiteFactory) CreateDB() (DB, error) {
	return f.openWithRetry(func() (DB, error) {
		fmt.Printf("[SQLiteFactory] Opening file %s\n", f.FilePath)
		return &SQLiteDB{filePath: f.FilePath}, nil
	})
}

func (f *SQLiteFactory) DriverName() string { return "sqlite3" }

// ── Repository that uses any DB ──────────────────────────────────────────────

type UserRepository struct {
	db DB
}

func NewUserRepository(factory DBFactory) (*UserRepository, error) {
	db, err := factory.CreateDB()
	if err != nil {
		return nil, fmt.Errorf("UserRepository: %w", err)
	}
	fmt.Printf("UserRepository ready (driver=%s)\n\n", factory.DriverName())
	return &UserRepository{db: db}, nil
}

func (r *UserRepository) FindAll() ([]map[string]any, error) {
	return r.db.Query("SELECT id, name FROM users")
}

func (r *UserRepository) Save(name string) (int64, error) {
	return r.db.Execute("INSERT INTO users (name) VALUES (?)", name)
}

func (r *UserRepository) Close() error { return r.db.Close() }

// ── Client Code ──────────────────────────────────────────────────────────────

func resolveFactory(driver string) (DBFactory, error) {
	base := BaseFactory{MaxRetries: 3, Timeout: 5 * time.Second}
	switch driver {
	case "postgres":
		return &PostgresFactory{BaseFactory: base, DSN: "postgres://localhost:5432/app"}, nil
	case "mysql":
		return &MySQLFactory{BaseFactory: base, DSN: "root:@tcp(localhost:3306)/app"}, nil
	case "sqlite", "sqlite3":
		return &SQLiteFactory{BaseFactory: base, FilePath: "./app.db"}, nil
	default:
		return nil, fmt.Errorf("unsupported driver: %q", driver)
	}
}

func main() {
	driver := "postgres" // could come from env var or config file

	factory, err := resolveFactory(driver)
	if err != nil {
		panic(err)
	}

	repo, err := NewUserRepository(factory)
	if err != nil {
		panic(err)
	}
	defer repo.Close()

	// Repository code never changes regardless of which DB is underneath.
	users, _ := repo.FindAll()
	fmt.Println("Users:", users)

	affected, _ := repo.Save("Charlie")
	fmt.Println("Rows affected:", affected)
}
```

---

### PHP

```php
<?php
/**
 * Real-world example: Storage adapter factory.
 * A file-upload service must support storing files locally (dev),
 * in AWS S3 (production), and in Google Cloud Storage (optional).
 * Controllers depend only on StorageAdapter; the factory decides the backend.
 */

declare(strict_types=1);

// ── Product Interface ────────────────────────────────────────────────────────

interface StorageAdapter
{
    /**
     * Store content under the given key and return the public URL.
     *
     * @param  string $key      Path/filename, e.g. "uploads/avatar.jpg"
     * @param  string $content  File contents (binary safe)
     * @param  array  $metadata Optional metadata (content-type, acl, etc.)
     * @return string           Public or pre-signed URL
     */
    public function put(string $key, string $content, array $metadata = []): string;

    /**
     * Retrieve the contents of a stored object.
     */
    public function get(string $key): string;

    /**
     * Delete a stored object.
     */
    public function delete(string $key): void;

    /**
     * Check whether a key exists.
     */
    public function exists(string $key): bool;
}

// ── Concrete Products ────────────────────────────────────────────────────────

final class LocalDiskAdapter implements StorageAdapter
{
    public function __construct(private readonly string $basePath) {}

    public function put(string $key, string $content, array $metadata = []): string
    {
        $fullPath = $this->resolvePath($key);
        $dir = dirname($fullPath);
        if (!is_dir($dir)) {
            mkdir($dir, 0755, recursive: true);
        }
        file_put_contents($fullPath, $content);
        echo "[LocalDisk] Written to {$fullPath}\n";
        return "file://{$fullPath}";
    }

    public function get(string $key): string
    {
        $fullPath = $this->resolvePath($key);
        if (!file_exists($fullPath)) {
            throw new \RuntimeException("File not found: {$key}");
        }
        return file_get_contents($fullPath);
    }

    public function delete(string $key): void
    {
        $fullPath = $this->resolvePath($key);
        if (file_exists($fullPath)) {
            unlink($fullPath);
        }
        echo "[LocalDisk] Deleted {$fullPath}\n";
    }

    public function exists(string $key): bool
    {
        return file_exists($this->resolvePath($key));
    }

    private function resolvePath(string $key): string
    {
        return rtrim($this->basePath, '/') . '/' . ltrim($key, '/');
    }
}

final class S3Adapter implements StorageAdapter
{
    public function __construct(
        private readonly string $bucket,
        private readonly string $region,
        private readonly string $accessKey,
        private readonly string $secretKey
    ) {}

    public function put(string $key, string $content, array $metadata = []): string
    {
        // Real impl: Aws\S3\S3Client->putObject(...)
        $url = "https://{$this->bucket}.s3.{$this->region}.amazonaws.com/{$key}";
        $size = strlen($content);
        echo "[S3] PUT s3://{$this->bucket}/{$key} ({$size} bytes)\n";
        echo "[S3] Metadata: " . json_encode($metadata) . "\n";
        return $url;
    }

    public function get(string $key): string
    {
        // Real impl: S3Client->getObject(...)
        echo "[S3] GET s3://{$this->bucket}/{$key}\n";
        return ""; // simulated
    }

    public function delete(string $key): void
    {
        echo "[S3] DELETE s3://{$this->bucket}/{$key}\n";
    }

    public function exists(string $key): bool
    {
        echo "[S3] HEAD s3://{$this->bucket}/{$key}\n";
        return false; // simulated
    }
}

final class GcsAdapter implements StorageAdapter
{
    public function __construct(
        private readonly string $bucket,
        private readonly string $keyFilePath
    ) {}

    public function put(string $key, string $content, array $metadata = []): string
    {
        // Real impl: Google\Cloud\Storage\StorageClient->bucket(...)->upload(...)
        $url = "https://storage.googleapis.com/{$this->bucket}/{$key}";
        $size = strlen($content);
        echo "[GCS] Uploading {$key} ({$size} bytes) to gs://{$this->bucket}\n";
        return $url;
    }

    public function get(string $key): string
    {
        echo "[GCS] Downloading gs://{$this->bucket}/{$key}\n";
        return "";
    }

    public function delete(string $key): void
    {
        echo "[GCS] Deleting gs://{$this->bucket}/{$key}\n";
    }

    public function exists(string $key): bool
    {
        echo "[GCS] Checking gs://{$this->bucket}/{$key}\n";
        return false;
    }
}

// ── Creator (Abstract) ───────────────────────────────────────────────────────

abstract class StorageFactory
{
    /** Factory method. */
    abstract protected function createAdapter(): StorageAdapter;

    /**
     * High-level method used by controllers.
     * Handles validation and delegates storage to the adapter.
     */
    public function storeUpload(string $originalName, string $content): string
    {
        if (empty($content)) {
            throw new \InvalidArgumentException("Cannot store empty content.");
        }

        // Sanitise the filename
        $safeName = preg_replace('/[^a-zA-Z0-9._-]/', '_', $originalName);
        $key = sprintf('uploads/%s/%s', date('Y/m'), $safeName);

        $adapter = $this->createAdapter();
        $url = $adapter->put($key, $content, [
            'ContentType'  => mime_content_type_from_name($originalName) ?? 'application/octet-stream',
            'CacheControl' => 'public, max-age=31536000',
        ]);

        echo "Stored upload. Public URL: {$url}\n";
        return $url;
    }
}

/** Helper to guess MIME from filename (simplified). */
function mime_content_type_from_name(string $name): ?string
{
    $ext = strtolower(pathinfo($name, PATHINFO_EXTENSION));
    return match ($ext) {
        'jpg', 'jpeg' => 'image/jpeg',
        'png'         => 'image/png',
        'gif'         => 'image/gif',
        'pdf'         => 'application/pdf',
        'txt'         => 'text/plain',
        default       => null,
    };
}

// ── Concrete Creators ────────────────────────────────────────────────────────

final class LocalStorageFactory extends StorageFactory
{
    public function __construct(private readonly string $basePath = '/tmp/uploads') {}

    protected function createAdapter(): StorageAdapter
    {
        return new LocalDiskAdapter($this->basePath);
    }
}

final class S3StorageFactory extends StorageFactory
{
    public function __construct(
        private readonly string $bucket,
        private readonly string $region    = 'us-east-1',
        private readonly string $accessKey = '',
        private readonly string $secretKey = ''
    ) {}

    protected function createAdapter(): StorageAdapter
    {
        return new S3Adapter($this->bucket, $this->region, $this->accessKey, $this->secretKey);
    }
}

final class GcsStorageFactory extends StorageFactory
{
    public function __construct(
        private readonly string $bucket,
        private readonly string $keyFilePath = '/etc/gcp/key.json'
    ) {}

    protected function createAdapter(): StorageAdapter
    {
        return new GcsAdapter($this->bucket, $this->keyFilePath);
    }
}

// ── Client Code ──────────────────────────────────────────────────────────────

function buildStorageFactory(string $driver): StorageFactory
{
    return match ($driver) {
        'local' => new LocalStorageFactory('/tmp/myapp'),
        's3'    => new S3StorageFactory('my-production-bucket', 'eu-west-1'),
        'gcs'   => new GcsStorageFactory('my-gcs-bucket'),
        default => throw new \InvalidArgumentException("Unknown driver: {$driver}"),
    };
}

$driver  = $_ENV['STORAGE_DRIVER'] ?? 'local';
$factory = buildStorageFactory($driver);

echo "=== Storage driver: {$driver} ===\n\n";

// Simulate a file upload — this code never changes regardless of driver.
$url = $factory->storeUpload('profile-photo.jpg', str_repeat("\xFF\xD8", 512));
```

---

### Ruby

```ruby
# Real-world example: Authentication strategy factory.
# A web application supports multiple OAuth providers (GitHub, Google, Twitter).
# Each provider has its own token exchange and user info endpoints.
# The SessionController works only with the AuthStrategy interface.

# ── Product Interface (duck-typed, explicit contract via raise) ──────────────

module AuthStrategy
  # Exchange the authorization code for an access token.
  # @param code [String] OAuth2 authorization code
  # @return [String] access_token
  def exchange_code(code)
    raise NotImplementedError, "#{self.class}#exchange_code is not implemented"
  end

  # Fetch the authenticated user's profile.
  # @param access_token [String]
  # @return [Hash] with at minimum :uid, :name, :email
  def fetch_user(access_token)
    raise NotImplementedError, "#{self.class}#fetch_user is not implemented"
  end

  # Human-readable provider name.
  def provider_name
    raise NotImplementedError, "#{self.class}#provider_name is not implemented"
  end
end

# ── Concrete Products ────────────────────────────────────────────────────────

class GitHubStrategy
  include AuthStrategy

  def initialize(client_id:, client_secret:)
    @client_id     = client_id
    @client_secret = client_secret
  end

  def exchange_code(code)
    # Real impl: POST https://github.com/login/oauth/access_token
    puts "[GitHub] Exchanging code #{code[0, 8]}... for access token"
    "gho_#{SecureRandom.hex(20)}"
  end

  def fetch_user(access_token)
    # Real impl: GET https://api.github.com/user  (Authorization: token ...)
    puts "[GitHub] Fetching user profile with token #{access_token[0, 12]}..."
    { uid: "gh_#{rand(100_000)}", name: "Octocat", email: "octocat@github.com", login: "octocat" }
  end

  def provider_name = "github"
end

class GoogleStrategy
  include AuthStrategy

  def initialize(client_id:, client_secret:, redirect_uri:)
    @client_id     = client_id
    @client_secret = client_secret
    @redirect_uri  = redirect_uri
  end

  def exchange_code(code)
    # Real impl: POST https://oauth2.googleapis.com/token
    puts "[Google] Exchanging code #{code[0, 8]}... for access token"
    "ya29.#{SecureRandom.hex(40)}"
  end

  def fetch_user(access_token)
    # Real impl: GET https://www.googleapis.com/oauth2/v3/userinfo
    puts "[Google] Fetching user info with token #{access_token[0, 12]}..."
    { uid: "google_#{rand(1_000_000)}", name: "Jane Doe", email: "jane@gmail.com" }
  end

  def provider_name = "google"
end

class TwitterStrategy
  include AuthStrategy

  def initialize(api_key:, api_secret:)
    @api_key    = api_key
    @api_secret = api_secret
  end

  def exchange_code(code)
    # Real impl: OAuth 1.0a or OAuth 2.0 PKCE
    puts "[Twitter] Exchanging PKCE code #{code[0, 8]}..."
    "AAAA#{SecureRandom.hex(30)}"
  end

  def fetch_user(access_token)
    # Real impl: GET https://api.twitter.com/2/users/me
    puts "[Twitter] Fetching user via v2 API..."
    { uid: "tw_#{rand(10_000_000)}", name: "Elon Musk", email: nil, username: "@elon" }
  end

  def provider_name = "twitter"
end

# ── Creator (Abstract) ───────────────────────────────────────────────────────

class OAuthHandler
  # Factory method — subclasses override this.
  def create_strategy
    raise NotImplementedError, "#{self.class}#create_strategy must be implemented"
  end

  # High-level: full OAuth callback flow.
  # @param code    [String] Authorization code from the provider's redirect
  # @param session [Hash]   Mutable session hash (simulates Rails session)
  # @return [Hash] the user attributes
  def handle_callback(code:, session: {})
    raise ArgumentError, "code must not be blank" if code.to_s.strip.empty?

    strategy = create_strategy

    puts "\n=== OAuth callback via #{strategy.provider_name} ==="
    access_token = strategy.exchange_code(code)
    user         = strategy.fetch_user(access_token)

    # Persist in session (framework-agnostic)
    session[:user_id]       = user[:uid]
    session[:provider]      = strategy.provider_name
    session[:access_token]  = access_token

    puts "Authenticated: #{user[:name]} (#{user[:email] || "no email"}) [#{strategy.provider_name}]"
    user
  end
end

# ── Concrete Creators ────────────────────────────────────────────────────────

class GitHubOAuthHandler < OAuthHandler
  def initialize(client_id:, client_secret:)
    @client_id     = client_id
    @client_secret = client_secret
  end

  def create_strategy
    GitHubStrategy.new(client_id: @client_id, client_secret: @client_secret)
  end
end

class GoogleOAuthHandler < OAuthHandler
  def initialize(client_id:, client_secret:, redirect_uri:)
    @client_id     = client_id
    @client_secret = client_secret
    @redirect_uri  = redirect_uri
  end

  def create_strategy
    GoogleStrategy.new(client_id: @client_id, client_secret: @client_secret,
                       redirect_uri: @redirect_uri)
  end
end

class TwitterOAuthHandler < OAuthHandler
  def initialize(api_key:, api_secret:)
    @api_key    = api_key
    @api_secret = api_secret
  end

  def create_strategy
    TwitterStrategy.new(api_key: @api_key, api_secret: @api_secret)
  end
end

# ── Client Code ──────────────────────────────────────────────────────────────

require "securerandom"

def build_handler(provider)
  case provider.to_sym
  when :github
    GitHubOAuthHandler.new(client_id: "gh_client_id", client_secret: "gh_secret")
  when :google
    GoogleOAuthHandler.new(client_id: "google_client_id", client_secret: "google_secret",
                           redirect_uri: "https://app.example.com/auth/google/callback")
  when :twitter
    TwitterOAuthHandler.new(api_key: "tw_api_key", api_secret: "tw_api_secret")
  else
    raise ArgumentError, "Unknown provider: #{provider}"
  end
end

# Simulate an incoming OAuth callback from the browser
provider = ARGV[0]&.to_sym || :github
handler  = build_handler(provider)
session  = {}
user     = handler.handle_callback(code: "oauth_code_#{SecureRandom.hex(8)}", session: session)

puts "\nSession state: #{session.reject { |k, _| k == :access_token }}"
puts "User profile:  #{user}"
```

---

## When To Use

Use the Factory Method pattern when:

1. **You do not know beforehand the exact types of objects your code must work with.** The factory method separates product construction from the code that uses the product, making it easy to extend independently.

2. **You want to provide users of a library or framework a way to extend its internal components.** Users subclass the creator and override the factory method to plug in their own product implementations without modifying framework source.

3. **You want to conserve system resources by reusing existing objects instead of rebuilding them each time.** Place pooling or caching logic inside the factory method — callers never know whether they received a fresh or recycled instance.

4. **You need to decouple product creation from the product's consumers** to satisfy the Dependency Inversion Principle and make unit testing easier (inject a mock creator).

5. **A base class wants to delegate the creation responsibility entirely to its subclasses,** especially useful when the base class contains non-trivial business logic that should not be duplicated in each subclass.

---

## Pros & Cons

### Pros

| | Benefit |
|---|---|
| **Decoupling** | Avoids tight coupling between the creator and its concrete products. The creator depends only on the product interface. |
| **Single Responsibility Principle** | Product creation code is centralised in one place (the factory method), making it easy to maintain. |
| **Open/Closed Principle** | New product types can be introduced without breaking existing creator code — just add a new subclass pair. |
| **Testability** | Creators can be replaced with test doubles; product instantiation is intercepted without touching client code. |
| **Composition over inheritance alternative** | When combined with dependency injection, you can pass factory lambdas/objects instead of subclassing. |

### Cons

| | Drawback |
|---|---|
| **Class proliferation** | Every new product variant requires a new ConcreteProduct *and* a new ConcreteCreator, which can bloat a codebase. |
| **Inheritance required** | The pattern relies on subclassing the creator; languages without inheritance (e.g., Go) need alternative idioms (interfaces + constructor functions). |
| **Indirection** | Tracing the exact type that is instantiated requires navigating the class hierarchy, which can be confusing for new contributors. |

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Abstract Factory** | Abstract Factory is often implemented using a collection of Factory Methods. Abstract Factory deals with *families* of related products; Factory Method handles a *single* product. If your factory has more than one creation method, it may be evolving into an Abstract Factory. |
| **Template Method** | Factory Method is a specialisation of Template Method. The factory method is a hook that subclasses override as part of the parent's template algorithm. In fact, "Template Method + factory hook = Factory Method pattern". |
| **Prototype** | Prototype can replace Factory Method when the cost of subclassing creators is too high. Rather than creating a subclass, you clone a registered prototype and customise it. The two patterns are not mutually exclusive. |

---

## Sources

- https://refactoring.guru/design-patterns/factory-method
- https://sourcemaking.com/design_patterns/factory_method
