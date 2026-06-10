# Abstract Factory Pattern

**Category:** Creational  
**Also Known As:** Kit

---

## Intent

Provide an interface for creating **families of related or dependent objects** without specifying their concrete classes. The Abstract Factory defines a contract for producing a set of products; concrete factories fulfil that contract for a particular product family, guaranteeing that all products created by one factory are designed to work together.

---

## Problem It Solves

Imagine you are building a cross-platform UI toolkit that must run on Windows, macOS, and Linux. Each platform has its own native widgets: buttons, checkboxes, text fields, scroll bars. If you instantiate concrete widget classes directly throughout your application (e.g. `new WindowsButton()`), you lock the code to one platform. Switching platforms requires hunting every instantiation site and replacing it — a fragile, error-prone process.

The same problem surfaces whenever code must work with **families of related products** whose exact types may vary:

- Rendering engines (OpenGL vs. Vulkan vs. DirectX families of shaders, buffers, and pipelines)
- Database access layers (MySQL vs. PostgreSQL vs. SQLite families of connections, queries, and result sets)
- UI theming systems (Light theme vs. Dark theme vs. High-Contrast theme families of colours, fonts, and icons)
- Cloud provider SDKs (AWS vs. Azure vs. GCP families of storage, queues, and compute clients)

The core problems are:

1. **Compatibility** — products within a family must be used together; mixing products across families can cause subtle bugs or crashes.
2. **Coupling** — client code should not depend on platform-specific or vendor-specific concrete classes.
3. **Extensibility** — adding a new product family should not require modifying existing client code.

---

## Solution

Declare **abstract product interfaces** for each kind of product in the family (e.g. `Button`, `Checkbox`). Declare an **Abstract Factory interface** that lists a creation method for each product type. Implement one **Concrete Factory** per product family; each concrete factory creates only products that belong to its family. Client code works exclusively through the abstract interfaces — it never knows which concrete classes are being used.

**Key principle:** A single concrete factory object is injected into (or chosen by) the client once; from then on, every product the client creates comes from that same family automatically.

---

## Structure (ASCII diagram)

```
         ┌───────────────────────────────────────────────────────────┐
         │                    «interface»                             │
         │                  AbstractFactory                           │
         │  ─────────────────────────────────────────────────────    │
         │  + createProductA(): AbstractProductA                      │
         │  + createProductB(): AbstractProductB                      │
         └───────────────────────────────┬───────────────────────────┘
                        ┌───────────────┴───────────────┐
                        │                               │
           ┌────────────▼────────────┐     ┌────────────▼────────────┐
           │    ConcreteFactory1     │     │    ConcreteFactory2     │
           │  ───────────────────── │     │  ───────────────────── │
           │  + createProductA()    │     │  + createProductA()    │
           │    → ProductA1         │     │    → ProductA2         │
           │  + createProductB()    │     │  + createProductB()    │
           │    → ProductB1         │     │    → ProductB2         │
           └────────────┬───────────┘     └────────────┬───────────┘
                        │                               │
          ┌─────────────┤                               ├─────────────┐
          │             │                               │             │
  ┌───────▼──────┐ ┌────▼──────────┐       ┌───────────▼──┐ ┌────────▼─────┐
  │  ProductA1   │ │  ProductB1    │       │  ProductA2   │ │  ProductB2   │
  └──────────────┘ └───────────────┘       └──────────────┘ └──────────────┘
          ▲                 ▲                      ▲                  ▲
          │                 │                      │                  │
  ┌───────┴──────┐ ┌────────┴──────┐       ┌──────┴───────┐ ┌────────┴─────┐
  │ «interface»  │ │ «interface»   │       │ «interface»  │ │ «interface»  │
  │AbstractProdA │ │AbstractProdB  │       │AbstractProdA │ │AbstractProdB │
  └──────────────┘ └───────────────┘       └──────────────┘ └──────────────┘

  ┌────────────────────────────────────────────────────────┐
  │                      Client                            │
  │  ─────────────────────────────────────────────────     │
  │  - factory: AbstractFactory                            │
  │  + Client(factory: AbstractFactory)                    │
  │  + doSomething()                                       │
  └────────────────────────────────────────────────────────┘
```

---

## Participants

| Participant | Role |
|---|---|
| **AbstractFactory** | Declares the interface with creation methods for each abstract product type. |
| **ConcreteFactory** | Implements the creation methods; each factory corresponds to one product family (variant). |
| **AbstractProduct** | Declares the interface for a type of product object. |
| **ConcreteProduct** | Implements the abstract product interface; belongs to exactly one product family. |
| **Client** | Uses only the abstract interfaces. Receives a concrete factory through dependency injection; never instantiates concrete products directly. |

---

## How It Works (step-by-step)

1. **Define abstract products.** For each distinct kind of object in your product family, write an interface (or abstract class) that captures its behaviour — e.g. `Button` with `render()` and `onClick()`.

2. **Define the Abstract Factory.** Write an interface that declares one factory method per product type — e.g. `createButton(): Button`, `createCheckbox(): Checkbox`.

3. **Implement Concrete Factories.** Write one class per product family that implements the Abstract Factory. Each method returns a concrete product from the same family — e.g. `WindowsFactory.createButton()` returns a `WindowsButton`.

4. **Implement Concrete Products.** Write concrete product classes for each combination of family × product type, implementing the abstract product interface.

5. **Configure the client.** At startup (or via a config file / environment variable), determine which concrete factory to instantiate. Inject it into the client.

6. **Client creates and uses products.** The client calls factory methods to create products and uses them through their abstract interfaces. It is completely unaware of the concrete types.

7. **Switching families.** To switch from Windows widgets to macOS widgets, swap `WindowsFactory` for `MacFactory` at the injection point — no other code changes.

---

## Code Examples

### Python

```python
"""
Abstract Factory — cross-platform UI widget system.

Demonstrates creating families of UI widgets (Button, Checkbox)
for different operating systems (Windows, macOS) without coupling
application code to concrete widget classes.

Run:
    python abstract_factory.py
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import platform as _platform


# ---------------------------------------------------------------------------
# Abstract Products
# ---------------------------------------------------------------------------

class Button(ABC):
    """Abstract product: a clickable button widget."""

    @abstractmethod
    def render(self) -> str:
        """Return a string representation of the rendered widget."""

    @abstractmethod
    def on_click(self, handler: str) -> str:
        """Bind a click handler and return confirmation."""


class Checkbox(ABC):
    """Abstract product: a toggleable checkbox widget."""

    @abstractmethod
    def render(self) -> str:
        """Return a string representation of the rendered widget."""

    @abstractmethod
    def toggle(self) -> str:
        """Toggle the checkbox state and return new state description."""


# ---------------------------------------------------------------------------
# Concrete Products — Windows family
# ---------------------------------------------------------------------------

class WindowsButton(Button):
    def render(self) -> str:
        return "[Windows Button]  ▓▓▓▓▓▓▓▓▓▓▓▓"

    def on_click(self, handler: str) -> str:
        return f"WinAPI: Registered WM_LBUTTONUP → {handler}"


class WindowsCheckbox(Checkbox):
    def __init__(self) -> None:
        self._checked = False

    def render(self) -> str:
        mark = "■" if self._checked else "□"
        return f"[Windows Checkbox] {mark}"

    def toggle(self) -> str:
        self._checked = not self._checked
        state = "checked" if self._checked else "unchecked"
        return f"WinAPI: BST_{state.upper()}"


# ---------------------------------------------------------------------------
# Concrete Products — macOS family
# ---------------------------------------------------------------------------

class MacButton(Button):
    def render(self) -> str:
        return "( macOS Button ●━━━━━━━━━━━━ )"

    def on_click(self, handler: str) -> str:
        return f"AppKit: addTarget:action: → {handler}"


class MacCheckbox(Checkbox):
    def __init__(self) -> None:
        self._checked = False

    def render(self) -> str:
        mark = "◉" if self._checked else "○"
        return f"(macOS Checkbox) {mark}"

    def toggle(self) -> str:
        self._checked = not self._checked
        state = "on" if self._checked else "off"
        return f"AppKit: NSControlStateValue.{state}"


# ---------------------------------------------------------------------------
# Abstract Factory
# ---------------------------------------------------------------------------

class GUIFactory(ABC):
    """Abstract factory: produces families of GUI widgets."""

    @abstractmethod
    def create_button(self) -> Button:
        ...

    @abstractmethod
    def create_checkbox(self) -> Checkbox:
        ...


# ---------------------------------------------------------------------------
# Concrete Factories
# ---------------------------------------------------------------------------

class WindowsFactory(GUIFactory):
    """Creates the Windows family of widgets."""

    def create_button(self) -> Button:
        return WindowsButton()

    def create_checkbox(self) -> Checkbox:
        return WindowsCheckbox()


class MacFactory(GUIFactory):
    """Creates the macOS family of widgets."""

    def create_button(self) -> Button:
        return MacButton()

    def create_checkbox(self) -> Checkbox:
        return MacCheckbox()


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class Application:
    """
    The client. Works exclusively through abstract interfaces.
    It never references concrete widget classes.
    """

    def __init__(self, factory: GUIFactory) -> None:
        self._factory = factory
        # Create the widget family once; all products are compatible.
        self._button: Button = factory.create_button()
        self._checkbox: Checkbox = factory.create_checkbox()

    def render_ui(self) -> None:
        print("Rendering UI:")
        print(" ", self._button.render())
        print(" ", self._checkbox.render())

    def simulate_interaction(self) -> None:
        print("\nSimulating user interaction:")
        print(" ", self._button.on_click("submit_form"))
        print(" ", self._checkbox.toggle())
        print(" ", self._checkbox.render())


# ---------------------------------------------------------------------------
# Factory selector — runs once at startup
# ---------------------------------------------------------------------------

def get_factory() -> GUIFactory:
    """
    In a real application this might read a config file,
    environment variable, or call platform.system().
    """
    os_name = _platform.system()
    if os_name == "Windows":
        return WindowsFactory()
    elif os_name == "Darwin":
        return MacFactory()
    else:
        # Fallback — demonstrate Windows factory on other platforms too
        print(f"[Info] Unrecognised OS '{os_name}'; defaulting to Windows widgets.\n")
        return WindowsFactory()


if __name__ == "__main__":
    # --- Windows demo ---
    print("=== Windows Factory ===")
    app_win = Application(WindowsFactory())
    app_win.render_ui()
    app_win.simulate_interaction()

    print()

    # --- macOS demo ---
    print("=== macOS Factory ===")
    app_mac = Application(MacFactory())
    app_mac.render_ui()
    app_mac.simulate_interaction()
```

---

### Java

```java
/**
 * Abstract Factory — database access layer.
 *
 * Models a database toolkit where MySQL and PostgreSQL each have their own
 * Connection, Command, and ResultSet implementations.  Client code (the
 * Repository) works only through abstract interfaces.
 *
 * Compile & run:
 *   javac AbstractFactoryDemo.java && java AbstractFactoryDemo
 */

// ── Abstract Products ────────────────────────────────────────────────────────

interface DbConnection {
    void open();
    void close();
    boolean isOpen();
}

interface DbCommand {
    DbResultSet execute(String sql);
    int executeUpdate(String sql);
}

interface DbResultSet {
    boolean next();
    String getString(String column);
    int getInt(String column);
    void close();
}

// ── Concrete Products — MySQL family ────────────────────────────────────────

class MySqlConnection implements DbConnection {
    private boolean open = false;

    @Override public void open() {
        System.out.println("[MySQL] Opening connection to 127.0.0.1:3306");
        open = true;
    }

    @Override public void close() {
        System.out.println("[MySQL] Closing connection");
        open = false;
    }

    @Override public boolean isOpen() { return open; }
}

class MySqlResultSet implements DbResultSet {
    private final String[][] data = {
        {"1", "Alice", "30"},
        {"2", "Bob",   "25"},
    };
    private int cursor = -1;

    @Override public boolean next() { return ++cursor < data.length; }

    @Override public String getString(String column) {
        return switch (column) {
            case "id"   -> data[cursor][0];
            case "name" -> data[cursor][1];
            case "age"  -> data[cursor][2];
            default     -> throw new IllegalArgumentException("Unknown column: " + column);
        };
    }

    @Override public int getInt(String column) {
        return Integer.parseInt(getString(column));
    }

    @Override public void close() {
        System.out.println("[MySQL] ResultSet closed");
    }
}

class MySqlCommand implements DbCommand {
    @Override public DbResultSet execute(String sql) {
        System.out.println("[MySQL] Executing query: " + sql);
        return new MySqlResultSet();
    }

    @Override public int executeUpdate(String sql) {
        System.out.println("[MySQL] Executing update: " + sql);
        return 1; // rows affected
    }
}

// ── Concrete Products — PostgreSQL family ───────────────────────────────────

class PostgreSqlConnection implements DbConnection {
    private boolean open = false;

    @Override public void open() {
        System.out.println("[PostgreSQL] Opening connection to 127.0.0.1:5432");
        open = true;
    }

    @Override public void close() {
        System.out.println("[PostgreSQL] Closing connection");
        open = false;
    }

    @Override public boolean isOpen() { return open; }
}

class PostgreSqlResultSet implements DbResultSet {
    private final String[][] data = {
        {"10", "Carol", "28"},
        {"11", "Dave",  "35"},
        {"12", "Eve",   "22"},
    };
    private int cursor = -1;

    @Override public boolean next() { return ++cursor < data.length; }

    @Override public String getString(String column) {
        return switch (column) {
            case "id"   -> data[cursor][0];
            case "name" -> data[cursor][1];
            case "age"  -> data[cursor][2];
            default     -> throw new IllegalArgumentException("Unknown column: " + column);
        };
    }

    @Override public int getInt(String column) {
        return Integer.parseInt(getString(column));
    }

    @Override public void close() {
        System.out.println("[PostgreSQL] ResultSet closed");
    }
}

class PostgreSqlCommand implements DbCommand {
    @Override public DbResultSet execute(String sql) {
        System.out.println("[PostgreSQL] Executing query: " + sql);
        return new PostgreSqlResultSet();
    }

    @Override public int executeUpdate(String sql) {
        System.out.println("[PostgreSQL] Executing update: " + sql);
        return 1;
    }
}

// ── Abstract Factory ─────────────────────────────────────────────────────────

interface DatabaseFactory {
    DbConnection createConnection();
    DbCommand    createCommand();
}

// ── Concrete Factories ───────────────────────────────────────────────────────

class MySqlFactory implements DatabaseFactory {
    @Override public DbConnection createConnection() { return new MySqlConnection(); }
    @Override public DbCommand    createCommand()    { return new MySqlCommand(); }
}

class PostgreSqlFactory implements DatabaseFactory {
    @Override public DbConnection createConnection() { return new PostgreSqlConnection(); }
    @Override public DbCommand    createCommand()    { return new PostgreSqlCommand(); }
}

// ── Client ───────────────────────────────────────────────────────────────────

class UserRepository {
    private final DbConnection connection;
    private final DbCommand    command;

    /** Inject the factory; the repository never knows which DB vendor is used. */
    public UserRepository(DatabaseFactory factory) {
        this.connection = factory.createConnection();
        this.command    = factory.createCommand();
    }

    public void findAll() {
        connection.open();
        DbResultSet rs = command.execute("SELECT id, name, age FROM users");
        System.out.println("  id | name  | age");
        System.out.println("  ---|-------|----");
        while (rs.next()) {
            System.out.printf("  %-2s | %-5s | %s%n",
                rs.getString("id"),
                rs.getString("name"),
                rs.getString("age"));
        }
        rs.close();
        connection.close();
    }

    public void insertUser(String name, int age) {
        connection.open();
        int rows = command.executeUpdate(
            String.format("INSERT INTO users (name, age) VALUES ('%s', %d)", name, age));
        System.out.printf("  %d row(s) inserted.%n", rows);
        connection.close();
    }
}

// ── Entry Point ──────────────────────────────────────────────────────────────

public class AbstractFactoryDemo {
    public static void main(String[] args) {
        System.out.println("=== MySQL Repository ===");
        UserRepository mysqlRepo = new UserRepository(new MySqlFactory());
        mysqlRepo.findAll();
        mysqlRepo.insertUser("Frank", 40);

        System.out.println("\n=== PostgreSQL Repository ===");
        UserRepository pgRepo = new UserRepository(new PostgreSqlFactory());
        pgRepo.findAll();
        pgRepo.insertUser("Grace", 29);
    }
}
```

---

### C++

```cpp
/**
 * Abstract Factory — rendering backend system.
 *
 * Models a 3-D renderer that can use either an OpenGL or a Vulkan backend.
 * Each backend provides its own Buffer, Shader, and RenderPipeline.
 * The Scene (client) works only through abstract interfaces.
 *
 * Compile:
 *   g++ -std=c++17 -o abstract_factory abstract_factory.cpp && ./abstract_factory
 */

#include <iostream>
#include <memory>
#include <string>
#include <vector>

// ── Abstract Products ────────────────────────────────────────────────────────

class Buffer {
public:
    virtual ~Buffer() = default;
    virtual void upload(const std::vector<float>& data) = 0;
    virtual std::string info() const = 0;
};

class Shader {
public:
    virtual ~Shader() = default;
    virtual void compile(const std::string& source) = 0;
    virtual std::string info() const = 0;
};

class RenderPipeline {
public:
    virtual ~RenderPipeline() = default;
    virtual void bind(const Shader& shader, const Buffer& buffer) = 0;
    virtual void drawCall(int vertexCount) = 0;
    virtual std::string info() const = 0;
};

// ── Concrete Products — OpenGL family ────────────────────────────────────────

class OpenGLBuffer : public Buffer {
    std::string state_ = "empty";
public:
    void upload(const std::vector<float>& data) override {
        state_ = "loaded(" + std::to_string(data.size()) + " floats)";
        std::cout << "  [OpenGL] glBufferData → " << state_ << "\n";
    }
    std::string info() const override { return "OpenGLBuffer[" + state_ + "]"; }
};

class OpenGLShader : public Shader {
    std::string name_;
public:
    void compile(const std::string& source) override {
        name_ = source.substr(0, 20) + "...";
        std::cout << "  [OpenGL] glCompileShader: " << name_ << "\n";
    }
    std::string info() const override { return "OpenGLShader[" + name_ + "]"; }
};

class OpenGLPipeline : public RenderPipeline {
public:
    void bind(const Shader& shader, const Buffer& buffer) override {
        std::cout << "  [OpenGL] glUseProgram + glBindBuffer → "
                  << shader.info() << " + " << buffer.info() << "\n";
    }
    void drawCall(int vertexCount) override {
        std::cout << "  [OpenGL] glDrawArrays(GL_TRIANGLES, 0, " << vertexCount << ")\n";
    }
    std::string info() const override { return "OpenGLPipeline"; }
};

// ── Concrete Products — Vulkan family ────────────────────────────────────────

class VulkanBuffer : public Buffer {
    std::string state_ = "empty";
public:
    void upload(const std::vector<float>& data) override {
        state_ = "loaded(" + std::to_string(data.size()) + " floats)";
        std::cout << "  [Vulkan] vkCmdCopyBuffer → " << state_ << "\n";
    }
    std::string info() const override { return "VkBuffer[" + state_ + "]"; }
};

class VulkanShader : public Shader {
    std::string name_;
public:
    void compile(const std::string& source) override {
        name_ = source.substr(0, 20) + "...";
        std::cout << "  [Vulkan] vkCreateShaderModule: " << name_ << "\n";
    }
    std::string info() const override { return "VkShaderModule[" + name_ + "]"; }
};

class VulkanPipeline : public RenderPipeline {
public:
    void bind(const Shader& shader, const Buffer& buffer) override {
        std::cout << "  [Vulkan] vkCmdBindPipeline + vkCmdBindVertexBuffers → "
                  << shader.info() << " + " << buffer.info() << "\n";
    }
    void drawCall(int vertexCount) override {
        std::cout << "  [Vulkan] vkCmdDraw(commandBuffer, " << vertexCount << ", 1, 0, 0)\n";
    }
    std::string info() const override { return "VkPipeline"; }
};

// ── Abstract Factory ─────────────────────────────────────────────────────────

class RenderFactory {
public:
    virtual ~RenderFactory() = default;
    virtual std::unique_ptr<Buffer>         createBuffer()   const = 0;
    virtual std::unique_ptr<Shader>         createShader()   const = 0;
    virtual std::unique_ptr<RenderPipeline> createPipeline() const = 0;
};

// ── Concrete Factories ───────────────────────────────────────────────────────

class OpenGLFactory : public RenderFactory {
public:
    std::unique_ptr<Buffer>         createBuffer()   const override { return std::make_unique<OpenGLBuffer>(); }
    std::unique_ptr<Shader>         createShader()   const override { return std::make_unique<OpenGLShader>(); }
    std::unique_ptr<RenderPipeline> createPipeline() const override { return std::make_unique<OpenGLPipeline>(); }
};

class VulkanFactory : public RenderFactory {
public:
    std::unique_ptr<Buffer>         createBuffer()   const override { return std::make_unique<VulkanBuffer>(); }
    std::unique_ptr<Shader>         createShader()   const override { return std::make_unique<VulkanShader>(); }
    std::unique_ptr<RenderPipeline> createPipeline() const override { return std::make_unique<VulkanPipeline>(); }
};

// ── Client ───────────────────────────────────────────────────────────────────

class Scene {
    std::unique_ptr<Buffer>         buffer_;
    std::unique_ptr<Shader>         shader_;
    std::unique_ptr<RenderPipeline> pipeline_;

public:
    explicit Scene(const RenderFactory& factory)
        : buffer_(factory.createBuffer())
        , shader_(factory.createShader())
        , pipeline_(factory.createPipeline())
    {}

    void load() {
        std::vector<float> vertices = {
            // Triangle (x, y, z)
             0.0f,  0.5f, 0.0f,
            -0.5f, -0.5f, 0.0f,
             0.5f, -0.5f, 0.0f
        };
        buffer_->upload(vertices);
        shader_->compile("void main() { gl_Position = vec4(pos, 1.0); }");
        pipeline_->bind(*shader_, *buffer_);
    }

    void render() {
        pipeline_->drawCall(3);
    }
};

// ── Entry Point ──────────────────────────────────────────────────────────────

int main() {
    std::cout << "=== OpenGL Backend ===\n";
    {
        OpenGLFactory glFactory;
        Scene scene(glFactory);
        scene.load();
        scene.render();
    }

    std::cout << "\n=== Vulkan Backend ===\n";
    {
        VulkanFactory vkFactory;
        Scene scene(vkFactory);
        scene.load();
        scene.render();
    }

    return 0;
}
```

---

### C#

```csharp
/**
 * Abstract Factory — cloud storage provider abstraction.
 *
 * The application manages files and queues without coupling to a specific
 * cloud vendor. Swap between AWS and Azure by changing one line at startup.
 *
 * Run:
 *   dotnet script AbstractFactory.csx   (or paste into a .NET 6+ project)
 */

using System;
using System.Collections.Generic;

// ── Abstract Products ────────────────────────────────────────────────────────

public interface IBlobStorage
{
    void Upload(string blobName, string content);
    string Download(string blobName);
    IEnumerable<string> ListBlobs(string prefix);
}

public interface IMessageQueue
{
    void SendMessage(string body);
    string? ReceiveMessage();
    void DeleteMessage(string messageId);
}

public interface IKeyValueStore
{
    void Set(string key, string value, TimeSpan? ttl = null);
    string? Get(string key);
    void Delete(string key);
}

// ── Concrete Products — AWS family ──────────────────────────────────────────

public class S3Storage : IBlobStorage
{
    private readonly Dictionary<string, string> _store = new();

    public void Upload(string blobName, string content)
    {
        _store[blobName] = content;
        Console.WriteLine($"[S3] PutObject s3://my-bucket/{blobName}");
    }

    public string Download(string blobName)
    {
        Console.WriteLine($"[S3] GetObject s3://my-bucket/{blobName}");
        return _store.TryGetValue(blobName, out var v) ? v : throw new KeyNotFoundException(blobName);
    }

    public IEnumerable<string> ListBlobs(string prefix)
    {
        Console.WriteLine($"[S3] ListObjectsV2 prefix={prefix}");
        foreach (var key in _store.Keys)
            if (key.StartsWith(prefix)) yield return key;
    }
}

public class SqsQueue : IMessageQueue
{
    private readonly Queue<(string id, string body)> _queue = new();
    private int _counter = 0;

    public void SendMessage(string body)
    {
        var id = $"SQS-{++_counter}";
        _queue.Enqueue((id, body));
        Console.WriteLine($"[SQS] SendMessage → {id}: {body}");
    }

    public string? ReceiveMessage()
    {
        if (_queue.TryDequeue(out var msg))
        {
            Console.WriteLine($"[SQS] ReceiveMessage → {msg.id}");
            return msg.body;
        }
        return null;
    }

    public void DeleteMessage(string messageId) =>
        Console.WriteLine($"[SQS] DeleteMessage {messageId}");
}

public class ElastiCacheStore : IKeyValueStore
{
    private readonly Dictionary<string, string> _cache = new();

    public void Set(string key, string value, TimeSpan? ttl = null)
    {
        _cache[key] = value;
        var ttlStr = ttl.HasValue ? $" EX {(int)ttl.Value.TotalSeconds}" : "";
        Console.WriteLine($"[ElastiCache] SET {key}{ttlStr}");
    }

    public string? Get(string key)
    {
        Console.WriteLine($"[ElastiCache] GET {key}");
        return _cache.TryGetValue(key, out var v) ? v : null;
    }

    public void Delete(string key)
    {
        _cache.Remove(key);
        Console.WriteLine($"[ElastiCache] DEL {key}");
    }
}

// ── Concrete Products — Azure family ─────────────────────────────────────────

public class AzureBlobStorage : IBlobStorage
{
    private readonly Dictionary<string, string> _store = new();

    public void Upload(string blobName, string content)
    {
        _store[blobName] = content;
        Console.WriteLine($"[AzureBlob] UploadBlob https://myaccount.blob.core.windows.net/mycontainer/{blobName}");
    }

    public string Download(string blobName)
    {
        Console.WriteLine($"[AzureBlob] DownloadContent {blobName}");
        return _store.TryGetValue(blobName, out var v) ? v : throw new KeyNotFoundException(blobName);
    }

    public IEnumerable<string> ListBlobs(string prefix)
    {
        Console.WriteLine($"[AzureBlob] GetBlobs prefix={prefix}");
        foreach (var key in _store.Keys)
            if (key.StartsWith(prefix)) yield return key;
    }
}

public class AzureServiceBusQueue : IMessageQueue
{
    private readonly Queue<(string id, string body)> _queue = new();
    private int _counter = 0;

    public void SendMessage(string body)
    {
        var id = $"ASB-{++_counter}";
        _queue.Enqueue((id, body));
        Console.WriteLine($"[ServiceBus] SendMessage → {id}: {body}");
    }

    public string? ReceiveMessage()
    {
        if (_queue.TryDequeue(out var msg))
        {
            Console.WriteLine($"[ServiceBus] ReceiveMessage → {msg.id}");
            return msg.body;
        }
        return null;
    }

    public void DeleteMessage(string messageId) =>
        Console.WriteLine($"[ServiceBus] Complete {messageId}");
}

public class AzureCacheForRedis : IKeyValueStore
{
    private readonly Dictionary<string, string> _cache = new();

    public void Set(string key, string value, TimeSpan? ttl = null)
    {
        _cache[key] = value;
        var ttlStr = ttl.HasValue ? $" (ttl {ttl.Value.TotalSeconds}s)" : "";
        Console.WriteLine($"[AzureRedis] SET {key}{ttlStr}");
    }

    public string? Get(string key)
    {
        Console.WriteLine($"[AzureRedis] GET {key}");
        return _cache.TryGetValue(key, out var v) ? v : null;
    }

    public void Delete(string key)
    {
        _cache.Remove(key);
        Console.WriteLine($"[AzureRedis] DEL {key}");
    }
}

// ── Abstract Factory ─────────────────────────────────────────────────────────

public interface ICloudFactory
{
    IBlobStorage   CreateBlobStorage();
    IMessageQueue  CreateMessageQueue();
    IKeyValueStore CreateKeyValueStore();
}

// ── Concrete Factories ───────────────────────────────────────────────────────

public class AwsFactory : ICloudFactory
{
    public IBlobStorage   CreateBlobStorage()   => new S3Storage();
    public IMessageQueue  CreateMessageQueue()  => new SqsQueue();
    public IKeyValueStore CreateKeyValueStore() => new ElastiCacheStore();
}

public class AzureFactory : ICloudFactory
{
    public IBlobStorage   CreateBlobStorage()   => new AzureBlobStorage();
    public IMessageQueue  CreateMessageQueue()  => new AzureServiceBusQueue();
    public IKeyValueStore CreateKeyValueStore() => new AzureCacheForRedis();
}

// ── Client ───────────────────────────────────────────────────────────────────

public class FileProcessingService
{
    private readonly IBlobStorage   _storage;
    private readonly IMessageQueue  _queue;
    private readonly IKeyValueStore _cache;

    public FileProcessingService(ICloudFactory factory)
    {
        _storage = factory.CreateBlobStorage();
        _queue   = factory.CreateMessageQueue();
        _cache   = factory.CreateKeyValueStore();
    }

    public void ProcessUpload(string fileName, string content)
    {
        // Store file
        _storage.Upload(fileName, content);

        // Cache metadata
        _cache.Set($"meta:{fileName}", $"size={content.Length}", TimeSpan.FromMinutes(10));

        // Notify downstream
        _queue.SendMessage($"FILE_UPLOADED:{fileName}");
    }

    public void HandleNotification()
    {
        var msg = _queue.ReceiveMessage();
        if (msg is null) { Console.WriteLine("  (no messages)"); return; }

        Console.WriteLine($"  Processing: {msg}");
        var fileName = msg.Split(':')[1];
        var meta = _cache.Get($"meta:{fileName}");
        Console.WriteLine($"  Metadata from cache: {meta}");
        var content = _storage.Download(fileName);
        Console.WriteLine($"  Content length: {content.Length} chars");
    }
}

// ── Entry Point ──────────────────────────────────────────────────────────────

class Program
{
    static void Main()
    {
        RunDemo("AWS",   new AwsFactory());
        Console.WriteLine();
        RunDemo("Azure", new AzureFactory());
    }

    static void RunDemo(string provider, ICloudFactory factory)
    {
        Console.WriteLine($"=== {provider} Cloud ===");
        var service = new FileProcessingService(factory);
        service.ProcessUpload("reports/q1-2026.csv", "date,revenue\n2026-01-01,50000");
        Console.WriteLine("--- Handling notification ---");
        service.HandleNotification();
    }
}
```

---

### TypeScript

```typescript
/**
 * Abstract Factory — UI theme system (Light / Dark / High-Contrast).
 *
 * Each theme provides a consistent family of styled components:
 * Button, Input, and Card. The Page (client) uses only abstract types.
 *
 * Run:
 *   npx ts-node abstract_factory.ts
 */

// ── Abstract Products ────────────────────────────────────────────────────────

interface StyledButton {
  render(): string;
  getCSS(): Record<string, string>;
}

interface StyledInput {
  render(placeholder: string): string;
  getCSS(): Record<string, string>;
}

interface StyledCard {
  render(title: string, body: string): string;
  getCSS(): Record<string, string>;
}

// ── Concrete Products — Light theme ─────────────────────────────────────────

class LightButton implements StyledButton {
  render(): string {
    return `<button style="${cssStr(this.getCSS())}">Click me</button>`;
  }
  getCSS(): Record<string, string> {
    return {
      backgroundColor: '#ffffff',
      color: '#000000',
      border: '1px solid #cccccc',
      borderRadius: '4px',
      padding: '8px 16px',
    };
  }
}

class LightInput implements StyledInput {
  render(placeholder: string): string {
    return `<input placeholder="${placeholder}" style="${cssStr(this.getCSS())}" />`;
  }
  getCSS(): Record<string, string> {
    return {
      backgroundColor: '#f9f9f9',
      color: '#000000',
      border: '1px solid #dddddd',
      borderRadius: '4px',
      padding: '6px 12px',
    };
  }
}

class LightCard implements StyledCard {
  render(title: string, body: string): string {
    const css = cssStr(this.getCSS());
    return `<div class="card" style="${css}"><h3>${title}</h3><p>${body}</p></div>`;
  }
  getCSS(): Record<string, string> {
    return {
      backgroundColor: '#ffffff',
      color: '#333333',
      border: '1px solid #e0e0e0',
      borderRadius: '8px',
      padding: '16px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    };
  }
}

// ── Concrete Products — Dark theme ───────────────────────────────────────────

class DarkButton implements StyledButton {
  render(): string {
    return `<button style="${cssStr(this.getCSS())}">Click me</button>`;
  }
  getCSS(): Record<string, string> {
    return {
      backgroundColor: '#1e1e1e',
      color: '#ffffff',
      border: '1px solid #555555',
      borderRadius: '4px',
      padding: '8px 16px',
    };
  }
}

class DarkInput implements StyledInput {
  render(placeholder: string): string {
    return `<input placeholder="${placeholder}" style="${cssStr(this.getCSS())}" />`;
  }
  getCSS(): Record<string, string> {
    return {
      backgroundColor: '#2d2d2d',
      color: '#ffffff',
      border: '1px solid #444444',
      borderRadius: '4px',
      padding: '6px 12px',
    };
  }
}

class DarkCard implements StyledCard {
  render(title: string, body: string): string {
    const css = cssStr(this.getCSS());
    return `<div class="card" style="${css}"><h3>${title}</h3><p>${body}</p></div>`;
  }
  getCSS(): Record<string, string> {
    return {
      backgroundColor: '#1e1e1e',
      color: '#e0e0e0',
      border: '1px solid #3a3a3a',
      borderRadius: '8px',
      padding: '16px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.5)',
    };
  }
}

// ── Concrete Products — High-Contrast theme ──────────────────────────────────

class HCButton implements StyledButton {
  render(): string {
    return `<button style="${cssStr(this.getCSS())}">Click me</button>`;
  }
  getCSS(): Record<string, string> {
    return {
      backgroundColor: '#000000',
      color: '#ffff00',
      border: '2px solid #ffff00',
      borderRadius: '0px',
      padding: '8px 16px',
      fontWeight: 'bold',
    };
  }
}

class HCInput implements StyledInput {
  render(placeholder: string): string {
    return `<input placeholder="${placeholder}" style="${cssStr(this.getCSS())}" />`;
  }
  getCSS(): Record<string, string> {
    return {
      backgroundColor: '#000000',
      color: '#ffffff',
      border: '2px solid #ffffff',
      borderRadius: '0px',
      padding: '6px 12px',
    };
  }
}

class HCCard implements StyledCard {
  render(title: string, body: string): string {
    const css = cssStr(this.getCSS());
    return `<div class="card" style="${css}"><h3>${title}</h3><p>${body}</p></div>`;
  }
  getCSS(): Record<string, string> {
    return {
      backgroundColor: '#000000',
      color: '#ffffff',
      border: '3px solid #ffffff',
      borderRadius: '0px',
      padding: '16px',
    };
  }
}

// ── Abstract Factory ─────────────────────────────────────────────────────────

interface ThemeFactory {
  createButton(): StyledButton;
  createInput(): StyledInput;
  createCard(): StyledCard;
}

// ── Concrete Factories ───────────────────────────────────────────────────────

class LightThemeFactory implements ThemeFactory {
  createButton(): StyledButton { return new LightButton(); }
  createInput():  StyledInput  { return new LightInput();  }
  createCard():   StyledCard   { return new LightCard();   }
}

class DarkThemeFactory implements ThemeFactory {
  createButton(): StyledButton { return new DarkButton(); }
  createInput():  StyledInput  { return new DarkInput();  }
  createCard():   StyledCard   { return new DarkCard();   }
}

class HighContrastThemeFactory implements ThemeFactory {
  createButton(): StyledButton { return new HCButton(); }
  createInput():  StyledInput  { return new HCInput();  }
  createCard():   StyledCard   { return new HCCard();   }
}

// ── Client ───────────────────────────────────────────────────────────────────

class LoginPage {
  private readonly button: StyledButton;
  private readonly input: StyledInput;
  private readonly card: StyledCard;

  constructor(factory: ThemeFactory) {
    this.button = factory.createButton();
    this.input  = factory.createInput();
    this.card   = factory.createCard();
  }

  render(): string {
    const emailInput    = this.input.render('Enter email');
    const passwordInput = this.input.render('Enter password');
    const submitButton  = this.button.render();
    const formContent   = `${emailInput}\n    ${passwordInput}\n    ${submitButton}`;
    return this.card.render('Login', formContent);
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function cssStr(styles: Record<string, string>): string {
  return Object.entries(styles)
    .map(([k, v]) => `${k.replace(/([A-Z])/g, '-$1').toLowerCase()}:${v}`)
    .join(';');
}

function getFactory(theme: string): ThemeFactory {
  switch (theme) {
    case 'dark':          return new DarkThemeFactory();
    case 'highcontrast':  return new HighContrastThemeFactory();
    default:              return new LightThemeFactory();
  }
}

// ── Entry Point ──────────────────────────────────────────────────────────────

const themes = ['light', 'dark', 'highcontrast'] as const;

for (const theme of themes) {
  console.log(`\n=== ${theme.toUpperCase()} Theme ===`);
  const page = new LoginPage(getFactory(theme));
  console.log(page.render());
}
```

---

### Go

```go
// Abstract Factory — notification system.
//
// Different notification channels (Email and SMS) are grouped into
// provider families (SendGrid/Twilio for production, stub for testing).
// The AlertService (client) depends only on interfaces.
//
// Run:
//   go run abstract_factory.go

package main

import (
	"fmt"
	"strings"
	"time"
)

// ── Abstract Products ─────────────────────────────────────────────────────────

// EmailSender sends an email message.
type EmailSender interface {
	Send(to, subject, body string) error
	Provider() string
}

// SMSSender sends an SMS message.
type SMSSender interface {
	Send(to, message string) error
	Provider() string
}

// ── Concrete Products — Production (SendGrid + Twilio) ────────────────────────

type SendGridEmail struct {
	apiKey string
}

func (s *SendGridEmail) Send(to, subject, body string) error {
	fmt.Printf("[SendGrid] POST /v3/mail/send → to=%s subject=%q (key=%.8s...)\n",
		to, subject, s.apiKey)
	return nil // real impl would call the API
}

func (s *SendGridEmail) Provider() string { return "SendGrid" }

type TwilioSMS struct {
	accountSID string
	authToken  string
	fromNumber string
}

func (t *TwilioSMS) Send(to, message string) error {
	fmt.Printf("[Twilio] POST /2010-04-01/Accounts/%s/Messages → to=%s msg=%q\n",
		t.accountSID[:8]+"...", to, message)
	return nil
}

func (t *TwilioSMS) Provider() string { return "Twilio" }

// ── Concrete Products — Stub (for unit tests / local dev) ─────────────────────

type StubEmail struct {
	Sent []struct{ To, Subject, Body string }
}

func (s *StubEmail) Send(to, subject, body string) error {
	s.Sent = append(s.Sent, struct{ To, Subject, Body string }{to, subject, body})
	fmt.Printf("[StubEmail] captured → to=%s subject=%q\n", to, subject)
	return nil
}

func (s *StubEmail) Provider() string { return "Stub" }

type StubSMS struct {
	Sent []struct{ To, Message string }
}

func (s *StubSMS) Send(to, message string) error {
	s.Sent = append(s.Sent, struct{ To, Message string }{to, message})
	fmt.Printf("[StubSMS] captured → to=%s msg=%q\n", to, message)
	return nil
}

func (s *StubSMS) Provider() string { return "Stub" }

// ── Abstract Factory ──────────────────────────────────────────────────────────

// NotificationFactory creates families of notification senders.
type NotificationFactory interface {
	CreateEmailSender() EmailSender
	CreateSMSSender() SMSSender
}

// ── Concrete Factories ────────────────────────────────────────────────────────

type ProductionFactory struct {
	SendGridAPIKey     string
	TwilioAccountSID   string
	TwilioAuthToken    string
	TwilioFromNumber   string
}

func (f *ProductionFactory) CreateEmailSender() EmailSender {
	return &SendGridEmail{apiKey: f.SendGridAPIKey}
}

func (f *ProductionFactory) CreateSMSSender() SMSSender {
	return &TwilioSMS{
		accountSID: f.TwilioAccountSID,
		authToken:  f.TwilioAuthToken,
		fromNumber: f.TwilioFromNumber,
	}
}

type StubFactory struct {
	// Expose stubs so tests can inspect captured messages.
	Email *StubEmail
	SMS   *StubSMS
}

func NewStubFactory() *StubFactory {
	return &StubFactory{Email: &StubEmail{}, SMS: &StubSMS{}}
}

func (f *StubFactory) CreateEmailSender() EmailSender { return f.Email }
func (f *StubFactory) CreateSMSSender() SMSSender     { return f.SMS }

// ── Client ────────────────────────────────────────────────────────────────────

// Alert represents a system alert to be dispatched.
type Alert struct {
	Level   string // "info", "warning", "critical"
	Title   string
	Message string
	At      time.Time
}

// AlertService dispatches alerts via the injected notification family.
type AlertService struct {
	email EmailSender
	sms   SMSSender
	ops   []string // on-call phone numbers
}

func NewAlertService(factory NotificationFactory, opsPhones ...string) *AlertService {
	return &AlertService{
		email: factory.CreateEmailSender(),
		sms:   factory.CreateSMSSender(),
		ops:   opsPhones,
	}
}

func (a *AlertService) Dispatch(alert Alert) {
	subject := fmt.Sprintf("[%s] %s", strings.ToUpper(alert.Level), alert.Title)
	body := fmt.Sprintf("Alert at %s:\n\n%s\n\nLevel: %s",
		alert.At.Format(time.RFC3339), alert.Message, alert.Level)

	// Always send an email to the ops team distribution list.
	if err := a.email.Send("ops@example.com", subject, body); err != nil {
		fmt.Printf("email error: %v\n", err)
	}

	// For critical alerts also send SMS to each on-call number.
	if alert.Level == "critical" {
		smsBody := fmt.Sprintf("CRITICAL: %s — %s", alert.Title, alert.Message)
		for _, phone := range a.ops {
			if err := a.sms.Send(phone, smsBody); err != nil {
				fmt.Printf("sms error to %s: %v\n", phone, err)
			}
		}
	}
}

// ── Entry Point ───────────────────────────────────────────────────────────────

func main() {
	// Production configuration (credentials would come from env vars in reality).
	fmt.Println("=== Production AlertService ===")
	prodFactory := &ProductionFactory{
		SendGridAPIKey:   "SG.prod_key_example_only",
		TwilioAccountSID: "ACprod12345678",
		TwilioAuthToken:  "auth_token_example",
		TwilioFromNumber: "+15550001111",
	}
	prodSvc := NewAlertService(prodFactory, "+15559990001", "+15559990002")

	prodSvc.Dispatch(Alert{
		Level:   "info",
		Title:   "Deployment completed",
		Message: "v2.5.1 deployed to production.",
		At:      time.Now(),
	})
	prodSvc.Dispatch(Alert{
		Level:   "critical",
		Title:   "Database unreachable",
		Message: "Primary DB failed health check 3 times.",
		At:      time.Now(),
	})

	fmt.Println("\n=== Test AlertService (stub) ===")
	stubFactory := NewStubFactory()
	testSvc := NewAlertService(stubFactory, "+15550000000")

	testSvc.Dispatch(Alert{
		Level:   "critical",
		Title:   "Test alert",
		Message: "This is a test.",
		At:      time.Now(),
	})

	fmt.Printf("\nStub captured %d email(s) and %d SMS(es)\n",
		len(stubFactory.Email.Sent),
		len(stubFactory.SMS.Sent))
}
```

---

### PHP

```php
<?php
/**
 * Abstract Factory — payment gateway system.
 *
 * The checkout flow (client) supports Stripe and PayPal without
 * depending on either SDK. Each gateway provides a compatible set of:
 *   - PaymentIntent  (authorise / capture)
 *   - Refund         (partial or full refund)
 *   - WebhookHandler (validate inbound events)
 *
 * Run:
 *   php abstract_factory.php
 */

declare(strict_types=1);

// ── Abstract Products ─────────────────────────────────────────────────────────

interface PaymentIntent
{
    /** Authorise and capture a payment. Returns a transaction reference. */
    public function create(int $amountCents, string $currency, string $description): string;

    /** Retrieve current status of an existing intent. */
    public function status(string $ref): string;
}

interface Refund
{
    /** Issue a refund. $amountCents = 0 means full refund. */
    public function issue(string $transactionRef, int $amountCents = 0): string;
}

interface WebhookHandler
{
    /** Verify the inbound webhook payload and return the event type. */
    public function verify(string $payload, string $signature): string;
}

// ── Concrete Products — Stripe family ────────────────────────────────────────

class StripePaymentIntent implements PaymentIntent
{
    private array $intents = [];

    public function create(int $amountCents, string $currency, string $description): string
    {
        $ref = 'pi_stripe_' . uniqid();
        $this->intents[$ref] = 'succeeded';
        printf("[Stripe] POST /v1/payment_intents → amount=%d %s \"%s\" → %s\n",
            $amountCents, strtoupper($currency), $description, $ref);
        return $ref;
    }

    public function status(string $ref): string
    {
        $status = $this->intents[$ref] ?? 'not_found';
        printf("[Stripe] GET /v1/payment_intents/%s → %s\n", $ref, $status);
        return $status;
    }
}

class StripeRefund implements Refund
{
    public function issue(string $transactionRef, int $amountCents = 0): string
    {
        $refundRef = 're_stripe_' . uniqid();
        $amountStr = $amountCents === 0 ? 'full' : "{$amountCents} cents";
        printf("[Stripe] POST /v1/refunds → payment_intent=%s amount=%s → %s\n",
            $transactionRef, $amountStr, $refundRef);
        return $refundRef;
    }
}

class StripeWebhookHandler implements WebhookHandler
{
    private string $secret;

    public function __construct(string $webhookSecret)
    {
        $this->secret = $webhookSecret;
    }

    public function verify(string $payload, string $signature): string
    {
        // Real impl: Stripe\Webhook::constructEvent($payload, $signature, $this->secret)
        $expectedSig = hash_hmac('sha256', $payload, $this->secret);
        if (!hash_equals($expectedSig, $signature)) {
            throw new \RuntimeException('Invalid Stripe webhook signature');
        }
        $event = json_decode($payload, true);
        printf("[Stripe] Webhook verified: %s\n", $event['type']);
        return $event['type'];
    }
}

// ── Concrete Products — PayPal family ────────────────────────────────────────

class PayPalPaymentIntent implements PaymentIntent
{
    private array $orders = [];

    public function create(int $amountCents, string $currency, string $description): string
    {
        $ref = 'PAYPAL-ORDER-' . strtoupper(uniqid());
        $this->orders[$ref] = 'COMPLETED';
        $amount = number_format($amountCents / 100, 2);
        printf("[PayPal] POST /v2/checkout/orders → amount=%s %s \"%s\" → %s\n",
            $amount, strtoupper($currency), $description, $ref);
        return $ref;
    }

    public function status(string $ref): string
    {
        $status = $this->orders[$ref] ?? 'NOT_FOUND';
        printf("[PayPal] GET /v2/checkout/orders/%s → %s\n", $ref, $status);
        return $status;
    }
}

class PayPalRefund implements Refund
{
    public function issue(string $transactionRef, int $amountCents = 0): string
    {
        $refundRef = 'PAYPAL-REFUND-' . strtoupper(uniqid());
        $amountStr = $amountCents === 0 ? 'full' : number_format($amountCents / 100, 2);
        printf("[PayPal] POST /v2/payments/captures/%s/refund → amount=%s → %s\n",
            $transactionRef, $amountStr, $refundRef);
        return $refundRef;
    }
}

class PayPalWebhookHandler implements WebhookHandler
{
    public function verify(string $payload, string $signature): string
    {
        // Real impl: call PayPal's webhook verification API
        printf("[PayPal] Webhook verified (PAYPAL-AUTH-ALGO/ED25519): ");
        $event = json_decode($payload, true);
        printf("%s\n", $event['event_type']);
        return $event['event_type'];
    }
}

// ── Abstract Factory ──────────────────────────────────────────────────────────

interface PaymentGatewayFactory
{
    public function createPaymentIntent(): PaymentIntent;
    public function createRefund(): Refund;
    public function createWebhookHandler(): WebhookHandler;
}

// ── Concrete Factories ────────────────────────────────────────────────────────

class StripeFactory implements PaymentGatewayFactory
{
    public function __construct(
        private string $secretKey,
        private string $webhookSecret,
    ) {}

    public function createPaymentIntent(): PaymentIntent { return new StripePaymentIntent(); }
    public function createRefund(): Refund               { return new StripeRefund(); }
    public function createWebhookHandler(): WebhookHandler
    {
        return new StripeWebhookHandler($this->webhookSecret);
    }
}

class PayPalFactory implements PaymentGatewayFactory
{
    public function __construct(
        private string $clientId,
        private string $clientSecret,
    ) {}

    public function createPaymentIntent(): PaymentIntent { return new PayPalPaymentIntent(); }
    public function createRefund(): Refund               { return new PayPalRefund(); }
    public function createWebhookHandler(): WebhookHandler { return new PayPalWebhookHandler(); }
}

// ── Client ────────────────────────────────────────────────────────────────────

class CheckoutService
{
    private PaymentIntent  $intentService;
    private Refund         $refundService;
    private WebhookHandler $webhookHandler;

    public function __construct(PaymentGatewayFactory $factory)
    {
        $this->intentService  = $factory->createPaymentIntent();
        $this->refundService  = $factory->createRefund();
        $this->webhookHandler = $factory->createWebhookHandler();
    }

    public function processOrder(int $amountCents, string $currency, string $desc): string
    {
        $ref = $this->intentService->create($amountCents, $currency, $desc);
        $status = $this->intentService->status($ref);
        printf("  Order result: ref=%s status=%s\n", $ref, $status);
        return $ref;
    }

    public function refundOrder(string $ref, int $amountCents = 0): void
    {
        $refundRef = $this->refundService->issue($ref, $amountCents);
        printf("  Refund issued: %s\n", $refundRef);
    }

    public function handleWebhook(string $payload, string $sig): void
    {
        $eventType = $this->webhookHandler->verify($payload, $sig);
        printf("  Handled webhook event: %s\n", $eventType);
    }
}

// ── Entry Point ───────────────────────────────────────────────────────────────

echo "=== Stripe Gateway ===\n";
$stripeFactory = new StripeFactory('sk_test_example', 'whsec_example');
$checkoutStripe = new CheckoutService($stripeFactory);
$stripeRef = $checkoutStripe->processOrder(4999, 'usd', 'Pro Plan subscription');
$checkoutStripe->refundOrder($stripeRef, 2500);

$stripePayload   = json_encode(['type' => 'payment_intent.succeeded']);
$stripeSig       = hash_hmac('sha256', $stripePayload, 'whsec_example');
$checkoutStripe->handleWebhook($stripePayload, $stripeSig);

echo "\n=== PayPal Gateway ===\n";
$paypalFactory = new PayPalFactory('client_id_example', 'client_secret_example');
$checkoutPayPal = new CheckoutService($paypalFactory);
$paypalRef = $checkoutPayPal->processOrder(9900, 'eur', 'Annual plan');
$checkoutPayPal->refundOrder($paypalRef);

$paypalPayload = json_encode(['event_type' => 'PAYMENT.CAPTURE.COMPLETED']);
$checkoutPayPal->handleWebhook($paypalPayload, 'ignored_by_stub');
```

---

### Ruby

```ruby
# Abstract Factory — logging backend system.
#
# An application uses a family of loggers: a structured Logger for
# application events and a MetricsRecorder for numeric measurements.
# Two backends are provided: Console (development) and CloudWatch (production).
#
# Run:
#   ruby abstract_factory.rb

require 'json'
require 'time'

# ── Abstract Products (duck-typed via documentation contracts) ────────────────

# Logger interface:
#   #log(level, message, context = {}) → void

# MetricsRecorder interface:
#   #record(metric_name, value, unit: 'Count', dimensions: {}) → void
#   #timing(metric_name, duration_ms, dimensions: {}) → void

# ── Concrete Products — Console family (development) ─────────────────────────

class ConsoleLogger
  COLORS = { debug: 36, info: 32, warn: 33, error: 31, fatal: 35 }.freeze

  def log(level, message, context = {})
    color  = COLORS.fetch(level, 37)
    ts     = Time.now.strftime('%H:%M:%S.%L')
    ctx    = context.empty? ? '' : " #{context.to_json}"
    puts "\e[#{color}m[#{ts}] #{level.upcase.ljust(5)} #{message}#{ctx}\e[0m"
  end
end

class ConsoleMetricsRecorder
  def record(metric_name, value, unit: 'Count', dimensions: {})
    dim_str = dimensions.map { |k, v| "#{k}=#{v}" }.join(' ')
    puts "[METRICS] #{metric_name}: #{value} #{unit}" \
         "#{dim_str.empty? ? '' : " (#{dim_str})"}"
  end

  def timing(metric_name, duration_ms, dimensions: {})
    record(metric_name, duration_ms, unit: 'Milliseconds', dimensions: dimensions)
  end
end

# ── Concrete Products — CloudWatch family (production) ────────────────────────

class CloudWatchLogger
  def initialize(log_group:, log_stream:, region: 'us-east-1')
    @log_group  = log_group
    @log_stream = log_stream
    @region     = region
  end

  def log(level, message, context = {})
    # Real impl: Aws::CloudWatchLogs::Client#put_log_events
    payload = {
      timestamp: (Time.now.to_f * 1000).to_i,
      message: { level: level, msg: message, **context }.to_json
    }
    puts "[CloudWatch] PutLogEvents → group=#{@log_group} stream=#{@log_stream} " \
         "payload=#{payload[:message]}"
  end
end

class CloudWatchMetricsRecorder
  def initialize(namespace:, region: 'us-east-1')
    @namespace = namespace
    @region    = region
  end

  def record(metric_name, value, unit: 'Count', dimensions: {})
    dim_str = dimensions.map { |k, v| "{ Name: #{k}, Value: #{v} }" }.join(', ')
    puts "[CloudWatch] PutMetricData → Namespace=#{@namespace} " \
         "MetricName=#{metric_name} Value=#{value} Unit=#{unit}" \
         "#{dim_str.empty? ? '' : " Dimensions=[#{dim_str}]"}"
  end

  def timing(metric_name, duration_ms, dimensions: {})
    record(metric_name, duration_ms, unit: 'Milliseconds', dimensions: dimensions)
  end
end

# ── Abstract Factory ──────────────────────────────────────────────────────────

module ObservabilityFactory
  # Subclasses must implement:
  #   #create_logger   → responds to #log(level, message, context)
  #   #create_metrics  → responds to #record and #timing
end

# ── Concrete Factories ────────────────────────────────────────────────────────

class DevelopmentFactory
  include ObservabilityFactory

  def create_logger  = ConsoleLogger.new
  def create_metrics = ConsoleMetricsRecorder.new
end

class ProductionFactory
  include ObservabilityFactory

  def initialize(app_name:, aws_region: 'us-east-1')
    @app_name  = app_name
    @region    = aws_region
  end

  def create_logger
    CloudWatchLogger.new(
      log_group:  "/#{@app_name}/application",
      log_stream: Time.now.strftime('%Y/%m/%d'),
      region:     @region
    )
  end

  def create_metrics
    CloudWatchMetricsRecorder.new(namespace: @app_name, region: @region)
  end
end

# ── Client ────────────────────────────────────────────────────────────────────

class OrderProcessor
  def initialize(factory)
    @logger  = factory.create_logger
    @metrics = factory.create_metrics
  end

  def process(order)
    @logger.log(:info, 'Processing order', order_id: order[:id], user: order[:user])

    start = Process.clock_gettime(Process::CLOCK_MONOTONIC, :millisecond)

    # Simulate processing
    if order[:amount] <= 0
      @logger.log(:error, 'Invalid order amount', order_id: order[:id])
      @metrics.record('OrderFailures', 1, dimensions: { reason: 'invalid_amount' })
      return false
    end

    duration = Process.clock_gettime(Process::CLOCK_MONOTONIC, :millisecond) - start

    @logger.log(:info, 'Order processed successfully',
                order_id: order[:id], amount_cents: order[:amount])
    @metrics.record('OrdersProcessed', 1, dimensions: { currency: order[:currency] })
    @metrics.timing('OrderProcessingTime', duration, dimensions: { step: 'full' })

    true
  end
end

# ── Entry Point ───────────────────────────────────────────────────────────────

orders = [
  { id: 'ORD-001', user: 'alice', amount: 4999, currency: 'USD' },
  { id: 'ORD-002', user: 'bob',   amount: -1,   currency: 'EUR' },
  { id: 'ORD-003', user: 'carol', amount: 9900, currency: 'GBP' },
]

puts '=== Development (Console) ==='
dev_processor = OrderProcessor.new(DevelopmentFactory.new)
orders.each { |o| dev_processor.process(o) }

puts "\n=== Production (CloudWatch) ==="
prod_processor = OrderProcessor.new(
  ProductionFactory.new(app_name: 'my-ecommerce', aws_region: 'eu-west-1')
)
orders.each { |o| prod_processor.process(o) }
```

---

## When To Use

Use the Abstract Factory pattern when:

- **You need families of compatible products.** The application must work with multiple variants of related objects (e.g. Windows widgets, macOS widgets) and you must guarantee that products from one family are never mixed with products from another.

- **You want to hide concrete implementations from client code.** Client code should not depend on the concrete classes; only on interfaces. This is especially important in library or framework design where you publish interfaces but want the flexibility to change (or let callers override) the concrete implementations.

- **You anticipate adding new product families.** Adding a new family (e.g. a Linux widget set) means adding new concrete products and a new factory — existing client code needs no modification (Open/Closed Principle).

- **You are building a configurable or pluggable architecture.** The factory can be selected from a configuration file, dependency injection container, or environment variable, making the entire product family swappable without recompilation.

- **You need to enforce compatibility at design time.** If using the wrong combination of products would cause runtime errors or subtle bugs, Abstract Factory makes incompatible combinations impossible to construct.

**Do NOT use when:**

- There is only one product type (prefer a simple Factory Method instead).
- The product family is unlikely to change and adding new families is not a requirement — the extra indirection may not be worth it.
- You are prototyping and the overhead of defining many interfaces slows you down.

---

## Pros & Cons

### Pros

| Benefit | Detail |
|---|---|
| **Compatibility guarantee** | All products returned by one concrete factory are designed to work together. You cannot accidentally mix a Windows button with a macOS checkbox. |
| **Loose coupling** | Client code depends only on abstract interfaces. Concrete classes can change without affecting clients. |
| **Single Responsibility Principle** | Product creation code is isolated in one place (the concrete factory), rather than scattered across the application. |
| **Open/Closed Principle** | Adding a new product family requires adding new classes without touching existing code. |
| **Swappable families** | Switching the entire product family (e.g. from MySQL to PostgreSQL) requires changing only the factory instantiation site. |

### Cons

| Drawback | Detail |
|---|---|
| **Increased complexity** | Introducing many interfaces and classes for a small number of product types may be overkill. |
| **Adding new product types is hard** | Adding a new product type (e.g. a `Tooltip`) to an existing Abstract Factory requires changing the factory interface and every concrete factory — a breaking change in terms of the interface contract. |
| **Can obscure intent** | Heavily abstracted factories can make it harder to trace which concrete class is ultimately being used during debugging. |

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Factory Method** | Abstract Factory is often implemented using Factory Methods. Each creation method in the concrete factory is essentially a Factory Method. Abstract Factory has a wider scope — it creates families; Factory Method creates one product type. |
| **Builder** | Both construct complex objects. Builder focuses on constructing a single object step-by-step (useful when construction requires many optional parameters). Abstract Factory instantiates multiple related objects in one shot, emphasising family compatibility. |
| **Singleton** | Concrete factories are often implemented as Singletons, because an application typically needs only one instance of a factory. The factory itself manages which product variants exist. |
| **Prototype** | Abstract Factory can use Prototype to store and clone product templates rather than subclassing for every variant. This is useful when the number of product variants is large or determined at runtime. |

---

## Sources

- https://refactoring.guru/design-patterns/abstract-factory
- https://sourcemaking.com/design_patterns/abstract_factory
