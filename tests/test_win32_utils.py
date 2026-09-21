"""Tests for Win32 utility modules in qtframelesskit.native."""


def test_win32_types_import():
    """Verify win32_types structures and enums can be imported."""
    from qtframelesskit.native.win32_types import (
        DWMWINDOWATTRIBUTE,
        LPNCCALCSIZE_PARAMS,
        MARGINS,
        NCCALCSIZE_PARAMS,
        PWINDOWPOS,
    )

    margins = MARGINS(-1, -1, -1, -1)
    assert margins.cxLeftWidth == -1
    assert margins.cyTopHeight == -1
    assert DWMWINDOWATTRIBUTE.DWMWA_USE_IMMERSIVE_DARK_MODE.value == 20
    assert PWINDOWPOS is not None
    assert NCCALCSIZE_PARAMS is not None
    assert LPNCCALCSIZE_PARAMS is not None


def test_win32_utils_import():
    """Verify win32_utils functions and classes can be imported."""
    from qtframelesskit.native.win32_utils import (
        Taskbar,
        findWindow,
        isGreaterEqualWin8_1,
    )

    assert Taskbar.LEFT == 0
    assert Taskbar.TOP == 1
    assert Taskbar.RIGHT == 2
    assert Taskbar.BOTTOM == 3
    assert Taskbar.NO_POSITION == 4
    assert findWindow(0) is None
    assert isinstance(isGreaterEqualWin8_1(), bool)


def test_get_dpi_for_window_modern_api(monkeypatch):
    """Verify getDpiForWindow queries GetDpiForWindow on modern Windows systems.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from qtframelesskit.native.win32_utils import getDpiForWindow

    mockWindowHandle = 12345
    mockDpi = 144
    monkeypatch.setattr(
        "qtframelesskit.native.win32_utils.windll.user32.GetDpiForWindow",
        lambda handle: mockDpi if handle == mockWindowHandle else 0,
        raising=False,
    )

    resolvedDpi = getDpiForWindow(mockWindowHandle)
    assert resolvedDpi == 144


def test_get_dpi_for_window_fallback(monkeypatch):
    """Verify getDpiForWindow falls back to devicePixelRatio or default 96.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from unittest.mock import MagicMock

    from qtframelesskit.native.win32_utils import getDpiForWindow

    mockWindowHandle = 54321
    # Simulate pre-1607 Windows without GetDpiForWindow
    monkeypatch.setattr(
        "qtframelesskit.native.win32_utils.windll.user32.GetDpiForWindow",
        None,
        raising=False,
    )

    mockWindow = MagicMock()
    mockWindow.devicePixelRatio.return_value = 1.5
    monkeypatch.setattr(
        "qtframelesskit.native.win32_utils.findWindow",
        lambda handle: mockWindow if handle == mockWindowHandle else None,
    )

    resolvedDpi = getDpiForWindow(mockWindowHandle)
    assert resolvedDpi == 144

    # Invalid handle falls back to standard 96 DPI
    assert getDpiForWindow(0) == 96


def test_get_system_metrics_for_dpi_modern_api(monkeypatch):
    """Verify getSystemMetricsForDpi queries GetSystemMetricsForDpi when available.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    import win32con

    from qtframelesskit.native.win32_utils import getSystemMetricsForDpi

    def mockGetSystemMetricsForDpi(metricIndex: int, dpiValue: int) -> int:
        if metricIndex == win32con.SM_CXSIZEFRAME and dpiValue == 144:
            return 12
        return 0

    monkeypatch.setattr(
        "qtframelesskit.native.win32_utils.windll.user32.GetSystemMetricsForDpi",
        mockGetSystemMetricsForDpi,
        raising=False,
    )

    metricValue = getSystemMetricsForDpi(win32con.SM_CXSIZEFRAME, 144)
    assert metricValue == 12


def test_get_system_metrics_for_dpi_fallback(monkeypatch):
    """Verify getSystemMetricsForDpi scales standard GetSystemMetrics by DPI factor.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    import win32con

    from qtframelesskit.native.win32_utils import getSystemMetricsForDpi

    # Simulate absence of GetSystemMetricsForDpi
    monkeypatch.setattr(
        "qtframelesskit.native.win32_utils.windll.user32.GetSystemMetricsForDpi",
        None,
        raising=False,
    )
    monkeypatch.setattr(
        "qtframelesskit.native.win32_utils.win32api.GetSystemMetrics",
        lambda metricIndex: 8 if metricIndex == win32con.SM_CXSIZEFRAME else 0,
    )

    # 8 * 144 / 96 = 12
    scaledMetric = getSystemMetricsForDpi(win32con.SM_CXSIZEFRAME, 144)
    assert scaledMetric == 12

    # Standard 96 DPI leaves metric unchanged
    standardMetric = getSystemMetricsForDpi(win32con.SM_CXSIZEFRAME, 96)
    assert standardMetric == 8


def test_get_resize_border_thickness_modern_dpi(monkeypatch):
    """Verify getResizeBorderThickness resolves DPI-scaled frame and padding metrics.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    import win32con

    from qtframelesskit.native.win32_utils import getResizeBorderThickness

    mockWindowHandle = 98765
    monkeypatch.setattr(
        "qtframelesskit.native.win32_utils.getDpiForWindow",
        lambda handle: 144 if handle == mockWindowHandle else 96,
    )

    def mockGetSystemMetricsForDpi(metricIndex: int, dpiValue: int) -> int:
        if dpiValue == 144:
            if metricIndex == win32con.SM_CXSIZEFRAME:
                return 6
            if metricIndex == 92:
                return 6
        return 0

    monkeypatch.setattr(
        "qtframelesskit.native.win32_utils.windll.user32.GetSystemMetricsForDpi",
        mockGetSystemMetricsForDpi,
        raising=False,
    )

    calculatedThickness = getResizeBorderThickness(mockWindowHandle)
    assert calculatedThickness == 12


def test_get_resize_border_thickness_legacy_fallback(monkeypatch):
    """Verify getResizeBorderThickness falls back to standard metrics with devicePixelRatio.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from unittest.mock import MagicMock

    import win32con

    from qtframelesskit.native.win32_utils import getResizeBorderThickness

    mockWindowHandle = 55555
    monkeypatch.setattr(
        "qtframelesskit.native.win32_utils.windll.user32.GetDpiForWindow",
        None,
        raising=False,
    )
    monkeypatch.setattr(
        "qtframelesskit.native.win32_utils.windll.user32.GetSystemMetricsForDpi",
        None,
        raising=False,
    )

    def mockStandardMetrics(metricIndex: int) -> int:
        if metricIndex == win32con.SM_CXSIZEFRAME:
            return 4
        if metricIndex == 92:
            return 4
        return 0

    monkeypatch.setattr(
        "qtframelesskit.native.win32_utils.win32api.GetSystemMetrics",
        mockStandardMetrics,
    )

    mockWindow = MagicMock()
    mockWindow.devicePixelRatio.return_value = 2.0
    monkeypatch.setattr(
        "qtframelesskit.native.win32_utils.findWindow",
        lambda handle: mockWindow if handle == mockWindowHandle else None,
    )

    # (4 + 4) * 2.0 = 16
    calculatedThickness = getResizeBorderThickness(mockWindowHandle)
    assert calculatedThickness == 16


def test_get_resize_border_thickness_zero_metric_and_invalid_handle(monkeypatch):
    """Verify getResizeBorderThickness fallback for zero metrics and invalid window handle.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from unittest.mock import MagicMock

    from qtframelesskit.native.win32_utils import getResizeBorderThickness

    mockWindowHandle = 33333
    monkeypatch.setattr(
        "qtframelesskit.native.win32_utils.windll.user32.GetDpiForWindow",
        None,
        raising=False,
    )
    monkeypatch.setattr(
        "qtframelesskit.native.win32_utils.windll.user32.GetSystemMetricsForDpi",
        None,
        raising=False,
    )
    monkeypatch.setattr(
        "qtframelesskit.native.win32_utils.win32api.GetSystemMetrics",
        lambda metricIndex: 0,
    )

    mockWindow = MagicMock()
    mockWindow.devicePixelRatio.return_value = 1.25
    monkeypatch.setattr(
        "qtframelesskit.native.win32_utils.findWindow",
        lambda handle: mockWindow if handle == mockWindowHandle else None,
    )

    # 8 * 1.25 = 10
    calculatedThickness = getResizeBorderThickness(mockWindowHandle)
    assert calculatedThickness == 10

    # Invalid handle 0 returns 0
    assert getResizeBorderThickness(0) == 0


def test_win32_utils_type_signatures():
    """Verify strict type hints on win32_utils functions.

    Checks parameter and return type annotations for isMaximized,
    isFullScreen, getMonitorInfo, findWindow, and isGreaterEqualVersion.
    """
    import inspect
    from typing import Any

    from qtpy.QtCore import QOperatingSystemVersion
    from qtpy.QtGui import QWindow

    from qtframelesskit.native.win32_utils import (
        findWindow,
        getMonitorInfo,
        isFullScreen,
        isGreaterEqualVersion,
        isMaximized,
    )

    maximizedSignature = inspect.signature(isMaximized)
    assert maximizedSignature.parameters["hWnd"].annotation is int
    assert maximizedSignature.return_annotation is bool

    fullScreenSignature = inspect.signature(isFullScreen)
    assert fullScreenSignature.parameters["hWnd"].annotation is int
    assert fullScreenSignature.return_annotation is bool

    monitorInfoSignature = inspect.signature(getMonitorInfo)
    assert monitorInfoSignature.parameters["hWnd"].annotation is int
    assert monitorInfoSignature.parameters["dwFlags"].annotation is int
    assert monitorInfoSignature.return_annotation == (dict[str, Any] | None)

    findWindowSignature = inspect.signature(findWindow)
    assert findWindowSignature.parameters["hWnd"].annotation is int
    assert findWindowSignature.return_annotation == (QWindow | None)

    versionSignature = inspect.signature(isGreaterEqualVersion)
    assert versionSignature.parameters["version"].annotation is QOperatingSystemVersion
    assert versionSignature.return_annotation is bool


def test_win32_utils_integer_handle_queries():
    """Verify integer handle resolution and graceful fallback for invalid handles.

    Asserts that passing integer handles returns boolean or None without errors.
    """
    from qtframelesskit.native.win32_utils import (
        findWindow,
        getMonitorInfo,
        isFullScreen,
        isMaximized,
    )

    # Invalid handle 0 returns expected falsy defaults
    assert isMaximized(0) is False
    assert isFullScreen(0) is False
    assert findWindow(0) is None
    assert getMonitorInfo(0, 0) is None


def test_find_window_existing_and_non_existing(qtbot):
    """Verify findWindow locates open top-level window by handle and returns None for unknown handle.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    from qtpy.QtWidgets import QWidget

    from qtframelesskit.native.win32_utils import findWindow

    widget = QWidget()
    qtbot.addWidget(widget)
    widget.show()

    windowHandle = widget.windowHandle()
    assert windowHandle is not None
    nativeHandle = int(widget.winId())

    foundWindow = findWindow(nativeHandle)
    assert foundWindow == windowHandle

    # Non-existent handle returns None
    assert findWindow(99999999) is None
