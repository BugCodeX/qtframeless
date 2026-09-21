<div align="center">
  <img src="docs/images/logo.png" alt="qtframeless logo" width="320" />

  # qtframeless

  **Modern, cross-Qt frameless window framework for Windows in pure Python.**

  [![PyPI Version](https://img.shields.io/pypi/v/qtframeless.svg?color=blue)](https://pypi.org/project/qtframeless/)
  [![Python Versions](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://pypi.org/project/qtframeless/)
  [![PySide6](https://img.shields.io/badge/Qt-PySide6-41cd52.svg)](https://pypi.org/project/PySide6/)
  [![PyQt6](https://img.shields.io/badge/Qt-PyQt6-41cd52.svg)](https://pypi.org/project/PyQt6/)
  [![Platform](https://img.shields.io/badge/platform-Windows-0078d6.svg)](https://www.microsoft.com/windows)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
</div>

---

## Overview

**qtframeless** is a modern, lightweight, pure-Python framework for building native-feeling frameless windows in Qt on Windows.

Standard Qt frameless windows (`Qt.WindowType.FramelessWindowHint`) strip away crucial operating system capabilities: native DWM drop shadows, smooth window resize borders, Windows 11 Snap Layout menus, and modern backdrop materials like Mica and Acrylic.

`qtframeless` restores these native Win32 window mechanics through `ctypes` and `pywin32`—with **zero C++ compilation** or binary wheel dependencies required.

---

## Key Features

- **Windows 11 Snap Layouts**: Full native support for the Windows 11 Snap Layout hover menu on the maximize/restore button via non-client `WM_NCHITTEST` and `HTMAXBUTTON` hit testing.
- **Windows 11 Mica & Mica Alt**: Native DWM backdrop materials matching the user's desktop wallpaper and system theme (`DWMSBT_MAINWINDOW` and `DWMSBT_TABBEDWINDOW`).
- **Windows Fluent Acrylic Blur**: Native blur-behind backdrop material for Windows 10 and 11 with customizable gradient tint color and opacity.
- **DWM Rounded Corners & Borders**: Configurable native Windows 11 corner rounding preferences (`ROUND`, `ROUND_SMALL`, `DO_NOT_ROUND`) and custom border colors.
- **Dark / Light QPalette Synchronization**: Automatic detection of Windows system theme transitions with seamless `QPalette` and title bar color synchronization.
- **Per-Monitor DPI Scaling**: Dynamic coordinate scaling and crisp vector rendering across multiple displays handling `WM_DPICHANGED` messages.
- **Modular Vector Title Bar**: High-DPI crisp title bar featuring vector-drawn control buttons (minimize, maximize/restore, close) rendered with `QPainter`, custom icon, title, and central widget slots.
- **Pure Python Implementation**: Built entirely on standard Python `ctypes` and `pywin32`—no C++ compilers or precompiled binaries needed.
- **Cross-Qt Compatibility**: Seamless support across **PySide6**, **PyQt6**, and **PyQt5** via `qtpy`.

---

## Installation

Install `qtframeless` with your preferred Qt binding:

```bash
# With PySide6 (recommended)
pip install qtframeless[pyside6]

# With PyQt6
pip install qtframeless[pyqt6]

# If you already have a Qt binding installed
pip install qtframeless
```

---

## Quick Start

### 1. Standard Frameless Window

A standard frameless window featuring native DWM drop shadows, rounded corners, custom border color, and full Snap Layouts support:

```python
import sys
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout
from qtframeless import FramelessMainWindow, WindowCornerPreference


class MainWindow(FramelessMainWindow):
    """Frameless main window application."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._setupContent()

    def _setupContent(self) -> None:
        """Configure title bar and window content."""
        self.setWindowTitle("QtFrameless Demo")
        self.resize(800, 500)

        # Configure Windows 11 styling
        self.windowCornerPreference = WindowCornerPreference.ROUND
        self.borderColor = "#696969"
        self.darkTheme = False

        # Customize title bar
        titleBar = self.getTitleBar()
        if titleBar is not None:
            titleBar.setTitleBarFont(QFont("Segoe UI", 10))
            titleBar.setIconSize(18, 18)
            titleBar.setTitleBarHint(["min", "max", "close"])

        # Add content to central widget
        centralWidget = self.centralWidget()
        if centralWidget is not None and centralWidget.layout() is not None:
            contentLayout = QVBoxLayout()
            label = QLabel("Welcome to qtframeless!")
            toggleButton = QPushButton("Toggle Dark / Light Theme")
            toggleButton.clicked.connect(self._toggleTheme)

            contentLayout.addWidget(label)
            contentLayout.addWidget(toggleButton)
            centralWidget.layout().addLayout(contentLayout)

    def _toggleTheme(self) -> None:
        """Toggle dark and light window themes."""
        self.darkTheme = not self.darkTheme


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

### 2. Windows 11 Mica MainWindow

Leverage the native Windows 11 Mica backdrop material:

```python
import sys
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout
from qtframeless import FramelessMicaMainWindow, WindowCornerPreference


class MicaWindow(FramelessMicaMainWindow):
    """Frameless window with native Windows 11 Mica backdrop."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, isAlt=False, **kwargs)
        self._setupContent()

    def _setupContent(self) -> None:
        """Configure Mica backdrop and content."""
        self.setWindowTitle("Windows 11 Mica")
        self.resize(800, 500)
        self.windowCornerPreference = WindowCornerPreference.ROUND

        titleBar = self.getTitleBar()
        if titleBar is not None:
            titleBar.setTitleBarFont(QFont("Segoe UI", 10))

        centralWidget = self.centralWidget()
        if centralWidget is not None and centralWidget.layout() is not None:
            label = QLabel("Native Mica backdrop window")
            centralWidget.layout().addWidget(label)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MicaWindow()
    window.show()
    sys.exit(app.exec())
```

> **Tip**: Set `isAlt=True` or call `self.setIsAlt(True)` to enable **Mica Alt** (tabbed material).

### 3. Windows Fluent Acrylic MainWindow

Apply native Windows Fluent Acrylic blur-behind material with custom tint color:

```python
import sys
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout
from qtframeless import FramelessAcrylicMainWindow, WindowCornerPreference


class AcrylicWindow(FramelessAcrylicMainWindow):
    """Frameless window with Windows Fluent Acrylic blur-behind material."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, gradientColor="F2F2F299", **kwargs)
        self._setupContent()

    def _setupContent(self) -> None:
        """Configure Acrylic blur backdrop and content."""
        self.setWindowTitle("Windows Acrylic Material")
        self.resize(800, 500)
        self.windowCornerPreference = WindowCornerPreference.ROUND

        titleBar = self.getTitleBar()
        if titleBar is not None:
            titleBar.setTitleBarFont(QFont("Segoe UI", 10))

        centralWidget = self.centralWidget()
        if centralWidget is not None and centralWidget.layout() is not None:
            layout = QVBoxLayout()
            toggleButton = QPushButton("Toggle Dark Acrylic")
            toggleButton.clicked.connect(self._toggleTheme)
            layout.addWidget(toggleButton)
            centralWidget.layout().addLayout(layout)

    def _toggleTheme(self) -> None:
        """Toggle dark/light theme and update Acrylic gradient tint."""
        self.darkTheme = not self.darkTheme
        self.setGradientColor("20202099" if self.darkTheme else "F2F2F299")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AcrylicWindow()
    window.show()
    sys.exit(app.exec())
```

---

## Architecture

The project is structured into three clean, decoupled layers:

```
src/qtframeless/
├── native/      # Low-level Win32 ctypes structures, DWM API, and system utilities
├── core/        # Frame controller, native event filtering, and theme controller
└── windows/     # High-level Qt widgets, material windows, and vector title bar
```

| Layer | Module | Responsibility |
|---|---|---|
| **`native`** | `win32_types.py` | ctypes mirrors for `MARGINS`, `NCCALCSIZE_PARAMS`, `APPBARDATA`, and DWM enums. |
| | `win32_utils.py` | Win32 utility functions for DPI, monitors, taskbar position, and OS build detection. |
| | `window_effect.py` | `WindowsEffectHelper` wrapping `user32` and `dwmapi` for Mica, Acrylic, and DWM styles. |
| **`core`** | `frame_controller.py` | `WindowFrameController` handling `WM_NCCALCSIZE`, `WM_NCHITTEST`, Snap Layouts, and resizing. |
| | `frameless_mixin.py` | `FramelessWindowMixin` integrating native Win32 messages, DWM shadows, and Qt properties. |
| | `theme.py` | `ThemeController` detecting Windows dark/light mode and synchronizing `QPalette`. |
| **`windows`** | `window.py` | Ready-to-use window classes (`FramelessMainWindow`, `FramelessMicaMainWindow`, `FramelessAcrylicMainWindow`). |
| | `title_bar.py` | High-DPI `TitleBar` with icon, title, customizable hints, and center widget slot. |
| | `buttons.py` | Vector-rendered control buttons (`MinimizeButton`, `MaximizeButton`, `CloseButton`) via `QPainter`. |

---

## Windows Compatibility

`qtframeless` automatically detects the host Windows OS build at runtime and gracefully enables or falls back on visual effects:

| Feature | Windows 11 22H2+<br>(Build &ge; 22621) | Windows 11 21H2<br>(Build &ge; 22000) | Windows 10 1809+<br>(Build &ge; 17763) |
|---|:---:|:---:|:---:|
| **Frameless DWM Drop Shadows** | Full | Full | Full |
| **Snap Layouts Hover Menu** | Full | Full | &mdash; |
| **DWM Rounded Corners** | Full | Full | &mdash; |
| **Mica Material** | Full | Full | &mdash; |
| **Mica Alt (Tabbed Material)** | Full | &mdash; | &mdash; |
| **Acrylic Blur-Behind** | Full | Full | Full |
| **Dark / Light Theme Sync** | Full | Full | Full |
| **Per-Monitor DPI Scaling** | Full | Full | Full |

*Note: On non-Windows platforms, importing `qtframeless` raises `PlatformNotSupportedError`.*

---

## Development & Testing

We use [uv](https://github.com/astral-sh/uv) for fast, reproducible dependency management and execution:

```bash
# Clone the repository
git clone https://github.com/BugCodeX/qtframeless.git
cd qtframeless

# Sync development dependencies (including test extras and PySide6)
uv sync --extra test --extra pyside6

# Run the test suite with pytest
uv run pytest

# Run linting with ruff
uv run ruff check .

# Run static type checking with pyright
uv run pyright

# Build source distribution and wheel
uv build
```

---

## License

This project is licensed under the terms of the [MIT License](LICENSE).
