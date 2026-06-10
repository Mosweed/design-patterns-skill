# Iterator Pattern

**Category:** Behavioral
**Also Known As:** Cursor

---

## Intent

Provide a way to access the elements of an aggregate object sequentially without exposing its underlying representation (list, stack, tree, graph, etc.). The Iterator pattern decouples the algorithm of traversal from the data structure being traversed.

---

## Problem It Solves

Collections are among the most-used data types in programming. Yet a collection is just a container for a group of objects. Most collections store their elements in simple lists, but some are based on stacks, trees, graphs, and other complex structures.

No matter how a collection is structured, it must provide some way of accessing its elements so that other code can use them. There should be a way to go through each element without accessing the same element multiple times.

This sounds like an easy job if you have a list-based collection. You just loop over all the elements. But how do you sequentially traverse elements of a complex data structure such as a tree? One day you may need depth-first traversal; the next day you may want breadth-first; the day after, you might need random access to tree nodes.

Adding more and more traversal algorithms to the collection gradually blurs its primary responsibility (efficient data storage), turning it into a kitchen-sink object that does too many things. The client code that is supposed to work with various collections may not even care how they store their elements — it just wants to work with them through a common interface.

---

## Solution

The Iterator pattern extracts the traversal behavior of a collection into a separate object called an **iterator**.

In addition to implementing the algorithm itself, an iterator object encapsulates all of the traversal details, such as the current position and how many elements are left till the end. Because of this, several iterators can go through the same collection at the same time, independently of each other.

Usually, iterators provide one primary method for fetching elements of the collection. The client can keep running this method until it returns nothing, meaning the iterator has traversed all elements.

All iterators must implement the same interface so that client code is compatible with any collection type or traversal algorithm as long as there is a proper iterator. If you need a special way to traverse a collection, you just create a new iterator class without having to change the collection or the client.

---

## Structure

```
+-------------------+          +-------------------+
| «interface»       |          | «interface»       |
| IterableCollection|<-------->| Iterator          |
+-------------------+          +-------------------+
| +createIterator() |          | +hasNext(): bool  |
+-------------------+          | +next(): T        |
         ^                     | +current(): T     |
         |                     | +rewind(): void   |
         |                     +-------------------+
+-------------------+                   ^
| ConcreteCollection|                   |
+-------------------+          +-------------------+
| -items: T[]       |          | ConcreteIterator  |
|                   |--------->+-------------------+
| +createIterator() |          | -collection: ref  |
+-------------------+          | -position: int    |
                               |                   |
                               | +hasNext(): bool  |
                               | +next(): T        |
                               | +current(): T     |
                               | +rewind(): void   |
                               +-------------------+
                                        |
                                        |  uses
                                        v
                               +-------------------+
                               |     Client        |
                               +-------------------+
                               | -iterator: Iterator|
                               | +doSomething()    |
                               +-------------------+
```

**Flow:**

```
Client --> ConcreteCollection.createIterator()
                |
                v
         ConcreteIterator (holds reference to collection)
                |
         Client --> iterator.hasNext()  --> true/false
         Client --> iterator.next()     --> element
         Client --> iterator.current()  --> element
         Client --> iterator.rewind()   --> reset to start
```

---

## Participants

| Participant | Role |
|---|---|
| **Iterator** | Declares the interface for accessing and traversing elements: `hasNext()`, `next()`, `current()`, `rewind()`. |
| **ConcreteIterator** | Implements the Iterator interface. Tracks the current position in the traversal. Handles the logic for moving through the collection. |
| **IterableCollection** | Declares the interface for creating an iterator object, usually a single `createIterator()` method. |
| **ConcreteCollection** | Implements the IterableCollection interface. Returns a new instance of a particular ConcreteIterator when the client requests one. Stores the actual data. |
| **Client** | Works with both collections and iterators via their interfaces. The client doesn't need to know the concrete classes, making it compatible with any collection or iterator. |

---

## How It Works

1. **Client requests an iterator** by calling `createIterator()` on the collection object. The collection returns a new ConcreteIterator tied to itself.

2. **The ConcreteIterator stores** a reference to the collection and tracks its current traversal position (e.g., an index for a list, a stack pointer for a tree DFS traversal).

3. **The client enters a traversal loop**, calling `hasNext()` on each iteration. The iterator checks whether there are more elements remaining.

4. **If `hasNext()` returns true**, the client calls `next()` to advance the iterator and return the current element. The iterator updates its internal position.

5. **The client uses the returned element** — reads it, processes it, aggregates results, etc.

6. **When `hasNext()` returns false**, the loop ends. If needed, the client calls `rewind()` to reset the iterator back to the beginning.

7. **Multiple iterators** can be active over the same collection simultaneously, each independently tracking its own traversal position. Modifying the collection while iterating is generally unsafe and most implementations will raise an error.

---

## Code Examples

### Python

```python
"""
Iterator Pattern — Python Example
Real-world use case: A file-system directory walker that supports
both breadth-first and depth-first traversal of a folder tree.
The client code works with a single unified iterator interface
regardless of the traversal strategy chosen.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from typing import Iterator as TypingIterator, List, Optional


# ---------------------------------------------------------------------------
# Domain model: a simple in-memory file-system tree
# ---------------------------------------------------------------------------

@dataclass
class FileSystemNode:
    """Represents either a file or a directory in the tree."""
    name: str
    is_directory: bool = False
    size_bytes: int = 0                          # 0 for directories
    children: List["FileSystemNode"] = field(default_factory=list)

    def add_child(self, node: "FileSystemNode") -> None:
        if not self.is_directory:
            raise ValueError("Cannot add children to a file node.")
        self.children.append(node)

    def __repr__(self) -> str:
        kind = "DIR " if self.is_directory else "FILE"
        return f"{kind} {self.name} ({self.size_bytes} bytes)"


# ---------------------------------------------------------------------------
# Iterator interface
# ---------------------------------------------------------------------------

class FileSystemIterator(ABC):
    """Abstract iterator over a file-system tree."""

    @abstractmethod
    def has_next(self) -> bool:
        """Return True if there are more nodes to visit."""

    @abstractmethod
    def next(self) -> FileSystemNode:
        """Return the next node and advance the position."""

    @abstractmethod
    def rewind(self) -> None:
        """Reset traversal to the beginning."""

    # Make iterators usable in Python for-loops via the standard protocol
    def __iter__(self) -> "FileSystemIterator":
        self.rewind()
        return self

    def __next__(self) -> FileSystemNode:
        if not self.has_next():
            raise StopIteration
        return self.next()


# ---------------------------------------------------------------------------
# Concrete iterators
# ---------------------------------------------------------------------------

class DepthFirstIterator(FileSystemIterator):
    """Traverses the directory tree depth-first (pre-order)."""

    def __init__(self, root: FileSystemNode) -> None:
        self._root = root
        self._stack: List[FileSystemNode] = []
        self.rewind()

    def rewind(self) -> None:
        self._stack = [self._root]

    def has_next(self) -> bool:
        return len(self._stack) > 0

    def next(self) -> FileSystemNode:
        if not self.has_next():
            raise StopIteration("No more nodes.")
        node = self._stack.pop()
        # Push children in reverse order so left-most child is visited first
        for child in reversed(node.children):
            self._stack.append(child)
        return node


class BreadthFirstIterator(FileSystemIterator):
    """Traverses the directory tree breadth-first (level-order)."""

    def __init__(self, root: FileSystemNode) -> None:
        self._root = root
        self._queue: deque[FileSystemNode] = deque()
        self.rewind()

    def rewind(self) -> None:
        self._queue = deque([self._root])

    def has_next(self) -> bool:
        return len(self._queue) > 0

    def next(self) -> FileSystemNode:
        if not self.has_next():
            raise StopIteration("No more nodes.")
        node = self._queue.popleft()
        self._queue.extend(node.children)
        return node


class FilesOnlyIterator(FileSystemIterator):
    """Wraps another iterator and filters out directories, yielding files only."""

    def __init__(self, inner: FileSystemIterator) -> None:
        self._inner = inner
        self._next_file: Optional[FileSystemNode] = None
        self._advance()

    def _advance(self) -> None:
        """Pre-fetch the next file node."""
        self._next_file = None
        while self._inner.has_next():
            candidate = self._inner.next()
            if not candidate.is_directory:
                self._next_file = candidate
                return

    def rewind(self) -> None:
        self._inner.rewind()
        self._advance()

    def has_next(self) -> bool:
        return self._next_file is not None

    def next(self) -> FileSystemNode:
        if self._next_file is None:
            raise StopIteration("No more file nodes.")
        result = self._next_file
        self._advance()
        return result


# ---------------------------------------------------------------------------
# Iterable collection
# ---------------------------------------------------------------------------

class DirectoryTree:
    """
    Iterable collection backed by a file-system tree.
    Supports multiple traversal strategies via factory methods.
    """

    def __init__(self, root: FileSystemNode) -> None:
        self._root = root

    def create_depth_first_iterator(self) -> DepthFirstIterator:
        return DepthFirstIterator(self._root)

    def create_breadth_first_iterator(self) -> BreadthFirstIterator:
        return BreadthFirstIterator(self._root)

    def create_files_only_iterator(self) -> FilesOnlyIterator:
        """Returns only file nodes, using depth-first traversal underneath."""
        return FilesOnlyIterator(self.create_depth_first_iterator())

    def total_size(self) -> int:
        """Compute total size of all files using the files-only iterator."""
        total = 0
        for node in self.create_files_only_iterator():
            total += node.size_bytes
        return total


# ---------------------------------------------------------------------------
# Client code
# ---------------------------------------------------------------------------

def build_sample_tree() -> FileSystemNode:
    """Build a representative directory tree for demonstration."""
    root = FileSystemNode("home", is_directory=True)

    docs = FileSystemNode("Documents", is_directory=True)
    docs.add_child(FileSystemNode("resume.pdf",      size_bytes=245_000))
    docs.add_child(FileSystemNode("cover_letter.docx", size_bytes=18_000))

    projects = FileSystemNode("Projects", is_directory=True)

    web = FileSystemNode("web-app", is_directory=True)
    web.add_child(FileSystemNode("index.html",  size_bytes=4_200))
    web.add_child(FileSystemNode("styles.css",  size_bytes=8_900))
    web.add_child(FileSystemNode("app.js",      size_bytes=55_000))
    projects.add_child(web)

    ml = FileSystemNode("ml-model", is_directory=True)
    ml.add_child(FileSystemNode("train.py",     size_bytes=12_000))
    ml.add_child(FileSystemNode("model.pkl",    size_bytes=2_048_000))
    projects.add_child(ml)

    root.add_child(docs)
    root.add_child(projects)
    root.add_child(FileSystemNode(".bashrc",    size_bytes=3_100))
    return root


def main() -> None:
    tree = DirectoryTree(build_sample_tree())

    print("=== Depth-First Traversal ===")
    for node in tree.create_depth_first_iterator():
        indent = "  " if not node.is_directory else ""
        print(f"{indent}{node}")

    print("\n=== Breadth-First Traversal ===")
    for node in tree.create_breadth_first_iterator():
        print(node)

    print("\n=== Files Only (depth-first) ===")
    for node in tree.create_files_only_iterator():
        print(f"  {node.name:30s}  {node.size_bytes:>10,} bytes")

    print(f"\nTotal disk usage: {tree.total_size():,} bytes")


if __name__ == "__main__":
    main()
```

---

### Java

```java
/**
 * Iterator Pattern — Java Example
 * Real-world use case: A paginated REST-API result set iterator.
 * The client iterates over Employee records as if they were a
 * plain local list, while the iterator transparently fetches
 * successive pages from a remote API under the hood.
 */

import java.util.*;

// ---------------------------------------------------------------------------
// Domain model
// ---------------------------------------------------------------------------

record Employee(int id, String name, String department, double salary) {
    @Override public String toString() {
        return String.format("Employee{id=%d, name='%s', dept='%s', salary=%.0f}",
                id, name, department, salary);
    }
}

// ---------------------------------------------------------------------------
// Simulated remote API (replaces a real HTTP client for demonstration)
// ---------------------------------------------------------------------------

class EmployeeApiClient {
    private static final List<Employee> DATABASE = List.of(
        new Employee(1,  "Alice Martin",   "Engineering", 95_000),
        new Employee(2,  "Bob Chen",        "Engineering", 88_000),
        new Employee(3,  "Carol White",     "Marketing",   72_000),
        new Employee(4,  "David Kim",       "Engineering", 102_000),
        new Employee(5,  "Eva Gonzalez",    "HR",          65_000),
        new Employee(6,  "Frank Bell",      "Marketing",   78_000),
        new Employee(7,  "Grace Liu",       "Engineering", 115_000),
        new Employee(8,  "Henry Park",      "HR",          67_000),
        new Employee(9,  "Iris Brown",      "Finance",     91_000),
        new Employee(10, "Jack Wilson",     "Finance",     87_000),
        new Employee(11, "Karen Patel",     "Engineering", 99_000),
        new Employee(12, "Leo Nguyen",      "Marketing",   74_000)
    );

    /**
     * Simulates a paginated GET /employees?page=X&size=Y endpoint.
     * Returns an empty list when the page is beyond the last record.
     */
    public List<Employee> fetchPage(int page, int pageSize) {
        System.out.printf("  [API] Fetching page %d (size=%d)%n", page, pageSize);
        int fromIndex = page * pageSize;
        if (fromIndex >= DATABASE.size()) {
            return Collections.emptyList();
        }
        int toIndex = Math.min(fromIndex + pageSize, DATABASE.size());
        return DATABASE.subList(fromIndex, toIndex);
    }
}

// ---------------------------------------------------------------------------
// Iterator interface
// ---------------------------------------------------------------------------

interface Iterator<T> {
    boolean hasNext();
    T next();
    void reset();
}

// ---------------------------------------------------------------------------
// Concrete iterator — fetches pages lazily
// ---------------------------------------------------------------------------

class PaginatedEmployeeIterator implements Iterator<Employee> {
    private final EmployeeApiClient apiClient;
    private final int pageSize;

    private int currentPage = 0;
    private List<Employee> currentPageData = new ArrayList<>();
    private int indexInPage = 0;
    private boolean exhausted = false;

    public PaginatedEmployeeIterator(EmployeeApiClient apiClient, int pageSize) {
        this.apiClient = apiClient;
        this.pageSize  = pageSize;
        loadNextPage();
    }

    private void loadNextPage() {
        currentPageData = apiClient.fetchPage(currentPage, pageSize);
        indexInPage = 0;
        if (currentPageData.isEmpty()) {
            exhausted = true;
        }
    }

    @Override
    public boolean hasNext() {
        return !exhausted;
    }

    @Override
    public Employee next() {
        if (!hasNext()) {
            throw new NoSuchElementException("No more employees.");
        }
        Employee emp = currentPageData.get(indexInPage++);

        // If we've consumed the current page, pre-load the next one
        if (indexInPage >= currentPageData.size()) {
            currentPage++;
            loadNextPage();
        }
        return emp;
    }

    @Override
    public void reset() {
        currentPage     = 0;
        indexInPage     = 0;
        currentPageData = new ArrayList<>();
        exhausted       = false;
        loadNextPage();
    }
}

// ---------------------------------------------------------------------------
// Iterable collection
// ---------------------------------------------------------------------------

interface IterableCollection<T> {
    Iterator<T> createIterator();
}

class EmployeeCollection implements IterableCollection<Employee> {
    private final EmployeeApiClient apiClient;
    private final int pageSize;

    public EmployeeCollection(EmployeeApiClient apiClient, int pageSize) {
        this.apiClient = apiClient;
        this.pageSize  = pageSize;
    }

    @Override
    public Iterator<Employee> createIterator() {
        return new PaginatedEmployeeIterator(apiClient, pageSize);
    }
}

// ---------------------------------------------------------------------------
// Client code
// ---------------------------------------------------------------------------

public class IteratorPatternDemo {

    /** Compute total payroll using the paginated iterator. */
    static double totalPayroll(Iterator<Employee> it) {
        double total = 0;
        while (it.hasNext()) {
            total += it.next().salary();
        }
        return total;
    }

    /** Filter employees by department. */
    static List<Employee> filterByDept(Iterator<Employee> it, String dept) {
        List<Employee> result = new ArrayList<>();
        while (it.hasNext()) {
            Employee e = it.next();
            if (dept.equalsIgnoreCase(e.department())) {
                result.add(e);
            }
        }
        return result;
    }

    public static void main(String[] args) {
        EmployeeApiClient api        = new EmployeeApiClient();
        EmployeeCollection collection = new EmployeeCollection(api, 4); // 4 records per page

        System.out.println("=== All Employees ===");
        Iterator<Employee> it = collection.createIterator();
        while (it.hasNext()) {
            System.out.println("  " + it.next());
        }

        System.out.println("\n=== Engineering Department ===");
        // Each createIterator() call returns a fresh iterator (new pagination state)
        List<Employee> engineers = filterByDept(collection.createIterator(), "Engineering");
        engineers.forEach(e -> System.out.println("  " + e));

        System.out.println("\n=== Total Payroll ===");
        double payroll = totalPayroll(collection.createIterator());
        System.out.printf("  $%.0f%n", payroll);

        System.out.println("\n=== Reset Demonstration ===");
        Iterator<Employee> sameIt = collection.createIterator();
        System.out.println("  First employee (before reset): " + sameIt.next());
        sameIt.reset();
        System.out.println("  First employee (after reset):  " + sameIt.next());
    }
}
```

---

### C++

```cpp
/**
 * Iterator Pattern — C++ Example
 * Real-world use case: A song playlist that supports sequential
 * playback, reverse playback, and shuffle — each as a separate
 * iterator type. The media player (client) works through a single
 * PlaylistIterator interface regardless of playback mode.
 */

#include <algorithm>
#include <iostream>
#include <memory>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

// ---------------------------------------------------------------------------
// Domain model
// ---------------------------------------------------------------------------

struct Song {
    std::string title;
    std::string artist;
    int         duration_seconds;  // e.g., 210 = 3:30

    std::string formatted_duration() const {
        return std::to_string(duration_seconds / 60) + ":"
             + (duration_seconds % 60 < 10 ? "0" : "")
             + std::to_string(duration_seconds % 60);
    }

    friend std::ostream& operator<<(std::ostream& os, const Song& s) {
        return os << '"' << s.title << '"' << " by " << s.artist
                  << " [" << s.formatted_duration() << "]";
    }
};

// ---------------------------------------------------------------------------
// Iterator interface
// ---------------------------------------------------------------------------

template<typename T>
class Iterator {
public:
    virtual ~Iterator() = default;
    virtual bool   has_next()  const = 0;
    virtual T      next()            = 0;
    virtual void   rewind()          = 0;
};

// ---------------------------------------------------------------------------
// Concrete iterators
// ---------------------------------------------------------------------------

class ForwardIterator : public Iterator<Song> {
    const std::vector<Song>& songs_;
    std::size_t              pos_;
public:
    explicit ForwardIterator(const std::vector<Song>& songs)
        : songs_(songs), pos_(0) {}

    bool has_next()  const override { return pos_ < songs_.size(); }
    Song next()            override {
        if (!has_next()) throw std::out_of_range("No more songs.");
        return songs_[pos_++];
    }
    void rewind()          override { pos_ = 0; }
};

class ReverseIterator : public Iterator<Song> {
    const std::vector<Song>& songs_;
    int                      pos_;   // use signed int to allow -1 sentinel
public:
    explicit ReverseIterator(const std::vector<Song>& songs)
        : songs_(songs), pos_(static_cast<int>(songs.size()) - 1) {}

    bool has_next()  const override { return pos_ >= 0; }
    Song next()            override {
        if (!has_next()) throw std::out_of_range("No more songs.");
        return songs_[pos_--];
    }
    void rewind()          override {
        pos_ = static_cast<int>(songs_.size()) - 1;
    }
};

class ShuffleIterator : public Iterator<Song> {
    const std::vector<Song>& songs_;
    std::vector<std::size_t> order_;
    std::size_t              pos_;

    void build_order() {
        order_.resize(songs_.size());
        std::iota(order_.begin(), order_.end(), 0);
        std::mt19937 rng(std::random_device{}());
        std::shuffle(order_.begin(), order_.end(), rng);
        pos_ = 0;
    }
public:
    explicit ShuffleIterator(const std::vector<Song>& songs)
        : songs_(songs), pos_(0) { build_order(); }

    bool has_next()  const override { return pos_ < order_.size(); }
    Song next()            override {
        if (!has_next()) throw std::out_of_range("No more songs.");
        return songs_[order_[pos_++]];
    }
    void rewind()          override { build_order(); }  // re-shuffle on rewind
};

// ---------------------------------------------------------------------------
// Iterable collection
// ---------------------------------------------------------------------------

class Playlist {
    std::string        name_;
    std::vector<Song>  songs_;
public:
    explicit Playlist(std::string name) : name_(std::move(name)) {}

    void add_song(Song song)     { songs_.push_back(std::move(song)); }
    const std::string& name()    const { return name_; }
    std::size_t size()           const { return songs_.size(); }

    std::unique_ptr<Iterator<Song>> create_forward_iterator() const {
        return std::make_unique<ForwardIterator>(songs_);
    }
    std::unique_ptr<Iterator<Song>> create_reverse_iterator() const {
        return std::make_unique<ReverseIterator>(songs_);
    }
    std::unique_ptr<Iterator<Song>> create_shuffle_iterator() const {
        return std::make_unique<ShuffleIterator>(songs_);
    }
};

// ---------------------------------------------------------------------------
// Client: MediaPlayer
// ---------------------------------------------------------------------------

class MediaPlayer {
    std::string name_;
public:
    explicit MediaPlayer(std::string name) : name_(std::move(name)) {}

    void play(Iterator<Song>& it, const std::string& mode) {
        std::cout << "\n[" << name_ << "] Playing in " << mode << " mode:\n";
        int track = 1;
        while (it.has_next()) {
            Song s = it.next();
            std::cout << "  " << track++ << ". " << s << "\n";
        }
        std::cout << "  -- End of playlist --\n";
    }

    int total_duration(Iterator<Song>& it) {
        int total = 0;
        while (it.has_next()) total += it.next().duration_seconds;
        return total;
    }
};

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    Playlist playlist("Summer Vibes 2025");
    playlist.add_song({"Blinding Lights",   "The Weeknd",    200});
    playlist.add_song({"As It Was",          "Harry Styles",  167});
    playlist.add_song({"Levitating",         "Dua Lipa",      203});
    playlist.add_song({"Stay",               "The Kid LAROI", 141});
    playlist.add_song({"Heat Waves",         "Glass Animals", 238});
    playlist.add_song({"Watermelon Sugar",   "Harry Styles",  174});

    MediaPlayer player("MyPlayer");

    // Forward playback
    auto fwd = playlist.create_forward_iterator();
    player.play(*fwd, "Forward");

    // Reverse playback — same playlist, different iterator
    auto rev = playlist.create_reverse_iterator();
    player.play(*rev, "Reverse");

    // Shuffle playback
    auto shuf = playlist.create_shuffle_iterator();
    player.play(*shuf, "Shuffle");

    // Compute total runtime using forward iterator
    auto fwd2 = playlist.create_forward_iterator();
    int  secs  = player.total_duration(*fwd2);
    std::cout << "\nTotal playlist duration: "
              << secs / 60 << " min " << secs % 60 << " sec\n";

    return 0;
}
```

---

### C#

```csharp
/**
 * Iterator Pattern — C# Example
 * Real-world use case: A product catalog that supports multiple
 * filtered views (all products, by category, by price range) via
 * custom iterators.  The store front (client) works with a generic
 * IIterator<T> regardless of which filter is active.
 *
 * Note: C# already has IEnumerable<T>/IEnumerator<T>; this example
 * implements the raw pattern from scratch to illustrate the mechanics,
 * then shows idiomatic integration with foreach via IEnumerable<T>.
 */

using System;
using System.Collections.Generic;

// ---------------------------------------------------------------------------
// Domain model
// ---------------------------------------------------------------------------

public class Product
{
    public int    Id         { get; init; }
    public string Name       { get; init; } = string.Empty;
    public string Category   { get; init; } = string.Empty;
    public decimal Price     { get; init; }
    public bool   InStock    { get; init; }

    public override string ToString() =>
        $"[{Id:D3}] {Name,-30} {Category,-12} ${Price,8:F2}  {(InStock ? "In Stock" : "Out of Stock")}";
}

// ---------------------------------------------------------------------------
// Iterator interface (hand-rolled, separate from IEnumerator<T>)
// ---------------------------------------------------------------------------

public interface IIterator<T>
{
    bool HasNext();
    T    Next();
    void Reset();
}

// ---------------------------------------------------------------------------
// Concrete iterators
// ---------------------------------------------------------------------------

/// <summary>Iterates over all products in insertion order.</summary>
public class AllProductsIterator : IIterator<Product>
{
    private readonly IReadOnlyList<Product> _products;
    private int _index;

    public AllProductsIterator(IReadOnlyList<Product> products)
    {
        _products = products;
        _index    = 0;
    }

    public bool    HasNext() => _index < _products.Count;
    public Product Next()    => HasNext() ? _products[_index++]
                                          : throw new InvalidOperationException("No more products.");
    public void    Reset()   => _index = 0;
}

/// <summary>Filters products by category.</summary>
public class CategoryIterator : IIterator<Product>
{
    private readonly IReadOnlyList<Product> _products;
    private readonly string                 _category;
    private int                             _index;
    private Product?                        _prefetched;

    public CategoryIterator(IReadOnlyList<Product> products, string category)
    {
        _products = products;
        _category = category;
        _index    = 0;
        Prefetch();
    }

    private void Prefetch()
    {
        _prefetched = null;
        while (_index < _products.Count)
        {
            var p = _products[_index++];
            if (p.Category.Equals(_category, StringComparison.OrdinalIgnoreCase))
            {
                _prefetched = p;
                return;
            }
        }
    }

    public bool    HasNext() => _prefetched is not null;
    public Product Next()
    {
        var result = _prefetched ?? throw new InvalidOperationException("No more products.");
        Prefetch();
        return result;
    }
    public void Reset() { _index = 0; Prefetch(); }
}

/// <summary>Filters products by price range, in-stock only.</summary>
public class PriceRangeIterator : IIterator<Product>
{
    private readonly IReadOnlyList<Product> _products;
    private readonly decimal                _min;
    private readonly decimal                _max;
    private int                             _index;
    private Product?                        _prefetched;

    public PriceRangeIterator(IReadOnlyList<Product> products, decimal min, decimal max)
    {
        _products = products;
        _min      = min;
        _max      = max;
        _index    = 0;
        Prefetch();
    }

    private void Prefetch()
    {
        _prefetched = null;
        while (_index < _products.Count)
        {
            var p = _products[_index++];
            if (p.InStock && p.Price >= _min && p.Price <= _max)
            {
                _prefetched = p;
                return;
            }
        }
    }

    public bool    HasNext() => _prefetched is not null;
    public Product Next()
    {
        var result = _prefetched ?? throw new InvalidOperationException("No more products.");
        Prefetch();
        return result;
    }
    public void Reset() { _index = 0; Prefetch(); }
}

// ---------------------------------------------------------------------------
// Iterable collection
// ---------------------------------------------------------------------------

public interface IProductCollection
{
    IIterator<Product> CreateAllIterator();
    IIterator<Product> CreateCategoryIterator(string category);
    IIterator<Product> CreatePriceRangeIterator(decimal min, decimal max);
}

public class ProductCatalog : IProductCollection
{
    private readonly List<Product> _products = new();

    public void AddProduct(Product p) => _products.Add(p);

    public IIterator<Product> CreateAllIterator()
        => new AllProductsIterator(_products.AsReadOnly());

    public IIterator<Product> CreateCategoryIterator(string category)
        => new CategoryIterator(_products.AsReadOnly(), category);

    public IIterator<Product> CreatePriceRangeIterator(decimal min, decimal max)
        => new PriceRangeIterator(_products.AsReadOnly(), min, max);
}

// ---------------------------------------------------------------------------
// Client code (StoreFront)
// ---------------------------------------------------------------------------

public class StoreFront
{
    private readonly ProductCatalog _catalog;

    public StoreFront(ProductCatalog catalog) => _catalog = catalog;

    private static void PrintProducts(IIterator<Product> it, string header)
    {
        Console.WriteLine($"\n=== {header} ===");
        Console.WriteLine($"{"ID",-5} {"Name",-30} {"Category",-12} {"Price",9}  {"Availability"}");
        Console.WriteLine(new string('-', 75));
        while (it.HasNext())
            Console.WriteLine(it.Next());
    }

    private static decimal TotalValue(IIterator<Product> it)
    {
        decimal total = 0m;
        while (it.HasNext()) total += it.Next().Price;
        return total;
    }

    public void Run()
    {
        PrintProducts(_catalog.CreateAllIterator(), "Full Catalog");

        PrintProducts(
            _catalog.CreateCategoryIterator("Electronics"),
            "Electronics Only");

        PrintProducts(
            _catalog.CreatePriceRangeIterator(20m, 150m),
            "In-Stock Products $20 – $150");

        decimal catalogValue = TotalValue(_catalog.CreateAllIterator());
        Console.WriteLine($"\nTotal catalog value: ${catalogValue:F2}");
    }
}

// ---------------------------------------------------------------------------
// Program entry point
// ---------------------------------------------------------------------------

public class Program
{
    public static void Main()
    {
        var catalog = new ProductCatalog();
        catalog.AddProduct(new Product { Id = 1,  Name = "Wireless Mouse",       Category = "Electronics", Price = 29.99m,  InStock = true  });
        catalog.AddProduct(new Product { Id = 2,  Name = "Mechanical Keyboard",  Category = "Electronics", Price = 149.99m, InStock = true  });
        catalog.AddProduct(new Product { Id = 3,  Name = "USB-C Hub",            Category = "Electronics", Price = 49.99m,  InStock = false });
        catalog.AddProduct(new Product { Id = 4,  Name = "Standing Desk",        Category = "Furniture",   Price = 599.00m, InStock = true  });
        catalog.AddProduct(new Product { Id = 5,  Name = "Ergonomic Chair",      Category = "Furniture",   Price = 389.00m, InStock = true  });
        catalog.AddProduct(new Product { Id = 6,  Name = "Notebook",             Category = "Stationery",  Price = 5.99m,   InStock = true  });
        catalog.AddProduct(new Product { Id = 7,  Name = "Monitor 27\"",         Category = "Electronics", Price = 349.00m, InStock = true  });
        catalog.AddProduct(new Product { Id = 8,  Name = "Desk Lamp",            Category = "Furniture",   Price = 39.99m,  InStock = true  });
        catalog.AddProduct(new Product { Id = 9,  Name = "Ballpoint Pens (12pk)",Category = "Stationery",  Price = 8.49m,   InStock = true  });
        catalog.AddProduct(new Product { Id = 10, Name = "Webcam HD",            Category = "Electronics", Price = 79.99m,  InStock = false });

        new StoreFront(catalog).Run();
    }
}
```

---

### TypeScript

```typescript
/**
 * Iterator Pattern — TypeScript Example
 * Real-world use case: A social-media feed aggregator that unifies
 * posts from multiple platforms (Twitter-like, Reddit-like) behind
 * a single FeedIterator interface.  The dashboard (client) renders
 * a merged, chronologically sorted feed without knowing anything
 * about each platform's internal data format.
 */

// ---------------------------------------------------------------------------
// Domain model
// ---------------------------------------------------------------------------

interface Post {
  id: string;
  platform: "twitter" | "reddit" | "hackernews";
  author: string;
  content: string;
  likes: number;
  publishedAt: Date;
}

// ---------------------------------------------------------------------------
// Iterator interface
// ---------------------------------------------------------------------------

interface FeedIterator {
  hasNext(): boolean;
  next(): Post;
  reset(): void;
}

// ---------------------------------------------------------------------------
// Simulated data sources
// ---------------------------------------------------------------------------

function makeTwitterFeed(): Post[] {
  return [
    { id: "tw1", platform: "twitter", author: "@alice",  content: "Just shipped a new feature! #buildinpublic", likes: 142, publishedAt: new Date("2025-06-09T10:00:00Z") },
    { id: "tw2", platform: "twitter", author: "@bob",    content: "Hot take: tabs > spaces. Fight me.",          likes: 891, publishedAt: new Date("2025-06-09T09:30:00Z") },
    { id: "tw3", platform: "twitter", author: "@carol",  content: "TypeScript 6.0 looks amazing so far.",        likes: 320, publishedAt: new Date("2025-06-09T08:15:00Z") },
  ];
}

function makeRedditFeed(): Post[] {
  return [
    { id: "rd1", platform: "reddit", author: "u/devguru",   content: "Iterator Pattern explained with examples",  likes: 2_400, publishedAt: new Date("2025-06-09T11:00:00Z") },
    { id: "rd2", platform: "reddit", author: "u/rustlover",  content: "Why I rewrote my app in Rust and regret nothing", likes: 5_800, publishedAt: new Date("2025-06-09T07:45:00Z") },
  ];
}

function makeHNFeed(): Post[] {
  return [
    { id: "hn1", platform: "hackernews", author: "thrwaway42",   content: "Ask HN: What's your go-to debugging workflow?", likes: 310, publishedAt: new Date("2025-06-09T10:30:00Z") },
    { id: "hn2", platform: "hackernews", author: "pragmaticdev",  content: "Show HN: I built a serverless iterator library",  likes: 175, publishedAt: new Date("2025-06-09T09:00:00Z") },
  ];
}

// ---------------------------------------------------------------------------
// Concrete iterators
// ---------------------------------------------------------------------------

/** Iterates over a single platform's feed in chronological order. */
class SingleFeedIterator implements FeedIterator {
  private index: number = 0;
  private posts: Post[];

  constructor(posts: Post[]) {
    // Sort newest-first by default
    this.posts = [...posts].sort(
      (a, b) => b.publishedAt.getTime() - a.publishedAt.getTime()
    );
  }

  hasNext(): boolean { return this.index < this.posts.length; }

  next(): Post {
    if (!this.hasNext()) throw new Error("No more posts.");
    return this.posts[this.index++];
  }

  reset(): void { this.index = 0; }
}

/**
 * Merged iterator — takes N platform iterators and yields posts in
 * globally sorted (newest-first) order using an N-way merge.
 */
class MergedFeedIterator implements FeedIterator {
  private sorted: Post[];
  private index: number = 0;

  constructor(private readonly iterators: FeedIterator[]) {
    // Collect all posts from all iterators, then sort globally
    const all: Post[] = [];
    for (const it of iterators) {
      it.reset();
      while (it.hasNext()) all.push(it.next());
    }
    this.sorted = all.sort(
      (a, b) => b.publishedAt.getTime() - a.publishedAt.getTime()
    );
  }

  hasNext(): boolean { return this.index < this.sorted.length; }

  next(): Post {
    if (!this.hasNext()) throw new Error("No more posts.");
    return this.sorted[this.index++];
  }

  reset(): void { this.index = 0; }
}

/** Filters posts with fewer likes than a threshold. */
class ViralPostIterator implements FeedIterator {
  private prefetched: Post | null = null;
  private buffer: Post[];
  private index: number = 0;

  constructor(source: FeedIterator, private readonly minLikes: number) {
    const all: Post[] = [];
    source.reset();
    while (source.hasNext()) all.push(source.next());
    this.buffer = all.filter(p => p.likes >= minLikes);
    this.buffer.sort((a, b) => b.likes - a.likes); // sort by popularity
  }

  hasNext(): boolean { return this.index < this.buffer.length; }

  next(): Post {
    if (!this.hasNext()) throw new Error("No more viral posts.");
    return this.buffer[this.index++];
  }

  reset(): void { this.index = 0; }
}

// ---------------------------------------------------------------------------
// Iterable collection
// ---------------------------------------------------------------------------

interface FeedCollection {
  createIterator(): FeedIterator;
}

class SocialDashboard implements FeedCollection {
  private twitterIterator: SingleFeedIterator;
  private redditIterator: SingleFeedIterator;
  private hnIterator: SingleFeedIterator;

  constructor() {
    this.twitterIterator = new SingleFeedIterator(makeTwitterFeed());
    this.redditIterator  = new SingleFeedIterator(makeRedditFeed());
    this.hnIterator      = new SingleFeedIterator(makeHNFeed());
  }

  /** Default: merged feed from all platforms. */
  createIterator(): FeedIterator {
    return new MergedFeedIterator([
      this.twitterIterator,
      this.redditIterator,
      this.hnIterator,
    ]);
  }

  /** Only posts from a specific platform. */
  createPlatformIterator(platform: Post["platform"]): FeedIterator {
    const map: Record<Post["platform"], FeedIterator> = {
      twitter:     this.twitterIterator,
      reddit:      this.redditIterator,
      hackernews:  this.hnIterator,
    };
    map[platform].reset();
    return map[platform];
  }

  /** Only posts meeting or exceeding the like threshold. */
  createViralIterator(minLikes: number): FeedIterator {
    return new ViralPostIterator(this.createIterator(), minLikes);
  }
}

// ---------------------------------------------------------------------------
// Client code
// ---------------------------------------------------------------------------

function formatPost(p: Post): string {
  const time = p.publishedAt.toISOString().slice(11, 16) + " UTC";
  return `[${p.platform.padEnd(11)}] ${time}  ${p.author.padEnd(15)} ${p.likes.toLocaleString().padStart(6)} likes  "${p.content}"`;
}

function printFeed(it: FeedIterator, header: string): void {
  console.log(`\n=== ${header} ===`);
  while (it.hasNext()) {
    console.log(" ", formatPost(it.next()));
  }
}

const dashboard = new SocialDashboard();

printFeed(dashboard.createIterator(), "All Platforms (Newest First)");
printFeed(dashboard.createPlatformIterator("reddit"), "Reddit Only");
printFeed(dashboard.createViralIterator(300), "Viral Posts (300+ likes)");
```

---

### Go

```go
// Iterator Pattern — Go Example
// Real-world use case: A database query result set walker.
// The application iterates over rows from multiple simulated
// "database tables" (Users, Orders) using a single Row iterator
// interface, without knowing the storage layout.
package main

import (
	"errors"
	"fmt"
	"strings"
	"time"
)

// ---------------------------------------------------------------------------
// Domain models
// ---------------------------------------------------------------------------

type User struct {
	ID        int
	Username  string
	Email     string
	CreatedAt time.Time
}

func (u User) String() string {
	return fmt.Sprintf("User{id=%d, username=%q, email=%q, created=%s}",
		u.ID, u.Username, u.Email, u.CreatedAt.Format("2006-01-02"))
}

type Order struct {
	ID         int
	UserID     int
	Product    string
	Amount     float64
	OrderedAt  time.Time
}

func (o Order) String() string {
	return fmt.Sprintf("Order{id=%d, user=%d, product=%q, amount=$%.2f, date=%s}",
		o.ID, o.UserID, o.Product, o.Amount, o.OrderedAt.Format("2006-01-02"))
}

// ---------------------------------------------------------------------------
// Generic iterator interface (using any / interface{})
// ---------------------------------------------------------------------------

// Iterator is the base interface every concrete iterator must satisfy.
type Iterator[T any] interface {
	HasNext() bool
	Next() (T, error)
	Reset()
}

// ---------------------------------------------------------------------------
// Concrete iterator: UserIterator
// ---------------------------------------------------------------------------

type UserIterator struct {
	users  []User
	cursor int
}

func NewUserIterator(users []User) *UserIterator {
	return &UserIterator{users: users, cursor: 0}
}

func (it *UserIterator) HasNext() bool {
	return it.cursor < len(it.users)
}

func (it *UserIterator) Next() (User, error) {
	if !it.HasNext() {
		return User{}, errors.New("user iterator exhausted")
	}
	u := it.users[it.cursor]
	it.cursor++
	return u, nil
}

func (it *UserIterator) Reset() {
	it.cursor = 0
}

// ---------------------------------------------------------------------------
// Concrete iterator: OrderIterator (filtered by user ID)
// ---------------------------------------------------------------------------

type OrderIterator struct {
	orders   []Order
	filterID int // 0 = no filter
	cursor   int
	buffer   []Order // pre-filtered slice
}

func NewOrderIterator(orders []Order, filterUserID int) *OrderIterator {
	it := &OrderIterator{orders: orders, filterID: filterUserID}
	it.buildBuffer()
	return it
}

func (it *OrderIterator) buildBuffer() {
	it.buffer = nil
	for _, o := range it.orders {
		if it.filterID == 0 || o.UserID == it.filterID {
			it.buffer = append(it.buffer, o)
		}
	}
	it.cursor = 0
}

func (it *OrderIterator) HasNext() bool {
	return it.cursor < len(it.buffer)
}

func (it *OrderIterator) Next() (Order, error) {
	if !it.HasNext() {
		return Order{}, errors.New("order iterator exhausted")
	}
	o := it.buffer[it.cursor]
	it.cursor++
	return o, nil
}

func (it *OrderIterator) Reset() {
	it.cursor = 0
}

// ---------------------------------------------------------------------------
// Iterable collections
// ---------------------------------------------------------------------------

type UserTable struct {
	rows []User
}

func (t *UserTable) AddRow(u User) { t.rows = append(t.rows, u) }

func (t *UserTable) CreateIterator() Iterator[User] {
	return NewUserIterator(t.rows)
}

// FilterByUsername returns an iterator over users whose username
// contains the given substring (case-insensitive).
func (t *UserTable) FilterByUsername(sub string) Iterator[User] {
	var filtered []User
	for _, u := range t.rows {
		if strings.Contains(strings.ToLower(u.Username), strings.ToLower(sub)) {
			filtered = append(filtered, u)
		}
	}
	return NewUserIterator(filtered)
}

type OrderTable struct {
	rows []Order
}

func (t *OrderTable) AddRow(o Order) { t.rows = append(t.rows, o) }

func (t *OrderTable) CreateIterator() Iterator[Order] {
	return NewOrderIterator(t.rows, 0)
}

func (t *OrderTable) CreateIteratorForUser(userID int) Iterator[Order] {
	return NewOrderIterator(t.rows, userID)
}

// ---------------------------------------------------------------------------
// Client: reporting functions
// ---------------------------------------------------------------------------

func printUsers(it Iterator[User], header string) {
	fmt.Printf("\n=== %s ===\n", header)
	for it.HasNext() {
		u, err := it.Next()
		if err != nil {
			fmt.Println("ERROR:", err)
			break
		}
		fmt.Println(" ", u)
	}
}

func printOrders(it Iterator[Order], header string) {
	fmt.Printf("\n=== %s ===\n", header)
	total := 0.0
	count := 0
	for it.HasNext() {
		o, err := it.Next()
		if err != nil {
			fmt.Println("ERROR:", err)
			break
		}
		fmt.Printf("  %s\n", o)
		total += o.Amount
		count++
	}
	fmt.Printf("  --> %d orders, total $%.2f\n", count, total)
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

func main() {
	day := func(s string) time.Time {
		t, _ := time.Parse("2006-01-02", s)
		return t
	}

	// Populate tables
	users := &UserTable{}
	users.AddRow(User{1, "alice_w",   "alice@example.com",  day("2023-01-15")})
	users.AddRow(User{2, "bob_dev",   "bob@example.com",    day("2023-03-20")})
	users.AddRow(User{3, "carol_ux",  "carol@example.com",  day("2024-06-01")})
	users.AddRow(User{4, "dave_ops",  "dave@example.com",   day("2024-11-30")})
	users.AddRow(User{5, "alice_qa",  "alice2@example.com", day("2025-02-10")})

	orders := &OrderTable{}
	orders.AddRow(Order{101, 1, "Laptop Pro",      1_299.00, day("2025-01-10")})
	orders.AddRow(Order{102, 2, "Mechanical Keyboard", 149.00, day("2025-02-14")})
	orders.AddRow(Order{103, 1, "USB-C Hub",          49.99,  day("2025-03-05")})
	orders.AddRow(Order{104, 3, "Standing Desk",      599.00, day("2025-03-22")})
	orders.AddRow(Order{105, 2, "Monitor 27in",       349.00, day("2025-04-01")})
	orders.AddRow(Order{106, 1, "Webcam HD",           79.99, day("2025-04-18")})
	orders.AddRow(Order{107, 4, "Ergonomic Chair",    389.00, day("2025-05-03")})

	// All users
	printUsers(users.CreateIterator(), "All Users")

	// Filter users by name
	printUsers(users.FilterByUsername("alice"), "Users matching 'alice'")

	// All orders
	printOrders(orders.CreateIterator(), "All Orders")

	// Orders for a specific user
	printOrders(orders.CreateIteratorForUser(1), "Orders for User #1 (alice_w)")

	// Demonstrate reset
	it := orders.CreateIterator()
	first, _ := it.Next()
	fmt.Printf("\nFirst order (before reset): %s\n", first)
	it.Reset()
	first, _ = it.Next()
	fmt.Printf("First order (after reset):  %s\n", first)
}
```

---

### PHP

```php
<?php
/**
 * Iterator Pattern — PHP Example
 * Real-world use case: A report generator that iterates over
 * database query results (simulated). Supports CSV export and
 * HTML table rendering by passing different iterators to the same
 * renderer functions.  PHP's SPL SplDoublyLinkedList is used as
 * the backing store for the ConcreteCollection to show integration
 * with a real PHP data structure.
 */

declare(strict_types=1);

// ---------------------------------------------------------------------------
// Domain model
// ---------------------------------------------------------------------------

final class SaleRecord
{
    public function __construct(
        public readonly int    $id,
        public readonly string $region,
        public readonly string $product,
        public readonly float  $revenue,
        public readonly string $date,   // YYYY-MM-DD
    ) {}

    public function toArray(): array
    {
        return [
            'id'      => $this->id,
            'region'  => $this->region,
            'product' => $this->product,
            'revenue' => $this->revenue,
            'date'    => $this->date,
        ];
    }

    public function __toString(): string
    {
        return sprintf(
            '#%d | %-10s | %-20s | $%8.2f | %s',
            $this->id,
            $this->region,
            $this->product,
            $this->revenue,
            $this->date,
        );
    }
}

// ---------------------------------------------------------------------------
// Iterator interface
// ---------------------------------------------------------------------------

interface SalesIterator
{
    public function hasNext(): bool;
    public function next(): SaleRecord;
    public function current(): SaleRecord;
    public function rewind(): void;
}

// ---------------------------------------------------------------------------
// Concrete iterators
// ---------------------------------------------------------------------------

/** Forward iterator over all sales records. */
class AllSalesIterator implements SalesIterator
{
    private int $position = 0;

    /** @param SaleRecord[] $records */
    public function __construct(private readonly array $records) {}

    public function hasNext(): bool      { return $this->position < count($this->records); }
    public function current(): SaleRecord{ return $this->records[$this->position]; }
    public function next(): SaleRecord
    {
        if (!$this->hasNext()) {
            throw new \OutOfRangeException('Iterator exhausted.');
        }
        return $this->records[$this->position++];
    }
    public function rewind(): void { $this->position = 0; }
}

/** Filters sales records by a given region. */
class RegionIterator implements SalesIterator
{
    /** @var SaleRecord[] */
    private array $filtered = [];
    private int   $position = 0;

    /** @param SaleRecord[] $records */
    public function __construct(array $records, string $region)
    {
        $this->filtered = array_values(
            array_filter($records, fn(SaleRecord $r) => strcasecmp($r->region, $region) === 0)
        );
    }

    public function hasNext(): bool       { return $this->position < count($this->filtered); }
    public function current(): SaleRecord { return $this->filtered[$this->position]; }
    public function next(): SaleRecord
    {
        if (!$this->hasNext()) {
            throw new \OutOfRangeException('Iterator exhausted.');
        }
        return $this->filtered[$this->position++];
    }
    public function rewind(): void { $this->position = 0; }
}

/** Sorts records by revenue descending (top N). */
class TopRevenueIterator implements SalesIterator
{
    /** @var SaleRecord[] */
    private array $sorted = [];
    private int   $position = 0;

    /** @param SaleRecord[] $records */
    public function __construct(array $records, int $limit)
    {
        $copy = $records;
        usort($copy, fn(SaleRecord $a, SaleRecord $b) => $b->revenue <=> $a->revenue);
        $this->sorted = array_slice($copy, 0, $limit);
    }

    public function hasNext(): bool       { return $this->position < count($this->sorted); }
    public function current(): SaleRecord { return $this->sorted[$this->position]; }
    public function next(): SaleRecord
    {
        if (!$this->hasNext()) {
            throw new \OutOfRangeException('Iterator exhausted.');
        }
        return $this->sorted[$this->position++];
    }
    public function rewind(): void { $this->position = 0; }
}

// ---------------------------------------------------------------------------
// Iterable collection
// ---------------------------------------------------------------------------

interface SalesCollection
{
    public function createAllIterator(): SalesIterator;
    public function createRegionIterator(string $region): SalesIterator;
    public function createTopRevenueIterator(int $limit): SalesIterator;
}

class SalesReport implements SalesCollection
{
    /** @var SaleRecord[] */
    private array $records = [];

    public function add(SaleRecord $record): void
    {
        $this->records[] = $record;
    }

    public function createAllIterator(): SalesIterator
    {
        return new AllSalesIterator($this->records);
    }

    public function createRegionIterator(string $region): SalesIterator
    {
        return new RegionIterator($this->records, $region);
    }

    public function createTopRevenueIterator(int $limit): SalesIterator
    {
        return new TopRevenueIterator($this->records, $limit);
    }
}

// ---------------------------------------------------------------------------
// Client: report renderers
// ---------------------------------------------------------------------------

function renderTextTable(SalesIterator $it, string $title): void
{
    echo "\n=== $title ===\n";
    printf("%-4s  %-10s  %-20s  %10s  %-12s\n", 'ID', 'Region', 'Product', 'Revenue', 'Date');
    echo str_repeat('-', 64) . "\n";

    $totalRevenue = 0.0;
    $count        = 0;
    while ($it->hasNext()) {
        $r = $it->next();
        printf("%-4d  %-10s  %-20s  %10.2f  %-12s\n",
            $r->id, $r->region, $r->product, $r->revenue, $r->date);
        $totalRevenue += $r->revenue;
        $count++;
    }
    printf("%-4s  %-10s  %-20s  %10.2f  (total, %d records)\n",
        '', '', '', $totalRevenue, $count);
}

function exportCsv(SalesIterator $it, string $filename): void
{
    $lines = ["id,region,product,revenue,date"];
    while ($it->hasNext()) {
        $r       = $it->next();
        $lines[] = implode(',', [
            $r->id,
            "\"{$r->region}\"",
            "\"{$r->product}\"",
            number_format($r->revenue, 2, '.', ''),
            $r->date,
        ]);
    }
    file_put_contents($filename, implode("\n", $lines) . "\n");
    echo "\nCSV exported to: $filename\n";
}

// ---------------------------------------------------------------------------
// Populate and run
// ---------------------------------------------------------------------------

$report = new SalesReport();
$report->add(new SaleRecord(1,  'North', 'Widget Pro',        12_500.00, '2025-01-15'));
$report->add(new SaleRecord(2,  'South', 'Gadget X',           8_200.00, '2025-01-20'));
$report->add(new SaleRecord(3,  'East',  'Widget Pro',         9_800.00, '2025-02-05'));
$report->add(new SaleRecord(4,  'North', 'SuperTool',          5_400.00, '2025-02-14'));
$report->add(new SaleRecord(5,  'West',  'Gadget X',          14_000.00, '2025-03-01'));
$report->add(new SaleRecord(6,  'South', 'SuperTool',          3_100.00, '2025-03-18'));
$report->add(new SaleRecord(7,  'East',  'Widget Pro',        11_250.00, '2025-04-10'));
$report->add(new SaleRecord(8,  'West',  'MegaUnit',          22_000.00, '2025-04-22'));
$report->add(new SaleRecord(9,  'North', 'Gadget X',           7_600.00, '2025-05-03'));
$report->add(new SaleRecord(10, 'East',  'MegaUnit',          18_500.00, '2025-05-28'));

renderTextTable($report->createAllIterator(),          'All Sales');
renderTextTable($report->createRegionIterator('North'), 'North Region');
renderTextTable($report->createTopRevenueIterator(3),   'Top 3 by Revenue');
exportCsv($report->createAllIterator(), sys_get_temp_dir() . '/sales_export.csv');
```

---

### Ruby

```ruby
# Iterator Pattern — Ruby Example
# Real-world use case: A task queue processor that supports FIFO,
# LIFO (undo stack), and priority-based iteration over work items.
# The worker (client) processes tasks using a common iterator interface
# regardless of the queue discipline.
#
# Note: Ruby has built-in Enumerable/Enumerator; this example
# implements the raw pattern from scratch, then adds Enumerable
# integration for idiomatic Ruby (each/select/map/etc.).

# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

Task = Struct.new(:id, :title, :priority, :created_at, keyword_init: true) do
  PRIORITIES = { low: 1, medium: 2, high: 3, critical: 4 }.freeze

  def priority_value
    PRIORITIES.fetch(priority, 0)
  end

  def to_s
    "[#{id.to_s.rjust(3, '0')}] #{priority.upcase.ljust(8)} | #{title}"
  end
end

# ---------------------------------------------------------------------------
# Iterator interface (module as abstract base)
# ---------------------------------------------------------------------------

module TaskIterator
  def has_next?
    raise NotImplementedError, "#{self.class}#has_next? not implemented"
  end

  def next_task
    raise NotImplementedError, "#{self.class}#next_task not implemented"
  end

  def rewind
    raise NotImplementedError, "#{self.class}#rewind not implemented"
  end

  # Integration with Ruby's Enumerable via Enumerator::Yielder
  def to_enumerator
    Enumerator.new do |yielder|
      rewind
      yielder << next_task while has_next?
    end
  end
end

# ---------------------------------------------------------------------------
# Concrete iterators
# ---------------------------------------------------------------------------

# FIFO — processes tasks in arrival order
class FifoIterator
  include TaskIterator

  def initialize(tasks)
    @tasks = tasks.dup
    @index = 0
  end

  def has_next? = @index < @tasks.length

  def next_task
    raise StopIteration, "No more tasks." unless has_next?
    task = @tasks[@index]
    @index += 1
    task
  end

  def rewind = (@index = 0)
end

# LIFO — processes tasks in reverse arrival order (undo-stack semantics)
class LifoIterator
  include TaskIterator

  def initialize(tasks)
    @tasks = tasks.dup
    @index = @tasks.length - 1
  end

  def has_next? = @index >= 0

  def next_task
    raise StopIteration, "No more tasks." unless has_next?
    task = @tasks[@index]
    @index -= 1
    task
  end

  def rewind = (@index = @tasks.length - 1)
end

# Priority — processes highest-priority tasks first, ties broken by arrival
class PriorityIterator
  include TaskIterator

  def initialize(tasks)
    @sorted = tasks.sort_by { |t| [-t.priority_value, t.created_at] }
    @index  = 0
  end

  def has_next? = @index < @sorted.length

  def next_task
    raise StopIteration, "No more tasks." unless has_next?
    task = @sorted[@index]
    @index += 1
    task
  end

  def rewind = (@index = 0)
end

# ---------------------------------------------------------------------------
# Iterable collection
# ---------------------------------------------------------------------------

class TaskQueue
  def initialize
    @tasks = []
  end

  def enqueue(task)
    @tasks << task
    self
  end

  def size = @tasks.size

  def create_fifo_iterator     = FifoIterator.new(@tasks)
  def create_lifo_iterator     = LifoIterator.new(@tasks)
  def create_priority_iterator = PriorityIterator.new(@tasks)
end

# ---------------------------------------------------------------------------
# Client: Worker
# ---------------------------------------------------------------------------

class Worker
  def process(iterator, label)
    puts "\n=== #{label} ==="
    count = 0
    while iterator.has_next?
      task = iterator.next_task
      puts "  Processing: #{task}"
      count += 1
    end
    puts "  --> #{count} task(s) processed."
  end

  # Accepts any TaskIterator and returns tasks matching a block condition
  # (uses to_enumerator for idiomatic Ruby)
  def select_tasks(iterator, &block)
    iterator.to_enumerator.select(&block)
  end
end

# ---------------------------------------------------------------------------
# Populate and run
# ---------------------------------------------------------------------------

queue = TaskQueue.new
now   = Time.now

queue
  .enqueue(Task.new(id: 1, title: "Send weekly newsletter",    priority: :low,      created_at: now - 300))
  .enqueue(Task.new(id: 2, title: "Fix login bug",             priority: :critical, created_at: now - 240))
  .enqueue(Task.new(id: 3, title: "Update dependencies",       priority: :medium,   created_at: now - 180))
  .enqueue(Task.new(id: 4, title: "Deploy hotfix to prod",     priority: :critical, created_at: now - 120))
  .enqueue(Task.new(id: 5, title: "Write unit tests",          priority: :medium,   created_at: now - 60))
  .enqueue(Task.new(id: 6, title: "Review pull requests",      priority: :high,     created_at: now))

worker = Worker.new

worker.process(queue.create_fifo_iterator,     "FIFO Queue")
worker.process(queue.create_lifo_iterator,     "LIFO Stack")
worker.process(queue.create_priority_iterator, "Priority Queue")

# Idiomatic Ruby: use Enumerable via to_enumerator
critical_tasks = worker.select_tasks(queue.create_priority_iterator) do |task|
  task.priority == :critical
end

puts "\n=== Critical Tasks Only ==="
critical_tasks.each { |t| puts "  #{t}" }

puts "\n=== Tasks via map (titles) ==="
titles = queue.create_fifo_iterator.to_enumerator.map(&:title)
titles.each { |t| puts "  - #{t}" }
```

---

## When To Use

Use the Iterator pattern when:

- **The collection has a complex internal structure** and you want to hide that complexity from clients. The iterator encapsulates the details of working with a linked list, tree, graph, or hash map, giving clients a simple traversal interface.

- **You want to reduce duplication of traversal code.** Moving non-trivial iteration algorithms into separate iterator classes means the traversal logic lives in exactly one place and can be reused across the codebase.

- **You need your code to traverse different data structures**, or the concrete types of these structures are not known until runtime. If all iterators and collections implement common interfaces, the client code works with any combination.

- **You want multiple simultaneous traversals over the same collection.** Each iterator object keeps its own state (position, visited flags, etc.), so having two iterators active over the same collection is safe and straightforward.

- **You want lazy evaluation.** An iterator can compute elements on demand (e.g., streaming from a file or a remote API), rather than materializing the entire collection upfront.

- **You need pluggable traversal strategies.** Swapping in a different iterator type (forward, reverse, filtered, shuffled) changes the traversal algorithm without changing the collection or the client.

Do NOT use the Iterator pattern when:

- Your application only works with simple, linear collections (arrays, slices) where language-built-in loops (`for`, `foreach`) are sufficient.
- Direct index access is required for performance and the overhead of an object-per-element call is unacceptable.

---

## Pros & Cons

### Pros

| Benefit | Explanation |
|---|---|
| **Single Responsibility Principle** | Traversal logic is extracted into its own class, keeping collection classes focused on efficient data storage. |
| **Open/Closed Principle** | New traversal strategies (e.g., reverse, filtered, lazy) can be added without modifying the collection or client code. |
| **Parallel iteration** | Multiple independent iterators can traverse the same collection simultaneously, each maintaining its own state. |
| **Delayed / lazy iteration** | Iterators can fetch or compute elements on demand, enabling streaming over large or remote data sources without loading everything into memory first. |
| **Unified traversal interface** | Client code works identically with lists, trees, graphs, or remote result sets — it only sees `hasNext()` and `next()`. |

### Cons

| Drawback | Explanation |
|---|---|
| **Overkill for simple collections** | Creating iterator classes for a plain array accessed in a single place adds unnecessary complexity with no real benefit. |
| **Potential performance overhead** | Going through a dedicated iterator object may be slower than direct index access for cache-hot, specialized data structures. |
| **Extra classes to maintain** | Every new traversal strategy requires a new ConcreteIterator class, growing the class count of your project. |
| **Invalidation hazards** | Modifying a collection while an iterator is active leads to undefined behavior in most implementations; the pattern does not inherently address concurrent modification. |

---

## Relations to Other Patterns

| Pattern | Relationship |
|---|---|
| **Composite** | Iterators are commonly used to traverse recursive Composite trees. A single, uniform iterator interface hides whether the current node is a leaf or a branch. |
| **Factory Method** | `createIterator()` on the collection is itself an application of the Factory Method pattern — the collection decides which ConcreteIterator subclass to instantiate. |
| **Memento** | Can be used together with Iterator to capture an iterator's state (current position) so that traversal can be rolled back. The Memento stores the iterator's snapshot without exposing its internals. |
| **Visitor** | Both patterns work over a collection of elements, but with different focuses. Iterator is about *how* you traverse; Visitor is about *what operation* you perform on each element. They are often combined: iterate with Iterator, perform operations with Visitor. |

---

## Sources

- https://refactoring.guru/design-patterns/iterator
- https://sourcemaking.com/design_patterns/iterator
