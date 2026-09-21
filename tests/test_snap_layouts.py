"""Tests for Windows 11 Snap Layouts integration and non-client events."""

import ctypes
from ctypes.wintypes import MSG

import win32con
from qtpy.QtCore import QByteArray, QPoint, Qt
from qtpy.QtGui import QPixmap
from qtpy.QtWidgets import QWidget

from qtframelesskit import FramelessWidget
from qtframelesskit.native.win32_types import WM_NCMOUSELEAVE
from qtframelesskit.windows.title_bar import MaximizeButton, TitleBar


def test_maximize_button_hover_state(qtbot) -> None:
    """Verify MaximizeButton hover state getter and setter with visual update."""
    parentWidget = QWidget()
    qtbot.addWidget(parentWidget)

    maximizeButton = MaximizeButton(parentWidget)
    maximizeButton.resize(46, 30)

    # Initial hover state must be False
    assert maximizeButton.isHovered() is False

    # Setting hover state to True
    maximizeButton.setHoverState(True)
    assert maximizeButton.isHovered() is True
    hoverColor = maximizeButton.getHoverColor()
    qtbot.waitUntil(
        lambda: maximizeButton.getCurrentBackgroundColor() == hoverColor,
        timeout=1000,
    )

    # Render pixmap when hovered and confirm non-empty rendering
    pixmap = QPixmap(maximizeButton.size())
    pixmap.fill(Qt.GlobalColor.transparent)
    maximizeButton.render(pixmap)
    image = pixmap.toImage()

    # The background should be drawn with hover color
    centerPixelColor = image.pixelColor(2, 2)
    assert centerPixelColor == hoverColor

    # Setting hover state back to False resets the state
    maximizeButton.setHoverState(False)
    assert maximizeButton.isHovered() is False
    qtbot.waitUntil(
        lambda: maximizeButton.getCurrentBackgroundColor().alpha() == 0,
        timeout=1000,
    )

    # Render pixmap when not hovered: background pixel should be transparent
    clearedPixmap = QPixmap(maximizeButton.size())
    clearedPixmap.fill(Qt.GlobalColor.transparent)
    maximizeButton.render(clearedPixmap)
    clearedImage = clearedPixmap.toImage()
    assert clearedImage.pixelColor(2, 2).alpha() == 0


def test_maximize_button_pressed_state(qtbot) -> None:
    """Verify MaximizeButton pressed state getter, setter, and visual styling."""
    parentWidget = QWidget()
    qtbot.addWidget(parentWidget)

    maximizeButton = MaximizeButton(parentWidget)
    maximizeButton.resize(46, 30)

    # Initial pressed state must be False
    assert maximizeButton.isPressedState() is False
    assert maximizeButton.isDown() is False

    # Setting pressed state to True
    maximizeButton.setPressedState(True)
    assert maximizeButton.isPressedState() is True
    assert maximizeButton.isDown() is True
    pressedColor = maximizeButton.getPressedColor()
    qtbot.waitUntil(
        lambda: maximizeButton.getCurrentBackgroundColor() == pressedColor,
        timeout=1000,
    )

    # Render pixmap when pressed and verify pressed background color (#cacaca)
    pixmap = QPixmap(maximizeButton.size())
    pixmap.fill(Qt.GlobalColor.transparent)
    maximizeButton.render(pixmap)
    image = pixmap.toImage()
    assert image.pixelColor(2, 2) == pressedColor

    # Reset pressed state to False
    maximizeButton.setPressedState(False)
    assert maximizeButton.isPressedState() is False
    assert maximizeButton.isDown() is False
    qtbot.waitUntil(
        lambda: maximizeButton.getCurrentBackgroundColor().alpha() == 0,
        timeout=1000,
    )

    # Triangulation: setting Qt's native setDown(True) also reflects in isPressedState
    maximizeButton.setDown(True)
    assert maximizeButton.isPressedState() is True
    maximizeButton.setDown(False)
    assert maximizeButton.isPressedState() is False


def test_titlebar_get_maximize_button(qtbot) -> None:
    """Verify TitleBar getMaximizeButton returns instance when present and None when excluded."""
    window = QWidget()
    qtbot.addWidget(window)

    titleBar = TitleBar(window, hint=["min", "max", "close"])
    maximizeButton = titleBar.getMaximizeButton()
    assert maximizeButton is not None
    assert isinstance(maximizeButton, MaximizeButton)

    # TitleBar without max in hint should return None
    titleBarNoMax = TitleBar(window, hint=["min", "close"])
    assert titleBarNoMax.getMaximizeButton() is None

    # Setting base window non-resizable hides max button and returns None
    titleBar.setBaseWindowResizable(False)
    assert titleBar.getMaximizeButton() is None

    # Re-enabling resizability restores visibility and returns button
    titleBar.setBaseWindowResizable(True)
    assert titleBar.getMaximizeButton() is not None


def test_wm_nchittest_returns_htmaxbutton_for_resizable_window(qtbot, monkeypatch) -> None:
    """Verify WM_NCHITTEST returns HTMAXBUTTON when cursor is over maximize button."""
    widget = FramelessWidget()
    qtbot.addWidget(widget)
    widget.setGeometry(100, 100, 400, 300)
    widget.show()

    titleBar = widget.getTitleBar()
    assert titleBar is not None
    maximizeButton = titleBar.getMaximizeButton()
    assert maximizeButton is not None

    # Calculate global position inside maximize button
    buttonCenter = QPoint(maximizeButton.width() // 2, maximizeButton.height() // 2)
    globalCursorPosition = maximizeButton.mapToGlobal(buttonCenter)

    monkeypatch.setattr(
        "qtframelesskit.core.frame_controller.QCursor.pos",
        staticmethod(lambda: globalCursorPosition),
    )

    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = win32con.WM_NCHITTEST
    messagePointer = ctypes.addressof(syntheticMessage)

    eventHandled, hitCode = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)

    assert eventHandled is True
    assert hitCode == win32con.HTMAXBUTTON


def test_wm_nchittest_does_not_return_htmaxbutton_for_non_resizable(qtbot, monkeypatch) -> None:
    """Verify WM_NCHITTEST falls back and does not return HTMAXBUTTON when non-resizable."""
    widget = FramelessWidget()
    qtbot.addWidget(widget)
    widget.setGeometry(100, 100, 400, 300)
    widget.show()

    titleBar = widget.getTitleBar()
    assert titleBar is not None
    maximizeButton = titleBar._maximizeButton
    buttonCenter = QPoint(maximizeButton.width() // 2, maximizeButton.height() // 2)
    globalCursorPosition = maximizeButton.mapToGlobal(buttonCenter)

    monkeypatch.setattr(
        "qtframelesskit.core.frame_controller.QCursor.pos",
        staticmethod(lambda: globalCursorPosition),
    )

    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = win32con.WM_NCHITTEST
    messagePointer = ctypes.addressof(syntheticMessage)

    # When window is set non-resizable
    widget.setResizable(False)
    eventHandled, hitCode = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert hitCode != win32con.HTMAXBUTTON

    # When window has fixed size
    widget.setFixedSize(400, 300)
    eventHandled, hitCode = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert hitCode != win32con.HTMAXBUTTON


def test_wm_nchittest_without_maximize_button(qtbot, monkeypatch) -> None:
    """Verify WM_NCHITTEST does not return HTMAXBUTTON when title bar omits maximize button."""
    widget = FramelessWidget(hint=["min", "close"])
    qtbot.addWidget(widget)
    widget.setGeometry(100, 100, 400, 300)
    widget.show()

    titleBar = widget.getTitleBar()
    assert titleBar is not None
    assert titleBar.getMaximizeButton() is None

    # Pick a point in the title bar corner area
    globalCursorPosition = widget.mapToGlobal(QPoint(350, 15))
    monkeypatch.setattr(
        "qtframelesskit.core.frame_controller.QCursor.pos",
        staticmethod(lambda: globalCursorPosition),
    )

    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = win32con.WM_NCHITTEST
    messagePointer = ctypes.addressof(syntheticMessage)

    eventHandled, hitCode = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert hitCode != win32con.HTMAXBUTTON


def test_wm_nchittest_when_maximized(qtbot, monkeypatch) -> None:
    """Verify WM_NCHITTEST returns HTMAXBUTTON on restore button when window is maximized."""
    widget = FramelessWidget()
    qtbot.addWidget(widget)
    widget.setGeometry(100, 100, 400, 300)
    widget.show()
    widget.showMaximized()

    titleBar = widget.getTitleBar()
    assert titleBar is not None
    maximizeButton = titleBar.getMaximizeButton()
    assert maximizeButton is not None

    buttonCenter = QPoint(maximizeButton.width() // 2, maximizeButton.height() // 2)
    globalCursorPosition = maximizeButton.mapToGlobal(buttonCenter)

    monkeypatch.setattr(
        "qtframelesskit.core.frame_controller.QCursor.pos",
        staticmethod(lambda: globalCursorPosition),
    )

    syntheticMessage = MSG()
    syntheticMessage.hWnd = int(widget.winId())
    syntheticMessage.message = win32con.WM_NCHITTEST
    messagePointer = ctypes.addressof(syntheticMessage)

    eventHandled, hitCode = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), messagePointer)
    assert eventHandled is True
    assert hitCode == win32con.HTMAXBUTTON


def test_non_client_mouse_move_and_leave_synchronization(qtbot) -> None:
    """Verify WM_NCMOUSEMOVE and WM_NCMOUSELEAVE synchronize maximize button hover state."""
    widget = FramelessWidget()
    qtbot.addWidget(widget)
    widget.setGeometry(100, 100, 400, 300)
    widget.show()

    titleBar = widget.getTitleBar()
    assert titleBar is not None
    maximizeButton = titleBar.getMaximizeButton()
    assert maximizeButton is not None
    assert maximizeButton.isHovered() is False

    # Simulate WM_NCMOUSEMOVE with wParam == HTMAXBUTTON
    moveMessage = MSG()
    moveMessage.hWnd = int(widget.winId())
    moveMessage.message = win32con.WM_NCMOUSEMOVE
    moveMessage.wParam = win32con.HTMAXBUTTON
    movePointer = ctypes.addressof(moveMessage)

    eventHandled, result = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), movePointer)
    assert eventHandled is True
    assert maximizeButton.isHovered() is True

    # Simulate WM_NCMOUSELEAVE
    leaveMessage = MSG()
    leaveMessage.hWnd = int(widget.winId())
    leaveMessage.message = WM_NCMOUSELEAVE
    leaveMessage.wParam = 0
    leavePointer = ctypes.addressof(leaveMessage)

    eventHandled, result = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), leavePointer)
    assert eventHandled is True
    assert maximizeButton.isHovered() is False


def test_non_client_click_toggle_action(qtbot) -> None:
    """Verify WM_NCLBUTTONDOWN and WM_NCLBUTTONUP update press state and toggle maximize."""
    widget = FramelessWidget()
    qtbot.addWidget(widget)
    widget.setGeometry(100, 100, 400, 300)
    widget.show()

    titleBar = widget.getTitleBar()
    assert titleBar is not None
    maximizeButton = titleBar.getMaximizeButton()
    assert maximizeButton is not None

    # Simulate WM_NCLBUTTONDOWN with HTMAXBUTTON
    downMessage = MSG()
    downMessage.hWnd = int(widget.winId())
    downMessage.message = win32con.WM_NCLBUTTONDOWN
    downMessage.wParam = win32con.HTMAXBUTTON
    downPointer = ctypes.addressof(downMessage)

    eventHandled, result = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), downPointer)
    assert eventHandled is True
    assert maximizeButton.isPressedState() is True

    # Simulate WM_NCLBUTTONUP with HTMAXBUTTON -> maximizes normal window
    assert widget.isMaximized() is False
    upMessage = MSG()
    upMessage.hWnd = int(widget.winId())
    upMessage.message = win32con.WM_NCLBUTTONUP
    upMessage.wParam = win32con.HTMAXBUTTON
    upPointer = ctypes.addressof(upMessage)

    eventHandled, result = widget.nativeEvent(QByteArray(b"windows_generic_MSG"), upPointer)
    assert eventHandled is True
    assert maximizeButton.isPressedState() is False
    assert widget.isMaximized() is True

    # Simulate second click (WM_NCLBUTTONDOWN then WM_NCLBUTTONUP) -> restores window
    widget.nativeEvent(QByteArray(b"windows_generic_MSG"), downPointer)
    assert maximizeButton.isPressedState() is True

    widget.nativeEvent(QByteArray(b"windows_generic_MSG"), upPointer)
    assert maximizeButton.isPressedState() is False
    assert widget.isMaximized() is False


def test_non_client_mouse_move_off_clears_hover(qtbot) -> None:
    """Verify WM_NCMOUSEMOVE with non-HTMAXBUTTON wParam resets hover state."""
    widget = FramelessWidget()
    qtbot.addWidget(widget)
    widget.setGeometry(100, 100, 400, 300)
    widget.show()

    titleBar = widget.getTitleBar()
    assert titleBar is not None
    maximizeButton = titleBar.getMaximizeButton()
    assert maximizeButton is not None

    # Hover the maximize button
    moveMessage = MSG()
    moveMessage.hWnd = int(widget.winId())
    moveMessage.message = win32con.WM_NCMOUSEMOVE
    moveMessage.wParam = win32con.HTMAXBUTTON
    movePointer = ctypes.addressof(moveMessage)
    widget.nativeEvent(QByteArray(b"windows_generic_MSG"), movePointer)
    assert maximizeButton.isHovered() is True

    # Move to caption (wParam == HTCAPTION)
    moveCaptionMessage = MSG()
    moveCaptionMessage.hWnd = int(widget.winId())
    moveCaptionMessage.message = win32con.WM_NCMOUSEMOVE
    moveCaptionMessage.wParam = win32con.HTCAPTION
    moveCaptionPointer = ctypes.addressof(moveCaptionMessage)
    widget.nativeEvent(QByteArray(b"windows_generic_MSG"), moveCaptionPointer)
    assert maximizeButton.isHovered() is False


def test_non_client_release_outside_clears_pressed_without_toggle(qtbot) -> None:
    """Verify WM_NCLBUTTONUP outside HTMAXBUTTON clears pressed state without toggle."""
    widget = FramelessWidget()
    qtbot.addWidget(widget)
    widget.setGeometry(100, 100, 400, 300)
    widget.show()

    titleBar = widget.getTitleBar()
    assert titleBar is not None
    maximizeButton = titleBar.getMaximizeButton()
    assert maximizeButton is not None

    # Press on maximize button
    downMessage = MSG()
    downMessage.hWnd = int(widget.winId())
    downMessage.message = win32con.WM_NCLBUTTONDOWN
    downMessage.wParam = win32con.HTMAXBUTTON
    widget.nativeEvent(QByteArray(b"windows_generic_MSG"), ctypes.addressof(downMessage))
    assert maximizeButton.isPressedState() is True

    # Release over caption area
    upCaptionMessage = MSG()
    upCaptionMessage.hWnd = int(widget.winId())
    upCaptionMessage.message = win32con.WM_NCLBUTTONUP
    upCaptionMessage.wParam = win32con.HTCAPTION
    widget.nativeEvent(QByteArray(b"windows_generic_MSG"), ctypes.addressof(upCaptionMessage))

    assert maximizeButton.isPressedState() is False
    # Window should not have maximized
    assert widget.isMaximized() is False
