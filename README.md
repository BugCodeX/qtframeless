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

## Screenshots

### Windows 11

<div align="center">
  <img src="docs/images/windows11_showcase.gif" alt="qtframeless Windows 11 Showcase" width="800" />
</div>

### Windows 10

<div align="center">
  <img src="docs/images/windows10_showcase.gif" alt="qtframeless Windows 10 Showcase" width="800" />
</div>

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
from PySide6.QtWidgets import QApplication, QLabel
from qtframeless import FramelessMainWindow, WindowCornerPreference


class MainWindow(FramelessMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QtFrameless Demo")
        self.resize(800, 500)

        # Configure Windows 11 styling
        self.windowCornerPreference = WindowCornerPreference.ROUND
        self.borderColor = "#696969"

        # Add content to central widget
        centralWidget = self.centralWidget()
        if centralWidget is not None and centralWidget.layout() is not None:
            centralWidget.layout().addWidget(QLabel("Welcome to qtframeless!"))


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
from PySide6.QtWidgets import QApplication, QLabel
from qtframeless import FramelessMicaMainWindow, WindowCornerPreference


class MicaWindow(FramelessMicaMainWindow):
    def __init__(self) -> None:
        super().__init__(isAlt=False)
        self.setWindowTitle("Windows 11 Mica")
        self.resize(800, 500)
        self.windowCornerPreference = WindowCornerPreference.ROUND

        centralWidget = self.centralWidget()
        if centralWidget is not None and centralWidget.layout() is not None:
            centralWidget.layout().addWidget(QLabel("Native Mica backdrop window"))


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
from PySide6.QtWidgets import QApplication, QLabel
from qtframeless import FramelessAcrylicMainWindow, WindowCornerPreference


class AcrylicWindow(FramelessAcrylicMainWindow):
    def __init__(self) -> None:
        # Tint format: RRGGBBAA
        super().__init__(gradientColor="20202099")
        self.setWindowTitle("Windows Acrylic Material")
        self.resize(800, 500)
        self.windowCornerPreference = WindowCornerPreference.ROUND

        centralWidget = self.centralWidget()
        if centralWidget is not None and centralWidget.layout() is not None:
            centralWidget.layout().addWidget(QLabel("Native Acrylic blur backdrop"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AcrylicWindow()
    window.show()
    sys.exit(app.exec())
```

### 4. Integrated Title Bar MenuBar & Centered Title

Seamlessly embed a `QMenuBar` directly into the title bar alongside a centered window title:

```python
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from qtframeless import FramelessMainWindow


class Window(FramelessMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Example MainWindow")
        self.resize(800, 500)

        # 1. Center the title in the title bar
        self.getTitleBar().setTitleAlignment(Qt.AlignmentFlag.AlignCenter)

        # 2. Add menus directly to the integrated title bar menu bar
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu("File(&F)")
        fileMenu.addAction("New(&N)")
        fileMenu.addAction("Open(&O)")

        editMenu = menuBar.addMenu("Edit(&E)")
        editMenu.addAction("Undo(&U)")
        editMenu.addAction("Redo(&R)")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
```

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

## Acknowledgments & Inspiration

Special thanks and credit to the open-source projects that inspired and informed this framework:

- [qwindowkit](https://github.com/stdware/qwindowkit) by stdware: An outstanding C++ window customization framework for Qt, which served as a primary architectural inspiration for native frameless mechanics, Windows 11 Snap Layout hit-testing, and modern DWM composition patterns.

---

## License

This project is licensed under the terms of the [MIT License](LICENSE).
