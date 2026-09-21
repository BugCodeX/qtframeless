"""Win32 native window frame message controller.

Encapsulates non-client calculations, border resize hit testing, non-client mouse events,
DPI changes, and native window drag delegation.
"""

from ctypes import byref, cast, sizeof, windll
from ctypes.wintypes import LPRECT, MSG
from typing import TYPE_CHECKING
from typing import cast as typeCast

import win32con
import win32gui
from qtpy.QtCore import QByteArray, QPoint, QRect
from qtpy.QtGui import QCursor
from qtpy.QtWidgets import QWidget

from qtframeless.native.win32_types import (
    LPNCCALCSIZE_PARAMS,
    TME_LEAVE,
    TME_NONCLIENT,
    TRACKMOUSEEVENT,
    WM_DPICHANGED,
    WM_NCMOUSELEAVE,
)
from qtframeless.native.win32_utils import (
    Taskbar,
    getDpiForWindow,
    getResizeBorderThickness,
    isFullScreen,
    isMaximized,
)

if TYPE_CHECKING:
    from qtframeless.windows.title_bar import TitleBar

__all__ = ["WindowFrameController"]


class WindowFrameController:
    """Controller managing native Win32 window frame messages and sizing logic.

    Parameters
    ----------
    window : QWidget
        Target top-level window widget.
    borderWidth : int, default=5
        Resize border thickness in pixels.
    resizable : bool, default=True
        Whether window resizing is enabled.
    pressToMove : bool, default=True
        Whether press-to-move window dragging is enabled.
    dpiScaling : bool, default=True
        Whether automatic DPI scaling is allowed.
    """

    def __init__(
        self,
        window: QWidget,
        borderWidth: int = 5,
        resizable: bool = True,
        pressToMove: bool = True,
        dpiScaling: bool = True,
    ) -> None:
        self._window = window
        self._borderWidth = borderWidth
        self._border_width = borderWidth
        self._resizable = resizable
        self._pressToMove = pressToMove
        self._dpiScalingFlag = dpiScaling

    def getBorderWidth(self) -> int:
        """Return the resize border thickness in pixels.

        Returns
        -------
        int
            Border width in pixels.
        """
        return self._borderWidth

    def setBorderWidth(self, width: int) -> None:
        """Set the resize border thickness in pixels.

        Parameters
        ----------
        width : int
            New border width in pixels.
        """
        self._borderWidth = width
        self._border_width = width
        if hasattr(self._window, "_borderWidth"):
            self._window._borderWidth = width
            self._window._border_width = width

    def isResizable(self) -> bool:
        """Return whether the window can be resized.

        Returns
        -------
        bool
            True if resizing is allowed.
        """
        return self._resizable

    def setResizable(self, resizable: bool) -> None:
        """Set whether the window is resizable.

        Parameters
        ----------
        resizable : bool
            True to allow resizing.
        """
        self._resizable = resizable

    def isPressToMove(self) -> bool:
        """Return whether press-to-move dragging is enabled.

        Returns
        -------
        bool
            True if press-to-move is enabled.
        """
        return self._pressToMove

    def setPressToMove(self, enabled: bool) -> None:
        """Enable or disable press-to-move window dragging.

        Parameters
        ----------
        enabled : bool
            True to enable press-to-move.
        """
        self._pressToMove = enabled

    def isDpiScalingAllowed(self) -> bool:
        """Return whether automatic DPI scaling is allowed.

        Returns
        -------
        bool
            True if automatic DPI scaling is allowed.
        """
        return self._dpiScalingFlag

    def setDpiScalingAllowed(self, allow: bool) -> None:
        """Enable or disable automatic DPI scaling.

        Parameters
        ----------
        allow : bool
            True to allow automatic DPI scaling.
        """
        self._dpiScalingFlag = allow

    def startSystemMove(self) -> None:
        """Start native system window drag."""
        targetWindow = self._window.window()
        if targetWindow:
            windowHandle = targetWindow.windowHandle()
            if windowHandle:
                windowHandle.startSystemMove()

    def _getTitleBar(self) -> "TitleBar | None":
        """Return title bar instance associated with target window if present.

        Returns
        -------
        TitleBar or None
            Title bar instance or None.
        """
        if hasattr(self._window, "getTitleBar"):
            return self._window.getTitleBar()
        return getattr(self._window, "_titleBar", None)

    def handleNativeEvent(
        self, eventType: QByteArray | bytes, message: int
    ) -> tuple[bool, int] | None:
        """Process native Win32 messages for window framing, sizing, and hit testing.

        Parameters
        ----------
        eventType : QByteArray or bytes
            Native event type identifier.
        message : int
            Pointer address to the native Win32 MSG structure.

        Returns
        -------
        tuple of (bool, int) or None
            Tuple of (True, result_code) when message is handled, or None when unhandled.
        """
        _ = eventType
        msg = MSG.from_address(int(message))
        if not msg.hWnd:
            return None

        msgType = msg.message
        if msgType == win32con.WM_NCHITTEST:
            return self._handleNcHitTest(msg)
        if msgType == win32con.WM_NCMOUSEMOVE:
            return self._handleNcMouseMove(msg)
        if msgType == WM_NCMOUSELEAVE:
            return self._handleNcMouseLeave(msg)
        if msgType == win32con.WM_NCLBUTTONDOWN:
            return self._handleNcLButtonDown(msg)
        if msgType == win32con.WM_NCLBUTTONUP:
            return self._handleNcLButtonUp(msg)
        if msgType == win32con.WM_NCCALCSIZE:
            return self._handleNcCalcSize(msg)
        if msgType == win32con.WM_SETTINGCHANGE:
            return self._handleSettingChange(msg)
        if msgType == win32con.WM_STYLECHANGING:
            return self._handleStyleChanging(msg)
        if msgType == WM_DPICHANGED:
            return self._handleDpiChanged(msg)

        return None

    def _handleNcHitTest(self, msg: MSG) -> tuple[bool, int] | None:
        """Process WM_NCHITTEST message for window border and title bar hit testing.

        Parameters
        ----------
        msg : MSG
            Win32 MSG structure pointer.

        Returns
        -------
        tuple of (bool, int) or None
            Hit test result if handled, or None if in client area / unhandled.
        """
        if self._resizable:
            if not self._window.isMaximized():
                cursorPosition = QCursor.pos()
                x = cursorPosition.x() - self._window.x()
                y = cursorPosition.y() - self._window.y()
                width, height = self._window.width(), self._window.height()

                dpi = getDpiForWindow(msg.hWnd)
                scaledBorderWidth = round(self._borderWidth * dpi / 96)

                left = x < scaledBorderWidth
                top = y < scaledBorderWidth
                right = x > width - scaledBorderWidth
                bottom = y > height - scaledBorderWidth

                if top and left:
                    return True, win32con.HTTOPLEFT
                if top and right:
                    return True, win32con.HTTOPRIGHT
                if bottom and left:
                    return True, win32con.HTBOTTOMLEFT
                if bottom and right:
                    return True, win32con.HTBOTTOMRIGHT
                if left:
                    return True, win32con.HTLEFT
                if top:
                    return True, win32con.HTTOP
                if right:
                    return True, win32con.HTRIGHT
                if bottom:
                    return True, win32con.HTBOTTOM

            titleBar = self._getTitleBar()
            if titleBar is not None:
                maximizeButton = titleBar.getMaximizeButton()
                if maximizeButton is not None and maximizeButton.isVisible():
                    buttonPosition = maximizeButton.mapTo(
                        typeCast(QWidget, self._window), QPoint(0, 0)
                    )
                    buttonRect = QRect(buttonPosition, maximizeButton.size())
                    cursorPosition = QCursor.pos()
                    windowPoint = self._window.mapFromGlobal(cursorPosition)
                    if buttonRect.contains(windowPoint):
                        return True, win32con.HTMAXBUTTON
        return None

    def _handleNcMouseMove(self, msg: MSG) -> tuple[bool, int] | None:
        """Process WM_NCMOUSEMOVE message for snap layout maximize button hovering.

        Parameters
        ----------
        msg : MSG
            Win32 MSG structure pointer.

        Returns
        -------
        tuple of (bool, int) or None
            (True, 0) if handled, or None if unhandled.
        """
        titleBar = self._getTitleBar()
        if titleBar is not None:
            maximizeButton = titleBar.getMaximizeButton()
            if maximizeButton is not None:
                if msg.wParam == win32con.HTMAXBUTTON:
                    maximizeButton.setHoverState(True)
                    trackMouseEvent = TRACKMOUSEEVENT()
                    trackMouseEvent.cbSize = sizeof(TRACKMOUSEEVENT)
                    trackMouseEvent.dwFlags = TME_NONCLIENT | TME_LEAVE
                    trackMouseEvent.hwndTrack = msg.hWnd
                    trackMouseEvent.dwHoverTime = 0
                    windll.user32.TrackMouseEvent(byref(trackMouseEvent))
                    return True, 0
                if maximizeButton.isHovered():
                    maximizeButton.setHoverState(False)
                    maximizeButton.setPressedState(False)
        return None

    def _handleNcMouseLeave(self, msg: MSG) -> tuple[bool, int] | None:
        """Process WM_NCMOUSELEAVE message to reset maximize button hover state.

        Parameters
        ----------
        msg : MSG
            Win32 MSG structure pointer.

        Returns
        -------
        tuple of (bool, int)
            (True, 0) indicating handled event.
        """
        _ = msg
        titleBar = self._getTitleBar()
        if titleBar is not None:
            maximizeButton = titleBar.getMaximizeButton()
            if maximizeButton is not None:
                maximizeButton.setHoverState(False)
                maximizeButton.setPressedState(False)
        return True, 0

    def _handleNcLButtonDown(self, msg: MSG) -> tuple[bool, int] | None:
        """Process WM_NCLBUTTONDOWN message for maximize button pressing.

        Parameters
        ----------
        msg : MSG
            Win32 MSG structure pointer.

        Returns
        -------
        tuple of (bool, int) or None
            (True, 0) if handled, or None if unhandled.
        """
        if msg.wParam == win32con.HTMAXBUTTON:
            titleBar = self._getTitleBar()
            if titleBar is not None:
                maximizeButton = titleBar.getMaximizeButton()
                if maximizeButton is not None:
                    maximizeButton.setPressedState(True)
            return True, 0
        return None

    def _handleNcLButtonUp(self, msg: MSG) -> tuple[bool, int] | None:
        """Process WM_NCLBUTTONUP message for maximize button clicking and window toggle.

        Parameters
        ----------
        msg : MSG
            Win32 MSG structure pointer.

        Returns
        -------
        tuple of (bool, int) or None
            (True, 0) if handled, or None if unhandled.
        """
        titleBar = self._getTitleBar()
        if msg.wParam == win32con.HTMAXBUTTON:
            if titleBar is not None:
                maximizeButton = titleBar.getMaximizeButton()
                if maximizeButton is not None:
                    maximizeButton.setPressedState(False)
            if self._window.isMaximized():
                self._window.showNormal()
            else:
                self._window.showMaximized()
            return True, 0

        if titleBar is not None:
            maximizeButton = titleBar.getMaximizeButton()
            if maximizeButton is not None and maximizeButton.isPressedState():
                maximizeButton.setPressedState(False)
        return None

    def _handleNcCalcSize(self, msg: MSG) -> tuple[bool, int] | None:
        """Process WM_NCCALCSIZE message for removing standard window frame.

        Parameters
        ----------
        msg : MSG
            Win32 MSG structure pointer.

        Returns
        -------
        tuple of (bool, int)
            (True, result_code) calculation result.
        """
        if msg.wParam:
            rect = cast(msg.lParam, LPNCCALCSIZE_PARAMS).contents.rgrc[0]
        else:
            rect = cast(msg.lParam, LPRECT).contents

        maximized = isMaximized(msg.hWnd)
        fullScreen = isFullScreen(msg.hWnd)

        if maximized and not fullScreen:
            thickness = getResizeBorderThickness(msg.hWnd)
            rect.top += thickness
            rect.left += thickness
            rect.right -= thickness
            rect.bottom -= thickness

        if (maximized or fullScreen) and Taskbar.isAutoHide():
            position = Taskbar.getPosition(msg.hWnd)
            if position == Taskbar.TOP:
                rect.top += Taskbar.AUTO_HIDE_THICKNESS
            elif position == Taskbar.BOTTOM:
                rect.bottom -= Taskbar.AUTO_HIDE_THICKNESS
            elif position == Taskbar.LEFT:
                rect.left += Taskbar.AUTO_HIDE_THICKNESS
            elif position == Taskbar.RIGHT:
                rect.right -= Taskbar.AUTO_HIDE_THICKNESS

        result = 0 if not msg.wParam else win32con.WVR_REDRAW
        return True, result

    def _handleSettingChange(self, msg: MSG) -> tuple[bool, int] | None:
        """Process WM_SETTINGCHANGE message to sync system theme mode if allowed.

        Parameters
        ----------
        msg : MSG
            Win32 MSG structure pointer.

        Returns
        -------
        tuple of (bool, int)
            (True, 0) indicating handled event.
        """
        _ = msg
        if getattr(self._window, "isDetectingThemeAllowed", lambda: False)():
            getattr(self._window, "_setCurrentWindowsTheme", lambda: None)()
        return True, 0

    def _handleStyleChanging(self, msg: MSG) -> tuple[bool, int] | None:
        """Process WM_STYLECHANGING message to update resizable and pressToMove permissions.

        Parameters
        ----------
        msg : MSG
            Win32 MSG structure pointer.

        Returns
        -------
        tuple of (bool, int)
            (True, 0) indicating handled event.
        """
        _ = msg
        isFull = self._window.isFullScreen()
        self.setResizable(not isFull)
        self.setPressToMove(not isFull)
        if hasattr(self._window, "_resizable"):
            self._window._resizable = not isFull
        if hasattr(self._window, "_pressToMove"):
            self._window._pressToMove = not isFull
        return True, 0

    def _handleDpiChanged(self, msg: MSG) -> tuple[bool, int] | None:
        """Process WM_DPICHANGED message to rescale title bar and notify DWM.

        Parameters
        ----------
        msg : MSG
            Win32 MSG structure pointer.

        Returns
        -------
        tuple of (bool, int)
            (True, 0) indicating handled event.
        """
        if self._dpiScalingFlag:
            titleBar = self._getTitleBar()
            if titleBar is not None:
                newDpi = msg.wParam & 0xFFFF
                if newDpi <= 0:
                    newDpi = getDpiForWindow(msg.hWnd)
                titleBar.updateDpiScaling(newDpi)
        win32gui.SetWindowPos(
            msg.hWnd,
            None,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE
            | win32con.SWP_NOSIZE
            | win32con.SWP_NOZORDER
            | win32con.SWP_FRAMECHANGED,
        )
        return True, 0
