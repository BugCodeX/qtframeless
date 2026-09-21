# Defense in Depth

Validate at EVERY layer data passes through. A single guard at the outer boundary is not enough.

## Four Layers

| Layer | What to validate | Where it lives |
| --- | --- | --- |
| **Layer 1 -- Entry point** | Reject invalid input at the API boundary | Public method or slot |
| **Layer 2 -- Business logic** | Confirm data makes sense for this operation | Domain / model code |
| **Layer 3 -- Environment guard** | Check context-specific preconditions | Widget or subsystem init |
| **Layer 4 -- Debug logging** | Surface unexpected state when other layers miss it | `logging.debug(...)` |

## Qt/Python Example

```python
def set_color(self, color: QColor) -> None:
    # Layer 1: entry point validation -- reject at the boundary
    if not color.isValid():
        raise ValueError(f"Invalid QColor passed to set_color: {color!r}")

    # Layer 2: business logic guard -- skip no-op updates to avoid spurious repaints
    if color == self._color:
        return

    # Layer 3: environment guard -- warn if widget is not yet fully constructed
    if not self.isVisible():
        logging.debug(
            "set_color called before widget is shown; color will apply on next show()"
        )

    self._color = color
    self.update()  # Schedule repaint only when the value actually changed
```

## Key Principle

Each layer catches what the layer above missed. When a bug slips through, ask which layer should have caught it -- then add the guard there, not at the symptom.
