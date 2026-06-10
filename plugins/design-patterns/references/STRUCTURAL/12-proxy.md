# Proxy Pattern

**Category:** Structural
**Also Known As:** Surrogate

---

## Intent

Provide a substitute or placeholder for another object. A proxy controls access to the original object, allowing you to perform something either before or after the request gets through to the original object — without changing the original object's interface.

---

## Problem It Solves

Real-world software often deals with objects that are:

- **Expensive to create** — a database connection pool, a large image, or a video file loaded from disk should not be initialized until actually needed (lazy initialization).
- **Remotely located** — a service may live on another server or process; the client should not need to know how to communicate with it directly.
- **Sensitive** — only certain clients should be able to invoke certain operations (access control).
- **Worth auditing** — every call to a service may need to be logged for debugging or compliance purposes.
- **Cacheable** — repeated identical requests should return a stored result rather than re-computing it.

Changing the real service class to handle all these concerns violates the Single Responsibility Principle and pollutes business logic with infrastructure code. Changing every client call site is equally bad.

The Proxy pattern inserts a lightweight stand-in that keeps the same interface as the real object, so clients are unaware they are talking to a proxy.

---

## Solution

1. Define a **ServiceInterface** that both the real service and the proxy implement.
2. Create a **RealService** class that contains the actual heavyweight logic.
3. Create a **Proxy** class that:
   - Holds a reference to the RealService (or creates it lazily).
   - Implements the same interface.
   - Intercepts calls, performs additional work (logging, caching, auth checks, etc.), and delegates to the RealService when appropriate.
4. The **Client** is programmed to the interface and receives a Proxy instance — it never needs to change.

---

## Structure (ASCII diagram)

```
         «interface»
       ServiceInterface
       +--------------+
       | + request()  |
       +------+-------+
              |
      +-------+--------+
      |                |
+-----+------+   +-----+--------+
| RealService|   |    Proxy     |
+------------+   +--------------+
| + request()|   | - realSvc:   |
|            |   |   RealService|
+------------+   | + request()  |
                 +------+-------+
                        |  delegates to
                        v
                 +------+-------+
                 | RealService  |
                 +--------------+

Client --> ServiceInterface
           (may be Proxy or RealService)
```

**Data-flow for a Caching Proxy:**

```
Client
  |
  | request(key)
  v
Proxy
  |-- check cache
  |     hit  --> return cached result
  |     miss --> call RealService.request(key)
  |                  --> store in cache
  |                  --> return result
```

---

## Participants

| Participant | Role |
|---|---|
| **ServiceInterface** | Declares the common interface for RealService and Proxy so the Proxy can be used anywhere a RealService is expected. |
| **RealService (Service)** | The real object containing core business logic; often slow to instantiate or sensitive to call directly. |
| **Proxy** | Holds a reference to RealService. Controls access by performing pre/post processing and delegating to RealService. |
| **Client** | Works with both RealService and Proxy through the ServiceInterface; is unaware of the proxy layer. |

---

## How It Works (step-by-step)

1. **Client calls** the proxy's method using the ServiceInterface.
2. **Proxy pre-processes** the request — it may check access rights, look up a cache, log the call, or measure timing.
3. **Decision point:**
   - If the proxy can satisfy the request on its own (e.g., cache hit, access denied), it returns without involving RealService.
   - Otherwise it proceeds.
4. **Lazy instantiation:** if the RealService has not been created yet, the proxy constructs it now.
5. **Proxy delegates** the call to `realService.method(args)`.
6. **Proxy post-processes** the response — it may cache the result, log the response time, or transform the data.
7. **Result is returned** to the Client.

---

## Code Examples

### Python

```python
"""
Caching Proxy — Real-world scenario: a DataFetcher that makes expensive
HTTP API calls. The CachingProxy intercepts calls and returns stored
results for repeated queries, reducing network traffic.
"""
from __future__ import annotations
import time
from abc import ABC, abstractmethod
from typing import Optional


# ------------------------------------------------------------------
# Service Interface
# ------------------------------------------------------------------
class DataFetcher(ABC):
    @abstractmethod
    def fetch(self, endpoint: str) -> str:
        """Fetch data from the given API endpoint."""


# ------------------------------------------------------------------
# Real Service — simulates a slow external HTTP call
# ------------------------------------------------------------------
class RealDataFetcher(DataFetcher):
    def fetch(self, endpoint: str) -> str:
        print(f"  [RealDataFetcher] Making HTTP request to '{endpoint}' …")
        time.sleep(0.5)  # simulate network latency
        return f"<response from {endpoint}>"


# ------------------------------------------------------------------
# Caching Proxy
# ------------------------------------------------------------------
class CachingProxy(DataFetcher):
    def __init__(self, ttl_seconds: float = 5.0) -> None:
        self._real: Optional[RealDataFetcher] = None
        self._cache: dict[str, tuple[str, float]] = {}  # key -> (value, timestamp)
        self._ttl = ttl_seconds

    def _get_real(self) -> RealDataFetcher:
        if self._real is None:
            print("  [CachingProxy] Lazily creating RealDataFetcher …")
            self._real = RealDataFetcher()
        return self._real

    def fetch(self, endpoint: str) -> str:
        now = time.monotonic()
        if endpoint in self._cache:
            value, ts = self._cache[endpoint]
            age = now - ts
            if age < self._ttl:
                print(f"  [CachingProxy] Cache HIT for '{endpoint}' (age={age:.2f}s)")
                return value
            else:
                print(f"  [CachingProxy] Cache EXPIRED for '{endpoint}'")

        result = self._get_real().fetch(endpoint)
        self._cache[endpoint] = (result, now)
        print(f"  [CachingProxy] Stored result for '{endpoint}' in cache")
        return result


# ------------------------------------------------------------------
# Client code — depends only on DataFetcher interface
# ------------------------------------------------------------------
def client_code(fetcher: DataFetcher) -> None:
    endpoints = [
        "/api/users",
        "/api/products",
        "/api/users",   # should be served from cache
        "/api/users",   # should be served from cache
        "/api/products",
    ]
    for ep in endpoints:
        print(f"\nClient requesting '{ep}':")
        data = fetcher.fetch(ep)
        print(f"  Got: {data}")


if __name__ == "__main__":
    print("=== Using CachingProxy ===")
    proxy = CachingProxy(ttl_seconds=2.0)
    client_code(proxy)
```

---

### Java

```java
/**
 * Protection Proxy — Real-world scenario: a DocumentService where only
 * users with the "EDITOR" role may save documents. The
 * ProtectedDocumentService proxy enforces authorization before delegating
 * to the real service.
 */
import java.util.Set;

// ------------------------------------------------------------------
// Service Interface
// ------------------------------------------------------------------
interface DocumentService {
    String load(String docId);
    void save(String docId, String content);
}

// ------------------------------------------------------------------
// Real Service
// ------------------------------------------------------------------
class RealDocumentService implements DocumentService {
    @Override
    public String load(String docId) {
        System.out.printf("  [RealDocumentService] Loading document '%s'%n", docId);
        return "Content of " + docId;
    }

    @Override
    public void save(String docId, String content) {
        System.out.printf("  [RealDocumentService] Saving document '%s': %s%n", docId, content);
    }
}

// ------------------------------------------------------------------
// User context (simplified)
// ------------------------------------------------------------------
class User {
    private final String name;
    private final Set<String> roles;

    public User(String name, String... roles) {
        this.name = name;
        this.roles = Set.of(roles);
    }

    public String getName() { return name; }
    public boolean hasRole(String role) { return roles.contains(role); }
}

// ------------------------------------------------------------------
// Protection Proxy
// ------------------------------------------------------------------
class ProtectedDocumentService implements DocumentService {
    private final RealDocumentService real = new RealDocumentService();
    private final User currentUser;

    public ProtectedDocumentService(User currentUser) {
        this.currentUser = currentUser;
    }

    @Override
    public String load(String docId) {
        // Any authenticated user may load
        System.out.printf("  [Proxy] User '%s' loading '%s'%n", currentUser.getName(), docId);
        return real.load(docId);
    }

    @Override
    public void save(String docId, String content) {
        if (!currentUser.hasRole("EDITOR")) {
            System.out.printf(
                "  [Proxy] DENIED — user '%s' lacks EDITOR role%n", currentUser.getName());
            return;
        }
        System.out.printf("  [Proxy] User '%s' authorized to save '%s'%n",
            currentUser.getName(), docId);
        real.save(docId, content);
    }
}

// ------------------------------------------------------------------
// Client
// ------------------------------------------------------------------
public class ProxyDemo {
    static void clientCode(DocumentService svc, String docId) {
        System.out.println("Loading document …");
        String content = svc.load(docId);
        System.out.println("  Content: " + content);

        System.out.println("Saving document …");
        svc.save(docId, "Updated content");
    }

    public static void main(String[] args) {
        System.out.println("=== Viewer (no EDITOR role) ===");
        DocumentService viewerProxy =
            new ProtectedDocumentService(new User("alice", "VIEWER"));
        clientCode(viewerProxy, "report-2024.docx");

        System.out.println("\n=== Editor ===");
        DocumentService editorProxy =
            new ProtectedDocumentService(new User("bob", "VIEWER", "EDITOR"));
        clientCode(editorProxy, "report-2024.docx");
    }
}
```

---

### C++

```cpp
/**
 * Logging Proxy — Real-world scenario: a FileStorage service that reads
 * and writes files. The LoggingProxy wraps every call with a timestamped
 * audit trail written to stdout (could equally write to a log file).
 */
#include <chrono>
#include <ctime>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>

// ------------------------------------------------------------------
// Service Interface
// ------------------------------------------------------------------
class FileStorage {
public:
    virtual ~FileStorage() = default;
    virtual void write(const std::string& path, const std::string& data) = 0;
    virtual std::string read(const std::string& path) = 0;
};

// ------------------------------------------------------------------
// Real Service
// ------------------------------------------------------------------
class RealFileStorage : public FileStorage {
public:
    void write(const std::string& path, const std::string& data) override {
        std::ofstream ofs(path);
        if (!ofs) throw std::runtime_error("Cannot open file: " + path);
        ofs << data;
        std::cout << "  [RealFileStorage] Written " << data.size()
                  << " bytes to '" << path << "'\n";
    }

    std::string read(const std::string& path) override {
        std::ifstream ifs(path);
        if (!ifs) throw std::runtime_error("File not found: " + path);
        std::ostringstream ss;
        ss << ifs.rdbuf();
        std::cout << "  [RealFileStorage] Read " << ss.str().size()
                  << " bytes from '" << path << "'\n";
        return ss.str();
    }
};

// ------------------------------------------------------------------
// Logging Proxy
// ------------------------------------------------------------------
class LoggingProxy : public FileStorage {
public:
    explicit LoggingProxy(std::shared_ptr<FileStorage> real)
        : real_(std::move(real)) {}

    void write(const std::string& path, const std::string& data) override {
        log("WRITE", path, "bytes=" + std::to_string(data.size()));
        try {
            real_->write(path, data);
            log("WRITE-OK", path, "");
        } catch (const std::exception& e) {
            log("WRITE-ERR", path, e.what());
            throw;
        }
    }

    std::string read(const std::string& path) override {
        log("READ", path, "");
        try {
            std::string result = real_->read(path);
            log("READ-OK", path, "bytes=" + std::to_string(result.size()));
            return result;
        } catch (const std::exception& e) {
            log("READ-ERR", path, e.what());
            throw;
        }
    }

private:
    std::shared_ptr<FileStorage> real_;

    static void log(const std::string& op,
                    const std::string& path,
                    const std::string& extra) {
        auto now = std::chrono::system_clock::to_time_t(
            std::chrono::system_clock::now());
        char buf[20];
        std::strftime(buf, sizeof(buf), "%H:%M:%S", std::localtime(&now));
        std::cout << "[" << buf << "] [LoggingProxy] " << op
                  << " path='" << path << "'";
        if (!extra.empty()) std::cout << " " << extra;
        std::cout << "\n";
    }
};

// ------------------------------------------------------------------
// Client
// ------------------------------------------------------------------
void clientCode(FileStorage& storage) {
    storage.write("/tmp/proxy_demo.txt", "Hello from Proxy pattern!");
    std::string content = storage.read("/tmp/proxy_demo.txt");
    std::cout << "  Client received: \"" << content << "\"\n";
}

int main() {
    auto real    = std::make_shared<RealFileStorage>();
    auto proxy   = std::make_shared<LoggingProxy>(real);

    std::cout << "=== Using LoggingProxy ===\n";
    clientCode(*proxy);
    return 0;
}
```

---

### C#

```csharp
/**
 * Virtual Proxy (Lazy Initialization) — Real-world scenario: loading a
 * high-resolution image from disk is expensive. ImageProxy defers the
 * actual disk read until the first time the image is rendered.
 */
using System;

namespace ProxyPattern
{
    // ------------------------------------------------------------------
    // Service Interface
    // ------------------------------------------------------------------
    public interface IImage
    {
        void Render();
        (int Width, int Height) GetDimensions();
    }

    // ------------------------------------------------------------------
    // Real Service — expensive to construct
    // ------------------------------------------------------------------
    public class HighResolutionImage : IImage
    {
        private readonly string _filePath;
        private readonly int _width;
        private readonly int _height;

        public HighResolutionImage(string filePath)
        {
            _filePath = filePath;
            Console.WriteLine($"  [HighResolutionImage] Loading '{filePath}' from disk … (slow!)");
            // Simulate expensive I/O
            System.Threading.Thread.Sleep(300);
            _width  = 3840;
            _height = 2160;
            Console.WriteLine($"  [HighResolutionImage] Loaded {_width}x{_height} image.");
        }

        public void Render()
        {
            Console.WriteLine($"  [HighResolutionImage] Rendering '{_filePath}' ({_width}x{_height})");
        }

        public (int Width, int Height) GetDimensions() => (_width, _height);
    }

    // ------------------------------------------------------------------
    // Virtual Proxy — defers creation until first use
    // ------------------------------------------------------------------
    public class ImageProxy : IImage
    {
        private readonly string _filePath;
        private HighResolutionImage? _realImage;

        public ImageProxy(string filePath)
        {
            _filePath = filePath;
            Console.WriteLine($"  [ImageProxy] Proxy created for '{filePath}' (image NOT loaded yet)");
        }

        private HighResolutionImage GetReal()
        {
            if (_realImage is null)
            {
                Console.WriteLine("  [ImageProxy] First access — initializing real image …");
                _realImage = new HighResolutionImage(_filePath);
            }
            return _realImage;
        }

        public void Render() => GetReal().Render();

        // Dimensions are needed for layout; still triggers lazy load
        public (int Width, int Height) GetDimensions() => GetReal().GetDimensions();
    }

    // ------------------------------------------------------------------
    // Client
    // ------------------------------------------------------------------
    class Program
    {
        static void DisplayImageInfo(IImage image)
        {
            var (w, h) = image.GetDimensions();
            Console.WriteLine($"  Image dimensions: {w}x{h}");
        }

        static void Main()
        {
            Console.WriteLine("=== Creating image references (no I/O yet) ===");
            IImage hero   = new ImageProxy("/assets/hero-banner.jpg");
            IImage avatar = new ImageProxy("/assets/user-avatar.jpg");

            Console.WriteLine("\n=== Rendering hero image (triggers load) ===");
            hero.Render();

            Console.WriteLine("\n=== Rendering hero image again (no reload) ===");
            hero.Render();

            Console.WriteLine("\n=== Querying hero dimensions ===");
            DisplayImageInfo(hero);

            Console.WriteLine("\n=== Avatar was never rendered — never loaded ===");
            // avatar is never used, so RealImage is never constructed
            Console.WriteLine("  (avatar proxy destroyed without ever loading the file)");
        }
    }
}
```

---

### TypeScript

```typescript
/**
 * Caching Proxy — Real-world scenario: a WeatherService that calls a
 * paid third-party API. The CachingWeatherProxy stores results for a
 * configurable TTL to minimize API costs.
 */

// ------------------------------------------------------------------
// Service Interface
// ------------------------------------------------------------------
interface WeatherService {
  getCurrentWeather(city: string): Promise<WeatherData>;
}

interface WeatherData {
  city: string;
  temperatureC: number;
  condition: string;
  fetchedAt: Date;
}

// ------------------------------------------------------------------
// Real Service — simulates an HTTP call to a paid weather API
// ------------------------------------------------------------------
class RealWeatherService implements WeatherService {
  async getCurrentWeather(city: string): Promise<WeatherData> {
    console.log(`  [RealWeatherService] Calling external API for "${city}" …`);
    // Simulate network delay
    await new Promise((r) => setTimeout(r, 400));
    return {
      city,
      temperatureC: Math.round(15 + Math.random() * 20),
      condition: ["Sunny", "Cloudy", "Rainy"][Math.floor(Math.random() * 3)],
      fetchedAt: new Date(),
    };
  }
}

// ------------------------------------------------------------------
// Caching Proxy
// ------------------------------------------------------------------
class CachingWeatherProxy implements WeatherService {
  private readonly real: WeatherService;
  private readonly cache = new Map<string, { data: WeatherData; expiry: number }>();
  private readonly ttlMs: number;

  constructor(real: WeatherService, ttlSeconds = 30) {
    this.real = real;
    this.ttlMs = ttlSeconds * 1000;
  }

  async getCurrentWeather(city: string): Promise<WeatherData> {
    const normalizedCity = city.toLowerCase().trim();
    const now = Date.now();
    const cached = this.cache.get(normalizedCity);

    if (cached && cached.expiry > now) {
      const remainingSec = ((cached.expiry - now) / 1000).toFixed(1);
      console.log(
        `  [CachingProxy] Cache HIT for "${city}" — expires in ${remainingSec}s`
      );
      return cached.data;
    }

    if (cached) {
      console.log(`  [CachingProxy] Cache EXPIRED for "${city}"`);
    }

    const data = await this.real.getCurrentWeather(city);
    this.cache.set(normalizedCity, { data, expiry: now + this.ttlMs });
    console.log(
      `  [CachingProxy] Stored result for "${city}" (TTL ${this.ttlMs / 1000}s)`
    );
    return data;
  }
}

// ------------------------------------------------------------------
// Client
// ------------------------------------------------------------------
async function displayWeather(svc: WeatherService, city: string): Promise<void> {
  const weather = await svc.getCurrentWeather(city);
  console.log(
    `  ${weather.city}: ${weather.temperatureC}°C, ${weather.condition} ` +
      `(fetched at ${weather.fetchedAt.toISOString()})`
  );
}

(async () => {
  const real  = new RealWeatherService();
  const proxy = new CachingWeatherProxy(real, 5); // 5-second TTL

  console.log("=== Request 1: London (cache miss) ===");
  await displayWeather(proxy, "London");

  console.log("\n=== Request 2: London (cache hit) ===");
  await displayWeather(proxy, "London");

  console.log("\n=== Request 3: Paris (cache miss) ===");
  await displayWeather(proxy, "Paris");

  console.log("\n=== Request 4: LONDON (normalized, cache hit) ===");
  await displayWeather(proxy, "LONDON");
})();
```

---

### Go

```go
// Logging Proxy — Real-world scenario: an OrderRepository that
// reads/writes orders to a database. The LoggingOrderRepository proxy
// wraps each operation with structured log output including duration.
package main

import (
	"fmt"
	"math/rand"
	"time"
)

// ------------------------------------------------------------------
// Domain model
// ------------------------------------------------------------------
type Order struct {
	ID       int
	Customer string
	Total    float64
}

// ------------------------------------------------------------------
// Service Interface
// ------------------------------------------------------------------
type OrderRepository interface {
	FindByID(id int) (*Order, error)
	Save(order *Order) error
	Delete(id int) error
}

// ------------------------------------------------------------------
// Real Service
// ------------------------------------------------------------------
type DatabaseOrderRepository struct{}

func (r *DatabaseOrderRepository) FindByID(id int) (*Order, error) {
	// Simulate DB query latency
	time.Sleep(time.Duration(50+rand.Intn(100)) * time.Millisecond)
	if id <= 0 {
		return nil, fmt.Errorf("order not found: %d", id)
	}
	return &Order{ID: id, Customer: "Alice", Total: 142.50}, nil
}

func (r *DatabaseOrderRepository) Save(order *Order) error {
	time.Sleep(time.Duration(30+rand.Intn(70)) * time.Millisecond)
	fmt.Printf("  [DB] Persisted order id=%d customer=%s total=%.2f\n",
		order.ID, order.Customer, order.Total)
	return nil
}

func (r *DatabaseOrderRepository) Delete(id int) error {
	time.Sleep(time.Duration(20+rand.Intn(50)) * time.Millisecond)
	if id <= 0 {
		return fmt.Errorf("cannot delete order: %d", id)
	}
	fmt.Printf("  [DB] Deleted order id=%d\n", id)
	return nil
}

// ------------------------------------------------------------------
// Logging Proxy
// ------------------------------------------------------------------
type LoggingOrderRepository struct {
	real OrderRepository
}

func NewLoggingOrderRepository(real OrderRepository) *LoggingOrderRepository {
	return &LoggingOrderRepository{real: real}
}

func (l *LoggingOrderRepository) FindByID(id int) (*Order, error) {
	start := time.Now()
	fmt.Printf("[Proxy] FindByID id=%d\n", id)
	result, err := l.real.FindByID(id)
	elapsed := time.Since(start)
	if err != nil {
		fmt.Printf("[Proxy] FindByID FAILED id=%d err=%v duration=%s\n", id, err, elapsed)
	} else {
		fmt.Printf("[Proxy] FindByID OK id=%d duration=%s\n", id, elapsed)
	}
	return result, err
}

func (l *LoggingOrderRepository) Save(order *Order) error {
	start := time.Now()
	fmt.Printf("[Proxy] Save id=%d\n", order.ID)
	err := l.real.Save(order)
	elapsed := time.Since(start)
	if err != nil {
		fmt.Printf("[Proxy] Save FAILED id=%d err=%v duration=%s\n", order.ID, err, elapsed)
	} else {
		fmt.Printf("[Proxy] Save OK id=%d duration=%s\n", order.ID, elapsed)
	}
	return err
}

func (l *LoggingOrderRepository) Delete(id int) error {
	start := time.Now()
	fmt.Printf("[Proxy] Delete id=%d\n", id)
	err := l.real.Delete(id)
	elapsed := time.Since(start)
	if err != nil {
		fmt.Printf("[Proxy] Delete FAILED id=%d err=%v duration=%s\n", id, err, elapsed)
	} else {
		fmt.Printf("[Proxy] Delete OK id=%d duration=%s\n", id, elapsed)
	}
	return err
}

// ------------------------------------------------------------------
// Client
// ------------------------------------------------------------------
func processOrder(repo OrderRepository, id int) {
	order, err := repo.FindByID(id)
	if err != nil {
		fmt.Printf("  Client error: %v\n", err)
		return
	}
	order.Total += 10.00 // add shipping
	_ = repo.Save(order)
}

func main() {
	real  := &DatabaseOrderRepository{}
	proxy := NewLoggingOrderRepository(real)

	fmt.Println("=== Processing valid order ===")
	processOrder(proxy, 42)

	fmt.Println("\n=== Processing invalid order ===")
	processOrder(proxy, -1)

	fmt.Println("\n=== Deleting order ===")
	_ = proxy.Delete(42)
}
```

---

### PHP

```php
<?php
/**
 * Caching Proxy — Real-world scenario: a ProductRepository that queries
 * a slow relational database. The CachingProductRepository wraps it with
 * an in-memory cache so repeated lookups within the same request skip
 * the database entirely.
 */

declare(strict_types=1);

// ------------------------------------------------------------------
// Domain model
// ------------------------------------------------------------------
final class Product
{
    public function __construct(
        public readonly int    $id,
        public readonly string $name,
        public readonly float  $price,
    ) {}
}

// ------------------------------------------------------------------
// Service Interface
// ------------------------------------------------------------------
interface ProductRepository
{
    public function findById(int $id): ?Product;
    public function findAll(): array;
}

// ------------------------------------------------------------------
// Real Service — simulates a slow DB query
// ------------------------------------------------------------------
final class DatabaseProductRepository implements ProductRepository
{
    private array $store = [
        1 => ['name' => 'Laptop',     'price' => 999.99],
        2 => ['name' => 'Headphones', 'price' =>  79.99],
        3 => ['name' => 'Webcam',     'price' =>  49.99],
    ];

    public function findById(int $id): ?Product
    {
        echo "  [DB] SELECT * FROM products WHERE id = {$id}\n";
        usleep(200_000); // simulate 200 ms query

        if (!isset($this->store[$id])) {
            return null;
        }
        return new Product($id, $this->store[$id]['name'], $this->store[$id]['price']);
    }

    public function findAll(): array
    {
        echo "  [DB] SELECT * FROM products\n";
        usleep(500_000); // simulate 500 ms query

        return array_map(
            fn($id, $row) => new Product($id, $row['name'], $row['price']),
            array_keys($this->store),
            array_values($this->store),
        );
    }
}

// ------------------------------------------------------------------
// Caching Proxy
// ------------------------------------------------------------------
final class CachingProductRepository implements ProductRepository
{
    private array $singleCache = [];
    private ?array $allCache   = null;

    public function __construct(private readonly ProductRepository $real) {}

    public function findById(int $id): ?Product
    {
        if (array_key_exists($id, $this->singleCache)) {
            echo "  [Cache] HIT findById({$id})\n";
            return $this->singleCache[$id];
        }

        echo "  [Cache] MISS findById({$id})\n";
        $product = $this->real->findById($id);
        $this->singleCache[$id] = $product;
        return $product;
    }

    public function findAll(): array
    {
        if ($this->allCache !== null) {
            echo "  [Cache] HIT findAll()\n";
            return $this->allCache;
        }

        echo "  [Cache] MISS findAll()\n";
        $this->allCache = $this->real->findAll();
        return $this->allCache;
    }
}

// ------------------------------------------------------------------
// Client
// ------------------------------------------------------------------
function renderProductPage(ProductRepository $repo, int $productId): void
{
    $product = $repo->findById($productId);
    if ($product === null) {
        echo "  Product {$productId} not found.\n";
        return;
    }
    echo "  Showing: {$product->name} — \${$product->price}\n";
}

$real  = new DatabaseProductRepository();
$proxy = new CachingProductRepository($real);

echo "=== First load (cache cold) ===\n";
renderProductPage($proxy, 1);
renderProductPage($proxy, 2);

echo "\n=== Second load (cache warm) ===\n";
renderProductPage($proxy, 1);
renderProductPage($proxy, 2);

echo "\n=== findAll() first call ===\n";
$products = $proxy->findAll();
echo "  Found " . count($products) . " products\n";

echo "\n=== findAll() second call ===\n";
$products = $proxy->findAll();
echo "  Found " . count($products) . " products\n";
```

---

### Ruby

```ruby
# frozen_string_literal: true

# Protection Proxy — Real-world scenario: an AdminService that can
# delete users and export data. Only principals with the :admin role
# may invoke these operations; others receive an AuthorizationError.

# ------------------------------------------------------------------
# Domain
# ------------------------------------------------------------------
AuthorizationError = Class.new(StandardError)

User = Struct.new(:name, :roles, keyword_init: true) do
  def admin? = roles.include?(:admin)
end

# ------------------------------------------------------------------
# Service Interface (duck-typed in Ruby; explicit module for clarity)
# ------------------------------------------------------------------
module AdminService
  def delete_user(user_id) = raise NotImplementedError
  def export_data(format)  = raise NotImplementedError
  def list_users           = raise NotImplementedError
end

# ------------------------------------------------------------------
# Real Service
# ------------------------------------------------------------------
class RealAdminService
  include AdminService

  def delete_user(user_id)
    puts "  [RealAdminService] Deleting user #{user_id} …"
    "User #{user_id} deleted."
  end

  def export_data(format)
    puts "  [RealAdminService] Exporting data as #{format} …"
    "<#{format.upcase} data blob>"
  end

  def list_users
    puts "  [RealAdminService] Fetching user list …"
    ["alice", "bob", "carol"]
  end
end

# ------------------------------------------------------------------
# Protection Proxy
# ------------------------------------------------------------------
class ProtectedAdminService
  include AdminService

  # Operations that require the :admin role
  PROTECTED_OPERATIONS = %i[delete_user export_data].freeze

  def initialize(current_user)
    @current_user = current_user
    @real = RealAdminService.new
  end

  def delete_user(user_id)
    authorize!(:delete_user)
    @real.delete_user(user_id)
  end

  def export_data(format)
    authorize!(:export_data)
    @real.export_data(format)
  end

  # list_users is available to all authenticated users
  def list_users
    puts "  [Proxy] #{@current_user.name} listing users (allowed)"
    @real.list_users
  end

  private

  def authorize!(operation)
    if PROTECTED_OPERATIONS.include?(operation) && !@current_user.admin?
      raise AuthorizationError,
            "User '#{@current_user.name}' is not authorized to perform '#{operation}'"
    end
    puts "  [Proxy] #{@current_user.name} authorized for '#{operation}'"
  end
end

# ------------------------------------------------------------------
# Client
# ------------------------------------------------------------------
def run_as(service)
  puts "  Listing users:"
  p service.list_users

  puts "  Deleting user 42:"
  result = service.delete_user(42)
  puts "  Result: #{result}"

  puts "  Exporting CSV:"
  blob = service.export_data(:csv)
  puts "  Blob: #{blob}"
rescue AuthorizationError => e
  puts "  ACCESS DENIED: #{e.message}"
end

viewer = User.new(name: "alice", roles: [:viewer])
admin  = User.new(name: "bob",   roles: [:viewer, :admin])

puts "=== Viewer session ==="
run_as(ProtectedAdminService.new(viewer))

puts "\n=== Admin session ==="
run_as(ProtectedAdminService.new(admin))
```

---

## When To Use

| Scenario | Proxy Type | Description |
|---|---|---|
| **Lazy initialization** | Virtual Proxy | The real object is heavyweight (large file, DB connection). Create it only when first accessed. |
| **Access control** | Protection Proxy | Different callers should have different permissions. The proxy checks credentials before forwarding. |
| **Remote resources** | Remote Proxy | The real service lives in another process or machine. The proxy handles marshalling and network transport (classic RPC/CORBA use case). |
| **Logging / auditing** | Logging Proxy | Record every request (caller, arguments, timestamp, duration) without touching the real service. |
| **Caching** | Caching Proxy | Identical requests to a slow or expensive service return stored results. TTL logic lives in the proxy. |
| **Smart reference** | Smart Reference | Free a heavyweight object when no clients hold references; track whether the object has been modified. |

Use the Proxy pattern when you want to add behaviour around an object without modifying it, and when you need the wrapper to be transparent to callers (same interface).

---

## Pros & Cons

### Pros

- **Transparency:** Clients use the proxy through the same interface as the real object; no client code changes are required.
- **Single Responsibility:** Cross-cutting concerns (caching, logging, auth) live in the proxy, not in the real service.
- **Open/Closed Principle:** New proxy types can be introduced without changing existing clients or the real service.
- **Lifecycle management:** The proxy can control when the real object is created and destroyed.
- **Resilience:** A proxy can return cached data when the real service is unavailable, preventing cascading failures.

### Cons

- **Increased complexity:** Every proxied service requires at least one additional class; large systems can accumulate many proxy classes.
- **Latency overhead:** The extra indirection through the proxy adds a (usually tiny) processing cost on each call.
- **Potential staleness:** Caching proxies can serve stale data if TTL logic is poorly configured.
- **Risk of obscuring failures:** A proxy that silently absorbs errors (e.g., returning cached data when a real error should surface) can hide bugs.
- **Interface coupling:** If the ServiceInterface changes, both RealService and all proxies must be updated.

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Adapter** | An Adapter provides a *different* interface to the wrapped object; a Proxy provides the *same* interface. Use Adapter when the client and service interfaces are incompatible; use Proxy when they are compatible and you want to intercept calls. |
| **Decorator** | Decorator and Proxy share identical structure (both wrap an object through the same interface), but their intent differs. A Decorator *adds* behaviour dynamically and is designed to be composed in chains. A Proxy *controls access* to an existing object and typically does not support chaining in the same way. In practice, a Caching or Logging Proxy can look very much like a Decorator — the design intent is what separates them conceptually. |
| **Facade** | Facade provides a simplified interface to a *subsystem* (many classes); Proxy wraps a *single* object and preserves its interface. Facade reduces complexity; Proxy adds a control layer. |

---

## Sources

- https://refactoring.guru/design-patterns/proxy
- https://sourcemaking.com/design_patterns/proxy
