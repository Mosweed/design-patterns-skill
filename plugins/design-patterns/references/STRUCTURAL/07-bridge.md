# Bridge Pattern

**Category:** Structural  
**Also Known As:** Handle/Body

---

## Intent

The Bridge pattern lets you split a large class or a set of closely related classes into two separate hierarchies — **abstraction** and **implementation** — which can be developed and extended independently of each other.

---

## Problem It Solves

Imagine you are building a UI rendering system that supports multiple widget types (Button, Checkbox, TextField) across multiple platforms (Windows, macOS, Linux). A naive approach produces a cartesian-product explosion:

```
WindowsButton
MacOSButton
LinuxButton
WindowsCheckbox
MacOSCheckbox
LinuxCheckbox
...
```

Every time you add a new widget or a new platform you must create and maintain N × M classes. The root cause is that you are trying to extend the class in **two independent dimensions** — widget type and rendering platform — inside a single inheritance hierarchy.

The Bridge pattern solves this by separating the two concerns into distinct hierarchies that are connected via composition (a "bridge") rather than inheritance.

---

## Solution

1. Identify the two independent dimensions of variation (e.g., abstraction = widget type; implementation = rendering platform).
2. Extract the implementation dimension into its own interface (`Implementation`).
3. Create concrete classes for each variant of the implementation (`ConcreteImplementationA`, `ConcreteImplementationB`).
4. The abstraction class holds a **reference** to an `Implementation` object and delegates platform-specific work to it.
5. Define refined abstractions that add higher-level logic on top of the abstraction, without touching the implementation.

Both hierarchies can now grow independently. Adding a new platform means adding one new `ConcreteImplementation`; adding a new widget means adding one new `RefinedAbstraction`.

---

## Structure

```
┌──────────────────────────────────┐       ┌──────────────────────────────────┐
│           Abstraction            │       │         Implementation            │
│──────────────────────────────────│       │──────────────────────────────────│
│  - impl: Implementation          │──────▶│  + operationImpl(): void         │
│──────────────────────────────────│       └──────────────────────────────────┘
│  + operation(): void             │                      ▲
│    delegates to impl             │          ┌───────────┴───────────┐
└──────────────────────────────────┘          │                       │
              ▲                    ┌───────────────────┐  ┌───────────────────┐
              │                    │ConcreteImplA      │  │ConcreteImplB      │
   ┌──────────┴──────────┐        │───────────────────│  │───────────────────│
   │  RefinedAbstraction │        │+ operationImpl()  │  │+ operationImpl()  │
   │─────────────────────│        └───────────────────┘  └───────────────────┘
   │+ extendedOperation()│
   └─────────────────────┘

  Client creates a ConcreteImpl and passes it to an Abstraction (or RefinedAbstraction).
  The Abstraction exposes a high-level API; ConcreteImpl handles low-level details.
```

---

## Participants

| Participant | Role |
|---|---|
| **Abstraction** | Defines the high-level control interface. Maintains a reference to an `Implementation` object. |
| **RefinedAbstraction** | Extends the `Abstraction` interface with additional logic while still delegating implementation work. |
| **Implementation** | Declares the interface for all concrete implementations. This interface only needs to provide primitive operations that `Abstraction` composes into higher-level operations. |
| **ConcreteImplementation** | Contains platform/variant-specific code. Implements the `Implementation` interface. |
| **Client** | Constructs and assembles objects from both hierarchies and uses only the `Abstraction` interface at runtime. |

---

## How It Works

1. **Define the Implementation interface** with low-level primitive operations needed by the Abstraction.
2. **Create Concrete Implementations** — one per platform/variant — each implementing the primitive operations.
3. **Define the Abstraction class** that holds a reference (`impl`) to an `Implementation` object. Its public methods delegate to `impl`.
4. **Create Refined Abstractions** that inherit from `Abstraction` and add higher-level behavior, still relying on `impl` for primitives.
5. **At construction time** (or via a setter) the client injects the desired `ConcreteImplementation` into the `Abstraction`. This is the "bridge."
6. **At runtime** the client calls methods on the Abstraction. The Abstraction orchestrates its own logic and calls `impl` whenever platform-specific work is needed.
7. **Swapping implementations** requires only changing which `ConcreteImplementation` is injected — no changes to the Abstraction hierarchy and no changes to client code.

---

## Code Examples

### Python

```python
"""
Bridge Pattern — Notification System

A notification center that supports multiple notification types
(EmailNotification, SMSNotification) sent via multiple messaging platforms
(SendGrid, Twilio, SMTP). The "what" (notification shape) is separated from
the "how" (delivery platform).

Run:
    python bridge_notification.py
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import textwrap
from datetime import datetime


# ---------------------------------------------------------------------------
# Implementation hierarchy — the "how": messaging platform low-level API
# ---------------------------------------------------------------------------

class MessageSender(ABC):
    """Low-level interface every messaging back-end must implement."""

    @abstractmethod
    def send_message(self, recipient: str, subject: str, body: str) -> None: ...

    @abstractmethod
    def platform_name(self) -> str: ...


class SMTPSender(MessageSender):
    """Concrete implementation: plain SMTP email."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port

    def platform_name(self) -> str:
        return f"SMTP({self._host}:{self._port})"

    def send_message(self, recipient: str, subject: str, body: str) -> None:
        # In production this would open an SMTP connection.
        print(
            f"[{self.platform_name()}] → {recipient}\n"
            f"  Subject : {subject}\n"
            f"  Body    : {textwrap.shorten(body, 60)}\n"
        )


class SendGridSender(MessageSender):
    """Concrete implementation: SendGrid HTTP API."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key[:8] + "..."  # mask for demo

    def platform_name(self) -> str:
        return f"SendGrid(key={self._api_key})"

    def send_message(self, recipient: str, subject: str, body: str) -> None:
        print(
            f"[{self.platform_name()}] POST /v3/mail/send → {recipient}\n"
            f"  Subject : {subject}\n"
            f"  Body    : {textwrap.shorten(body, 60)}\n"
        )


class TwilioSender(MessageSender):
    """Concrete implementation: Twilio SMS API."""

    def __init__(self, account_sid: str, from_number: str) -> None:
        self._sid = account_sid
        self._from = from_number

    def platform_name(self) -> str:
        return f"Twilio({self._from})"

    def send_message(self, recipient: str, subject: str, body: str) -> None:
        # SMS ignores subject; body is truncated to 160 chars.
        sms_body = f"[{subject}] {body}"[:160]
        print(
            f"[{self.platform_name()}] → {recipient}\n"
            f"  SMS: {sms_body}\n"
        )


# ---------------------------------------------------------------------------
# Abstraction hierarchy — the "what": notification shape and business logic
# ---------------------------------------------------------------------------

class Notification(ABC):
    """
    Abstraction. Holds a reference to a MessageSender (the bridge).
    Subclasses add notification-type-specific structure.
    """

    def __init__(self, sender: MessageSender) -> None:
        self._sender = sender  # the bridge

    @abstractmethod
    def notify(self, recipient: str, **context) -> None: ...

    def _send(self, recipient: str, subject: str, body: str) -> None:
        """Delegates actual delivery to the implementation."""
        self._sender.send_message(recipient, subject, body)

    def switch_sender(self, sender: MessageSender) -> None:
        """Bridge can be replaced at runtime (useful for fallback logic)."""
        self._sender = sender


class AlertNotification(Notification):
    """Refined abstraction: urgent system alert with severity level."""

    LEVELS = ("INFO", "WARNING", "CRITICAL")

    def notify(self, recipient: str, **context) -> None:
        level = context.get("level", "INFO").upper()
        message = context.get("message", "")
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        subject = f"[{level}] System Alert"
        body = (
            f"Severity  : {level}\n"
            f"Time      : {timestamp}\n"
            f"Details   : {message}\n"
        )
        self._send(recipient, subject, body)


class InvoiceNotification(Notification):
    """Refined abstraction: invoice-ready notification with line-item summary."""

    def notify(self, recipient: str, **context) -> None:
        invoice_id = context.get("invoice_id", "INV-???")
        amount = context.get("amount", 0.0)
        due_date = context.get("due_date", "N/A")

        subject = f"Invoice {invoice_id} Ready"
        body = (
            f"Invoice ID : {invoice_id}\n"
            f"Amount Due : ${amount:,.2f}\n"
            f"Due Date   : {due_date}\n"
            f"Please log in to your account to view and pay.\n"
        )
        self._send(recipient, subject, body)


class WelcomeNotification(Notification):
    """Refined abstraction: user onboarding welcome message."""

    def notify(self, recipient: str, **context) -> None:
        username = context.get("username", "User")
        plan = context.get("plan", "Free")

        subject = "Welcome to Acme Corp!"
        body = (
            f"Hi {username},\n\n"
            f"Your account has been created on the {plan} plan.\n"
            f"Get started at https://app.acme.corp\n"
        )
        self._send(recipient, subject, body)


# ---------------------------------------------------------------------------
# Client code
# ---------------------------------------------------------------------------

def main() -> None:
    smtp = SMTPSender("mail.acme.corp", 587)
    sendgrid = SendGridSender("SG.XXXXXXXXXXXXXXXXXXXXXXXXXXXX")
    twilio = TwilioSender("AC123abc", "+15550001234")

    print("=" * 60)
    print("Scenario 1: System alert via SMTP")
    print("=" * 60)
    alert = AlertNotification(smtp)
    alert.notify(
        "ops-team@acme.corp",
        level="CRITICAL",
        message="Database connection pool exhausted (pool_size=50).",
    )

    print("=" * 60)
    print("Scenario 2: Invoice email via SendGrid")
    print("=" * 60)
    invoice = InvoiceNotification(sendgrid)
    invoice.notify(
        "customer@example.com",
        invoice_id="INV-20260609-0042",
        amount=1_249.99,
        due_date="2026-06-30",
    )

    print("=" * 60)
    print("Scenario 3: Welcome SMS via Twilio")
    print("=" * 60)
    welcome = WelcomeNotification(twilio)
    welcome.notify("alice@example.com", username="Alice", plan="Pro")

    print("=" * 60)
    print("Scenario 4: Runtime sender swap (primary SMTP → fallback SendGrid)")
    print("=" * 60)
    alert2 = AlertNotification(smtp)
    alert2.notify("ops@acme.corp", level="WARNING", message="High CPU usage detected.")
    print("  [SMTP failed — switching to SendGrid fallback]")
    alert2.switch_sender(sendgrid)
    alert2.notify("ops@acme.corp", level="WARNING", message="High CPU usage detected.")


if __name__ == "__main__":
    main()
```

---

### Java

```java
/**
 * Bridge Pattern — Cross-platform UI Rendering
 *
 * A widget library (Button, Checkbox) that works across multiple rendering
 * back-ends (OpenGL, DirectX, HTML Canvas). Adding a new widget or a new
 * renderer requires touching only one hierarchy.
 *
 * Compile & run:
 *   javac bridge/*.java && java bridge.Client
 */
package bridge;

// ---------------------------------------------------------------------------
// Implementation hierarchy — rendering back-end
// ---------------------------------------------------------------------------

interface Renderer {
    void drawRect(int x, int y, int width, int height, String color);
    void drawText(int x, int y, String text, int fontSize, String color);
    void drawCircle(int cx, int cy, int radius, String color);
    String name();
}

class OpenGLRenderer implements Renderer {
    @Override public String name() { return "OpenGL"; }

    @Override
    public void drawRect(int x, int y, int width, int height, String color) {
        System.out.printf("[OpenGL] glBegin(GL_QUADS) rect(%d,%d,%d,%d) fill=%s%n",
                x, y, width, height, color);
    }

    @Override
    public void drawText(int x, int y, String text, int fontSize, String color) {
        System.out.printf("[OpenGL] renderText(\"%s\") at (%d,%d) size=%d color=%s%n",
                text, x, y, fontSize, color);
    }

    @Override
    public void drawCircle(int cx, int cy, int radius, String color) {
        System.out.printf("[OpenGL] gluDisk circle(%d,%d) r=%d fill=%s%n",
                cx, cy, radius, color);
    }
}

class DirectXRenderer implements Renderer {
    @Override public String name() { return "DirectX"; }

    @Override
    public void drawRect(int x, int y, int width, int height, String color) {
        System.out.printf("[DirectX] DrawPrimitive D3DPT_TRIANGLESTRIP rect(%d,%d,%d,%d) color=%s%n",
                x, y, width, height, color);
    }

    @Override
    public void drawText(int x, int y, String text, int fontSize, String color) {
        System.out.printf("[DirectX] ID3DXFont::DrawText(\"%s\") at (%d,%d) size=%d color=%s%n",
                text, x, y, fontSize, color);
    }

    @Override
    public void drawCircle(int cx, int cy, int radius, String color) {
        System.out.printf("[DirectX] DrawCircle at (%d,%d) r=%d color=%s%n",
                cx, cy, radius, color);
    }
}

class HTMLCanvasRenderer implements Renderer {
    @Override public String name() { return "HTML Canvas"; }

    @Override
    public void drawRect(int x, int y, int width, int height, String color) {
        System.out.printf("[Canvas] ctx.fillRect(%d,%d,%d,%d); fillStyle='%s'%n",
                x, y, width, height, color);
    }

    @Override
    public void drawText(int x, int y, String text, int fontSize, String color) {
        System.out.printf("[Canvas] ctx.fillText(\"%s\",%d,%d); font='%dpx sans'; fillStyle='%s'%n",
                text, x, y, fontSize, color);
    }

    @Override
    public void drawCircle(int cx, int cy, int radius, String color) {
        System.out.printf("[Canvas] ctx.arc(%d,%d,%d,0,2*Math.PI); fillStyle='%s'%n",
                cx, cy, radius, color);
    }
}

// ---------------------------------------------------------------------------
// Abstraction hierarchy — UI widgets
// ---------------------------------------------------------------------------

abstract class Widget {
    protected Renderer renderer; // the bridge
    protected int x, y;
    protected boolean enabled = true;

    Widget(int x, int y, Renderer renderer) {
        this.x = x;
        this.y = y;
        this.renderer = renderer;
    }

    /** Switch renderer at runtime — e.g., for theme changes or offscreen rendering. */
    public void setRenderer(Renderer renderer) {
        this.renderer = renderer;
    }

    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
    }

    public abstract void draw();
    public abstract void onClick();
}

class Button extends Widget {
    private final String label;
    private final int width;
    private final int height;

    Button(int x, int y, int width, int height, String label, Renderer renderer) {
        super(x, y, renderer);
        this.label = label;
        this.width = width;
        this.height = height;
    }

    @Override
    public void draw() {
        String bgColor = enabled ? "#4A90D9" : "#AAAAAA";
        String textColor = "#FFFFFF";
        // Draw background rectangle
        renderer.drawRect(x, y, width, height, bgColor);
        // Center text inside the button
        int textX = x + width / 2 - (label.length() * 4);
        int textY = y + height / 2 + 5;
        renderer.drawText(textX, textY, label, 14, textColor);
        System.out.printf("  [Button '%s' drawn via %s]%n", label, renderer.name());
    }

    @Override
    public void onClick() {
        if (enabled) {
            System.out.printf("  [Button '%s' clicked]%n", label);
        } else {
            System.out.printf("  [Button '%s' is disabled — click ignored]%n", label);
        }
    }
}

class Checkbox extends Widget {
    private final String label;
    private boolean checked;

    Checkbox(int x, int y, String label, boolean checked, Renderer renderer) {
        super(x, y, renderer);
        this.label = label;
        this.checked = checked;
    }

    @Override
    public void draw() {
        // Draw the checkbox square
        renderer.drawRect(x, y, 16, 16, "#FFFFFF");
        // Draw checkmark as a small filled square if checked
        if (checked) {
            renderer.drawRect(x + 3, y + 3, 10, 10, "#4A90D9");
        }
        // Draw label to the right
        renderer.drawText(x + 22, y + 13, label, 13, "#333333");
        System.out.printf("  [Checkbox '%s' (%s) drawn via %s]%n",
                label, checked ? "checked" : "unchecked", renderer.name());
    }

    @Override
    public void onClick() {
        if (enabled) {
            checked = !checked;
            System.out.printf("  [Checkbox '%s' toggled → %s]%n", label, checked);
        }
    }
}

class RadioButton extends Widget {
    private final String label;
    private boolean selected;

    RadioButton(int x, int y, String label, boolean selected, Renderer renderer) {
        super(x, y, renderer);
        this.label = label;
        this.selected = selected;
    }

    @Override
    public void draw() {
        // Outer circle (border)
        renderer.drawCircle(x + 8, y + 8, 8, "#AAAAAA");
        // Inner circle (fill if selected)
        if (selected) {
            renderer.drawCircle(x + 8, y + 8, 4, "#4A90D9");
        }
        renderer.drawText(x + 22, y + 13, label, 13, "#333333");
        System.out.printf("  [RadioButton '%s' (%s) drawn via %s]%n",
                label, selected ? "selected" : "unselected", renderer.name());
    }

    @Override
    public void onClick() {
        if (enabled) {
            selected = true;
            System.out.printf("  [RadioButton '%s' selected]%n", label);
        }
    }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

class Client {
    public static void main(String[] args) {
        Renderer opengl = new OpenGLRenderer();
        Renderer directx = new DirectXRenderer();
        Renderer canvas  = new HTMLCanvasRenderer();

        System.out.println("=== Desktop window (OpenGL) ===");
        Button saveBtn = new Button(100, 200, 120, 36, "Save", opengl);
        Checkbox rememberMe = new Checkbox(100, 250, "Remember me", false, opengl);
        RadioButton optA = new RadioButton(100, 280, "Option A", true, opengl);
        saveBtn.draw();
        rememberMe.draw();
        optA.draw();
        saveBtn.onClick();
        rememberMe.onClick();

        System.out.println("\n=== Same widgets redrawn with DirectX renderer ===");
        saveBtn.setRenderer(directx);
        rememberMe.setRenderer(directx);
        optA.setRenderer(directx);
        saveBtn.draw();
        rememberMe.draw();
        optA.draw();

        System.out.println("\n=== Web export (HTML Canvas) ===");
        Button loginBtn = new Button(10, 10, 100, 32, "Log In", canvas);
        Checkbox terms = new Checkbox(10, 60, "Accept terms", true, canvas);
        loginBtn.draw();
        terms.draw();
        loginBtn.setEnabled(false);
        loginBtn.onClick();
    }
}
```

---

### C++

```cpp
/**
 * Bridge Pattern — Device & Remote Control
 *
 * A universal remote control library. Remote controls (BasicRemote,
 * AdvancedRemote) work with any Device (TV, Radio, Projector) through a
 * shared Device interface. New devices or new remote control types can be
 * added independently.
 *
 * Compile: g++ -std=c++17 -o bridge bridge.cpp && ./bridge
 */

#include <iostream>
#include <string>
#include <memory>
#include <algorithm>
#include <iomanip>

// ---------------------------------------------------------------------------
// Implementation hierarchy — devices
// ---------------------------------------------------------------------------

class Device {
public:
    virtual ~Device() = default;
    virtual bool isEnabled() const = 0;
    virtual void enable()  = 0;
    virtual void disable() = 0;
    virtual int  getVolume() const = 0;
    virtual void setVolume(int volume) = 0;
    virtual int  getChannel() const = 0;
    virtual void setChannel(int channel) = 0;
    virtual std::string status() const = 0;
};

class TV : public Device {
    bool enabled_   = false;
    int  volume_    = 30;
    int  channel_   = 1;
    static constexpr int MAX_CHANNEL = 99;
public:
    bool isEnabled() const override { return enabled_; }
    void enable()  override { enabled_ = true;  std::cout << "[TV] Powered ON\n"; }
    void disable() override { enabled_ = false; std::cout << "[TV] Powered OFF\n"; }

    int  getVolume() const override { return volume_; }
    void setVolume(int v) override {
        volume_ = std::clamp(v, 0, 100);
        std::cout << "[TV] Volume set to " << volume_ << "\n";
    }

    int  getChannel() const override { return channel_; }
    void setChannel(int ch) override {
        channel_ = std::clamp(ch, 1, MAX_CHANNEL);
        std::cout << "[TV] Channel set to " << channel_ << "\n";
    }

    std::string status() const override {
        return std::string("[TV] ") + (enabled_ ? "ON" : "OFF") +
               " | Vol: " + std::to_string(volume_) +
               " | Ch: "  + std::to_string(channel_);
    }
};

class Radio : public Device {
    bool enabled_ = false;
    int  volume_  = 50;
    int  channel_ = 88;   // FM frequency as integer (88 = 88.0 MHz)
public:
    bool isEnabled() const override { return enabled_; }
    void enable()  override { enabled_ = true;  std::cout << "[Radio] Powered ON\n"; }
    void disable() override { enabled_ = false; std::cout << "[Radio] Powered OFF\n"; }

    int  getVolume() const override { return volume_; }
    void setVolume(int v) override {
        volume_ = std::clamp(v, 0, 100);
        std::cout << "[Radio] Volume set to " << volume_ << "\n";
    }

    int  getChannel() const override { return channel_; }
    void setChannel(int ch) override {
        channel_ = std::clamp(ch, 87, 108);
        std::cout << "[Radio] Frequency set to " << channel_ << ".0 MHz\n";
    }

    std::string status() const override {
        return std::string("[Radio] ") + (enabled_ ? "ON" : "OFF") +
               " | Vol: " + std::to_string(volume_) +
               " | FM: "  + std::to_string(channel_) + ".0 MHz";
    }
};

class Projector : public Device {
    bool enabled_  = false;
    int  volume_   = 20;
    int  channel_  = 1;
    int  brightness_ = 80;
public:
    bool isEnabled() const override { return enabled_; }
    void enable()  override { enabled_ = true;  std::cout << "[Projector] Lamp ON — warming up...\n"; }
    void disable() override { enabled_ = false; std::cout << "[Projector] Lamp OFF — cooling down...\n"; }

    int  getVolume() const override { return volume_; }
    void setVolume(int v) override {
        volume_ = std::clamp(v, 0, 100);
        std::cout << "[Projector] Volume: " << volume_ << "\n";
    }

    int  getChannel() const override { return channel_; }
    void setChannel(int ch) override {
        channel_ = std::max(1, ch);
        std::cout << "[Projector] Input source: HDMI-" << channel_ << "\n";
    }

    std::string status() const override {
        return std::string("[Projector] ") + (enabled_ ? "ON" : "OFF") +
               " | Vol: " + std::to_string(volume_) +
               " | HDMI-" + std::to_string(channel_) +
               " | Brightness: " + std::to_string(brightness_);
    }
};

// ---------------------------------------------------------------------------
// Abstraction hierarchy — remote controls
// ---------------------------------------------------------------------------

class RemoteControl {
protected:
    std::shared_ptr<Device> device_; // the bridge

public:
    explicit RemoteControl(std::shared_ptr<Device> device)
        : device_(std::move(device)) {}

    virtual ~RemoteControl() = default;

    void togglePower() {
        if (device_->isEnabled()) device_->disable();
        else                       device_->enable();
    }

    void volumeDown() { device_->setVolume(device_->getVolume() - 10); }
    void volumeUp()   { device_->setVolume(device_->getVolume() + 10); }
    void channelDown(){ device_->setChannel(device_->getChannel() - 1); }
    void channelUp()  { device_->setChannel(device_->getChannel() + 1); }

    void printStatus() const {
        std::cout << "Status: " << device_->status() << "\n";
    }
};

// Refined abstraction — adds mute, favourites, and preset channels
class AdvancedRemote : public RemoteControl {
    int  savedVolume_  = -1;
    bool muted_        = false;

public:
    using RemoteControl::RemoteControl;

    void mute() {
        if (!muted_) {
            savedVolume_ = device_->getVolume();
            device_->setVolume(0);
            muted_ = true;
            std::cout << "[AdvancedRemote] Muted (saved vol=" << savedVolume_ << ")\n";
        } else {
            device_->setVolume(savedVolume_);
            muted_ = false;
            std::cout << "[AdvancedRemote] Unmuted → vol=" << savedVolume_ << "\n";
        }
    }

    void goToChannel(int ch) {
        std::cout << "[AdvancedRemote] Direct channel input: " << ch << "\n";
        device_->setChannel(ch);
    }

    void setFavouriteVolume(int vol) {
        std::cout << "[AdvancedRemote] Favourite volume set to " << vol << "\n";
        savedVolume_ = vol;
    }
};

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

int main() {
    auto tv        = std::make_shared<TV>();
    auto radio     = std::make_shared<Radio>();
    auto projector = std::make_shared<Projector>();

    std::cout << "=== Basic Remote + TV ===\n";
    RemoteControl basicTv(tv);
    basicTv.togglePower();
    basicTv.volumeUp();
    basicTv.volumeUp();
    basicTv.channelUp();
    basicTv.channelUp();
    basicTv.channelUp();
    basicTv.printStatus();

    std::cout << "\n=== Advanced Remote + Radio ===\n";
    AdvancedRemote advRadio(radio);
    advRadio.togglePower();
    advRadio.volumeUp();
    advRadio.goToChannel(103);   // 103.0 MHz
    advRadio.mute();
    advRadio.mute();             // unmute
    advRadio.printStatus();

    std::cout << "\n=== Advanced Remote + Projector ===\n";
    AdvancedRemote advProj(projector);
    advProj.togglePower();
    advProj.goToChannel(2);      // HDMI-2
    advProj.volumeUp();
    advProj.mute();
    advProj.printStatus();
    advProj.togglePower();

    return 0;
}
```

---

### C#

```csharp
/**
 * Bridge Pattern — Data Export System
 *
 * Reports (SalesReport, InventoryReport) can be exported via multiple
 * format renderers (CsvExporter, JsonExporter, XmlExporter). New report
 * types and new export formats grow independently.
 *
 * Dotnet run: dotnet script bridge.csx  (or paste into a Console project)
 */

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

// ---------------------------------------------------------------------------
// Implementation hierarchy — export format back-ends
// ---------------------------------------------------------------------------

interface IExporter
{
    string FormatName { get; }
    string Export(string title, IReadOnlyList<string> headers, IReadOnlyList<IReadOnlyList<object>> rows);
}

class CsvExporter : IExporter
{
    public string FormatName => "CSV";

    public string Export(string title, IReadOnlyList<string> headers, IReadOnlyList<IReadOnlyList<object>> rows)
    {
        var sb = new StringBuilder();
        sb.AppendLine($"# {title}");
        sb.AppendLine(string.Join(",", headers.Select(Escape)));
        foreach (var row in rows)
            sb.AppendLine(string.Join(",", row.Select(v => Escape(v?.ToString() ?? ""))));
        return sb.ToString();
    }

    private static string Escape(string s) =>
        s.Contains(',') || s.Contains('"') || s.Contains('\n')
            ? $"\"{s.Replace("\"", "\"\"")}\""
            : s;
}

class JsonExporter : IExporter
{
    public string FormatName => "JSON";

    public string Export(string title, IReadOnlyList<string> headers, IReadOnlyList<IReadOnlyList<object>> rows)
    {
        var sb = new StringBuilder();
        sb.AppendLine("{");
        sb.AppendLine($"  \"title\": \"{title}\",");
        sb.AppendLine("  \"data\": [");
        for (int i = 0; i < rows.Count; i++)
        {
            sb.Append("    {");
            var fields = headers.Zip(rows[i], (h, v) => $"\"{h}\": \"{v}\"");
            sb.Append(string.Join(", ", fields));
            sb.Append(i < rows.Count - 1 ? "}," : "}");
            sb.AppendLine();
        }
        sb.AppendLine("  ]");
        sb.AppendLine("}");
        return sb.ToString();
    }
}

class XmlExporter : IExporter
{
    public string FormatName => "XML";

    public string Export(string title, IReadOnlyList<string> headers, IReadOnlyList<IReadOnlyList<object>> rows)
    {
        var sb = new StringBuilder();
        sb.AppendLine("<?xml version=\"1.0\" encoding=\"UTF-8\"?>");
        sb.AppendLine($"<report title=\"{title}\">");
        foreach (var row in rows)
        {
            sb.AppendLine("  <row>");
            for (int c = 0; c < headers.Count; c++)
                sb.AppendLine($"    <{headers[c]}>{row[c]}</{headers[c]}>");
            sb.AppendLine("  </row>");
        }
        sb.AppendLine("</report>");
        return sb.ToString();
    }
}

// ---------------------------------------------------------------------------
// Abstraction hierarchy — report types
// ---------------------------------------------------------------------------

abstract class Report
{
    protected IExporter Exporter; // the bridge

    protected Report(IExporter exporter) => Exporter = exporter;

    /// <summary>Switch exporter at runtime (e.g., from CSV to JSON on user request).</summary>
    public void SwitchExporter(IExporter exporter) => Exporter = exporter;

    public string Generate()
    {
        var (title, headers, rows) = BuildData();
        Console.WriteLine($"[{GetType().Name}] Generating via {Exporter.FormatName}...");
        return Exporter.Export(title, headers, rows);
    }

    protected abstract (string Title, IReadOnlyList<string> Headers, IReadOnlyList<IReadOnlyList<object>> Rows) BuildData();
}

class SalesReport : Report
{
    private readonly DateTime _from;
    private readonly DateTime _to;

    public SalesReport(IExporter exporter, DateTime from, DateTime to)
        : base(exporter)
    {
        _from = from;
        _to   = to;
    }

    protected override (string, IReadOnlyList<string>, IReadOnlyList<IReadOnlyList<object>>) BuildData()
    {
        // Simulate fetching sales data from a database
        var title   = $"Sales Report {_from:yyyy-MM-dd} to {_to:yyyy-MM-dd}";
        var headers = new[] { "Date", "Product", "Units", "Revenue" };
        var rows    = new List<IReadOnlyList<object>>
        {
            new object[] { "2026-06-01", "Widget Pro",   120, "$14,400.00" },
            new object[] { "2026-06-02", "Widget Lite",  340, "$10,200.00" },
            new object[] { "2026-06-03", "Widget Pro",    95, "$11,400.00" },
            new object[] { "2026-06-04", "Gadget Max",    60, "$18,000.00" },
        };
        return (title, headers, rows);
    }
}

class InventoryReport : Report
{
    private readonly string _warehouse;

    public InventoryReport(IExporter exporter, string warehouse) : base(exporter)
        => _warehouse = warehouse;

    protected override (string, IReadOnlyList<string>, IReadOnlyList<IReadOnlyList<object>>) BuildData()
    {
        var title   = $"Inventory Report — Warehouse: {_warehouse}";
        var headers = new[] { "SKU", "Product", "OnHand", "Reserved", "Available", "ReorderPoint" };
        var rows    = new List<IReadOnlyList<object>>
        {
            new object[] { "WP-001", "Widget Pro",   500, 120, 380, 150 },
            new object[] { "WL-002", "Widget Lite", 1200, 340, 860, 300 },
            new object[] { "GM-003", "Gadget Max",    80,  20,  60,  50 },
            new object[] { "AC-010", "Accessory Kit", 300,  45, 255, 100 },
        };
        return (title, headers, rows);
    }
}

class AuditReport : Report
{
    public AuditReport(IExporter exporter) : base(exporter) { }

    protected override (string, IReadOnlyList<string>, IReadOnlyList<IReadOnlyList<object>>) BuildData()
    {
        var title   = $"Audit Log — {DateTime.UtcNow:yyyy-MM-dd}";
        var headers = new[] { "Timestamp", "User", "Action", "Resource", "Result" };
        var rows    = new List<IReadOnlyList<object>>
        {
            new object[] { "2026-06-09T08:01:00Z", "alice",  "LOGIN",  "auth-service",  "OK"     },
            new object[] { "2026-06-09T08:05:12Z", "alice",  "READ",   "sales-report",  "OK"     },
            new object[] { "2026-06-09T08:10:45Z", "bob",    "DELETE", "customer/4492", "DENIED" },
            new object[] { "2026-06-09T09:00:01Z", "system", "BACKUP", "database",      "OK"     },
        };
        return (title, headers, rows);
    }
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

class Program
{
    static void Main()
    {
        var csv  = new CsvExporter();
        var json = new JsonExporter();
        var xml  = new XmlExporter();

        Console.WriteLine("=== Sales Report → CSV ===");
        var sales = new SalesReport(csv, new DateTime(2026, 6, 1), new DateTime(2026, 6, 4));
        Console.WriteLine(sales.Generate());

        Console.WriteLine("=== Inventory Report → JSON ===");
        var inventory = new InventoryReport(json, "WAREHOUSE-EU-01");
        Console.WriteLine(inventory.Generate());

        Console.WriteLine("=== Audit Report → XML ===");
        var audit = new AuditReport(xml);
        Console.WriteLine(audit.Generate());

        Console.WriteLine("=== Sales Report: switch from CSV to JSON at runtime ===");
        sales.SwitchExporter(json);
        Console.WriteLine(sales.Generate());
    }
}
```

---

### TypeScript

```typescript
/**
 * Bridge Pattern — Payment Processing
 *
 * Payment types (OneTimePayment, SubscriptionPayment, RefundPayment) are
 * processed by multiple payment gateways (StripeGateway, PayPalGateway,
 * BraintreeGateway). Both dimensions are extensible independently.
 *
 * Run: npx ts-node bridge.ts
 */

// ---------------------------------------------------------------------------
// Implementation hierarchy — payment gateways
// ---------------------------------------------------------------------------

interface PaymentGateway {
  readonly name: string;
  charge(amount: number, currency: string, token: string, metadata: Record<string, string>): Promise<GatewayResult>;
  refund(transactionId: string, amount: number): Promise<GatewayResult>;
  createSubscription(planId: string, token: string, metadata: Record<string, string>): Promise<GatewayResult>;
}

interface GatewayResult {
  success: boolean;
  transactionId?: string;
  subscriptionId?: string;
  errorMessage?: string;
  rawResponse: Record<string, unknown>;
}

class StripeGateway implements PaymentGateway {
  readonly name = "Stripe";

  constructor(private readonly apiKey: string) {}

  async charge(amount: number, currency: string, token: string, metadata: Record<string, string>): Promise<GatewayResult> {
    // Simulate Stripe PaymentIntent API call
    console.log(`[Stripe] POST /v1/payment_intents { amount: ${amount}, currency: ${currency}, token: ${token} }`);
    const txId = `pi_${Math.random().toString(36).slice(2, 14)}`;
    return {
      success: true,
      transactionId: txId,
      rawResponse: { id: txId, status: "succeeded", amount, currency, metadata },
    };
  }

  async refund(transactionId: string, amount: number): Promise<GatewayResult> {
    console.log(`[Stripe] POST /v1/refunds { payment_intent: ${transactionId}, amount: ${amount} }`);
    return {
      success: true,
      transactionId: `re_${Math.random().toString(36).slice(2, 12)}`,
      rawResponse: { status: "succeeded", amount },
    };
  }

  async createSubscription(planId: string, token: string, metadata: Record<string, string>): Promise<GatewayResult> {
    console.log(`[Stripe] POST /v1/subscriptions { plan: ${planId}, payment_method: ${token} }`);
    const subId = `sub_${Math.random().toString(36).slice(2, 12)}`;
    return {
      success: true,
      subscriptionId: subId,
      rawResponse: { id: subId, status: "active", plan: planId, metadata },
    };
  }
}

class PayPalGateway implements PaymentGateway {
  readonly name = "PayPal";

  constructor(private readonly clientId: string, private readonly secret: string) {}

  async charge(amount: number, currency: string, token: string, metadata: Record<string, string>): Promise<GatewayResult> {
    console.log(`[PayPal] POST /v2/checkout/orders { amount: ${amount} ${currency}, token: ${token} }`);
    const txId = `PAYID-${Date.now()}-${Math.floor(Math.random() * 9999)}`;
    return {
      success: true,
      transactionId: txId,
      rawResponse: { id: txId, status: "COMPLETED", purchase_units: [{ amount: { value: amount, currency_code: currency } }] },
    };
  }

  async refund(transactionId: string, amount: number): Promise<GatewayResult> {
    console.log(`[PayPal] POST /v2/payments/captures/${transactionId}/refund { amount: ${amount} }`);
    return {
      success: true,
      transactionId: `REF-${Date.now()}`,
      rawResponse: { status: "COMPLETED" },
    };
  }

  async createSubscription(planId: string, token: string, metadata: Record<string, string>): Promise<GatewayResult> {
    console.log(`[PayPal] POST /v1/billing/subscriptions { plan_id: ${planId} }`);
    const subId = `I-${Math.random().toString(36).slice(2, 12).toUpperCase()}`;
    return {
      success: true,
      subscriptionId: subId,
      rawResponse: { id: subId, status: "ACTIVE", plan_id: planId },
    };
  }
}

// ---------------------------------------------------------------------------
// Abstraction hierarchy — payment types
// ---------------------------------------------------------------------------

interface PaymentResult {
  success: boolean;
  message: string;
  transactionId?: string;
  subscriptionId?: string;
}

abstract class Payment {
  constructor(protected gateway: PaymentGateway) {}

  /** Swap gateway at runtime — e.g., for fallback on gateway outage. */
  setGateway(gateway: PaymentGateway): void {
    console.log(`[Payment] Switching gateway from ${this.gateway.name} to ${gateway.name}`);
    this.gateway = gateway;
  }

  abstract process(): Promise<PaymentResult>;
}

class OneTimePayment extends Payment {
  constructor(
    gateway: PaymentGateway,
    private readonly amount: number,
    private readonly currency: string,
    private readonly paymentToken: string,
    private readonly orderId: string,
    private readonly customerId: string,
  ) {
    super(gateway);
  }

  async process(): Promise<PaymentResult> {
    console.log(`\n[OneTimePayment] Charging $${this.amount} ${this.currency} via ${this.gateway.name}`);
    const result = await this.gateway.charge(this.amount, this.currency, this.paymentToken, {
      orderId: this.orderId,
      customerId: this.customerId,
    });

    if (result.success) {
      return {
        success: true,
        message: `Charged $${this.amount} ${this.currency} successfully.`,
        transactionId: result.transactionId,
      };
    }
    return { success: false, message: `Charge failed: ${result.errorMessage}` };
  }
}

class SubscriptionPayment extends Payment {
  constructor(
    gateway: PaymentGateway,
    private readonly planId: string,
    private readonly paymentToken: string,
    private readonly userId: string,
    private readonly email: string,
  ) {
    super(gateway);
  }

  async process(): Promise<PaymentResult> {
    console.log(`\n[SubscriptionPayment] Creating subscription for plan '${this.planId}' via ${this.gateway.name}`);
    const result = await this.gateway.createSubscription(this.planId, this.paymentToken, {
      userId: this.userId,
      email: this.email,
    });

    if (result.success) {
      return {
        success: true,
        message: `Subscription '${this.planId}' created for ${this.email}.`,
        subscriptionId: result.subscriptionId,
      };
    }
    return { success: false, message: `Subscription failed: ${result.errorMessage}` };
  }
}

class RefundPayment extends Payment {
  constructor(
    gateway: PaymentGateway,
    private readonly originalTransactionId: string,
    private readonly refundAmount: number,
    private readonly reason: string,
  ) {
    super(gateway);
  }

  async process(): Promise<PaymentResult> {
    console.log(`\n[RefundPayment] Refunding $${this.refundAmount} for txn ${this.originalTransactionId} via ${this.gateway.name}`);
    console.log(`  Reason: ${this.reason}`);
    const result = await this.gateway.refund(this.originalTransactionId, this.refundAmount);

    if (result.success) {
      return {
        success: true,
        message: `Refunded $${this.refundAmount} for transaction ${this.originalTransactionId}.`,
        transactionId: result.transactionId,
      };
    }
    return { success: false, message: `Refund failed: ${result.errorMessage}` };
  }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const stripe = new StripeGateway("sk_live_XXXXXXXXXXXXXXXXXXXX");
  const paypal = new PayPalGateway("CLIENT_ID_XXX", "CLIENT_SECRET_XXX");

  // Scenario 1: One-time payment via Stripe
  const order = new OneTimePayment(stripe, 99.99, "USD", "tok_visa_4242", "ORD-1001", "CUST-555");
  const orderResult = await order.process();
  console.log("  Result:", orderResult.message, "| TxnID:", orderResult.transactionId);

  // Scenario 2: Subscription via PayPal
  const sub = new SubscriptionPayment(paypal, "plan_pro_monthly", "BA-XXXXXXXXXX", "USR-7890", "alice@example.com");
  const subResult = await sub.process();
  console.log("  Result:", subResult.message, "| SubID:", subResult.subscriptionId);

  // Scenario 3: Refund via Stripe
  const refund = new RefundPayment(stripe, "pi_abc123def456", 49.99, "Customer request — product defective");
  const refundResult = await refund.process();
  console.log("  Result:", refundResult.message);

  // Scenario 4: Gateway fallback at runtime
  console.log("\n=== Gateway Fallback Demo ===");
  const failingOrder = new OneTimePayment(stripe, 250.00, "EUR", "tok_eu_9999", "ORD-1002", "CUST-666");
  console.log("Primary gateway (Stripe) — simulating outage:");
  // Switch to PayPal as fallback
  failingOrder.setGateway(paypal);
  const fallbackResult = await failingOrder.process();
  console.log("  Fallback result:", fallbackResult.message, "| TxnID:", fallbackResult.transactionId);
}

main().catch(console.error);
```

---

### Go

```go
// Bridge Pattern — Logging System
//
// Loggers (ApplicationLogger, AuditLogger, MetricsLogger) write via multiple
// transport implementations (ConsoleTransport, FileTransport, ElasticsearchTransport).
// Both hierarchies extend independently.
//
// Run: go run bridge.go

package main

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// ---------------------------------------------------------------------------
// Implementation hierarchy — log transports
// ---------------------------------------------------------------------------

// LogEntry is the normalized log record passed to transports.
type LogEntry struct {
	Timestamp time.Time         `json:"timestamp"`
	Level     string            `json:"level"`
	Source    string            `json:"source"`
	Message   string            `json:"message"`
	Fields    map[string]string `json:"fields,omitempty"`
}

// Transport is the low-level delivery interface.
type Transport interface {
	Write(entry LogEntry) error
	Name() string
	Flush() error
}

// ConsoleTransport prints human-readable lines to stdout.
type ConsoleTransport struct {
	colored bool
}

func NewConsoleTransport(colored bool) *ConsoleTransport {
	return &ConsoleTransport{colored: colored}
}

func (t *ConsoleTransport) Name() string { return "console" }

func (t *ConsoleTransport) Write(entry LogEntry) error {
	levelStr := fmt.Sprintf("%-8s", entry.Level)
	if t.colored {
		switch entry.Level {
		case "ERROR", "FATAL":
			levelStr = "\033[31m" + levelStr + "\033[0m"
		case "WARN":
			levelStr = "\033[33m" + levelStr + "\033[0m"
		case "INFO":
			levelStr = "\033[32m" + levelStr + "\033[0m"
		case "DEBUG":
			levelStr = "\033[36m" + levelStr + "\033[0m"
		}
	}
	ts := entry.Timestamp.Format("2006-01-02T15:04:05Z")
	fieldsStr := ""
	for k, v := range entry.Fields {
		fieldsStr += fmt.Sprintf(" %s=%q", k, v)
	}
	fmt.Printf("[%s] %s [%s] %s%s\n", ts, levelStr, entry.Source, entry.Message, fieldsStr)
	return nil
}

func (t *ConsoleTransport) Flush() error { return nil }

// FileTransport simulates writing to a rotating log file.
type FileTransport struct {
	path    string
	written int
}

func NewFileTransport(path string) *FileTransport {
	return &FileTransport{path: path}
}

func (t *FileTransport) Name() string { return fmt.Sprintf("file(%s)", t.path) }

func (t *FileTransport) Write(entry LogEntry) error {
	ts := entry.Timestamp.Format(time.RFC3339)
	line := fmt.Sprintf("%s %s [%s] %s", ts, entry.Level, entry.Source, entry.Message)
	for k, v := range entry.Fields {
		line += fmt.Sprintf(" %s=%q", k, v)
	}
	// Simulate writing (in production, append to file)
	fmt.Printf("[FILE:%s] %s\n", t.path, line)
	t.written++
	return nil
}

func (t *FileTransport) Flush() error {
	fmt.Printf("[FILE:%s] Flushed %d entries\n", t.path, t.written)
	t.written = 0
	return nil
}

// ElasticsearchTransport ships log entries as JSON documents.
type ElasticsearchTransport struct {
	endpoint string
	index    string
	batch    []LogEntry
}

func NewElasticsearchTransport(endpoint, index string) *ElasticsearchTransport {
	return &ElasticsearchTransport{endpoint: endpoint, index: index}
}

func (t *ElasticsearchTransport) Name() string {
	return fmt.Sprintf("elasticsearch(%s/%s)", t.endpoint, t.index)
}

func (t *ElasticsearchTransport) Write(entry LogEntry) error {
	t.batch = append(t.batch, entry)
	// Simulate bulk-indexing threshold
	if len(t.batch) >= 3 {
		return t.Flush()
	}
	fmt.Printf("[ES] Buffered entry (batch size=%d)\n", len(t.batch))
	return nil
}

func (t *ElasticsearchTransport) Flush() error {
	if len(t.batch) == 0 {
		return nil
	}
	payload := make([]string, 0, len(t.batch)*2)
	for _, e := range t.batch {
		meta, _ := json.Marshal(map[string]any{"index": map[string]string{"_index": t.index}})
		doc, _  := json.Marshal(e)
		payload  = append(payload, string(meta), string(doc))
	}
	bulk := strings.Join(payload, "\n")
	fmt.Printf("[ES] POST %s/_bulk (%d docs)\n%s\n", t.endpoint, len(t.batch), bulk[:min(len(bulk), 200)]+"...")
	t.batch = t.batch[:0]
	return nil
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// ---------------------------------------------------------------------------
// Abstraction hierarchy — logger types
// ---------------------------------------------------------------------------

// Logger is the base abstraction.
type Logger struct {
	transport Transport // the bridge
	source    string
}

func NewLogger(source string, t Transport) *Logger {
	return &Logger{source: source, transport: t}
}

func (l *Logger) SetTransport(t Transport) { l.transport = t }

func (l *Logger) log(level, message string, fields map[string]string) {
	_ = l.transport.Write(LogEntry{
		Timestamp: time.Now().UTC(),
		Level:     level,
		Source:    l.source,
		Message:   message,
		Fields:    fields,
	})
}

func (l *Logger) Info(msg string, fields map[string]string)  { l.log("INFO", msg, fields) }
func (l *Logger) Warn(msg string, fields map[string]string)  { l.log("WARN", msg, fields) }
func (l *Logger) Error(msg string, fields map[string]string) { l.log("ERROR", msg, fields) }
func (l *Logger) Debug(msg string, fields map[string]string) { l.log("DEBUG", msg, fields) }
func (l *Logger) Flush()                                     { _ = l.transport.Flush() }

// ApplicationLogger — refined abstraction with request context helpers.
type ApplicationLogger struct {
	Logger
	service string
	version string
}

func NewApplicationLogger(service, version string, t Transport) *ApplicationLogger {
	return &ApplicationLogger{
		Logger:  Logger{source: service, transport: t},
		service: service,
		version: version,
	}
}

func (a *ApplicationLogger) baseFields() map[string]string {
	return map[string]string{"service": a.service, "version": a.version}
}

func (a *ApplicationLogger) RequestIn(method, path, requestID string) {
	f := a.baseFields()
	f["method"] = method
	f["path"] = path
	f["request_id"] = requestID
	a.Info("Request received", f)
}

func (a *ApplicationLogger) RequestOut(statusCode int, durationMs int64, requestID string) {
	f := a.baseFields()
	f["status_code"] = fmt.Sprintf("%d", statusCode)
	f["duration_ms"] = fmt.Sprintf("%d", durationMs)
	f["request_id"] = requestID
	if statusCode >= 500 {
		a.Error("Request completed with server error", f)
	} else {
		a.Info("Request completed", f)
	}
}

// AuditLogger — refined abstraction for compliance-grade audit trails.
type AuditLogger struct {
	Logger
}

func NewAuditLogger(t Transport) *AuditLogger {
	return &AuditLogger{Logger: Logger{source: "audit", transport: t}}
}

func (al *AuditLogger) RecordAction(actor, action, resource, result string) {
	al.log("AUDIT", fmt.Sprintf("%s performed %s on %s: %s", actor, action, resource, result),
		map[string]string{"actor": actor, "action": action, "resource": resource, "result": result})
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

func main() {
	console := NewConsoleTransport(true)
	file    := NewFileTransport("/var/log/acme/app.log")
	es      := NewElasticsearchTransport("https://es.acme.corp:9200", "logs-2026.06")

	fmt.Println("=== Application Logger → Console ===")
	appLog := NewApplicationLogger("order-service", "2.4.1", console)
	appLog.RequestIn("POST", "/api/orders", "req-abc-123")
	appLog.Info("Order validated", map[string]string{"order_id": "ORD-9876"})
	appLog.RequestOut(201, 45, "req-abc-123")

	fmt.Println("\n=== Application Logger → File ===")
	appLog.SetTransport(file)
	appLog.RequestIn("GET", "/api/products", "req-def-456")
	appLog.RequestOut(200, 12, "req-def-456")
	appLog.Flush()

	fmt.Println("\n=== Audit Logger → Elasticsearch ===")
	auditLog := NewAuditLogger(es)
	auditLog.RecordAction("alice", "READ",   "customer/4492", "ALLOWED")
	auditLog.RecordAction("bob",   "DELETE", "customer/4492", "DENIED")
	auditLog.RecordAction("alice", "UPDATE", "order/ORD-9876", "ALLOWED")
	auditLog.Flush() // flush any remaining buffered entries
}
```

---

### PHP

```php
<?php
/**
 * Bridge Pattern — Theme / Template Rendering Engine
 *
 * Page types (LandingPage, BlogPost, ProductPage) are rendered via multiple
 * template engines (TwigRenderer, BladeRenderer, MustacheRenderer).
 * New page types and new renderers extend independently.
 *
 * Run: php bridge.php
 */

declare(strict_types=1);

// ---------------------------------------------------------------------------
// Implementation hierarchy — template engines
// ---------------------------------------------------------------------------

interface TemplateRenderer
{
    public function renderBlock(string $name, array $variables): string;
    public function renderLayout(string $layout, array $blocks): string;
    public function engineName(): string;
}

class TwigRenderer implements TemplateRenderer
{
    public function engineName(): string { return 'Twig'; }

    public function renderBlock(string $name, array $variables): string
    {
        // Simulate Twig block compilation
        $vars = implode(', ', array_map(
            fn($k, $v) => "$k=\"$v\"",
            array_keys($variables),
            $variables
        ));
        return "[Twig:block:{$name}({$vars})]";
    }

    public function renderLayout(string $layout, array $blocks): string
    {
        $output  = "[Twig] {% extends '{$layout}.html.twig' %}\n";
        foreach ($blocks as $name => $content) {
            $output .= "  {% block {$name} %}{$content}{% endblock %}\n";
        }
        return $output;
    }
}

class BladeRenderer implements TemplateRenderer
{
    public function engineName(): string { return 'Blade'; }

    public function renderBlock(string $name, array $variables): string
    {
        $vars = implode(', ', array_map(
            fn($k, $v) => "\${$k}=\"$v\"",
            array_keys($variables),
            $variables
        ));
        return "[Blade:@include('{$name}', [{$vars}])]";
    }

    public function renderLayout(string $layout, array $blocks): string
    {
        $output  = "[Blade] @extends('{$layout}')\n";
        foreach ($blocks as $name => $content) {
            $output .= "  @section('{$name}'){$content}@endsection\n";
        }
        return $output;
    }
}

class MustacheRenderer implements TemplateRenderer
{
    public function engineName(): string { return 'Mustache'; }

    public function renderBlock(string $name, array $variables): string
    {
        $vars = json_encode($variables, JSON_UNESCAPED_SLASHES);
        return "[Mustache:{{>{$name}}} context={$vars}]";
    }

    public function renderLayout(string $layout, array $blocks): string
    {
        $output  = "[Mustache] partials layout='{$layout}'\n";
        foreach ($blocks as $name => $content) {
            $output .= "  {{#{$name}}}{$content}{{/{$name}}}\n";
        }
        return $output;
    }
}

// ---------------------------------------------------------------------------
// Abstraction hierarchy — page types
// ---------------------------------------------------------------------------

abstract class Page
{
    protected TemplateRenderer $renderer; // the bridge

    public function __construct(TemplateRenderer $renderer)
    {
        $this->renderer = $renderer;
    }

    public function switchRenderer(TemplateRenderer $renderer): void
    {
        echo sprintf(
            "  [Page] Switching renderer from %s to %s\n",
            $this->renderer->engineName(),
            $renderer->engineName()
        );
        $this->renderer = $renderer;
    }

    abstract public function render(): string;
}

class LandingPage extends Page
{
    public function __construct(
        TemplateRenderer $renderer,
        private readonly string $headline,
        private readonly string $subheadline,
        private readonly string $ctaLabel,
        private readonly string $ctaUrl,
    ) {
        parent::__construct($renderer);
    }

    public function render(): string
    {
        $hero = $this->renderer->renderBlock('hero', [
            'headline'    => $this->headline,
            'subheadline' => $this->subheadline,
        ]);

        $cta = $this->renderer->renderBlock('cta_button', [
            'label' => $this->ctaLabel,
            'url'   => $this->ctaUrl,
        ]);

        return $this->renderer->renderLayout('landing', [
            'hero' => $hero,
            'cta'  => $cta,
        ]);
    }
}

class BlogPost extends Page
{
    public function __construct(
        TemplateRenderer $renderer,
        private readonly string $title,
        private readonly string $author,
        private readonly string $publishedAt,
        private readonly string $body,
        private readonly array  $tags = [],
    ) {
        parent::__construct($renderer);
    }

    public function render(): string
    {
        $header = $this->renderer->renderBlock('post_header', [
            'title'       => $this->title,
            'author'      => $this->author,
            'publishedAt' => $this->publishedAt,
        ]);

        $content = $this->renderer->renderBlock('post_body', [
            'body' => substr($this->body, 0, 80) . '...',
        ]);

        $tagList = $this->renderer->renderBlock('tag_list', [
            'tags' => implode(', ', $this->tags),
        ]);

        return $this->renderer->renderLayout('blog_post', [
            'header'  => $header,
            'content' => $content,
            'tags'    => $tagList,
        ]);
    }
}

class ProductPage extends Page
{
    public function __construct(
        TemplateRenderer $renderer,
        private readonly string $sku,
        private readonly string $name,
        private readonly float  $price,
        private readonly string $description,
        private readonly int    $stock,
    ) {
        parent::__construct($renderer);
    }

    public function render(): string
    {
        $gallery = $this->renderer->renderBlock('product_gallery', [
            'sku'  => $this->sku,
            'name' => $this->name,
        ]);

        $info = $this->renderer->renderBlock('product_info', [
            'name'        => $this->name,
            'price'       => number_format($this->price, 2),
            'description' => substr($this->description, 0, 60) . '...',
            'stock'       => (string) $this->stock,
        ]);

        $addToCart = $this->renderer->renderBlock('add_to_cart', [
            'sku'      => $this->sku,
            'disabled' => $this->stock > 0 ? 'false' : 'true',
        ]);

        return $this->renderer->renderLayout('product', [
            'gallery'    => $gallery,
            'info'       => $info,
            'add_to_cart' => $addToCart,
        ]);
    }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

$twig     = new TwigRenderer();
$blade    = new BladeRenderer();
$mustache = new MustacheRenderer();

echo "=== Landing Page via Twig ===\n";
$landing = new LandingPage(
    renderer:    $twig,
    headline:    'Ship Faster with Acme Platform',
    subheadline: 'The all-in-one developer toolkit for modern teams.',
    ctaLabel:    'Start Free Trial',
    ctaUrl:      'https://acme.corp/trial',
);
echo $landing->render() . "\n";

echo "=== Blog Post via Blade ===\n";
$post = new BlogPost(
    renderer:    $blade,
    title:       'Understanding the Bridge Design Pattern',
    author:      'Jane Doe',
    publishedAt: '2026-06-09',
    body:        'The Bridge pattern is one of the most powerful structural patterns in object-oriented design...',
    tags:        ['design-patterns', 'oop', 'architecture'],
);
echo $post->render() . "\n";

echo "=== Product Page via Mustache ===\n";
$product = new ProductPage(
    renderer:    $mustache,
    sku:         'WP-001',
    name:        'Widget Pro',
    price:       119.99,
    description: 'The Widget Pro delivers professional-grade performance for demanding workflows.',
    stock:       42,
);
echo $product->render() . "\n";

echo "=== Runtime renderer switch: Blog Post Twig → Mustache ===\n";
$post->switchRenderer($mustache);
echo $post->render() . "\n";
```

---

### Ruby

```ruby
# Bridge Pattern — Cloud Storage / File Management
#
# File operations (FileUpload, FileDownload, FileDelete) are performed against
# multiple cloud storage back-ends (S3Storage, GCSStorage, AzureBlobStorage).
# Both hierarchies extend independently.
#
# Run: ruby bridge.rb

require 'digest'
require 'time'

# ---------------------------------------------------------------------------
# Implementation hierarchy — storage back-ends
# ---------------------------------------------------------------------------

module StorageBackend
  StorageResult = Struct.new(:success, :url, :etag, :error_message, keyword_init: true)

  class Base
    def upload(bucket, key, data, content_type: 'application/octet-stream', metadata: {})
      raise NotImplementedError
    end

    def download(bucket, key)
      raise NotImplementedError
    end

    def delete(bucket, key)
      raise NotImplementedError
    end

    def name
      self.class.name.split('::').last
    end
  end

  class S3Storage < Base
    def initialize(region:, access_key_id:)
      @region         = region
      @access_key_id  = access_key_id
    end

    def upload(bucket, key, data, content_type: 'application/octet-stream', metadata: {})
      etag = Digest::MD5.hexdigest(data.to_s)
      puts "[S3] PUT s3://#{bucket}/#{key} (#{data.to_s.bytesize} bytes, #{content_type})"
      puts "     region=#{@region} ETag=\"#{etag}\""
      StorageResult.new(
        success: true,
        url:     "https://#{bucket}.s3.#{@region}.amazonaws.com/#{key}",
        etag:    etag
      )
    end

    def download(bucket, key)
      puts "[S3] GET s3://#{bucket}/#{key}"
      StorageResult.new(success: true, url: "https://#{bucket}.s3.#{@region}.amazonaws.com/#{key}")
    end

    def delete(bucket, key)
      puts "[S3] DELETE s3://#{bucket}/#{key}"
      StorageResult.new(success: true)
    end
  end

  class GCSStorage < Base
    def initialize(project_id:, service_account:)
      @project_id      = project_id
      @service_account = service_account
    end

    def upload(bucket, key, data, content_type: 'application/octet-stream', metadata: {})
      etag = Digest::SHA256.hexdigest(data.to_s)[0..15]
      puts "[GCS] POST https://storage.googleapis.com/upload/storage/v1/b/#{bucket}/o"
      puts "      object=#{key} size=#{data.to_s.bytesize} project=#{@project_id}"
      StorageResult.new(
        success: true,
        url:     "https://storage.googleapis.com/#{bucket}/#{key}",
        etag:    etag
      )
    end

    def download(bucket, key)
      puts "[GCS] GET https://storage.googleapis.com/#{bucket}/#{key}"
      StorageResult.new(success: true, url: "https://storage.googleapis.com/#{bucket}/#{key}")
    end

    def delete(bucket, key)
      puts "[GCS] DELETE https://storage.googleapis.com/storage/v1/b/#{bucket}/o/#{key}"
      StorageResult.new(success: true)
    end
  end

  class AzureBlobStorage < Base
    def initialize(account_name:, container:)
      @account_name = account_name
      @container    = container
    end

    def upload(bucket, key, data, content_type: 'application/octet-stream', metadata: {})
      etag = "\"#{Digest::MD5.hexdigest(data.to_s)}\""
      puts "[Azure] PUT https://#{@account_name}.blob.core.windows.net/#{bucket}/#{key}"
      puts "        Content-Type: #{content_type}, x-ms-blob-type: BlockBlob"
      StorageResult.new(
        success: true,
        url:     "https://#{@account_name}.blob.core.windows.net/#{bucket}/#{key}",
        etag:    etag
      )
    end

    def download(bucket, key)
      puts "[Azure] GET https://#{@account_name}.blob.core.windows.net/#{bucket}/#{key}"
      StorageResult.new(success: true, url: "https://#{@account_name}.blob.core.windows.net/#{bucket}/#{key}")
    end

    def delete(bucket, key)
      puts "[Azure] DELETE https://#{@account_name}.blob.core.windows.net/#{bucket}/#{key}"
      StorageResult.new(success: true)
    end
  end
end

# ---------------------------------------------------------------------------
# Abstraction hierarchy — file operations
# ---------------------------------------------------------------------------

class FileOperation
  attr_reader :backend

  def initialize(backend)
    @backend = backend  # the bridge
  end

  # Switch storage provider at runtime (e.g., multi-region failover)
  def switch_backend(backend)
    puts "  [FileOperation] Switching backend: #{@backend.name} → #{backend.name}"
    @backend = backend
  end

  def execute
    raise NotImplementedError
  end
end

class FileUpload < FileOperation
  def initialize(backend, bucket:, key:, local_path:, content_type: 'application/octet-stream', tags: [])
    super(backend)
    @bucket       = bucket
    @key          = key
    @local_path   = local_path
    @content_type = content_type
    @tags         = tags
  end

  def execute
    # Simulate reading file content
    simulated_data = "BINARY_CONTENT[#{@local_path}:#{File.basename(@local_path)}]"
    metadata = { source: @local_path, tags: @tags.join(','), uploaded_at: Time.now.iso8601 }

    puts "\n[FileUpload] #{@local_path} → #{@backend.name}://#{@bucket}/#{@key}"
    result = @backend.upload(@bucket, @key, simulated_data,
                             content_type: @content_type, metadata: metadata)

    if result.success
      puts "  Upload succeeded. URL: #{result.url}"
      puts "  ETag: #{result.etag}" if result.etag
    else
      puts "  Upload FAILED: #{result.error_message}"
    end
    result
  end
end

class FileDownload < FileOperation
  def initialize(backend, bucket:, key:, dest_path:)
    super(backend)
    @bucket    = bucket
    @key       = key
    @dest_path = dest_path
  end

  def execute
    puts "\n[FileDownload] #{@backend.name}://#{@bucket}/#{@key} → #{@dest_path}"
    result = @backend.download(@bucket, @key)

    if result.success
      puts "  Download succeeded. Would write to #{@dest_path}"
      puts "  Source URL: #{result.url}"
    else
      puts "  Download FAILED: #{result.error_message}"
    end
    result
  end
end

class FileDelete < FileOperation
  def initialize(backend, bucket:, key:, soft_delete: false)
    super(backend)
    @bucket      = bucket
    @key         = key
    @soft_delete = soft_delete
  end

  def execute
    action = @soft_delete ? 'Soft-delete' : 'Hard-delete'
    puts "\n[FileDelete] #{action}: #{@backend.name}://#{@bucket}/#{@key}"

    if @soft_delete
      # Simulate moving to a trash prefix instead of deleting
      trash_key = "trash/#{Time.now.strftime('%Y%m%d')}/#{@key}"
      puts "  Moving to trash prefix: #{trash_key}"
      result = @backend.upload(@bucket, trash_key, '', metadata: { original_key: @key })
    else
      result = @backend.delete(@bucket, @key)
    end

    puts result.success ? "  Delete succeeded." : "  Delete FAILED: #{result.error_message}"
    result
  end
end

# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

s3    = StorageBackend::S3Storage.new(region: 'us-east-1', access_key_id: 'AKIAIOSFODNN7EXAMPLE')
gcs   = StorageBackend::GCSStorage.new(project_id: 'acme-prod', service_account: 'storage@acme-prod.iam')
azure = StorageBackend::AzureBlobStorage.new(account_name: 'acmestorage', container: 'assets')

puts '=' * 60
puts 'Scenario 1: Upload profile photo to S3'
puts '=' * 60
upload = FileUpload.new(s3,
  bucket:       'acme-user-uploads',
  key:          'profiles/user-555/avatar.jpg',
  local_path:   '/tmp/avatar.jpg',
  content_type: 'image/jpeg',
  tags:         %w[profile avatar user-content]
)
upload.execute

puts '=' * 60
puts 'Scenario 2: Download report from GCS'
puts '=' * 60
download = FileDownload.new(gcs,
  bucket:    'acme-reports',
  key:       'sales/2026-06/summary.xlsx',
  dest_path: '/tmp/sales-summary.xlsx'
)
download.execute

puts '=' * 60
puts 'Scenario 3: Soft-delete temp file on Azure'
puts '=' * 60
delete_op = FileDelete.new(azure,
  bucket:      'acme-tmp',
  key:         'exports/job-12345/output.csv',
  soft_delete: true
)
delete_op.execute

puts '=' * 60
puts 'Scenario 4: Multi-region failover — switch S3 region at runtime'
puts '=' * 60
us_west_s3 = StorageBackend::S3Storage.new(region: 'us-west-2', access_key_id: 'AKIAIOSFODNN7BACKUP')
upload.switch_backend(us_west_s3)
upload.execute
```

---

## When To Use

- **Class-explosion risk**: You have (or anticipate) multiple independent dimensions of variation, e.g., N types × M platforms. Without Bridge you would need N × M classes; with Bridge you need N + M.
- **Runtime implementation switching**: You want to change the implementation used by an object while the program is running (e.g., swap a database driver, rendering engine, or payment gateway without restarting or rebuilding).
- **Platform independence**: You want your high-level abstraction code to be unaware of platform-specific details (OS, hardware, third-party service), keeping it portable and testable with mock implementations.
- **Independent team development**: Two teams must develop two parts of the system in parallel. The Bridge interface acts as the contract that allows each team to progress independently.
- **Legacy code isolation**: You need to wrap a legacy system behind an `Implementation` interface so that new abstractions can use it without being coupled to its internals.

**Do NOT use Bridge** when:

- The class has only one dimension of variation — simple inheritance is sufficient.
- The abstractions and implementations are tightly coupled by nature and will never need to vary independently.
- The added indirection would make a simple, highly cohesive class harder to understand without providing real extensibility benefits.

---

## Pros & Cons

| Pros | Cons |
|---|---|
| **Platform independence** — abstraction code has no knowledge of platform details, making it easier to port. | **Added complexity** — introduces two parallel hierarchies and a layer of delegation that may be overkill for simple problems. |
| **Open/Closed Principle** — you can extend either hierarchy independently without modifying the other. | **Upfront design cost** — identifying the right split between abstraction and implementation requires domain knowledge and forward planning. |
| **Single Responsibility Principle** — high-level logic lives in the abstraction; low-level details live in the implementation. | **Indirection** — method calls go through an extra level of delegation, which can make call stacks and debugging slightly more involved. |
| **Runtime flexibility** — implementations can be swapped at runtime (e.g., fallback to a secondary service on failure). | **Interface design is critical** — a poorly designed `Implementation` interface that is too narrow or too broad forces workarounds in both hierarchies. |
| **Improved testability** — implementations can be replaced with test doubles, enabling unit testing of the abstraction in isolation. | |
| **Hides implementation details** — clients interact with the Abstraction interface only and are insulated from low-level changes. | |

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Abstract Factory** | Abstract Factory can create and configure a Bridge. The factory produces matching Abstraction/Implementation pairs, ensuring the correct concrete implementation is injected. |
| **Adapter** | Adapter makes incompatible interfaces work together *after the fact* (wrapping an existing class). Bridge is designed *upfront* to let abstractions and implementations vary independently. Adapter is a retrofit; Bridge is an intentional architecture. |
| **Composite** | Bridge can be combined with Composite: the Abstraction can be a Composite tree, and each node delegates leaf-level operations to the shared Implementation. |
| **Strategy** | Both patterns use composition to delegate behavior. The difference is intent: Strategy replaces an *algorithm* within a single object; Bridge separates an entire *implementation hierarchy* from an abstraction hierarchy. You could think of Strategy as a single-level Bridge focused on behavioral substitution. |

---

## Sources

- https://refactoring.guru/design-patterns/bridge
- https://sourcemaking.com/design_patterns/bridge
