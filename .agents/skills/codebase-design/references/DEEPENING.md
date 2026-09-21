# Deepening

How to consolidate and deepen a cluster of shallow modules safely.

---

## Dependency Categories

When assessing a module candidate for deepening, classify its dependencies to determine how it crosses seams and tests:

### 1. In-Process (Pure Computation / Internal State)

- Python data structures, coordinate math, geometry calculations, color palette transformations.
- **Deepening strategy:** Merge shallow helper classes into a single deep module. Test through the module's public interface directly with standard assertions. No adapters or mocks needed.

### 2. Local-Substitutable (Qt Subsystems & Widgets)

- `QWidget`, `QPainter`, event filters, or theme providers.
- **Deepening strategy:** Run directly against headless or virtual Qt instances via `qtbot` and `qapp`. The seam is internal; avoid exposing mock hooks at the public interface purely for tests.

### 3. Remote or OS-Bound (Platform / Native API)

- Windows Win32 API (`user32.dll`, `dwmapi.dll`), native hit-testing (`WM_NCHITTEST`), window message hooks.
- **Deepening strategy:** Define a clean interface at the seam. The deep module owns the high-level logic (e.g. framing, maximize tracking, snapping), while platform calls sit behind a native adapter:
  - `WindowsNativeWindowAdapter` (calls Windows DWM)
  - `LinuxNativeWindowAdapter` (calls X11/Wayland protocols)
  - `HeadlessNativeWindowAdapter` (for fast deterministic CI tests)

---

## Seam Discipline

- **One adapter means a hypothetical seam. Two adapters means a real one.**
  Do not introduce abstract base classes or interfaces unless at least two implementations exist or are planned (e.g. production platform vs test fake). A single-adapter seam is just indirection that adds noise.
- **Internal seams vs. external seams:**
  A deep module can have private internal helper classes. Never expose internal seams through the public interface just to satisfy unit tests. The public interface is the only contract that matters.

---

## Testing Strategy: Replace, Don't Layer

1. **Delete shallow unit tests:**
   When consolidating shallow classes into a deep module, delete the hyper-specific tests that tested the old internal plumbing.
2. **The interface is the test surface:**
   Write new tests against the deep module's public interface using `pytest-qt`. Tests assert on observable outcomes (widget properties, emitted signals, final geometry), never internal variables.
3. **Tests survive refactors:**
   If internal implementation changes but external behavior remains constant, tests must continue to pass without modification. If a test breaks when an internal variable is renamed, it was testing past the interface.
