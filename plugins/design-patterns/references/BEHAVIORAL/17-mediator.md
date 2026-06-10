# Mediator Pattern

**Category:** Behavioral  
**Also Known As:** Intermediary, Controller

---

## Intent

Define an object that encapsulates how a set of objects interact. The Mediator promotes loose coupling by keeping objects from referring to each other explicitly, and it lets you vary their interaction independently. It reduces chaotic dependencies between objects by restricting direct communications and forcing collaboration only through a mediator object.

---

## Problem It Solves

In complex systems, components often need to communicate with each other. Without a mediator, each component maintains direct references to every other component it interacts with. This creates a tightly-coupled web of dependencies:

- Changing one class forces you to look at every other class it communicates with.
- Reusing a component in a different program is nearly impossible because it drags along all its dependencies.
- Every time a new component is added, relationships must be added to all existing components.
- You end up creating tons of component subclasses just to reuse some basic behavior in various contexts.

A concrete example: a GUI dialog with form fields, buttons, and checkboxes. When a user checks a checkbox, it might need to enable a text field, which might need to update a button's state. If every widget holds references to every other widget, you get an unmaintainable spider web of cross-references.

```
Before Mediator (tight coupling):

ComponentA <---> ComponentB
    ^    \       /    ^
    |     \     /     |
    v      \   /      v
ComponentC <-X-> ComponentD
```

Every component knows about every other component it needs to talk to — changing one risks breaking all the others.

---

## Solution

The Mediator pattern introduces a dedicated mediator object that centralizes all communication between components. Components no longer talk to each other directly; instead they notify the mediator of events, and the mediator routes those events to the appropriate recipients.

- Each component only knows about the mediator interface.
- The mediator knows about all components and coordinates their interactions.
- Components become independent and reusable because they are decoupled from each other.

```
After Mediator (loose coupling):

ComponentA ----\          /----> ComponentB
                \        /
                v        
ComponentC --> Mediator ----> ComponentD
```

All communication flows through the mediator. Components only depend on the mediator interface, not on each other.

---

## Structure

```
+-------------------+          +-----------------------------+
|   <<interface>>   |          |      ConcreteMediator       |
|     Mediator      |<---------+-----------------------------+
+-------------------+  refs    | - componentA: ComponentA   |
| + notify(sender,  |          | - componentB: ComponentB   |
|   event): void    |          +-----------------------------+
+-------------------+          | + notify(sender,            |
         ^                     |   event): void              |
         |                     | + reactOnA(): void          |
         |                     | + reactOnB(): void          |
         |                     +-----------------------------+
         |                            |           |
         |                            |           |
         |                     refs   v           v
+-------------------+     +----------+---+ +------+----------+
|   BaseComponent   |     | ComponentA   | | ComponentB      |
+-------------------+     +--------------+ +-----------------+
| # mediator:       |     | + doA(): void| | + doB(): void   |
|   Mediator        |     +--------------+ +-----------------+
+-------------------+
| + setMediator(m)  |
+-------------------+
         ^
         |
   (extended by)
   ComponentA, ComponentB
```

**Flow of a typical interaction:**

```
ComponentA          Mediator         ComponentB
    |                   |                |
    |--doA()----------->|                |
    |                   |--reactOnA()--->|
    |                   |               |--doB()
    |                   |               |
    |<------------------|               |
```

---

## Participants

| Participant | Role |
|---|---|
| **Mediator** | Interface that declares the `notify(sender, event)` method used by components to communicate with the mediator. |
| **ConcreteMediator** | Implements cooperative behavior by coordinating several component objects. Maintains references to all components it manages and sometimes even manages their lifecycle. |
| **Component** | Various classes that contain business logic. Each component holds a reference to the mediator (declared as the mediator interface type). The component does not know the actual class of the mediator, so it can be reused in different programs by linking it to a different mediator. |

---

## How It Works

1. **Component triggers an action** — A component (e.g., a button click, a field change) performs its local work and then calls `mediator.notify(this, "eventName")` instead of calling other components directly.

2. **Mediator receives the notification** — The concrete mediator's `notify` method receives the sender reference and the event identifier.

3. **Mediator decides what to do** — Based on the sender and event, the mediator determines which other components should react and how. It calls methods on those other components directly (because it holds references to all of them).

4. **Other components react** — The target components perform their actions without knowing who triggered them or why.

5. **Result is consistent state** — The mediator ensures the overall system state remains consistent. Components remain decoupled from each other; they only know about the mediator interface.

---

## Code Examples

### Python

```python
"""
Real-world example: Air Traffic Control (ATC) system.

Aircraft (components) do not communicate with each other directly.
Instead, all communication flows through the ATC tower (mediator).
This prevents collision conflicts and ensures orderly traffic management.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
import time


# ---------------------------------------------------------------------------
# Mediator Interface
# ---------------------------------------------------------------------------

class ATCMediator(ABC):
    """Abstract mediator: the Air Traffic Control interface."""

    @abstractmethod
    def notify(self, sender: "Aircraft", event: str, data: Optional[str] = None) -> None:
        pass

    @abstractmethod
    def request_landing(self, aircraft: "Aircraft") -> bool:
        pass

    @abstractmethod
    def request_takeoff(self, aircraft: "Aircraft") -> bool:
        pass


# ---------------------------------------------------------------------------
# Component Base
# ---------------------------------------------------------------------------

class Aircraft:
    """Base component. Each aircraft holds a reference to the ATC mediator."""

    def __init__(self, callsign: str, mediator: Optional[ATCMediator] = None) -> None:
        self.callsign = callsign
        self._mediator = mediator
        self.altitude = 0  # feet
        self.speed = 0     # knots
        self.on_ground = True

    def set_mediator(self, mediator: ATCMediator) -> None:
        self._mediator = mediator

    def request_takeoff(self) -> None:
        print(f"[{self.callsign}] Requesting takeoff clearance...")
        if self._mediator and self._mediator.request_takeoff(self):
            self._execute_takeoff()
        else:
            print(f"[{self.callsign}] Takeoff denied. Holding position.")

    def request_landing(self) -> None:
        print(f"[{self.callsign}] Requesting landing clearance...")
        if self._mediator and self._mediator.request_landing(self):
            self._execute_landing()
        else:
            print(f"[{self.callsign}] Landing denied. Entering holding pattern.")

    def _execute_takeoff(self) -> None:
        self.on_ground = False
        self.speed = 160
        self.altitude = 2000
        print(f"[{self.callsign}] Cleared for takeoff. Now airborne at {self.altitude} ft.")
        self._mediator.notify(self, "airborne")

    def _execute_landing(self) -> None:
        self.altitude = 0
        self.speed = 0
        self.on_ground = True
        print(f"[{self.callsign}] Cleared to land. Touchdown complete.")
        self._mediator.notify(self, "landed")

    def emergency(self, reason: str) -> None:
        print(f"[{self.callsign}] MAYDAY MAYDAY MAYDAY — {reason}")
        self._mediator.notify(self, "emergency", reason)

    def __repr__(self) -> str:
        status = "on ground" if self.on_ground else f"airborne at {self.altitude} ft"
        return f"Aircraft({self.callsign}, {status})"


# ---------------------------------------------------------------------------
# Concrete Mediator
# ---------------------------------------------------------------------------

class TowerATC(ATCMediator):
    """
    Concrete mediator: the control tower.
    Coordinates all aircraft operations, manages runway availability,
    and handles emergencies.
    """

    def __init__(self, airport_name: str) -> None:
        self.airport_name = airport_name
        self._aircraft_registry: dict[str, Aircraft] = {}
        self._runway_occupied: bool = False
        self._emergency_active: bool = False
        self._airborne: list[str] = []

    def register(self, aircraft: Aircraft) -> None:
        """Register an aircraft with this ATC tower."""
        self._aircraft_registry[aircraft.callsign] = aircraft
        aircraft.set_mediator(self)
        print(f"[ATC-{self.airport_name}] {aircraft.callsign} registered on frequency.")

    def notify(self, sender: Aircraft, event: str, data: Optional[str] = None) -> None:
        """Central notification handler — routes events to appropriate responses."""
        print(f"[ATC-{self.airport_name}] Received '{event}' from {sender.callsign}.")

        if event == "airborne":
            self._runway_occupied = False
            self._airborne.append(sender.callsign)
            print(f"[ATC-{self.airport_name}] Runway clear. {len(self._airborne)} aircraft airborne.")

        elif event == "landed":
            self._runway_occupied = False
            if sender.callsign in self._airborne:
                self._airborne.remove(sender.callsign)
            print(f"[ATC-{self.airport_name}] Runway clear. Welcome to {self.airport_name}.")

        elif event == "emergency":
            self._emergency_active = True
            print(f"[ATC-{self.airport_name}] EMERGENCY DECLARED. Clearing all traffic for {sender.callsign}.")
            # Notify all other airborne aircraft to hold
            for callsign, aircraft in self._aircraft_registry.items():
                if callsign != sender.callsign and not aircraft.on_ground:
                    print(f"[ATC-{self.airport_name}] {callsign}: enter holding pattern immediately.")

    def request_takeoff(self, aircraft: Aircraft) -> bool:
        """Evaluate and respond to a takeoff request."""
        if self._emergency_active:
            print(f"[ATC-{self.airport_name}] Takeoff denied: emergency in progress.")
            return False
        if self._runway_occupied:
            print(f"[ATC-{self.airport_name}] Takeoff denied: runway occupied.")
            return False
        if not aircraft.on_ground:
            print(f"[ATC-{self.airport_name}] {aircraft.callsign} is already airborne.")
            return False

        self._runway_occupied = True
        print(f"[ATC-{self.airport_name}] {aircraft.callsign}: cleared for takeoff runway 28L.")
        return True

    def request_landing(self, aircraft: Aircraft) -> bool:
        """Evaluate and respond to a landing request."""
        if self._runway_occupied:
            print(f"[ATC-{self.airport_name}] Landing denied: runway occupied.")
            return False
        if aircraft.on_ground:
            print(f"[ATC-{self.airport_name}] {aircraft.callsign} is already on the ground.")
            return False

        self._runway_occupied = True
        print(f"[ATC-{self.airport_name}] {aircraft.callsign}: cleared to land runway 10R.")
        return True


# ---------------------------------------------------------------------------
# Client Code
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("Air Traffic Control — Mediator Pattern Demo")
    print("=" * 60)

    # Create the mediator (ATC tower)
    tower = TowerATC("KJFK")

    # Create aircraft (components) and register them
    flight1 = Aircraft("UAL101")
    flight2 = Aircraft("DAL202")
    flight3 = Aircraft("AAL303")

    tower.register(flight1)
    tower.register(flight2)
    tower.register(flight3)

    print("\n--- Normal Operations ---")
    flight1.request_takeoff()   # Should succeed
    flight2.request_takeoff()   # Should be denied (runway occupied by flight1's sequence)

    print("\n--- Flight 2 tries again after runway clears ---")
    flight2.request_takeoff()   # Runway freed after flight1 airborne

    print("\n--- Landing sequence ---")
    flight1.request_landing()   # Should succeed
    flight2.request_landing()   # Denied — runway still occupied by flight1

    print("\n--- Emergency scenario ---")
    flight3.on_ground = False  # Simulate flight3 is airborne
    flight3.altitude = 5000
    flight3.emergency("Engine failure, immediate landing required")
    flight3.request_landing()


if __name__ == "__main__":
    main()
```

---

### Java

```java
/**
 * Real-world example: Chat Room application.
 *
 * Users (components) send messages to the ChatRoom (mediator),
 * which decides how to route those messages — privately, to all,
 * or to specific groups. Users never hold references to other users.
 */

import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

// ---------------------------------------------------------------------------
// Mediator Interface
// ---------------------------------------------------------------------------

interface ChatMediator {
    void register(User user);
    void sendMessage(String message, User sender);
    void sendPrivateMessage(String message, User sender, String recipientName);
    void broadcastSystemMessage(String message);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

class User {
    private final String name;
    private final String role; // "admin" or "member"
    private ChatMediator mediator;
    private final List<String> messageHistory = new ArrayList<>();

    public User(String name, String role) {
        this.name = name;
        this.role = role;
    }

    public void setMediator(ChatMediator mediator) {
        this.mediator = mediator;
    }

    public String getName() { return name; }
    public String getRole() { return role; }

    /** Send a message to the chat room (routed through mediator). */
    public void send(String message) {
        System.out.println("[" + timestamp() + "] " + name + " sends: \"" + message + "\"");
        mediator.sendMessage(message, this);
    }

    /** Send a private message to a specific user via mediator. */
    public void sendPrivate(String message, String recipientName) {
        System.out.println("[" + timestamp() + "] " + name + " DMs " + recipientName + ": \"" + message + "\"");
        mediator.sendPrivateMessage(message, this, recipientName);
    }

    /** Kick a user (admin only — mediator will validate). */
    public void kick(String targetName) {
        if (!"admin".equals(role)) {
            System.out.println("[" + name + "] You don't have permission to kick users.");
            return;
        }
        mediator.sendMessage("/kick " + targetName, this);
    }

    /** Called by the mediator when a message is delivered to this user. */
    public void receive(String message, String from) {
        String entry = "[" + timestamp() + "] [FROM: " + from + "] " + message;
        messageHistory.add(entry);
        System.out.println("  >> " + name + " receives: [" + from + "]: " + message);
    }

    public void receiveSystem(String message) {
        System.out.println("  >> [SYSTEM -> " + name + "]: " + message);
    }

    public List<String> getHistory() { return Collections.unmodifiableList(messageHistory); }

    private String timestamp() {
        return LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss"));
    }

    @Override
    public String toString() {
        return "User(" + name + ", " + role + ")";
    }
}

// ---------------------------------------------------------------------------
// Concrete Mediator
// ---------------------------------------------------------------------------

class ChatRoom implements ChatMediator {
    private final String roomName;
    private final Map<String, User> users = new LinkedHashMap<>();
    private final Set<String> bannedUsers = new HashSet<>();

    public ChatRoom(String roomName) {
        this.roomName = roomName;
        System.out.println("[ChatRoom: " + roomName + "] Room created.");
    }

    @Override
    public void register(User user) {
        users.put(user.getName(), user);
        user.setMediator(this);
        broadcastSystemMessage(user.getName() + " joined the room.");
        System.out.println("[ChatRoom] " + user.getName() + " (" + user.getRole() + ") registered.");
    }

    @Override
    public void sendMessage(String message, User sender) {
        // Handle admin commands
        if (message.startsWith("/kick ") && "admin".equals(sender.getRole())) {
            String targetName = message.substring(6).trim();
            handleKick(targetName, sender);
            return;
        }

        if (bannedUsers.contains(sender.getName())) {
            sender.receiveSystem("You have been banned from this room.");
            return;
        }

        // Broadcast to all other users
        for (User user : users.values()) {
            if (!user.getName().equals(sender.getName())) {
                user.receive(message, sender.getName());
            }
        }
    }

    @Override
    public void sendPrivateMessage(String message, User sender, String recipientName) {
        User recipient = users.get(recipientName);
        if (recipient == null) {
            sender.receiveSystem("User '" + recipientName + "' not found in this room.");
            return;
        }
        recipient.receive("[PM] " + message, sender.getName());
    }

    @Override
    public void broadcastSystemMessage(String message) {
        System.out.println("[SYSTEM - " + roomName + "]: " + message);
        for (User user : users.values()) {
            user.receiveSystem(message);
        }
    }

    private void handleKick(String targetName, User admin) {
        User target = users.get(targetName);
        if (target == null) {
            admin.receiveSystem("User '" + targetName + "' not found.");
            return;
        }
        if ("admin".equals(target.getRole())) {
            admin.receiveSystem("Cannot kick another admin.");
            return;
        }
        bannedUsers.add(targetName);
        users.remove(targetName);
        broadcastSystemMessage(targetName + " has been kicked by " + admin.getName() + ".");
    }

    public void printStats() {
        System.out.println("\n[ChatRoom Stats] Room: " + roomName);
        System.out.println("  Active users: " + users.keySet());
        System.out.println("  Banned users: " + bannedUsers);
    }
}

// ---------------------------------------------------------------------------
// Client Code
// ---------------------------------------------------------------------------

public class MediatorChatRoom {
    public static void main(String[] args) {
        System.out.println("=".repeat(55));
        System.out.println("Chat Room — Mediator Pattern Demo");
        System.out.println("=".repeat(55));

        ChatRoom room = new ChatRoom("tech-talk");

        User alice = new User("Alice", "admin");
        User bob   = new User("Bob",   "member");
        User carol = new User("Carol", "member");
        User dave  = new User("Dave",  "member");

        room.register(alice);
        room.register(bob);
        room.register(carol);
        room.register(dave);

        System.out.println("\n--- Public Messages ---");
        bob.send("Hey everyone, how's it going?");
        carol.send("All good here! Working on the new feature.");

        System.out.println("\n--- Private Message ---");
        alice.sendPrivate("Can you review my PR when you get a chance?", "Bob");

        System.out.println("\n--- Admin Action ---");
        dave.kick("Bob");    // Dave is not admin — should be denied
        alice.kick("Dave");  // Alice is admin — should succeed

        System.out.println("\n--- Post-kick Activity ---");
        carol.send("Is Dave still here?");

        room.printStats();
    }
}
```

---

### C++

```cpp
/**
 * Real-world example: Smart Home Automation System.
 *
 * Devices (Thermostat, SecurityCamera, SmartLight, DoorLock) are components.
 * The SmartHomeHub is the mediator that coordinates their interactions.
 * 
 * Example: When the security camera detects motion at night,
 * the hub turns on the lights and locks the doors — without the camera
 * needing to know anything about lights or locks.
 */

#include <iostream>
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <algorithm>
#include <ctime>

// ---------------------------------------------------------------------------
// Forward declarations
// ---------------------------------------------------------------------------
class SmartDevice;

// ---------------------------------------------------------------------------
// Mediator Interface
// ---------------------------------------------------------------------------
class HomeMediator {
public:
    virtual ~HomeMediator() = default;
    virtual void notify(SmartDevice* sender, const std::string& event,
                        const std::string& data = "") = 0;
    virtual void registerDevice(SmartDevice* device) = 0;
};

// ---------------------------------------------------------------------------
// Component Base
// ---------------------------------------------------------------------------
class SmartDevice {
protected:
    HomeMediator* mediator_;
    std::string name_;
    bool active_;

public:
    SmartDevice(const std::string& name, HomeMediator* mediator = nullptr)
        : mediator_(mediator), name_(name), active_(false) {}

    virtual ~SmartDevice() = default;

    void setMediator(HomeMediator* mediator) { mediator_ = mediator; }
    const std::string& getName() const { return name_; }
    bool isActive() const { return active_; }

    virtual void activate() {
        active_ = true;
        std::cout << "[" << name_ << "] Activated.\n";
    }

    virtual void deactivate() {
        active_ = false;
        std::cout << "[" << name_ << "] Deactivated.\n";
    }

    virtual void handleCommand(const std::string& command, const std::string& data) = 0;
};

// ---------------------------------------------------------------------------
// Concrete Components
// ---------------------------------------------------------------------------

class SmartLight : public SmartDevice {
    int brightness_; // 0-100
public:
    SmartLight(const std::string& name, HomeMediator* med = nullptr)
        : SmartDevice(name, med), brightness_(0) {}

    void setBrightness(int level) {
        brightness_ = std::clamp(level, 0, 100);
        active_ = (brightness_ > 0);
        std::cout << "[" << name_ << "] Brightness set to " << brightness_ << "%.\n";
        if (mediator_)
            mediator_->notify(this, "brightness_changed", std::to_string(brightness_));
    }

    void handleCommand(const std::string& command, const std::string& data) override {
        if (command == "set_brightness") {
            setBrightness(std::stoi(data));
        } else if (command == "turn_on") {
            setBrightness(100);
        } else if (command == "turn_off") {
            setBrightness(0);
        }
    }
};

class Thermostat : public SmartDevice {
    float temperature_; // Celsius
    float targetTemp_;
public:
    Thermostat(const std::string& name, HomeMediator* med = nullptr)
        : SmartDevice(name, med), temperature_(20.0f), targetTemp_(22.0f) {}

    void setTargetTemperature(float temp) {
        targetTemp_ = temp;
        active_ = true;
        std::cout << "[" << name_ << "] Target temperature set to " << temp << "°C.\n";
        if (mediator_)
            mediator_->notify(this, "temp_target_changed", std::to_string(temp));
    }

    void reportTemperature(float temp) {
        temperature_ = temp;
        std::cout << "[" << name_ << "] Current temperature: " << temp << "°C.\n";
        if (temp < 15.0f && mediator_)
            mediator_->notify(this, "temperature_critical", std::to_string(temp));
    }

    void handleCommand(const std::string& command, const std::string& data) override {
        if (command == "set_target")
            setTargetTemperature(std::stof(data));
        else if (command == "report_temp")
            reportTemperature(std::stof(data));
    }
};

class SecurityCamera : public SmartDevice {
    bool recordingActive_;
public:
    SecurityCamera(const std::string& name, HomeMediator* med = nullptr)
        : SmartDevice(name, med), recordingActive_(false) {}

    void detectMotion(const std::string& zone) {
        std::cout << "[" << name_ << "] Motion detected in zone: " << zone << "!\n";
        if (mediator_)
            mediator_->notify(this, "motion_detected", zone);
    }

    void startRecording() {
        recordingActive_ = true;
        active_ = true;
        std::cout << "[" << name_ << "] Recording started.\n";
    }

    void stopRecording() {
        recordingActive_ = false;
        std::cout << "[" << name_ << "] Recording stopped.\n";
    }

    void handleCommand(const std::string& command, const std::string& data) override {
        if (command == "detect_motion") detectMotion(data);
        else if (command == "start_recording") startRecording();
        else if (command == "stop_recording") stopRecording();
    }
};

class DoorLock : public SmartDevice {
    bool locked_;
public:
    DoorLock(const std::string& name, HomeMediator* med = nullptr)
        : SmartDevice(name, med), locked_(false) {}

    void lock() {
        locked_ = true;
        active_ = true;
        std::cout << "[" << name_ << "] Door LOCKED.\n";
        if (mediator_)
            mediator_->notify(this, "door_locked", "");
    }

    void unlock() {
        locked_ = false;
        active_ = false;
        std::cout << "[" << name_ << "] Door UNLOCKED.\n";
        if (mediator_)
            mediator_->notify(this, "door_unlocked", "");
    }

    bool isLocked() const { return locked_; }

    void handleCommand(const std::string& command, const std::string& data) override {
        if (command == "lock") lock();
        else if (command == "unlock") unlock();
    }
};

// ---------------------------------------------------------------------------
// Concrete Mediator
// ---------------------------------------------------------------------------
class SmartHomeHub : public HomeMediator {
    std::unordered_map<std::string, SmartDevice*> devices_;
    bool nightMode_;
    bool awayMode_;

    bool isNightTime() const {
        time_t now = time(nullptr);
        tm* ltm = localtime(&now);
        return (ltm->tm_hour >= 22 || ltm->tm_hour < 6);
    }

    SmartDevice* getDevice(const std::string& name) {
        auto it = devices_.find(name);
        return (it != devices_.end()) ? it->second : nullptr;
    }

    void sendCommand(const std::string& deviceName, const std::string& cmd,
                     const std::string& data = "") {
        SmartDevice* dev = getDevice(deviceName);
        if (dev) dev->handleCommand(cmd, data);
    }

public:
    SmartHomeHub() : nightMode_(false), awayMode_(false) {
        std::cout << "[SmartHomeHub] Hub initialized.\n";
    }

    void registerDevice(SmartDevice* device) override {
        devices_[device->getName()] = device;
        device->setMediator(this);
        std::cout << "[SmartHomeHub] Registered device: " << device->getName() << "\n";
    }

    void notify(SmartDevice* sender, const std::string& event,
                const std::string& data) override {
        std::cout << "[SmartHomeHub] Event '" << event
                  << "' from '" << sender->getName() << "'";
        if (!data.empty()) std::cout << " (data: " << data << ")";
        std::cout << "\n";

        if (event == "motion_detected") {
            // Turn on lights and start recording when motion is detected
            sendCommand("LivingRoomLight", "set_brightness", "80");
            sendCommand("EntranceCamera", "start_recording");
            if (awayMode_) {
                // Lock all doors when away
                sendCommand("FrontDoor", "lock");
                std::cout << "[SmartHomeHub] ALERT: Motion detected while in away mode!\n";
            }
        }
        else if (event == "temperature_critical") {
            // Boost heating if temperature drops critically
            std::cout << "[SmartHomeHub] Critical temperature! Activating emergency heating.\n";
            sendCommand("Thermostat", "set_target", "24");
        }
        else if (event == "door_locked") {
            // Dim lights when door is locked (user going to sleep)
            if (isNightTime()) {
                sendCommand("LivingRoomLight", "set_brightness", "20");
                std::cout << "[SmartHomeHub] Night mode activated.\n";
                nightMode_ = true;
            }
        }
        else if (event == "door_unlocked") {
            // Welcome home — turn on lights
            sendCommand("LivingRoomLight", "turn_on");
            nightMode_ = false;
        }
    }

    void setAwayMode(bool away) {
        awayMode_ = away;
        if (away) {
            std::cout << "[SmartHomeHub] Away mode ON — locking all doors.\n";
            sendCommand("FrontDoor", "lock");
            sendCommand("LivingRoomLight", "turn_off");
        } else {
            std::cout << "[SmartHomeHub] Away mode OFF — welcome home!\n";
            sendCommand("FrontDoor", "unlock");
            sendCommand("LivingRoomLight", "turn_on");
        }
    }
};

// ---------------------------------------------------------------------------
// Client Code
// ---------------------------------------------------------------------------
int main() {
    std::cout << std::string(55, '=') << "\n";
    std::cout << "Smart Home Automation — Mediator Pattern Demo\n";
    std::cout << std::string(55, '=') << "\n\n";

    SmartHomeHub hub;

    SmartLight      livingRoomLight("LivingRoomLight");
    Thermostat      thermostat("Thermostat");
    SecurityCamera  camera("EntranceCamera");
    DoorLock        frontDoor("FrontDoor");

    hub.registerDevice(&livingRoomLight);
    hub.registerDevice(&thermostat);
    hub.registerDevice(&camera);
    hub.registerDevice(&frontDoor);

    std::cout << "\n--- Scenario 1: Normal evening ---\n";
    frontDoor.lock();           // Hub dims lights for night mode

    std::cout << "\n--- Scenario 2: Motion detected while home ---\n";
    camera.detectMotion("Front Yard");  // Hub turns on lights + starts recording

    std::cout << "\n--- Scenario 3: Away mode ---\n";
    hub.setAwayMode(true);
    camera.detectMotion("Backyard"); // Hub sends alert and locks door

    std::cout << "\n--- Scenario 4: Temperature emergency ---\n";
    thermostat.reportTemperature(12.5f);  // Hub boosts heating

    std::cout << "\n--- Scenario 5: Coming home ---\n";
    hub.setAwayMode(false);

    return 0;
}
```

---

### C#

```csharp
/**
 * Real-world example: Hospital Coordination System.
 *
 * Medical staff (Doctor, Nurse, Pharmacist, Lab) are components.
 * The HospitalCoordinator is the mediator that routes requests
 * between departments without them needing direct references.
 */

using System;
using System.Collections.Generic;

// ---------------------------------------------------------------------------
// Mediator Interface
// ---------------------------------------------------------------------------
public interface IHospitalMediator
{
    void Notify(MedicalStaff sender, string eventType, string patientId, string data = "");
    void Register(MedicalStaff staff);
}

// ---------------------------------------------------------------------------
// Component Base
// ---------------------------------------------------------------------------
public abstract class MedicalStaff
{
    protected IHospitalMediator _mediator;
    public string Name { get; }
    public string Department { get; }

    protected MedicalStaff(string name, string department)
    {
        Name = name;
        Department = department;
    }

    public void SetMediator(IHospitalMediator mediator) => _mediator = mediator;

    public abstract void ReceiveNotification(string eventType, string patientId, string from, string data);
}

// ---------------------------------------------------------------------------
// Concrete Components
// ---------------------------------------------------------------------------
public class Doctor : MedicalStaff
{
    private readonly List<string> _activePatients = new();

    public Doctor(string name) : base(name, "Medical") { }

    public void AdmitPatient(string patientId, string diagnosis)
    {
        _activePatients.Add(patientId);
        Console.WriteLine($"[Dr. {Name}] Admitting patient {patientId} with diagnosis: {diagnosis}");
        _mediator.Notify(this, "patient_admitted", patientId, diagnosis);
    }

    public void OrderMedication(string patientId, string medication)
    {
        Console.WriteLine($"[Dr. {Name}] Ordering medication '{medication}' for patient {patientId}");
        _mediator.Notify(this, "medication_ordered", patientId, medication);
    }

    public void OrderLabTest(string patientId, string testType)
    {
        Console.WriteLine($"[Dr. {Name}] Ordering lab test '{testType}' for patient {patientId}");
        _mediator.Notify(this, "lab_test_ordered", patientId, testType);
    }

    public void DischargePatient(string patientId)
    {
        _activePatients.Remove(patientId);
        Console.WriteLine($"[Dr. {Name}] Discharging patient {patientId}");
        _mediator.Notify(this, "patient_discharged", patientId);
    }

    public override void ReceiveNotification(string eventType, string patientId, string from, string data)
    {
        if (eventType == "lab_results_ready")
            Console.WriteLine($"  [Dr. {Name}] Lab results for patient {patientId}: {data} (from {from})");
        else if (eventType == "medication_dispensed")
            Console.WriteLine($"  [Dr. {Name}] Medication dispensed for patient {patientId}: {data}");
    }
}

public class Nurse : MedicalStaff
{
    public Nurse(string name) : base(name, "Nursing") { }

    public void ReportVitals(string patientId, string vitals)
    {
        Console.WriteLine($"[Nurse {Name}] Reporting vitals for {patientId}: {vitals}");
        _mediator.Notify(this, "vitals_reported", patientId, vitals);
    }

    public override void ReceiveNotification(string eventType, string patientId, string from, string data)
    {
        switch (eventType)
        {
            case "patient_admitted":
                Console.WriteLine($"  [Nurse {Name}] Prepare bed for patient {patientId}. Diagnosis: {data}");
                break;
            case "medication_dispensed":
                Console.WriteLine($"  [Nurse {Name}] Administer medication to patient {patientId}: {data}");
                break;
            case "patient_discharged":
                Console.WriteLine($"  [Nurse {Name}] Prepare discharge paperwork for patient {patientId}");
                break;
        }
    }
}

public class Pharmacist : MedicalStaff
{
    private readonly Dictionary<string, int> _inventory = new()
    {
        { "Amoxicillin", 50 },
        { "Ibuprofen", 100 },
        { "Metformin", 75 },
        { "Lisinopril", 40 }
    };

    public Pharmacist(string name) : base(name, "Pharmacy") { }

    public override void ReceiveNotification(string eventType, string patientId, string from, string data)
    {
        if (eventType == "medication_ordered")
        {
            DispenseMedication(patientId, data);
        }
    }

    private void DispenseMedication(string patientId, string medication)
    {
        if (_inventory.TryGetValue(medication, out int stock) && stock > 0)
        {
            _inventory[medication]--;
            Console.WriteLine($"  [Pharmacist {Name}] Dispensing '{medication}' for patient {patientId}. Stock remaining: {_inventory[medication]}");
            _mediator.Notify(this, "medication_dispensed", patientId, medication);
        }
        else
        {
            Console.WriteLine($"  [Pharmacist {Name}] OUT OF STOCK: '{medication}'. Notifying doctor.");
            _mediator.Notify(this, "medication_unavailable", patientId, medication);
        }
    }
}

public class Laboratory : MedicalStaff
{
    public Laboratory() : base("Lab Team", "Laboratory") { }

    public override void ReceiveNotification(string eventType, string patientId, string from, string data)
    {
        if (eventType == "lab_test_ordered")
        {
            RunTest(patientId, data);
        }
    }

    private void RunTest(string patientId, string testType)
    {
        Console.WriteLine($"  [Lab] Running '{testType}' for patient {patientId}...");
        // Simulate test result
        string result = testType switch
        {
            "blood_glucose" => "6.2 mmol/L (Normal)",
            "CBC"           => "WBC: 7.5 G/L, RBC: 4.8 T/L (Normal)",
            "lipid_panel"   => "LDL: 3.1 mmol/L (Borderline High)",
            _               => "Result: Normal"
        };
        Console.WriteLine($"  [Lab] Test '{testType}' complete for patient {patientId}.");
        _mediator.Notify(this, "lab_results_ready", patientId, result);
    }
}

// ---------------------------------------------------------------------------
// Concrete Mediator
// ---------------------------------------------------------------------------
public class HospitalCoordinator : IHospitalMediator
{
    private readonly Dictionary<string, List<MedicalStaff>> _departments = new();
    private readonly List<string> _eventLog = new();

    public void Register(MedicalStaff staff)
    {
        if (!_departments.ContainsKey(staff.Department))
            _departments[staff.Department] = new List<MedicalStaff>();

        _departments[staff.Department].Add(staff);
        staff.SetMediator(this);
        Console.WriteLine($"[Coordinator] {staff.Name} ({staff.Department}) registered.");
    }

    public void Notify(MedicalStaff sender, string eventType, string patientId, string data = "")
    {
        string logEntry = $"[{DateTime.Now:HH:mm:ss}] {eventType} | Patient: {patientId} | From: {sender.Name}";
        _eventLog.Add(logEntry);
        Console.WriteLine($"[Coordinator] Routing event '{eventType}' for patient {patientId}...");

        // Route to appropriate departments based on event type
        switch (eventType)
        {
            case "patient_admitted":
                NotifyDepartment("Nursing", eventType, patientId, sender.Name, data);
                break;

            case "medication_ordered":
                NotifyDepartment("Pharmacy", eventType, patientId, sender.Name, data);
                break;

            case "medication_dispensed":
            case "medication_unavailable":
                NotifyDepartment("Medical", eventType, patientId, sender.Name, data);
                NotifyDepartment("Nursing", eventType, patientId, sender.Name, data);
                break;

            case "lab_test_ordered":
                NotifyDepartment("Laboratory", eventType, patientId, sender.Name, data);
                break;

            case "lab_results_ready":
                NotifyDepartment("Medical", eventType, patientId, sender.Name, data);
                break;

            case "vitals_reported":
                NotifyDepartment("Medical", eventType, patientId, sender.Name, data);
                break;

            case "patient_discharged":
                NotifyDepartment("Nursing", eventType, patientId, sender.Name, data);
                break;
        }
    }

    private void NotifyDepartment(string dept, string eventType, string patientId,
                                   string from, string data)
    {
        if (_departments.TryGetValue(dept, out var staff))
            foreach (var member in staff)
                member.ReceiveNotification(eventType, patientId, from, data);
    }

    public void PrintEventLog()
    {
        Console.WriteLine("\n[Coordinator] === Event Log ===");
        foreach (var entry in _eventLog)
            Console.WriteLine("  " + entry);
    }
}

// ---------------------------------------------------------------------------
// Client Code
// ---------------------------------------------------------------------------
class MediatorHospital
{
    static void Main()
    {
        Console.WriteLine(new string('=', 55));
        Console.WriteLine("Hospital Coordination — Mediator Pattern Demo");
        Console.WriteLine(new string('=', 55));

        var coordinator = new HospitalCoordinator();

        var drSmith    = new Doctor("Smith");
        var nurseJones = new Nurse("Jones");
        var pharmacist = new Pharmacist("Chen");
        var lab        = new Laboratory();

        coordinator.Register(drSmith);
        coordinator.Register(nurseJones);
        coordinator.Register(pharmacist);
        coordinator.Register(lab);

        Console.WriteLine("\n--- Patient P001 Admission ---");
        drSmith.AdmitPatient("P001", "Type 2 Diabetes");

        Console.WriteLine("\n--- Ordering Tests and Medication ---");
        drSmith.OrderLabTest("P001", "blood_glucose");
        drSmith.OrderMedication("P001", "Metformin");

        Console.WriteLine("\n--- Nurse Reports Vitals ---");
        nurseJones.ReportVitals("P001", "BP: 135/85, HR: 78 bpm, Temp: 37.1°C");

        Console.WriteLine("\n--- Discharge ---");
        drSmith.DischargePatient("P001");

        coordinator.PrintEventLog();
    }
}
```

---

### TypeScript

```typescript
/**
 * Real-world example: Event-driven UI Component System.
 *
 * UI components (SearchBar, FilterPanel, ResultsList, Pagination, StatusBar)
 * communicate through a DashboardMediator. When a user types in the search
 * bar, the mediator resets pagination, clears filters, triggers a search,
 * and updates the status bar — all without components knowing about each other.
 */

// ---------------------------------------------------------------------------
// Types & Interfaces
// ---------------------------------------------------------------------------

interface UIMediator {
  notify(sender: UIComponent, event: string, payload?: unknown): void;
  registerComponent(component: UIComponent): void;
}

interface SearchQuery {
  term: string;
  filters: Record<string, string>;
  page: number;
  pageSize: number;
}

// ---------------------------------------------------------------------------
// Component Base
// ---------------------------------------------------------------------------

abstract class UIComponent {
  protected mediator: UIMediator | null = null;
  public readonly id: string;

  constructor(id: string) {
    this.id = id;
  }

  setMediator(mediator: UIMediator): void {
    this.mediator = mediator;
  }

  protected emit(event: string, payload?: unknown): void {
    this.mediator?.notify(this, event, payload);
  }

  abstract render(): string;
  abstract handleUpdate(event: string, payload?: unknown): void;
}

// ---------------------------------------------------------------------------
// Concrete Components
// ---------------------------------------------------------------------------

class SearchBar extends UIComponent {
  private value = "";
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    super("search-bar");
  }

  /** Simulates a user typing in the search box. */
  userTypes(text: string): void {
    this.value = text;
    console.log(`[SearchBar] User typed: "${text}"`);

    // Debounce: wait 300ms before emitting
    if (this.debounceTimer) clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(() => {
      this.emit("search_changed", { term: this.value });
    }, 100); // shortened for demo
  }

  /** Called by the mediator to clear the search field. */
  handleUpdate(event: string, payload?: unknown): void {
    if (event === "clear_search") {
      this.value = "";
      console.log(`  [SearchBar] Cleared.`);
    }
  }

  render(): string {
    return `<SearchBar value="${this.value}" />`;
  }
}

class FilterPanel extends UIComponent {
  private activeFilters: Record<string, string> = {};

  constructor() {
    super("filter-panel");
  }

  applyFilter(key: string, value: string): void {
    this.activeFilters[key] = value;
    console.log(`[FilterPanel] Filter applied: ${key}=${value}`);
    this.emit("filter_changed", { filters: { ...this.activeFilters } });
  }

  removeFilter(key: string): void {
    delete this.activeFilters[key];
    console.log(`[FilterPanel] Filter removed: ${key}`);
    this.emit("filter_changed", { filters: { ...this.activeFilters } });
  }

  getFilters(): Record<string, string> {
    return { ...this.activeFilters };
  }

  handleUpdate(event: string, payload?: unknown): void {
    if (event === "reset_filters") {
      this.activeFilters = {};
      console.log(`  [FilterPanel] All filters reset.`);
    }
  }

  render(): string {
    const filters = Object.entries(this.activeFilters)
      .map(([k, v]) => `${k}:${v}`)
      .join(", ");
    return `<FilterPanel filters="${filters || "none"}" />`;
  }
}

class ResultsList extends UIComponent {
  private results: string[] = [];
  private isLoading = false;

  constructor() {
    super("results-list");
  }

  handleUpdate(event: string, payload?: unknown): void {
    if (event === "show_loading") {
      this.isLoading = true;
      this.results = [];
      console.log(`  [ResultsList] Showing loading state...`);
    } else if (event === "show_results") {
      this.isLoading = false;
      this.results = (payload as { items: string[] }).items;
      console.log(`  [ResultsList] Showing ${this.results.length} results.`);
    }
  }

  render(): string {
    if (this.isLoading) return `<ResultsList loading={true} />`;
    return `<ResultsList items={[${this.results.map(r => `"${r}"`).join(", ")}]} />`;
  }
}

class Pagination extends UIComponent {
  private currentPage = 1;
  private totalPages = 1;

  constructor() {
    super("pagination");
  }

  goToPage(page: number): void {
    if (page < 1 || page > this.totalPages) return;
    this.currentPage = page;
    console.log(`[Pagination] Navigating to page ${page} of ${this.totalPages}`);
    this.emit("page_changed", { page: this.currentPage });
  }

  handleUpdate(event: string, payload?: unknown): void {
    if (event === "reset_pagination") {
      this.currentPage = 1;
      console.log(`  [Pagination] Reset to page 1.`);
    } else if (event === "update_total") {
      const { totalPages } = payload as { totalPages: number };
      this.totalPages = totalPages;
      console.log(`  [Pagination] Total pages updated to ${totalPages}.`);
    }
  }

  render(): string {
    return `<Pagination current={${this.currentPage}} total={${this.totalPages}} />`;
  }
}

class StatusBar extends UIComponent {
  private message = "Ready";
  private count = 0;

  constructor() {
    super("status-bar");
  }

  handleUpdate(event: string, payload?: unknown): void {
    if (event === "update_status") {
      const { message, count } = payload as { message: string; count: number };
      this.message = message;
      this.count = count;
      console.log(`  [StatusBar] Status: "${message}" (${count} results)`);
    }
  }

  render(): string {
    return `<StatusBar message="${this.message}" count={${this.count}} />`;
  }
}

// ---------------------------------------------------------------------------
// Concrete Mediator
// ---------------------------------------------------------------------------

class DashboardMediator implements UIMediator {
  private components = new Map<string, UIComponent>();
  private currentQuery: SearchQuery = {
    term: "",
    filters: {},
    page: 1,
    pageSize: 10,
  };

  registerComponent(component: UIComponent): void {
    this.components.set(component.id, component);
    component.setMediator(this);
    console.log(`[DashboardMediator] Registered: ${component.id}`);
  }

  notify(sender: UIComponent, event: string, payload?: unknown): void {
    console.log(
      `[DashboardMediator] Event "${event}" from "${sender.id}"`
    );

    switch (event) {
      case "search_changed": {
        const { term } = payload as { term: string };
        this.currentQuery = { ...this.currentQuery, term, page: 1 };
        // Reset pagination and trigger search
        this.get<Pagination>("pagination")?.handleUpdate("reset_pagination");
        this.get<FilterPanel>("filter-panel")?.handleUpdate("reset_filters");
        this.executeSearch();
        break;
      }

      case "filter_changed": {
        const { filters } = payload as { filters: Record<string, string> };
        this.currentQuery = { ...this.currentQuery, filters, page: 1 };
        this.get<Pagination>("pagination")?.handleUpdate("reset_pagination");
        this.executeSearch();
        break;
      }

      case "page_changed": {
        const { page } = payload as { page: number };
        this.currentQuery = { ...this.currentQuery, page };
        this.executeSearch();
        break;
      }
    }
  }

  private get<T extends UIComponent>(id: string): T | undefined {
    return this.components.get(id) as T | undefined;
  }

  /** Simulates an async data fetch and routes results to all affected components. */
  private executeSearch(): void {
    const { term, filters, page } = this.currentQuery;
    const filterStr = Object.entries(filters).map(([k, v]) => `${k}=${v}`).join("&");
    console.log(
      `[DashboardMediator] Executing search: term="${term}" filters=[${filterStr}] page=${page}`
    );

    // Show loading state
    this.get<ResultsList>("results-list")?.handleUpdate("show_loading");
    this.get<StatusBar>("status-bar")?.handleUpdate("update_status", {
      message: "Searching...",
      count: 0,
    });

    // Simulate API response
    const mockResults = [
      `Result for "${term}" #1`,
      `Result for "${term}" #2`,
      `Result for "${term}" #3`,
    ].filter((_, i) => Object.keys(filters).length === 0 || i < 2);

    const totalPages = Math.ceil(mockResults.length / this.currentQuery.pageSize) || 1;

    // Distribute results to components
    this.get<ResultsList>("results-list")?.handleUpdate("show_results", {
      items: mockResults,
    });
    this.get<Pagination>("pagination")?.handleUpdate("update_total", { totalPages });
    this.get<StatusBar>("status-bar")?.handleUpdate("update_status", {
      message: `Found ${mockResults.length} results`,
      count: mockResults.length,
    });
  }
}

// ---------------------------------------------------------------------------
// Client Code
// ---------------------------------------------------------------------------

function renderDashboard(components: UIComponent[]): void {
  console.log("\n--- Dashboard Render ---");
  components.forEach((c) => console.log(" ", c.render()));
}

const mediator = new DashboardMediator();

const searchBar   = new SearchBar();
const filterPanel = new FilterPanel();
const resultsList = new ResultsList();
const pagination  = new Pagination();
const statusBar   = new StatusBar();

[searchBar, filterPanel, resultsList, pagination, statusBar].forEach((c) =>
  mediator.registerComponent(c)
);

const allComponents = [searchBar, filterPanel, resultsList, pagination, statusBar];

console.log("\n" + "=".repeat(55));
console.log("Dashboard UI — Mediator Pattern Demo");
console.log("=".repeat(55));

console.log("\n--- User searches for 'typescript' ---");
searchBar.userTypes("typescript");

// Allow debounce to fire
setTimeout(() => {
  console.log("\n--- User applies a filter ---");
  filterPanel.applyFilter("category", "tutorial");

  console.log("\n--- User navigates to page 2 ---");
  pagination.goToPage(2);

  renderDashboard(allComponents);
}, 200);
```

---

### Go

```go
// Real-world example: Microservice Event Bus.
//
// Services (OrderService, InventoryService, NotificationService, BillingService)
// communicate through an EventBus mediator. When an order is placed, the
// mediator routes the event to inventory (to reserve stock), billing (to charge),
// and notifications (to send confirmation) — without any service knowing the others.

package main

import (
	"fmt"
	"math/rand"
	"strings"
	"time"
)

// ---------------------------------------------------------------------------
// Event & Mediator interface
// ---------------------------------------------------------------------------

// Event represents a message passed between services.
type Event struct {
	Type    string
	Payload map[string]string
	Source  string
}

// EventHandler is the mediator interface.
type EventHandler interface {
	Publish(event Event)
	Subscribe(eventType string, handler Service)
	RegisterService(service Service)
}

// Service is the component interface.
type Service interface {
	GetName() string
	Handle(event Event) error
	SetBus(bus EventHandler)
}

// ---------------------------------------------------------------------------
// BaseService provides shared mediator-referencing logic.
// ---------------------------------------------------------------------------

type BaseService struct {
	name string
	bus  EventHandler
}

func (b *BaseService) GetName() string        { return b.name }
func (b *BaseService) SetBus(bus EventHandler) { b.bus = bus }

func (b *BaseService) publish(eventType string, payload map[string]string) {
	b.bus.Publish(Event{
		Type:    eventType,
		Payload: payload,
		Source:  b.name,
	})
}

// ---------------------------------------------------------------------------
// Concrete Services (Components)
// ---------------------------------------------------------------------------

// OrderService handles order creation and cancellation.
type OrderService struct {
	BaseService
	orders map[string]string // orderID -> status
}

func NewOrderService() *OrderService {
	return &OrderService{
		BaseService: BaseService{name: "OrderService"},
		orders:      make(map[string]string),
	}
}

func (s *OrderService) PlaceOrder(productID, userID string, quantity int) string {
	orderID := fmt.Sprintf("ORD-%04d", rand.Intn(9000)+1000)
	s.orders[orderID] = "pending"
	fmt.Printf("[%s] Order %s placed by user %s (product: %s, qty: %d)\n",
		s.name, orderID, userID, productID, quantity)

	// Publish event — let the bus route it to the right services
	s.publish("order.placed", map[string]string{
		"order_id":   orderID,
		"user_id":    userID,
		"product_id": productID,
		"quantity":   fmt.Sprintf("%d", quantity),
	})
	return orderID
}

func (s *OrderService) Handle(event Event) error {
	switch event.Type {
	case "inventory.reserved":
		orderID := event.Payload["order_id"]
		s.orders[orderID] = "confirmed"
		fmt.Printf("  [%s] Order %s confirmed (inventory reserved).\n", s.name, orderID)

	case "inventory.failed":
		orderID := event.Payload["order_id"]
		s.orders[orderID] = "failed"
		fmt.Printf("  [%s] Order %s failed — insufficient inventory.\n", s.name, orderID)
		// Publish cancellation so billing and notifications react
		s.publish("order.cancelled", map[string]string{
			"order_id": orderID,
			"reason":   "out_of_stock",
		})

	case "billing.charged":
		orderID := event.Payload["order_id"]
		fmt.Printf("  [%s] Payment confirmed for order %s.\n", s.name, orderID)
	}
	return nil
}

// InventoryService manages product stock.
type InventoryService struct {
	BaseService
	stock map[string]int
}

func NewInventoryService() *InventoryService {
	return &InventoryService{
		BaseService: BaseService{name: "InventoryService"},
		stock: map[string]int{
			"PROD-001": 10,
			"PROD-002": 2,
			"PROD-003": 0,
		},
	}
}

func (s *InventoryService) Handle(event Event) error {
	if event.Type != "order.placed" {
		return nil
	}

	orderID   := event.Payload["order_id"]
	productID := event.Payload["product_id"]
	quantity  := 0
	fmt.Sscanf(event.Payload["quantity"], "%d", &quantity)

	available, ok := s.stock[productID]
	if !ok || available < quantity {
		fmt.Printf("  [%s] Insufficient stock for %s (have %d, need %d).\n",
			s.name, productID, available, quantity)
		s.publish("inventory.failed", map[string]string{"order_id": orderID})
		return nil
	}

	s.stock[productID] -= quantity
	fmt.Printf("  [%s] Reserved %d units of %s. Remaining stock: %d.\n",
		s.name, quantity, productID, s.stock[productID])
	s.publish("inventory.reserved", map[string]string{
		"order_id":   orderID,
		"product_id": productID,
		"quantity":   fmt.Sprintf("%d", quantity),
	})
	return nil
}

// BillingService processes payments.
type BillingService struct {
	BaseService
	prices map[string]float64
}

func NewBillingService() *BillingService {
	return &BillingService{
		BaseService: BaseService{name: "BillingService"},
		prices: map[string]float64{
			"PROD-001": 29.99,
			"PROD-002": 149.99,
			"PROD-003": 9.99,
		},
	}
}

func (s *BillingService) Handle(event Event) error {
	switch event.Type {
	case "inventory.reserved":
		orderID   := event.Payload["order_id"]
		productID := event.Payload["product_id"]
		quantity  := 1
		fmt.Sscanf(event.Payload["quantity"], "%d", &quantity)

		price := s.prices[productID] * float64(quantity)
		fmt.Printf("  [%s] Charging $%.2f for order %s.\n", s.name, price, orderID)
		s.publish("billing.charged", map[string]string{
			"order_id": orderID,
			"amount":   fmt.Sprintf("%.2f", price),
		})

	case "order.cancelled":
		orderID := event.Payload["order_id"]
		fmt.Printf("  [%s] No charge issued — order %s was cancelled.\n", s.name, orderID)
	}
	return nil
}

// NotificationService sends emails/SMS.
type NotificationService struct {
	BaseService
}

func NewNotificationService() *NotificationService {
	return &NotificationService{BaseService: BaseService{name: "NotificationService"}}
}

func (s *NotificationService) Handle(event Event) error {
	switch event.Type {
	case "billing.charged":
		orderID := event.Payload["order_id"]
		amount  := event.Payload["amount"]
		fmt.Printf("  [%s] Sending confirmation email: Order %s confirmed. Amount: $%s.\n",
			s.name, orderID, amount)

	case "order.cancelled":
		orderID := event.Payload["order_id"]
		reason  := event.Payload["reason"]
		fmt.Printf("  [%s] Sending cancellation email: Order %s cancelled (%s).\n",
			s.name, orderID, reason)
	}
	return nil
}

// ---------------------------------------------------------------------------
// Concrete Mediator: EventBus
// ---------------------------------------------------------------------------

type EventBus struct {
	services      map[string]Service
	subscriptions map[string][]Service
	eventLog      []string
}

func NewEventBus() *EventBus {
	return &EventBus{
		services:      make(map[string]Service),
		subscriptions: make(map[string][]Service),
	}
}

func (b *EventBus) RegisterService(service Service) {
	b.services[service.GetName()] = service
	service.SetBus(b)
	fmt.Printf("[EventBus] Registered service: %s\n", service.GetName())
}

func (b *EventBus) Subscribe(eventType string, handler Service) {
	b.subscriptions[eventType] = append(b.subscriptions[eventType], handler)
	fmt.Printf("[EventBus] %s subscribed to '%s'\n", handler.GetName(), eventType)
}

func (b *EventBus) Publish(event Event) {
	logEntry := fmt.Sprintf("[%s] %s -> %s",
		time.Now().Format("15:04:05"), event.Source, event.Type)
	b.eventLog = append(b.eventLog, logEntry)

	fmt.Printf("[EventBus] Publishing '%s' from %s\n", event.Type, event.Source)

	handlers, ok := b.subscriptions[event.Type]
	if !ok || len(handlers) == 0 {
		fmt.Printf("[EventBus] No handlers for event '%s'\n", event.Type)
		return
	}

	for _, handler := range handlers {
		if handler.GetName() != event.Source { // Don't send back to sender
			if err := handler.Handle(event); err != nil {
				fmt.Printf("[EventBus] Error in %s handling %s: %v\n",
					handler.GetName(), event.Type, err)
			}
		}
	}
}

func (b *EventBus) PrintEventLog() {
	fmt.Println("\n[EventBus] === Event Log ===")
	for _, entry := range b.eventLog {
		fmt.Println(" ", entry)
	}
}

// ---------------------------------------------------------------------------
// Client Code
// ---------------------------------------------------------------------------

func main() {
	fmt.Println(strings.Repeat("=", 55))
	fmt.Println("Microservice Event Bus — Mediator Pattern Demo")
	fmt.Println(strings.Repeat("=", 55))

	rand.Seed(time.Now().UnixNano())

	bus := NewEventBus()

	// Create services (components)
	orderSvc   := NewOrderService()
	invSvc     := NewInventoryService()
	billSvc    := NewBillingService()
	notifySvc  := NewNotificationService()

	// Register with mediator
	bus.RegisterService(orderSvc)
	bus.RegisterService(invSvc)
	bus.RegisterService(billSvc)
	bus.RegisterService(notifySvc)

	// Subscribe services to relevant events
	fmt.Println()
	bus.Subscribe("order.placed",      invSvc)
	bus.Subscribe("order.cancelled",   billSvc)
	bus.Subscribe("order.cancelled",   notifySvc)
	bus.Subscribe("inventory.reserved", orderSvc)
	bus.Subscribe("inventory.reserved", billSvc)
	bus.Subscribe("inventory.failed",   orderSvc)
	bus.Subscribe("billing.charged",    orderSvc)
	bus.Subscribe("billing.charged",    notifySvc)

	// Scenario 1: Successful order
	fmt.Println("\n--- Scenario 1: Successful Order ---")
	orderSvc.PlaceOrder("PROD-001", "USER-42", 2)

	// Scenario 2: Insufficient stock
	fmt.Println("\n--- Scenario 2: Out of Stock ---")
	orderSvc.PlaceOrder("PROD-003", "USER-99", 5)

	bus.PrintEventLog()
}
```

---

### PHP

```php
<?php
/**
 * Real-world example: E-commerce Checkout Workflow.
 *
 * Steps (Cart, AddressForm, PaymentForm, OrderSummary, SubmitButton)
 * are components. CheckoutMediator coordinates their state — enabling
 * and disabling steps, validating data, and advancing the flow.
 */

declare(strict_types=1);

// ---------------------------------------------------------------------------
// Mediator Interface
// ---------------------------------------------------------------------------

interface CheckoutMediatorInterface
{
    public function notify(CheckoutComponent $sender, string $event, array $data = []): void;
    public function register(CheckoutComponent $component): void;
}

// ---------------------------------------------------------------------------
// Component Base
// ---------------------------------------------------------------------------

abstract class CheckoutComponent
{
    protected ?CheckoutMediatorInterface $mediator = null;
    protected string $id;
    protected bool $enabled;

    public function __construct(string $id, bool $enabled = true)
    {
        $this->id      = $id;
        $this->enabled = $enabled;
    }

    public function setMediator(CheckoutMediatorInterface $mediator): void
    {
        $this->mediator = $mediator;
    }

    public function getId(): string  { return $this->id; }
    public function isEnabled(): bool { return $this->enabled; }
    public function enable(): void   { $this->enabled = true; }
    public function disable(): void  { $this->enabled = false; }

    protected function emit(string $event, array $data = []): void
    {
        $this->mediator?->notify($this, $event, $data);
    }

    abstract public function handleUpdate(string $event, array $data = []): void;
    abstract public function render(): string;
}

// ---------------------------------------------------------------------------
// Concrete Components
// ---------------------------------------------------------------------------

class Cart extends CheckoutComponent
{
    private array $items = [];
    private float $total = 0.0;

    public function __construct()
    {
        parent::__construct('cart');
    }

    public function addItem(string $name, float $price, int $qty = 1): void
    {
        $this->items[] = compact('name', 'price', 'qty');
        $this->total  += $price * $qty;
        echo "[Cart] Added: {$name} x{$qty} @ \${$price}\n";
        $this->emit('cart_updated', ['total' => $this->total, 'count' => count($this->items)]);
    }

    public function removeItem(int $index): void
    {
        if (!isset($this->items[$index])) {
            echo "[Cart] Item #{$index} not found.\n";
            return;
        }
        $item          = $this->items[$index];
        $this->total  -= $item['price'] * $item['qty'];
        array_splice($this->items, $index, 1);
        echo "[Cart] Removed: {$item['name']}\n";
        $this->emit('cart_updated', ['total' => $this->total, 'count' => count($this->items)]);
    }

    public function getTotal(): float  { return $this->total; }
    public function getItems(): array  { return $this->items; }

    public function handleUpdate(string $event, array $data = []): void
    {
        // Cart doesn't react to other components in this example
    }

    public function render(): string
    {
        $lines = array_map(
            fn($item) => "  - {$item['name']} x{$item['qty']} @ \${$item['price']}",
            $this->items
        );
        return "<Cart total=\${$this->total}>\n" . implode("\n", $lines) . "\n</Cart>";
    }
}

class AddressForm extends CheckoutComponent
{
    private array $address = [];
    private bool  $valid   = false;

    public function __construct()
    {
        parent::__construct('address-form', false); // disabled until cart has items
    }

    public function fill(string $street, string $city, string $zip, string $country): void
    {
        if (!$this->enabled) {
            echo "[AddressForm] Form is disabled. Add items to cart first.\n";
            return;
        }

        $this->address = compact('street', 'city', 'zip', 'country');
        $this->valid   = !empty($street) && !empty($city) && strlen($zip) >= 4;

        echo "[AddressForm] Address filled: {$street}, {$city} {$zip}, {$country}\n";

        if ($this->valid) {
            $this->emit('address_valid', $this->address);
        } else {
            $this->emit('address_invalid', []);
        }
    }

    public function getAddress(): array { return $this->address; }
    public function isValid(): bool     { return $this->valid; }

    public function handleUpdate(string $event, array $data = []): void
    {
        if ($event === 'enable_address' && !$this->enabled) {
            $this->enable();
            echo "  [AddressForm] Enabled — cart has items.\n";
        } elseif ($event === 'disable_address') {
            $this->disable();
            $this->valid = false;
            echo "  [AddressForm] Disabled — cart is empty.\n";
        }
    }

    public function render(): string
    {
        $state = $this->enabled ? ($this->valid ? 'valid' : 'empty') : 'disabled';
        return "<AddressForm state=\"{$state}\" />";
    }
}

class PaymentForm extends CheckoutComponent
{
    private string $method      = '';
    private bool   $valid       = false;
    private string $cardLast4   = '';

    public function __construct()
    {
        parent::__construct('payment-form', false);
    }

    public function setCard(string $cardNumber, string $expiry, string $cvv): void
    {
        if (!$this->enabled) {
            echo "[PaymentForm] Please fill in your address first.\n";
            return;
        }

        // Simulate validation
        $this->valid    = strlen($cardNumber) === 16 && !empty($expiry) && strlen($cvv) === 3;
        $this->method   = 'credit_card';
        $this->cardLast4 = substr($cardNumber, -4);

        echo "[PaymentForm] Card ending in {$this->cardLast4} entered.\n";

        if ($this->valid) {
            $this->emit('payment_valid', [
                'method'   => $this->method,
                'last4'    => $this->cardLast4,
            ]);
        } else {
            echo "[PaymentForm] Invalid card details.\n";
        }
    }

    public function handleUpdate(string $event, array $data = []): void
    {
        if ($event === 'enable_payment') {
            $this->enable();
            echo "  [PaymentForm] Enabled — address confirmed.\n";
        } elseif ($event === 'disable_payment') {
            $this->disable();
            $this->valid = false;
            echo "  [PaymentForm] Disabled — address not complete.\n";
        }
    }

    public function render(): string
    {
        $state = $this->enabled ? ($this->valid ? "card-****{$this->cardLast4}" : 'empty') : 'disabled';
        return "<PaymentForm state=\"{$state}\" />";
    }
}

class OrderSummary extends CheckoutComponent
{
    private array $summaryData = [];

    public function __construct()
    {
        parent::__construct('order-summary', false);
    }

    public function handleUpdate(string $event, array $data = []): void
    {
        if ($event === 'show_summary') {
            $this->summaryData = $data;
            $this->enable();
            echo "  [OrderSummary] Summary updated — ready for review.\n";
            echo "    Items: {$data['item_count']}, Total: \${$data['total']}, ";
            echo "Payment: **** {$data['last4']}\n";
        } elseif ($event === 'hide_summary') {
            $this->disable();
            $this->summaryData = [];
        }
    }

    public function render(): string
    {
        if (!$this->enabled || empty($this->summaryData)) {
            return "<OrderSummary state=\"hidden\" />";
        }
        return "<OrderSummary total=\"\${$this->summaryData['total']}\" />";
    }
}

class SubmitButton extends CheckoutComponent
{
    private bool $submitted = false;

    public function __construct()
    {
        parent::__construct('submit-button', false);
    }

    public function click(): void
    {
        if (!$this->enabled) {
            echo "[SubmitButton] Cannot submit — checkout not complete.\n";
            return;
        }
        $this->submitted = true;
        $this->disable();
        echo "[SubmitButton] Order submitted!\n";
        $this->emit('order_submitted', ['timestamp' => date('Y-m-d H:i:s')]);
    }

    public function handleUpdate(string $event, array $data = []): void
    {
        if ($event === 'enable_submit') {
            $this->enable();
            echo "  [SubmitButton] Enabled — ready to submit.\n";
        } elseif ($event === 'disable_submit') {
            $this->disable();
        }
    }

    public function render(): string
    {
        return "<SubmitButton enabled=\"" . ($this->enabled ? 'true' : 'false') . "\" />";
    }
}

// ---------------------------------------------------------------------------
// Concrete Mediator
// ---------------------------------------------------------------------------

class CheckoutMediator implements CheckoutMediatorInterface
{
    /** @var array<string, CheckoutComponent> */
    private array $components = [];
    private float $cartTotal  = 0.0;
    private array $address    = [];
    private array $payment    = [];

    public function register(CheckoutComponent $component): void
    {
        $this->components[$component->getId()] = $component;
        $component->setMediator($this);
        echo "[CheckoutMediator] Registered: {$component->getId()}\n";
    }

    public function notify(CheckoutComponent $sender, string $event, array $data = []): void
    {
        echo "[CheckoutMediator] Event '{$event}' from '{$sender->getId()}'\n";

        switch ($event) {
            case 'cart_updated':
                $this->cartTotal = $data['total'];
                if ($data['count'] > 0) {
                    $this->get('address-form')?->handleUpdate('enable_address');
                } else {
                    $this->get('address-form')?->handleUpdate('disable_address');
                    $this->get('payment-form')?->handleUpdate('disable_payment');
                    $this->get('order-summary')?->handleUpdate('hide_summary');
                    $this->get('submit-button')?->handleUpdate('disable_submit');
                }
                break;

            case 'address_valid':
                $this->address = $data;
                $this->get('payment-form')?->handleUpdate('enable_payment');
                break;

            case 'address_invalid':
                $this->address = [];
                $this->get('payment-form')?->handleUpdate('disable_payment');
                $this->get('submit-button')?->handleUpdate('disable_submit');
                break;

            case 'payment_valid':
                $this->payment = $data;
                $this->get('order-summary')?->handleUpdate('show_summary', [
                    'item_count' => count($this->get('cart') instanceof Cart
                        ? $this->get('cart')->getItems()
                        : []),
                    'total'      => $this->cartTotal,
                    'address'    => $this->address,
                    'last4'      => $data['last4'],
                ]);
                $this->get('submit-button')?->handleUpdate('enable_submit');
                break;

            case 'order_submitted':
                echo "[CheckoutMediator] Order placed at {$data['timestamp']}. Processing...\n";
                break;
        }
    }

    private function get(string $id): ?CheckoutComponent
    {
        return $this->components[$id] ?? null;
    }

    public function renderAll(): void
    {
        echo "\n--- Checkout State ---\n";
        foreach ($this->components as $component) {
            echo $component->render() . "\n";
        }
    }
}

// ---------------------------------------------------------------------------
// Client Code
// ---------------------------------------------------------------------------

echo str_repeat('=', 55) . "\n";
echo "E-commerce Checkout — Mediator Pattern Demo\n";
echo str_repeat('=', 55) . "\n\n";

$mediator = new CheckoutMediator();

$cart          = new Cart();
$addressForm   = new AddressForm();
$paymentForm   = new PaymentForm();
$orderSummary  = new OrderSummary();
$submitButton  = new SubmitButton();

$mediator->register($cart);
$mediator->register($addressForm);
$mediator->register($paymentForm);
$mediator->register($orderSummary);
$mediator->register($submitButton);

echo "\n--- Step 1: Try to submit (should fail) ---\n";
$submitButton->click();

echo "\n--- Step 2: Add items to cart ---\n";
$cart->addItem('TypeScript Handbook', 29.99, 1);
$cart->addItem('PHP 8 Course',        49.99, 2);

echo "\n--- Step 3: Fill address ---\n";
$addressForm->fill('123 Main St', 'Springfield', '12345', 'US');

echo "\n--- Step 4: Enter payment details ---\n";
$paymentForm->setCard('4111111111111234', '12/27', '123');

echo "\n--- Step 5: Submit order ---\n";
$submitButton->click();

$mediator->renderAll();
```

---

### Ruby

```ruby
# Real-world example: Stock Trading Platform.
#
# Components: MarketDataFeed, RiskEngine, OrderBook, PortfolioTracker, AlertSystem.
# The TradingMediator coordinates: when market data changes, risk is re-evaluated,
# orders may be auto-triggered, and alerts are fired — without direct coupling.

# ---------------------------------------------------------------------------
# Mediator Interface (module mixin)
# ---------------------------------------------------------------------------

module TradingMediatorInterface
  def notify(sender, event, data = {})
    raise NotImplementedError, "#{self.class}#notify must be implemented"
  end

  def register_component(component)
    raise NotImplementedError, "#{self.class}#register_component must be implemented"
  end
end

# ---------------------------------------------------------------------------
# Component Base
# ---------------------------------------------------------------------------

class TradingComponent
  attr_reader :name

  def initialize(name)
    @name     = name
    @mediator = nil
  end

  def set_mediator(mediator)
    @mediator = mediator
  end

  def handle_event(event, data = {})
    raise NotImplementedError, "#{self.class}#handle_event must be implemented"
  end

  protected

  def emit(event, data = {})
    @mediator&.notify(self, event, data)
  end
end

# ---------------------------------------------------------------------------
# Concrete Components
# ---------------------------------------------------------------------------

class MarketDataFeed < TradingComponent
  attr_reader :prices

  def initialize
    super("MarketDataFeed")
    @prices = { "AAPL" => 175.00, "GOOGL" => 140.00, "MSFT" => 380.00 }
  end

  # Simulate a price tick from the exchange
  def price_update(symbol, new_price)
    old_price        = @prices[symbol] || 0.0
    @prices[symbol]  = new_price
    change_pct       = old_price > 0 ? ((new_price - old_price) / old_price * 100).round(2) : 0.0

    puts "[#{@name}] #{symbol}: $#{old_price} -> $#{new_price} (#{change_pct > 0 ? '+' : ''}#{change_pct}%)"

    emit("price_updated", {
      symbol:     symbol,
      price:      new_price,
      old_price:  old_price,
      change_pct: change_pct
    })
  end

  def handle_event(event, data = {})
    # MarketDataFeed does not react to other components in this scenario
  end
end

class RiskEngine < TradingComponent
  RISK_THRESHOLDS = {
    max_position_value: 50_000.0,
    max_daily_loss:     -5_000.0,
    volatility_limit:   5.0  # percent
  }.freeze

  def initialize
    super("RiskEngine")
    @daily_pnl = 0.0
  end

  def evaluate_order(symbol, quantity, price, direction)
    position_value = quantity * price
    risk_ok        = true
    reasons        = []

    if position_value > RISK_THRESHOLDS[:max_position_value]
      risk_ok = false
      reasons << "Position value $#{position_value} exceeds max $#{RISK_THRESHOLDS[:max_position_value]}"
    end

    if @daily_pnl < RISK_THRESHOLDS[:max_daily_loss]
      risk_ok = false
      reasons << "Daily loss limit reached: $#{@daily_pnl}"
    end

    puts "[#{@name}] Risk check for #{direction} #{quantity} #{symbol} @ $#{price}: " \
         "#{risk_ok ? 'APPROVED' : 'REJECTED'}"
    reasons.each { |r| puts "  [#{@name}] Reason: #{r}" }

    emit("risk_evaluated", {
      symbol:    symbol,
      approved:  risk_ok,
      quantity:  quantity,
      price:     price,
      direction: direction
    })
  end

  def handle_event(event, data = {})
    case event
    when "price_updated"
      # Alert on extreme volatility
      if data[:change_pct].abs >= RISK_THRESHOLDS[:volatility_limit]
        puts "  [#{@name}] HIGH VOLATILITY detected for #{data[:symbol]}: #{data[:change_pct]}%"
        emit("risk_alert", {
          symbol:  data[:symbol],
          reason:  "Volatility spike: #{data[:change_pct]}%",
          level:   :high
        })
      end

    when "trade_executed"
      # Update P&L tracking
      pnl_change = data[:direction] == "BUY" ? -data[:value] : data[:value]
      @daily_pnl += pnl_change
      puts "  [#{@name}] Daily P&L updated: $#{@daily_pnl.round(2)}"
    end
  end
end

class OrderBook < TradingComponent
  def initialize
    super("OrderBook")
    @orders          = {}
    @order_sequence  = 0
  end

  def place_order(symbol, quantity, price, direction)
    @order_sequence += 1
    order_id = "ORD-#{@order_sequence.to_s.rjust(4, '0')}"
    puts "[#{@name}] Placing #{direction} order #{order_id}: #{quantity} #{symbol} @ $#{price}"

    # Ask risk engine to evaluate first
    emit("order_requested", {
      order_id:  order_id,
      symbol:    symbol,
      quantity:  quantity,
      price:     price,
      direction: direction
    })
  end

  def handle_event(event, data = {})
    case event
    when "risk_evaluated"
      if data[:approved]
        order_id = "ORD-EXEC-#{rand(1000)}"
        value    = data[:quantity] * data[:price]
        puts "  [#{@name}] Executing order: #{data[:direction]} #{data[:quantity]} #{data[:symbol]}" \
             " @ $#{data[:price]} (total: $#{value})"
        emit("trade_executed", {
          symbol:    data[:symbol],
          quantity:  data[:quantity],
          price:     data[:price],
          direction: data[:direction],
          value:     value
        })
      else
        puts "  [#{@name}] Order rejected by risk engine."
      end
    end
  end
end

class PortfolioTracker < TradingComponent
  def initialize
    super("PortfolioTracker")
    @holdings = Hash.new(0)  # symbol -> shares
    @cash     = 100_000.0
  end

  def handle_event(event, data = {})
    case event
    when "trade_executed"
      symbol    = data[:symbol]
      quantity  = data[:quantity]
      value     = data[:value]

      if data[:direction] == "BUY"
        @holdings[symbol] += quantity
        @cash             -= value
        puts "  [#{@name}] Bought #{quantity} #{symbol}. Holdings: #{@holdings[symbol]} shares. Cash: $#{@cash.round(2)}"
      else
        @holdings[symbol] = [@holdings[symbol] - quantity, 0].max
        @cash             += value
        puts "  [#{@name}] Sold #{quantity} #{symbol}. Holdings: #{@holdings[symbol]} shares. Cash: $#{@cash.round(2)}"
      end

    when "price_updated"
      symbol = data[:symbol]
      if @holdings[symbol] > 0
        value = @holdings[symbol] * data[:price]
        puts "  [#{@name}] #{symbol} position now worth: $#{value.round(2)}"
      end
    end
  end
end

class AlertSystem < TradingComponent
  def initialize
    super("AlertSystem")
    @alert_count = 0
  end

  def handle_event(event, data = {})
    case event
    when "risk_alert"
      @alert_count += 1
      puts "  [#{@name}] ALERT ##{@alert_count} [#{data[:level].upcase}]: #{data[:symbol]} — #{data[:reason]}"

    when "trade_executed"
      puts "  [#{@name}] NOTIFICATION: Trade executed — #{data[:direction]} #{data[:quantity]}" \
           " #{data[:symbol]} @ $#{data[:price]}"

    when "price_updated"
      # Only alert on significant moves
      if data[:change_pct].abs >= 3.0
        puts "  [#{@name}] PRICE ALERT: #{data[:symbol]} moved #{data[:change_pct]}%"
      end
    end
  end
end

# ---------------------------------------------------------------------------
# Concrete Mediator
# ---------------------------------------------------------------------------

class TradingMediator
  include TradingMediatorInterface

  def initialize
    @components  = {}
    @event_log   = []
    @risk_engine = nil
    @order_book  = nil
  end

  def register_component(component)
    @components[component.name] = component
    component.set_mediator(self)

    # Keep typed references for routing
    @risk_engine = component if component.is_a?(RiskEngine)
    @order_book  = component if component.is_a?(OrderBook)

    puts "[TradingMediator] Registered: #{component.name}"
  end

  def notify(sender, event, data = {})
    @event_log << { time: Time.now.strftime("%H:%M:%S"), sender: sender.name, event: event }
    puts "[TradingMediator] '#{event}' from '#{sender.name}'"

    case event
    when "price_updated"
      # Route to: RiskEngine, PortfolioTracker, AlertSystem
      route_to(%w[RiskEngine PortfolioTracker AlertSystem], event, data, except: sender.name)

    when "order_requested"
      # Route to RiskEngine for evaluation
      @risk_engine&.evaluate_order(
        data[:symbol], data[:quantity], data[:price], data[:direction]
      )

    when "risk_evaluated"
      # Route result to OrderBook to execute or cancel
      route_to(%w[OrderBook], event, data, except: sender.name)

    when "risk_alert"
      route_to(%w[AlertSystem], event, data, except: sender.name)

    when "trade_executed"
      route_to(%w[PortfolioTracker RiskEngine AlertSystem], event, data, except: sender.name)
    end
  end

  def print_event_log
    puts "\n[TradingMediator] === Event Log (#{@event_log.size} events) ==="
    @event_log.each do |entry|
      puts "  [#{entry[:time]}] #{entry[:sender]} -> #{entry[:event]}"
    end
  end

  private

  def route_to(names, event, data, except: nil)
    names.each do |name|
      next if name == except
      @components[name]&.handle_event(event, data)
    end
  end
end

# ---------------------------------------------------------------------------
# Client Code
# ---------------------------------------------------------------------------

puts "=" * 55
puts "Stock Trading Platform — Mediator Pattern Demo"
puts "=" * 55

mediator = TradingMediator.new

market_feed = MarketDataFeed.new
risk_engine = RiskEngine.new
order_book  = OrderBook.new
portfolio   = PortfolioTracker.new
alerts      = AlertSystem.new

[market_feed, risk_engine, order_book, portfolio, alerts].each do |c|
  mediator.register_component(c)
end

puts "\n--- Market Data Updates ---"
market_feed.price_update("AAPL",  182.50)   # Small move — no alert
market_feed.price_update("GOOGL", 131.00)   # 6.4% drop — volatility alert!

puts "\n--- Order Placement ---"
order_book.place_order("AAPL",  100, 182.50, "BUY")   # Should be approved
order_book.place_order("AAPL", 1000, 182.50, "BUY")   # Should be rejected (too large)

puts "\n--- Another Price Tick ---"
market_feed.price_update("MSFT", 395.00)   # Small move

mediator.print_event_log
```

---

## When To Use

Use the Mediator pattern when:

- **Tight coupling is making classes hard to change.** When modifying one class forces you to examine or modify a dozen others, it's time to introduce a mediator to centralize that communication.

- **A component cannot be reused elsewhere.** If a component carries so many dependencies on other components that it can't be dropped into a new project, extract those dependencies into a mediator.

- **You're creating excessive subclasses.** When you find yourself subclassing components just to handle slightly different interaction behaviors, a mediator can absorb that variation.

- **You have a form, dialog, or wizard with interdependent controls.** UI workflows are a canonical use case: checkboxes that enable text fields, selections that hide panels, buttons that become active only when all validation passes.

- **You are building a publish-subscribe or event-bus system.** Any time multiple independent components need to react to each other's state changes without being explicitly connected.

- **You have microservices or agents that coordinate through a central hub.** API gateways, workflow engines, orchestrators, and message brokers all embody the Mediator pattern at the architectural level.

---

## Pros & Cons

### Pros

| # | Benefit | Explanation |
|---|---|---|
| 1 | **Single Responsibility Principle** | Communication logic is extracted into a single mediator class, leaving components focused on their own concerns. |
| 2 | **Open/Closed Principle** | You can introduce new mediators without touching existing components. |
| 3 | **Reduced coupling** | Components only know the mediator interface; they know nothing about each other. |
| 4 | **Easier reuse** | Components can be reused in entirely different contexts just by linking them to a different mediator. |
| 5 | **Simplified testing** | Components can be tested in isolation with a mock mediator. |
| 6 | **Centralized control flow** | All interaction logic lives in one place, making system behavior easier to understand and trace. |

### Cons

| # | Drawback | Explanation |
|---|---|---|
| 1 | **God Object risk** | Over time, as more interactions are added, the mediator can absorb too much logic and become a bloated, hard-to-maintain class — a "God Object" that knows and does everything. |
| 2 | **Single point of failure** | All communication flows through the mediator; if it has a bug, the entire system is affected. |
| 3 | **Indirection overhead** | Tracing a specific behavior requires looking at the mediator rather than following a direct call chain, which can make debugging less intuitive. |

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Chain of Responsibility** | Both pass requests along a sequence of handlers. CoR passes a request linearly until one handler processes it; Mediator routes events from a single sender to multiple receivers based on business rules. |
| **Command** | Commands encapsulate a request as an object. A mediator can receive Command objects instead of raw events, giving even more decoupling and the ability to queue, log, or undo operations. |
| **Facade** | Both simplify an interface to a subsystem. Facade provides a simplified read-only view; Mediator actively manages bidirectional communication between components and may be known to them. |
| **Observer** | Mediator is often implemented using Observer: components subscribe to mediator events, and the mediator publishes notifications. The key difference is intent — Observer decouples a publisher from many subscribers; Mediator decouples components from each other through a central coordinator. |

---

## Sources

- https://refactoring.guru/design-patterns/mediator
- https://sourcemaking.com/design_patterns/mediator
