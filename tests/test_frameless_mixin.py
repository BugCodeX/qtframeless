"""Unit tests for FramelessWindowMixin DPI scaling and native event handling.

Verifies WM_NCHITTEST boundary scaling across arbitrary display DPI values
and WM_DPICHANGED interception, frame synchronization, and title bar scaling.
"""

import ctypes
from ctypes.wintypes import MSG, RECT
from unittest.mock import MagicMock

import win32con
from qtpy.QtCore import QByteArray, QPoint
from qtpy.QtWidgets import QWidget

from qtframeless.core.frameless_mixin import FramelessWindowMixin
from qtframeless.native.win32_types import WM_DPICHANGED


class DummyFramelessWidget(FramelessWindowMixin, QWidget):
    """Test widget combining FramelessWindowMixin and QWidget."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._initVal()
        self._initUi()


def test_frameless_mixin_nc_hit_test_scaled_dpi(qtbot, monkeypatch):
    """Verify WM_NCHITTEST adapts resize hit testing to scaled DPI border width.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)
    widget.setGeometry(100, 100, 200, 200)
    widget.show()

    # 192 DPI (2.0x scale -> scaled border width = round(5 * 192 / 96) = 10 px)
    monkeypatch.setattr(
        "qtframeless.core.frameless_mixin.getDpiForWindow",
        lambda hWnd: 192,
    )

    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = win32con.WM_NCHITTEST
    messagePointer = ctypes.addressof(syntheticMessage)

    # Relative x = 7 is inside 10px scaled left border
    scaledLeftPoint = QPoint(107, 200)
    monkeypatch.setattr(
        "qtframeless.core.frameless_mixin.QCursor.pos",
        staticmethod(lambda: scaledLeftPoint),
    )
    eventHandled, hitCode = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert eventHandled is True
    assert hitCode == win32con.HTLEFT

    # Relative x = 12 is outside 10px border, falls through to client area
    clientPoint = QPoint(112, 200)
    monkeypatch.setattr(
        "qtframeless.core.frameless_mixin.QCursor.pos",
        staticmethod(lambda: clientPoint),
    )
    eventHandled, _ = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert eventHandled is False


def test_frameless_mixin_dpi_changed_event_processing(qtbot, monkeypatch):
    """Verify WM_DPICHANGED triggers title bar scaling and frame sync without overriding bounds.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)
    widget.show()

    titleBar = widget.getTitleBar()
    assert titleBar is not None
    mockUpdateDpiScaling = MagicMock()
    monkeypatch.setattr(titleBar, "updateDpiScaling", mockUpdateDpiScaling)

    recordedSetWindowPosCalls = []
    monkeypatch.setattr(
        "win32gui.SetWindowPos",
        lambda *args: recordedSetWindowPosCalls.append(args),
    )

    suggestedRect = RECT(100, 100, 600, 500)
    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = WM_DPICHANGED
    # DPI 144 in LOWORD
    syntheticMessage.wParam = (144 << 16) | 144
    syntheticMessage.lParam = ctypes.addressof(suggestedRect)
    messagePointer = ctypes.addressof(syntheticMessage)

    eventHandled, resultCode = widget.nativeEvent(
        QByteArray(b"windows_generic_MSG"), messagePointer
    )
    assert eventHandled is True
    assert resultCode == 0

    # TitleBar DPI scaling was triggered with new DPI
    mockUpdateDpiScaling.assert_called_once_with(144)

    # SetWindowPos was called with SWP_FRAMECHANGED and no position/size overrides
    assert len(recordedSetWindowPosCalls) == 1
    callArgs = recordedSetWindowPosCalls[0]
    assert callArgs[0] == int(widget.winId())
    flags = callArgs[6]
    expectedFlags = (
        win32con.SWP_NOMOVE
        | win32con.SWP_NOSIZE
        | win32con.SWP_NOZORDER
        | win32con.SWP_FRAMECHANGED
    )
    assert flags & expectedFlags == expectedFlags


def test_frameless_mixin_allow_dpi_scaling_toggle(qtbot, monkeypatch):
    """Verify allowDpiScaling toggle enables and suppresses title bar DPI scaling.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)
    widget.show()

    # Enabled by default
    assert widget.isDpiScalingAllowed() is True

    titleBar = widget.getTitleBar()
    assert titleBar is not None
    mockUpdateDpiScaling = MagicMock()
    monkeypatch.setattr(titleBar, "updateDpiScaling", mockUpdateDpiScaling)

    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = WM_DPICHANGED
    syntheticMessage.wParam = (144 << 16) | 144
    messagePointer = ctypes.addressof(syntheticMessage)

    # Disable DPI scaling
    widget.allowDpiScaling(False)
    assert widget.isDpiScalingAllowed() is False
    # Switching to False resets TitleBar to base 96 DPI
    mockUpdateDpiScaling.assert_called_with(96)
    mockUpdateDpiScaling.reset_mock()

    # When disabled, WM_DPICHANGED does NOT update title bar
    widget.nativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    mockUpdateDpiScaling.assert_not_called()

    # Re-enable DPI scaling
    widget.allowDpiScaling(True)
    assert widget.isDpiScalingAllowed() is True
    widget.nativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    mockUpdateDpiScaling.assert_called_once_with(144)


def test_frameless_mixin_signals_and_properties_state_change(qtbot):
    """Verify signals emit on state changes and properties reflect updated values.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    from qtpy.QtGui import QColor

    from qtframeless.native.win32_types import WindowCornerPreference

    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    # resizable & resizableChanged
    with qtbot.waitSignal(widget.resizableChanged, timeout=1000) as blocker:
        widget.resizable = False
    assert blocker.args == [False]
    assert widget.isResizable() is False
    assert widget.resizable is False

    # pressToMove & pressToMoveChanged
    with qtbot.waitSignal(widget.pressToMoveChanged, timeout=1000) as blocker:
        widget.pressToMove = False
    assert blocker.args == [False]
    assert widget.isPressToMove() is False
    assert widget.pressToMove is False

    # dpiScalingAllowed & dpiScalingAllowedChanged
    with qtbot.waitSignal(widget.dpiScalingAllowedChanged, timeout=1000) as blocker:
        widget.dpiScalingAllowed = False
    assert blocker.args == [False]
    assert widget.isDpiScalingAllowed() is False
    assert widget.dpiScalingAllowed is False

    # detectingThemeAllowed & detectingThemeAllowedChanged
    with qtbot.waitSignal(widget.detectingThemeAllowedChanged, timeout=1000) as blocker:
        widget.detectingThemeAllowed = False
    assert blocker.args == [False]
    assert widget.isDetectingThemeAllowed() is False
    assert widget.detectingThemeAllowed is False

    # darkTheme & darkThemeChanged
    with qtbot.waitSignal(widget.darkThemeChanged, timeout=1000) as blocker:
        widget.darkTheme = True
    assert blocker.args == [True]
    assert widget.isDarkTheme() is True
    assert widget.darkTheme is True

    # windowCornerPreference & windowCornerPreferenceChanged
    with qtbot.waitSignal(widget.windowCornerPreferenceChanged, timeout=1000) as blocker:
        widget.windowCornerPreference = WindowCornerPreference.ROUND
    assert blocker.args == [WindowCornerPreference.ROUND]
    assert widget.getWindowCornerPreference() == WindowCornerPreference.ROUND
    assert widget.windowCornerPreference == WindowCornerPreference.ROUND

    # borderColor & borderColorChanged
    testColor = QColor(255, 0, 0)
    with qtbot.waitSignal(widget.borderColorChanged, timeout=1000) as blocker:
        widget.borderColor = testColor
    assert blocker.args == [testColor]
    assert widget.getBorderColor() == testColor
    assert widget.borderColor == testColor


def test_frameless_mixin_signals_suppressed_on_unchanged_state(qtbot):
    """Verify notification signals are suppressed when setters are called with unchanged state.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    from qtframeless.native.win32_types import WindowCornerPreference

    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    resizableSignals = []
    widget.resizableChanged.connect(resizableSignals.append)
    widget.setResizable(True)
    assert resizableSignals == []

    pressSignals = []
    widget.pressToMoveChanged.connect(pressSignals.append)
    widget.setPressToMove(True)
    assert pressSignals == []

    dpiSignals = []
    widget.dpiScalingAllowedChanged.connect(dpiSignals.append)
    widget.allowDpiScaling(True)
    assert dpiSignals == []

    detectThemeSignals = []
    widget.detectingThemeAllowedChanged.connect(detectThemeSignals.append)
    widget.allowDetectingTheme(True)
    assert detectThemeSignals == []

    darkSignals = []
    widget.darkThemeChanged.connect(darkSignals.append)
    widget.setDarkTheme(widget.isDarkTheme())
    assert darkSignals == []

    cornerSignals = []
    widget.windowCornerPreferenceChanged.connect(cornerSignals.append)
    widget.setWindowCornerPreference(WindowCornerPreference.DEFAULT)
    assert cornerSignals == []

    borderSignals = []
    widget.borderColorChanged.connect(borderSignals.append)
    widget.setBorderColor(None)
    assert borderSignals == []


def test_frameless_mixin_qt_property_reflection(qtbot):
    """Verify dynamic Qt property reflection via property() and setProperty().

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    from qtpy.QtGui import QColor

    from qtframeless.native.win32_types import WindowCornerPreference

    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    # Initial default reflections
    assert widget.property("darkTheme") is False
    assert widget.property("resizable") is True
    assert widget.property("pressToMove") is True
    assert widget.property("dpiScalingAllowed") is True
    assert widget.property("detectingThemeAllowed") is True
    assert widget.property("windowCornerPreference") == WindowCornerPreference.DEFAULT
    assert widget.property("borderColor") is None

    # Reflection after setProperty
    widget.setProperty("resizable", False)
    assert widget.property("resizable") is False
    assert widget.isResizable() is False

    widget.setProperty("pressToMove", False)
    assert widget.property("pressToMove") is False
    assert widget.isPressToMove() is False

    widget.setProperty("darkTheme", True)
    assert widget.property("darkTheme") is True
    assert widget.isDarkTheme() is True

    widget.setProperty("dpiScalingAllowed", False)
    assert widget.property("dpiScalingAllowed") is False
    assert widget.isDpiScalingAllowed() is False

    widget.setProperty("detectingThemeAllowed", False)
    assert widget.property("detectingThemeAllowed") is False
    assert widget.isDetectingThemeAllowed() is False

    widget.setProperty("windowCornerPreference", WindowCornerPreference.ROUND)
    assert widget.property("windowCornerPreference") == WindowCornerPreference.ROUND

    testColor = QColor(0, 120, 215)
    widget.borderColor = testColor
    assert widget.property("borderColor") == testColor


def test_frameless_mixin_dark_theme_palette_sync(qtbot):
    """Verify setDarkTheme synchronizes QPalette color roles for window content.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    from qtpy.QtGui import QPalette

    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    # Initially or after toggling to dark theme
    with qtbot.waitSignal(widget.darkThemeChanged, timeout=1000):
        widget.setDarkTheme(True)

    darkPalette = widget.palette()
    assert darkPalette.color(QPalette.ColorRole.Window).name().lower() == "#202020"
    assert darkPalette.color(QPalette.ColorRole.WindowText).name().lower() == "#ffffff"
    assert darkPalette.color(QPalette.ColorRole.Base).name().lower() == "#191919"
    assert darkPalette.color(QPalette.ColorRole.Text).name().lower() == "#ffffff"

    # Switching back to light theme restores light palette roles
    with qtbot.waitSignal(widget.darkThemeChanged, timeout=1000):
        widget.setDarkTheme(False)

    lightPalette = widget.palette()
    assert lightPalette.color(QPalette.ColorRole.Window).name().lower() == "#f3f3f3"
    assert lightPalette.color(QPalette.ColorRole.WindowText).name().lower() == "#000000"
    assert lightPalette.color(QPalette.ColorRole.Text).name().lower() == "#000000"

