"""Unit tests for WindowFrameController native message handling and properties."""

import ctypes
from ctypes.wintypes import MSG, RECT
from unittest.mock import MagicMock

import win32con
from qtpy.QtCore import QByteArray, QPoint
from qtpy.QtWidgets import QWidget

from qtframeless.core.frame_controller import WindowFrameController
from qtframeless.core.frameless_mixin import FramelessWindowMixin
from qtframeless.native.win32_types import NCCALCSIZE_PARAMS, WM_DPICHANGED, WM_NCMOUSELEAVE


class DummyWindow(FramelessWindowMixin, QWidget):
    """Test widget integrating FramelessWindowMixin and QWidget."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._initVal()
        self._initUi()


def test_frame_controller_initialization_and_properties(qtbot) -> None:
    """Verify WindowFrameController initialization and property getter/setters.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    widget = DummyWindow()
    qtbot.addWidget(widget)

    controller = WindowFrameController(
        widget,
        borderWidth=8,
        resizable=True,
        pressToMove=True,
        dpiScaling=True,
    )

    assert controller.getBorderWidth() == 8
    assert controller.isResizable() is True
    assert controller.isPressToMove() is True
    assert controller.isDpiScalingAllowed() is True

    controller.setBorderWidth(10)
    assert controller.getBorderWidth() == 10
    assert widget._borderWidth == 10

    controller.setResizable(False)
    assert controller.isResizable() is False

    controller.setPressToMove(False)
    assert controller.isPressToMove() is False

    controller.setDpiScalingAllowed(False)
    assert controller.isDpiScalingAllowed() is False


def test_frame_controller_resize_hit_testing(qtbot, monkeypatch) -> None:
    """Verify WM_NCHITTEST border hit testing for corners, edges, and non-resizable states.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    widget = DummyWindow()
    qtbot.addWidget(widget)
    widget.setGeometry(100, 100, 200, 200)
    widget.show()

    controller = WindowFrameController(widget, borderWidth=5)

    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = win32con.WM_NCHITTEST
    messagePointer = ctypes.addressof(syntheticMessage)

    # 1. Top-left corner hit test
    monkeypatch.setattr(
        "qtframeless.core.frame_controller.QCursor.pos",
        staticmethod(lambda: QPoint(100, 100)),
    )
    result = controller.handleNativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert result == (True, win32con.HTTOPLEFT)

    # 2. Right edge hit test
    monkeypatch.setattr(
        "qtframeless.core.frame_controller.QCursor.pos",
        staticmethod(lambda: QPoint(299, 200)),
    )
    result = controller.handleNativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert result == (True, win32con.HTRIGHT)

    # 3. Client area hit test returns None
    monkeypatch.setattr(
        "qtframeless.core.frame_controller.QCursor.pos",
        staticmethod(lambda: QPoint(200, 200)),
    )
    result = controller.handleNativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert result is None

    # 4. Non-resizable window returns None for borders
    controller.setResizable(False)
    monkeypatch.setattr(
        "qtframeless.core.frame_controller.QCursor.pos",
        staticmethod(lambda: QPoint(100, 100)),
    )
    result = controller.handleNativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert result is None


def test_frame_controller_snap_layout_hit_testing(qtbot, monkeypatch) -> None:
    """Verify WM_NCHITTEST returns HTMAXBUTTON over maximize button.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    widget = DummyWindow()
    qtbot.addWidget(widget)
    widget.setGeometry(100, 100, 400, 300)
    widget.show()

    controller = widget._frameController
    titleBar = widget.getTitleBar()
    assert titleBar is not None
    maximizeButton = titleBar.getMaximizeButton()
    assert maximizeButton is not None

    buttonCenter = QPoint(maximizeButton.width() // 2, maximizeButton.height() // 2)
    globalCursorPosition = maximizeButton.mapToGlobal(buttonCenter)

    monkeypatch.setattr(
        "qtframeless.core.frame_controller.QCursor.pos",
        staticmethod(lambda: globalCursorPosition),
    )

    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = win32con.WM_NCHITTEST
    messagePointer = ctypes.addressof(syntheticMessage)

    result = controller.handleNativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert result == (True, win32con.HTMAXBUTTON)


def test_frame_controller_nc_mouse_events(qtbot, monkeypatch) -> None:
    """Verify non-client mouse move, leave, button down, and button up handling.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    widget = DummyWindow()
    qtbot.addWidget(widget)
    widget.setGeometry(100, 100, 400, 300)
    widget.show()

    controller = widget._frameController
    titleBar = widget.getTitleBar()
    assert titleBar is not None
    maximizeButton = titleBar.getMaximizeButton()
    assert maximizeButton is not None

    monkeypatch.setattr(
        "qtframeless.core.frame_controller.windll.user32.TrackMouseEvent", lambda pointer: True
    )

    # 1. WM_NCMOUSEMOVE with HTMAXBUTTON
    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = win32con.WM_NCMOUSEMOVE
    syntheticMessage.wParam = win32con.HTMAXBUTTON
    messagePointer = ctypes.addressof(syntheticMessage)

    result = controller.handleNativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert result == (True, 0)
    assert maximizeButton.isHovered() is True

    # 2. WM_NCLBUTTONDOWN with HTMAXBUTTON
    syntheticMessage.message = win32con.WM_NCLBUTTONDOWN
    result = controller.handleNativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert result == (True, 0)
    assert maximizeButton.isPressedState() is True

    # 3. WM_NCLBUTTONUP with HTMAXBUTTON toggles window maximization
    syntheticMessage.message = win32con.WM_NCLBUTTONUP
    result = controller.handleNativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert result == (True, 0)
    assert maximizeButton.isPressedState() is False
    assert widget.isMaximized() is True

    # 4. WM_NCMOUSELEAVE resets hover and pressed state
    syntheticMessage.message = WM_NCMOUSELEAVE
    syntheticMessage.wParam = 0
    result = controller.handleNativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert result == (True, 0)
    assert maximizeButton.isHovered() is False
    assert maximizeButton.isPressedState() is False


def test_frame_controller_nc_calc_size(qtbot, monkeypatch) -> None:
    """Verify WM_NCCALCSIZE frame rect adjustment for normal and maximized states.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    widget = DummyWindow()
    qtbot.addWidget(widget)
    widget.show()

    controller = widget._frameController

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

    # 1. Normal state: rect remains unchanged
    monkeypatch.setattr("qtframeless.core.frame_controller.isMaximized", lambda hWnd: False)
    monkeypatch.setattr("qtframeless.core.frame_controller.isFullScreen", lambda hWnd: False)

    result = controller.handleNativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert result == (True, win32con.WVR_REDRAW)
    assert calcParams.rgrc[0].left == 0
    assert calcParams.rgrc[0].top == 0

    # 2. Maximized state: inset by border thickness
    monkeypatch.setattr("qtframeless.core.frame_controller.isMaximized", lambda hWnd: True)
    monkeypatch.setattr(
        "qtframeless.core.frame_controller.getResizeBorderThickness", lambda hWnd: 8
    )
    monkeypatch.setattr("qtframeless.core.frame_controller.Taskbar.isAutoHide", lambda: False)

    result = controller.handleNativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert result == (True, win32con.WVR_REDRAW)
    assert calcParams.rgrc[0].left == 8
    assert calcParams.rgrc[0].top == 8
    assert calcParams.rgrc[0].right == 792
    assert calcParams.rgrc[0].bottom == 592


def test_frame_controller_dpi_changed(qtbot, monkeypatch) -> None:
    """Verify WM_DPICHANGED triggers title bar scaling update and DWM sync.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    widget = DummyWindow()
    qtbot.addWidget(widget)
    widget.show()

    controller = widget._frameController
    titleBar = widget.getTitleBar()
    assert titleBar is not None

    mockUpdateDpiScaling = MagicMock()
    monkeypatch.setattr(titleBar, "updateDpiScaling", mockUpdateDpiScaling)
    monkeypatch.setattr("win32gui.SetWindowPos", lambda *args: None)

    suggestedRect = RECT(100, 100, 600, 500)
    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = WM_DPICHANGED
    syntheticMessage.wParam = (144 << 16) | 144
    syntheticMessage.lParam = ctypes.addressof(suggestedRect)
    messagePointer = ctypes.addressof(syntheticMessage)

    # 1. Enabled DPI scaling triggers title bar update with new DPI
    result = controller.handleNativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert result == (True, 0)
    mockUpdateDpiScaling.assert_called_once_with(144)

    # 2. Disabled DPI scaling ignores DPI change in title bar
    mockUpdateDpiScaling.reset_mock()
    controller.setDpiScalingAllowed(False)
    result = controller.handleNativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert result == (True, 0)
    mockUpdateDpiScaling.assert_not_called()


def test_frame_controller_start_system_move(qtbot, monkeypatch) -> None:
    """Verify startSystemMove invokes window handle system move delegation.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    widget = DummyWindow()
    qtbot.addWidget(widget)
    widget.show()

    controller = widget._frameController
    windowHandle = widget.windowHandle()
    assert windowHandle is not None

    mockStartSystemMove = MagicMock()
    monkeypatch.setattr(windowHandle, "startSystemMove", mockStartSystemMove)

    controller.startSystemMove()
    mockStartSystemMove.assert_called_once()
