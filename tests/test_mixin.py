"""Tests for FramelessWindowMixin core logic and Win32 event handling."""

from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QWidget

from qtframeless.core.frameless_mixin import FramelessWindowMixin


class DummyFramelessWidget(FramelessWindowMixin, QWidget):
    """Test widget subclass combining FramelessWindowMixin and QWidget."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._initVal()
        self._initUi()


def test_mixin_initialization(qtbot):
    """Verify FramelessWindowMixin initializes window flags and title bar."""
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    assert bool(widget.windowFlags() & Qt.WindowType.FramelessWindowHint)
    assert widget.getTitleBar() is not None
    assert widget.isPressToMove() is True
    assert widget.isResizable() is True


def test_mixin_fixed_size_disables_resizable(qtbot):
    """Verify setFixedSize disables resizability on mixin."""
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    assert widget.isResizable() is True
    widget.setFixedSize(400, 300)
    assert widget.isResizable() is False


def test_mixin_theme_detection_and_signal(qtbot):
    """Verify theme detection emits darkThemeChanged signal."""
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    # Test signal emission using qtbot.waitSignal
    with qtbot.waitSignal(widget.darkThemeChanged, timeout=1000) as blocker:
        widget._setCurrentWindowsTheme()
    assert blocker.signal_triggered
    assert isinstance(blocker.args[0], bool)


def test_mixin_light_theme_detection(qtbot, monkeypatch):
    """Verify light theme detection when registry returns AppsUseLightTheme=1."""
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    from unittest.mock import MagicMock

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


def test_mixin_dark_theme_detection(qtbot, monkeypatch):
    """Verify dark theme detection when registry returns AppsUseLightTheme=0."""
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    from unittest.mock import MagicMock

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


def test_mixin_dark_theme_manual_override(qtbot):
    """Verify setDarkTheme calls window effect without errors."""
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    widget.setDarkTheme(True)
    widget.setDarkTheme(False)


def test_mixin_title_and_icon_delegation(qtbot):
    """Verify setWindowTitle and setTitleBarVisible update title bar state."""
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    widget.setWindowTitle("Mixin Title Test")
    assert widget.getTitleBar().getTitle().text() == "Mixin Title Test"

    widget.setTitleBarVisible(False)
    assert widget.getTitleBar().isHidden()
    assert widget.isPressToMove() is True

    widget.setTitleBarVisible(True)
    assert not widget.getTitleBar().isHidden()


def test_mixin_icon_and_hints_delegation(qtbot):
    """Verify setWindowIcon and setTitleBarHint propagate to TitleBar."""
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    from qtpy.QtGui import QColor, QPixmap

    pixmap = QPixmap(16, 16)
    pixmap.fill(QColor("red"))
    icon = QIcon(pixmap)

    widget.setWindowIcon(icon)
    assert not widget.getTitleBar().getIcon().pixmap().isNull()

    widget.setTitleBarHint(["min", "close"])
    buttons = widget.getTitleBar().getButtons()
    assert not buttons["min"].isHidden()
    assert not buttons["close"].isHidden()
    assert buttons["max"].isHidden()


def test_mixin_theme_detection_toggle(qtbot):
    """Verify allowDetectingTheme and isDetectingThemeAllowed."""
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    assert widget.isDetectingThemeAllowed() is True
    widget.allowDetectingTheme(False)
    assert widget.isDetectingThemeAllowed() is False
    widget.allowDetectingTheme(True)
    assert widget.isDetectingThemeAllowed() is True


def test_mixin_screen_changed(qtbot, monkeypatch):
    """Verify _onScreenChanged triggers win32gui.SetWindowPos with SWP_FRAMECHANGED."""
    import win32con

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


def test_mixin_mouse_press_system_move_delegation(qtbot, monkeypatch):
    """Verify window movement is delegated to _startSystemMove on left mouse press."""
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)
    widget.show()

    moveCallCount = 0

    def recordSystemMove():
        nonlocal moveCallCount
        moveCallCount += 1

    monkeypatch.setattr(widget, "_startSystemMove", recordSystemMove)

    # Left click with pressToMove enabled triggers _startSystemMove
    assert widget.isPressToMove() is True
    qtbot.mousePress(widget, Qt.MouseButton.LeftButton)
    assert moveCallCount == 1

    # Right click does not trigger _startSystemMove
    qtbot.mousePress(widget, Qt.MouseButton.RightButton)
    assert moveCallCount == 1

    # Disabling pressToMove prevents _startSystemMove on left click
    widget.setPressToMove(False)
    assert widget.isPressToMove() is False
    qtbot.mousePress(widget, Qt.MouseButton.LeftButton)
    assert moveCallCount == 1


def test_mixin_native_event_nc_hit_test(qtbot, monkeypatch):
    """Verify WM_NCHITTEST hit-testing for corners, edges, center, and fixed size."""
    import ctypes
    from ctypes.wintypes import MSG

    import win32con
    from qtpy.QtCore import QByteArray, QPoint

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

    for name, cursorPosition, expectedHitCode in hitTestCases:
        monkeypatch.setattr(
            "qtframeless.core.frame_controller.QCursor.pos",
            staticmethod(lambda pos=cursorPosition: pos),
        )
        eventHandled, hitCode = widget.nativeEvent(
            QByteArray(b"windows_generic_MSG"), messagePointer
        )
        assert eventHandled is True, f"Failed handling for {name}"
        assert hitCode == expectedHitCode, (
            f"Incorrect hit code for {name}: {hitCode} != {expectedHitCode}"
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


def test_mixin_native_event_nc_calc_size_wparam_true(qtbot, monkeypatch):
    """Verify WM_NCCALCSIZE client rect calculation when wParam is non-zero."""
    import ctypes
    from ctypes.wintypes import MSG

    import win32con
    from qtpy.QtCore import QByteArray

    from qtframeless.native.win32_types import NCCALCSIZE_PARAMS

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


def test_mixin_native_event_nc_calc_size_wparam_false_and_autohide_taskbar(qtbot, monkeypatch):
    """Verify WM_NCCALCSIZE with wParam=0 and auto-hide taskbar adjustments."""
    import ctypes
    from ctypes.wintypes import MSG, RECT

    import win32con
    from qtpy.QtCore import QByteArray

    from qtframeless.native.win32_utils import Taskbar

    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)
    widget.show()

    clientRect = RECT(0, 0, 800, 600)
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

    clientRect = RECT(0, 0, 800, 600)
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
        taskbarRect = RECT(0, 0, 800, 600)
        syntheticMessage.lParam = ctypes.addressof(taskbarRect)
        eventHandled, _ = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
        assert eventHandled is True
        if isAdd:
            expectedCoordinate = 8 + Taskbar.AUTO_HIDE_THICKNESS
        else:
            baseCoordinate = 600 if attributeName == "bottom" else 800
            expectedCoordinate = baseCoordinate - 8 - Taskbar.AUTO_HIDE_THICKNESS
        assert getattr(taskbarRect, attributeName) == expectedCoordinate


def test_mixin_native_event_settings_and_style(qtbot):
    """Verify nativeEvent responds to WM_SETTINGCHANGE and WM_STYLECHANGING."""
    import ctypes
    from ctypes.wintypes import MSG

    import win32con
    from qtpy.QtCore import QByteArray

    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)
    widget.show()

    # Create synthetic MSG for WM_SETTINGCHANGE
    msg_setting = MSG()
    msg_setting.hWnd = int(widget.winId())
    msg_setting.message = win32con.WM_SETTINGCHANGE
    msg_ptr_setting = ctypes.addressof(msg_setting)
    handled, _ = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), msg_ptr_setting)
    assert handled is True

    # Create synthetic MSG for WM_STYLECHANGING
    msg_style = MSG()
    msg_style.hWnd = int(widget.winId())
    msg_style.message = win32con.WM_STYLECHANGING
    msg_ptr_style = ctypes.addressof(msg_style)
    handled, _ = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), msg_ptr_style)
    assert handled is True
    assert widget.isResizable() is True


def test_mixin_native_event_nc_hit_test_scaled_dpi(qtbot, monkeypatch):
    """Verify WM_NCHITTEST hit-testing boundaries adapt to scaled DPI border width.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    import ctypes
    from ctypes.wintypes import MSG

    import win32con
    from qtpy.QtCore import QByteArray, QPoint

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


def test_mixin_native_event_dpi_changed(qtbot, monkeypatch):
    """Verify WM_DPICHANGED triggers TitleBar DPI scaling and SetWindowPos with SWP_FRAMECHANGED.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    import ctypes
    from ctypes.wintypes import MSG, RECT
    from unittest.mock import MagicMock

    import win32con
    from qtpy.QtCore import QByteArray

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

    wmDpiChanged = 0x02E0
    suggestedRect = RECT(100, 100, 500, 400)
    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = wmDpiChanged
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


def test_base_frameless_mixin_pure_opaque_no_window_effect(qtbot):
    """Verify base FramelessWindowMixin is pure opaque and decoupled from setWindowEffect."""
    widget = DummyFramelessWidget()
    qtbot.addWidget(widget)

    assert not hasattr(widget, "setWindowEffect")
    assert not hasattr(widget, "windowEffect")
    assert not hasattr(widget, "windowEffectChanged")
    assert not hasattr(widget, "_handleAcrylicLagMitigation")
    assert not hasattr(widget, "_restoreAcrylicEffect")
    assert widget.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is False
