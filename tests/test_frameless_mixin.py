"""Unit tests for FramelessWindowMixin DPI scaling, native event handling, and window lifecycle.

Verifies WM_NCHITTEST boundary scaling across arbitrary display DPI values,
WM_DPICHANGED interception, frame synchronization, title bar scaling,
theme detection, and native Win32 window message calculations.
"""

import ctypes
from ctypes.wintypes import MSG, RECT
from unittest.mock import MagicMock

import win32con
from qtpy.QtCore import QByteArray, QPoint, Qt
from qtpy.QtGui import QColor, QFont, QIcon, QMouseEvent, QPalette, QPixmap
from qtpy.QtWidgets import QWidget

from qtframeless.core.frameless_mixin import FramelessWindowMixin
from qtframeless.native.win32_types import (
    NCCALCSIZE_PARAMS,
    WM_DPICHANGED,
    WindowCornerPreference,
)
from qtframeless.native.win32_types import (
    RECT as WIN32_RECT,
)
from qtframeless.native.win32_utils import Taskbar


class DummyFramelessWidget(FramelessWindowMixin, QWidget):
    """Test widget combining FramelessWindowMixin and QWidget.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Optional parent widget.
    """

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
        "qtframeless.core.frame_controller.getDpiForWindow",
        lambda hWnd: 192,
    )

    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = win32con.WM_NCHITTEST
    messagePointer = ctypes.addressof(syntheticMessage)

    # Relative x = 7 is inside 10px scaled left border
    scaledLeftPoint = QPoint(107, 200)
    monkeypatch.setattr(
        "qtframeless.core.frame_controller.QCursor.pos",
        staticmethod(lambda: scaledLeftPoint),
    )
    eventHandled, hitCode = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert eventHandled is True
    assert hitCode == win32con.HTLEFT

    # Relative x = 12 is outside 10px border, falls through to client area
    clientPoint = QPoint(112, 200)
    monkeypatch.setattr(
        "qtframeless.core.frame_controller.QCursor.pos",
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
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    # resizable & resizableChanged
    with qtbot.waitSignal(widget.resizableChanged, timeout=1000) as signalBlocker:
        widget.resizable = False
    assert signalBlocker.args == [False]
    assert widget.isResizable() is False
    assert widget.resizable is False

    # pressToMove & pressToMoveChanged
    with qtbot.waitSignal(widget.pressToMoveChanged, timeout=1000) as signalBlocker:
        widget.pressToMove = False
    assert signalBlocker.args == [False]
    assert widget.isPressToMove() is False
    assert widget.pressToMove is False

    # dpiScalingAllowed & dpiScalingAllowedChanged
    with qtbot.waitSignal(widget.dpiScalingAllowedChanged, timeout=1000) as signalBlocker:
        widget.dpiScalingAllowed = False
    assert signalBlocker.args == [False]
    assert widget.isDpiScalingAllowed() is False
    assert widget.dpiScalingAllowed is False

    # detectingThemeAllowed & detectingThemeAllowedChanged
    with qtbot.waitSignal(widget.detectingThemeAllowedChanged, timeout=1000) as signalBlocker:
        widget.detectingThemeAllowed = False
    assert signalBlocker.args == [False]
    assert widget.isDetectingThemeAllowed() is False
    assert widget.detectingThemeAllowed is False

    # darkTheme & darkThemeChanged
    with qtbot.waitSignal(widget.darkThemeChanged, timeout=1000) as signalBlocker:
        widget.darkTheme = True
    assert signalBlocker.args == [True]
    assert widget.isDarkTheme() is True
    assert widget.darkTheme is True

    # windowCornerPreference & windowCornerPreferenceChanged
    with qtbot.waitSignal(widget.windowCornerPreferenceChanged, timeout=1000) as signalBlocker:
        widget.windowCornerPreference = WindowCornerPreference.ROUND
    assert signalBlocker.args == [WindowCornerPreference.ROUND]
    assert widget.getWindowCornerPreference() == WindowCornerPreference.ROUND
    assert widget.windowCornerPreference == WindowCornerPreference.ROUND

    # borderColor & borderColorChanged
    testColor = QColor(255, 0, 0)
    with qtbot.waitSignal(widget.borderColorChanged, timeout=1000) as signalBlocker:
        widget.borderColor = testColor
    assert signalBlocker.args == [testColor]
    assert widget.getBorderColor() == testColor
    assert widget.borderColor == testColor


def test_frameless_mixin_signals_suppressed_on_unchanged_state(qtbot):
    """Verify notification signals are suppressed when setters are called with unchanged state.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
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


def test_frameless_mixin_initialization(qtbot):
    """Verify FramelessWindowMixin initializes window flags and title bar.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    assert bool(widget.windowFlags() & Qt.WindowType.FramelessWindowHint)
    assert widget.getTitleBar() is not None
    assert widget.isPressToMove() is True
    assert widget.isResizable() is True


def test_frameless_mixin_fixed_size_disables_resizable(qtbot):
    """Verify setFixedSize disables resizability on mixin.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    assert widget.isResizable() is True
    widget.setFixedSize(400, 300)
    assert widget.isResizable() is False


def test_frameless_mixin_theme_detection_and_signal(qtbot):
    """Verify theme detection emits darkThemeChanged signal.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.darkThemeChanged, timeout=1000) as signalBlocker:
        widget._setCurrentWindowsTheme()
    assert signalBlocker.signal_triggered
    assert isinstance(signalBlocker.args[0], bool)


def test_frameless_mixin_light_theme_detection(qtbot, monkeypatch):
    """Verify light theme detection when registry returns AppsUseLightTheme=1.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    monkeypatch.setattr(
        "qtframeless.core.theme.OpenKey",
        lambda *args, **kwargs: MagicMock(),
    )
    monkeypatch.setattr(
        "qtframeless.core.theme.QueryValueEx",
        lambda *args, **kwargs: (1, 4),
    )

    with qtbot.waitSignal(widget.darkThemeChanged, timeout=1000) as signalBlocker:
        widget._setCurrentWindowsTheme()
    assert signalBlocker.signal_triggered
    assert signalBlocker.args == [False]


def test_frameless_mixin_dark_theme_detection(qtbot, monkeypatch):
    """Verify dark theme detection when registry returns AppsUseLightTheme=0.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    monkeypatch.setattr(
        "qtframeless.core.theme.OpenKey",
        lambda *args, **kwargs: MagicMock(),
    )
    monkeypatch.setattr(
        "qtframeless.core.theme.QueryValueEx",
        lambda *args, **kwargs: (0, 4),
    )

    with qtbot.waitSignal(widget.darkThemeChanged, timeout=1000) as signalBlocker:
        widget._setCurrentWindowsTheme()
    assert signalBlocker.signal_triggered
    assert signalBlocker.args == [True]


def test_frameless_mixin_dark_theme_manual_override(qtbot):
    """Verify setDarkTheme updates theme state without errors.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    widget.setDarkTheme(True)
    assert widget.isDarkTheme() is True
    widget.setDarkTheme(False)
    assert widget.isDarkTheme() is False


def test_frameless_mixin_title_and_icon_delegation(qtbot):
    """Verify setWindowTitle, setTitleBarFont, and setTitleBarVisible update title bar state.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    titleBar = widget.getTitleBar()
    assert titleBar is not None

    widget.setWindowTitle("Mixin Title Test")
    assert titleBar.getTitle().text() == "Mixin Title Test"

    customFont = QFont("Arial", 12)
    titleBar.setTitleBarFont(customFont)
    assert titleBar.getTitle().font().family() == "Arial"

    widget.setTitleBarVisible(False)
    assert titleBar.isHidden()
    assert widget.isPressToMove() is True

    widget.setTitleBarVisible(True)
    assert not titleBar.isHidden()


def test_frameless_mixin_icon_and_hints_delegation(qtbot):
    """Verify setWindowIcon and setTitleBarHint propagate to TitleBar.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    testPixmap = QPixmap(16, 16)
    testPixmap.fill(QColor("red"))
    testIcon = QIcon(testPixmap)

    widget.setWindowIcon(testIcon)
    assert not widget.getTitleBar().getIcon().pixmap().isNull()

    widget.setTitleBarHint(["min", "close"])
    buttons = widget.getTitleBar().getButtons()
    assert not buttons["min"].isHidden()
    assert not buttons["close"].isHidden()
    assert buttons["max"].isHidden()


def test_frameless_mixin_theme_detection_toggle(qtbot):
    """Verify allowDetectingTheme and isDetectingThemeAllowed state toggling.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    assert widget.isDetectingThemeAllowed() is True
    widget.allowDetectingTheme(False)
    assert widget.isDetectingThemeAllowed() is False
    widget.allowDetectingTheme(True)
    assert widget.isDetectingThemeAllowed() is True


def test_frameless_mixin_screen_changed(qtbot, monkeypatch):
    """Verify _onScreenChanged triggers win32gui.SetWindowPos with SWP_FRAMECHANGED.

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

    recordedCalls = []
    monkeypatch.setattr(
        "win32gui.SetWindowPos",
        lambda *args: recordedCalls.append(args),
    )

    widget._onScreenChanged()
    assert len(recordedCalls) == 1
    windowHandle = widget.windowHandle()
    assert windowHandle is not None
    assert recordedCalls[0][0] == int(windowHandle.winId())
    assert bool(recordedCalls[0][6] & win32con.SWP_FRAMECHANGED)


def test_frameless_mixin_mouse_press_system_move_delegation(qtbot, monkeypatch):
    """Verify window movement is delegated to _startSystemMove on left mouse press.

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

    moveCallCount = 0

    def recordSystemMove():
        nonlocal moveCallCount
        moveCallCount += 1

    monkeypatch.setattr(widget, "_startSystemMove", recordSystemMove)

    recordedMouseEvents = []
    originalMousePressEvent = widget.mousePressEvent

    def recordMousePress(event: QMouseEvent):
        recordedMouseEvents.append(event)
        originalMousePressEvent(event)

    monkeypatch.setattr(widget, "mousePressEvent", recordMousePress)

    # Left click with pressToMove enabled triggers _startSystemMove
    assert widget.isPressToMove() is True
    qtbot.mousePress(widget, Qt.MouseButton.LeftButton)
    assert moveCallCount == 1
    assert len(recordedMouseEvents) == 1
    assert isinstance(recordedMouseEvents[0], QMouseEvent)

    # Right click does not trigger _startSystemMove
    qtbot.mousePress(widget, Qt.MouseButton.RightButton)
    assert moveCallCount == 1

    # Disabling pressToMove prevents _startSystemMove on left click
    widget.setPressToMove(False)
    assert widget.isPressToMove() is False
    qtbot.mousePress(widget, Qt.MouseButton.LeftButton)
    assert moveCallCount == 1


def test_frameless_mixin_native_event_nc_hit_test(qtbot, monkeypatch):
    """Verify WM_NCHITTEST hit-testing for corners, edges, center, and fixed size.

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

    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = win32con.WM_NCHITTEST
    messagePointer = ctypes.addressof(syntheticMessage)

    # Geometry is (100, 100, 200, 200), border width is 5
    # Relative coordinates: left=0..4, right=195..199, top=0..4, bottom=195..199
    hitTestCases = [
        ("top_left", QPoint(100, 100), win32con.HTTOPLEFT),
        ("top_right", QPoint(299, 100), win32con.HTTOPRIGHT),
        ("bottom_left", QPoint(100, 299), win32con.HTBOTTOMLEFT),
        ("bottom_right", QPoint(299, 299), win32con.HTBOTTOMRIGHT),
        ("top_edge", QPoint(200, 100), win32con.HTTOP),
        ("bottom_edge", QPoint(200, 299), win32con.HTBOTTOM),
        ("left_edge", QPoint(100, 200), win32con.HTLEFT),
        ("right_edge", QPoint(299, 200), win32con.HTRIGHT),
    ]

    for caseName, cursorPosition, expectedHitCode in hitTestCases:
        monkeypatch.setattr(
            "qtframeless.core.frame_controller.QCursor.pos",
            staticmethod(lambda pos=cursorPosition: pos),
        )
        eventHandled, hitCode = widget.nativeEvent(
            QByteArray(b"windows_generic_MSG"), messagePointer
        )
        assert eventHandled is True, f"Failed handling for {caseName}"
        assert hitCode == expectedHitCode, (
            f"Incorrect hit code for {caseName}: {hitCode} != {expectedHitCode}"
        )

    # Center (client area) falls through
    centerPosition = QPoint(200, 200)
    monkeypatch.setattr(
        "qtframeless.core.frame_controller.QCursor.pos",
        staticmethod(lambda: centerPosition),
    )
    eventHandled, _ = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert eventHandled is False

    # When window is not resizable, border hits fall through
    widget.setResizable(False)
    topEdgePosition = QPoint(200, 100)
    monkeypatch.setattr(
        "qtframeless.core.frame_controller.QCursor.pos",
        staticmethod(lambda: topEdgePosition),
    )
    eventHandled, _ = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert eventHandled is False


def test_frameless_mixin_native_event_nc_calc_size_wparam_true(qtbot, monkeypatch):
    """Verify WM_NCCALCSIZE client rect calculation when wParam is non-zero.

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

    calcParams = NCCALCSIZE_PARAMS()
    calcParams.rgrc[0].left = 0
    calcParams.rgrc[0].top = 0
    calcParams.rgrc[0].right = 800
    calcParams.rgrc[0].bottom = 600

    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = win32con.WM_NCCALCSIZE
    syntheticMessage.wParam = 1
    syntheticMessage.lParam = ctypes.addressof(calcParams)
    messagePointer = ctypes.addressof(syntheticMessage)

    # 1. Normal window state: rect remains unchanged
    monkeypatch.setattr("qtframeless.core.frame_controller.isMaximized", lambda hWnd: False)
    monkeypatch.setattr("qtframeless.core.frame_controller.isFullScreen", lambda hWnd: False)

    eventHandled, resultCode = widget.nativeEvent(
        QByteArray(b"windows_generic_MSG"), messagePointer
    )
    assert eventHandled is True
    assert resultCode == win32con.WVR_REDRAW
    assert calcParams.rgrc[0].left == 0
    assert calcParams.rgrc[0].top == 0
    assert calcParams.rgrc[0].right == 800
    assert calcParams.rgrc[0].bottom == 600

    # 2. Maximized window state: rect inset by resize border thickness
    monkeypatch.setattr("qtframeless.core.frame_controller.isMaximized", lambda hWnd: True)
    monkeypatch.setattr("qtframeless.core.frame_controller.isFullScreen", lambda hWnd: False)
    monkeypatch.setattr(
        "qtframeless.core.frame_controller.getResizeBorderThickness", lambda hWnd: 8
    )
    monkeypatch.setattr("qtframeless.core.frame_controller.Taskbar.isAutoHide", lambda: False)

    eventHandled, resultCode = widget.nativeEvent(
        QByteArray(b"windows_generic_MSG"), messagePointer
    )
    assert eventHandled is True
    assert resultCode == win32con.WVR_REDRAW
    assert calcParams.rgrc[0].left == 8
    assert calcParams.rgrc[0].top == 8
    assert calcParams.rgrc[0].right == 792
    assert calcParams.rgrc[0].bottom == 592


def test_frameless_mixin_native_event_nc_calc_size_wparam_false_and_autohide_taskbar(
    qtbot, monkeypatch
):
    """Verify WM_NCCALCSIZE with wParam=0 and auto-hide taskbar adjustments.

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

    clientRect = WIN32_RECT(0, 0, 800, 600)
    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = win32con.WM_NCCALCSIZE
    syntheticMessage.wParam = 0
    syntheticMessage.lParam = ctypes.addressof(clientRect)
    messagePointer = ctypes.addressof(syntheticMessage)

    # 1. Normal state with wParam=0 returns 0
    monkeypatch.setattr("qtframeless.core.frame_controller.isMaximized", lambda hWnd: False)
    monkeypatch.setattr("qtframeless.core.frame_controller.isFullScreen", lambda hWnd: False)

    eventHandled, resultCode = widget.nativeEvent(
        QByteArray(b"windows_generic_MSG"), messagePointer
    )
    assert eventHandled is True
    assert resultCode == 0

    # 2. Maximized with auto-hide taskbar on TOP
    monkeypatch.setattr("qtframeless.core.frame_controller.isMaximized", lambda hWnd: True)
    monkeypatch.setattr("qtframeless.core.frame_controller.isFullScreen", lambda hWnd: False)
    monkeypatch.setattr(
        "qtframeless.core.frame_controller.getResizeBorderThickness", lambda hWnd: 8
    )
    monkeypatch.setattr("qtframeless.core.frame_controller.Taskbar.isAutoHide", lambda: True)
    monkeypatch.setattr(
        "qtframeless.core.frame_controller.Taskbar.getPosition",
        lambda hWnd: Taskbar.TOP,
    )

    clientRect = WIN32_RECT(0, 0, 800, 600)
    syntheticMessage.lParam = ctypes.addressof(clientRect)
    eventHandled, resultCode = widget.nativeEvent(
        QByteArray(b"windows_generic_MSG"), messagePointer
    )
    assert eventHandled is True
    assert clientRect.top == 8 + Taskbar.AUTO_HIDE_THICKNESS
    assert clientRect.left == 8
    assert clientRect.right == 792
    assert clientRect.bottom == 592

    # 3. Maximized with auto-hide taskbar on BOTTOM, LEFT, RIGHT
    for position, attributeName, isAdd in [
        (Taskbar.BOTTOM, "bottom", False),
        (Taskbar.LEFT, "left", True),
        (Taskbar.RIGHT, "right", False),
    ]:
        monkeypatch.setattr(
            "qtframeless.core.frame_controller.Taskbar.getPosition",
            lambda hWnd, pos=position: pos,
        )
        taskbarRect = WIN32_RECT(0, 0, 800, 600)
        syntheticMessage.lParam = ctypes.addressof(taskbarRect)
        eventHandled, _ = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
        assert eventHandled is True
        if isAdd:
            expectedCoordinate = 8 + Taskbar.AUTO_HIDE_THICKNESS
        else:
            baseCoordinate = 600 if attributeName == "bottom" else 800
            expectedCoordinate = baseCoordinate - 8 - Taskbar.AUTO_HIDE_THICKNESS
        assert getattr(taskbarRect, attributeName) == expectedCoordinate


def test_frameless_mixin_native_event_settings_and_style(qtbot):
    """Verify nativeEvent responds to WM_SETTINGCHANGE and WM_STYLECHANGING.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)
    widget.show()

    # Create synthetic MSG for WM_SETTINGCHANGE
    settingMessage = MSG()
    settingMessage.hWnd = int(widget.winId())
    settingMessage.message = win32con.WM_SETTINGCHANGE
    settingMessagePointer = ctypes.addressof(settingMessage)
    eventHandled, _ = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), settingMessagePointer)
    assert eventHandled is True

    # Create synthetic MSG for WM_STYLECHANGING
    styleMessage = MSG()
    styleMessage.hWnd = int(widget.winId())
    styleMessage.message = win32con.WM_STYLECHANGING
    styleMessagePointer = ctypes.addressof(styleMessage)
    eventHandled, _ = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), styleMessagePointer)
    assert eventHandled is True
    assert widget.isResizable() is True


def test_frameless_mixin_native_event_nc_hit_test_scaled_dpi(qtbot, monkeypatch):
    """Verify WM_NCHITTEST hit-testing boundaries adapt to scaled DPI border width.

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

    # Mock 192 DPI (2.0x scale -> scaled border width = round(5 * 192 / 96) = 10 px)
    monkeypatch.setattr(
        "qtframeless.core.frame_controller.getDpiForWindow",
        lambda hWnd: 192,
    )

    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = win32con.WM_NCHITTEST
    messagePointer = ctypes.addressof(syntheticMessage)

    # Relative x = 7 is inside the 10px scaled left border (at 96 DPI it would be client area)
    scaledLeftPoint = QPoint(107, 200)
    monkeypatch.setattr(
        "qtframeless.core.frame_controller.QCursor.pos",
        staticmethod(lambda: scaledLeftPoint),
    )
    eventHandled, hitCode = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert eventHandled is True
    assert hitCode == win32con.HTLEFT

    # Relative x = 12 is outside the 10px border, should fall through to client area
    clientPoint = QPoint(112, 200)
    monkeypatch.setattr(
        "qtframeless.core.frame_controller.QCursor.pos",
        staticmethod(lambda: clientPoint),
    )
    eventHandled, _ = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert eventHandled is False


def test_frameless_mixin_native_event_dpi_changed(qtbot, monkeypatch):
    """Verify WM_DPICHANGED triggers TitleBar DPI scaling and SetWindowPos with SWP_FRAMECHANGED.

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

    suggestedRect = RECT(100, 100, 500, 400)
    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = WM_DPICHANGED
    # wParam has new DPI: LOWORD and HIWORD both 144
    syntheticMessage.wParam = (144 << 16) | 144
    syntheticMessage.lParam = ctypes.addressof(suggestedRect)
    messagePointer = ctypes.addressof(syntheticMessage)

    eventHandled, resultCode = widget.nativeEvent(
        QByteArray(b"windows_generic_MSG"), messagePointer
    )
    assert eventHandled is True
    assert resultCode == 0

    # TitleBar updateDpiScaling was called with 144
    mockUpdateDpiScaling.assert_called_once_with(144)

    # SetWindowPos was called with SWP_FRAMECHANGED
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


def test_frameless_mixin_pure_opaque_no_window_effect(qtbot):
    """Verify base FramelessWindowMixin is pure opaque and decoupled from setWindowEffect.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    assert not hasattr(widget, "setWindowEffect")
    assert not hasattr(widget, "windowEffect")
    assert not hasattr(widget, "windowEffectChanged")
    assert not hasattr(widget, "_handleAcrylicLagMitigation")
    assert not hasattr(widget, "_restoreAcrylicEffect")
    assert widget.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is False
