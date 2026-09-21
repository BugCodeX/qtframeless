"""Win32 utility helpers for frameless window behavior on Windows.

Wraps low-level Win32 API calls for window state detection (maximized,
full-screen), resize border measurement, monitor resolution, and taskbar
auto-hide/position queries.
"""

from ctypes import Structure, byref, sizeof, windll
from ctypes.wintypes import DWORD, HWND, LPARAM, RECT, UINT
from typing import Any

import win32api
import win32con
import win32gui
from qtpy.QtCore import QOperatingSystemVersion
from qtpy.QtGui import QGuiApplication, QWindow
from win32comext.shell import shellcon


def isMaximized(hWnd: int) -> bool:
    """Return whether the window identified by ``hWnd`` is maximized.

    Parameters
    ----------
    hWnd : int
        Native window handle.

    Returns
    -------
    bool
        ``True`` when the window placement shows ``SW_MAXIMIZE``.
    """
    if not hWnd:
        return False
    try:
        windowPlacement = win32gui.GetWindowPlacement(hWnd)
    except Exception:
        return False
    if not windowPlacement:
        return False

    return windowPlacement[1] == win32con.SW_MAXIMIZE


def isFullScreen(hWnd: int) -> bool:
    """Return whether the window covers the entire primary monitor area.

    Compares the window rect against the monitor rect reported by Win32;
    does not rely on any Qt window-state flag.

    Parameters
    ----------
    hWnd : int
        Native window handle.

    Returns
    -------
    bool
        ``True`` when the window rect exactly matches the monitor rect.
    """
    if not hWnd:
        return False
    try:
        winRect = win32gui.GetWindowRect(hWnd)
    except Exception:
        return False
    if not winRect:
        return False
    monitorInfo = getMonitorInfo(hWnd, win32con.MONITOR_DEFAULTTOPRIMARY)
    if not monitorInfo:
        return False
    monitorRect = monitorInfo["Monitor"]
    return all(i == j for i, j in zip(winRect, monitorRect, strict=False))


def getMonitorInfo(hWnd: int, dwFlags: int) -> dict[str, Any] | None:
    """Return the monitor info dict for the monitor containing ``hWnd``.

    Parameters
    ----------
    hWnd : int
        Native window handle.
    dwFlags : int
        ``MONITOR_DEFAULTTO*`` flag controlling fallback behavior when the
        window is not on any monitor.

    Returns
    -------
    dict or None
        Win32 monitor-info mapping, or ``None`` when no monitor is found.
    """
    if not hWnd:
        return None
    try:
        monitor = win32api.MonitorFromWindow(hWnd, dwFlags)
    except Exception:
        return None
    if not monitor:
        return None

    return dict(win32api.GetMonitorInfo(monitor))


def getDpiForWindow(windowHandle: int) -> int:
    """Return the dots-per-inch (DPI) scaling factor for the specified window.

    Queries ``GetDpiForWindow`` on Windows 10 build 1607 or newer. Falls back
    to Qt ``devicePixelRatio`` scaling or 96 DPI when the native API is
    unavailable.

    Parameters
    ----------
    windowHandle : int
        Native window handle.

    Returns
    -------
    int
        Active DPI value (e.g. 96 for 100%, 144 for 150%, 192 for 200%).
    """
    if not windowHandle:
        return 96

    getDpiFunction = getattr(windll.user32, "GetDpiForWindow", None)
    if callable(getDpiFunction):
        try:
            dpi = int(getDpiFunction(windowHandle))
            if dpi > 0:
                return dpi
        except (AttributeError, OSError, TypeError):
            pass

    window = findWindow(windowHandle)
    if window is not None:
        try:
            return round(96 * window.devicePixelRatio())
        except (AttributeError, TypeError):
            pass

    return 96


def getSystemMetricsForDpi(metricIndex: int, dpiValue: int) -> int:
    """Return system metric scaled for the specified DPI value.

    Queries ``GetSystemMetricsForDpi`` on Windows 10 build 1607 or newer.
    Falls back to standard ``GetSystemMetrics`` scaled proportionally by
    ``dpiValue / 96`` when the native API is unavailable.

    Parameters
    ----------
    metricIndex : int
        Win32 system metric index (e.g. ``SM_CXSIZEFRAME``).
    dpiValue : int
        Dots-per-inch value to scale metric for.

    Returns
    -------
    int
        Scaled system metric in physical pixels.
    """
    getSystemMetricsFunction = getattr(windll.user32, "GetSystemMetricsForDpi", None)
    if callable(getSystemMetricsFunction):
        try:
            metric = int(getSystemMetricsFunction(metricIndex, dpiValue))
            if metric > 0:
                return metric
        except (AttributeError, OSError, TypeError):
            pass

    try:
        standardMetric = win32api.GetSystemMetrics(metricIndex)
        if standardMetric > 0:
            if dpiValue != 96:
                return round(standardMetric * dpiValue / 96)
            return standardMetric
    except Exception:
        pass

    return 0


def getResizeBorderThickness(windowHandle: int) -> int:
    """Return the resize border thickness for ``windowHandle`` in physical pixels.

    Resolves resize border thickness via ``GetSystemMetricsForDpi`` using
    ``GetDpiForWindow`` on modern Windows systems. Falls back to standard
    ``GetSystemMetrics`` scaled by ``devicePixelRatio`` when per-monitor
    DPI APIs are unavailable.

    Parameters
    ----------
    windowHandle : int
        Native window handle.

    Returns
    -------
    int
        Border thickness in physical pixels, or ``0`` when the window
        cannot be found or handle is invalid.
    """
    if not windowHandle:
        return 0

    window = findWindow(windowHandle)

    # Modern per-monitor DPI resolution path
    getDpiFunction = getattr(windll.user32, "GetDpiForWindow", None)
    getSystemMetricsFunction = getattr(windll.user32, "GetSystemMetricsForDpi", None)

    if callable(getDpiFunction) and callable(getSystemMetricsFunction):
        try:
            dpi = getDpiForWindow(windowHandle)
            if dpi > 0:
                frameThickness = getSystemMetricsForDpi(win32con.SM_CXSIZEFRAME, dpi)
                paddedBorderThickness = getSystemMetricsForDpi(92, dpi)  # SM_CXPADDEDBORDER = 92
                totalThickness = frameThickness + paddedBorderThickness
                if totalThickness > 0:
                    return totalThickness
        except (AttributeError, OSError, TypeError):
            pass

    # Legacy system metric path
    try:
        frameThickness = win32api.GetSystemMetrics(win32con.SM_CXSIZEFRAME)
        paddedBorderThickness = win32api.GetSystemMetrics(92)
        totalThickness = frameThickness + paddedBorderThickness
    except Exception:
        totalThickness = 0

    ratio = window.devicePixelRatio() if window is not None else 1.0
    if totalThickness > 0:
        return round(totalThickness * ratio)

    # Fallback default thickness (8 logical pixels) scaled by ratio
    defaultLogicalThickness = 8
    return round(defaultLogicalThickness * ratio)


def findWindow(hWnd: int) -> QWindow | None:
    """Find the Qt top-level window whose native handle matches ``hWnd``.

    Parameters
    ----------
    hWnd : int
        Native window handle to look up.

    Returns
    -------
    QWindow or None
        The matching Qt window, or ``None`` when not found.
    """
    if not hWnd:
        return None

    windows = QGuiApplication.topLevelWindows()
    if not windows:
        return None

    for window in windows:
        if window and int(window.winId()) == hWnd:
            return window

    return None


def isGreaterEqualVersion(version: QOperatingSystemVersion) -> bool:
    """Return whether the current OS version is at least ``version``.

    Parameters
    ----------
    version : QOperatingSystemVersion
        Operating system version threshold to compare against.

    Returns
    -------
    bool
        True if host OS meets or exceeds the version threshold.
    """
    return QOperatingSystemVersion.current() >= version


def isGreaterEqualWin8_1():
    """Return whether the current OS is Windows 8.1 or later."""
    return isGreaterEqualVersion(QOperatingSystemVersion.Windows8_1)


def isGreaterEqualWin11() -> bool:
    """Return whether the current OS is Windows 11 (build >= 22000) or later."""
    import sys

    if sys.platform != "win32":
        return False
    try:
        return sys.getwindowsversion().build >= 22000
    except (AttributeError, OSError):
        return False


def isGreaterEqualWin11_22H2() -> bool:
    """Return whether the current OS is Windows 11 Build 22621 (22H2) or later.

    Returns
    -------
    bool
        True if the host OS build is at least 22621, False otherwise.
    """
    import sys

    if sys.platform != "win32":
        return False
    try:
        return sys.getwindowsversion().build >= 22621
    except (AttributeError, OSError):
        return False


def isGreaterEqualWin10_17063() -> bool:
    """Return whether the current OS is Windows 10 Build 17063 or later.

    Returns
    -------
    bool
        True if the host OS build is at least 17063, False otherwise.
    """
    import sys

    if sys.platform != "win32":
        return False
    try:
        return sys.getwindowsversion().build >= 17063
    except (AttributeError, OSError):
        return False


class APPBARDATA(Structure):
    """ctypes mirror of the Win32 ``APPBARDATA`` structure.

    Used with ``SHAppBarMessage`` to query taskbar state and position.
    """

    _fields_ = [
        ("cbSize", DWORD),
        ("hWnd", HWND),
        ("uCallbackMessage", UINT),
        ("uEdge", UINT),
        ("rc", RECT),
        ("lParam", LPARAM),
    ]


class Taskbar:
    """Helpers for querying the Windows taskbar state and screen-edge position.

    Attributes
    ----------
    LEFT, TOP, RIGHT, BOTTOM : int
        Edge constants matching ``ABE_*`` values used by ``SHAppBarMessage``.
    NO_POSITION : int
        Sentinel returned when the taskbar position cannot be determined.
    AUTO_HIDE_THICKNESS : int
        Pixels the taskbar reserves when in auto-hide mode (always 2).
    """

    LEFT = 0
    TOP = 1
    RIGHT = 2
    BOTTOM = 3
    NO_POSITION = 4

    AUTO_HIDE_THICKNESS = 2

    @staticmethod
    def isAutoHide():
        """Return whether the taskbar is set to auto-hide."""
        appbarData = APPBARDATA(sizeof(APPBARDATA), 0, 0, 0, RECT(0, 0, 0, 0), 0)
        taskbarState = windll.shell32.SHAppBarMessage(shellcon.ABM_GETSTATE, byref(appbarData))

        return taskbarState == shellcon.ABS_AUTOHIDE

    @classmethod
    def getPosition(cls, hWnd):
        """Return the screen edge where the taskbar is docked.

        On Windows 8.1+, uses ``ABM_GETAUTOHIDEBAREX`` per-monitor.
        On older systems, falls back to ``Shell_TrayWnd`` and
        ``ABM_GETTASKBARPOS`` on the primary monitor.

        Parameters
        ----------
        hWnd : int
            Native handle of the window whose monitor is checked.

        Returns
        -------
        int
            One of ``LEFT``, ``TOP``, ``RIGHT``, ``BOTTOM``, or
            ``NO_POSITION`` when the taskbar cannot be located.
        """
        if isGreaterEqualWin8_1():
            monitorInfo = getMonitorInfo(hWnd, win32con.MONITOR_DEFAULTTONEAREST)
            if not monitorInfo:
                return cls.NO_POSITION

            monitor = RECT(*monitorInfo["Monitor"])
            appbarData = APPBARDATA(sizeof(APPBARDATA), 0, 0, 0, monitor, 0)
            positions = [cls.LEFT, cls.TOP, cls.RIGHT, cls.BOTTOM]
            for position in positions:
                appbarData.uEdge = position
                if windll.shell32.SHAppBarMessage(11, byref(appbarData)):
                    return position

            return cls.NO_POSITION

        appbarData = APPBARDATA(
            sizeof(APPBARDATA),
            win32gui.FindWindow("Shell_TrayWnd", None),
            0,
            0,
            RECT(0, 0, 0, 0),
            0,
        )
        if appbarData.hWnd:
            windowMonitor = win32api.MonitorFromWindow(hWnd, win32con.MONITOR_DEFAULTTONEAREST)
            if not windowMonitor:
                return cls.NO_POSITION

            taskbarMonitor = win32api.MonitorFromWindow(
                appbarData.hWnd, win32con.MONITOR_DEFAULTTOPRIMARY
            )
            if not taskbarMonitor:
                return cls.NO_POSITION

            if taskbarMonitor == windowMonitor:
                windll.shell32.SHAppBarMessage(shellcon.ABM_GETTASKBARPOS, byref(appbarData))
                return appbarData.uEdge

        return cls.NO_POSITION
