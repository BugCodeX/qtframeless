---
name: codebase-design
description: "Trigger: codebase design, deep module, shallow module, interface design, design it twice, refactor architecture, seam, sdd-design. Design deep modules with high leverage and clean seams."
license: MIT
metadata:
  author: BugCodeX
  version: "1.0"
---

# Skill: codebase-design

## Activation Contract

Activate when:

- Designing new modules, widgets, classes, or public interfaces (especially during `sdd-design` or architectural proposals).
- Refactoring existing code with excessive boilerplate, shallow pass-through classes, or leaky abstractions.
- Deciding where a seam or abstraction boundary belongs.
- Reviewing code for testability, cognitive load, or unnecessary indirection.

---

## Core Philosophy: Deep vs Shallow Modules

Derived from John Ousterhout (*A Philosophy of Software Design*):

- **Deep Module (Target):**
  A lot of functionality hidden behind a small, simple interface.
  - Callers gain high **Leverage** (maximum capability per concept learned).
  - Maintainers gain high **Locality** (modifications and fixes stay contained in one place).
- **Shallow Module (Anti-pattern):**
  A large interface with minimal logic (e.g. pure pass-through wrappers or getters/setters that expose internal mechanics).
  - High cognitive load for callers with zero encapsulation benefit.

```text
      DEEP MODULE (Good)                   SHALLOW MODULE (Avoid)
┌──────────────────────────────┐       ┌────────────────────────────────────┐
│ Small Interface (1-3 methods)│       │ Wide Interface (Many methods/props)│
├──────────────────────────────┤       ├────────────────────────────────────┤
│                              │       │ Thin Implementation (Pass-through) │
│ Substantial logic, state     │       └────────────────────────────────────┘
│ synchronization, and details │
│ hidden behind the seam       │
└──────────────────────────────┘
```

---

## The Core Vocabulary

Use these exact terms to keep architectural discussions unambiguous:

- **Module:** Any unit with an interface and an implementation (function, class, widget, or package). Avoid vague terms like *component* or *service*.
- **Interface:** Everything a caller must understand to use the module correctly (method signatures, type annotations, invariants, ordering constraints, error modes).
- **Implementation:** The internal code and private state hidden behind the interface.
- **Depth:** Leverage at the interface. The ratio of behavior provided to the complexity of the interface the caller must learn.
- **Seam (Michael Feathers):** The exact location where behavior can be altered or observed without modifying code at that site.
- **Adapter:** A concrete implementation that satisfies an interface at a seam (e.g. `WindowsNativeWindowAdapter`).
- **Leverage:** What callers gain: more work done per line of interface code.
- **Locality:** What maintainers gain: bugs, changes, and assertions concentrate in one spot instead of bleeding across N callers.

---

## Hard Rules

1. **The Deletion Test:**
   Mentally delete the module. If complexity disappears, it was a pass-through (shallow). If complexity scatters across N callers, it was earning its keep (deep).
2. **One Adapter is a Guess; Two Adapters is a Seam:**
   Never introduce an abstract interface or port unless at least two distinct implementations exist or are immediately planned (e.g. real platform vs test fake). A single-adapter seam is needless indirection.
3. **The Interface is the Test Surface:**
   Callers and tests cross the exact same seam. Test behavior through public methods and observable signals. If tests require poking private attributes (`_variable`), the module boundary is shaped incorrectly.
4. **Design It Twice:**
   For any non-trivial module, formulate at least two radically different interfaces before committing to implementation. Never default to the first idea (see `references/DESIGN-IT-TWICE.md`).
5. **Accept Dependencies, Don't Instantiate Them:**
   Pass collaborating objects (theme providers, window controllers) into the constructor or initializer rather than having the module instantiate singletons or hardcoded dependencies internally.

---

## Decision Gates

| Scenario | Action |
| --- | --- |
| Creating a new class or public widget | Run **Design It Twice** (`references/DESIGN-IT-TWICE.md`); produce two distinct interface options |
| Class contains mostly pass-through methods | Merge it into the caller or into the module it wraps (apply `references/DEEPENING.md`) |
| Multi-platform OS code (Win32 vs Linux/macOS) | Place a seam between window controller logic and native platform adapters |
| Test requires mocking 5+ internal objects | Redesign module into a deeper unit that accepts inputs and returns values / emits signals |
| Adding an interface with only one implementation | Remove the interface / ABC; use the concrete class directly until a second adapter is needed |

---

## Execution Steps

1. **Identify the Seam:** Determine where the boundary between caller and implementation belongs.
2. **Draft Alternative Interfaces (Design It Twice):**
   - Option A: Minimal surface area (highest leverage).
   - Option B: Composable / signal-driven (highest flexibility).
   - Compare on depth, locality, and testing ergonomics.
3. **Hide the Plumbing:** Move configuration, state synchronization, Qt event filters, and validation inside the implementation.
4. **Validate Testability:** Ensure tests can exercise full functionality via public methods or `qtbot.waitSignal` without white-box inspection.
5. **Verify with Deletion Test:** Ensure the caller is dramatically simpler than it was before the module was introduced.

---

## Output Contract

When submitting a design under this skill, provide:

1. **Interface Definition:** Concise Python class/function signatures with type hints and docstrings.
2. **Two Alternatives Evaluated:** Brief summary of the rejected alternative and why the chosen one provides higher depth/locality.
3. **Usage Example:** Realistic caller code demonstrating how simple it is to use.
4. **Hidden Complexity Summary:** Explicit list of edge cases, OS calls, or invariants handled internally.

---

## References

- `references/DESIGN-IT-TWICE.md` — Detailed process for designing alternative interfaces in parallel.
- `references/DEEPENING.md` — Techniques for classifying dependencies and consolidating shallow modules safely.
