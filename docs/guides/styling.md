# Materials & Styling

`qtframelesskit` provides deep integration with native Windows desktop composition features, including Windows 11 **Mica**, **Mica Alt**, and **Fluent Acrylic** blur-behind backdrops, DWM corner rounding, custom border colors, and automatic dark/light theme synchronization.

---

## Windows 11 Mica Material

**Mica** is a dynamic desktop material introduced in Windows 11 that softly samples the user's desktop wallpaper to create a subtle, personalized backdrop behind window content.

### Standard Mica

Use `FramelessMicaMainWindow`, `FramelessMicaWindow`, or `FramelessMicaDialog`:

```python linenums="1"
import sys
from PySide6.QtWidgets import QApplication, QLabel
from qtframelesskit import FramelessMicaMainWindow, WindowCornerPreference


class MicaWindow(FramelessMicaMainWindow):
    """Window featuring Windows 11 Mica backdrop material."""

    def __init__(self) -> None:
        super().__init__(isAlt=False)
        self.setWindowTitle("Windows 11 Mica Example")
        self.resize(800, 500)

        # Rounded corners match Windows 11 aesthetic
        self.windowCornerPreference = WindowCornerPreference.ROUND

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

### Mica Alt (Tabbed Surfaces)

**Mica Alt** (available on Windows 11 22H2 Build 22621+) provides a more pronounced sampling of desktop tinting, specifically designed for tabbed title bars and document-heavy applications (like Windows 11 Notepad and File Explorer).

Enable Mica Alt by passing `isAlt=True` to the constructor or calling `setIsAlt(True)`:

```python
class MicaAltWindow(FramelessMicaMainWindow):
    def __init__(self) -> None:
        super().__init__(isAlt=True)
        self.setWindowTitle("Windows 11 Mica Alt Example")
```

Or toggle it dynamically:

```python
window.setIsAlt(True)
assert window.isAlt()
```

---

## Windows Fluent Acrylic Material

**Acrylic** is a translucent blur-behind material that reveals desktop contents with a fine noise texture and custom tint color. It is supported on both **Windows 10 (1809+)** and **Windows 11**.

Use `FramelessAcrylicMainWindow`, `FramelessAcrylicWindow`, or `FramelessAcrylicDialog`:

```python linenums="1"
import sys
from PySide6.QtWidgets import QApplication, QLabel
from qtframelesskit import FramelessAcrylicMainWindow, WindowCornerPreference


class AcrylicWindow(FramelessAcrylicMainWindow):
    """Window featuring native Windows Fluent Acrylic blur-behind material."""

    def __init__(self) -> None:
        # gradientColor format: RRGGBBAA hex string or integer
        # "20202099" -> Dark tint with ~60% opacity
        # "F0F0F099" -> Light tint with ~60% opacity
        super().__init__(gradientColor="20202099")

        self.setWindowTitle("Fluent Acrylic Example")
        self.resize(800, 500)
        self.windowCornerPreference = WindowCornerPreference.ROUND

        centralWidget = self.centralWidget()
        if centralWidget is not None and centralWidget.layout() is not None:
            label = QLabel("Native Acrylic blur backdrop")
            centralWidget.layout().addWidget(label)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AcrylicWindow()
    window.show()
    sys.exit(app.exec())
```

### Dynamic Tint Color

You can change the Acrylic gradient tint color at runtime:

```python
# Change tint to light frosted glass
window.setGradientColor("F0F0F080")

# Or read active tint
currentColor = window.getGradientColor()
```

---

## Window Corner Rounding

Windows 11 allows applications to specify their DWM window corner rounding preferences via the `WindowCornerPreference` enum:

| Preference | DWM Value | Appearance |
| --- | --- | --- |
| `WindowCornerPreference.DEFAULT` | `0` | System decides rounding based on window styles. |
| `WindowCornerPreference.DO_NOT_ROUND` | `1` | Square 90-degree corners (Windows 10 style). |
| `WindowCornerPreference.ROUND` | `2` | Standard Windows 11 rounded corners (~8px radius). |
| `WindowCornerPreference.ROUND_SMALL` | `3` | Subtle rounded corners (~4px radius), ideal for tool windows. |

Configure corner rounding through the Qt property or method:

```python
from qtframelesskit import WindowCornerPreference

# Using property syntax
window.windowCornerPreference = WindowCornerPreference.ROUND

# Or using method syntax
window.setWindowCornerPreference(WindowCornerPreference.ROUND_SMALL)
```

---

## Native Border Color

On Windows 11 (Build 22000+), DWM supports custom window border colors. `qtframelesskit` exposes this through the `borderColor` property:

```python
from PySide6.QtGui import QColor

# Hex string
window.borderColor = "#0078D4"

# Or QColor object
window.borderColor = QColor(105, 105, 105)

# Reset to system default border
window.setBorderColor(None)
```

---

## Dark & Light Theme Synchronization

`qtframelesskit` automatically detects the Windows system color scheme using registry monitoring and native `WM_SETTINGCHANGE` notifications.

### Reacting to Theme Changes

Connect to the `darkThemeChanged` signal:

```python
class ThemedWindow(FramelessMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.darkThemeChanged.connect(self._onThemeChanged)

        # Apply initial theme
        self._onThemeChanged(self.isDarkTheme())

    def _onThemeChanged(self, isDark: bool) -> None:
        if isDark:
            self.setStyleSheet("QLabel { color: #FFFFFF; }")
            self.borderColor = "#333333"
        else:
            self.setStyleSheet("QLabel { color: #000000; }")
            self.borderColor = "#CCCCCC"
```

### Manual Theme Override

If your application has an in-app theme toggle independent of Windows system settings:

```python
# Disable automatic Windows theme tracking
window.setDetectingThemeAllowed(False)

# Explicitly force dark theme
window.setDarkTheme(True)
```
