"""DWM and Win32 effect helpers for frameless windows.

Wraps ``DwmExtendFrameIntoClientArea``, ``DwmSetWindowAttribute``, and
``SetWindowLong`` to apply drop shadows, window animations, and dark-mode
title bar chrome to a frameless Qt window.
"""

from ctypes import addressof, byref, c_int, c_uint, sizeof, windll
from ctypes.wintypes import BOOL

import win32con
import win32gui

from .win32_types import (
    ACCENT_FLAG_ACRYLIC,
    ACCENT_POLICY,
    ACCENT_STATE,
    DWM_BB_ENABLE,
    DWM_BLURBEHIND,
    DWM_SYSTEMBACKDROP_TYPE,
    DWMSBT_MAINWINDOW,
    DWMSBT_TABBEDWINDOW,
    DWMWA_COLOR_DEFAULT,
    DWMWA_COLOR_NONE,
    DWMWA_MICA_EFFECT,
    DWMWA_SYSTEMBACKDROP_TYPE,
    DWMWINDOWATTRIBUTE,
    MARGINS,
    WCA_ACCENT_POLICY,
    WINDOWCOMPOSITIONATTRIBDATA,
    WindowCornerPreference,
    colorToColorRef,
)
from .win32_utils import (
    isGreaterEqualWin10_17063,
    isGreaterEqualWin11,
    isGreaterEqualWin11_22H2,
)

# Direct exports for convenience
__all__ = [
    "DWMSBT_MAINWINDOW",
    "DWMSBT_TABBEDWINDOW",
    "DWMWA_COLOR_DEFAULT",
    "DWMWA_COLOR_NONE",
    "DWMWA_MICA_EFFECT",
    "DWMWA_SYSTEMBACKDROP_TYPE",
    "WindowsEffectHelper",
    "_parseGradientColor",
]


class WindowsEffectHelper:
    """Apply DWM visual effects to a native Win32 window handle.

    Loads ``user32`` and ``dwmapi`` at construction time and caches the
    relevant function pointers so every call avoids repeated DLL lookups.
    """

    def __init__(self):
        # user32 and dwmapi must be loaded explicitly; windll attributes are
        # lazy proxies that can't be cached as plain callables.
        user32 = windll.LoadLibrary("user32")
        dwmapi = windll.LoadLibrary("dwmapi")

        self.__windowCompositionAttribute = user32.SetWindowCompositionAttribute
        self.__dwmExtendFrameIntoClientArea = dwmapi.DwmExtendFrameIntoClientArea
        self.__dwmSetWindowAttribute = dwmapi.DwmSetWindowAttribute
        self.__dwmEnableBlurBehindWindow = dwmapi.DwmEnableBlurBehindWindow

    def setBasicEffect(self, hWnd, hint, extendFrame: bool = True):
        """Enable DWM shadow and configure window style flags from ``hint``.

        ``MARGINS(-1, -1, -1, -1)`` extends the DWM frame into the entire
        client area, which is what produces the drop shadow on a borderless
        window without actually drawing a glass frame.

        ``WS_CAPTION`` is always set because Windows requires it for window
        animations (open/close/minimize) and snap layout support to work;
        the native caption bar is never actually visible on a frameless window.

        Parameters
        ----------
        hWnd : int or ctypes handle
            Native window handle, accepts Qt's ``winId()`` return value directly.
        hint : list of str
            Title-bar button keys (``"min"``, ``"max"``, ``"close"``) that
            determine which ``WS_*`` style flags are applied.
        extendFrame : bool, optional
            Whether to extend the DWM glass frame into the client area. Defaults to True.
        """
        hWnd = int(hWnd)
        # All-(-1) margins tell DWM to extend the frame into the whole client
        # area — the only way to get a real drop shadow without a native frame.
        if extendFrame:
            margins = MARGINS(-1, -1, -1, -1)
            self.__dwmExtendFrameIntoClientArea(hWnd, byref(margins))
        # WS_CAPTION is mandatory for animations and snap layouts even though
        # the caption bar itself is hidden by the frameless flag.
        dwNewLong = win32con.WS_CAPTION
        if "close" in hint and len(hint) == 1:
            pass
        else:
            if "min" in hint:
                dwNewLong |= win32con.WS_MINIMIZEBOX
            # WS_THICKFRAME enables resizing; CS_DBLCLKS enables the
            # double-click-to-maximize behavior at the OS level.
            if "max" in hint:
                dwNewLong |= win32con.CS_DBLCLKS | win32con.WS_THICKFRAME | win32con.WS_MAXIMIZEBOX
        win32gui.SetWindowLong(hWnd, win32con.GWL_STYLE, dwNewLong)

    def setDarkTheme(self, hWnd, dark: bool) -> bool:
        """Toggle immersive dark mode on the DWM non-client area.

        Calls ``DwmSetWindowAttribute`` with
        ``DWMWA_USE_IMMERSIVE_DARK_MODE`` (value 20) to switch the OS-drawn
        title bar chrome between light and dark. Has no effect on the Qt
        client area — that must be styled separately.

        Parameters
        ----------
        hWnd : int or ctypes handle
            Native window handle.
        dark : bool
            ``True`` to enable dark mode, ``False`` to restore light mode.

        Returns
        -------
        bool
            ``True`` if applied successfully, ``False`` otherwise.
        """
        try:
            result = self.__dwmSetWindowAttribute(
                int(hWnd),
                DWMWINDOWATTRIBUTE.DWMWA_USE_IMMERSIVE_DARK_MODE.value,
                byref(BOOL(dark)),
                sizeof(BOOL),
            )
            return result == 0
        except OSError:
            return False

    def setWindowCornerPreference(
        self, hWnd: int, preference: WindowCornerPreference | int
    ) -> bool:
        """Configure Windows 11 window corner rounding preference.

        Invokes ``DwmSetWindowAttribute`` with ``DWMWA_WINDOW_CORNER_PREFERENCE`` (33)
        on Windows 11 (build 22000) or later.

        Parameters
        ----------
        hWnd : int or ctypes handle
            Native window handle.
        preference : WindowCornerPreference or int
            Target corner rounding preference.

        Returns
        -------
        bool
            ``True`` if applied successfully, ``False`` otherwise.
        """
        if not isGreaterEqualWin11():
            return False

        value = (
            preference.value if isinstance(preference, WindowCornerPreference) else int(preference)
        )
        try:
            result = self.__dwmSetWindowAttribute(
                int(hWnd),
                DWMWINDOWATTRIBUTE.DWMWA_WINDOW_CORNER_PREFERENCE.value,
                byref(c_int(value)),
                sizeof(c_int),
            )
            return result == 0
        except OSError:
            return False

    def setBorderColor(self, hWnd: int, color: object) -> bool:
        """Configure Windows 11 window border color.

        Invokes ``DwmSetWindowAttribute`` with ``DWMWA_BORDER_COLOR`` (34)
        on Windows 11 (build 22000) or later.

        Parameters
        ----------
        hWnd : int or ctypes handle
            Native window handle.
        color : QColor or str
            Color to set on the border.

        Returns
        -------
        bool
            ``True`` if applied successfully, ``False`` otherwise.
        """
        if not isGreaterEqualWin11():
            return False

        colorRef = colorToColorRef(color)
        try:
            result = self.__dwmSetWindowAttribute(
                int(hWnd),
                DWMWINDOWATTRIBUTE.DWMWA_BORDER_COLOR.value,
                byref(c_int(colorRef)),
                sizeof(c_int),
            )
            return result == 0
        except OSError:
            return False

    def setCaptionColor(self, hWnd: int, color: object) -> bool:
        """Configure Windows 11 window title bar caption color.

        Invokes ``DwmSetWindowAttribute`` with ``DWMWA_CAPTION_COLOR`` (35)
        on Windows 11 (build 22000) or later. Passing ``None`` or ``DWMWA_COLOR_NONE``
        (``0xFFFFFFFE``) removes the native caption background color completely,
        allowing backdrop materials (Mica, Mica Alt, Acrylic) to show through.

        Parameters
        ----------
        hWnd : int or ctypes handle
            Native window handle.
        color : object
            Target caption color. Accepts ``DWMWA_COLOR_NONE`` (``0xFFFFFFFE``),
            ``None`` (treated as ``DWMWA_COLOR_NONE``), ``DWMWA_COLOR_DEFAULT``
            (``0xFFFFFFFF``), integer COLORREF/ARGB, hex string, or QColor.

        Returns
        -------
        bool
            ``True`` if applied successfully, ``False`` otherwise.
        """
        if not isGreaterEqualWin11():
            return False

        if color is None or color == DWMWA_COLOR_NONE:
            value = DWMWA_COLOR_NONE
        elif color == DWMWA_COLOR_DEFAULT:
            value = DWMWA_COLOR_DEFAULT
        else:
            value = colorToColorRef(color)

        try:
            result = self.__dwmSetWindowAttribute(
                int(hWnd),
                DWMWINDOWATTRIBUTE.DWMWA_CAPTION_COLOR.value,
                byref(c_uint(value)),
                sizeof(c_uint),
            )
            return result == 0
        except OSError:
            return False

    def setMicaEffect(self, hWnd: int, isAlt: bool = False) -> bool:
        """Enable native Mica or Mica Alt backdrop material on Windows 11.

        Invokes ``DwmSetWindowAttribute`` with ``DWMWA_SYSTEMBACKDROP_TYPE`` (38)
        on Windows 11 Build 22621 or newer, or falls back to ``DWMWA_MICA_EFFECT`` (1029)
        on Windows 11 Build 22000. Returns ``False`` on older platforms without raising exceptions.

        Parameters
        ----------
        hWnd : int or ctypes handle
            Native window handle.
        isAlt : bool, optional
            ``True`` to apply Mica Alt (tabbed window backdrop), ``False`` for standard Mica.
            Defaults to ``False``.

        Returns
        -------
        bool
            ``True`` if applied successfully, ``False`` otherwise.
        """
        if isGreaterEqualWin11_22H2():
            targetBackdrop = (
                DWM_SYSTEMBACKDROP_TYPE.TABBEDWINDOW.value
                if isAlt
                else DWM_SYSTEMBACKDROP_TYPE.MAINWINDOW.value
            )
            try:
                result = self.__dwmSetWindowAttribute(
                    int(hWnd),
                    DWMWINDOWATTRIBUTE.DWMWA_SYSTEMBACKDROP_TYPE.value,
                    byref(c_int(targetBackdrop)),
                    sizeof(c_int),
                )
                if result == 0:
                    self.setCaptionColor(hWnd, DWMWA_COLOR_NONE)
                    return True
                return False
            except OSError:
                return False
        elif isGreaterEqualWin11():
            try:
                result = self.__dwmSetWindowAttribute(
                    int(hWnd),
                    DWMWINDOWATTRIBUTE.DWMWA_MICA_EFFECT.value,
                    byref(c_int(1)),
                    sizeof(c_int),
                )
                if result == 0:
                    self.setCaptionColor(hWnd, DWMWA_COLOR_NONE)
                    return True
                return False
            except OSError:
                return False
        return False

    def enableBlurBehindWindow(self, hWnd: int) -> bool:
        """Enable desktop window manager blur behind for native Acrylic rendering.

        Parameters
        ----------
        hWnd : int or ctypes handle
            Native window handle.

        Returns
        -------
        bool
            True if applied successfully, False otherwise.
        """
        blurBehind = DWM_BLURBEHIND()
        blurBehind.dwFlags = DWM_BB_ENABLE
        blurBehind.fEnable = True
        blurBehind.hRgnBlur = None
        blurBehind.fTransitionOnMaximized = False
        try:
            result = self.__dwmEnableBlurBehindWindow(int(hWnd), byref(blurBehind))
            return result == 0
        except OSError:
            return False

    def setAcrylicEffect(self, hWnd: int, gradientColor: str | int | None = None) -> bool:
        """Enable native Fluent Acrylic blur-behind material on Windows 10/11.

        Invokes ``SetWindowCompositionAttribute`` with ``ACCENT_ENABLE_ACRYLICBLURBEHIND``
        and the specified gradient color tint on Windows 10 Build 17063 or newer.

        Parameters
        ----------
        hWnd : int or ctypes handle
            Native window handle.
        gradientColor : str, int, or None, optional
            Gradient tint color in integer (0xAABBGGRR), hex string, or None for default tint.
            Defaults to ``0x99222222``.

        Returns
        -------
        bool
            ``True`` if applied successfully, ``False`` otherwise.
        """
        if not isGreaterEqualWin10_17063():
            return False

        self.enableBlurBehindWindow(hWnd)

        parsedColor = _parseGradientColor(gradientColor)
        policy = ACCENT_POLICY()
        policy.AccentState = ACCENT_STATE.ACCENT_ENABLE_ACRYLICBLURBEHIND.value
        policy.AccentFlags = ACCENT_FLAG_ACRYLIC
        policy.GradientColor = parsedColor
        policy.AnimationId = 0

        attribData = WINDOWCOMPOSITIONATTRIBDATA()
        attribData.Attrib = WCA_ACCENT_POLICY
        attribData.pvData = addressof(policy)
        attribData.cbData = sizeof(policy)

        try:
            result = self.__windowCompositionAttribute(int(hWnd), byref(attribData))
            if result and isGreaterEqualWin11():
                self.setCaptionColor(hWnd, DWMWA_COLOR_NONE)
            return bool(result)
        except OSError:
            return False

    def refreshBackgroundBlurEffect(
        self, hWnd: int, gradientColor: str | int | None = None
    ) -> bool:
        """Reapply native Acrylic blur-behind composition after window state change.

        Parameters
        ----------
        hWnd : int or ctypes handle
            Native window handle.
        gradientColor : str, int, or None, optional
            Gradient tint color.

        Returns
        -------
        bool
            True if refreshed successfully, False otherwise.
        """
        return self.setAcrylicEffect(hWnd, gradientColor)

    def clearAcrylicEffect(self, hWnd: int) -> bool:
        """Clear native Acrylic blur-behind material on Windows 10/11.

        Parameters
        ----------
        hWnd : int or ctypes handle
            Native window handle.

        Returns
        -------
        bool
            ``True`` if cleared successfully, ``False`` otherwise.
        """
        if not isGreaterEqualWin10_17063():
            return False

        policy = ACCENT_POLICY()
        policy.AccentState = ACCENT_STATE.ACCENT_DISABLED.value
        policy.AccentFlags = 0
        policy.GradientColor = 0
        policy.AnimationId = 0

        attribData = WINDOWCOMPOSITIONATTRIBDATA()
        attribData.Attrib = WCA_ACCENT_POLICY
        attribData.pvData = addressof(policy)
        attribData.cbData = sizeof(policy)

        try:
            result = self.__windowCompositionAttribute(int(hWnd), byref(attribData))
            return bool(result)
        except OSError:
            return False

    def removeBackdropEffect(self, hWnd: int) -> bool:
        """Remove any active backdrop material (Mica, Mica Alt, or Acrylic).

        Resets DWM system backdrop attribute on Windows 11 and disables
        composition accent policy on Windows 10/11.

        Parameters
        ----------
        hWnd : int or ctypes handle
            Native window handle.

        Returns
        -------
        bool
            ``True`` if backdrop effects were reset successfully, ``False`` otherwise.
        """
        success = True
        if isGreaterEqualWin11_22H2():
            try:
                result = self.__dwmSetWindowAttribute(
                    int(hWnd),
                    DWMWINDOWATTRIBUTE.DWMWA_SYSTEMBACKDROP_TYPE.value,
                    byref(c_int(DWM_SYSTEMBACKDROP_TYPE.NONE.value)),
                    sizeof(c_int),
                )
                if result != 0:
                    success = False
            except OSError:
                success = False
        elif isGreaterEqualWin11():
            try:
                result = self.__dwmSetWindowAttribute(
                    int(hWnd),
                    DWMWINDOWATTRIBUTE.DWMWA_MICA_EFFECT.value,
                    byref(c_int(0)),
                    sizeof(c_int),
                )
                if result != 0:
                    success = False
            except OSError:
                success = False

        if isGreaterEqualWin10_17063():
            acrylicCleared = self.clearAcrylicEffect(hWnd)
            if not acrylicCleared:
                success = False

        if isGreaterEqualWin11():
            self.setCaptionColor(hWnd, DWMWA_COLOR_DEFAULT)

        return success


def _parseGradientColor(gradientColor: object) -> int:
    """Parse gradient color parameter into a Win32 ABGR integer.

    Parameters
    ----------
    gradientColor : object
        Color representation to convert: int, hex string, QColor, or None.

    Returns
    -------
    int
        ABGR integer format (0xAABBGGRR). Defaults to 0x99F2F2F2 if None or invalid.
    """
    if gradientColor is None:
        return 0x99F2F2F2
    if isinstance(gradientColor, int):
        return gradientColor
    if isinstance(gradientColor, str):
        colorString = gradientColor.strip()
        if colorString.startswith(("0x", "0X")):
            try:
                return int(colorString, 16)
            except ValueError:
                return 0x99F2F2F2
        cleanHex = colorString.lstrip("#")
        if len(cleanHex) == 8:
            try:
                reversedHex = "".join(cleanHex[i : i + 2] for i in range(6, -1, -2))
                return int(reversedHex, 16)
            except ValueError:
                return 0x99F2F2F2
        elif len(cleanHex) == 6:
            try:
                reversedHex = "99" + cleanHex[4:6] + cleanHex[2:4] + cleanHex[0:2]
                return int(reversedHex, 16)
            except ValueError:
                return 0x99F2F2F2

    from qtpy.QtGui import QColor

    if isinstance(gradientColor, QColor) and gradientColor.isValid():
        return (
            gradientColor.red()
            | (gradientColor.green() << 8)
            | (gradientColor.blue() << 16)
            | (gradientColor.alpha() << 24)
        )

    return 0x99F2F2F2
