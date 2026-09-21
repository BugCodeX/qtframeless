# Getting Started

This guide walks you through installing `qtframeless` and creating your first frameless Qt window on Windows.

---

## Installation

`qtframeless` is compatible with **Python 3.10+** on Windows. You can install it alongside your preferred Qt binding using `pip` or `uv`.

=== "PySide6 (Recommended)"

    ```bash
    # With pip
    pip install qtframeless[pyside6]

    # With uv
    uv add qtframeless --extra pyside6
    ```

=== "PyQt6"

    ```bash
    # With pip
    pip install qtframeless[pyqt6]

    # With uv
    uv add qtframeless --extra pyqt6
    ```

=== "Existing Qt Environment"

    If you already have `PySide6`, `PyQt6`, or `PyQt5` installed in your virtual environment:

    ```bash
    pip install qtframeless
    ```

---

## Minimal Working Window

Here is a complete, runnable application using `FramelessMainWindow`:

```python linenums="1"
import sys
from PySide6.QtWidgets import QApplication, QLabel
from qtframeless import FramelessMainWindow, WindowCornerPreference


class MainWindow(FramelessMainWindow):
    """Main application window using qtframeless."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QtFrameless Quickstart")
        self.resize(800, 500)

        # Configure Windows 11 rounded corners and dark border
        self.windowCornerPreference = WindowCornerPreference.ROUND
        self.borderColor = "#696969"

        # Add widgets to the central layout
        centralWidget = self.centralWidget()
        if centralWidget is not None and centralWidget.layout() is not None:
            label = QLabel("Welcome to qtframeless!")
            centralWidget.layout().addWidget(label)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

### What Happens When You Run This?

1. **Native DWM Integration**: The window receives true native drop shadows and rounded corners managed by Windows DWM.
2. **Integrated Title Bar**: A custom, vector-rendered title bar is placed at the top, supporting drag-to-move, double-click to maximize/restore, and DPI-aware vector buttons.
3. **Windows 11 Snap Layouts**: Hovering over the maximize button automatically triggers the native Windows 11 Snap Layouts flyout.
4. **Smooth Resizing**: The edges and corners act as hardware-accelerated Win32 resize grips with standard cursor icons.

---

## Fundamental Concepts

To build applications with `qtframeless`, it helps to understand three core design concepts:

### 1. The Win32 Message Pump Bridge

Instead of hiding the window frame using Qt flags alone, `qtframeless` intercepts native Windows messages via `nativeEvent`:

- `WM_NCCALCSIZE`: Tells Windows that the client area should occupy the entire window frame, removing the default title bar while keeping DWM composition active.
- `WM_NCHITTEST`: Translates cursor positions into Win32 hit codes (`HTCAPTION`, `HTLEFT`, `HTRIGHT`, `HTMAXBUTTON`, etc.), providing native drag and resize mechanics.
- `WM_DPICHANGED`: Adjusts geometries and title bar vector elements when dragged across monitors with different DPI scalings.

### 2. Standard Qt Widget Hierarchy

`FramelessMainWindow` subclasses `QMainWindow`. The title bar is hosted inside the central widget alongside your content layout, ensuring that:

- Standard menu bars can be integrated directly into the title bar via `self.menuBar()`.
- Qt status bars, docks, and toolbars continue to operate without interference.
- Your widgets are added using familiar Qt layouts (`centralWidget.layout().addWidget(...)`).

### 3. DPI Awareness and Vector Buttons

All title bar buttons (`MinimizeButton`, `MaximizeButton`, `CloseButton`, `FullScreenButton`) are vector-rendered using `QPainter`. They scale smoothly on high-DPI displays (100%, 125%, 150%, 200%+) without pixelation or blurry assets.

---

## Next Steps

Now that you have a running frameless window:

- [Explore Window Types](guides/windows.md) to learn about `FramelessWindow`, `FramelessDialog`, and `FramelessWidget`.
- [Customize the TitleBar](guides/titlebar.md) to embed `QMenuBar`, center titles, or customize control buttons.
- [Apply Fluent Styling](guides/styling.md) to use Windows 11 Mica and Fluent Acrylic backdrops.
