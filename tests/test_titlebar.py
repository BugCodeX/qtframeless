"""Tests for TitleBar widget, vector button rendering, and event filtering."""

from qtpy.QtCore import QEvent, Qt
from qtpy.QtGui import QColor, QFont, QIcon, QPainter, QPaintEvent, QPalette, QPixmap
from qtpy.QtWidgets import QApplication, QWidget

from qtframeless.windows.title_bar import (
    CloseButton,
    FullScreenButton,
    MaximizeButton,
    MinimizeButton,
    TitleBar,
    VectorButton,
)


def test_vector_buttons_creation_and_paint(qtbot):
    """Verify vector buttons instantiate and render non-empty glyphs without error."""
    parent = QWidget()
    qtbot.addWidget(parent)

    min_button = MinimizeButton(parent)
    max_button = MaximizeButton(parent)
    close_button = CloseButton(parent)

    for button in (min_button, max_button, close_button):
        assert isinstance(button, VectorButton)
        button.resize(46, 30)
        pixmap = QPixmap(button.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        button.render(pixmap)
        image = pixmap.toImage()
        drawnPixelCount = sum(
            1
            for x in range(image.width())
            for y in range(image.height())
            if image.pixelColor(x, y).alpha() > 0
        )
        assert drawnPixelCount > 0


def test_maximize_button_state_toggle(qtbot):
    """Verify MaximizeButton toggles maximized glyph state."""
    parent = QWidget()
    qtbot.addWidget(parent)

    max_button = MaximizeButton(parent)
    assert not max_button.isMaximizedState()

    max_button.setMaximizedState(True)
    assert max_button.isMaximizedState()

    max_button.setMaximizedState(False)
    assert not max_button.isMaximizedState()


def test_titlebar_title_and_font(qtbot):
    """Verify TitleBar title text and font updates."""
    window = QWidget()
    qtbot.addWidget(window)
    title_bar = TitleBar(window)

    title_bar.setTitle("Test Title")
    assert title_bar.getTitle().text() == "Test Title"

    custom_font = QFont("Arial", 14)
    title_bar.setTitleBarFont(custom_font)
    assert title_bar.getTitle().font().pointSize() == 14


def test_titlebar_icon_and_size(qtbot):
    """Verify TitleBar icon and size updates."""
    window = QWidget()
    qtbot.addWidget(window)
    title_bar = TitleBar(window)

    # Create dummy icon pixmap
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor("blue"))
    icon = QIcon(pixmap)

    title_bar.setIcon(icon)
    title_bar.setIconSize(24, 24)

    icon_pixmap = title_bar.getIcon().pixmap()
    assert not icon_pixmap.isNull()
    assert icon_pixmap.width() == 24
    assert icon_pixmap.height() == 24


def test_titlebar_hints_configuration(qtbot):
    """Verify TitleBar hint controls button visibility."""
    window = QWidget()
    qtbot.addWidget(window)

    title_bar = TitleBar(window, hint=["min", "close"])
    buttons = title_bar.getButtons()

    assert not buttons["min"].isHidden()
    assert not buttons["close"].isHidden()
    assert buttons["max"].isHidden()

    # Default hint shows standard buttons
    default_title_bar = TitleBar(window, hint=None)
    default_buttons = default_title_bar.getButtons()
    assert not default_buttons["min"].isHidden()
    assert not default_buttons["max"].isHidden()
    assert not default_buttons["close"].isHidden()


def test_titlebar_event_filter_window_state_change(qtbot):
    """Verify TitleBar eventFilter reacts to QEvent.Type.WindowStateChange."""
    window = QWidget()
    qtbot.addWidget(window)
    title_bar = TitleBar(window)

    # Simulate maximized state change event
    window.setWindowState(Qt.WindowState.WindowMaximized)
    event = QEvent(QEvent.Type.WindowStateChange)
    title_bar.eventFilter(window, event)

    max_button = title_bar.getButtons()["max"]
    assert isinstance(max_button, MaximizeButton)
    assert max_button.isMaximizedState()


def test_titlebar_event_filter_layout_request(qtbot):
    """Verify TitleBar eventFilter clamps maximum height on QEvent.Type.LayoutRequest."""
    window = QWidget()
    qtbot.addWidget(window)
    title_bar = TitleBar(window)

    event = QEvent(QEvent.Type.LayoutRequest)
    title_bar.eventFilter(window, event)
    assert title_bar.maximumHeight() == title_bar.sizeHint().height()


def test_fullscreen_button_and_event_filter(qtbot):
    """Verify FullScreenButton toggles and eventFilter hides/shows title bar."""
    window = QWidget()
    qtbot.addWidget(window)
    title_bar = TitleBar(window, hint=["full_screen", "min", "max", "close"])

    fullscreen_button = title_bar.getButtons()["full_screen"]
    pixmap = QPixmap(fullscreen_button.size())
    pixmap.fill(Qt.GlobalColor.transparent)
    fullscreen_button.render(pixmap)
    image = pixmap.toImage()
    drawnPixelCount = sum(
        1
        for x in range(image.width())
        for y in range(image.height())
        if image.pixelColor(x, y).alpha() > 0
    )
    assert drawnPixelCount > 0

    # Trigger fullscreen state event
    window.setWindowState(Qt.WindowState.WindowFullScreen)
    event = QEvent(QEvent.Type.WindowStateChange)
    title_bar.eventFilter(window, event)
    assert fullscreen_button.isChecked()
    assert title_bar.isHidden()

    # Trigger normal state event
    window.setWindowState(Qt.WindowState.WindowNoState)
    title_bar.eventFilter(window, event)
    assert not fullscreen_button.isChecked()
    assert not title_bar.isHidden()


def test_titlebar_base_widget_kwarg(qtbot):
    """Verify legacy base_widget keyword argument works."""
    window = QWidget()
    qtbot.addWidget(window)
    title_bar = TitleBar(base_widget=window)
    assert title_bar.parent() == window


def test_titlebar_resizable_toggle(qtbot):
    """Verify setBaseWindowResizable toggles maximize button visibility."""
    window = QWidget()
    qtbot.addWidget(window)
    title_bar = TitleBar(window)

    max_button = title_bar.getButtons()["max"]
    assert not max_button.isHidden()

    title_bar.setBaseWindowResizable(False)
    assert max_button.isHidden()

    title_bar.setBaseWindowResizable(True)
    assert not max_button.isHidden()


def test_titlebar_double_click_maximize(qtbot):
    """Verify double clicking TitleBar triggers maximize/restore on window."""
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(300, 200)
    window.show()
    title_bar = TitleBar(window)

    # Double click with left button
    qtbot.mouseDClick(title_bar, Qt.MouseButton.LeftButton)
    assert window.isMaximized()

    qtbot.mouseDClick(title_bar, Qt.MouseButton.LeftButton)
    assert not window.isMaximized()


def test_maximize_button_vector_painting_normal_and_restore(qtbot, monkeypatch):
    """Verify MaximizeButton paints single rectangle when normal and dual rectangles when maximized."""
    from unittest.mock import MagicMock

    parent = QWidget()
    qtbot.addWidget(parent)
    maxButton = MaximizeButton(parent)
    maxButton.resize(46, 30)

    # 1. Normal state (isMaximizedState = False): draws single square
    assert maxButton.isMaximizedState() is False
    mockPainterNormal = MagicMock()
    mockClassNormal = MagicMock(return_value=mockPainterNormal)
    mockClassNormal.RenderHint = QPainter.RenderHint
    monkeypatch.setattr(
        "qtframeless.windows.buttons.QPainter",
        mockClassNormal,
    )
    maxButton.paintEvent(QPaintEvent(maxButton.rect()))

    assert mockPainterNormal.drawRect.call_count == 1
    assert mockPainterNormal.drawPolyline.call_count == 0
    normalRect = mockPainterNormal.drawRect.call_args[0][0]
    # Button is 46x30, center is (23.0, 15.0), normal rect is 9x9 centered
    assert normalRect.width() == 9.0
    assert normalRect.height() == 9.0

    # 2. Maximized state (isMaximizedState = True): draws background polyline + front rect
    maxButton.setMaximizedState(True)
    assert maxButton.isMaximizedState() is True
    mockPainterMaximized = MagicMock()
    mockClassMaximized = MagicMock(return_value=mockPainterMaximized)
    mockClassMaximized.RenderHint = QPainter.RenderHint
    monkeypatch.setattr(
        "qtframeless.windows.buttons.QPainter",
        mockClassMaximized,
    )
    maxButton.paintEvent(QPaintEvent(maxButton.rect()))

    assert mockPainterMaximized.drawRect.call_count == 1
    assert mockPainterMaximized.drawPolyline.call_count == 1
    frontRect = mockPainterMaximized.drawRect.call_args[0][0]
    assert frontRect.width() == 8.0
    assert frontRect.height() == 8.0
    polylinePoints = mockPainterMaximized.drawPolyline.call_args[0][0]
    assert len(polylinePoints) == 5

    # 3. Verify actual rasterization in both states produces non-transparent pixels
    monkeypatch.undo()
    for isMaximized in (False, True):
        maxButton.setMaximizedState(isMaximized)
        pixmap = QPixmap(maxButton.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        maxButton.render(pixmap)
        image = pixmap.toImage()
        drawnPixelCount = sum(
            1
            for x in range(image.width())
            for y in range(image.height())
            if image.pixelColor(x, y).alpha() > 0
        )
        assert drawnPixelCount > 0


def test_vector_button_hover_and_pressed_styling_and_painting(qtbot, monkeypatch):
    """Verify vector button hover/pressed background colors and glyph stroke colors.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest fixture for monkeypatching methods.
    """
    from unittest.mock import MagicMock

    parent = QWidget()
    qtbot.addWidget(parent)

    minButton = MinimizeButton(parent)
    closeButton = CloseButton(parent)
    for button in (minButton, closeButton):
        button.resize(46, 30)

    # 1. Zero stylesheet verification
    assert minButton.styleSheet() == ""
    assert closeButton.styleSheet() == ""

    # 2. MinimizeButton hover and pressed background interpolation
    minButton.setHoverState(True)
    qtbot.waitUntil(
        lambda: minButton.getCurrentBackgroundColor() == minButton.getHoverColor(),
        timeout=1000,
    )
    minButton.setPressedState(True)
    qtbot.waitUntil(
        lambda: minButton.getCurrentBackgroundColor() == minButton.getPressedColor(),
        timeout=1000,
    )
    minButton.setPressedState(False)
    minButton.setHoverState(False)
    qtbot.waitUntil(
        lambda: minButton.getCurrentBackgroundColor().alpha() == 0,
        timeout=1000,
    )

    # 3. CloseButton hover and pressed background interpolation
    closeButton.setHoverState(True)
    qtbot.waitUntil(
        lambda: closeButton.getCurrentBackgroundColor() == QColor("#e81123"),
        timeout=1000,
    )
    closeButton.setPressedState(True)
    qtbot.waitUntil(
        lambda: closeButton.getCurrentBackgroundColor() == QColor("#f1707a"),
        timeout=1000,
    )
    closeButton.setPressedState(False)
    closeButton.setHoverState(False)
    qtbot.waitUntil(
        lambda: closeButton.getCurrentBackgroundColor().alpha() == 0,
        timeout=1000,
    )

    # 2. MinimizeButton glyph color in normal vs hover state
    mockPainterMinNormal = MagicMock()
    mockClassMin = MagicMock(return_value=mockPainterMinNormal)
    mockClassMin.RenderHint = QPainter.RenderHint
    monkeypatch.setattr(
        "qtframeless.windows.buttons.QPainter",
        mockClassMin,
    )
    monkeypatch.setattr(minButton, "underMouse", lambda: False)
    minButton.paintEvent(QPaintEvent(minButton.rect()))
    normalPen = mockPainterMinNormal.setPen.call_args[0][0]
    assert normalPen.color().name() == "#333333"

    mockPainterMinHover = MagicMock()
    mockClassMin.return_value = mockPainterMinHover
    monkeypatch.setattr(minButton, "underMouse", lambda: True)
    minButton.paintEvent(QPaintEvent(minButton.rect()))
    hoverPen = mockPainterMinHover.setPen.call_args[0][0]
    assert hoverPen.color().name() == "#111111"

    # 3. CloseButton glyph color in normal, hover, and pressed states
    mockPainterCloseNormal = MagicMock()
    mockClassClose = MagicMock(return_value=mockPainterCloseNormal)
    mockClassClose.RenderHint = QPainter.RenderHint
    monkeypatch.setattr(
        "qtframeless.windows.buttons.QPainter",
        mockClassClose,
    )
    monkeypatch.setattr(closeButton, "underMouse", lambda: False)
    monkeypatch.setattr(closeButton, "isDown", lambda: False)
    closeButton.paintEvent(QPaintEvent(closeButton.rect()))
    closeNormalPen = mockPainterCloseNormal.setPen.call_args[0][0]
    assert closeNormalPen.color().name() == "#333333"

    mockPainterCloseHover = MagicMock()
    mockClassClose.return_value = mockPainterCloseHover
    monkeypatch.setattr(closeButton, "underMouse", lambda: True)
    monkeypatch.setattr(closeButton, "isDown", lambda: False)
    closeButton.paintEvent(QPaintEvent(closeButton.rect()))
    closeHoverPen = mockPainterCloseHover.setPen.call_args[0][0]
    assert closeHoverPen.color().name() == "#ffffff"

    mockPainterClosePressed = MagicMock()
    mockClassClose.return_value = mockPainterClosePressed
    monkeypatch.setattr(closeButton, "underMouse", lambda: False)
    monkeypatch.setattr(closeButton, "isDown", lambda: True)
    closeButton.paintEvent(QPaintEvent(closeButton.rect()))
    closePressedPen = mockPainterClosePressed.setPen.call_args[0][0]
    assert closePressedPen.color().name() == "#ffffff"


def test_vector_button_pure_qpainter_animation_and_colors(qtbot):
    """Verify VectorButton animates background colors via QPainter without stylesheets.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    button = VectorButton()
    qtbot.addWidget(button)

    # 1. Zero stylesheet and transparent initial background
    assert button.styleSheet() == ""
    assert button.getCurrentBackgroundColor().alpha() == 0
    assert button._currentBackgroundColor.alpha() == 0

    # 2. Hover transition in light theme interpolates to #cfcfcf
    button.setHoverState(True)
    assert button.isHovered() is True
    qtbot.waitUntil(
        lambda: button.getCurrentBackgroundColor() == QColor("#cfcfcf"),
        timeout=1000,
    )

    # 3. Pressed transition in light theme interpolates to #b8b8b8
    button.setPressedState(True)
    assert button.isPressedState() is True
    qtbot.waitUntil(
        lambda: button.getCurrentBackgroundColor() == QColor("#b8b8b8"),
        timeout=1000,
    )

    # 4. Release and leave transition back to transparent
    button.setPressedState(False)
    button.setHoverState(False)
    qtbot.waitUntil(
        lambda: button.getCurrentBackgroundColor().alpha() == 0,
        timeout=1000,
    )

    # 5. Dark theme transitions
    button.setDarkTheme(True)
    assert button.styleSheet() == ""
    button.setHoverState(True)
    qtbot.waitUntil(
        lambda: button.getCurrentBackgroundColor() == QColor("#3f3f3f"),
        timeout=1000,
    )
    button.setPressedState(True)
    qtbot.waitUntil(
        lambda: button.getCurrentBackgroundColor() == QColor("#525252"),
        timeout=1000,
    )

    # 6. Custom hover and pressed colors
    button.setHoverColor("#ff5500")
    button.setPressedColor("#aa2200")
    assert button.getHoverColor() == QColor("#ff5500")
    assert button.getPressedColor() == QColor("#aa2200")
    button.setHoverColor(None)
    button.setPressedColor(None)
    assert button.getHoverColor() == QColor("#3f3f3f")
    assert button.getPressedColor() == QColor("#525252")


def test_titlebar_and_buttons_stylesheet_is_empty(qtbot):
    """Verify TitleBar, its labels, and control buttons have completely empty stylesheets.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window, hint=["full_screen", "min", "max", "close"])

    # 1. TitleBar and inner label stylesheets
    assert titleBar.styleSheet() == ""
    assert titleBar.getTitle().styleSheet() == ""
    assert titleBar.getIcon().styleSheet() == ""

    # 2. Control button stylesheets on TitleBar
    for button in titleBar.getButtons().values():
        assert button.styleSheet() == ""

    # 3. Standalone vector buttons
    standaloneButtons = [
        VectorButton(),
        MinimizeButton(),
        MaximizeButton(),
        CloseButton(),
        FullScreenButton(),
    ]
    for standaloneButton in standaloneButtons:
        qtbot.addWidget(standaloneButton)
        assert standaloneButton.styleSheet() == ""


def test_titlebar_and_buttons_global_qss_immunity(qtbot):
    """Verify global application stylesheets do not affect TitleBar or button rendering.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    applicationInstance = QApplication.instance()
    assert applicationInstance is not None
    previousStyleSheet = applicationInstance.styleSheet()

    try:
        # Inject invasive global stylesheet
        applicationInstance.setStyleSheet(
            "* { background: red; color: yellow; margin: 20px; border: 5px solid green; }"
        )

        window = QWidget()
        qtbot.addWidget(window)
        titleBar = TitleBar(window)

        # 1. Internal stylesheets remain strictly empty
        assert titleBar.styleSheet() == ""
        assert titleBar.getTitle().styleSheet() == ""
        assert titleBar.getIcon().styleSheet() == ""

        # 2. Text color derives directly from QPalette rather than QSS
        titlePalette = titleBar.getTitle().palette()
        assert titlePalette.color(QPalette.ColorRole.WindowText).name() == "#000000"

        titleBar.setDarkTheme(True)
        darkPalette = titleBar.getTitle().palette()
        assert darkPalette.color(QPalette.ColorRole.WindowText).name() == "#ffffff"

        # 3. Vector button background colors interpolate unaffected by global QSS
        closeButton = titleBar.getButtons()["close"]
        assert closeButton.styleSheet() == ""
        assert closeButton.getCurrentBackgroundColor().alpha() == 0

        closeButton.setHoverState(True)
        qtbot.waitUntil(
            lambda: closeButton.getCurrentBackgroundColor() == QColor("#e81123"),
            timeout=1000,
        )

        closeButton.setHoverState(False)
        qtbot.waitUntil(
            lambda: closeButton.getCurrentBackgroundColor().alpha() == 0,
            timeout=1000,
        )
    finally:
        applicationInstance.setStyleSheet(previousStyleSheet)


def test_titlebar_background_color_and_paint_event(qtbot):
    """Verify TitleBar background color getter/setter and QPainter paintEvent rendering.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    # 1. Default background color is None
    assert titleBar.getBackgroundColor() is None

    # 2. Set transparent background color
    titleBar.setBackgroundColor(QColor(0, 0, 0, 0))
    assert titleBar.getBackgroundColor() == QColor(0, 0, 0, 0)

    # 3. Paint event with QPainter renders transparent without error
    titleBar.resize(400, 30)
    titleBar.paintEvent(QPaintEvent(titleBar.rect()))

    # 4. Grab transparent TitleBar
    window.show()
    qtbot.waitExposed(window)
    grabbedImage = titleBar.grab().toImage()
    assert grabbedImage.pixelColor(10, 10).alpha() == 0

    # 5. Set custom hex string color
    titleBar.setBackgroundColor("#ff0000")
    assert titleBar.getBackgroundColor() == QColor("#ff0000")

    # 6. Reset to None
    titleBar.setBackgroundColor(None)
    assert titleBar.getBackgroundColor() is None


def test_vector_buttons_transparent_idle_background_preserves_parent(qtbot):
    """Verify VectorButtons are completely transparent in idle state and do not overwrite parent background.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    window.resize(400, 100)
    palette = window.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#1e1e1e"))
    window.setPalette(palette)
    window.setAutoFillBackground(True)
    qtbot.addWidget(window)

    titleBar = TitleBar(window)
    titleBar.setDarkTheme(True)
    titleBar.resize(400, 30)
    window.show()
    qtbot.waitExposed(window)

    grabbedImage = window.grab().toImage()

    for buttonKey in ("min", "max", "close"):
        button = titleBar.getButtons()[buttonKey]
        pos = button.mapTo(window, button.rect().topLeft())
        pixel = grabbedImage.pixelColor(pos.x() + 5, pos.y() + 5)
        assert pixel.name() == "#1e1e1e"


def test_vector_buttons_hover_transitions_over_parent_background(qtbot):
    """Verify VectorButtons transition to hover colors and restore transparency.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    window.resize(400, 100)
    palette = window.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#1e1e1e"))
    window.setPalette(palette)
    window.setAutoFillBackground(True)
    qtbot.addWidget(window)

    titleBar = TitleBar(window)
    titleBar.setDarkTheme(True)
    titleBar.resize(400, 30)
    window.show()
    qtbot.waitExposed(window)

    minButton = titleBar.getButtons()["min"]
    closeButton = titleBar.getButtons()["close"]

    # 1. Hover on minimize button interpolates to dark hover color
    minButton.setHoverState(True)
    qtbot.waitUntil(
        lambda: minButton.getCurrentBackgroundColor() == minButton.getHoverColor(),
        timeout=1000,
    )
    hoverImage = window.grab().toImage()
    posMin = minButton.mapTo(window, minButton.rect().topLeft())
    assert hoverImage.pixelColor(posMin.x() + 5, posMin.y() + 5).name() == "#3f3f3f"

    # 2. Leave hover restores transparent background showing parent #1e1e1e
    minButton.setHoverState(False)
    qtbot.waitUntil(
        lambda: minButton.getCurrentBackgroundColor().alpha() == 0,
        timeout=1000,
    )
    restoredImage = window.grab().toImage()
    assert restoredImage.pixelColor(posMin.x() + 5, posMin.y() + 5).name() == "#1e1e1e"

    # 3. Hover on close button interpolates to red
    closeButton.setHoverState(True)
    qtbot.waitUntil(
        lambda: closeButton.getCurrentBackgroundColor() == QColor("#e81123"),
        timeout=1000,
    )
    closeHoverImage = window.grab().toImage()
    posClose = closeButton.mapTo(window, closeButton.rect().topLeft())
    assert closeHoverImage.pixelColor(posClose.x() + 5, posClose.y() + 5).name() == "#e81123"

    # 4. Leave hover restores transparent background showing parent #1e1e1e
    closeButton.setHoverState(False)
    qtbot.waitUntil(
        lambda: closeButton.getCurrentBackgroundColor().alpha() == 0,
        timeout=1000,
    )
    closeRestoredImage = window.grab().toImage()
    assert closeRestoredImage.pixelColor(posClose.x() + 5, posClose.y() + 5).name() == "#1e1e1e"
