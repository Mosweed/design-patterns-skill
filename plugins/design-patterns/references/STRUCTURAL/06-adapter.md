# Adapter Pattern

**Category:** Structural
**Also known as:** Wrapper

---

## Intent

The Adapter pattern converts the interface of a class into another interface that clients expect. It allows classes with incompatible interfaces to work together by wrapping one of the classes in an adapter that translates calls between the two interfaces.

---

## Problem It Solves

You have an existing class (or a third-party library) that does exactly what you need, but its interface does not match what the rest of your code expects. Changing the existing class is not an option — it may be:

- Part of a third-party library you do not control.
- Used by many other parts of the system, so changing it would break them.
- A legacy component that is too risky to modify.

**Concrete example:** Your application works with data in JSON format. You need to integrate an analytics library that only accepts XML. You cannot change the analytics library. Without an adapter, you are stuck.

---

## Solution

Create an **Adapter** class that:

1. Implements the interface your client already expects (the *Target* interface).
2. Holds a reference to the incompatible object (the *Adaptee*).
3. Inside each method required by the Target interface, translates the call into whatever the Adaptee understands and delegates to it.

The client never knows it is talking to an adapter — it only sees the Target interface it expects.

---

## Structure (ASCII diagram)

```
┌──────────┐        uses        ┌─────────────────┐
│  Client  │ ─────────────────> │ «interface»     │
└──────────┘                    │ ClientInterface │
                                │  + request()    │
                                └────────┬────────┘
                                         │ implements
                                         │
                                ┌────────▼────────┐       wraps      ┌───────────────┐
                                │    Adapter      │ ───────────────> │   Adaptee     │
                                │  + request()    │                  │ (Service)     │
                                └─────────────────┘                  │ +specificReq()│
                                                                      └───────────────┘

Flow:
  Client calls adapter.request()
  → Adapter translates & calls adaptee.specificRequest()
  → Adaptee executes real logic
  → Result is translated back and returned to Client
```

**Object Adapter** (composition — most common, language-agnostic):
The adapter holds an instance of the adaptee.

**Class Adapter** (multiple inheritance — only in languages that support it, e.g., C++):
The adapter inherits from both the target interface and the adaptee class.

---

## Participants

| Participant | Role |
|---|---|
| **Client** | The class that contains the existing business logic. It works only through the Target interface and never interacts with the Adaptee directly. |
| **ClientInterface / Target** | The interface that the Client expects all collaborators to implement. |
| **Adapter** | Implements the Target interface and wraps an Adaptee. Translates calls from the Client into calls the Adaptee understands. |
| **Adaptee / Service** | The class with the useful behavior but an incompatible interface. Often a third-party or legacy class. |

---

## How It Works (step-by-step)

1. **Identify the conflict.** The client code expects a `Target` interface. The existing useful class (Adaptee) exposes a different interface.
2. **Define (or identify) the Target interface.** This is the contract the client already works with.
3. **Create the Adapter class** that implements the Target interface.
4. **Add a field** in the Adapter to hold a reference to an Adaptee instance (composition).
5. **Implement each Target method** in the Adapter. Inside each method, translate the call (convert parameters, restructure data, etc.) and delegate to the corresponding Adaptee method.
6. **Wire it up.** The client receives the Adapter through dependency injection or construction. From the client's perspective it is simply another Target — no special handling needed.
7. **Return/translate results** back from the Adaptee format to the format the client expects, if necessary.

---

## Code Examples

### Python

```python
"""
Real-world scenario: A payment processing system.

The application uses a unified PaymentProcessor interface.
A new payment gateway (StripeGateway) has been acquired, but its
API is completely different from the interface the rest of the
checkout system expects. We cannot modify StripeGateway because
it is a third-party SDK.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


# ── Target Interface ─────────────────────────────────────────────────────────

class PaymentProcessor(ABC):
    """The interface the checkout system already uses."""

    @abstractmethod
    def charge(self, amount_usd: Decimal, card_token: str) -> dict:
        """
        Charge a card.

        Returns a dict with keys:
            success (bool), transaction_id (str), message (str)
        """
        ...

    @abstractmethod
    def refund(self, transaction_id: str, amount_usd: Decimal) -> bool:
        ...


# ── Existing compatible processor (works natively) ───────────────────────────

class BraintreeProcessor(PaymentProcessor):
    """Already implements the expected interface — no adapter needed."""

    def charge(self, amount_usd: Decimal, card_token: str) -> dict:
        # Simulate Braintree call
        print(f"[Braintree] Charging ${amount_usd} to token {card_token}")
        return {
            "success": True,
            "transaction_id": "bt_txn_001",
            "message": "Braintree charge successful",
        }

    def refund(self, transaction_id: str, amount_usd: Decimal) -> bool:
        print(f"[Braintree] Refunding ${amount_usd} for txn {transaction_id}")
        return True


# ── Adaptee (third-party SDK with incompatible interface) ────────────────────

class StripeGateway:
    """
    Third-party Stripe SDK — we cannot change this class.
    It uses cents (int), returns Stripe-specific objects, etc.
    """

    def create_charge(self, amount_cents: int, source: str, currency: str = "usd") -> "StripeCharge":
        print(f"[Stripe SDK] Creating charge: {amount_cents} cents, source={source}")
        return StripeCharge(
            id=f"ch_stripe_{amount_cents}",
            status="succeeded",
            amount=amount_cents,
        )

    def create_refund(self, charge_id: str, amount_cents: int) -> "StripeRefund":
        print(f"[Stripe SDK] Refunding {amount_cents} cents on charge {charge_id}")
        return StripeRefund(id=f"re_{charge_id}", status="succeeded")


@dataclass
class StripeCharge:
    id: str
    status: str  # "succeeded" | "failed" | "pending"
    amount: int   # in cents


@dataclass
class StripeRefund:
    id: str
    status: str


# ── Adapter ──────────────────────────────────────────────────────────────────

class StripeAdapter(PaymentProcessor):
    """
    Adapts StripeGateway to the PaymentProcessor interface.

    Translates:
      - Decimal USD  →  integer cents
      - StripeCharge →  standard result dict
      - StripeRefund →  bool
    """

    def __init__(self, stripe: StripeGateway) -> None:
        self._stripe = stripe

    def charge(self, amount_usd: Decimal, card_token: str) -> dict:
        # Convert dollars to cents
        amount_cents = int(amount_usd * 100)
        try:
            stripe_charge = self._stripe.create_charge(
                amount_cents=amount_cents,
                source=card_token,
            )
            return {
                "success": stripe_charge.status == "succeeded",
                "transaction_id": stripe_charge.id,
                "message": f"Stripe charge {stripe_charge.status}",
            }
        except Exception as exc:
            return {"success": False, "transaction_id": "", "message": str(exc)}

    def refund(self, transaction_id: str, amount_usd: Decimal) -> bool:
        amount_cents = int(amount_usd * 100)
        try:
            result = self._stripe.create_refund(
                charge_id=transaction_id,
                amount_cents=amount_cents,
            )
            return result.status == "succeeded"
        except Exception:
            return False


# ── Client Code ──────────────────────────────────────────────────────────────

class CheckoutService:
    """Uses PaymentProcessor — unaware of which gateway is beneath."""

    def __init__(self, processor: PaymentProcessor) -> None:
        self._processor = processor

    def checkout(self, card_token: str, total: Decimal) -> None:
        print(f"\nProcessing checkout for ${total}")
        result = self._processor.charge(total, card_token)
        if result["success"]:
            print(f"  Payment succeeded! TXN: {result['transaction_id']}")
        else:
            print(f"  Payment failed: {result['message']}")

    def issue_refund(self, txn_id: str, amount: Decimal) -> None:
        ok = self._processor.refund(txn_id, amount)
        print(f"  Refund {'succeeded' if ok else 'failed'} for {txn_id}")


# ── Demo ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Using Braintree (native interface) ===")
    braintree_service = CheckoutService(BraintreeProcessor())
    braintree_service.checkout("tok_braintree_xyz", Decimal("49.99"))

    print("\n=== Using Stripe via Adapter ===")
    stripe_adapter = StripeAdapter(StripeGateway())
    stripe_service = CheckoutService(stripe_adapter)
    stripe_service.checkout("tok_stripe_abc", Decimal("149.95"))
    stripe_service.issue_refund("ch_stripe_14995", Decimal("50.00"))
```

---

### Java

```java
/**
 * Real-world scenario: Logging system migration.
 *
 * An application uses a custom Logger interface throughout.
 * A new requirement mandates SLF4J/Logback as the logging backend,
 * but the hundreds of call-sites expect the legacy Logger interface.
 * We adapt SLF4J's org.slf4j.Logger to our own Logger interface.
 *
 * (SLF4J is simulated here so the example is self-contained.)
 */

// ── Target Interface ──────────────────────────────────────────────────────────

interface AppLogger {
    void info(String message);
    void warn(String message);
    void error(String message, Throwable cause);
    boolean isDebugEnabled();
    void debug(String message);
}


// ── Adaptee (simulated third-party SLF4J Logger) ──────────────────────────────

class Slf4jLogger {
    private final String name;

    public Slf4jLogger(String name) {
        this.name = name;
    }

    // SLF4J uses {} placeholders and different method signatures
    public void info(String format, Object... args) {
        System.out.printf("[SLF4J INFO][%s] %s%n", name, String.format(format.replace("{}", "%s"), args));
    }

    public void warn(String format, Object... args) {
        System.out.printf("[SLF4J WARN][%s] %s%n", name, String.format(format.replace("{}", "%s"), args));
    }

    public void error(String format, Throwable t, Object... args) {
        System.out.printf("[SLF4J ERROR][%s] %s | caused by: %s%n",
                name,
                String.format(format.replace("{}", "%s"), args),
                t.getMessage());
    }

    public void debug(String format, Object... args) {
        System.out.printf("[SLF4J DEBUG][%s] %s%n", name, String.format(format.replace("{}", "%s"), args));
    }

    public boolean isDebugEnabled() {
        // In real SLF4J this checks log level config
        return Boolean.getBoolean("app.debug");
    }
}


// ── Adapter ───────────────────────────────────────────────────────────────────

class Slf4jLoggerAdapter implements AppLogger {
    private final Slf4jLogger slf4j;

    public Slf4jLoggerAdapter(Slf4jLogger slf4j) {
        this.slf4j = slf4j;
    }

    @Override
    public void info(String message) {
        // Translate: our simple string → SLF4J format call
        slf4j.info("{}", message);
    }

    @Override
    public void warn(String message) {
        slf4j.warn("{}", message);
    }

    @Override
    public void error(String message, Throwable cause) {
        // Translate: our (message, cause) → SLF4J's (format, throwable, args)
        slf4j.error("{}", cause, message);
    }

    @Override
    public boolean isDebugEnabled() {
        return slf4j.isDebugEnabled();
    }

    @Override
    public void debug(String message) {
        slf4j.debug("{}", message);
    }
}


// ── Client Code ───────────────────────────────────────────────────────────────

class OrderService {
    private final AppLogger logger;

    public OrderService(AppLogger logger) {
        this.logger = logger;
    }

    public void processOrder(String orderId, double amount) {
        logger.info("Processing order: " + orderId);
        try {
            if (amount <= 0) {
                throw new IllegalArgumentException("Amount must be positive, got: " + amount);
            }
            logger.debug("Order " + orderId + " validated, amount=$" + amount);
            logger.info("Order " + orderId + " processed successfully");
        } catch (Exception e) {
            logger.error("Failed to process order: " + orderId, e);
        }
    }
}


// ── Demo ──────────────────────────────────────────────────────────────────────

public class AdapterDemo {
    public static void main(String[] args) {
        // Create SLF4J logger (third-party, incompatible interface)
        Slf4jLogger rawSlf4j = new Slf4jLogger("OrderService");

        // Wrap it in an adapter so it satisfies our AppLogger interface
        AppLogger logger = new Slf4jLoggerAdapter(rawSlf4j);

        // Client code never knows it is talking to SLF4J
        OrderService service = new OrderService(logger);

        System.out.println("=== Processing valid order ===");
        service.processOrder("ORD-1001", 99.95);

        System.out.println("\n=== Processing invalid order ===");
        service.processOrder("ORD-1002", -5.00);
    }
}
```

---

### C++

```cpp
/**
 * Real-world scenario: Rendering engine integration.
 *
 * A game engine uses a Renderer interface. A new high-performance
 * Vulkan rendering library has been licensed, but it has a completely
 * different API from the OpenGL-style interface the engine expects.
 * An adapter bridges the gap.
 */

#include <iostream>
#include <string>
#include <memory>
#include <vector>

// ── Target Interface ──────────────────────────────────────────────────────────

class Renderer {
public:
    virtual ~Renderer() = default;

    virtual void beginFrame() = 0;
    virtual void drawMesh(const std::string& meshId, float x, float y, float z) = 0;
    virtual void setAmbientLight(float r, float g, float b) = 0;
    virtual void endFrame() = 0;
};


// ── Adaptee (third-party Vulkan-style library) ────────────────────────────────

struct VkColor { float r, g, b, a; };
struct VkVec3  { float x, y, z; };

class VulkanBackend {
public:
    void vkBeginRenderPass(const std::string& passName) {
        std::cout << "[Vulkan] vkBeginRenderPass(\"" << passName << "\")\n";
    }

    void vkSubmitDrawCall(const std::string& meshId, VkVec3 position, VkColor tint) {
        std::cout << "[Vulkan] vkSubmitDrawCall(mesh=" << meshId
                  << ", pos=[" << position.x << "," << position.y << "," << position.z << "]"
                  << ", tint=[" << tint.r << "," << tint.g << "," << tint.b << "])\n";
    }

    void vkSetGlobalUniform(const std::string& name, VkColor value) {
        std::cout << "[Vulkan] vkSetGlobalUniform(\"" << name << "\", ["
                  << value.r << "," << value.g << "," << value.b << "])\n";
    }

    void vkEndRenderPass() {
        std::cout << "[Vulkan] vkEndRenderPass()\n";
    }
};


// ── Adapter (Object Adapter using composition) ────────────────────────────────

class VulkanRendererAdapter : public Renderer {
public:
    explicit VulkanRendererAdapter(std::shared_ptr<VulkanBackend> backend)
        : m_backend(std::move(backend)) {}

    void beginFrame() override {
        // Translate: simple beginFrame() → Vulkan render pass with name
        m_backend->vkBeginRenderPass("MainPass");
    }

    void drawMesh(const std::string& meshId, float x, float y, float z) override {
        // Translate: individual floats → Vulkan's VkVec3 + default white tint
        VkVec3 position{x, y, z};
        VkColor defaultTint{1.0f, 1.0f, 1.0f, 1.0f};
        m_backend->vkSubmitDrawCall(meshId, position, defaultTint);
    }

    void setAmbientLight(float r, float g, float b) override {
        // Translate: RGB triplet → Vulkan uniform named "uAmbientLight"
        VkColor color{r, g, b, 1.0f};
        m_backend->vkSetGlobalUniform("uAmbientLight", color);
    }

    void endFrame() override {
        m_backend->vkEndRenderPass();
    }

private:
    std::shared_ptr<VulkanBackend> m_backend;
};


// ── Client Code ───────────────────────────────────────────────────────────────

class SceneRenderer {
public:
    explicit SceneRenderer(std::unique_ptr<Renderer> renderer)
        : m_renderer(std::move(renderer)) {}

    void renderScene(const std::vector<std::pair<std::string, VkVec3>>& objects) {
        m_renderer->beginFrame();
        m_renderer->setAmbientLight(0.3f, 0.3f, 0.4f);

        for (const auto& [meshId, pos] : objects) {
            m_renderer->drawMesh(meshId, pos.x, pos.y, pos.z);
        }

        m_renderer->endFrame();
    }

private:
    std::unique_ptr<Renderer> m_renderer;
};


// ── Demo ──────────────────────────────────────────────────────────────────────

int main() {
    auto vulkanBackend = std::make_shared<VulkanBackend>();
    auto adapter       = std::make_unique<VulkanRendererAdapter>(vulkanBackend);
    SceneRenderer scene(std::move(adapter));

    std::vector<std::pair<std::string, VkVec3>> objects = {
        {"mesh_terrain",   {0.0f,  0.0f, 0.0f}},
        {"mesh_character", {1.5f,  0.0f, 2.0f}},
        {"mesh_tree",      {-3.0f, 0.0f, 1.0f}},
    };

    std::cout << "=== Rendering scene with Vulkan backend (via adapter) ===\n";
    scene.renderScene(objects);

    return 0;
}
```

---

### C#

```csharp
/**
 * Real-world scenario: Cloud storage abstraction.
 *
 * An application uses an IFileStorage interface for saving/loading files.
 * A new Azure Blob Storage SDK has been adopted, but its client API
 * is completely different from IFileStorage. The adapter wraps the SDK.
 */

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

// ── Target Interface ──────────────────────────────────────────────────────────

public interface IFileStorage
{
    void Upload(string path, byte[] data);
    byte[] Download(string path);
    bool Exists(string path);
    void Delete(string path);
    IEnumerable<string> ListFiles(string directory);
}


// ── Adaptee (simulated Azure Blob Storage SDK) ────────────────────────────────

public class BlobContainerClient
{
    private readonly string _containerName;
    private readonly Dictionary<string, byte[]> _blobs = new();

    public BlobContainerClient(string containerName)
    {
        _containerName = containerName;
        Console.WriteLine($"[Azure SDK] Connected to container: {containerName}");
    }

    // Azure SDK uses BlobClient objects, not direct paths
    public BlobClient GetBlobClient(string blobName) => new(_containerName, blobName, _blobs);

    public IEnumerable<BlobItem> GetBlobs(string prefix = "")
    {
        foreach (var key in _blobs.Keys)
        {
            if (key.StartsWith(prefix))
                yield return new BlobItem { Name = key };
        }
    }
}

public class BlobClient
{
    private readonly string _container;
    private readonly string _name;
    private readonly Dictionary<string, byte[]> _store;

    public BlobClient(string container, string name, Dictionary<string, byte[]> store)
    {
        _container = container;
        _name = name;
        _store = store;
    }

    public void Upload(BinaryData data)
    {
        _store[_name] = data.ToArray();
        Console.WriteLine($"[Azure SDK] Uploaded blob '{_name}' to container '{_container}' ({data.ToArray().Length} bytes)");
    }

    public BinaryData DownloadContent()
    {
        if (!_store.ContainsKey(_name))
            throw new FileNotFoundException($"Blob '{_name}' not found.");
        Console.WriteLine($"[Azure SDK] Downloaded blob '{_name}' from container '{_container}'");
        return BinaryData.FromBytes(_store[_name]);
    }

    public bool Exists() => _store.ContainsKey(_name);

    public void Delete()
    {
        _store.Remove(_name);
        Console.WriteLine($"[Azure SDK] Deleted blob '{_name}'");
    }
}

public class BlobItem { public string Name { get; set; } = ""; }


// ── Adapter ───────────────────────────────────────────────────────────────────

public class AzureBlobStorageAdapter : IFileStorage
{
    private readonly BlobContainerClient _containerClient;

    public AzureBlobStorageAdapter(BlobContainerClient containerClient)
    {
        _containerClient = containerClient;
    }

    public void Upload(string path, byte[] data)
    {
        // Translate: simple path + byte[] → Azure BlobClient + BinaryData
        string blobName = NormalizePath(path);
        var blobClient = _containerClient.GetBlobClient(blobName);
        blobClient.Upload(BinaryData.FromBytes(data));
    }

    public byte[] Download(string path)
    {
        string blobName = NormalizePath(path);
        var blobClient = _containerClient.GetBlobClient(blobName);
        return blobClient.DownloadContent().ToArray();
    }

    public bool Exists(string path)
    {
        string blobName = NormalizePath(path);
        return _containerClient.GetBlobClient(blobName).Exists();
    }

    public void Delete(string path)
    {
        string blobName = NormalizePath(path);
        _containerClient.GetBlobClient(blobName).Delete();
    }

    public IEnumerable<string> ListFiles(string directory)
    {
        string prefix = NormalizePath(directory).TrimEnd('/') + "/";
        foreach (var item in _containerClient.GetBlobs(prefix))
            yield return "/" + item.Name;
    }

    // Translate filesystem-style paths to Azure blob names
    private static string NormalizePath(string path) =>
        path.TrimStart('/').Replace('\\', '/');
}


// ── Client Code ───────────────────────────────────────────────────────────────

public class DocumentManager
{
    private readonly IFileStorage _storage;

    public DocumentManager(IFileStorage storage)
    {
        _storage = storage;
    }

    public void SaveDocument(string path, string content)
    {
        var data = Encoding.UTF8.GetBytes(content);
        _storage.Upload(path, data);
        Console.WriteLine($"  Saved document to {path}");
    }

    public string LoadDocument(string path)
    {
        if (!_storage.Exists(path))
            throw new FileNotFoundException($"Document not found: {path}");
        var data = _storage.Download(path);
        return Encoding.UTF8.GetString(data);
    }

    public void PrintDirectory(string dir)
    {
        Console.WriteLine($"  Files in {dir}:");
        foreach (var file in _storage.ListFiles(dir))
            Console.WriteLine($"    - {file}");
    }
}


// ── Demo ──────────────────────────────────────────────────────────────────────

public class Program
{
    public static void Main()
    {
        Console.WriteLine("=== Document Manager with Azure Blob Storage (via Adapter) ===\n");

        var containerClient = new BlobContainerClient("my-documents");
        IFileStorage storage = new AzureBlobStorageAdapter(containerClient);
        var manager = new DocumentManager(storage);

        manager.SaveDocument("/reports/q1-2026.txt", "Q1 2026 Revenue: $4.2M");
        manager.SaveDocument("/reports/q2-2026.txt", "Q2 2026 Forecast: $5.1M");
        manager.SaveDocument("/invoices/inv-001.txt", "Invoice #001: $12,500");

        Console.WriteLine();
        manager.PrintDirectory("/reports");

        Console.WriteLine();
        string content = manager.LoadDocument("/reports/q1-2026.txt");
        Console.WriteLine($"  Loaded: {content}");
    }
}
```

---

### TypeScript

```typescript
/**
 * Real-world scenario: Notification service aggregator.
 *
 * The application dispatches notifications through a unified Notifier interface.
 * Three providers are integrated: an in-house EmailService (already compatible),
 * a third-party SlackSDK, and a third-party TwilioSMS SDK.
 * Adapters wrap the incompatible SDKs.
 */

// ── Target Interface ──────────────────────────────────────────────────────────

interface Notifier {
  sendNotification(recipient: string, subject: string, body: string): Promise<NotificationResult>;
  supportsRecipient(recipient: string): boolean;
}

interface NotificationResult {
  success: boolean;
  messageId: string;
  provider: string;
  error?: string;
}


// ── Native implementation (no adapter needed) ─────────────────────────────────

class EmailService implements Notifier {
  async sendNotification(recipient: string, subject: string, body: string): Promise<NotificationResult> {
    console.log(`[EmailService] Sending email to ${recipient}: "${subject}"`);
    // Simulate async HTTP call
    return {
      success: true,
      messageId: `email_${Date.now()}`,
      provider: "EmailService",
    };
  }

  supportsRecipient(recipient: string): boolean {
    return recipient.includes("@");
  }
}


// ── Adaptee #1: Third-party Slack SDK ────────────────────────────────────────

class SlackClient {
  constructor(private readonly botToken: string) {}

  /** Slack uses channel IDs, not human-readable names in production. */
  postMessage(params: {
    channel: string;
    text: string;
    blocks?: Array<{ type: string; text: { type: string; text: string } }>;
  }): { ok: boolean; ts: string; channel: string } {
    console.log(`[Slack SDK] postMessage to ${params.channel}: ${params.text}`);
    return { ok: true, ts: `${Date.now()}.000100`, channel: params.channel };
  }
}


// ── Adapter #1: Slack ─────────────────────────────────────────────────────────

class SlackNotifierAdapter implements Notifier {
  constructor(private readonly slack: SlackClient) {}

  async sendNotification(recipient: string, subject: string, body: string): Promise<NotificationResult> {
    // recipient is a Slack channel like "#alerts" or "U12345"
    const response = this.slack.postMessage({
      channel: recipient,
      text: `*${subject}*\n${body}`,
      // Translate: subject+body → Slack Block Kit format
      blocks: [
        { type: "section", text: { type: "mrkdwn", text: `*${subject}*` } },
        { type: "section", text: { type: "mrkdwn", text: body } },
      ],
    });

    return {
      success: response.ok,
      messageId: `slack_${response.ts}`,
      provider: "Slack",
      error: response.ok ? undefined : "Slack API error",
    };
  }

  supportsRecipient(recipient: string): boolean {
    // Slack recipients start with # (channel) or U (user ID)
    return recipient.startsWith("#") || recipient.startsWith("U");
  }
}


// ── Adaptee #2: Third-party Twilio SMS SDK ────────────────────────────────────

class TwilioClient {
  constructor(
    private readonly accountSid: string,
    private readonly authToken: string,
    private readonly fromNumber: string
  ) {}

  messages = {
    create: (params: { body: string; from: string; to: string }): { sid: string; status: string } => {
      console.log(`[Twilio SDK] SMS from ${params.from} to ${params.to}: ${params.body}`);
      return { sid: `SM${Math.random().toString(36).slice(2, 10)}`, status: "queued" };
    },
  };
}


// ── Adapter #2: Twilio SMS ────────────────────────────────────────────────────

class TwilioSmsAdapter implements Notifier {
  private readonly maxSmsLength = 160;

  constructor(
    private readonly twilio: TwilioClient,
    private readonly fromNumber: string
  ) {}

  async sendNotification(recipient: string, subject: string, body: string): Promise<NotificationResult> {
    // Translate: subject+body → single SMS string, truncated if needed
    const fullText = `${subject}: ${body}`;
    const smsBody = fullText.length > this.maxSmsLength
      ? fullText.slice(0, this.maxSmsLength - 3) + "..."
      : fullText;

    const message = this.twilio.messages.create({
      body: smsBody,
      from: this.fromNumber,
      to: recipient,
    });

    return {
      success: message.status === "queued" || message.status === "sent",
      messageId: `twilio_${message.sid}`,
      provider: "TwilioSMS",
    };
  }

  supportsRecipient(recipient: string): boolean {
    // Phone numbers in E.164 format: +15551234567
    return /^\+\d{10,15}$/.test(recipient);
  }
}


// ── Client: Notification Dispatcher ──────────────────────────────────────────

class NotificationDispatcher {
  private readonly notifiers: Notifier[];

  constructor(notifiers: Notifier[]) {
    this.notifiers = notifiers;
  }

  async dispatch(recipient: string, subject: string, body: string): Promise<void> {
    const notifier = this.notifiers.find((n) => n.supportsRecipient(recipient));
    if (!notifier) {
      console.error(`  No notifier found for recipient: ${recipient}`);
      return;
    }
    const result = await notifier.sendNotification(recipient, subject, body);
    const status = result.success ? "OK" : `FAILED (${result.error})`;
    console.log(`  [${result.provider}] ${status} — msgId: ${result.messageId}`);
  }
}


// ── Demo ──────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const dispatcher = new NotificationDispatcher([
    new EmailService(),
    new SlackNotifierAdapter(new SlackClient("xoxb-fake-token")),
    new TwilioSmsAdapter(
      new TwilioClient("AC123", "auth_token", "+15550001111"),
      "+15550001111"
    ),
  ]);

  console.log("=== Notification Dispatcher Demo ===\n");

  await dispatcher.dispatch("alice@example.com", "Invoice Ready", "Your Q2 invoice is available.");
  console.log();
  await dispatcher.dispatch("#engineering", "Deploy Alert", "v2.4.1 deployed to production.");
  console.log();
  await dispatcher.dispatch("+15559876543", "Verification Code", "Your OTP is 482917");
  console.log();
  await dispatcher.dispatch("unknown-recipient", "Test", "This should fail.");
}

main();
```

---

### Go

```go
// Real-world scenario: Database abstraction layer.
//
// A service uses a Repository interface for data access.
// A new time-series database (InfluxDB-like) has been added for metrics,
// but its client API is incompatible with the Repository interface.
// An adapter bridges the gap.

package main

import (
	"fmt"
	"strings"
	"time"
)

// ── Target Interface ──────────────────────────────────────────────────────────

// Repository is the standard data-access contract used across the application.
type Repository interface {
	Save(key string, value interface{}) error
	Find(key string) (interface{}, bool)
	Delete(key string) error
	Keys(prefix string) []string
}

// ── Existing native implementation ────────────────────────────────────────────

// InMemoryRepository satisfies Repository natively — no adapter needed.
type InMemoryRepository struct {
	data map[string]interface{}
}

func NewInMemoryRepository() *InMemoryRepository {
	return &InMemoryRepository{data: make(map[string]interface{})}
}

func (r *InMemoryRepository) Save(key string, value interface{}) error {
	r.data[key] = value
	fmt.Printf("[InMemory] Save(%q)\n", key)
	return nil
}

func (r *InMemoryRepository) Find(key string) (interface{}, bool) {
	v, ok := r.data[key]
	return v, ok
}

func (r *InMemoryRepository) Delete(key string) error {
	delete(r.data, key)
	return nil
}

func (r *InMemoryRepository) Keys(prefix string) []string {
	var out []string
	for k := range r.data {
		if strings.HasPrefix(k, prefix) {
			out = append(out, k)
		}
	}
	return out
}

// ── Adaptee: Simulated time-series DB client (incompatible API) ───────────────

// TimeSeriesPoint represents a data point in the TSDB.
type TimeSeriesPoint struct {
	Measurement string
	Tags        map[string]string
	Fields      map[string]interface{}
	Timestamp   time.Time
}

// TimeSeriesDB simulates a third-party InfluxDB-style client.
type TimeSeriesDB struct {
	bucket string
	points map[string]TimeSeriesPoint // keyed by measurement+tags
}

func NewTimeSeriesDB(bucket string) *TimeSeriesDB {
	fmt.Printf("[TSDB] Connected to bucket: %s\n", bucket)
	return &TimeSeriesDB{bucket: bucket, points: make(map[string]TimeSeriesPoint)}
}

// WritePoint writes a data point to the time-series database.
func (db *TimeSeriesDB) WritePoint(point TimeSeriesPoint) error {
	id := point.Measurement
	for k, v := range point.Tags {
		id += fmt.Sprintf(",%s=%s", k, v)
	}
	db.points[id] = point
	fmt.Printf("[TSDB] WritePoint(measurement=%q, fields=%v)\n", point.Measurement, point.Fields)
	return nil
}

// QueryMeasurement retrieves all points for a measurement.
func (db *TimeSeriesDB) QueryMeasurement(measurement string) ([]TimeSeriesPoint, error) {
	var results []TimeSeriesPoint
	for _, p := range db.points {
		if p.Measurement == measurement {
			results = append(results, p)
		}
	}
	fmt.Printf("[TSDB] Query(measurement=%q) → %d results\n", measurement, len(results))
	return results, nil
}

// DeleteMeasurement removes all points for a measurement.
func (db *TimeSeriesDB) DeleteMeasurement(measurement string) error {
	for k, p := range db.points {
		if p.Measurement == measurement {
			delete(db.points, k)
		}
	}
	fmt.Printf("[TSDB] DeleteMeasurement(%q)\n", measurement)
	return nil
}

// ListMeasurements returns all unique measurement names matching a prefix.
func (db *TimeSeriesDB) ListMeasurements(prefix string) []string {
	seen := make(map[string]bool)
	for _, p := range db.points {
		if strings.HasPrefix(p.Measurement, prefix) {
			seen[p.Measurement] = true
		}
	}
	var out []string
	for m := range seen {
		out = append(out, m)
	}
	return out
}

// ── Adapter ───────────────────────────────────────────────────────────────────

// TimeSeriesAdapter adapts TimeSeriesDB to the Repository interface.
// Keys are treated as measurement names. Values must be map[string]interface{}.
type TimeSeriesAdapter struct {
	tsdb *TimeSeriesDB
}

func NewTimeSeriesAdapter(tsdb *TimeSeriesDB) *TimeSeriesAdapter {
	return &TimeSeriesAdapter{tsdb: tsdb}
}

func (a *TimeSeriesAdapter) Save(key string, value interface{}) error {
	fields, ok := value.(map[string]interface{})
	if !ok {
		// Wrap scalar values in a generic "value" field
		fields = map[string]interface{}{"value": value}
	}
	return a.tsdb.WritePoint(TimeSeriesPoint{
		Measurement: key,
		Tags:        map[string]string{"source": "adapter"},
		Fields:      fields,
		Timestamp:   time.Now(),
	})
}

func (a *TimeSeriesAdapter) Find(key string) (interface{}, bool) {
	points, err := a.tsdb.QueryMeasurement(key)
	if err != nil || len(points) == 0 {
		return nil, false
	}
	// Return the most recent point's fields
	return points[len(points)-1].Fields, true
}

func (a *TimeSeriesAdapter) Delete(key string) error {
	return a.tsdb.DeleteMeasurement(key)
}

func (a *TimeSeriesAdapter) Keys(prefix string) []string {
	return a.tsdb.ListMeasurements(prefix)
}

// ── Client Code ───────────────────────────────────────────────────────────────

// MetricsService stores and retrieves application metrics.
// It depends only on the Repository interface.
type MetricsService struct {
	repo Repository
}

func NewMetricsService(repo Repository) *MetricsService {
	return &MetricsService{repo: repo}
}

func (s *MetricsService) RecordMetric(name string, value float64, unit string) {
	_ = s.repo.Save(name, map[string]interface{}{
		"value": value,
		"unit":  unit,
	})
}

func (s *MetricsService) GetMetric(name string) {
	val, ok := s.repo.Find(name)
	if !ok {
		fmt.Printf("  Metric %q not found\n", name)
		return
	}
	fmt.Printf("  Metric %q = %v\n", name, val)
}

func (s *MetricsService) ListMetrics(prefix string) {
	keys := s.repo.Keys(prefix)
	fmt.Printf("  Metrics with prefix %q: %v\n", prefix, keys)
}

// ── Demo ──────────────────────────────────────────────────────────────────────

func main() {
	fmt.Println("=== Metrics Service with Time-Series DB (via Adapter) ===\n")

	tsdb := NewTimeSeriesDB("app-metrics")
	adapter := NewTimeSeriesAdapter(tsdb)
	svc := NewMetricsService(adapter)

	fmt.Println()
	svc.RecordMetric("cpu.usage", 72.5, "percent")
	svc.RecordMetric("memory.usage", 4096, "MB")
	svc.RecordMetric("http.requests", 1520, "req/min")

	fmt.Println()
	svc.GetMetric("cpu.usage")
	svc.GetMetric("disk.usage") // not found

	fmt.Println()
	svc.ListMetrics("")
}
```

---

### PHP

```php
<?php

/**
 * Real-world scenario: Social authentication.
 *
 * An application uses an AuthProvider interface for OAuth login.
 * GitHub and Google both have SDKs with completely different APIs.
 * Adapters expose them through a unified interface.
 */

declare(strict_types=1);

// ── Target Interface ──────────────────────────────────────────────────────────

interface AuthProvider
{
    /**
     * Returns the URL to redirect the user to for authorization.
     */
    public function getAuthorizationUrl(string $redirectUri, array $scopes = []): string;

    /**
     * Exchanges an authorization code for an access token.
     */
    public function exchangeCodeForToken(string $code, string $redirectUri): string;

    /**
     * Fetches the authenticated user's profile using the token.
     *
     * @return array{id: string, email: string, name: string, avatar: string}
     */
    public function getUserProfile(string $accessToken): array;
}


// ── Adaptee #1: Simulated GitHub OAuth SDK ────────────────────────────────────

class GitHubOAuthClient
{
    private string $clientId;
    private string $clientSecret;

    public function __construct(string $clientId, string $clientSecret)
    {
        $this->clientId     = $clientId;
        $this->clientSecret = $clientSecret;
    }

    public function buildAuthorizeUrl(array $options): string
    {
        $params = http_build_query([
            'client_id'    => $this->clientId,
            'redirect_uri' => $options['redirect_uri'],
            'scope'        => implode(' ', $options['scopes'] ?? ['user']),
            'state'        => bin2hex(random_bytes(8)),
        ]);
        $url = "https://github.com/login/oauth/authorize?{$params}";
        echo "[GitHub SDK] buildAuthorizeUrl → {$url}\n";
        return $url;
    }

    public function getAccessToken(string $code, string $redirectUri): array
    {
        echo "[GitHub SDK] getAccessToken(code={$code})\n";
        // Simulated response
        return [
            'access_token' => 'ghu_simulated_' . substr($code, 0, 6),
            'token_type'   => 'bearer',
            'scope'        => 'user',
        ];
    }

    public function fetchAuthenticatedUser(string $token): array
    {
        echo "[GitHub SDK] fetchAuthenticatedUser(token={$token})\n";
        return [
            'login'      => 'octocat',
            'id'         => 1,
            'email'      => 'octocat@github.com',
            'name'       => 'The Octocat',
            'avatar_url' => 'https://github.com/images/octocat.png',
        ];
    }
}


// ── Adapter #1: GitHub ────────────────────────────────────────────────────────

class GitHubAuthAdapter implements AuthProvider
{
    private GitHubOAuthClient $github;

    public function __construct(GitHubOAuthClient $github)
    {
        $this->github = $github;
    }

    public function getAuthorizationUrl(string $redirectUri, array $scopes = []): string
    {
        return $this->github->buildAuthorizeUrl([
            'redirect_uri' => $redirectUri,
            'scopes'       => $scopes ?: ['user', 'user:email'],
        ]);
    }

    public function exchangeCodeForToken(string $code, string $redirectUri): string
    {
        $tokenData = $this->github->getAccessToken($code, $redirectUri);
        return $tokenData['access_token'];
    }

    public function getUserProfile(string $accessToken): array
    {
        $ghUser = $this->github->fetchAuthenticatedUser($accessToken);
        // Translate GitHub's fields → our standard profile shape
        return [
            'id'     => (string) $ghUser['id'],
            'email'  => $ghUser['email'],
            'name'   => $ghUser['name'],
            'avatar' => $ghUser['avatar_url'],
        ];
    }
}


// ── Adaptee #2: Simulated Google OAuth SDK ────────────────────────────────────

class GoogleOAuthService
{
    private string $clientId;
    private string $clientSecret;

    public function __construct(string $clientId, string $clientSecret)
    {
        $this->clientId     = $clientId;
        $this->clientSecret = $clientSecret;
    }

    public function createAuthUrl(string $redirectUri, string $scope, string $responseType = 'code'): string
    {
        $params = http_build_query([
            'client_id'     => $this->clientId,
            'redirect_uri'  => $redirectUri,
            'scope'         => $scope,
            'response_type' => $responseType,
            'access_type'   => 'offline',
        ]);
        $url = "https://accounts.google.com/o/oauth2/v2/auth?{$params}";
        echo "[Google SDK] createAuthUrl → {$url}\n";
        return $url;
    }

    public function fetchTokens(string $authCode, string $redirectUri): object
    {
        echo "[Google SDK] fetchTokens(code={$authCode})\n";
        return (object) [
            'access_token'  => 'ya29.simulated_' . substr($authCode, 0, 6),
            'refresh_token' => 'refreshtoken123',
            'expires_in'    => 3600,
        ];
    }

    public function getUserInfo(string $accessToken): object
    {
        echo "[Google SDK] getUserInfo(token={$accessToken})\n";
        return (object) [
            'sub'     => '109876543210',
            'email'   => 'user@gmail.com',
            'name'    => 'Google User',
            'picture' => 'https://lh3.googleusercontent.com/photo.jpg',
        ];
    }
}


// ── Adapter #2: Google ────────────────────────────────────────────────────────

class GoogleAuthAdapter implements AuthProvider
{
    private GoogleOAuthService $google;

    public function __construct(GoogleOAuthService $google)
    {
        $this->google = $google;
    }

    public function getAuthorizationUrl(string $redirectUri, array $scopes = []): string
    {
        // Translate: array of scopes → space-separated string
        $scopeStr = implode(' ', $scopes ?: ['openid', 'email', 'profile']);
        return $this->google->createAuthUrl($redirectUri, $scopeStr);
    }

    public function exchangeCodeForToken(string $code, string $redirectUri): string
    {
        $tokens = $this->google->fetchTokens($code, $redirectUri);
        return $tokens->access_token;
    }

    public function getUserProfile(string $accessToken): array
    {
        $info = $this->google->getUserInfo($accessToken);
        // Translate Google's fields → our standard profile shape
        return [
            'id'     => $info->sub,
            'email'  => $info->email,
            'name'   => $info->name,
            'avatar' => $info->picture,
        ];
    }
}


// ── Client Code ───────────────────────────────────────────────────────────────

class SocialLoginController
{
    /** @var AuthProvider[] */
    private array $providers;

    public function __construct(array $providers)
    {
        $this->providers = $providers;
    }

    public function login(string $providerName, string $callbackUrl): void
    {
        $provider = $this->providers[$providerName] ?? null;
        if ($provider === null) {
            echo "  Unknown provider: {$providerName}\n";
            return;
        }

        $authUrl = $provider->getAuthorizationUrl($callbackUrl);
        echo "  → Redirect user to: {$authUrl}\n\n";

        // Simulate callback with authorization code
        $code        = 'auth_code_' . random_int(1000, 9999);
        $accessToken = $provider->exchangeCodeForToken($code, $callbackUrl);
        $profile     = $provider->getUserProfile($accessToken);

        echo "  Logged in as: {$profile['name']} ({$profile['email']})\n";
        echo "  Avatar: {$profile['avatar']}\n";
    }
}


// ── Demo ──────────────────────────────────────────────────────────────────────

$controller = new SocialLoginController([
    'github' => new GitHubAuthAdapter(new GitHubOAuthClient('gh_client_id', 'gh_secret')),
    'google' => new GoogleAuthAdapter(new GoogleOAuthService('google_client_id', 'google_secret')),
]);

echo "=== Social Login: GitHub ===\n";
$controller->login('github', 'https://myapp.com/auth/github/callback');

echo "\n=== Social Login: Google ===\n";
$controller->login('google', 'https://myapp.com/auth/google/callback');
```

---

### Ruby

```ruby
# Real-world scenario: Currency exchange rate service.
#
# The application uses an ExchangeRateProvider interface.
# Two third-party APIs are integrated (Open Exchange Rates and Fixer.io),
# each with different response formats and call conventions.
# Adapters normalize them to a common interface.

require 'bigdecimal'
require 'bigdecimal/util'

# ── Target Interface (module as interface contract) ───────────────────────────

module ExchangeRateProvider
  # @param from [String] ISO 4217 base currency code (e.g., "USD")
  # @param to   [String] ISO 4217 target currency code (e.g., "EUR")
  # @return [BigDecimal] the exchange rate
  def rate(from:, to:)
    raise NotImplementedError, "#{self.class}#rate is not implemented"
  end

  # @param base [String] base currency
  # @return [Hash{String => BigDecimal}] all available rates keyed by currency code
  def all_rates(base:)
    raise NotImplementedError, "#{self.class}#all_rates is not implemented"
  end

  # @return [Time] timestamp of when the rates were last updated
  def last_updated
    raise NotImplementedError, "#{self.class}#last_updated is not implemented"
  end
end


# ── Adaptee #1: Simulated Open Exchange Rates client ─────────────────────────

class OpenExchangeRatesClient
  BASE_URL = "https://openexchangerates.org/api"

  def initialize(app_id)
    @app_id = app_id
    puts "[OXR] Client initialized with app_id=#{app_id}"
  end

  # Returns a Hash with keys: base, timestamp, rates (Hash of code => Float)
  def latest(base: "USD")
    puts "[OXR] GET /latest.json?base=#{base}"
    # Simulated response (OXR free tier only supports USD as base)
    {
      "base"      => base,
      "timestamp" => 1_749_000_000,
      "rates"     => {
        "EUR" => 0.9123,
        "GBP" => 0.7845,
        "JPY" => 149.52,
        "CAD" => 1.3601,
        "AUD" => 1.5234,
        base  => 1.0
      }
    }
  end
end


# ── Adapter #1: Open Exchange Rates ──────────────────────────────────────────

class OpenExchangeRatesAdapter
  include ExchangeRateProvider

  def initialize(client)
    @client = client
    @cache  = nil
  end

  def rate(from:, to:)
    data  = fetch_data(from)
    rates = data["rates"]

    unless rates.key?(to)
      raise ArgumentError, "Currency not supported: #{to}"
    end

    # OXR returns Floats; we use BigDecimal for financial precision
    rates[to].to_d
  end

  def all_rates(base:)
    data = fetch_data(base)
    data["rates"].transform_values(&:to_d)
  end

  def last_updated
    data = fetch_data("USD")
    Time.at(data["timestamp"])
  end

  private

  def fetch_data(base)
    @cache ||= @client.latest(base: base)
  end
end


# ── Adaptee #2: Simulated Fixer.io client ────────────────────────────────────

class FixerClient
  def initialize(api_key)
    @api_key = api_key
    puts "[Fixer] Client initialized with api_key=#{api_key}"
  end

  # Fixer returns a different structure with success flag and date string
  def fetch_latest(symbols: [], base: "EUR")
    puts "[Fixer] GET /latest?base=#{base}&symbols=#{symbols.join(',')}"
    {
      "success"   => true,
      "timestamp" => 1_748_999_000,
      "base"      => base,
      "date"      => "2026-06-08",
      "rates"     => {
        "USD" => 1.0963,
        "GBP" => 0.8598,
        "JPY" => 163.91,
        "CAD" => 1.4913,
        "AUD" => 1.6702,
        base  => 1.0
      }
    }
  end
end


# ── Adapter #2: Fixer.io ─────────────────────────────────────────────────────

class FixerAdapter
  include ExchangeRateProvider

  def initialize(client)
    @client = client
    @cache  = nil
  end

  def rate(from:, to:)
    data = fetch_data(from)
    raise "Fixer API error" unless data["success"]

    rates = data["rates"]
    rates.fetch(to) { raise ArgumentError, "Currency not supported: #{to}" }.to_d
  end

  def all_rates(base:)
    data = fetch_data(base)
    raise "Fixer API error" unless data["success"]

    data["rates"].transform_values(&:to_d)
  end

  def last_updated
    data = fetch_data("EUR")
    # Fixer returns an integer timestamp
    Time.at(data["timestamp"])
  end

  private

  def fetch_data(base)
    @cache ||= @client.fetch_latest(base: base)
  end
end


# ── Client Code ───────────────────────────────────────────────────────────────

class CurrencyConverter
  def initialize(provider)
    # provider is anything that includes ExchangeRateProvider
    @provider = provider
  end

  def convert(amount, from:, to:)
    rate   = @provider.rate(from: from, to: to)
    result = amount.to_d * rate
    puts "  #{amount} #{from} = #{result.round(2)} #{to}  (rate: #{rate.round(6)})"
    result
  end

  def print_all_rates(base:)
    puts "  Exchange rates based on #{base} (as of #{@provider.last_updated}):"
    @provider.all_rates(base: base).each do |currency, rate|
      printf("    %-4s  %.6f\n", currency, rate)
    end
  end
end


# ── Demo ──────────────────────────────────────────────────────────────────────

puts "=== CurrencyConverter with Open Exchange Rates (via Adapter) ==="
oxr_adapter = OpenExchangeRatesAdapter.new(OpenExchangeRatesClient.new("oxr_app_abc123"))
converter1  = CurrencyConverter.new(oxr_adapter)

puts
converter1.convert(1000, from: "USD", to: "EUR")
converter1.convert(500,  from: "USD", to: "JPY")
puts
converter1.print_all_rates(base: "USD")

puts "\n=== CurrencyConverter with Fixer.io (via Adapter) ==="
fixer_adapter = FixerAdapter.new(FixerClient.new("fixer_key_xyz789"))
converter2    = CurrencyConverter.new(fixer_adapter)

puts
converter2.convert(1000, from: "EUR", to: "USD")
converter2.convert(250,  from: "EUR", to: "GBP")
```

---

## When To Use

- **You need to use an existing class but its interface does not match.** The most common scenario: a third-party library, a legacy module, or any class you cannot or should not modify.
- **You want a reusable class that cooperates with classes that have incompatible interfaces.** The adapter acts as a protocol translation layer.
- **You need to reuse several existing subclasses** but they lack a common interface, and adding one to the superclass is not practical. Wrap each subclass with a separate adapter.
- **Migrating to a new library or service** without rewriting the entire codebase — swap the adapter, not every call site.
- **Testing** — adapters make it straightforward to swap real dependencies with test doubles by coding to the Target interface.

---

## Pros & Cons

### Pros

| | |
|---|---|
| **Single Responsibility Principle** | Separates interface conversion from business logic. The adapter handles translation; the client and adaptee each stay focused on their own concerns. |
| **Open/Closed Principle** | You can introduce new adapters without changing the existing client code or the adaptee. |
| **Works with incompatible classes** | Enables collaboration between classes that otherwise could not work together at all. |
| **Testability** | Coding against the Target interface makes it trivial to inject test doubles during unit testing. |
| **Encapsulates complexity** | Complex translation logic is contained in one place — the adapter — rather than scattered across the codebase. |

### Cons

| | |
|---|---|
| **Increased complexity** | Every new external dependency may require a new adapter class, increasing the number of classes in the project. |
| **Sometimes unnecessary** | If you control the service class, it can be simpler to modify it directly rather than writing an adapter. |
| **Potential performance overhead** | Translation (converting data types, restructuring objects) adds a small overhead per call, which is negligible in most cases but worth noting in tight loops. |
| **Hidden indirection** | Readers of the code must trace through the adapter to understand what actually executes, which can make debugging less straightforward. |

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Bridge** | Bridge is designed up front to decouple abstraction from implementation so both can vary independently. Adapter is applied after the fact to make incompatible interfaces work together. |
| **Decorator** | Decorator adds new behavior to an object while keeping the same interface. Adapter changes the interface without adding behavior. Both use composition and wrap an object. |
| **Proxy** | Proxy provides the same interface as the object it proxies and typically manages access, caching, or logging. Adapter provides a different interface to make incompatible classes compatible. |
| **Facade** | Facade defines a simplified interface to a complex subsystem. An Adapter tries to make an existing interface usable where a different one is expected. Facade can sometimes be seen as an adapter for the entire subsystem. |

---

## Sources

- https://refactoring.guru/design-patterns/adapter
- https://sourcemaking.com/design_patterns/adapter
