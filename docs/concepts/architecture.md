# Architecture

`qtframeless` is structured into three clean architectural layers. This separation ensures that low-level Win32 ctypes calls remain isolated from high-level Qt widget ergonomics.

```text
+-------------------------------------------------------------------------+
|                              windows Layer                              |
|   FramelessMainWindow  *  FramelessWindow  *  FramelessDialog           |
|   TitleBar  *  MinimizeButton  *  MaximizeButton  *  CloseButton        |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                               core Layer                                |
|   FramelessMixin  *  WindowFrameController  *  ThemeController         |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                              native Layer                               |
|   win32_types (ctypes)  *  win32_utils (APIs)  *  window_effect (DWM)   |
+-------------------------------------------------------------------------+
```

---

## The Three Layers

### 1. The `native` Layer

The `native` layer directly interacts with Windows system DLLs (`dwmapi.dll`, `user32.dll`, `gdi32.dll`) via `ctypes` and `pywin32`.

- **`win32_types.py`**:
  - Defines exact 1:1 `ctypes.Structure` representations of Win32 data types:
    - `NCCALCSIZE_PARAMS` & `PWINDOWPOS`: Sizing rectangles passed during `WM_NCCALCSIZE`.
    - `MARGINS`: Frame extension margins for `DwmExtendFrameIntoClientArea`.
    - `ACCENT_POLICY` & `WINDOWCOMPOSITIONATTRIBDATA`: Undocumented Windows composition structures for Acrylic blur.
    - `DWM_BLURBEHIND`: Classic Aero blur configuration.
  - Defines enums for DWM attributes (`WindowCornerPreference`, `WindowEffect`, `DWMWINDOWATTRIBUTE`).

- **`win32_utils.py`**:
  - Provides utility functions querying system states:
    - `getDpiForWindow(hWnd)`: Retrieves per-monitor DPI scaling.
    - `getResizeBorderThickness(hWnd)`: Reads system metric `SM_CXFRAME` + `SM_CXPADDEDBORDER`.
    - `isMaximized(hWnd)` & `isFullScreen(hWnd)`: Queries window placement and style flags.
    - `Taskbar`: Calculates auto-hide and visible taskbar geometry across monitors.
    - `isGreaterEqualWin11()`: Evaluates Windows OS build version numbers.

- **`window_effect.py`**:
  - `WindowsEffectHelper` acts as the DWM composition manager:
    - Sets backdrop effects: `setMicaEffect(hWnd, isAlt)` and `setAcrylicEffect(hWnd, gradientColor)`.
    - Configures corner rounding: `setWindowCornerPreference(hWnd, preference)`.
    - Sets title bar and border colors: `setBorderColor(hWnd, color)` and `setCaptionColor(hWnd, color)`.

---

### 2. The `core` Layer

The `core` layer bridges Windows operating system events into Qt's event loop without requiring C++ extensions.

- **`frame_controller.py` (`WindowFrameController`)**:
  - The core message processor for native Win32 window messages:
    - `WM_NCCALCSIZE`: Strips standard title bar borders while preserving DWM client calculations.
    - `WM_NCHITTEST`: Tests cursor coordinates against window resize borders, title bar drag zones, and control buttons.
    - `WM_DPICHANGED`: Adjusts window geometry when moved between monitors with varying DPI scales.
    - Non-client mouse events: Processes `WM_NCMOUSEMOVE`, `WM_NCLBUTTONDOWN`, and `WM_NCLBUTTONUP` to drive `MaximizeButton` hover states.

- **`frameless_mixin.py` (`FramelessWindowMixin`)**:
  - Installed on top-level Qt widgets.
  - Overrides `nativeEvent(eventType, message)` to forward Win32 messages directly to `WindowFrameController`.
  - Manages Qt properties (`borderColor`, `windowCornerPreference`, `resizable`, `pressToMove`) and signals (`darkThemeChanged`, `resizableChanged`).

- **`theme.py` (`ThemeController`)**:
  - Monitors the Windows registry key `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize`.
  - Emits signals when Windows toggles between Light and Dark mode.

---

### 3. The `windows` Layer

The `windows` layer exposes idiomatic, ready-to-use Qt widget classes.

- **`window.py`**:
  - Provides concrete window subclasses:
    - Standard opaque: `FramelessMainWindow`, `FramelessWindow`, `FramelessDialog`, `FramelessWidget`.
    - Windows 11 Mica: `FramelessMicaMainWindow`, `FramelessMicaWindow`, `FramelessMicaDialog`.
    - Windows Fluent Acrylic: `FramelessAcrylicMainWindow`, `FramelessAcrylicWindow`, `FramelessAcrylicDialog`.
- **`title_bar.py`**:
  - Provides `TitleBar`, featuring left icon/title/menu areas, flexible center containers, and right-aligned vector control buttons.
- **`buttons.py`**:
  - Provides `VectorButton`, `MinimizeButton`, `MaximizeButton`, `CloseButton`, and `FullScreenButton` rendered with `QPainter`.

---

## Win32 Message Flow

```text
[Windows OS / DWM]
        |
        | Native Win32 Messages (WM_NCCALCSIZE, WM_NCHITTEST, etc.)
        v
[Qt Event Loop: QWidget.nativeEvent]
        |
        v
[FramelessWindowMixin]
        |
        v
[WindowFrameController]
   +-----------------------+-----------------------+-----------------------+
   |                       |                       |                       |
   v                       v                       v                       v
WM_NCCALCSIZE           WM_NCHITTEST            WM_DPICHANGED          WM_SETTINGCHANGE
(Remove Frame)         (Border / Snap)          (Scale DPI)            (Update Theme)
   |                       |                       |                       |
   v                       v                       v                       v
Adjust client rect     Return HTCAPTION,        Update geometry,       Emit darkThemeChanged
preserving shadow      HTMAXBUTTON, HTLEFT      scale vector buttons   sync palette
```

### 1. `WM_NCCALCSIZE` (Frame Calculation)

When Windows creates or resizes a window, it sends `WM_NCCALCSIZE` to determine the client area rectangle.
In standard windows, the client rect is inset from the top by the height of the caption bar.
`WindowFrameController` adjusts `NCCALCSIZE_PARAMS`:

1. When **restored (normal)**: Leaves the client rect covering the entire window. The native frame is eliminated, but DWM shadow composition remains active.
2. When **maximized**: Compares window bounds against the active monitor's work area (using `GetMonitorInfoW`), trimming off invisible resize borders that would otherwise bleed over neighboring monitors or under the taskbar.

### 2. `WM_NCHITTEST` (Hit Testing)

Whenever the mouse moves, Windows asks the window what is under the cursor:

1. **Border Edges**: If the cursor is within `borderWidth` pixels of any edge, returns `HTLEFT`, `HTRIGHT`, `HTTOP`, `HTBOTTOM`, or diagonal corners.
2. **Maximize Button**: If cursor is inside `MaximizeButton.geometry()`, returns `HTMAXBUTTON`. This is what unlocks **Windows 11 Snap Layouts**.
3. **Title Bar Draggable Area**: If cursor is over the `TitleBar` (and not on an interactive widget like a menu or button), returns `HTCAPTION`.
4. **Window Client Area**: All other regions return `HTCLIENT`.

### 3. `WM_DPICHANGED` (DPI Scaling)

When the window is dragged between displays with different DPI scaling (e.g., from a 100% monitor to a 200% 4K monitor):

1. Windows sends `WM_DPICHANGED` with the suggested new window rectangle in `lParam`.
2. `WindowFrameController` applies the recommended rectangle.
3. `TitleBar.updateDpiScaling(newDpi)` scales the button heights, vector line thicknesses, and title bar fonts.

---

## Non-Invasive Qt Design

`qtframeless` does not inject global hooks, modify Qt internals, or require C++ binary wheels:

- **Clean Subclassing**: All classes inherit cleanly from Qt base classes (`QMainWindow`, `QWidget`, `QDialog`).
- **Standard Qt APIs**: You continue using `centralWidget()`, `layout()`, `menuBar()`, `show()`, and standard Qt signals/slots.
- **Pure Python**: Everything is executed through standard Python `ctypes` and `pywin32`.
