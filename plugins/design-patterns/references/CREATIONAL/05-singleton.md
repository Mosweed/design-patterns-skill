# Singleton Pattern

**Category:** Creational  
**Also Known As:** Single Instance

---

## Intent

Ensure that a class has only **one instance**, while providing a **global access point** to that instance. Singletons are used when exactly one object is needed to coordinate actions across a system.

---

## Problem It Solves

Many real-world resources must exist as a single, shared object:

- A **configuration manager** that reads settings once and exposes them everywhere.
- A **connection pool** that manages a finite set of database connections.
- A **logger** that writes to a single file or stream without interleaving output.
- A **thread pool**, **registry**, or **event bus**.

The naive solution is to use a **global variable**. However, global variables are unsafe because:

1. Any code anywhere can **overwrite** the reference.
2. They do not prevent the creation of **multiple instances** via `new`.
3. They pollute the global namespace and create invisible coupling.

You need a mechanism that **guarantees** one instance exists, enforces it at the language level, and exposes a clean access point without exposing the constructor.

---

## Solution

1. **Make the default constructor private.** This prevents any external code from calling `new Singleton()` and accidentally creating a second instance.
2. **Declare a private static field** to hold the single instance.
3. **Provide a public static factory method** (conventionally `getInstance()` or `instance()`). This method checks whether the static field is already populated:
   - If **not**, it calls the private constructor, stores the result, and returns it.
   - If **yes**, it returns the cached instance immediately.

All callers obtain their reference through the factory method, so the object is created at most once (lazy initialization).

---

## Structure (ASCII diagram)

```
┌──────────────────────────────────────────────────┐
│                    Singleton                     │
├──────────────────────────────────────────────────┤
│  - instance : Singleton   (private static)       │
│  - [other private fields]                        │
├──────────────────────────────────────────────────┤
│  - Singleton()            (private constructor)  │
│  + getInstance() : Singleton  (public static)    │
│  + [other public methods]                        │
└──────────────────────────────────────────────────┘

  Client A ──┐
             ├──► Singleton.getInstance() ──► same object ◄─┐
  Client B ──┘                                               │
                                                             │
  Client C ──────► Singleton.getInstance() ─────────────────┘
```

The key invariant: no matter how many times or from how many call sites `getInstance()` is invoked, it always returns the **same** object reference.

---

## Participants

| Participant   | Role                                                                                                                              |
|---------------|-----------------------------------------------------------------------------------------------------------------------------------|
| **Singleton** | Defines the `getInstance()` static method that lets clients access the unique instance. Responsible for creating its own unique instance and for keeping clients from constructing additional ones. |
| **Client**    | Accesses the Singleton only through `getInstance()`. Never constructs the object directly.                                        |

---

## How It Works (step-by-step)

1. **Class is loaded.** The static `instance` field is initialised to `null` (or equivalent unset state).
2. **First client calls `getInstance()`.**
   - The method checks: is `instance == null`?
   - Yes — it calls the **private constructor**, which allocates memory and initialises the object.
   - The new object is stored in the static `instance` field.
   - The object is returned.
3. **Subsequent clients call `getInstance()`.**
   - The method checks: is `instance == null`?
   - No — it immediately returns the already-stored object.
4. **No client can call `new Singleton()` directly** because the constructor is private; the compiler/runtime rejects it.
5. **Thread safety (multithreaded environments):** Without extra care, two threads could both see `instance == null` simultaneously and each call the constructor. Solutions include:
   - **Eager initialisation** — create the instance at class-load time.
   - **Synchronized / locked block** — wrap the null-check and construction in a mutex.
   - **Double-checked locking** — check twice (once without lock, once with) to avoid locking on every call after initialisation.
   - **Initialization-on-demand holder** (Java) / `once.Do` (Go) / module-level variable (Python).

---

## Code Examples

### Python

```python
"""
Singleton Pattern — Application Configuration Manager

A real-world scenario: a ConfigManager that loads settings from a file
once and provides read access to all parts of the application.
Thread-safe via threading.Lock with double-checked locking.
"""

import json
import threading
from pathlib import Path
from typing import Any


class ConfigManager:
    """
    Thread-safe Singleton configuration manager.

    Usage:
        cfg = ConfigManager.get_instance("config.json")
        db_url = cfg.get("database.url")
    """

    _instance: "ConfigManager | None" = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, config_path: str) -> None:
        # Guard: direct instantiation is not allowed after the first call.
        if ConfigManager._instance is not None:
            raise RuntimeError(
                "Use ConfigManager.get_instance() instead of the constructor."
            )
        self._config_path = Path(config_path)
        self._settings: dict[str, Any] = {}
        self._load()

    # ------------------------------------------------------------------ #
    #  Factory method                                                       #
    # ------------------------------------------------------------------ #

    @classmethod
    def get_instance(cls, config_path: str = "config.json") -> "ConfigManager":
        """Return the singleton instance, creating it on first call."""
        if cls._instance is None:                  # First check (no lock)
            with cls._lock:                        # Acquire lock
                if cls._instance is None:          # Second check (with lock)
                    cls._instance = cls.__new__(cls)
                    cls._instance._config_path = Path(config_path)
                    cls._instance._settings = {}
                    cls._instance._load()
        return cls._instance

    # ------------------------------------------------------------------ #
    #  Public interface                                                     #
    # ------------------------------------------------------------------ #

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value by dot-separated key path.
        e.g. cfg.get("database.host") looks up settings["database"]["host"].
        """
        keys = key.split(".")
        value: Any = self._settings
        for k in keys:
            if not isinstance(value, dict) or k not in value:
                return default
            value = value[k]
        return value

    def reload(self) -> None:
        """Re-read configuration from disk (useful after hot-reload)."""
        with self._lock:
            self._load()

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _load(self) -> None:
        if self._config_path.exists():
            with open(self._config_path, encoding="utf-8") as fh:
                self._settings = json.load(fh)
        else:
            # Sensible defaults when no file is present
            self._settings = {
                "database": {"host": "localhost", "port": 5432, "name": "app_db"},
                "cache": {"ttl": 300, "max_size": 1000},
                "logging": {"level": "INFO", "file": "app.log"},
            }

    def __repr__(self) -> str:  # pragma: no cover
        return f"ConfigManager(path={self._config_path!r})"


# ------------------------------------------------------------------ #
#  Demo                                                                #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    # Both variables point to the exact same object.
    cfg1 = ConfigManager.get_instance()
    cfg2 = ConfigManager.get_instance()

    assert cfg1 is cfg2, "Singleton guarantee violated!"
    print("cfg1 is cfg2:", cfg1 is cfg2)  # True

    print("DB host:", cfg1.get("database.host"))    # localhost
    print("Log level:", cfg2.get("logging.level"))  # INFO
    print("Missing key:", cfg1.get("app.secret", "N/A"))  # N/A
```

---

### Java

```java
/**
 * Singleton Pattern — Database Connection Pool
 *
 * A thread-safe Singleton that manages a pool of JDBC connections.
 * Uses the "Initialization-on-Demand Holder" (Bill Pugh) idiom:
 * the inner static class is loaded lazily and initialised exactly once
 * by the JVM class-loader, giving us thread safety without synchronization
 * on the hot path.
 */
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.util.ArrayDeque;
import java.util.Deque;

public final class ConnectionPool {

    // ------------------------------------------------------------------ //
    //  Configuration                                                        //
    // ------------------------------------------------------------------ //
    private static final String JDBC_URL  = "jdbc:postgresql://localhost:5432/app_db";
    private static final String DB_USER   = "app_user";
    private static final String DB_PASS   = "s3cr3t";
    private static final int    POOL_SIZE = 10;

    // ------------------------------------------------------------------ //
    //  State                                                                //
    // ------------------------------------------------------------------ //
    private final Deque<Connection> availableConnections = new ArrayDeque<>();
    private int totalCreated = 0;

    // ------------------------------------------------------------------ //
    //  Private constructor — external code cannot call new ConnectionPool() //
    // ------------------------------------------------------------------ //
    private ConnectionPool() {
        // Pre-warm the pool with a few connections.
        for (int i = 0; i < Math.min(2, POOL_SIZE); i++) {
            try {
                availableConnections.push(createConnection());
            } catch (SQLException e) {
                System.err.println("Warning: could not pre-warm connection: " + e.getMessage());
            }
        }
    }

    // ------------------------------------------------------------------ //
    //  Initialization-on-Demand Holder — lazy, thread-safe, no locking    //
    // ------------------------------------------------------------------ //
    private static final class Holder {
        private static final ConnectionPool INSTANCE = new ConnectionPool();
    }

    /** Returns the singleton ConnectionPool. */
    public static ConnectionPool getInstance() {
        return Holder.INSTANCE;
    }

    // ------------------------------------------------------------------ //
    //  Public API                                                           //
    // ------------------------------------------------------------------ //

    /**
     * Borrow a connection from the pool.
     * Creates a new one if the pool is empty and capacity allows.
     */
    public synchronized Connection acquire() throws SQLException {
        if (!availableConnections.isEmpty()) {
            return availableConnections.pop();
        }
        if (totalCreated < POOL_SIZE) {
            return createConnection();
        }
        throw new SQLException("Connection pool exhausted. All " + POOL_SIZE + " connections are in use.");
    }

    /**
     * Return a connection back to the pool.
     * If the connection is broken, it is discarded and a fresh one is created.
     */
    public synchronized void release(Connection conn) {
        try {
            if (conn != null && !conn.isClosed()) {
                availableConnections.push(conn);
                return;
            }
        } catch (SQLException ignored) { /* fall through */ }

        // Replace the broken connection.
        totalCreated--;
        try {
            availableConnections.push(createConnection());
        } catch (SQLException e) {
            System.err.println("Failed to replace broken connection: " + e.getMessage());
        }
    }

    public synchronized int availableCount() {
        return availableConnections.size();
    }

    // ------------------------------------------------------------------ //
    //  Private helpers                                                      //
    // ------------------------------------------------------------------ //

    private Connection createConnection() throws SQLException {
        Connection conn = DriverManager.getConnection(JDBC_URL, DB_USER, DB_PASS);
        totalCreated++;
        return conn;
    }

    // ------------------------------------------------------------------ //
    //  Demo main                                                            //
    // ------------------------------------------------------------------ //
    public static void main(String[] args) {
        ConnectionPool pool1 = ConnectionPool.getInstance();
        ConnectionPool pool2 = ConnectionPool.getInstance();

        // Both references point to the same object.
        System.out.println("Same instance: " + (pool1 == pool2)); // true

        // Usage pattern (actual DB connection skipped in demo):
        System.out.println("Pool is ready. Available slots: " + pool1.availableCount());
    }
}
```

---

### C++

```cpp
/**
 * Singleton Pattern — Application Logger
 *
 * A thread-safe logger singleton using C++11 "magic statics":
 * local static variables are initialised exactly once, even in the
 * presence of concurrent calls (guaranteed by the C++11 standard).
 *
 * Compile: g++ -std=c++17 -pthread -o logger logger.cpp
 */

#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <sstream>
#include <string>

enum class LogLevel { DEBUG, INFO, WARNING, ERROR, CRITICAL };

class Logger {
public:
    // ---------------------------------------------------------------- //
    //  Factory method — returns the one and only Logger instance.       //
    //  C++11 "magic static": thread-safe without explicit locking.      //
    // ---------------------------------------------------------------- //
    static Logger& getInstance(const std::string& logFile = "app.log") {
        static Logger instance(logFile);  // Constructed exactly once.
        return instance;
    }

    // Prevent copy and move so no second instance can be obtained.
    Logger(const Logger&)            = delete;
    Logger& operator=(const Logger&) = delete;
    Logger(Logger&&)                 = delete;
    Logger& operator=(Logger&&)      = delete;

    // ---------------------------------------------------------------- //
    //  Public logging API                                                //
    // ---------------------------------------------------------------- //
    void debug   (const std::string& msg) { log(LogLevel::DEBUG,    msg); }
    void info    (const std::string& msg) { log(LogLevel::INFO,     msg); }
    void warning (const std::string& msg) { log(LogLevel::WARNING,  msg); }
    void error   (const std::string& msg) { log(LogLevel::ERROR,    msg); }
    void critical(const std::string& msg) { log(LogLevel::CRITICAL, msg); }

    void setMinLevel(LogLevel level) {
        std::lock_guard<std::mutex> lock(mutex_);
        minLevel_ = level;
    }

private:
    // ---------------------------------------------------------------- //
    //  Private constructor                                               //
    // ---------------------------------------------------------------- //
    explicit Logger(const std::string& logFile)
        : minLevel_(LogLevel::DEBUG)
    {
        file_.open(logFile, std::ios::app);
        if (!file_.is_open()) {
            std::cerr << "[Logger] Could not open log file: " << logFile << "\n";
        }
        info("Logger initialised. Log file: " + logFile);
    }

    ~Logger() {
        if (file_.is_open()) file_.close();
    }

    // ---------------------------------------------------------------- //
    //  Internals                                                         //
    // ---------------------------------------------------------------- //
    void log(LogLevel level, const std::string& msg) {
        if (level < minLevel_) return;

        std::lock_guard<std::mutex> lock(mutex_);
        const std::string entry = timestamp() + " [" + levelName(level) + "] " + msg;

        // Write to both the log file and stdout.
        if (file_.is_open()) file_ << entry << "\n" << std::flush;
        std::cout << entry << "\n";
    }

    static std::string timestamp() {
        using namespace std::chrono;
        auto now  = system_clock::now();
        auto time = system_clock::to_time_t(now);
        std::ostringstream oss;
        oss << std::put_time(std::localtime(&time), "%Y-%m-%d %H:%M:%S");
        return oss.str();
    }

    static std::string levelName(LogLevel level) {
        switch (level) {
            case LogLevel::DEBUG:    return "DEBUG";
            case LogLevel::INFO:     return "INFO ";
            case LogLevel::WARNING:  return "WARN ";
            case LogLevel::ERROR:    return "ERROR";
            case LogLevel::CRITICAL: return "CRIT ";
        }
        return "?????";
    }

    std::ofstream file_;
    std::mutex    mutex_;
    LogLevel      minLevel_;
};

// -------------------------------------------------------------------- //
//  Demo                                                                  //
// -------------------------------------------------------------------- //
int main() {
    Logger& log1 = Logger::getInstance();
    Logger& log2 = Logger::getInstance("app.log"); // Same instance returned.

    std::cout << "Same instance: " << (&log1 == &log2 ? "yes" : "no") << "\n";

    log1.info("Application started.");
    log2.warning("Disk usage above 80%.");
    log1.setMinLevel(LogLevel::WARNING);
    log1.debug("This message is suppressed by the min level filter.");
    log2.error("Failed to connect to payment gateway.");
    log1.critical("Out of memory — shutting down.");

    return 0;
}
```

---

### C#

```csharp
/**
 * Singleton Pattern — Application Settings Service
 *
 * Uses the .NET Lazy<T> class for guaranteed thread-safe lazy initialisation
 * with no explicit locking code. Lazy<T> uses LazyThreadSafetyMode.ExecutionAndPublication
 * by default, which handles all concurrent-call edge cases correctly.
 */

using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Threading;

namespace DesignPatterns.Creational
{
    /// <summary>
    /// Thread-safe Singleton that manages application settings.
    /// The single instance is created on first access via the Lazy wrapper.
    /// </summary>
    public sealed class AppSettings
    {
        // ---------------------------------------------------------------- //
        //  Singleton plumbing                                               //
        // ---------------------------------------------------------------- //

        // Lazy<T> ensures the factory delegate runs exactly once,
        // even if multiple threads race to access Instance simultaneously.
        private static readonly Lazy<AppSettings> _lazy =
            new Lazy<AppSettings>(() => new AppSettings(), LazyThreadSafetyMode.ExecutionAndPublication);

        /// <summary>Returns the single AppSettings instance.</summary>
        public static AppSettings Instance => _lazy.Value;

        // Prevent subclassing and external construction.
        private AppSettings()
        {
            _settings = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            Load();
        }

        // ---------------------------------------------------------------- //
        //  State                                                            //
        // ---------------------------------------------------------------- //

        private readonly Dictionary<string, string> _settings;
        private readonly ReaderWriterLockSlim _rwLock = new ReaderWriterLockSlim();
        private const string DefaultPath = "appsettings.json";

        // ---------------------------------------------------------------- //
        //  Public API                                                       //
        // ---------------------------------------------------------------- //

        /// <summary>Retrieve a setting value, or <paramref name="defaultValue"/> if absent.</summary>
        public string Get(string key, string defaultValue = "")
        {
            _rwLock.EnterReadLock();
            try
            {
                return _settings.TryGetValue(key, out var value) ? value : defaultValue;
            }
            finally { _rwLock.ExitReadLock(); }
        }

        /// <summary>Persist an in-memory override (does not write to disk).</summary>
        public void Set(string key, string value)
        {
            _rwLock.EnterWriteLock();
            try { _settings[key] = value; }
            finally { _rwLock.ExitWriteLock(); }
        }

        /// <summary>Reload settings from disk.</summary>
        public void Reload() => Load();

        // ---------------------------------------------------------------- //
        //  Private helpers                                                  //
        // ---------------------------------------------------------------- //

        private void Load()
        {
            _rwLock.EnterWriteLock();
            try
            {
                _settings.Clear();

                if (!File.Exists(DefaultPath))
                {
                    // Sensible defaults when no file is present.
                    _settings["Database:Host"]   = "localhost";
                    _settings["Database:Port"]   = "5432";
                    _settings["Cache:Ttl"]       = "300";
                    _settings["Logging:Level"]   = "Information";
                    return;
                }

                var json = File.ReadAllText(DefaultPath);
                var doc  = JsonDocument.Parse(json);
                Flatten(doc.RootElement, prefix: "", _settings);
            }
            finally { _rwLock.ExitWriteLock(); }
        }

        /// <summary>Recursively flatten a JSON object into colon-delimited keys.</summary>
        private static void Flatten(JsonElement element, string prefix, Dictionary<string, string> result)
        {
            foreach (var prop in element.EnumerateObject())
            {
                var key = string.IsNullOrEmpty(prefix) ? prop.Name : $"{prefix}:{prop.Name}";
                if (prop.Value.ValueKind == JsonValueKind.Object)
                    Flatten(prop.Value, key, result);
                else
                    result[key] = prop.Value.ToString();
            }
        }
    }

    // -------------------------------------------------------------------- //
    //  Demo                                                                  //
    // -------------------------------------------------------------------- //
    internal static class Program
    {
        private static void Main()
        {
            var settings1 = AppSettings.Instance;
            var settings2 = AppSettings.Instance;

            Console.WriteLine($"Same instance: {ReferenceEquals(settings1, settings2)}"); // True

            Console.WriteLine($"DB Host:    {settings1.Get("Database:Host")}");
            Console.WriteLine($"Log Level:  {settings2.Get("Logging:Level")}");

            // Override at runtime without touching the file.
            settings1.Set("FeatureFlags:DarkMode", "true");
            Console.WriteLine($"Dark mode:  {settings2.Get("FeatureFlags:DarkMode")}");  // true
        }
    }
}
```

---

### TypeScript

```typescript
/**
 * Singleton Pattern — HTTP API Client
 *
 * A real-world scenario: a single Axios-based HTTP client shared across
 * all service modules. Avoids spinning up a new client (with its own
 * connection pool and interceptors) on every request.
 *
 * Run: ts-node api-client.ts  (requires axios: npm i axios)
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from "axios";

interface RetryConfig {
  maxRetries: number;
  retryDelay: number; // ms
}

class ApiClient {
  // ------------------------------------------------------------------ //
  //  Singleton state                                                      //
  // ------------------------------------------------------------------ //
  private static instance: ApiClient | null = null;

  private readonly http: AxiosInstance;
  private requestCount = 0;

  // ------------------------------------------------------------------ //
  //  Private constructor                                                  //
  // ------------------------------------------------------------------ //
  private constructor(
    baseURL: string,
    private readonly retry: RetryConfig = { maxRetries: 3, retryDelay: 500 }
  ) {
    this.http = axios.create({
      baseURL,
      timeout: 10_000,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    });

    // Request interceptor — attach auth token & track call count.
    this.http.interceptors.request.use((config) => {
      this.requestCount++;
      const token = process.env.API_TOKEN;
      if (token) config.headers.Authorization = `Bearer ${token}`;
      return config;
    });

    // Response interceptor — unwrap data layer.
    this.http.interceptors.response.use(
      (response) => response,
      async (error) => {
        const config = error.config as AxiosRequestConfig & { _retries?: number };
        config._retries = config._retries ?? 0;

        const isRetriable =
          error.response?.status >= 500 &&
          config._retries < this.retry.maxRetries;

        if (isRetriable) {
          config._retries++;
          await delay(this.retry.retryDelay * config._retries);
          return this.http.request(config);
        }
        return Promise.reject(error);
      }
    );
  }

  // ------------------------------------------------------------------ //
  //  Factory method                                                       //
  // ------------------------------------------------------------------ //
  static getInstance(
    baseURL = process.env.API_BASE_URL ?? "https://jsonplaceholder.typicode.com"
  ): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient(baseURL);
    }
    return ApiClient.instance;
  }

  // ------------------------------------------------------------------ //
  //  Public API                                                           //
  // ------------------------------------------------------------------ //
  async get<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.http.get(path, config);
    return response.data;
  }

  async post<T>(path: string, body: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.http.post(path, body, config);
    return response.data;
  }

  get totalRequests(): number {
    return this.requestCount;
  }
}

// -------------------------------------------------------------------- //
//  Helpers                                                               //
// -------------------------------------------------------------------- //
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// -------------------------------------------------------------------- //
//  Demo                                                                  //
// -------------------------------------------------------------------- //
async function main() {
  const client1 = ApiClient.getInstance();
  const client2 = ApiClient.getInstance();

  console.log("Same instance:", client1 === client2); // true

  interface Post { id: number; title: string; body: string; userId: number }

  const post = await client1.get<Post>("/posts/1");
  console.log("Fetched post:", post.title);

  const newPost = await client2.post<Post>("/posts", {
    title: "Singleton in Practice",
    body: "One instance to rule them all.",
    userId: 1,
  });
  console.log("Created post id:", newPost.id);
  console.log("Total requests made:", client1.totalRequests); // 2
}

main().catch(console.error);
```

---

### Go

```go
// Singleton Pattern — Metrics Collector
//
// A real-world scenario: a centralized metrics aggregator used by
// multiple goroutines. Uses sync.Once for guaranteed single initialisation.
//
// Run: go run metrics.go

package main

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// -------------------------------------------------------------------- //
//  Metrics types                                                          //
// -------------------------------------------------------------------- //

// Counter is an atomically incrementable metric.
type Counter struct {
	name  string
	value int64
}

func (c *Counter) Inc() { atomic.AddInt64(&c.value, 1) }
func (c *Counter) Add(n int64) { atomic.AddInt64(&c.value, n) }
func (c *Counter) Value() int64 { return atomic.LoadInt64(&c.value) }

// -------------------------------------------------------------------- //
//  Singleton: MetricsCollector                                            //
// -------------------------------------------------------------------- //

// MetricsCollector aggregates application counters.
// It is safe for concurrent use from multiple goroutines.
type MetricsCollector struct {
	mu       sync.RWMutex
	counters map[string]*Counter
	startedAt time.Time
}

var (
	collectorInstance *MetricsCollector
	once              sync.Once // Guarantees single initialisation.
)

// GetCollector returns the singleton MetricsCollector.
// sync.Once ensures the initialisation runs exactly once,
// even under heavy concurrent access — no explicit mutex needed.
func GetCollector() *MetricsCollector {
	once.Do(func() {
		collectorInstance = &MetricsCollector{
			counters:  make(map[string]*Counter),
			startedAt: time.Now(),
		}
	})
	return collectorInstance
}

// -------------------------------------------------------------------- //
//  Public API                                                             //
// -------------------------------------------------------------------- //

// Inc increments a named counter by 1.
func (mc *MetricsCollector) Inc(name string) {
	mc.counter(name).Inc()
}

// Add increments a named counter by n.
func (mc *MetricsCollector) Add(name string, n int64) {
	mc.counter(name).Add(n)
}

// Get returns the current value of a named counter.
func (mc *MetricsCollector) Get(name string) int64 {
	mc.mu.RLock()
	c, ok := mc.counters[name]
	mc.mu.RUnlock()
	if !ok {
		return 0
	}
	return c.Value()
}

// Snapshot returns a point-in-time copy of all counters.
func (mc *MetricsCollector) Snapshot() map[string]int64 {
	mc.mu.RLock()
	defer mc.mu.RUnlock()
	snap := make(map[string]int64, len(mc.counters))
	for name, c := range mc.counters {
		snap[name] = c.Value()
	}
	return snap
}

// Uptime returns how long the collector (and thus the application) has been running.
func (mc *MetricsCollector) Uptime() time.Duration {
	return time.Since(mc.startedAt)
}

// -------------------------------------------------------------------- //
//  Private helpers                                                        //
// -------------------------------------------------------------------- //

func (mc *MetricsCollector) counter(name string) *Counter {
	mc.mu.RLock()
	c, ok := mc.counters[name]
	mc.mu.RUnlock()
	if ok {
		return c
	}
	// Counter not found — create it under a write lock.
	mc.mu.Lock()
	defer mc.mu.Unlock()
	// Re-check after acquiring the write lock (another goroutine may have
	// created the counter between the RLock release and WLock acquisition).
	if c, ok = mc.counters[name]; ok {
		return c
	}
	c = &Counter{name: name}
	mc.counters[name] = c
	return c
}

// -------------------------------------------------------------------- //
//  Demo                                                                   //
// -------------------------------------------------------------------- //

func main() {
	col1 := GetCollector()
	col2 := GetCollector()

	fmt.Printf("Same instance: %v\n", col1 == col2) // true

	// Simulate concurrent usage from multiple goroutines.
	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			GetCollector().Inc("http.requests")
			GetCollector().Inc("http.requests")
			GetCollector().Inc("db.queries")
		}()
	}
	wg.Wait()

	snap := col1.Snapshot()
	fmt.Printf("http.requests: %d (expected 200)\n", snap["http.requests"])
	fmt.Printf("db.queries:    %d (expected 100)\n", snap["db.queries"])
	fmt.Printf("Uptime: %v\n", col2.Uptime().Round(time.Millisecond))
}
```

---

### PHP

```php
<?php

declare(strict_types=1);

/**
 * Singleton Pattern — Cache Manager
 *
 * A real-world scenario: a PSR-16 inspired in-process cache backed by a
 * simple array store. One shared instance prevents duplicate hydration
 * across multiple service classes in the same request lifecycle.
 *
 * Run: php cache-manager.php
 */

class CacheManager
{
    // ---------------------------------------------------------------- //
    //  Singleton plumbing                                                //
    // ---------------------------------------------------------------- //

    private static ?CacheManager $instance = null;

    /**
     * Private constructor — external code cannot call new CacheManager().
     */
    private function __construct(private readonly int $defaultTtl = 300)
    {
        // Initialise storage.
        $this->store    = [];
        $this->expiries = [];
        $this->hits     = 0;
        $this->misses   = 0;
    }

    /** Prevent cloning of the singleton. */
    private function __clone() {}

    /** Prevent unserialising into a second instance. */
    public function __wakeup(): void
    {
        throw new \RuntimeException('Cannot unserialize a Singleton.');
    }

    /**
     * Returns the singleton CacheManager instance.
     */
    public static function getInstance(int $defaultTtl = 300): self
    {
        if (self::$instance === null) {
            self::$instance = new self($defaultTtl);
        }
        return self::$instance;
    }

    // ---------------------------------------------------------------- //
    //  State                                                             //
    // ---------------------------------------------------------------- //

    /** @var array<string, mixed> */
    private array $store;

    /** @var array<string, float> Unix timestamps when each key expires. */
    private array $expiries;

    private int $hits;
    private int $misses;

    // ---------------------------------------------------------------- //
    //  Public API                                                        //
    // ---------------------------------------------------------------- //

    /**
     * Store a value under $key for $ttl seconds (default: constructor TTL).
     *
     * @param mixed $value Any serialisable value.
     */
    public function set(string $key, mixed $value, ?int $ttl = null): void
    {
        $this->store[$key]    = $value;
        $this->expiries[$key] = microtime(true) + ($ttl ?? $this->defaultTtl);
    }

    /**
     * Retrieve a cached value, or $default if absent/expired.
     *
     * @param mixed $default
     * @return mixed
     */
    public function get(string $key, mixed $default = null): mixed
    {
        if (!$this->has($key)) {
            $this->misses++;
            return $default;
        }
        $this->hits++;
        return $this->store[$key];
    }

    /**
     * Check whether a non-expired entry exists for $key.
     */
    public function has(string $key): bool
    {
        if (!isset($this->store[$key])) {
            return false;
        }
        if (microtime(true) > $this->expiries[$key]) {
            $this->delete($key); // Lazy eviction on read.
            return false;
        }
        return true;
    }

    /**
     * Remove a key from the cache.
     */
    public function delete(string $key): void
    {
        unset($this->store[$key], $this->expiries[$key]);
    }

    /**
     * Flush the entire cache.
     */
    public function clear(): void
    {
        $this->store    = [];
        $this->expiries = [];
    }

    /**
     * Return cache statistics.
     *
     * @return array{hits: int, misses: int, keys: int, hit_rate: float}
     */
    public function stats(): array
    {
        $total = $this->hits + $this->misses;
        return [
            'hits'     => $this->hits,
            'misses'   => $this->misses,
            'keys'     => count($this->store),
            'hit_rate' => $total > 0 ? round($this->hits / $total * 100, 1) : 0.0,
        ];
    }
}


// -------------------------------------------------------------------- //
//  Demo                                                                   //
// -------------------------------------------------------------------- //

$cache1 = CacheManager::getInstance();
$cache2 = CacheManager::getInstance();

// Both variables reference the same object.
var_dump($cache1 === $cache2); // bool(true)

// Simulate a service that caches a database query result.
$userKey = 'user:42';

if (!$cache1->has($userKey)) {
    // Expensive DB fetch (simulated).
    $user = ['id' => 42, 'name' => 'Alice', 'email' => 'alice@example.com'];
    $cache1->set($userKey, $user, ttl: 60);
    echo "Cache MISS — loaded from DB\n";
} else {
    echo "Cache HIT\n";
}

// Second access (via $cache2, but same instance) — will be a hit.
$cached = $cache2->get($userKey);
echo "User name: {$cached['name']}\n";

print_r($cache1->stats());
// Array ( [hits] => 1 [misses] => 1 [keys] => 1 [hit_rate] => 50 )
```

---

### Ruby

```ruby
# Singleton Pattern — Feature Flag Registry
#
# A real-world scenario: a centralized feature-flag store consulted by
# multiple parts of a Rails-like application. Ruby's standard library
# includes a Singleton module — we use it here and then extend it with
# a realistic API.
#
# Run: ruby feature_flags.rb

require 'singleton'  # Part of Ruby's standard library.
require 'json'
require 'monitor'    # Re-entrant mutex, safe for nested calls.

class FeatureFlagRegistry
  # Including Singleton:
  #  - Makes .new private.
  #  - Provides .instance as the single accessor.
  #  - The instance is created lazily on first call to .instance.
  include Singleton

  FLAG_FILE = 'feature_flags.json'.freeze

  def initialize
    @monitor = Monitor.new
    @flags   = {}
    @overrides = {}
    load_from_file
  end

  # ------------------------------------------------------------------
  #  Public API
  # ------------------------------------------------------------------

  # Returns true if the named flag is enabled for the given context.
  # @param name    [Symbol, String]  Flag identifier, e.g. :dark_mode
  # @param context [Hash]            Optional: { user_id:, role:, ... }
  def enabled?(name, context = {})
    key = name.to_sym
    @monitor.synchronize do
      # In-memory overrides take highest precedence (useful in tests).
      return @overrides[key] if @overrides.key?(key)

      flag = @flags[key]
      return false unless flag

      # Support percentage rollouts: enable for X% of users.
      if flag[:rollout] && context[:user_id]
        return (context[:user_id].hash % 100) < flag[:rollout]
      end

      !!flag[:enabled]
    end
  end

  # Override a flag at runtime (does not persist to disk).
  def override(name, value)
    @monitor.synchronize { @overrides[name.to_sym] = !!value }
  end

  # Clear a runtime override.
  def clear_override(name)
    @monitor.synchronize { @overrides.delete(name.to_sym) }
  end

  # Reload flags from disk (e.g. after a deployment).
  def reload
    @monitor.synchronize { load_from_file }
  end

  # Returns a snapshot of all flags and their current state.
  def all
    @monitor.synchronize { @flags.merge(@overrides) }
  end

  # ------------------------------------------------------------------
  #  Private helpers
  # ------------------------------------------------------------------
  private

  def load_from_file
    if File.exist?(FLAG_FILE)
      raw = JSON.parse(File.read(FLAG_FILE), symbolize_names: true)
      # Expect: { dark_mode: { enabled: true }, new_checkout: { rollout: 20 } }
      @flags = raw
    else
      # Sensible defaults when no file is present.
      @flags = {
        dark_mode:      { enabled: false },
        new_checkout:   { enabled: true  },
        beta_dashboard: { enabled: false, rollout: 10 },
        ai_assistant:   { enabled: true  }
      }
    end
  end
end

# --------------------------------------------------------------------
#  Demo
# --------------------------------------------------------------------

registry1 = FeatureFlagRegistry.instance
registry2 = FeatureFlagRegistry.instance

puts "Same instance: #{registry1.equal?(registry2)}"  # true

puts "new_checkout enabled?:   #{registry1.enabled?(:new_checkout)}"   # true
puts "dark_mode enabled?:      #{registry2.enabled?(:dark_mode)}"      # false

# Simulate a rollout: 10% of users get beta_dashboard.
users_with_flag = (1..100).count do |user_id|
  registry1.enabled?(:beta_dashboard, user_id: user_id)
end
puts "Users seeing beta_dashboard (~10%): #{users_with_flag}"

# Runtime override — useful in tests.
registry1.override(:dark_mode, true)
puts "dark_mode after override: #{registry2.enabled?(:dark_mode)}"  # true

registry1.clear_override(:dark_mode)
puts "dark_mode after clearing: #{registry2.enabled?(:dark_mode)}"  # false
```

---

## When To Use

Use the Singleton pattern when:

- **Exactly one shared resource** must coordinate access across an entire system, such as a database connection pool, file system handle, device driver, thread pool, registry, or event bus.
- **A class needs stricter global-variable control.** Unlike a plain global variable, a Singleton cannot be overwritten by accident because the reference is encapsulated behind a method.
- **Lazy initialisation is desirable.** The object is created only on first use, avoiding startup costs when the resource may not be needed every run.
- **State must be consistent between multiple consumers.** Two components that independently call `getInstance()` are guaranteed to see the same state rather than each maintaining their own divergent copy.

Do **not** use Singleton when:

- Multiple independent instances are possible or beneficial (e.g., per-tenant database connections).
- The dependency needs to be swapped at test time — prefer dependency injection instead.
- The class holds mutable global state that makes code hard to reason about.

---

## Pros & Cons

| Aspect | Detail |
|---|---|
| **Pro — Guaranteed single instance** | The runtime enforces that only one object of that type can ever exist, eliminating accidental duplication of heavyweight resources. |
| **Pro — Global access point** | Any code in the system can obtain the instance via `getInstance()` without needing it passed through constructors or parameter lists. |
| **Pro — Lazy initialisation** | The instance is created only when first needed, deferring allocation and I/O costs. |
| **Con — Violates Single Responsibility Principle** | The class manages both its domain logic and its own lifecycle (instantiation count). |
| **Con — Can mask bad design** | Teams sometimes reach for Singleton to avoid thinking carefully about object ownership and lifetimes. |
| **Con — Multithreaded complexity** | Without careful synchronisation, multiple threads can create multiple instances or read partially-constructed state. |
| **Con — Difficult to unit test** | Global state persists between tests, creating order-dependent failures. Singletons are hard to mock or replace with test doubles. |
| **Con — Tight coupling** | Callers that use `getInstance()` directly are tightly coupled to the concrete Singleton class, making substitution or subclassing difficult. |

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Abstract Factory** | An Abstract Factory is often implemented as a Singleton. There is usually only one factory needed per product family, and it should be accessible globally. |
| **Builder** | Builders are sometimes stored as Singletons when the same builder configuration is reused across many object constructions. |
| **Prototype** | A Singleton registry can store and return Prototype instances; the registry itself is often a Singleton. |
| **Facade** | A Facade class that wraps a complex subsystem is often turned into a Singleton, because a single facade object is usually sufficient. |

---

## Sources

- https://refactoring.guru/design-patterns/singleton
- https://sourcemaking.com/design_patterns/singleton
