---
name: qt-testing
description: "Trigger: test qt, pytest-qt, qtbot, test widget, gui test, testing pyside, qapp, waitSignal. Write reliable UI tests for QtMaterial3 with pytest-qt."
license: MIT
metadata:
  author: "BugCodeX"
  version: "1.0"
---

# Skill: qt-testing

## Activation Contract

Use when authoring, modifying, or debugging UI unit tests, widget interaction tests, signals, or dialog flows across `packages/*/tests/`.

## Hard Rules

- **Always use the `qtbot` or `qapp` fixture**: Never instantiate Qt widgets in a test without `qapp` or `qtbot` in the test signature; otherwise, headless environments hang or segfault.
- **Register top-level test widgets**: Use `qtbot.addWidget(widget)` on standalone widgets so Qt cleans them up upon test teardown.
- **NEVER use `time.sleep()`**: Use `qtbot.wait(ms)` or `qtbot.waitUntil(lambda: condition, timeout=...)` to allow the Qt event loop to process events.
- **Signal assertion with context manager**: Use `with qtbot.waitSignal(widget.mySignal, timeout=1000):` when testing asynchronous or event-triggered signals.
- **Simulate user input with qtbot**: Use `qtbot.mouseClick(button, Qt.MouseButton.LeftButton)` or `qtbot.keyClicks(lineEdit, "text")` rather than calling private event handlers directly.
- **Modal dialog testing**: Never invoke `.exec()` on modal dialogs directly during tests. Mock `.exec` with monkeypatch (`monkeypatch.setattr(dialog, "exec", lambda: QDialog.DialogCode.Accepted)`) or use `qtbot.waitExposed()`.

## Decision Gates

| Scenario | Pattern to Apply |
| --- | --- |
| Testing button click / action | `qtbot.mouseClick(button, Qt.MouseButton.LeftButton)` |
| Testing text input / typing | `qtbot.keyClicks(inputWidget, "search text")` |
| Verifying signal emission | `with qtbot.waitSignal(widget.colorChanged, timeout=1000): widget.setColor(...)` |
| Testing async or deferred updates | `qtbot.waitUntil(lambda: widget.isUpdated() is True, timeout=1000)` |
| Testing dialog acceptance/rejection | Mock `exec` returning `QDialog.DialogCode.Accepted` |
| Testing widgets without user events | Pass `qapp` fixture to provide `QApplication` context |

## Execution Steps

1. Add `qtbot` (or `qapp` for non-interactive state tests) to the test function parameters.
2. Instantiate the component and call `qtbot.addWidget(widget)`.
3. If testing signals, open the `with qtbot.waitSignal(...)` block before triggering the action.
4. Simulate interaction using `qtbot.mouseClick`, `qtbot.keyClicks`, or property setters.
5. Assert widget state, visual properties (`pixmap`, `text`, `styleSheet`), or signal payloads.
6. Verify tests run cleanly via `uv run pytest packages/<package>/tests`.

## Output Contract

- Pure deterministic pytest test functions with 0 race conditions and no hanging processes.
- All tests pass when run in both interactive and headless/CI environments.
