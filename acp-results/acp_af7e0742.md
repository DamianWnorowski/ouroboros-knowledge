Here are three common race conditions encountered in multithreaded programming and how to prevent them:

# 1. Check-Then-Act (Time-of-Check to Time-of-Use)
**The Problem:** 
This occurs when a thread checks a condition (like a variable's value or the existence of a file) and then takes an action based on that condition. However, between the check and the action, another thread modifies the condition, making the initial check invalid.
*   **Example:** Lazy initialization (Singleton pattern). Thread A checks `if (instance == null)`. It is true. Thread B also checks `if (instance == null)`. It is also true. Both threads then execute `instance = new Object()`, creating two distinct objects instead of one.

**How to Prevent It:**
*   **Locking/Mutexes:** Wrap both the "check" and the "act" phases in a single synchronized block or lock to ensure the operation is atomic.
*   **Concurrent Data Structures:** Use built-in atomic operations provided by thread-safe collections (e.g., `ConcurrentHashMap.putIfAbsent()` in Java or `ConcurrentDictionary.GetOrAdd()` in C).

# 2. Read-Modify-Write
**The Problem:**
This happens when multiple threads read a shared variable, perform a calculation on it, and write it back. If the operations overlap, one thread's write can overwrite and erase another thread's update.
*   **Example:** Incrementing a counter (`counter++`). This is actually three operations: Read the current value, add 1 to it, write the new value. If Thread A and Thread B both read the value `5` simultaneously, they will both calculate `6` and write `6`. The counter only incremented by 1 despite two operations occurring.

**How to Prevent It:**
*   **Atomic Variables:** Use language-provided atomic types (e.g., `std::atomic<int>` in C++, `AtomicInteger` in Java, or `sync/atomic` in Go) which perform the read-modify-write cycle as a single, uninterruptible hardware-level instruction.
*   **Synchronization:** If atomic variables aren't sufficient (e.g., you need to update multiple variables together), protect the entire block with a mutex or lock.

# 3. Initialization / Teardown Race
**The Problem:**
This occurs when one thread is creating or destroying a shared resource while another thread is simultaneously trying to access it. 
*   **Example:** Thread A decides to close a shared database connection or free a block of memory because it thinks the application is shutting down. At the exact same time, Thread B attempts to execute a query on that connection or read that memory, resulting in a crash or a `NullReferenceException`/`Segfault`.

**How to Prevent It:**
*   **Reference Counting:** Use smart pointers (like `std::shared_ptr` in C++ or `Arc` in Rust) to ensure a resource is only destroyed when exactly zero threads are holding a reference to it.
*   **State Machines & Barriers:** Maintain an explicit state (e.g., `STARTING`, `RUNNING`, `STOPPING`) protected by a lock. Threads must check this state before using the resource. For initialization, use constructs like `std::call_once` (C++) or `sync.Once` (Go) to guarantee a setup function runs exactly once before any other thread proceeds.