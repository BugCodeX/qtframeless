---
name: systematic-debugging
description: "Trigger: bug, test failure, unexpected behavior, debugging, pytest failure, Qt crash, signal not emitted. Investigate root cause before fixing."
license: MIT
metadata:
  author: BugCodeX
  version: "2.0"
---

# Systematic Debugging

## Overview

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```text
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you have not completed Phase 1, you cannot propose fixes. No exceptions.

## When to Use

Use for ANY technical issue:

- Pytest or unit test failures
- Bugs in production or runtime crashes (e.g. Qt segmentation faults, event loop deadlocks)
- Unexpected behavior or signals not emitted
- Performance regressions or memory leaks
- Build failures, typing errors, or packaging issues
- Integration issues between components

**Use this ESPECIALLY when:**

- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You have already tried multiple fixes
- Previous fix did not work
- You do not fully understand the issue

**Don't skip when:**

- Issue seems simple (simple bugs have root causes too)
- You are in a hurry (rushing guarantees rework)
- The user wants it fixed NOW (systematic is faster than thrashing)

---

## The Four Phases

You MUST complete each phase in sequence before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages and Stack Traces Carefully**
   - Do not skip past errors or warnings; they often pinpoint the exact failure.
   - Read Python tracebacks completely from bottom to top frame.
   - Note exact file paths, line numbers, variable types, and exception classes (`AttributeError`, `TypeError`, `RuntimeError`).

2. **Reproduce Consistently**
   - Can you trigger it reliably with a test or reproduction command?
   - What are the exact steps, inputs, and environment flags?
   - Does it happen every time?
   - If intermittent/flaky: gather more data, do not guess or add arbitrary sleeps.

3. **Check Recent Changes**
   - What changed that could cause this? Check `git diff` and recent commits (`git log -n 5`).
   - Look for modified dependencies in `pyproject.toml`, lockfile changes, or altered environment variables.

4. **Gather Evidence in Multi-Component Systems**
   - In Qt systems, widgets, layouts, signals/slots, and the event loop interact across boundaries.
   - **BEFORE proposing fixes, add diagnostic instrumentation:**

     ```text
     For EACH component boundary:
       - Log what data enters the component
       - Log what data exits the component
       - Verify environment / configuration propagation
       - Check state at each layer
     ```

   - **Qt / Python Boundary Logging Example:**

     ```python
     # Layer 1: Widget initialization & parentage
     print(f"=== [Boundary 1] Init widget: parent={self.parent()!r}, visible={self.isVisible()}")

     # Layer 2: Slot or property setter input
     print(f"=== [Boundary 2] setColor input: {color!r}, isValid={color.isValid()}")

     # Layer 3: Paint event or native dispatch
     print(f"=== [Boundary 3] paintEvent rect: {event.rect()}, color_state={self._color.name()}")
     ```

   - Run the code **once** to gather evidence showing WHERE it breaks, analyze the evidence, and isolate the failing component.

5. **Trace Data Flow Backward**
   - When an error is deep in the call stack, do not patch the symptom where it explodes.
   - Trace backward: Where does the invalid value originate? Who called this function with bad data?
   - Keep walking up the chain until the original trigger is identified (see `references/root-cause-tracing.md`).

---

### Phase 2: Pattern Analysis

**Find the working pattern before attempting fixes:**

1. **Find Working Examples**
   - Locate similar working implementations in the same codebase:

     ```bash
     git grep -n "setColor\|QColor" -- "*.py"
     ```

2. **Compare Against References**
   - If implementing a pattern or working with Qt APIs, read the reference implementation or official Qt docs COMPLETELY. Do not skim.
3. **Identify Differences**
   - Compare working vs. broken code. List every difference, however small.
   - Never assume "that detail cannot matter."
4. **Understand Dependencies & Lifecycles**
   - What does this component assume? (e.g. `QApplication` running, widget parented, theme initialized, signal connected).

---

### Phase 3: Hypothesis and Testing

**Apply the scientific method:**

1. **Form a Single Clear Hypothesis**
   - State explicitly: *"I think X is the root cause because Y."*
   - Write it down before modifying code.
   - Be specific, not vague.
2. **Test Minimally**
   - Make the SMALLEST possible modification to confirm or disprove the hypothesis.
   - Change **one variable at a time**.
   - Never fix multiple things at once.
3. **Verify Before Continuing**
   - Did the test confirm the hypothesis? If YES → proceed to Phase 4.
   - Did it fail? Form a NEW hypothesis based on new evidence. DO NOT pile more fixes on top.
4. **When You Do Not Understand**
   - State clearly: *"I do not understand X."*
   - Never pretend to know or guess blindly. Research or ask the user.

---

### Phase 4: Implementation & Verification

**Fix the root cause, not the symptom:**

1. **Create Failing Test Case First**
   - Write the simplest possible reproduction with `pytest` / `pytest-qt`.
   - Ensure the test fails for the exact reason identified in Phase 1.
   - NEVER write production code without a failing test first (Iron Law of TDD).
2. **Implement Single Focused Fix**
   - Address the root cause identified in Phase 1.
   - ONE change at a time. No opportunistic refactoring or "while I'm here" modifications.
3. **Verify Fix Completely**
   - Does the failing test pass now?
   - Run the full project test suite to verify no regressions:

     ```bash
     uv run pytest packages/<package>/tests
     ```

   - Verify output is pristine (zero unexpected warnings or errors).
4. **Count Fix Attempts (Circuit Breaker)**
   - If the fix fails: **STOP**.
   - Count how many fixes you have attempted for this issue:
     - **If < 3 attempts:** Return to Phase 1 and re-analyze with fresh evidence.
     - **If ≥ 3 attempts:** **STOP IMMEDIATELY.** Proceed to Step 5 below.

5. **If 3+ Fixes Failed: Question the Architecture**

   **Signs of an architectural problem rather than an isolated bug:**
   - Each fix reveals new coupling, shared state, or issues in another component.
   - Every fix requires massive ripple refactoring across unrelated files.
   - Each fix creates new bugs or test failures elsewhere.

   **STOP and question fundamentals:**
   - Is this design pattern fundamentally flawed for this use case?
   - Are we clinging to this implementation purely through inertia?
   - Should we refactor the subsystem design rather than patching symptoms?

   **MANDATORY:** Stop and discuss with your human partner before attempting Fix #4. This is an architectural boundary, not a simple bug.

---

## Red Flags — STOP and Return to Phase 1

If you catch yourself having any of these thoughts, STOP immediately:

- *"Quick fix for now, I'll investigate later."*
- *"Just try changing X and see if it works."*
- *"Add multiple changes and run the tests to see what sticks."*
- *"Skip the test, I'll manually verify it later."*
- *"It's probably X, let me fix that right away."*
- *"I don't fully understand why this happens, but this change might work."*
- *"The pattern requires X, but I'll adapt it without checking the docs."*
- *"One more fix attempt..."* (when you have already failed 2+ times).
- Proposing solutions before inspecting logs or tracing data flow.

**ALL of these mean: STOP. Return to Phase 1.**

---

## User Signals That You Are Guessing

Watch for user cues indicating you are thrashing:

- *"Is that not happening?"* → You assumed without verifying.
- *"Will that show us what's happening?"* → You should have added boundary instrumentation.
- *"Stop guessing"* → You are proposing fixes without evidence.
- *"Ultra-think this"* → Question fundamentals and architecture, not symptoms.
- *"We are stuck"* → Your mental model is wrong. Reset to Phase 1.

When you see any of these signals: **STOP. Re-read Phase 1.**

---

## Common Rationalizations

| Excuse / Rationalization | Reality |
| --- | --- |
| *"The issue is simple, I don't need the full process."* | Simple bugs have root causes too. Systematic diagnosis takes seconds for simple bugs. |
| *"This is urgent, no time for process."* | Systematic debugging is much FASTER than thrashing in guess-and-check loops. |
| *"Just try this first, then investigate."* | The first fix sets the pattern. Guessing pollutes the codebase and obscures the cause. |
| *"I'll write the test after verifying the fix works."* | Untested fixes regress. If you didn't watch the test fail, you don't know what it tests. |
| *"Multiple fixes at once save time."* | You cannot isolate what actually worked, and you introduce hidden secondary bugs. |
| *"Reference is too long, I'll adapt the pattern."* | Incomplete understanding guarantees bugs. Read the reference completely. |
| *"I see the problem, let me fix it."* | Seeing a symptom is NOT understanding the root cause. |
| *"Just one more quick fix attempt..."* | 3+ failed attempts = architectural problem. Question the design; do not try fix #4. |

---

## When Investigation Reveals "No Root Cause"

If thorough investigation proves the issue is truly environmental, platform-dependent, or an external runtime bug:

1. Complete the process and document every investigation step and finding.
2. Implement robust handling (e.g. graceful fallbacks, platform guards, clear error messages).
3. Add debug logging for future diagnostic visibility.
4. **Note:** 95% of "no root cause" claims are simply incomplete investigations. Verify twice before declaring an issue external.

---

## Decision Gates

| Scenario | Action |
| --- | --- |
| Python traceback or crash dump | Read every frame top-to-bottom; identify exact line and value |
| Flaky test in Qt / UI | Apply `references/condition-based-waiting.md` (`qtbot.waitUntil`) |
| Invalid value deep in call stack | Apply `references/root-cause-tracing.md` (backward tracing) |
| Multi-component failure | Instrument boundaries with prints; run once; analyze |
| 3 consecutive fixes failed | STOP immediately. Do NOT attempt fix #4. Question architecture with user |
| Confirmed root cause & fix ready | Apply `references/defense-in-depth.md` to prevent bypass |

---

## Output Contract

When reporting on a bug or test failure, you must provide:

1. **Root Cause Statement:** Exactly one clear sentence identifying the origin of the bug.
2. **Evidence:** Stack trace snippet, boundary log, or reproduction step proving the cause.
3. **Failing Test:** Test function or script demonstrating the failure before the fix.
4. **Targeted Fix:** Minimal code change at the source (never at the symptom).
5. **Verification:** Full suite test run output proving green status without regressions.

---

## References

- `references/root-cause-tracing.md` — Backward tracing technique for Python and Qt widgets.
- `references/condition-based-waiting.md` — Deterministic condition polling vs. arbitrary sleeps in tests.
- `references/defense-in-depth.md` — Multi-layer validation patterns across entry, business, and runtime layers.
