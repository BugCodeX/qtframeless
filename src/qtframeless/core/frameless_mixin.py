"""Unified FramelessWindowMixin providing native Win32 messages and DWM shadows.

Encapsulates non-client calculations, border resize hit testing, theme detection,
and drag-to-move delegation without duplicating code across concrete Qt window types.
"""

from ctypes import byref, cast, sizeof, windll  # noqa: F401
from ctypes.wintypes import LPRECT, MSG  # noqa: F401
from typing import cast as typeCast

import win32con
import win32gui
from qtpy.QtCore import Property, QByteArray, QPoint, QRect, Qt, Signal  # noqa: F401
from qtpy.QtGui import QColor, QCursor, QIcon, QMouseEvent, QPalette  # noqa: F401
from qtpy.QtWidgets import QWidget

from qtframeless.core.frame_controller import WindowFrameController
from qtframeless.core.theme import ThemeController
from qtframeless.native.win32_types import (  # noqa: F401
    LPNCCALCSIZE_PARAMS,
    TME_LEAVE,
    TME_NONCLIENT,
    TRACKMOUSEEVENT,
    WM_DPICHANGED,
    WM_NCMOUSELEAVE,
    WindowCornerPreference,
)
from qtframeless.native.win32_utils import (  # noqa: F401
    Taskbar,
    getDpiForWindow,
    getResizeBorderThickness,
    isFullScreen,
    isMaximized,
)
from qtframeless.native.window_effect import WindowsEffectHelper
from qtframeless.windows.title_bar import TitleBar


class FramelessWindowMixin:
    """Core mixin handling Win32 native events, DWM shadows, and frameless behavior.

    Encapsulates non-client window management, native border resizing, title bar
    synchronization, and Windows 11 styling extensions for Qt top-level windows.

    Attributes
    ----------
    darkThemeChanged : Signal(bool)
        Emitted when window dark theme state is toggled.
    changedToDark : Signal(bool)
        Backward-compatible legacy alias for ``darkThemeChanged``.
    resizableChanged : Signal(bool)
        Emitted when window resizability state changes.
    pressToMoveChanged : Signal(bool)
        Emitted when press-to-move dragging permission is toggled.
    dpiScalingAllowedChanged : Signal(bool)
        Emitted when automatic DPI scaling permission is toggled.
    detectingThemeAllowedChanged : Signal(bool)
        Emitted when automatic theme detection permission is toggled.
    windowCornerPreferenceChanged : Signal(object)
        Emitted when Windows 11 corner rounding preference changes.
    borderColorChanged : Signal(object)
        Emitted when native window border color customization changes.
    darkTheme : Property(bool)
        Qt property reflecting and setting window dark theme state.
    resizable : Property(bool)
        Qt property reflecting and setting window resizability.
    pressToMove : Property(bool)
        Qt property reflecting and setting press-to-move dragging permission.
    dpiScalingAllowed : Property(bool)
        Qt property reflecting and setting automatic DPI scaling permission.
    detectingThemeAllowed : Property(bool)
        Qt property reflecting and setting automatic theme detection permission.
    windowCornerPreference : Property(object)
        Qt property reflecting and setting Windows 11 corner rounding preference.
    borderColor : Property(object)
        Qt property reflecting and setting native window border color.
    """

    darkThemeChanged = Signal(bool)
    changedToDark = darkThemeChanged
    resizableChanged = Signal(bool)
    pressToMoveChanged = Signal(bool)
    dpiScalingAllowedChanged = Signal(bool)
    detectingThemeAllowedChanged = Signal(bool)
    windowCornerPreferenceChanged = Signal(object)
    borderColorChanged = Signal(object)
    captionColorChanged = Signal(object)

    def _isMaterialBackdrop(self) -> bool:
        """Return whether the window uses a material backdrop effect.

        Returns
        -------
        bool
            True for material backdrop windows, False for standard opaque windows.
        """
        return False

    def _initVal(self) -> None:
        """Initialize state variables for frameless window movement and sizing."""
        if not hasattr(self, "_pressToMove"):
            self._pressToMove = True
        if not hasattr(self, "_resizable"):
            self._resizable = True
        if not hasattr(self, "_borderWidth"):
            self._borderWidth = 5
            self._border_width = 5
        if not hasattr(self, "_dpiScalingFlag"):
            self._dpiScalingFlag = True
        if not hasattr(self, "_frameController"):
            self._frameController = WindowFrameController(
                typeCast(QWidget, self),
                borderWidth=self._borderWidth,
                resizable=self._resizable,
                pressToMove=self._pressToMove,
                dpiScaling=self._dpiScalingFlag,
            )
        if not hasattr(self, "_windowCornerPreference"):
            self._windowCornerPreference = WindowCornerPreference.DEFAULT
        if not hasattr(self, "_borderColor"):
            self._borderColor = None
        if not hasattr(self, "_captionColor"):
            self._captionColor = None
        if not hasattr(self, "_windowEffect"):
            self._windowEffect = WindowsEffectHelper()
        if not hasattr(self, "_titleBar"):
            self._titleBar: TitleBar | None = None
        if not hasattr(self, "_themeController"):
            self._themeController = ThemeController(self, isMaterial=self._isMaterialBackdrop())
            self._themeController.darkThemeChanged.connect(self.darkThemeChanged)
            self._themeController.detectingThemeAllowedChanged.connect(
                self.detectingThemeAllowedChanged
            )

    def _shouldExtendFrame(self) -> bool:
        """Return whether to extend DWM glass frame to create native drop shadow.

        Returns
        -------
        bool
            True to extend frame with MARGINS(-1, -1, -1, -1), False to omit.
        """
        return True

    def _initUi(self, hint: list[str] | None = None, flags: list | None = None) -> None:
        """Configure frameless window flags, DWM drop shadows, and custom title bar.

        Parameters
        ----------
        hint : list of str, optional
            Control button hints to display on the title bar.
        flags : list, optional
            Additional Qt window flags to apply.
        """
        if hint is None:
            hint = ["min", "max", "close"]
        if flags is None:
            flags = []

        self._windowEffect = WindowsEffectHelper()

        # Remove standard window border, keeping FramelessWindowHint
        newFlags = self.windowFlags() | Qt.WindowType.FramelessWindowHint
        for flag in flags:
            newFlags |= flag
        self.setWindowFlags(newFlags)

        # Apply native DWM drop shadow and window animation effects
        self._windowEffect.setBasicEffect(
            int(self.winId()), hint, extendFrame=self._shouldExtendFrame()
        )

        windowHandle = self.windowHandle()
        if windowHandle:
            windowHandle.screenChanged.connect(self._onScreenChanged)

        self.setPalette(self._createThemePalette(self.isDarkTheme()))

        if self._titleBar is None:
            self._titleBar = TitleBar(self, hint)
        else:
            self._titleBar.setTitleBarHint(hint)

        self._setCurrentWindowsTheme()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press event, delegating window dragging when press-to-move is active.

        Parameters
        ----------
        event : QMouseEvent
            Mouse press event.
        """
        if event.button() == Qt.MouseButton.LeftButton and self._pressToMove:
            self._startSystemMove()
        super().mousePressEvent(event)

    def _startSystemMove(self) -> None:
        """Start native system window drag via startSystemMove."""
        self._frameController.startSystemMove()

    _move = _startSystemMove

    def isPressToMove(self) -> bool:
        """Return whether pressing and dragging the window body moves it.

        Returns
        -------
        bool
            True if pressing to move is enabled.
        """
        return self._frameController.isPressToMove()

    def setPressToMove(self, enabled: bool) -> None:
        """Enable or disable dragging the window by pressing its body.

        Parameters
        ----------
        enabled : bool
            True to enable press-to-move dragging.
        """
        if self.isPressToMove() == enabled:
            return
        self._frameController.setPressToMove(enabled)
        self._pressToMove = enabled
        if hasattr(self, "_titleBar") and self._titleBar:
            self._titleBar.setPressToMove(enabled)
        self.pressToMoveChanged.emit(enabled)

    def _setCurrentWindowsTheme(self) -> None:
        """Detect Windows application theme from registry and apply title bar chrome effect."""
        self._themeController.syncWithSystemTheme(force=True)

    def _createThemePalette(self, isDark: bool) -> QPalette:
        """Create and return a QPalette configured for dark or light theme mode.

        Parameters
        ----------
        isDark : bool
            True to generate a dark theme palette, False for light theme.

        Returns
        -------
        QPalette
            Configured window palette instance.
        """
        return self._themeController.createThemePalette(isDark)

    def setDarkTheme(self, isDark: bool, force: bool = False) -> None:
        """Manually toggle dark theme on the DWM window chrome and title bar.

        Parameters
        ----------
        isDark : bool
            True to apply dark mode, False for light mode.
        force : bool, optional
            True to force re-applying theme even if isDark matches current state.
            Defaults to False.
        """
        self._themeController.setDarkTheme(isDark, force=force)

    def isDarkTheme(self) -> bool:
        """Return whether dark theme is currently applied to the window.

        Returns
        -------
        bool
            True if dark theme is active, False otherwise.
        """
        return self._themeController.isDarkTheme()

    def isDetectingThemeAllowed(self) -> bool:
        """Return whether automatic theme detection on setting changes is allowed.

        Returns
        -------
        bool
            True if automatic detection is active.
        """
        return self._themeController.isDetectingThemeAllowed()

    def allowDetectingTheme(self, allow: bool) -> None:
        """Enable or disable automatic theme detection on Windows setting changes.

        Parameters
        ----------
        allow : bool
            True to allow theme detection on setting change.
        """
        self._themeController.setDetectingThemeAllowed(allow)

    def isDpiScalingAllowed(self) -> bool:
        """Return whether automatic title bar and chrome DPI scaling is allowed.

        Returns
        -------
        bool
            True if automatic DPI scaling is enabled.
        """
        return self._frameController.isDpiScalingAllowed()

    def allowDpiScaling(self, allow: bool) -> None:
        """Enable or disable automatic title bar and chrome DPI scaling.

        When disabled, the title bar retains its base layout and dimensions
        across monitor DPI changes, while native window frame geometry
        synchronization remains preserved.

        Parameters
        ----------
        allow : bool
            True to enable automatic DPI scaling, False to freeze base dimensions.
        """
        if self.isDpiScalingAllowed() == allow:
            return
        self._frameController.setDpiScalingAllowed(allow)
        self._dpiScalingFlag = allow
        if not allow and hasattr(self, "_titleBar") and self._titleBar:
            self._titleBar.updateDpiScaling(96)
        self.dpiScalingAllowedChanged.emit(allow)

    def isResizable(self) -> bool:
        """Return whether the frameless window can be resized.

        Returns
        -------
        bool
            True if resizing is allowed.
        """
        return self._frameController.isResizable()

    def setResizable(self, resizable: bool) -> None:
        """Set whether the window is resizable and update title bar maximize button.

        Parameters
        ----------
        resizable : bool
            True to allow resizing and maximize controls.
        """
        if self.isResizable() == resizable:
            return
        self._frameController.setResizable(resizable)
        self._resizable = resizable
        if hasattr(self, "_titleBar") and self._titleBar:
            self._titleBar.setBaseWindowResizable(resizable)
        self.resizableChanged.emit(resizable)

    def nativeEvent(self, eventType: QByteArray | bytes, message: int) -> tuple[bool, int]:
        """Process native Win32 messages for sizing and hit testing.

        Parameters
        ----------
        eventType : QByteArray or bytes
            Type of the native event.
        message : int
            Pointer address to the native Win32 MSG struct.

        Returns
        -------
        tuple of (bool, int)
            Handling status and result code.
        """
        result = self._frameController.handleNativeEvent(eventType, message)
        if result is not None:
            return result

        if isinstance(eventType, (bytes, bytearray, memoryview)):
            eventType = QByteArray(bytes(eventType))
        try:
            return super().nativeEvent(eventType, message)
        except (ValueError, TypeError):
            try:
                import shiboken6

                if isinstance(message, int):
                    return super().nativeEvent(eventType, shiboken6.VoidPtr(message))
            except Exception:
                pass
            return False, 0

    def _onScreenChanged(self) -> None:
        """Trigger frame change notification when window changes screen display."""
        windowHandle = self.windowHandle()
        if windowHandle:
            hWnd = int(windowHandle.winId())
            win32gui.SetWindowPos(
                hWnd,
                None,
                0,
                0,
                0,
                0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED,
            )

    def setWindowIcon(self, icon: QIcon | str) -> None:
        """Set window icon on both Qt window and custom title bar.

        Parameters
        ----------
        icon : QIcon or str
            Icon instance or path to the icon image file.
        """
        if isinstance(icon, str):
            iconObject = QIcon()
            iconObject.addFile(icon)
        else:
            iconObject = icon
        if self._titleBar:
            self._titleBar.setIcon(iconObject)
        super().setWindowIcon(iconObject)

    def setWindowTitle(self, title: str) -> None:
        """Set window title text on both Qt window and custom title bar.

        Parameters
        ----------
        title : str
            Title string to display.
        """
        super().setWindowTitle(title)
        if self._titleBar:
            self._titleBar.setTitle(title)

    def setTitleBarVisible(self, isVisible: bool) -> None:
        """Toggle title bar visibility and adapt press-to-move accordingly.

        Parameters
        ----------
        isVisible : bool
            True to show the title bar, False to hide it.
        """
        if self._titleBar:
            self._titleBar.setVisible(isVisible)
            if self.isPressToMove() or self._titleBar.isPressToMove():
                self._titleBar.setPressToMove(isVisible)
                self.setPressToMove(not isVisible)

    def setTitleBarHint(self, hint: list[str]) -> None:
        """Configure button hints displayed on the title bar.

        Parameters
        ----------
        hint : list of str
            List of button keys ('min', 'max', 'close', 'full_screen').
        """
        if self._titleBar:
            self._titleBar.setTitleBarHint(hint)

    def getTitleBar(self) -> TitleBar | None:
        """Return the custom title bar instance.

        Returns
        -------
        TitleBar or None
            The custom title bar widget.
        """
        return self._titleBar

    def setFixedSize(self, width: int, height: int) -> None:
        """Set fixed window dimensions and disable resize behavior.

        Parameters
        ----------
        width : int
            Fixed width in pixels.
        height : int
            Fixed height in pixels.
        """
        super().setFixedSize(width, height)
        self.setResizable(False)

    def getWindowCornerPreference(self) -> WindowCornerPreference:
        """Return the current Windows 11 window corner rounding preference.

        Returns
        -------
        WindowCornerPreference
            Active window corner preference enum member.
        """
        return self._windowCornerPreference

    def setWindowCornerPreference(self, preference: WindowCornerPreference | int) -> bool:
        """Configure Windows 11 window corner rounding preference.

        Parameters
        ----------
        preference : WindowCornerPreference or int
            Target corner rounding preference.

        Returns
        -------
        bool
            True if corner preference was successfully applied by DWM, False otherwise.
        """
        if isinstance(preference, int):
            try:
                targetPref = WindowCornerPreference(preference)
            except ValueError:
                return False
        else:
            targetPref = preference

        previousPref = getattr(self, "_windowCornerPreference", WindowCornerPreference.DEFAULT)
        if previousPref == targetPref:
            return True

        if not hasattr(self, "_windowEffect"):
            self._windowEffect = WindowsEffectHelper()

        success = self._windowEffect.setWindowCornerPreference(int(self.winId()), targetPref)
        if success:
            self._windowCornerPreference = targetPref
            self.windowCornerPreferenceChanged.emit(targetPref)
            return True
        return False

    def getBorderColor(self) -> QColor | None:
        """Return the current customized window border color, if set.

        Returns
        -------
        QColor or None
            Active custom border color, or None if default.
        """
        return self._borderColor

    def setBorderColor(self, color: QColor | str | None) -> bool:
        """Customize native window border color on Windows 11.

        Parameters
        ----------
        color : QColor, str, or None
            Qt color, hexadecimal string (e.g. ``#FF0000``), or None for default.

        Returns
        -------
        bool
            True if border color was successfully applied by DWM, False otherwise.
        """
        if isinstance(color, str):
            parsedColor = QColor(color)
            targetColor = parsedColor if parsedColor.isValid() else None
        elif isinstance(color, QColor):
            targetColor = color if color.isValid() else None
        else:
            targetColor = None

        previousColor = getattr(self, "_borderColor", None)
        if previousColor == targetColor:
            return True

        if not hasattr(self, "_windowEffect"):
            self._windowEffect = WindowsEffectHelper()

        success = self._windowEffect.setBorderColor(int(self.winId()), color)
        if success:
            self._borderColor = targetColor
            self.borderColorChanged.emit(targetColor)
            return True
        return False

    def getCaptionColor(self) -> QColor | int | None:
        """Return the current customized window title bar caption color, if set.

        Returns
        -------
        QColor, int, or None
            Active custom caption color, or None if default.
        """
        return self._captionColor

    def setCaptionColor(self, color: QColor | str | int | None) -> bool:
        """Customize native window title bar caption color on Windows 11.

        Parameters
        ----------
        color : QColor, str, int, or None
            Target caption color. Accepts ``DWMWA_COLOR_NONE`` (``0xFFFFFFFE``),
            ``None`` (for transparent material backdrop), ``DWMWA_COLOR_DEFAULT``
            (``0xFFFFFFFF``), hex string, or QColor.

        Returns
        -------
        bool
            True if caption color was successfully applied by DWM, False otherwise.
        """
        if isinstance(color, str):
            parsedColor = QColor(color)
            targetColor = parsedColor if parsedColor.isValid() else None
        elif isinstance(color, QColor):
            targetColor = color if color.isValid() else None
        elif isinstance(color, int):
            targetColor = color
        else:
            targetColor = None

        previousColor = getattr(self, "_captionColor", None)
        if previousColor == targetColor:
            return True

        if not hasattr(self, "_windowEffect"):
            self._windowEffect = WindowsEffectHelper()

        success = self._windowEffect.setCaptionColor(int(self.winId()), color)
        if success:
            self._captionColor = targetColor
            self.captionColorChanged.emit(targetColor)
            return True
        return False

    darkTheme = Property(
        bool,
        isDarkTheme,
        setDarkTheme,
        notify=darkThemeChanged,
        doc="Active dark theme state.",
    )
    resizable = Property(
        bool,
        isResizable,
        setResizable,
        notify=resizableChanged,
        doc="Window resizability state.",
    )
    pressToMove = Property(
        bool,
        isPressToMove,
        setPressToMove,
        notify=pressToMoveChanged,
        doc="Press-to-move dragging state.",
    )
    dpiScalingAllowed = Property(
        bool,
        isDpiScalingAllowed,
        allowDpiScaling,
        notify=dpiScalingAllowedChanged,
        doc="Automatic DPI scaling state.",
    )
    detectingThemeAllowed = Property(
        bool,
        isDetectingThemeAllowed,
        allowDetectingTheme,
        notify=detectingThemeAllowedChanged,
        doc="Automatic theme detection state.",
    )
    windowCornerPreference = Property(
        object,
        getWindowCornerPreference,
        setWindowCornerPreference,
        notify=windowCornerPreferenceChanged,
        doc="Windows 11 corner rounding preference.",
    )
    borderColor = Property(
        object,
        getBorderColor,
        setBorderColor,
        notify=borderColorChanged,
        doc="Native window border color.",
    )
    captionColor = Property(
        object,
        getCaptionColor,
        setCaptionColor,
        notify=captionColorChanged,
        doc="Native window caption color.",
    )


def __getattr__(name: str) -> object:
    """Provide backwards-compatible module attributes for winreg constants and functions."""
    if name in ("HKEY_CURRENT_USER", "KEY_READ", "OpenKey", "QueryValueEx"):
        import qtframeless.core.theme as themeModule

        return getattr(themeModule, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
