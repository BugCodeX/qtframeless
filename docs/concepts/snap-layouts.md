# Snap Layouts

Windows 11 introduced **Snap Layouts**: an operating system flyout that appears when hovering over the maximize button of any top-level window, allowing users to effortlessly tile windows into 2, 3, or 4 pane arrangements.

This document explains the technical challenges of supporting Snap Layouts in custom frameless Qt windows and how `qtframelesskit` implements full Snap Layout support.

---

## The Problem with Frameless Windows

In standard Qt applications, if you remove the title bar with `Qt.WindowType.FramelessWindowHint` and draw a custom maximize button:

1. The custom maximize button is an ordinary Qt widget residing in the **client area** (`HTCLIENT`).
2. The Windows Desktop Window Manager (DWM) has no knowledge that your custom button is a maximize button.
3. Hovering over the button triggers no OS flyout menu.
4. Win + Z (the keyboard shortcut for Snap Layouts) fails to anchor to your button.

To make Windows 11 trigger Snap Layouts, the OS must be informed via Win32 message interception that the cursor is resting on the system maximize button.

---

## The Hit-Testing Mechanism (`WM_NCHITTEST`)

When the cursor moves across the screen, Windows sends the window a `WM_NCHITTEST` message containing the cursor's global screen coordinates:

```python
x = msg.lParam & 0xFFFF
y = (msg.lParam >> 16) & 0xFFFF
```

The application responds with a hit-test result code indicating what part of the window the cursor is over.

To trigger Snap Layouts, `WindowFrameController` checks whether the cursor coordinates intersect the `MaximizeButton`:

```text
+-------------------------------------------------------------+
| [TitleBar]                                       [_] [[]] [X] |
+-------------------------------------------------------|-----+
                                                        |
                                            Cursor over MaximizeButton?
                                                        |
                                          +-------------+-------------+
                                          |                           |
                                         Yes                          No
                                          |                           |
                                          v                           v
                              Return (True, HTMAXBUTTON)      Return HTCAPTION /
                              Windows opens Snap Layouts!     HTCLIENT / HTBORDER
```

### Coordinate Mapping

The coordinates provided in `lParam` are in **global screen space** (pixels relative to the primary monitor). Because Qt widgets position themselves in **window local space**, `WindowFrameController` performs coordinate transformation:

```python
# 1. Convert screen coordinates to QPoint
cursorPos = QPoint(xPos, yPos)

# 2. Map global screen coordinate to window-local coordinate
posInWindow = self._window.mapFromGlobal(cursorPos)

# 3. Check if coordinate falls within the MaximizeButton geometry
maxButton = titleBar.getMaximizeButton()
if maxButton is not None and maxButton.isVisible():
    buttonRect = maxButton.geometry()
    # Map button rectangle to window coordinates
    buttonRectInWindow = QRect(
        maxButton.mapTo(self._window, QPoint(0, 0)),
        maxButton.size(),
    )
    if buttonRectInWindow.contains(posInWindow):
        # 4. Return HTMAXBUTTON (9) to Windows
        return (True, win32con.HTMAXBUTTON)
```

Returning `win32con.HTMAXBUTTON` instructs Windows to open the Snap Layouts flyout anchored directly to your `MaximizeButton` rectangle!

---

## Non-Client Mouse Event Handling

Returning `HTMAXBUTTON` creates an interesting challenge in Qt:

!!! warning "The Non-Client Trap"
    When Windows considers an area to be part of the **non-client** region (`HTMAXBUTTON`), it stops dispatching standard client mouse messages (`WM_MOUSEMOVE`, `WM_LBUTTONDOWN`, `WM_LBUTTONUP`).

    As a result:
    - Qt's `enterEvent` and `leaveEvent` will **not** trigger on the button.
    - Qt stylesheets like `QPushButton:hover` will **not** activate.
    - Standard Qt `clicked` signals will **not** fire.

To resolve this, `WindowFrameController` intercepts the non-client mouse messages and manually simulates the button states:

### 1. Hover Tracking (`WM_NCMOUSEMOVE` and `WM_NCMOUSELEAVE`)

When the cursor enters the non-client maximize button region, Windows sends `WM_NCMOUSEMOVE`.

`WindowFrameController`:

1. Calls `TrackMouseEvent` with `TME_NONCLIENT | TME_LEAVE` so Windows notifies when the mouse leaves the non-client area.
2. Updates `MaximizeButton.setHoverState(True)` to draw the visual hover highlight.
3. When `WM_NCMOUSELEAVE` arrives, sets `MaximizeButton.setHoverState(False)`.

```python
def _handleNcMouseMove(self, msg: MSG) -> tuple[bool, int] | None:
    # Request notification when the cursor leaves the non-client region
    trackEvent = TRACKMOUSEEVENT()
    trackEvent.cbSize = sizeof(TRACKMOUSEEVENT)
    trackEvent.dwFlags = TME_LEAVE | TME_NONCLIENT
    trackEvent.hwndTrack = int(self._window.winId())
    windll.user32.TrackMouseEvent(byref(trackEvent))

    if maxButton is not None:
        maxButton.setHoverState(True)
    return (True, 0)
```

### 2. Click Handling (`WM_NCLBUTTONDOWN` and `WM_NCLBUTTONUP`)

When the user clicks the maximize button while Snap Layouts is active or to maximize the window:

- `WM_NCLBUTTONDOWN`: Updates `MaximizeButton.setPressedState(True)`.
- `WM_NCLBUTTONUP`: Updates `MaximizeButton.setPressedState(False)` and invokes window maximize or restore:

```python
def _handleNcLButtonUp(self, msg: MSG) -> tuple[bool, int] | None:
    if self._isCursorOnMaximizeButton():
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()
        return (True, 0)
    return None
```

---

## Snapping to Grid

When the user hovers over the button and chooses a layout slot in the Windows 11 Snap flyout:

1. Windows calculates the target window rectangle based on the chosen slot.
2. Windows sends `WM_WINDOWPOSCHANGING` and `WM_NCCALCSIZE` to position and resize the window.
3. `WindowFrameController` processes the sizing smoothly, maintaining the frameless presentation, crisp vector button scales, and proper work area boundaries.

The entire interaction feels 100% native to Windows 11 users while running in pure Python.
