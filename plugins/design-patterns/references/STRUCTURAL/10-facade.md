# Facade Pattern

**Category:** Structural  
**Also Known As:** —

---

## Intent

Provide a simplified, unified interface to a complex subsystem or set of classes, shielding clients from internal complexity without removing access to the underlying system when needed.

---

## Problem It Solves

As software grows, subsystems accumulate layers of classes, dependencies, and configuration. A client that needs to accomplish a high-level task — say, convert a video file — must orchestrate a codec library, a frame extractor, an audio encoder, a bitrate negotiator, and a container writer. This leads to:

- Business logic becoming tightly coupled to low-level implementation details.
- Dozens of initialization steps scattered across calling code.
- Every change in the subsystem rippling out to every caller.
- New team members struggling to understand what sequence of calls is required.

The subsystem itself is not wrong. It exposes fine-grained control that advanced users legitimately need. The problem is forcing every user — especially those who only need the common case — to understand all of it.

---

## Solution

Introduce a **Facade** class that:

1. Wraps the subsystem and exposes only the methods clients actually need.
2. Handles all the orchestration, initialization order, and wiring internally.
3. Delegates real work to the subsystem classes — it does not reimplement them.
4. Can coexist with direct subsystem access for power users who need it.

A facade simplifies without hiding. Clients who need advanced behaviour can still bypass it and talk to subsystem classes directly.

---

## Structure (ASCII diagram)

```
  ┌─────────────────────────────────────────────────────┐
  │                    Client Code                       │
  └────────────────────────┬────────────────────────────┘
                           │  calls simple API
                           ▼
  ┌─────────────────────────────────────────────────────┐
  │                      Facade                          │
  │  + operation()                                       │
  │    - coordinates subsystem classes                   │
  └───────┬──────────────┬──────────────┬───────────────┘
          │              │              │
          ▼              ▼              ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │ SubsystemA   │ │ SubsystemB   │ │ SubsystemC   │
  │ (complex)    │ │ (complex)    │ │ (complex)    │
  └──────────────┘ └──────────────┘ └──────────────┘

  Optional:
  ┌─────────────────────────────────────────────────────┐
  │               AdditionalFacade                       │
  │  Splits responsibilities; prevents the main Facade   │
  │  from becoming a God Object.                         │
  └─────────────────────────────────────────────────────┘
```

---

## Participants

| Participant | Role |
|---|---|
| **Facade** | Knows which subsystem classes are responsible for a request. Delegates client requests to the right subsystem objects. |
| **AdditionalFacade** | Optional. Extracts a subset of related functionality into a second facade to avoid a bloated primary facade. |
| **Subsystem Classes** | Implement subsystem functionality. Handle work assigned by the Facade. Have no knowledge of the Facade — they can also be used directly. |
| **Client** | Uses the Facade instead of calling subsystem objects directly. |

---

## How It Works (step-by-step)

1. **Client calls** a high-level method on the Facade (e.g., `HomeTheater.watchMovie("Inception")`).
2. **Facade translates** that single call into the correct sequence of subsystem calls.
3. **Subsystem A** is initialised/configured as a prerequisite (e.g., amplifier power on, input set).
4. **Subsystem B** is configured next in the required order (e.g., projector on, screen lowered).
5. **Subsystem C** begins the actual operation (e.g., media player starts playback).
6. **Client receives** either a result or simply observes the end state — it never saw the complexity.
7. **Teardown** (if needed) is similarly delegated: `endMovie()` reverses the sequence correctly.
8. Power users can still import and use subsystem classes directly when they need granular control.

---

## Code Examples

### Python

```python
"""
Facade Pattern — Home Theater System
Real-world scenario: controlling a complex home theater setup (amplifier,
projector, streaming player, screen, lights) through a single, simple API.
"""

from __future__ import annotations


# ──────────────────────────── Subsystem classes ─────────────────────────────

class Amplifier:
    def __init__(self, name: str) -> None:
        self.name = name
        self._volume: int = 0

    def on(self) -> None:
        print(f"[Amplifier] {self.name} powering on.")

    def off(self) -> None:
        print(f"[Amplifier] {self.name} powering off.")

    def set_surround_sound(self) -> None:
        print(f"[Amplifier] {self.name} surround sound enabled (5.1).")

    def set_volume(self, level: int) -> None:
        self._volume = level
        print(f"[Amplifier] {self.name} volume set to {level}.")


class StreamingPlayer:
    def __init__(self, name: str) -> None:
        self.name = name
        self._movie: str | None = None

    def on(self) -> None:
        print(f"[Player] {self.name} powering on.")

    def off(self) -> None:
        print(f"[Player] {self.name} powering off.")

    def play(self, movie: str) -> None:
        self._movie = movie
        print(f"[Player] {self.name} playing '{movie}'.")

    def stop(self) -> None:
        print(f"[Player] {self.name} stopped '{self._movie}'.")
        self._movie = None

    def set_two_channel_audio(self) -> None:
        print(f"[Player] {self.name} set to 2-channel audio.")

    def set_surround_audio(self) -> None:
        print(f"[Player] {self.name} set to surround audio.")


class Projector:
    def __init__(self, name: str) -> None:
        self.name = name

    def on(self) -> None:
        print(f"[Projector] {self.name} powering on.")

    def off(self) -> None:
        print(f"[Projector] {self.name} powering off.")

    def wide_screen_mode(self) -> None:
        print(f"[Projector] {self.name} set to widescreen mode (16:9).")


class Screen:
    def __init__(self, name: str) -> None:
        self.name = name

    def down(self) -> None:
        print(f"[Screen] {self.name} lowering.")

    def up(self) -> None:
        print(f"[Screen] {self.name} retracting.")


class TheaterLights:
    def __init__(self, name: str) -> None:
        self.name = name

    def on(self) -> None:
        print(f"[Lights] {self.name} on.")

    def dim(self, level: int) -> None:
        print(f"[Lights] {self.name} dimmed to {level}%.")


class PopcornPopper:
    def __init__(self, name: str) -> None:
        self.name = name

    def on(self) -> None:
        print(f"[Popper] {self.name} on.")

    def off(self) -> None:
        print(f"[Popper] {self.name} off.")

    def pop(self) -> None:
        print(f"[Popper] {self.name} popping popcorn!")


# ─────────────────────────────────── Facade ──────────────────────────────────

class HomeTheaterFacade:
    """Simplified interface to the entire home theater subsystem."""

    def __init__(
        self,
        amp: Amplifier,
        player: StreamingPlayer,
        projector: Projector,
        screen: Screen,
        lights: TheaterLights,
        popper: PopcornPopper,
    ) -> None:
        self._amp = amp
        self._player = player
        self._projector = projector
        self._screen = screen
        self._lights = lights
        self._popper = popper

    def watch_movie(self, movie: str) -> None:
        print("\n=== Get ready to watch a movie! ===")
        self._popper.on()
        self._popper.pop()
        self._lights.dim(10)
        self._screen.down()
        self._projector.on()
        self._projector.wide_screen_mode()
        self._amp.on()
        self._amp.set_surround_sound()
        self._amp.set_volume(5)
        self._player.on()
        self._player.set_surround_audio()
        self._player.play(movie)
        print("=== Enjoy the movie! ===\n")

    def end_movie(self) -> None:
        print("\n=== Shutting movie theater down... ===")
        self._popper.off()
        self._lights.on()
        self._screen.up()
        self._projector.off()
        self._amp.off()
        self._player.stop()
        self._player.off()
        print("=== Good night! ===\n")

    def listen_to_radio(self, frequency: str) -> None:
        print(f"\n=== Tuning in to {frequency} ===")
        self._amp.on()
        self._amp.set_volume(3)
        self._player.off()
        print(f"=== Radio {frequency} playing ===\n")


# ─────────────────────────────────── Client ──────────────────────────────────

def main() -> None:
    # Wire up subsystem components
    amp = Amplifier("Denon AVR-X3700H")
    player = StreamingPlayer("Apple TV 4K")
    projector = Projector("Epson 5050UB")
    screen = Screen("Elite Screens 120\"")
    lights = TheaterLights("Philips Hue")
    popper = PopcornPopper("Whirley-Pop")

    # Build the facade — clients only need this one object
    theater = HomeTheaterFacade(amp, player, projector, screen, lights, popper)

    theater.watch_movie("Inception (2010)")
    theater.end_movie()


if __name__ == "__main__":
    main()
```

---

### Java

```java
/**
 * Facade Pattern — E-Commerce Order Processing
 *
 * Scenario: placing an order requires coordinating inventory checking,
 * payment processing, shipping calculation, and email notification.
 * The OrderFacade hides all of this behind a single placeOrder() call.
 */

// ──────────────────────────── Subsystem classes ──────────────────────────────

class InventoryService {
    public boolean checkStock(String productId, int quantity) {
        System.out.printf("[Inventory] Checking stock for product %s (qty: %d)%n",
                productId, quantity);
        // Simulate: product is in stock
        return true;
    }

    public void reserveStock(String productId, int quantity) {
        System.out.printf("[Inventory] Reserved %d units of product %s%n",
                quantity, productId);
    }

    public void releaseReservation(String productId, int quantity) {
        System.out.printf("[Inventory] Released reservation for %d units of %s%n",
                quantity, productId);
    }
}

class PaymentGateway {
    public boolean charge(String customerId, double amount, String currency) {
        System.out.printf("[Payment] Charging customer %s: %.2f %s%n",
                customerId, amount, currency);
        // Simulate successful payment
        return true;
    }

    public void refund(String customerId, double amount, String currency) {
        System.out.printf("[Payment] Refunding customer %s: %.2f %s%n",
                customerId, amount, currency);
    }
}

class ShippingService {
    public double calculateShipping(String warehouseId, String destinationZip) {
        System.out.printf("[Shipping] Calculating rate from warehouse %s to %s%n",
                warehouseId, destinationZip);
        return 9.99;
    }

    public String createShipment(String orderId, String destinationZip) {
        String trackingNumber = "TRK-" + orderId.toUpperCase();
        System.out.printf("[Shipping] Shipment created. Tracking: %s%n", trackingNumber);
        return trackingNumber;
    }
}

class NotificationService {
    public void sendOrderConfirmation(String email, String orderId, String trackingNumber) {
        System.out.printf("[Email] Sending order confirmation to %s (order: %s, tracking: %s)%n",
                email, orderId, trackingNumber);
    }

    public void sendOrderFailure(String email, String reason) {
        System.out.printf("[Email] Sending failure notification to %s. Reason: %s%n",
                email, reason);
    }
}

// ─────────────────────────────────── Facade ──────────────────────────────────

class OrderRequest {
    public final String orderId;
    public final String customerId;
    public final String customerEmail;
    public final String productId;
    public final int quantity;
    public final double unitPrice;
    public final String destinationZip;

    public OrderRequest(String orderId, String customerId, String customerEmail,
                        String productId, int quantity, double unitPrice,
                        String destinationZip) {
        this.orderId = orderId;
        this.customerId = customerId;
        this.customerEmail = customerEmail;
        this.productId = productId;
        this.quantity = quantity;
        this.unitPrice = unitPrice;
        this.destinationZip = destinationZip;
    }
}

class OrderFacade {
    private final InventoryService inventory;
    private final PaymentGateway payment;
    private final ShippingService shipping;
    private final NotificationService notification;
    private static final String WAREHOUSE_ID = "WH-EAST-01";

    public OrderFacade(InventoryService inventory, PaymentGateway payment,
                       ShippingService shipping, NotificationService notification) {
        this.inventory = inventory;
        this.payment = payment;
        this.shipping = shipping;
        this.notification = notification;
    }

    /**
     * Places an order end-to-end. Clients call only this method.
     * Returns true on success, false if any step fails (with rollback).
     */
    public boolean placeOrder(OrderRequest req) {
        System.out.printf("%n=== Processing order %s ===%n", req.orderId);

        // Step 1: Check and reserve inventory
        if (!inventory.checkStock(req.productId, req.quantity)) {
            notification.sendOrderFailure(req.customerEmail, "Out of stock");
            return false;
        }
        inventory.reserveStock(req.productId, req.quantity);

        // Step 2: Calculate total including shipping
        double shippingCost = shipping.calculateShipping(WAREHOUSE_ID, req.destinationZip);
        double total = (req.unitPrice * req.quantity) + shippingCost;

        // Step 3: Charge customer
        if (!payment.charge(req.customerId, total, "USD")) {
            inventory.releaseReservation(req.productId, req.quantity);
            notification.sendOrderFailure(req.customerEmail, "Payment declined");
            return false;
        }

        // Step 4: Create shipment
        String tracking = shipping.createShipment(req.orderId, req.destinationZip);

        // Step 5: Notify customer
        notification.sendOrderConfirmation(req.customerEmail, req.orderId, tracking);

        System.out.printf("=== Order %s completed successfully! Total: $%.2f ===%n%n",
                req.orderId, total);
        return true;
    }
}

// ─────────────────────────────────── Client ──────────────────────────────────

public class FacadeDemo {
    public static void main(String[] args) {
        // Subsystems are wired together once (e.g., via DI framework)
        OrderFacade orderFacade = new OrderFacade(
                new InventoryService(),
                new PaymentGateway(),
                new ShippingService(),
                new NotificationService()
        );

        // Client only sees a clean, simple API
        OrderRequest order = new OrderRequest(
                "ORD-20260609-001",
                "CUST-42",
                "alice@example.com",
                "PROD-SKU-9988",
                2,
                49.99,
                "10001"
        );

        boolean success = orderFacade.placeOrder(order);
        System.out.println("Order placed: " + success);
    }
}
```

---

### C++

```cpp
/**
 * Facade Pattern — Video File Converter
 *
 * Scenario: converting a video file requires coordinating a codec reader,
 * audio mixer, bitrate controller, and file writer. The VideoConverter
 * facade exposes a single convert() function.
 */

#include <iostream>
#include <string>
#include <memory>
#include <stdexcept>

// ──────────────────────────── Subsystem classes ──────────────────────────────

class CodecFactory {
public:
    std::string extract(const std::string& filename) {
        // Determine codec from file extension
        std::string ext = filename.substr(filename.rfind('.') + 1);
        std::cout << "[CodecFactory] Detected codec: " << ext << " for file: " << filename << "\n";
        return ext;
    }
};

class BitrateReader {
public:
    std::string read(const std::string& filename, const std::string& codec) {
        std::cout << "[BitrateReader] Reading bitrate of '" << filename
                  << "' using codec: " << codec << "\n";
        return "buffer<" + filename + ">";
    }

    std::string convert(const std::string& buffer, const std::string& destinationCodec) {
        std::cout << "[BitrateReader] Converting buffer to " << destinationCodec << " format\n";
        return "converted-buffer<" + destinationCodec + ">";
    }
};

class AudioMixer {
public:
    std::string fix(const std::string& buffer) {
        std::cout << "[AudioMixer] Normalising audio levels\n";
        return "audio-fixed<" + buffer + ">";
    }
};

class VideoFile {
public:
    explicit VideoFile(const std::string& filename) : filename_(filename) {
        std::cout << "[VideoFile] Created output file: " << filename_ << "\n";
    }

    void save(const std::string& buffer) {
        std::cout << "[VideoFile] Saved " << buffer << " -> " << filename_ << "\n";
    }

private:
    std::string filename_;
};

// ─────────────────────────────────── Facade ──────────────────────────────────

class VideoConverterFacade {
public:
    VideoConverterFacade()
        : codecFactory_(std::make_unique<CodecFactory>()),
          bitrateReader_(std::make_unique<BitrateReader>()),
          audioMixer_(std::make_unique<AudioMixer>()) {}

    /**
     * Converts a video file to the target format.
     * @param filename   Source file path
     * @param format     Target format extension (e.g. "mp4", "ogg")
     * @return           Path of the converted file
     */
    std::string convert(const std::string& filename, const std::string& format) {
        std::cout << "\n=== VideoConverter: " << filename << " -> " << format << " ===\n";

        std::string sourceCodec = codecFactory_->extract(filename);
        std::string buffer = bitrateReader_->read(filename, sourceCodec);
        std::string convertedBuffer = bitrateReader_->convert(buffer, format);
        std::string fixedBuffer = audioMixer_->fix(convertedBuffer);

        // Build output filename
        std::string base = filename.substr(0, filename.rfind('.'));
        std::string outputName = base + "_converted." + format;

        VideoFile output(outputName);
        output.save(fixedBuffer);

        std::cout << "=== Conversion complete: " << outputName << " ===\n\n";
        return outputName;
    }

private:
    std::unique_ptr<CodecFactory>  codecFactory_;
    std::unique_ptr<BitrateReader> bitrateReader_;
    std::unique_ptr<AudioMixer>    audioMixer_;
};

// ─────────────────────────────────── Client ──────────────────────────────────

int main() {
    VideoConverterFacade converter;

    std::string result1 = converter.convert("documentary.avi", "mp4");
    std::cout << "Output: " << result1 << "\n";

    std::string result2 = converter.convert("podcast.mov", "ogg");
    std::cout << "Output: " << result2 << "\n";

    return 0;
}
```

---

### C#

```csharp
/**
 * Facade Pattern — Smart Home Automation
 *
 * Scenario: a "leaving home" routine must lock doors, turn off lights,
 * lower the thermostat, arm the alarm, and pause all media players.
 * SmartHomeFacade encapsulates the entire sequence.
 */

using System;
using System.Collections.Generic;

// ──────────────────────────── Subsystem classes ──────────────────────────────

class LockSystem
{
    public void LockAllDoors()
        => Console.WriteLine("[LockSystem] All exterior doors locked.");

    public void UnlockFrontDoor()
        => Console.WriteLine("[LockSystem] Front door unlocked.");
}

class LightingSystem
{
    private readonly List<string> _zones = new() { "Living Room", "Kitchen", "Bedroom", "Garage" };

    public void TurnOffAll()
    {
        foreach (var zone in _zones)
            Console.WriteLine($"[Lighting] {zone} lights OFF.");
    }

    public void SetScene(string scene)
        => Console.WriteLine($"[Lighting] Scene '{scene}' activated.");
}

class Thermostat
{
    private int _temperature = 22;

    public void SetTemperature(int degrees)
    {
        _temperature = degrees;
        Console.WriteLine($"[Thermostat] Temperature set to {_temperature}°C.");
    }

    public void SetAwayMode()
    {
        _temperature = 18;
        Console.WriteLine("[Thermostat] Away mode activated (18°C).");
    }
}

class SecurityAlarm
{
    public void Arm(string mode)
        => Console.WriteLine($"[Alarm] Armed in '{mode}' mode. Exit delay: 30s.");

    public void Disarm(string pin)
        => Console.WriteLine($"[Alarm] Disarmed with PIN.");

    public void TriggerSiren()
        => Console.WriteLine("[Alarm] SIREN TRIGGERED!");
}

class MediaController
{
    public void PauseAll()
        => Console.WriteLine("[Media] All media players paused.");

    public void ResumeAll()
        => Console.WriteLine("[Media] All media players resumed.");
}

// ─────────────────────────────────── Facade ──────────────────────────────────

class SmartHomeFacade
{
    private readonly LockSystem     _locks;
    private readonly LightingSystem _lights;
    private readonly Thermostat     _thermostat;
    private readonly SecurityAlarm  _alarm;
    private readonly MediaController _media;

    public SmartHomeFacade(
        LockSystem locks,
        LightingSystem lights,
        Thermostat thermostat,
        SecurityAlarm alarm,
        MediaController media)
    {
        _locks      = locks;
        _lights     = lights;
        _thermostat = thermostat;
        _alarm      = alarm;
        _media      = media;
    }

    /// <summary>Activates the full "leaving home" routine.</summary>
    public void LeaveHome()
    {
        Console.WriteLine("\n=== Activating 'Leave Home' routine ===");
        _media.PauseAll();
        _lights.TurnOffAll();
        _thermostat.SetAwayMode();
        _locks.LockAllDoors();
        _alarm.Arm("away");
        Console.WriteLine("=== Home secured. Have a great day! ===\n");
    }

    /// <summary>Activates the "arrive home" routine.</summary>
    public void ArriveHome(string alarmPin)
    {
        Console.WriteLine("\n=== Activating 'Arrive Home' routine ===");
        _alarm.Disarm(alarmPin);
        _locks.UnlockFrontDoor();
        _thermostat.SetTemperature(22);
        _lights.SetScene("Welcome");
        _media.ResumeAll();
        Console.WriteLine("=== Welcome home! ===\n");
    }

    /// <summary>Activates a movie-night scene.</summary>
    public void MovieNight()
    {
        Console.WriteLine("\n=== Activating 'Movie Night' routine ===");
        _lights.SetScene("Cinema");
        _thermostat.SetTemperature(21);
        // Alarm stays armed in "home" mode
        _alarm.Arm("home");
        Console.WriteLine("=== Enjoy the movie! ===\n");
    }
}

// ─────────────────────────────────── Client ──────────────────────────────────

class Program
{
    static void Main()
    {
        var home = new SmartHomeFacade(
            new LockSystem(),
            new LightingSystem(),
            new Thermostat(),
            new SecurityAlarm(),
            new MediaController()
        );

        home.LeaveHome();
        home.ArriveHome("1234");
        home.MovieNight();
    }
}
```

---

### TypeScript

```typescript
/**
 * Facade Pattern — Authentication & Session Management
 *
 * Scenario: logging a user in involves validating credentials, checking
 * MFA, generating a JWT, writing an audit log, and setting a session cookie.
 * AuthFacade exposes a simple login() / logout() API.
 */

// ──────────────────────────── Subsystem classes ──────────────────────────────

interface User {
  id: string;
  email: string;
  passwordHash: string;
  mfaEnabled: boolean;
  mfaSecret: string;
}

class UserRepository {
  private users: Map<string, User> = new Map([
    [
      "alice@example.com",
      {
        id: "usr_001",
        email: "alice@example.com",
        passwordHash: "hashed_password_123",
        mfaEnabled: true,
        mfaSecret: "JBSWY3DPEHPK3PXP",
      },
    ],
  ]);

  findByEmail(email: string): User | null {
    return this.users.get(email) ?? null;
  }
}

class PasswordValidator {
  verify(plaintext: string, hash: string): boolean {
    // Simulate bcrypt comparison
    const result = `hashed_${plaintext}` === hash;
    console.log(`[PasswordValidator] Password check: ${result ? "OK" : "FAIL"}`);
    return result;
  }
}

class MfaService {
  verify(secret: string, token: string): boolean {
    // Simulate TOTP verification (token "123456" always valid in demo)
    const valid = token === "123456";
    console.log(`[MfaService] TOTP token check: ${valid ? "OK" : "FAIL"}`);
    return valid;
  }
}

class JwtService {
  private secret = "super-secret-key";

  sign(userId: string, email: string): string {
    const payload = Buffer.from(JSON.stringify({ userId, email, iat: Date.now() })).toString("base64");
    const token = `eyJhbGciOiJIUzI1NiJ9.${payload}.signature`;
    console.log(`[JwtService] Token issued for user ${userId}`);
    return token;
  }

  verify(token: string): { userId: string; email: string } | null {
    try {
      const parts = token.split(".");
      const payload = JSON.parse(Buffer.from(parts[1], "base64").toString());
      return { userId: payload.userId, email: payload.email };
    } catch {
      return null;
    }
  }
}

class AuditLogger {
  log(event: string, userId: string, metadata: Record<string, unknown> = {}): void {
    console.log(`[AuditLog] ${new Date().toISOString()} | ${event} | user=${userId}`, metadata);
  }
}

class SessionStore {
  private sessions = new Map<string, string>(); // sessionId -> userId

  create(sessionId: string, userId: string): void {
    this.sessions.set(sessionId, userId);
    console.log(`[SessionStore] Session ${sessionId} created for user ${userId}`);
  }

  destroy(sessionId: string): boolean {
    const existed = this.sessions.has(sessionId);
    this.sessions.delete(sessionId);
    console.log(`[SessionStore] Session ${sessionId} destroyed`);
    return existed;
  }
}

// ─────────────────────────────────── Facade ──────────────────────────────────

interface LoginResult {
  success: boolean;
  token?: string;
  sessionId?: string;
  error?: string;
}

class AuthFacade {
  constructor(
    private readonly userRepo: UserRepository,
    private readonly passwordValidator: PasswordValidator,
    private readonly mfaService: MfaService,
    private readonly jwtService: JwtService,
    private readonly auditLogger: AuditLogger,
    private readonly sessionStore: SessionStore
  ) {}

  /**
   * Authenticates a user with email, password, and optional MFA token.
   * Handles all subsystem coordination internally.
   */
  login(email: string, password: string, mfaToken?: string): LoginResult {
    console.log(`\n=== Login attempt for ${email} ===`);

    // 1. Look up user
    const user = this.userRepo.findByEmail(email);
    if (!user) {
      this.auditLogger.log("LOGIN_FAILED", "unknown", { reason: "user not found", email });
      return { success: false, error: "Invalid credentials" };
    }

    // 2. Validate password
    if (!this.passwordValidator.verify(password, user.passwordHash)) {
      this.auditLogger.log("LOGIN_FAILED", user.id, { reason: "bad password" });
      return { success: false, error: "Invalid credentials" };
    }

    // 3. Check MFA if enabled
    if (user.mfaEnabled) {
      if (!mfaToken) {
        return { success: false, error: "MFA token required" };
      }
      if (!this.mfaService.verify(user.mfaSecret, mfaToken)) {
        this.auditLogger.log("LOGIN_FAILED", user.id, { reason: "bad MFA token" });
        return { success: false, error: "Invalid MFA token" };
      }
    }

    // 4. Issue JWT
    const token = this.jwtService.sign(user.id, user.email);

    // 5. Create session
    const sessionId = `sess_${Math.random().toString(36).slice(2)}`;
    this.sessionStore.create(sessionId, user.id);

    // 6. Audit success
    this.auditLogger.log("LOGIN_SUCCESS", user.id, { sessionId });

    console.log(`=== Login successful for ${email} ===\n`);
    return { success: true, token, sessionId };
  }

  /** Logs out by destroying the session and logging the event. */
  logout(sessionId: string, userId: string): void {
    console.log(`\n=== Logout for session ${sessionId} ===`);
    this.sessionStore.destroy(sessionId);
    this.auditLogger.log("LOGOUT", userId, { sessionId });
    console.log("=== Logged out ===\n");
  }
}

// ─────────────────────────────────── Client ──────────────────────────────────

const auth = new AuthFacade(
  new UserRepository(),
  new PasswordValidator(),
  new MfaService(),
  new JwtService(),
  new AuditLogger(),
  new SessionStore()
);

// Successful login
const result = auth.login("alice@example.com", "password_123", "123456");
console.log("Login result:", result);

if (result.success && result.sessionId) {
  auth.logout(result.sessionId, "usr_001");
}

// Failed login (wrong password)
const badResult = auth.login("alice@example.com", "wrong_password");
console.log("Bad login result:", badResult);
```

---

### Go

```go
// Facade Pattern — Notification Service
//
// Scenario: sending a user notification may involve email, SMS, and push
// notifications depending on the user's preferences. NotificationFacade
// coordinates all channels behind a single Send() call.

package main

import (
	"fmt"
	"strings"
	"time"
)

// ──────────────────────────── Subsystem types ─────────────────────────────

// UserPreferences simulates a user's notification preferences.
type UserPreferences struct {
	UserID      string
	Email       string
	Phone       string
	DeviceToken string
	Channels    []string // "email", "sms", "push"
}

// EmailClient sends emails via SMTP.
type EmailClient struct {
	SMTPHost string
	Port     int
}

func NewEmailClient() *EmailClient {
	return &EmailClient{SMTPHost: "smtp.example.com", Port: 587}
}

func (e *EmailClient) Send(to, subject, body string) error {
	fmt.Printf("[EmailClient] SMTP(%s:%d) -> To: %s | Subject: %s | Body: %s\n",
		e.SMTPHost, e.Port, to, subject, body)
	return nil
}

// SMSGateway sends SMS messages via an external API.
type SMSGateway struct {
	APIKey  string
	BaseURL string
}

func NewSMSGateway() *SMSGateway {
	return &SMSGateway{APIKey: "twilio-api-key-xxx", BaseURL: "https://api.twilio.com"}
}

func (s *SMSGateway) Send(phoneNumber, message string) error {
	fmt.Printf("[SMSGateway] POST %s/messages | To: %s | Msg: %s\n",
		s.BaseURL, phoneNumber, message)
	return nil
}

// PushNotificationService sends push notifications via APNs/FCM.
type PushNotificationService struct {
	FCMServerKey string
}

func NewPushService() *PushNotificationService {
	return &PushNotificationService{FCMServerKey: "fcm-server-key-yyy"}
}

func (p *PushNotificationService) Send(deviceToken, title, body string) error {
	fmt.Printf("[PushService] FCM -> Token: %s | Title: %s | Body: %s\n",
		deviceToken, title, body)
	return nil
}

// TemplateRenderer renders notification templates with variables.
type TemplateRenderer struct{}

func (t *TemplateRenderer) Render(template string, vars map[string]string) string {
	result := template
	for k, v := range vars {
		result = strings.ReplaceAll(result, "{{"+k+"}}", v)
	}
	return result
}

// PreferenceStore retrieves user notification preferences.
type PreferenceStore struct {
	data map[string]UserPreferences
}

func NewPreferenceStore() *PreferenceStore {
	return &PreferenceStore{
		data: map[string]UserPreferences{
			"usr_001": {
				UserID:      "usr_001",
				Email:       "alice@example.com",
				Phone:       "+15550001234",
				DeviceToken: "device-token-abc123",
				Channels:    []string{"email", "push"},
			},
			"usr_002": {
				UserID:      "usr_002",
				Email:       "bob@example.com",
				Phone:       "+15550005678",
				DeviceToken: "",
				Channels:    []string{"email", "sms"},
			},
		},
	}
}

func (p *PreferenceStore) GetPreferences(userID string) (UserPreferences, bool) {
	prefs, ok := p.data[userID]
	return prefs, ok
}

// ─────────────────────────────────── Facade ──────────────────────────────────

// Notification represents a message to be delivered.
type Notification struct {
	Title   string
	Body    string
	Vars    map[string]string
	SentAt  time.Time
}

// NotificationFacade coordinates all notification channels.
type NotificationFacade struct {
	prefs    *PreferenceStore
	email    *EmailClient
	sms      *SMSGateway
	push     *PushNotificationService
	renderer *TemplateRenderer
}

// NewNotificationFacade constructs the facade with all dependencies.
func NewNotificationFacade() *NotificationFacade {
	return &NotificationFacade{
		prefs:    NewPreferenceStore(),
		email:    NewEmailClient(),
		sms:      NewSMSGateway(),
		push:     NewPushService(),
		renderer: &TemplateRenderer{},
	}
}

// Send delivers a notification to the user via all configured channels.
func (n *NotificationFacade) Send(userID string, notif Notification) []error {
	fmt.Printf("\n=== Sending notification to user %s ===\n", userID)

	prefs, ok := n.prefs.GetPreferences(userID)
	if !ok {
		return []error{fmt.Errorf("user %s not found", userID)}
	}

	body := n.renderer.Render(notif.Body, notif.Vars)
	title := n.renderer.Render(notif.Title, notif.Vars)

	var errs []error

	for _, channel := range prefs.Channels {
		switch channel {
		case "email":
			if err := n.email.Send(prefs.Email, title, body); err != nil {
				errs = append(errs, fmt.Errorf("email: %w", err))
			}
		case "sms":
			if err := n.sms.Send(prefs.Phone, title+": "+body); err != nil {
				errs = append(errs, fmt.Errorf("sms: %w", err))
			}
		case "push":
			if prefs.DeviceToken != "" {
				if err := n.push.Send(prefs.DeviceToken, title, body); err != nil {
					errs = append(errs, fmt.Errorf("push: %w", err))
				}
			}
		}
	}

	if len(errs) == 0 {
		fmt.Printf("=== Notification delivered successfully via %v ===\n\n", prefs.Channels)
	}
	return errs
}

// ─────────────────────────────────── Client ──────────────────────────────────

func main() {
	facade := NewNotificationFacade()

	orderNotif := Notification{
		Title: "Order Confirmed: {{orderID}}",
		Body:  "Hello {{name}}, your order {{orderID}} will arrive by {{deliveryDate}}.",
		Vars: map[string]string{
			"name":         "Alice",
			"orderID":      "ORD-20260609-001",
			"deliveryDate": "June 12, 2026",
		},
		SentAt: time.Now(),
	}

	// Client sends notification with one call — no channel wiring needed
	errs := facade.Send("usr_001", orderNotif)
	if len(errs) > 0 {
		fmt.Println("Errors:", errs)
	}

	errs = facade.Send("usr_002", Notification{
		Title: "Password Changed",
		Body:  "Your {{name}} account password was changed. If this wasn't you, contact support.",
		Vars:  map[string]string{"name": "Bob"},
		SentAt: time.Now(),
	})
	if len(errs) > 0 {
		fmt.Println("Errors:", errs)
	}
}
```

---

### PHP

```php
<?php
/**
 * Facade Pattern — Report Generation Pipeline
 *
 * Scenario: generating a business report involves fetching data from
 * a database, applying business rules, formatting the output, and
 * delivering it via email or file export. ReportFacade hides all steps.
 */

declare(strict_types=1);

// ──────────────────────────── Subsystem classes ──────────────────────────────

class DatabaseConnection
{
    private string $dsn;

    public function __construct(string $dsn)
    {
        $this->dsn = $dsn;
    }

    /** @return array<int, array<string, mixed>> */
    public function query(string $sql, array $params = []): array
    {
        echo "[DB] Executing: {$sql} with " . json_encode($params) . "\n";

        // Simulate query result
        return [
            ['region' => 'North', 'revenue' => 125000.00, 'units' => 520],
            ['region' => 'South', 'revenue' => 98500.50,  'units' => 430],
            ['region' => 'East',  'revenue' => 210300.75, 'units' => 890],
            ['region' => 'West',  'revenue' => 175200.00, 'units' => 720],
        ];
    }
}

class DataAggregator
{
    /**
     * @param array<int, array<string, mixed>> $rows
     * @return array<string, mixed>
     */
    public function aggregate(array $rows): array
    {
        $totalRevenue = array_sum(array_column($rows, 'revenue'));
        $totalUnits   = array_sum(array_column($rows, 'units'));

        echo "[Aggregator] Aggregated " . count($rows) . " rows. Total revenue: {$totalRevenue}\n";

        return [
            'rows'          => $rows,
            'total_revenue' => $totalRevenue,
            'total_units'   => $totalUnits,
            'avg_revenue'   => $totalRevenue / count($rows),
        ];
    }
}

class ReportFormatter
{
    /** @param array<string, mixed> $data */
    public function toHtml(array $data, string $title): string
    {
        echo "[Formatter] Rendering HTML report\n";

        $rows = '';
        foreach ($data['rows'] as $row) {
            $rows .= "<tr><td>{$row['region']}</td><td>\${$row['revenue']}</td><td>{$row['units']}</td></tr>";
        }

        return <<<HTML
        <html><body>
        <h1>{$title}</h1>
        <table border="1">
          <tr><th>Region</th><th>Revenue</th><th>Units</th></tr>
          {$rows}
        </table>
        <p>Total Revenue: \${$data['total_revenue']} | Total Units: {$data['total_units']}</p>
        </body></html>
        HTML;
    }

    /** @param array<string, mixed> $data */
    public function toCsv(array $data): string
    {
        echo "[Formatter] Rendering CSV report\n";

        $csv = "Region,Revenue,Units\n";
        foreach ($data['rows'] as $row) {
            $csv .= "{$row['region']},{$row['revenue']},{$row['units']}\n";
        }
        $csv .= "TOTAL,{$data['total_revenue']},{$data['total_units']}\n";
        return $csv;
    }
}

class FileExporter
{
    public function save(string $content, string $filename): string
    {
        $path = sys_get_temp_dir() . DIRECTORY_SEPARATOR . $filename;
        file_put_contents($path, $content);
        echo "[FileExporter] Report saved to: {$path}\n";
        return $path;
    }
}

class MailService
{
    public function send(string $to, string $subject, string $htmlBody, ?string $attachment = null): void
    {
        echo "[MailService] Sending email to: {$to} | Subject: {$subject}";
        if ($attachment !== null) {
            echo " | Attachment: {$attachment}";
        }
        echo "\n";
    }
}

// ─────────────────────────────────── Facade ──────────────────────────────────

class SalesReportFacade
{
    public function __construct(
        private readonly DatabaseConnection $db,
        private readonly DataAggregator     $aggregator,
        private readonly ReportFormatter    $formatter,
        private readonly FileExporter       $exporter,
        private readonly MailService        $mailer,
    ) {}

    /**
     * Generates and emails an HTML sales report for the given period.
     */
    public function emailSalesReport(
        string $recipientEmail,
        string $startDate,
        string $endDate
    ): void {
        echo "\n=== Generating Sales Report ({$startDate} to {$endDate}) ===\n";

        $sql  = 'SELECT region, SUM(revenue) AS revenue, SUM(units) AS units
                 FROM sales WHERE date BETWEEN :start AND :end GROUP BY region';
        $rows = $this->db->query($sql, [':start' => $startDate, ':end' => $endDate]);
        $data = $this->aggregator->aggregate($rows);

        $title   = "Sales Report: {$startDate} to {$endDate}";
        $html    = $this->formatter->toHtml($data, $title);
        $csvPath = $this->exporter->save(
            $this->formatter->toCsv($data),
            "sales_report_{$startDate}_{$endDate}.csv"
        );

        $this->mailer->send($recipientEmail, $title, $html, $csvPath);

        echo "=== Report delivered to {$recipientEmail} ===\n\n";
    }

    /**
     * Generates and saves a CSV sales report to disk, returning the file path.
     */
    public function exportSalesReportCsv(string $startDate, string $endDate): string
    {
        echo "\n=== Exporting CSV Sales Report ({$startDate} to {$endDate}) ===\n";

        $rows    = $this->db->query(
            'SELECT region, SUM(revenue) AS revenue, SUM(units) AS units FROM sales
             WHERE date BETWEEN :start AND :end GROUP BY region',
            [':start' => $startDate, ':end' => $endDate]
        );
        $data    = $this->aggregator->aggregate($rows);
        $csv     = $this->formatter->toCsv($data);
        $path    = $this->exporter->save($csv, "export_{$startDate}_{$endDate}.csv");

        echo "=== CSV export complete ===\n\n";
        return $path;
    }
}

// ─────────────────────────────────── Client ──────────────────────────────────

$facade = new SalesReportFacade(
    new DatabaseConnection('mysql:host=localhost;dbname=sales_db'),
    new DataAggregator(),
    new ReportFormatter(),
    new FileExporter(),
    new MailService(),
);

// One-line call replaces dozens of subsystem interactions
$facade->emailSalesReport('cfo@example.com', '2026-05-01', '2026-05-31');

$csvPath = $facade->exportSalesReportCsv('2026-06-01', '2026-06-09');
echo "Exported to: {$csvPath}\n";
```

---

### Ruby

```ruby
# Facade Pattern — Cloud Storage Service
#
# Scenario: uploading a file to cloud storage involves validating the file,
# computing a checksum, uploading chunks, registering metadata, and
# generating a CDN-signed URL. CloudStorageFacade wraps it all.

# ──────────────────────────── Subsystem classes ──────────────────────────────

require 'digest'
require 'securerandom'
require 'time'

class FileValidator
  ALLOWED_TYPES = %w[image/jpeg image/png image/gif video/mp4 application/pdf].freeze
  MAX_SIZE_BYTES = 100 * 1024 * 1024 # 100 MB

  def validate!(filename, mime_type, size_bytes)
    raise ArgumentError, "File type '#{mime_type}' not allowed" unless ALLOWED_TYPES.include?(mime_type)
    raise ArgumentError, "File size #{size_bytes} exceeds #{MAX_SIZE_BYTES} bytes" if size_bytes > MAX_SIZE_BYTES
    raise ArgumentError, "Filename cannot be blank" if filename.strip.empty?

    puts "[FileValidator] #{filename} (#{mime_type}, #{size_bytes}B) passed validation."
  end
end

class ChecksumCalculator
  def compute(content)
    checksum = Digest::SHA256.hexdigest(content)
    puts "[ChecksumCalculator] SHA-256: #{checksum[0..15]}..."
    checksum
  end
end

class ChunkUploader
  CHUNK_SIZE = 5 * 1024 * 1024 # 5 MB per chunk

  def upload(bucket, key, content)
    total_chunks = [(content.bytesize / CHUNK_SIZE.to_f).ceil, 1].max
    puts "[ChunkUploader] Uploading #{total_chunks} chunk(s) to s3://#{bucket}/#{key}"
    total_chunks.times do |i|
      puts "  [ChunkUploader] Part #{i + 1}/#{total_chunks} uploaded"
    end
    "s3://#{bucket}/#{key}"
  end
end

class MetadataRegistry
  def register(file_id, metadata)
    puts "[MetadataRegistry] Registered file #{file_id}: #{metadata.inspect}"
    { file_id: file_id, registered_at: Time.now.iso8601, **metadata }
  end

  def lookup(file_id)
    puts "[MetadataRegistry] Looking up file #{file_id}"
    { file_id: file_id, bucket: 'assets-prod', key: "uploads/#{file_id}" }
  end
end

class CdnUrlSigner
  CDN_BASE = 'https://cdn.example.com'.freeze
  EXPIRY_SECONDS = 3600

  def sign(s3_path, expires_in: EXPIRY_SECONDS)
    # Simulate HMAC-signed URL generation
    key    = s3_path.gsub('s3://', '').gsub('/', '__')
    token  = Digest::MD5.hexdigest("#{key}:#{Time.now.to_i + expires_in}")
    url    = "#{CDN_BASE}/#{key}?token=#{token}&expires=#{Time.now.to_i + expires_in}"
    puts "[CdnUrlSigner] Signed URL generated (expires in #{expires_in}s)"
    url
  end
end

# ─────────────────────────────────── Facade ──────────────────────────────────

UploadResult = Struct.new(:file_id, :s3_path, :signed_url, :checksum, :metadata, keyword_init: true)

class CloudStorageFacade
  BUCKET = 'assets-prod'.freeze

  def initialize
    @validator  = FileValidator.new
    @checksum   = ChecksumCalculator.new
    @uploader   = ChunkUploader.new
    @registry   = MetadataRegistry.new
    @signer     = CdnUrlSigner.new
  end

  # Uploads a file and returns an UploadResult with a ready-to-use CDN URL.
  #
  # @param filename  [String] Original filename
  # @param mime_type [String] MIME type of the file
  # @param content   [String] Binary content of the file
  # @param owner_id  [String] ID of the uploading user
  # @return [UploadResult]
  def upload(filename:, mime_type:, content:, owner_id:)
    puts "\n=== Uploading '#{filename}' ==="

    # 1. Validate
    @validator.validate!(filename, mime_type, content.bytesize)

    # 2. Compute checksum (deduplication / integrity)
    digest = @checksum.compute(content)

    # 3. Generate a unique storage key
    file_id = SecureRandom.uuid
    ext     = File.extname(filename)
    key     = "uploads/#{owner_id}/#{file_id}#{ext}"

    # 4. Upload in chunks
    s3_path = @uploader.upload(BUCKET, key, content)

    # 5. Register metadata
    meta = @registry.register(file_id, {
      filename:  filename,
      mime_type: mime_type,
      size:      content.bytesize,
      checksum:  digest,
      owner_id:  owner_id,
      s3_path:   s3_path
    })

    # 6. Generate signed CDN URL
    url = @signer.sign(s3_path)

    puts "=== Upload complete: #{file_id} ===\n\n"

    UploadResult.new(
      file_id:    file_id,
      s3_path:    s3_path,
      signed_url: url,
      checksum:   digest,
      metadata:   meta
    )
  end

  # Returns a fresh signed URL for an already-uploaded file.
  def get_signed_url(file_id, expires_in: 3600)
    puts "\n=== Generating signed URL for #{file_id} ==="
    record  = @registry.lookup(file_id)
    s3_path = "s3://#{record[:bucket]}/#{record[:key]}"
    url     = @signer.sign(s3_path, expires_in: expires_in)
    puts "=== URL ready ===\n\n"
    url
  end
end

# ─────────────────────────────────── Client ──────────────────────────────────

storage = CloudStorageFacade.new

# Simulate a file upload — client only calls upload()
result = storage.upload(
  filename:  'profile_photo.jpg',
  mime_type: 'image/jpeg',
  content:   'JPEG_BINARY_DATA' * 1024,   # simulated binary content
  owner_id:  'usr_007'
)

puts "File ID    : #{result.file_id}"
puts "CDN URL    : #{result.signed_url}"
puts "Checksum   : #{result.checksum[0..15]}..."

# Later: refresh the signed URL
fresh_url = storage.get_signed_url(result.file_id, expires_in: 600)
puts "Fresh URL  : #{fresh_url}"
```

---

## When To Use

- **Simplifying a complex library or framework API** — when you need common operations to be accessible without understanding the entire system (e.g., wrapping a video codec library behind a `VideoConverter.convert()` call).
- **Layered architecture** — when structuring an application into layers (presentation, business logic, data access), facades serve as entry points to each layer, reducing coupling between them.
- **Legacy code isolation** — when you want to wrap a messy or poorly designed legacy subsystem behind a clean interface so new code does not need to touch the old implementation.
- **Reducing dependencies on third-party libraries** — when you want to limit the surface area through which your application depends on an external library, making future library swaps easier.
- **Onboarding new developers** — when a subsystem is large and unfamiliar, a facade documents the "happy path" and reduces the ramp-up time for new contributors.

---

## Pros & Cons

| | Detail |
|---|---|
| **Pro** | Isolates client code from the complexity of a subsystem. |
| **Pro** | Reduces coupling between subsystem internals and client code. |
| **Pro** | Promotes layered architecture and separation of concerns. |
| **Pro** | Provides a clear, documented entry point for common operations. |
| **Pro** | Makes subsystem changes transparent to clients. |
| **Con** | A facade can become a **God Object** — a single class that is coupled to every other class in the application. |
| **Con** | May limit access to advanced subsystem features that power users genuinely need (mitigated by allowing direct subsystem access). |
| **Con** | Adds an extra layer of indirection that can make debugging harder when tracing through the call chain. |
| **Con** | Risk of facade becoming a dumping ground for unrelated convenience methods over time. |

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Abstract Factory** | Can serve as an alternative to a Facade when you only need to hide the way subsystem objects are created from client code. |
| **Mediator** | Both patterns try to organise collaboration between tightly coupled classes. A Facade defines a simplified interface to a subsystem, while a Mediator centralises communication between components of a system — the components know about the mediator, whereas subsystem components are unaware of the facade. |
| **Proxy** | Both Facade and Proxy provide an alternative interface to an existing object. A Proxy has the same interface as its target; a Facade defines a different (simpler) interface. |
| **Singleton** | Facades are often turned into Singletons because a single facade object is usually sufficient and acts as a shared access point to the subsystem. |

---

## Sources

- https://refactoring.guru/design-patterns/facade
- https://sourcemaking.com/design_patterns/facade
