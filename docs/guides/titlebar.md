# Title Bar & MenuBar

The custom title bar (`TitleBar`) in `qtframeless` replaces the native Windows non-client caption while preserving full OS integration (drag-to-move, double-click to maximize, Windows 11 Snap Layouts flyout, and DPI scaling).

---

## Anatomy of the TitleBar

The title bar is divided into three functional horizontal sections:

```text
+-----------------------------------------------------------------------------------+
| [Icon] [Title / MenuBar]            [Center Container]             [_] [[]] [X]   |
| <----- Left Section ----->     <----- Center Section ----->    <-- Corner Buttons |
+-----------------------------------------------------------------------------------+
```

1. **Left Section**: Displays the window icon (`_iconLabel`) and window title or an integrated `QMenuBar`.
2. **Center Section**: A flexible container (`_centerContainer`) for centered titles, search fields, or tab bars.
3. **Corner Section**: Vector-drawn control buttons (`MinimizeButton`, `MaximizeButton`, `CloseButton`, `FullScreenButton`).

---

## Embedding a QMenuBar

In standard Windows applications, menu bars typically sit below the title bar, consuming valuable vertical real estate. `qtframeless` allows you to embed a `QMenuBar` directly into the title bar alongside your control buttons.

### In FramelessMainWindow

When using `FramelessMainWindow`, calling `self.menuBar()` automatically returns the `QMenuBar` mounted in the `TitleBar`:

```python linenums="1"
import sys
from PySide6.QtWidgets import QApplication
from qtframeless import FramelessMainWindow


class Window(FramelessMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MenuBar Example")
        self.resize(800, 500)

        # Access the integrated title bar menu bar
        bar = self.menuBar()

        # Add menus
        fileMenu = bar.addMenu("File(&F)")
        fileMenu.addAction("New Project(&N)")
        fileMenu.addAction("Open...(&O)")
        fileMenu.addSeparator()
        fileMenu.addAction("Quit(&Q)", self.close)

        editMenu = bar.addMenu("Edit(&E)")
        editMenu.addAction("Undo(&U)")
        editMenu.addAction("Redo(&R)")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
```

### In FramelessWindow or Custom Widgets

If you are using `FramelessWindow`, you can attach a `QMenuBar` explicitly through `TitleBar.setMenuBar()`:

```python
from PySide6.QtWidgets import QMenuBar
from qtframeless import FramelessWindow

window = FramelessWindow()
titleBar = window.getTitleBar()

menuBar = QMenuBar()
fileMenu = menuBar.addMenu("File")
fileMenu.addAction("Exit", window.close)

titleBar.setMenuBar(menuBar)
```

### Fluent Menu Styling

By default, `TitleBar` applies Windows 11 Fluent Design styling to embedded menu bars (`autoStyleMenuBar=True`). This styles:

- Menu bar items with rounded hover highlights and proper padding.
- Dropdown menus with rounded corners, subtle shadows, and borders.
- Dark and light theme colors automatically synced with system theme changes.

To customize or disable automatic styling:

```python
titleBar = window.getTitleBar()

# Disable automatic styling if you provide your own QSS
titleBar.setAutoStyleMenuBar(False)

# Or manually invoke styling with specific DPI and dark mode settings
titleBar.applyFluentMenuStyle(menuBar, isDark=True, dpi=120)
```

---

## Centered Window Titles

To align the title in the center of the title bar (a common modern design pattern in macOS and Windows 11 apps), use `setTitleAlignment`:

```python
from PySide6.QtCore import Qt

titleBar = window.getTitleBar()
titleBar.setTitleAlignment(Qt.AlignmentFlag.AlignCenter)
```

To restore left-aligned titles:

```python
titleBar.setTitleAlignment(Qt.AlignmentFlag.AlignLeft)
```

---

## Vector Control Buttons

The window control buttons (`MinimizeButton`, `MaximizeButton`, `CloseButton`, `FullScreenButton`) are subclasses of `VectorButton`. Instead of raster images or SVGs, they draw their icons using `QPainter`.

### Why Vector Buttons?

- **Crisp Rendering**: Geometric vector lines stay sharp at any fractional or high-DPI scaling factor (125%, 150%, 175%, 200%).
- **Theme Reactivity**: Colors adapt immediately when switching between dark and light modes without reloading image files.
- **Native Non-Client Hit-Testing**: `MaximizeButton` cooperates with `WindowFrameController` to trigger Windows 11 Snap Layouts when hovered.

### Button Classes

| Button Class | Default Action | Special Behavior |
| --- | --- | --- |
| `MinimizeButton` | Minimizes the parent window. | Standard hover highlight. |
| `MaximizeButton` | Toggles maximize / restore. | Intercepts `HTMAXBUTTON` to trigger Windows 11 Snap Layouts. |
| `CloseButton` | Closes the parent window. | Turns red on hover (`#E81123`) matching native Windows style. |
| `FullScreenButton` | Toggles fullscreen state. | Checkable button state with enter/exit fullscreen icon toggle. |

### Accessing Control Buttons

You can access and inspect individual buttons through the title bar:

```python
titleBar = window.getTitleBar()

# Get dictionary of active buttons
buttons = titleBar.getButtons()
minButton = buttons.get("min")
closeButton = buttons.get("close")

# Get maximize button directly
maxButton = titleBar.getMaximizeButton()
```

---

## Customizing Icons and Titles

### Window Icon

Set the window icon using `QIcon`. The title bar will render the icon with per-monitor DPI scaling:

```python
from PySide6.QtGui import QIcon

window.setWindowIcon(QIcon("assets/app_icon.png"))

# Or configure size explicitly on the title bar
window.getTitleBar().setIconSize(24, 24)
```

### Window Title and Font

```python
from PySide6.QtGui import QFont

window.setWindowTitle("Custom Application Title")

# Customize font styling on the title bar label
titleFont = QFont("Segoe UI Variable Display", 10)
titleFont.setBold(True)
window.getTitleBar().setTitleBarFont(titleFont)
```

---

## Dynamic Button Hints

You can customize which control buttons are displayed at creation time or change them dynamically at runtime:

```python
# Initial configuration
window = FramelessMainWindow(hint=["min", "close"])

# Update buttons dynamically
titleBar = window.getTitleBar()
titleBar.setTitleBarHint(["min", "max", "close"])
```

---

## Custom Center Widgets

You can place arbitrary Qt widgets (e.g. search boxes, breadcrumb navigation, segment controls) inside the center container of the title bar:

```python
from PySide6.QtWidgets import QLineEdit

searchField = QLineEdit()
searchField.setPlaceholderText("Search documents or actions...")
searchField.setFixedWidth(280)

window.getTitleBar().setCenterWidget(searchField)

# Remove the center widget when no longer needed
window.getTitleBar().removeCenterWidget()
```
