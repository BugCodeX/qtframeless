# Window Types

`qtframeless` provides four primary window classes tailored to different application structures:

| Class | Base Qt Class | Primary Use Case |
| --- | --- | --- |
| [`FramelessMainWindow`](#framelessmainwindow) | `QMainWindow` | Full desktop applications with menus, toolbars, status bars, and docks. |
| [`FramelessWindow`](#framelesswindow) | `QWidget` | Standalone top-level tool windows, utilities, or simple dashboards. |
| [`FramelessDialog`](#framelessdialog) | `QDialog` | Modal or modeless popups, settings dialogs, wizards, or alert windows. |
| [`FramelessWidget`](#framelesswidget) | `QWidget` | Generic container widget; alias and base implementation of `FramelessWindow`. |

All four classes inherit from [`FramelessWindowMixin`](../api/core.md), providing uniform Win32 message handling, DWM drop shadows, Snap Layouts, and theme synchronization.

---

## FramelessMainWindow

`FramelessMainWindow` is the standard choice for main desktop application windows. It wraps your window content and the custom `TitleBar` inside a `centralWidget` container so that standard Qt features (status bars, dock widgets, and toolbars) work as expected.

### Complete Example

```python linenums="1"
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout
from qtframeless import FramelessMainWindow, WindowCornerPreference


class MainWindow(FramelessMainWindow):
    """Primary application window with an integrated menu bar and central layout."""

    def __init__(self) -> None:
        # hint controls which control buttons appear on the title bar:
        # options: "min", "max", "close", "full_screen"
        super().__init__(hint=["min", "max", "close"])

        self.setWindowTitle("FramelessMainWindow Example")
        self.resize(900, 600)

        # 1. Configure Windows 11 rounded corners and border
        self.windowCornerPreference = WindowCornerPreference.ROUND
        self.borderColor = "#505050"

        # 2. Add an integrated QMenuBar
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu("File(&F)")
        fileMenu.addAction("New Project(&N)")
        fileMenu.addAction("Open...(&O)")
        fileMenu.addSeparator()
        fileMenu.addAction("Exit(&X)", self.close)

        # 3. Add widgets to the central layout
        central = self.centralWidget()
        if central is not None and central.layout() is not None:
            container = QVBoxLayout()
            label = QLabel("Content inside central widget layout")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            button = QPushButton("Click Me")

            container.addWidget(label)
            container.addWidget(button)
            central.layout().addLayout(container)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

### Adding Widgets to FramelessMainWindow

Because `FramelessMainWindow` manages a vertical layout holding the `TitleBar` at index 0, you add your content to `self.centralWidget().layout()`:

```python
centralWidget = self.centralWidget()
if centralWidget is not None and centralWidget.layout() is not None:
    centralWidget.layout().addWidget(myWidget)
```

---

## FramelessWindow

`FramelessWindow` is a direct subclass of `QWidget` equipped with native frameless mechanics and an integrated `TitleBar`. Use it for secondary windows, floating panels, utility tools, or applications that do not require `QMainWindow` docking or status bars.

### Complete Example

```python linenums="1"
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout
from qtframeless import FramelessWindow, WindowCornerPreference


class UtilityWindow(FramelessWindow):
    """Secondary utility window."""

    def __init__(self) -> None:
        # Exclude max button for fixed-size utility windows
        super().__init__(hint=["min", "close"])

        self.setWindowTitle("Utility Tool")
        self.resize(400, 300)
        self.windowCornerPreference = WindowCornerPreference.ROUND_SMALL

        # Center the window title
        self.getTitleBar().setTitleAlignment(Qt.AlignmentFlag.AlignCenter)

        # The layout already contains the TitleBar at index 0
        layout = self.layout()
        if layout is not None:
            contentLayout = QVBoxLayout()
            contentLayout.setContentsMargins(16, 16, 16, 16)
            contentLayout.addWidget(QLabel("Settings and options go here."))
            contentLayout.addWidget(QPushButton("Save Changes"))
            layout.addLayout(contentLayout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UtilityWindow()
    window.show()
    sys.exit(app.exec())
```

---

## FramelessDialog

`FramelessDialog` subclasses `QDialog`, making it ideal for modal confirmations, configuration sheets, and wizards. It preserves native dialog lifecycles (`exec()`, `accept()`, and `reject()`).

### Complete Example

```python linenums="1"
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)
from qtframeless import FramelessDialog, WindowCornerPreference


class ConfirmationDialog(FramelessDialog):
    """Modal confirmation dialog."""

    def __init__(self, parent=None) -> None:
        # Dialogs typically only show a close button
        super().__init__(parent=parent, hint=["close"])

        self.setWindowTitle("Confirm Action")
        self.resize(360, 180)
        self.setResizable(False)  # Fixed size dialog
        self.windowCornerPreference = WindowCornerPreference.ROUND

        layout = self.layout()
        if layout is not None:
            container = QVBoxLayout()
            container.setContentsMargins(20, 20, 20, 20)

            msg = QLabel("Are you sure you want to delete this item?")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)

            buttonBox = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttonBox.accepted.connect(self.accept)
            buttonBox.rejected.connect(self.reject)

            container.addWidget(msg)
            container.addWidget(buttonBox)
            layout.addLayout(container)
```

---

## FramelessWidget

`FramelessWidget` is the base widget class implementing the layout logic for `FramelessWindow`. `FramelessWindow` is an alias of `FramelessWidget`. You can instantiate or subclass either depending on your semantic preference.

```python
from qtframeless import FramelessWidget

widget = FramelessWidget(hint=["min", "max", "close"])
widget.setWindowTitle("Generic Widget Window")
```

---

## Common Configuration Properties

All window classes inherit common configuration properties and methods:

### Title Bar Control Hints

The `hint` constructor argument controls which vector control buttons appear in the top-right corner of the title bar:

| Key | Description | Corresponding Button Class |
| --- | --- | --- |
| `"min"` | Minimize button | `MinimizeButton` |
| `"max"` | Maximize / Restore button | `MaximizeButton` |
| `"close"` | Close button | `CloseButton` |
| `"full_screen"` | Fullscreen toggle button | `FullScreenButton` |

```python
# Display only minimize and close
window = FramelessWindow(hint=["min", "close"])

# Update hints dynamically at runtime
window.getTitleBar().setTitleBarHint(["close"])
```

### Window Resizability and Dragging

```python
# Disable border resizing
window.setResizable(False)
assert not window.isResizable()

# Adjust resize border thickness (default is 5px)
window.setBorderWidth(8)

# Toggle press-to-move window dragging from title bar
window.setPressToMove(True)
```

### Windows 11 Styling Attributes

```python
from qtframeless import WindowCornerPreference

# Corner rounding: ROUND, ROUND_SMALL, DO_NOT_ROUND, DEFAULT
window.windowCornerPreference = WindowCornerPreference.ROUND

# Native border color (hex string or QColor)
window.borderColor = "#4A90E2"
```
