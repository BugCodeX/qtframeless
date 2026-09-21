# Condition-Based Waiting

Never guess at timing. Wait for the actual condition you care about.

## Rule

- `time.sleep()` -- **forbidden** in tests. It guesses. It creates flaky tests.
- `qtbot.wait(ms)` -- acceptable only when the fixed duration IS the point (e.g. animation frame budget).
- `qtbot.waitUntil(lambda: condition, timeout=ms)` -- **required** whenever you are waiting for a state change.

## Pattern

```python
# BEFORE: guessing at timing -- flaky, environment-dependent
qtbot.wait(100)
assert widget.isVisible()

# AFTER: waiting for the actual condition
qtbot.waitUntil(lambda: widget.isVisible(), timeout=1000)
assert widget.isVisible()
```

## Signal-based variant

When a signal drives the state change, use `waitSignal` instead:

```python
# Wait for the signal that proves the work is done
with qtbot.waitSignal(widget.color_changed, timeout=1000):
    widget.set_color(QColor("red"))

assert widget.color() == QColor("red")
```

## Timeout guidance

| Scenario | Suggested timeout |
| --- | --- |
| Synchronous property update | 500 ms |
| Async worker / thread result | 2000-5000 ms |
| File I/O or network mock | 3000 ms |
| Animation / repaint cycle | 500 ms |

## Why this matters

A `qtbot.wait(100)` that passes locally will fail on a slow CI runner. A `qtbot.waitUntil(...)` fails only when the condition is genuinely never met -- a real bug, not a timing accident.
