# Design It Twice

When designing a new module or refactoring a shallow one, explore alternative interfaces before implementing. Based on John Ousterhout's *A Philosophy of Software Design*: **your first idea is unlikely to be the best.**

Uses the core vocabulary: **module**, **interface**, **seam**, **adapter**, **leverage**, and **locality**.

---

## The Process

### 1. Frame the Problem Space

Before sketching code, define:

- What problem does this module actually solve for its callers?
- What are the hard constraints (e.g. Qt thread safety, native OS window messages, event loop timing)?
- What dependencies does it require (in-process, Qt subsystem, or external)?
- A minimal illustrative snippet showing what callers are forced to do today.

### 2. Formulate 2–3 Radically Different Interfaces

Do not make minor variations of the same method signature. Produce distinct design philosophies:

- **Alternative A — Minimal Surface (High Leverage):**
  1–3 entry points maximum. Makes the default use case trivial. Hides all setup and state synchronization behind the seam.

  ```python
  # Example: Single declarative point of contact
  bar = WindowTitleBar(window)
  ```

- **Alternative B — Composable / Signal-Driven (High Flexibility):**
  Separates UI presentation from window controller logic via Qt signals and explicit slots.

  ```python
  controller = WindowFrameController(window)
  bar = CustomTitleBar()
  bar.minimizeRequested.connect(controller.minimize)
  bar.maximizeRequested.connect(controller.toggleMaximize)
  ```

- **Alternative C — Configuration / Builder Pattern (Fine-grained Control):**
  If configuration varies wildly across operating systems (Windows DWM vs macOS Cocoa).

### 3. Evaluate and Compare

Compare the alternatives across three axes:

| Criterion | Evaluation Question |
| --- | --- |
| **Depth** | Which alternative delivers the most behavior per unit of interface the caller must learn? |
| **Locality** | If window behavior or OS API changes, which alternative confines edits to a single file? |
| **Seam Placement** | Where does the boundary sit? Is it easy to test with `pytest-qt` without mocking internal state? |

### 4. Decide and Recommend

Be opinionated. Choose the design that maximizes depth without creating artificial rigidity. If combining elements from two designs creates higher leverage, formulate that hybrid before implementing.
