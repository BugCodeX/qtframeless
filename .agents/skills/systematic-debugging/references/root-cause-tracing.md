# Root Cause Tracing

Trace backward through the call chain until you find the origin of the bad value. Fix there.

## Technique

```text
Observe symptom
  -> Find immediate cause (what produced the wrong value?)
    -> Ask: what called this?
      -> Keep tracing up
        -> Find the original trigger
          -> Fix at source
```

When you cannot trace manually: add `print()` or `logging.debug()` instrumentation at each boundary, run once, read the output, then fix.

## Qt/Python Example

```python
# Symptom: paintEvent renders wrong color deep in the call stack

# Immediate cause -- _color is wrong here:
def paintEvent(self, event: QPaintEvent) -> None:
    painter = QPainter(self)
    painter.setBrush(QBrush(self._color))  # self._color is QColor(0, 0, 0) -- wrong!

# What sets _color?
def set_color(self, color: QColor) -> None:
    self._color = color  # Called correctly -- but with what value?

# Trace up: who calls set_color?
# WindowTitleBar.__init__ -> self.set_color(theme.accent_color())
# theme.accent_color() returns QColor() default -- never initialized!

# Root cause: ThemeManager was not injected before widget construction.
# Fix: ensure ThemeManager is initialized and passed to the widget constructor,
#      not created lazily after the widget already exists.
class WindowTitleBar(QWidget):
    def __init__(self, theme: ThemeManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # ThemeManager must be ready before set_color is called.
        self.set_color(theme.accent_color())
```

## Key Rule

Never add a workaround at `paintEvent` (the symptom). Fix the injection order (the source).
