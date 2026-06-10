# Flyweight Pattern

**Category:** Structural
**Also Known As:** Cache

---

## Intent

Lets you fit more objects into the available amount of RAM by sharing common parts of state between multiple objects instead of keeping all of the data in each object. A single flyweight object can be used in many different contexts simultaneously, storing only the state that is intrinsic (invariant, context-independent) and receiving the extrinsic (context-dependent) state from the caller at runtime.

---

## Problem It Solves

Imagine building a real-time particle system for a game where thousands of bullets, missiles, shrapnel fragments, and tree leaves are rendered every frame. Each particle object naively stores:

- Sprite / texture image (several megabytes each)
- Color tint
- Movement vector
- Current position (x, y)
- Speed scalar

If you instantiate 100,000 particle objects and each holds a full copy of the 5 MB sprite, you immediately exhaust RAM. The problem is that **most of that data is duplicated**: every bullet shares the same sprite, color, and movement behaviour — only the position and speed differ per instance.

The same scenario occurs in:

- **Text editors** rendering millions of character glyphs (font data is shared, position is unique)
- **Map engines** rendering millions of tree/rock/building tiles
- **Network simulators** managing thousands of identical connection objects
- **Browser DOM renderers** sharing style/layout boxes across repeated elements

The root cause: objects carry **redundant, shareable data** alongside **unique, per-instance data**, and we never separate the two concerns.

---

## Solution

Split each object's state into two buckets:

| Bucket | Name | Stored where | Changes? |
|--------|------|--------------|----------|
| Shared, context-independent data | **Intrinsic state** | Inside the Flyweight object | Never |
| Unique, context-dependent data | **Extrinsic state** | Outside, in the Client / Context | Per call |

The **Flyweight** object holds only intrinsic state and is therefore safe to share across thousands of contexts. The client retains (or recomputes) the extrinsic state and passes it to flyweight methods at the moment of use.

A **FlyweightFactory** acts as a cache. When a client requests a flyweight, the factory checks whether a matching one already exists and returns it; otherwise it creates, caches, and returns a new one. Clients never instantiate flyweights directly.

Because flyweights are shared, they must be **immutable** — their intrinsic state must be set once (usually in the constructor) and never changed afterwards.

---

## Structure (ASCII diagram)

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client                                  │
│                                                                 │
│  ┌─────────────────────┐      ┌──────────────────────────────┐  │
│  │  Context / Particle │      │       FlyweightFactory       │  │
│  │─────────────────────│      │──────────────────────────────│  │
│  │ - extrinsicState    │      │ - cache: Map<key, Flyweight>  │  │
│  │ - flyweight: ref ───┼─────>│                              │  │
│  │─────────────────────│      │ + getFlyweight(key): Flyweight│  │
│  │ + operation()       │      └──────────────┬───────────────┘  │
│  └─────────────────────┘                     │ creates / returns│
└─────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼
                                  ┌────────────────────────┐
                                  │       Flyweight         │
                                  │────────────────────────│
                                  │ - intrinsicState        │
                                  │────────────────────────│
                                  │ + operation(            │
                                  │    extrinsicState)      │
                                  └────────────────────────┘

Flow:
  1. Client asks FlyweightFactory for a Flyweight with given key.
  2. Factory looks up cache. Hit → return cached. Miss → create, cache, return.
  3. Client stores the returned flyweight reference alongside its own extrinsic state.
  4. At render/use time: flyweight.operation(extrinsicState) is called.
  5. Flyweight combines its intrinsic state with the passed extrinsic state.
```

---

## Participants

| Participant | Responsibility |
|-------------|----------------|
| **Flyweight** | Declares the interface through which flyweights can receive and act on extrinsic state. Stores only intrinsic (shared) state internally. Must be immutable after construction. |
| **ConcreteFlyweight** | Implements the Flyweight interface. Holds intrinsic state. A single instance is shared by many contexts simultaneously. |
| **FlyweightFactory** | Creates and manages the pool of flyweight objects. Ensures that flyweights are shared properly: when a client requests a flyweight the factory either returns an existing instance or creates a new one. |
| **Context (optional)** | Holds the extrinsic state. Pairs one extrinsic-state bundle with a reference to a shared Flyweight. Sometimes the Client plays this role directly. |
| **Client** | Computes or stores extrinsic state. Calls flyweight methods, passing extrinsic state as arguments. Obtains flyweights from the factory, never via `new`. |

---

## How It Works (step-by-step)

1. **Identify shared vs. unique state.** Examine the bloated object. Separate all fields into two groups: those that are identical across many instances (intrinsic) and those that differ per instance (extrinsic).

2. **Design the Flyweight interface.** Declare an `operation(extrinsicState)` method. The extrinsic state is passed in, not stored.

3. **Implement ConcreteFlyweight.** Store only intrinsic state. Make it immutable (set everything in the constructor, expose no setters). Implement `operation` using both its own intrinsic state and the received extrinsic state.

4. **Implement FlyweightFactory.** Maintain a dictionary/map keyed by a canonical representation of the intrinsic state. `getFlyweight(key)` checks the map — hit: return existing; miss: construct new, insert, return.

5. **Refactor Context/Client.** Instead of holding a fat object, the client holds: (a) a reference to a shared flyweight, and (b) its own extrinsic state fields. When it needs to "act", it calls `flyweight.operation(myExtrinsicState)`.

6. **Memory reduction is realised.** Where previously N objects each allocated M bytes of shared data, now only one flyweight holds M bytes, saving `(N-1) * M` bytes.

---

## Code Examples

### Python

```python
"""
Flyweight Pattern — Particle System (Game Engine)

A game fires thousands of projectiles. Each projectile type shares a
sprite texture and motion physics (intrinsic), but has its own position,
velocity vector, and lifetime (extrinsic).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import random
import time


# ---------------------------------------------------------------------------
# Flyweight: holds intrinsic (shared) state only
# ---------------------------------------------------------------------------
class ParticleType:
    """Immutable flyweight — shared by all particles of the same 'kind'."""

    def __init__(self, name: str, color: str, sprite: str, mass: float) -> None:
        # Intrinsic state — set once, never mutated
        self._name = name
        self._color = color
        self._sprite = sprite   # In reality: a loaded Texture object (large!)
        self._mass = mass       # Used in physics calculations

    @property
    def name(self) -> str:
        return self._name

    def draw(self, x: float, y: float, alpha: float) -> None:
        """Render the particle using its intrinsic sprite + extrinsic position/alpha."""
        print(
            f"[{self._name}] sprite='{self._sprite}' color={self._color} "
            f"@ ({x:.1f}, {y:.1f}) alpha={alpha:.2f}"
        )

    def update_physics(
        self, x: float, y: float, vx: float, vy: float, dt: float
    ) -> Tuple[float, float, float, float]:
        """Apply gravity (intrinsic mass) + velocity; return new position & velocity."""
        gravity = 9.8 * self._mass
        new_vy = vy + gravity * dt
        new_x = x + vx * dt
        new_y = y + new_vy * dt
        return new_x, new_y, vx, new_vy

    def __repr__(self) -> str:
        return f"ParticleType(name={self._name!r}, id={id(self)})"


# ---------------------------------------------------------------------------
# Flyweight Factory: manages the shared pool
# ---------------------------------------------------------------------------
class ParticleTypeFactory:
    """Creates and caches ParticleType flyweights."""

    _cache: Dict[str, ParticleType] = {}

    @classmethod
    def get(cls, name: str, color: str, sprite: str, mass: float) -> ParticleType:
        key = f"{name}:{color}:{sprite}:{mass}"
        if key not in cls._cache:
            print(f"  [Factory] Creating new ParticleType for key='{key}'")
            cls._cache[key] = ParticleType(name, color, sprite, mass)
        else:
            print(f"  [Factory] Reusing cached ParticleType for key='{key}'")
        return cls._cache[key]

    @classmethod
    def pool_size(cls) -> int:
        return len(cls._cache)

    @classmethod
    def list_types(cls) -> None:
        for key, pt in cls._cache.items():
            print(f"  {key!r}  ->  {pt!r}")


# ---------------------------------------------------------------------------
# Context: holds extrinsic (unique) state + reference to flyweight
# ---------------------------------------------------------------------------
@dataclass
class Particle:
    """One live particle in the scene — holds only extrinsic state."""

    x: float
    y: float
    vx: float
    vy: float
    lifetime: float          # seconds remaining
    particle_type: ParticleType  # shared flyweight reference

    def update(self, dt: float) -> None:
        self.x, self.y, self.vx, self.vy = self.particle_type.update_physics(
            self.x, self.y, self.vx, self.vy, dt
        )
        self.lifetime -= dt

    def draw(self) -> None:
        alpha = max(0.0, self.lifetime / 3.0)  # fade out over 3 seconds
        self.particle_type.draw(self.x, self.y, alpha)

    @property
    def is_alive(self) -> bool:
        return self.lifetime > 0


# ---------------------------------------------------------------------------
# Client / Simulation
# ---------------------------------------------------------------------------
class ParticleSystem:
    def __init__(self) -> None:
        self._particles: List[Particle] = []

    def emit(self, kind: str, x: float, y: float, count: int) -> None:
        """Spawn `count` particles of the given kind at (x, y)."""
        # Obtain (or reuse) the flyweight for this particle kind
        configs = {
            "bullet": ("bullet", "yellow", "bullet.png", 0.1),
            "smoke":  ("smoke",  "gray",   "smoke.png",  0.01),
            "spark":  ("spark",  "orange", "spark.png",  0.05),
        }
        name, color, sprite, mass = configs[kind]
        ptype = ParticleTypeFactory.get(name, color, sprite, mass)

        for _ in range(count):
            self._particles.append(Particle(
                x=x + random.uniform(-5, 5),
                y=y + random.uniform(-5, 5),
                vx=random.uniform(-10, 10),
                vy=random.uniform(-20, 0),
                lifetime=random.uniform(1.0, 3.0),
                particle_type=ptype,
            ))

    def tick(self, dt: float) -> None:
        self._particles = [p for p in self._particles if p.is_alive]
        for p in self._particles:
            p.update(dt)

    def draw(self) -> None:
        for p in self._particles:
            p.draw()

    def stats(self) -> None:
        print(f"\nParticles alive : {len(self._particles)}")
        print(f"Flyweight types : {ParticleTypeFactory.pool_size()}")
        ParticleTypeFactory.list_types()


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Particle System (Flyweight Demo) ===\n")
    system = ParticleSystem()

    print("--- Emitting 5 bullets ---")
    system.emit("bullet", 100, 200, 5)

    print("\n--- Emitting 5 more bullets (should reuse flyweight) ---")
    system.emit("bullet", 150, 200, 5)

    print("\n--- Emitting 3 smoke puffs ---")
    system.emit("smoke", 100, 200, 3)

    print("\n--- Emitting 4 sparks ---")
    system.emit("spark", 120, 220, 4)

    print("\n--- Simulation tick (dt=0.016s) ---")
    system.tick(0.016)

    print("\n--- Drawing frame ---")
    system.draw()

    system.stats()
    # Regardless of how many particles are alive, only 3 ParticleType objects exist.
```

---

### Java

```java
/**
 * Flyweight Pattern — Forest Renderer
 *
 * A game map renders hundreds of thousands of trees. Each tree has a unique
 * (x, y) position and age, but shares heavy data (name, color, texture) via
 * the TreeType flyweight.
 */

import java.util.*;

// ---------------------------------------------------------------------------
// Flyweight: intrinsic (shared) state
// ---------------------------------------------------------------------------
final class TreeType {
    private final String name;
    private final String color;
    private final String texture; // In real code: a loaded BufferedImage

    TreeType(String name, String color, String texture) {
        this.name    = name;
        this.color   = color;
        this.texture = texture;
    }

    /** Draw using intrinsic data + extrinsic position/age. */
    public void draw(int x, int y, int age) {
        double scale = 0.5 + age * 0.05; // older trees are taller
        System.out.printf(
            "[TreeType '%s'] color=%s texture=%s -> draw @ (%d,%d) scale=%.2f%n",
            name, color, texture, x, y, scale
        );
    }

    public String getName() { return name; }

    @Override
    public String toString() {
        return String.format("TreeType{name='%s', id=%d}", name, System.identityHashCode(this));
    }
}

// ---------------------------------------------------------------------------
// Flyweight Factory
// ---------------------------------------------------------------------------
final class TreeTypeFactory {
    private static final Map<String, TreeType> cache = new HashMap<>();

    public static TreeType getTreeType(String name, String color, String texture) {
        String key = name + ":" + color + ":" + texture;
        return cache.computeIfAbsent(key, k -> {
            System.out.println("  [Factory] Creating new TreeType: " + key);
            return new TreeType(name, color, texture);
        });
    }

    public static int poolSize() { return cache.size(); }

    public static void listTypes() {
        cache.values().forEach(t -> System.out.println("  " + t));
    }
}

// ---------------------------------------------------------------------------
// Context: extrinsic (unique) state
// ---------------------------------------------------------------------------
final class Tree {
    private final int x;
    private final int y;
    private final int age;
    private final TreeType type; // flyweight reference

    Tree(int x, int y, int age, TreeType type) {
        this.x    = x;
        this.y    = y;
        this.age  = age;
        this.type = type;
    }

    public void draw() {
        type.draw(x, y, age);
    }
}

// ---------------------------------------------------------------------------
// Client: Forest that owns Context objects
// ---------------------------------------------------------------------------
final class Forest {
    private final List<Tree> trees = new ArrayList<>();

    public void plantTree(int x, int y, int age, String name, String color, String texture) {
        TreeType type = TreeTypeFactory.getTreeType(name, color, texture);
        trees.add(new Tree(x, y, age, type));
    }

    public void draw() {
        trees.forEach(Tree::draw);
    }

    public int treeCount() { return trees.size(); }
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------
public class FlyweightDemo {
    public static void main(String[] args) {
        System.out.println("=== Forest Renderer (Flyweight Demo) ===\n");

        Forest forest = new Forest();
        Random rng = new Random(42);

        String[] names    = {"Oak", "Pine", "Birch"};
        String[] colors   = {"dark-green", "green", "light-green"};
        String[] textures = {"oak.png", "pine.png", "birch.png"};

        // Plant 20 trees (only 3 TreeType flyweights will be created)
        System.out.println("--- Planting 20 trees ---");
        for (int i = 0; i < 20; i++) {
            int idx = rng.nextInt(3);
            forest.plantTree(
                rng.nextInt(800), rng.nextInt(600),
                rng.nextInt(50) + 1,
                names[idx], colors[idx], textures[idx]
            );
        }

        System.out.println("\n--- Drawing forest ---");
        forest.draw();

        System.out.printf("%n--- Stats ---%n");
        System.out.printf("Total trees   : %d%n", forest.treeCount());
        System.out.printf("Flyweight pool: %d TreeType objects%n", TreeTypeFactory.poolSize());
        System.out.println("Flyweight types:");
        TreeTypeFactory.listTypes();
    }
}
```

---

### C++

```cpp
/**
 * Flyweight Pattern — Glyph Renderer (Text Editor)
 *
 * A text editor renders millions of characters. Each character cell has a
 * unique row/column/foreground colour, but shares font metrics and bitmap
 * data via a Glyph flyweight.
 */

#include <iostream>
#include <unordered_map>
#include <vector>
#include <memory>
#include <string>
#include <format>

// ---------------------------------------------------------------------------
// Flyweight: intrinsic state (font face, size, bold, italic, bitmap data)
// ---------------------------------------------------------------------------
class GlyphType {
public:
    GlyphType(char ch, const std::string& font, int size, bool bold)
        : ch_(ch), font_(font), size_(size), bold_(bold)
    {
        // Simulate loading a glyph bitmap (expensive operation done only once)
        bitmap_ = std::format("[bitmap:{}@{}pt{}]", ch, size, bold ? "-bold" : "");
    }

    // Render using intrinsic data + extrinsic (row, col, color)
    void draw(int row, int col, const std::string& color) const {
        std::cout << std::format(
            "Glyph '{}' font={} size={}pt bold={} bitmap={} -> ({},{}) color={}\n",
            ch_, font_, size_, bold_, bitmap_, row, col, color
        );
    }

    char character() const { return ch_; }

private:
    char        ch_;
    std::string font_;
    int         size_;
    bool        bold_;
    std::string bitmap_; // heavy data shared among all instances of same glyph config
};

// ---------------------------------------------------------------------------
// Flyweight Factory
// ---------------------------------------------------------------------------
class GlyphFactory {
public:
    static GlyphFactory& instance() {
        static GlyphFactory factory;
        return factory;
    }

    const GlyphType& getGlyph(char ch, const std::string& font, int size, bool bold) {
        std::string key = std::string(1, ch) + ":" + font + ":" +
                          std::to_string(size) + ":" + (bold ? "1" : "0");

        auto it = cache_.find(key);
        if (it == cache_.end()) {
            std::cout << "  [Factory] Creating GlyphType for key='" << key << "'\n";
            cache_.emplace(key, std::make_unique<GlyphType>(ch, font, size, bold));
            it = cache_.find(key);
        }
        return *it->second;
    }

    std::size_t poolSize() const { return cache_.size(); }

private:
    GlyphFactory() = default;
    std::unordered_map<std::string, std::unique_ptr<GlyphType>> cache_;
};

// ---------------------------------------------------------------------------
// Context: extrinsic state (position, color) + flyweight reference
// ---------------------------------------------------------------------------
struct GlyphContext {
    int                row;
    int                col;
    std::string        color;
    const GlyphType*   glyph; // non-owning pointer to shared flyweight

    void draw() const {
        glyph->draw(row, col, color);
    }
};

// ---------------------------------------------------------------------------
// Client: Document that holds a vector of GlyphContexts
// ---------------------------------------------------------------------------
class Document {
public:
    void addChar(int row, int col, char ch,
                 const std::string& font, int size, bool bold,
                 const std::string& color)
    {
        const GlyphType& g = GlyphFactory::instance().getGlyph(ch, font, size, bold);
        chars_.push_back({row, col, color, &g});
    }

    void render() const {
        for (const auto& ctx : chars_) ctx.draw();
    }

    std::size_t charCount() const { return chars_.size(); }

private:
    std::vector<GlyphContext> chars_;
};

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------
int main() {
    std::cout << "=== Text Editor Glyph Renderer (Flyweight Demo) ===\n\n";

    Document doc;
    GlyphFactory& factory = GlyphFactory::instance();

    // Simulate typing "Hello, World!" with mixed formatting
    std::string text = "Hello, World!";
    for (int i = 0; i < static_cast<int>(text.size()); ++i) {
        bool bold = (i < 5); // "Hello" in bold
        doc.addChar(0, i, text[i], "Arial", 12, bold, "black");
    }

    // Second line: same characters — factory reuses flyweights
    std::string text2 = "Hello again!";
    for (int i = 0; i < static_cast<int>(text2.size()); ++i) {
        doc.addChar(1, i, text2[i], "Arial", 12, false, "blue");
    }

    std::cout << "\n--- Rendering document ---\n";
    doc.render();

    std::cout << "\n--- Stats ---\n";
    std::cout << "Characters rendered : " << doc.charCount() << "\n";
    std::cout << "Glyph flyweights    : " << factory.poolSize()
              << " (unique glyph configurations)\n";

    return 0;
}
```

---

### C#

```csharp
/**
 * Flyweight Pattern — Map Tile Renderer
 *
 * A top-down game map consists of millions of tiles (grass, water, sand, rock).
 * Each tile shares heavy texture/collision data (intrinsic) via a TileType
 * flyweight, while position and overlay flags are extrinsic.
 */

using System;
using System.Collections.Generic;

// ---------------------------------------------------------------------------
// Flyweight: intrinsic state
// ---------------------------------------------------------------------------
sealed class TileType
{
    public string Name        { get; }
    public string TexturePath { get; }   // heavy: a loaded Texture2D in real engine
    public bool   IsWalkable  { get; }
    public float  MoveCost    { get; }   // movement cost multiplier for pathfinding

    public TileType(string name, string texturePath, bool isWalkable, float moveCost)
    {
        Name        = name;
        TexturePath = texturePath;
        IsWalkable  = isWalkable;
        MoveCost    = moveCost;
    }

    /// <summary>Draw using intrinsic texture + extrinsic world position and highlight flag.</summary>
    public void Draw(int worldX, int worldY, bool highlighted)
    {
        string h = highlighted ? " [HIGHLIGHTED]" : "";
        Console.WriteLine(
            $"Tile '{Name}' texture={TexturePath} walkable={IsWalkable} moveCost={MoveCost:F1} " +
            $"-> ({worldX},{worldY}){h}"
        );
    }

    public override string ToString() =>
        $"TileType{{Name='{Name}', Id={RuntimeHelpers.GetHashCode(this)}}}";
}

// Needed for identity hash code
static class RuntimeHelpers
{
    public static int GetHashCode(object obj) => System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(obj);
}

// ---------------------------------------------------------------------------
// Flyweight Factory
// ---------------------------------------------------------------------------
static class TileTypeFactory
{
    private static readonly Dictionary<string, TileType> _cache = new();

    public static TileType Get(string name, string texturePath, bool isWalkable, float moveCost)
    {
        string key = $"{name}:{texturePath}:{isWalkable}:{moveCost:F1}";
        if (!_cache.TryGetValue(key, out TileType? tileType))
        {
            Console.WriteLine($"  [Factory] Creating TileType: '{key}'");
            tileType = new TileType(name, texturePath, isWalkable, moveCost);
            _cache[key] = tileType;
        }
        return tileType;
    }

    public static int PoolSize => _cache.Count;

    public static void ListTypes()
    {
        foreach (var (key, t) in _cache)
            Console.WriteLine($"  '{key}' -> {t}");
    }
}

// ---------------------------------------------------------------------------
// Context: extrinsic state (position, highlighted) + flyweight reference
// ---------------------------------------------------------------------------
readonly struct MapTile
{
    public int      WorldX      { get; }
    public int      WorldY      { get; }
    public bool     Highlighted { get; }
    public TileType Type        { get; }   // shared flyweight

    public MapTile(int worldX, int worldY, bool highlighted, TileType type)
    {
        WorldX      = worldX;
        WorldY      = worldY;
        Highlighted = highlighted;
        Type        = type;
    }

    public void Draw() => Type.Draw(WorldX, WorldY, Highlighted);
}

// ---------------------------------------------------------------------------
// Client: GameMap holds a flat array of lightweight MapTile contexts
// ---------------------------------------------------------------------------
class GameMap
{
    private readonly List<MapTile> _tiles = new();

    private static readonly (string name, string tex, bool walk, float cost)[] _defs =
    {
        ("Grass", "grass.png",  true,  1.0f),
        ("Water", "water.png",  false, 0.0f),
        ("Sand",  "sand.png",   true,  1.5f),
        ("Rock",  "rock.png",   false, 0.0f),
    };

    public void GenerateRandom(int width, int height)
    {
        var rng = new Random(42);
        for (int y = 0; y < height; y++)
        {
            for (int x = 0; x < width; x++)
            {
                var (name, tex, walk, cost) = _defs[rng.Next(_defs.Length)];
                TileType tileType = TileTypeFactory.Get(name, tex, walk, cost);
                bool highlighted  = (x == width / 2 && y == height / 2); // centre tile
                _tiles.Add(new MapTile(x, y, highlighted, tileType));
            }
        }
    }

    public void Render()
    {
        foreach (var tile in _tiles)
            tile.Draw();
    }

    public int TileCount => _tiles.Count;
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------
class FlyweightDemo
{
    static void Main()
    {
        Console.WriteLine("=== Map Tile Renderer (Flyweight Demo) ===\n");

        var map = new GameMap();

        Console.WriteLine("--- Generating 5x5 map ---");
        map.GenerateRandom(5, 5);

        Console.WriteLine("\n--- Rendering map (first 10 tiles) ---");
        // For brevity just print stats; in real code: map.Render();
        map.Render();

        Console.WriteLine("\n--- Stats ---");
        Console.WriteLine($"Total tiles     : {map.TileCount}");
        Console.WriteLine($"Flyweight types : {TileTypeFactory.PoolSize}");
        TileTypeFactory.ListTypes();
    }
}
```

---

### TypeScript

```typescript
/**
 * Flyweight Pattern — Icon Renderer (UI Library)
 *
 * A UI toolkit renders thousands of icons in lists and toolbars. Each icon
 * instance has a unique position, size, and click handler (extrinsic), but
 * shares SVG path data, ARIA label, and default color via an IconFlyweight.
 */

// ---------------------------------------------------------------------------
// Flyweight: intrinsic (shared) state
// ---------------------------------------------------------------------------
class IconFlyweight {
  private readonly svgPath: string; // potentially large SVG markup
  private readonly ariaLabel: string;
  private readonly defaultColor: string;

  constructor(svgPath: string, ariaLabel: string, defaultColor: string) {
    this.svgPath = svgPath;
    this.ariaLabel = ariaLabel;
    this.defaultColor = defaultColor;
  }

  /**
   * Render icon HTML combining intrinsic SVG data with extrinsic position/size/color.
   */
  render(x: number, y: number, size: number, colorOverride?: string): string {
    const color = colorOverride ?? this.defaultColor;
    return (
      `<svg aria-label="${this.ariaLabel}" ` +
      `style="position:absolute;left:${x}px;top:${y}px;` +
      `width:${size}px;height:${size}px;fill:${color};" ` +
      `viewBox="0 0 24 24">${this.svgPath}</svg>`
    );
  }

  get label(): string {
    return this.ariaLabel;
  }
}

// ---------------------------------------------------------------------------
// Flyweight Factory
// ---------------------------------------------------------------------------
class IconFactory {
  private static cache = new Map<string, IconFlyweight>();

  static getIcon(name: string, svgPath: string, ariaLabel: string, defaultColor: string): IconFlyweight {
    if (!this.cache.has(name)) {
      console.log(`  [Factory] Creating flyweight for icon '${name}'`);
      this.cache.set(name, new IconFlyweight(svgPath, ariaLabel, defaultColor));
    }
    return this.cache.get(name)!;
  }

  static get poolSize(): number {
    return this.cache.size;
  }

  static listIcons(): void {
    for (const [name] of this.cache) {
      console.log(`  - '${name}'`);
    }
  }
}

// ---------------------------------------------------------------------------
// Context: extrinsic (unique) state + flyweight reference
// ---------------------------------------------------------------------------
interface IconContext {
  x: number;
  y: number;
  size: number;
  colorOverride?: string;
  flyweight: IconFlyweight;
  onClick: () => void;
}

// ---------------------------------------------------------------------------
// Client: Toolbar that renders many icon contexts
// ---------------------------------------------------------------------------
class Toolbar {
  private icons: IconContext[] = [];

  // Pre-define known SVG paths (simplified)
  private static svgPaths: Record<string, [string, string, string]> = {
    save:   ["<path d='M17 3H5a2 2 0 00-2 2v14l7-3 7 3V5a2 2 0 00-2-2z'/>", "Save",   "#333"],
    delete: ["<path d='M6 19c0 1.1.9 2 2 2h8a2 2 0 002-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z'/>", "Delete", "#c00"],
    edit:   ["<path d='M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 000-1.41l-2.34-2.34a1 1 0 00-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z'/>", "Edit", "#555"],
  };

  addIcon(
    iconName: string,
    x: number,
    y: number,
    size: number,
    colorOverride?: string,
    onClick?: () => void
  ): void {
    const [svgPath, ariaLabel, defaultColor] = Toolbar.svgPaths[iconName] ?? ["", iconName, "#000"];
    const flyweight = IconFactory.getIcon(iconName, svgPath, ariaLabel, defaultColor);

    this.icons.push({
      x,
      y,
      size,
      colorOverride,
      flyweight,
      onClick: onClick ?? (() => console.log(`Clicked: ${ariaLabel}`)),
    });
  }

  renderAll(): string {
    return this.icons.map(ctx =>
      ctx.flyweight.render(ctx.x, ctx.y, ctx.size, ctx.colorOverride)
    ).join("\n");
  }

  get iconCount(): number {
    return this.icons.length;
  }
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------
function main(): void {
  console.log("=== UI Icon Renderer (Flyweight Demo) ===\n");

  const toolbar = new Toolbar();

  console.log("--- Adding icons to toolbar ---");
  // Save buttons (same flyweight, different positions/colors)
  toolbar.addIcon("save",   10, 10, 24);
  toolbar.addIcon("save",   10, 44, 24, "#0a0");
  toolbar.addIcon("delete", 50, 10, 24);
  toolbar.addIcon("delete", 50, 44, 24);
  toolbar.addIcon("edit",   90, 10, 24);
  // Repeated save icon — factory reuses existing flyweight
  toolbar.addIcon("save",  130, 10, 32, "#00f");

  console.log("\n--- Rendered HTML ---");
  console.log(toolbar.renderAll());

  console.log("\n--- Stats ---");
  console.log(`Icons in toolbar : ${toolbar.iconCount}`);
  console.log(`Flyweight pool   : ${IconFactory.poolSize} IconFlyweight objects`);
  IconFactory.listIcons();
}

main();
```

---

### Go

```go
// Flyweight Pattern — Network Connection Pool
//
// A load balancer maintains thousands of outbound connections to backend
// servers. Each connection shares immutable server config (host, port,
// protocol) via a ServerConfig flyweight. Per-connection state (requestID,
// timeout, metadata) is extrinsic.

package main

import (
	"fmt"
	"math/rand"
	"sync"
	"time"
)

// ---------------------------------------------------------------------------
// Flyweight: intrinsic (shared) state
// ---------------------------------------------------------------------------

// ServerConfig holds immutable configuration shared by all connections
// to the same backend endpoint. Creating a TLS context or resolving DNS
// is expensive — doing it once per unique endpoint saves significant work.
type ServerConfig struct {
	Host       string
	Port       int
	Protocol   string // "http", "https", "grpc"
	MaxRetries int
	tlsContext string // simulated expensive TLS setup
}

// newServerConfig simulates the expensive one-time setup (TLS handshake,
// DNS resolution, etc.) when a new unique endpoint is first seen.
func newServerConfig(host string, port int, protocol string, maxRetries int) *ServerConfig {
	tlsCtx := fmt.Sprintf("[TLS-CTX:%s://%s:%d]", protocol, host, port)
	fmt.Printf("  [Factory] Setting up ServerConfig for %s:%d (TLS: %s)\n", host, port, tlsCtx)
	return &ServerConfig{
		Host:       host,
		Port:       port,
		Protocol:   protocol,
		MaxRetries: maxRetries,
		tlsContext: tlsCtx,
	}
}

// Send simulates sending a request using intrinsic config + extrinsic request data.
func (s *ServerConfig) Send(requestID string, payload string, timeoutMs int) {
	fmt.Printf(
		"  [%s://%s:%d] reqID=%s payload='%s' timeout=%dms retries=%d ctx=%s\n",
		s.Protocol, s.Host, s.Port,
		requestID, payload, timeoutMs, s.MaxRetries, s.tlsContext,
	)
}

// ---------------------------------------------------------------------------
// Flyweight Factory (thread-safe)
// ---------------------------------------------------------------------------

type ServerConfigFactory struct {
	mu    sync.Mutex
	cache map[string]*ServerConfig
}

var globalFactory = &ServerConfigFactory{cache: make(map[string]*ServerConfig)}

func (f *ServerConfigFactory) Get(host string, port int, protocol string, maxRetries int) *ServerConfig {
	key := fmt.Sprintf("%s://%s:%d/r%d", protocol, host, port, maxRetries)

	f.mu.Lock()
	defer f.mu.Unlock()

	if cfg, ok := f.cache[key]; ok {
		return cfg
	}
	cfg := newServerConfig(host, port, protocol, maxRetries)
	f.cache[key] = cfg
	return cfg
}

func (f *ServerConfigFactory) PoolSize() int {
	f.mu.Lock()
	defer f.mu.Unlock()
	return len(f.cache)
}

// ---------------------------------------------------------------------------
// Context: extrinsic (unique) state + flyweight reference
// ---------------------------------------------------------------------------

// Connection represents a single outbound request context.
// It is lightweight: only extrinsic state lives here.
type Connection struct {
	RequestID  string
	Payload    string
	TimeoutMs  int
	serverCfg  *ServerConfig // shared flyweight (non-owning)
}

func NewConnection(requestID, payload string, timeoutMs int, cfg *ServerConfig) *Connection {
	return &Connection{
		RequestID: requestID,
		Payload:   payload,
		TimeoutMs: timeoutMs,
		serverCfg: cfg,
	}
}

func (c *Connection) Execute() {
	c.serverCfg.Send(c.RequestID, c.Payload, c.TimeoutMs)
}

// ---------------------------------------------------------------------------
// Client: LoadBalancer spawns connections across a backend pool
// ---------------------------------------------------------------------------

type LoadBalancer struct {
	backends []struct{ host string; port int; proto string }
}

func NewLoadBalancer() *LoadBalancer {
	return &LoadBalancer{
		backends: []struct{ host string; port int; proto string }{
			{"api-1.internal", 8080, "https"},
			{"api-2.internal", 8080, "https"},
			{"api-3.internal", 9090, "grpc"},
		},
	}
}

func (lb *LoadBalancer) Dispatch(requestID, payload string, timeoutMs int) {
	backend := lb.backends[rand.Intn(len(lb.backends))]
	cfg := globalFactory.Get(backend.host, backend.port, backend.proto, 3)
	conn := NewConnection(requestID, payload, timeoutMs, cfg)
	conn.Execute()
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

func main() {
	rand.Seed(time.Now().UnixNano())
	fmt.Println("=== Load Balancer (Flyweight Demo) ===\n")

	lb := NewLoadBalancer()

	fmt.Println("--- Dispatching 10 requests ---")
	for i := 0; i < 10; i++ {
		reqID := fmt.Sprintf("req-%04d", i+1)
		payload := fmt.Sprintf(`{"action":"query","id":%d}`, i)
		lb.Dispatch(reqID, payload, 5000)
	}

	fmt.Printf("\n--- Stats ---\n")
	fmt.Printf("Requests dispatched  : 10\n")
	fmt.Printf("ServerConfig objects : %d (flyweight pool)\n", globalFactory.PoolSize())
	fmt.Println("(Only 3 ServerConfig objects were created despite 10 connections)")
}
```

---

### PHP

```php
<?php
/**
 * Flyweight Pattern — Product Card Renderer (E-commerce)
 *
 * An e-commerce listing page renders thousands of product cards.
 * Each card shares brand metadata and category icons (intrinsic) but has
 * its own price, stock count, and discount (extrinsic).
 */

declare(strict_types=1);

// ---------------------------------------------------------------------------
// Flyweight: intrinsic (shared) state
// ---------------------------------------------------------------------------
final class BrandProfile
{
    private string $name;
    private string $logoUrl;        // large binary in reality
    private string $primaryColor;
    private string $categoryIcon;   // SVG data

    public function __construct(
        string $name,
        string $logoUrl,
        string $primaryColor,
        string $categoryIcon
    ) {
        $this->name          = $name;
        $this->logoUrl       = $logoUrl;
        $this->primaryColor  = $primaryColor;
        $this->categoryIcon  = $categoryIcon;
    }

    /**
     * Render a product card using intrinsic brand data + extrinsic product data.
     *
     * @param string $productName  Extrinsic
     * @param float  $price        Extrinsic
     * @param int    $stock        Extrinsic
     * @param int    $discountPct  Extrinsic
     */
    public function renderCard(
        string $productName,
        float $price,
        int $stock,
        int $discountPct
    ): string {
        $finalPrice   = $price * (1 - $discountPct / 100);
        $stockLabel   = $stock > 0 ? "In Stock ({$stock})" : "Out of Stock";
        $discountBadge = $discountPct > 0 ? " [{$discountPct}% OFF]" : '';

        return sprintf(
            "<div class='card' style='border-color:%s;'>" .
            "<img src='%s' alt='%s logo'>" .
            "<span class='category'>%s</span>" .
            "<h3>%s%s</h3>" .
            "<p class='price'>$%.2f</p>" .
            "<p class='stock'>%s</p>" .
            "</div>",
            $this->primaryColor,
            $this->logoUrl,
            $this->name,
            $this->categoryIcon,
            $productName,
            $discountBadge,
            $finalPrice,
            $stockLabel
        );
    }

    public function getName(): string
    {
        return $this->name;
    }
}

// ---------------------------------------------------------------------------
// Flyweight Factory
// ---------------------------------------------------------------------------
final class BrandProfileFactory
{
    /** @var array<string, BrandProfile> */
    private static array $cache = [];

    public static function get(
        string $name,
        string $logoUrl,
        string $primaryColor,
        string $categoryIcon
    ): BrandProfile {
        $key = md5("{$name}:{$logoUrl}:{$primaryColor}:{$categoryIcon}");

        if (!isset(self::$cache[$key])) {
            echo "  [Factory] Creating BrandProfile for '{$name}'\n";
            self::$cache[$key] = new BrandProfile($name, $logoUrl, $primaryColor, $categoryIcon);
        }

        return self::$cache[$key];
    }

    public static function poolSize(): int
    {
        return count(self::$cache);
    }
}

// ---------------------------------------------------------------------------
// Context: extrinsic (unique) state + flyweight reference
// ---------------------------------------------------------------------------
final class ProductCard
{
    private string       $productName;
    private float        $price;
    private int          $stock;
    private int          $discountPct;
    private BrandProfile $brand; // shared flyweight

    public function __construct(
        string $productName,
        float $price,
        int $stock,
        int $discountPct,
        BrandProfile $brand
    ) {
        $this->productName  = $productName;
        $this->price        = $price;
        $this->stock        = $stock;
        $this->discountPct  = $discountPct;
        $this->brand        = $brand;
    }

    public function render(): string
    {
        return $this->brand->renderCard(
            $this->productName,
            $this->price,
            $this->stock,
            $this->discountPct
        );
    }
}

// ---------------------------------------------------------------------------
// Client: ProductListing builds and renders cards
// ---------------------------------------------------------------------------
final class ProductListing
{
    /** @var ProductCard[] */
    private array $cards = [];

    public function addProduct(
        string $productName,
        float  $price,
        int    $stock,
        int    $discountPct,
        string $brandName,
        string $logoUrl,
        string $primaryColor,
        string $categoryIcon
    ): void {
        $brand = BrandProfileFactory::get($brandName, $logoUrl, $primaryColor, $categoryIcon);
        $this->cards[] = new ProductCard($productName, $price, $stock, $discountPct, $brand);
    }

    public function renderAll(): void
    {
        foreach ($this->cards as $card) {
            echo $card->render() . "\n";
        }
    }

    public function count(): int
    {
        return count($this->cards);
    }
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------
echo "=== E-commerce Product Listing (Flyweight Demo) ===\n\n";

$listing = new ProductListing();

echo "--- Adding products ---\n";
// Multiple Nike products share ONE BrandProfile flyweight
$listing->addProduct('Air Max 270',     120.00, 50,  10, 'Nike', 'nike-logo.png', '#111', '[shoe-icon]');
$listing->addProduct('Revolution 6',     65.00, 30,   0, 'Nike', 'nike-logo.png', '#111', '[shoe-icon]');
$listing->addProduct('Pegasus 39',      130.00, 15,  20, 'Nike', 'nike-logo.png', '#111', '[shoe-icon]');

// Multiple Adidas products share ONE BrandProfile flyweight
$listing->addProduct('Ultraboost 22',   180.00, 20,  15, 'Adidas', 'adidas-logo.png', '#000', '[shoe-icon]');
$listing->addProduct('NMD R1',          140.00,  0,   0, 'Adidas', 'adidas-logo.png', '#000', '[shoe-icon]');

echo "\n--- Rendering product cards ---\n";
$listing->renderAll();

echo "\n--- Stats ---\n";
echo "Total product cards  : " . $listing->count() . "\n";
echo "BrandProfile objects : " . BrandProfileFactory::poolSize() . " (flyweight pool)\n";
```

---

### Ruby

```ruby
# Flyweight Pattern — Log Formatter (Logging Library)
#
# A high-throughput logger processes millions of log entries per second.
# Each entry shares a formatter configuration (timestamp format, colormap,
# output template) — intrinsic — but carries its own message, level, and
# source location — extrinsic.

# ---------------------------------------------------------------------------
# Flyweight: intrinsic (shared) state
# ---------------------------------------------------------------------------
class LogFormatter
  attr_reader :name

  ANSI = {
    reset:   "\e[0m",
    red:     "\e[31m",
    yellow:  "\e[33m",
    green:   "\e[32m",
    cyan:    "\e[36m",
    magenta: "\e[35m",
    white:   "\e[37m"
  }.freeze

  LEVEL_COLORS = {
    "DEBUG" => :cyan,
    "INFO"  => :green,
    "WARN"  => :yellow,
    "ERROR" => :red,
    "FATAL" => :magenta
  }.freeze

  def initialize(name, timestamp_format, template)
    @name             = name
    @timestamp_format = timestamp_format # e.g., "%Y-%m-%dT%H:%M:%S"
    @template         = template         # e.g., "[%<ts>s] [%<level>s] %<source>s: %<msg>s"
    # Simulate expensive setup: pre-compile regex, load template engine, etc.
    @compiled = @template.freeze
    puts "  [Factory] Compiled formatter '#{@name}'"
  end

  # Format using intrinsic template/timestamp-format + extrinsic log-entry data
  def format(level, source, message, time = Time.now)
    ts        = time.strftime(@timestamp_format)
    color     = ANSI[LEVEL_COLORS.fetch(level, :white)]
    reset     = ANSI[:reset]
    formatted = @compiled % { ts: ts, level: level, source: source, msg: message }
    "#{color}#{formatted}#{reset}"
  end
end

# ---------------------------------------------------------------------------
# Flyweight Factory
# ---------------------------------------------------------------------------
class FormatterFactory
  @@cache = {}

  def self.get(name, timestamp_format, template)
    key = "#{name}:#{timestamp_format}:#{template}"
    @@cache[key] ||= LogFormatter.new(name, timestamp_format, template)
  end

  def self.pool_size
    @@cache.size
  end

  def self.list
    @@cache.each_key { |k| puts "  #{k}" }
  end
end

# ---------------------------------------------------------------------------
# Context: extrinsic (unique) state + flyweight reference
# ---------------------------------------------------------------------------
LogEntry = Struct.new(:level, :source, :message, :time, :formatter) do
  def to_s
    formatter.format(level, source, message, time)
  end
end

# ---------------------------------------------------------------------------
# Client: Logger that routes entries through named formatters
# ---------------------------------------------------------------------------
class Logger
  FORMATTERS = {
    "json" => [
      "%Y-%m-%dT%H:%M:%SZ",
      '{"ts":"%<ts>s","level":"%<level>s","src":"%<source>s","msg":"%<msg>s"}'
    ],
    "text" => [
      "%H:%M:%S",
      "[%<ts>s] [%-5<level>s] (%<source>s) %<msg>s"
    ],
    "compact" => [
      "%H:%M:%S",
      "%<ts>s %<level>s %<msg>s"
    ]
  }.freeze

  def initialize(formatter_name = "text")
    name, ts_fmt, tmpl = formatter_name, *FORMATTERS.fetch(formatter_name)
    @formatter = FormatterFactory.get(name, ts_fmt, tmpl)
    @entries   = []
  end

  def log(level, source, message)
    entry = LogEntry.new(level, source, message, Time.now, @formatter)
    @entries << entry
    puts entry
  end

  def debug(src, msg) = log("DEBUG", src, msg)
  def info(src, msg)  = log("INFO",  src, msg)
  def warn(src, msg)  = log("WARN",  src, msg)
  def error(src, msg) = log("ERROR", src, msg)

  def entry_count = @entries.size
end

# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
puts "=== Logger (Flyweight Demo) ===\n\n"

puts "--- Creating loggers ---"
app_log  = Logger.new("text")
api_log  = Logger.new("json")
perf_log = Logger.new("compact")
# A second "text" logger — factory reuses the same formatter flyweight
audit_log = Logger.new("text")

puts "\n--- Application log ---"
app_log.debug("AuthService",    "Token validation started")
app_log.info("AuthService",     "User 'alice' authenticated")
app_log.warn("RateLimiter",     "Threshold 80% reached for IP 10.0.0.1")
app_log.error("PaymentGateway", "Stripe timeout after 30s")

puts "\n--- API log (JSON format) ---"
api_log.info("Router",  "GET /api/orders 200 OK")
api_log.error("Router", "POST /api/checkout 503 Service Unavailable")

puts "\n--- Perf log (compact format) ---"
perf_log.info("DB", "query users 12ms")
perf_log.warn("DB", "query reports 3200ms SLOW")

puts "\n--- Audit log (reuses 'text' formatter flyweight) ---"
audit_log.info("AuditTrail", "User 'alice' exported report #42")

puts "\n--- Stats ---"
total = app_log.entry_count + api_log.entry_count + perf_log.entry_count + audit_log.entry_count
puts "Total log entries : #{total}"
puts "Formatter objects : #{FormatterFactory.pool_size} (flyweight pool)"
puts "Formatter keys:"
FormatterFactory.list
```

---

## When To Use

Use the Flyweight pattern **only** when all of the following are true:

1. **Volume is massive.** The application must create a very large number of objects (tens of thousands or more) that would otherwise exhaust available RAM.

2. **Objects contain duplicated data.** A significant portion of each object's state is identical across many instances and could be shared.

3. **Extrinsic state can be extracted.** The unique portion of each object's state can be cleanly separated and passed in at call time.

4. **Shared objects are context-independent.** The shared state does not depend on which context it is used in (otherwise sharing becomes incorrect).

5. **RAM is the bottleneck.** You are willing to accept increased code complexity and potentially extra CPU cycles in exchange for reduced memory consumption.

**Do NOT use Flyweight when:**

- The number of objects is small (the pattern adds complexity for no gain).
- All state is unique per instance (no sharing is possible).
- Object creation cost is not the bottleneck.
- The extrinsic state is so expensive to recompute that CPU becomes the new bottleneck.

---

## Pros & Cons

### Pros

- **Dramatic RAM reduction.** If many thousands of objects share the same intrinsic state, memory usage collapses from O(N * M) to O(K * M) + O(N * E), where K is the number of unique flyweights (usually very small), M is the intrinsic state size, and E is the (small) extrinsic state size per context.
- **Scalability.** Enables object counts that would otherwise be impossible — game particles, map tiles, text glyphs — within practical memory limits.
- **Immutability guarantee.** Because flyweights must be immutable, you get thread-safety for shared state "for free".

### Cons

- **Increased code complexity.** Splitting state into two buckets, adding a factory, and threading extrinsic state through all call sites is non-trivial. Code becomes harder to read and maintain.
- **CPU trade-off.** When extrinsic state must be recalculated on every call to a flyweight method (rather than stored), you trade RAM for CPU cycles. Profile before assuming the trade is worth it.
- **Context management burden.** The client is now responsible for managing and passing extrinsic state correctly. Errors (passing wrong state, forgetting to pass state) lead to subtle bugs.
- **Factory coupling.** Clients must obtain flyweights through the factory, not via direct instantiation, introducing an additional dependency.
- **Not suitable for all objects.** Only works when a clean intrinsic/extrinsic split exists. Forced splits that don't align with the domain lead to awkward APIs.

---

## Relations to Other Patterns

### Composite
The Flyweight pattern is commonly applied to the **leaf nodes** of a Composite tree. In a text editor, the Composite tree represents document structure (paragraphs, lines) while individual character glyphs are Flyweights. This combination lets you build arbitrarily deep document trees without duplicating glyph data at each leaf.

### Singleton
Flyweight and Singleton both involve a reduced number of instances, but for different reasons:
- **Singleton** guarantees exactly one instance of an object (control / coordination concern).
- **Flyweight** may have many instances, but each unique intrinsic-state combination is represented by exactly one shared instance (memory concern).

The FlyweightFactory itself is often implemented as a Singleton (or a static class) so there is one authoritative cache. However, there can be many distinct Flyweight objects in the pool — one per unique intrinsic state key.

### Facade
Both reduce the number of "things" a client must deal with, but Facade simplifies an interface to a subsystem rather than sharing state. They can be combined: a Facade might use a FlyweightFactory under the hood.

### Strategy
A Flyweight can act as a stateless Strategy. If multiple contexts need to perform the same computation (intrinsic) with different inputs (extrinsic), sharing a single Strategy/Flyweight object across all of them avoids per-instance allocation.

---

## Sources

- https://refactoring.guru/design-patterns/flyweight
- https://sourcemaking.com/design_patterns/flyweight
