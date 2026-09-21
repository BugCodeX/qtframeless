"""Unit and integration tests for modern modular TitleBar features.

Covers modular center container hosting, intelligent drag hit-testing,
and dynamic parent theme adaptation.
"""

from unittest.mock import MagicMock

from qtpy.QtCore import QEvent, QPointF, Qt, Signal
from qtpy.QtGui import QColor, QFont, QMouseEvent, QPalette
from qtpy.QtWidgets import (
    QLabel,
    QLineEdit,
    QMenuBar,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from qtframeless.windows.title_bar import TitleBar, VectorButton
from qtframeless.windows.window import FramelessMainWindow


def test_titlebar_initial_center_widget_is_none(qtbot):
    """Verify that a freshly initialized TitleBar has no center widget installed.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    assert titleBar.getCenterWidget() is None


def test_titlebar_set_center_widget_installs_and_retrieves(qtbot):
    """Verify setCenterWidget installs a custom widget with expanding size policy.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    customWidget = QLabel("Search Bar", titleBar)
    titleBar.setCenterWidget(customWidget)

    retrievedWidget = titleBar.getCenterWidget()
    assert retrievedWidget is customWidget
    assert retrievedWidget.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding


def test_titlebar_set_center_widget_replaces_existing(qtbot):
    """Verify setCenterWidget removes the old widget when replacing it with a new one.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    firstWidget = QLabel("First", titleBar)
    secondWidget = QLineEdit(titleBar)

    titleBar.setCenterWidget(firstWidget)
    assert titleBar.getCenterWidget() is firstWidget

    titleBar.setCenterWidget(secondWidget)
    assert titleBar.getCenterWidget() is secondWidget
    assert firstWidget.parent() is None


def test_titlebar_remove_center_widget_detaches_without_destruction(qtbot):
    """Verify removeCenterWidget detaches the widget, returns it, and leaves it intact.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    customWidget = QLabel("Detachable", titleBar)
    titleBar.setCenterWidget(customWidget)

    removedWidget = titleBar.removeCenterWidget()
    assert removedWidget is customWidget
    assert titleBar.getCenterWidget() is None
    assert removedWidget.parent() is None

    # Removing again when empty returns None
    assert titleBar.removeCenterWidget() is None


def test_titlebar_set_center_widget_none_clears(qtbot):
    """Verify setCenterWidget with None clears the center widget.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    customWidget = QLabel("Temporary", titleBar)
    titleBar.setCenterWidget(customWidget)
    assert titleBar.getCenterWidget() is customWidget

    titleBar.setCenterWidget(None)
    assert titleBar.getCenterWidget() is None


def test_mouse_press_on_background_and_labels_initiates_system_move(qtbot, monkeypatch):
    """Verify left mouse click on background and labels triggers startSystemMove.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest fixture for monkeypatching methods.
    """
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(600, 400)
    window.show()

    titleBar = TitleBar(window)
    titleBar.resize(600, 40)
    titleBar.setTitle("My Title")
    titleBar.show()

    mockWindowHandle = MagicMock()
    monkeypatch.setattr(window, "windowHandle", lambda: mockWindowHandle)

    # 1. Click on empty background area of title bar
    qtbot.mouseClick(titleBar, Qt.MouseButton.LeftButton, pos=titleBar.rect().center())
    assert mockWindowHandle.startSystemMove.call_count == 1

    # 2. Click on title label
    mockWindowHandle.reset_mock()
    titleLabel = titleBar.getTitle()
    qtbot.mouseClick(titleLabel, Qt.MouseButton.LeftButton)
    assert mockWindowHandle.startSystemMove.call_count == 1

    # 3. Click on icon label
    mockWindowHandle.reset_mock()
    iconLabel = titleBar.getIcon()
    qtbot.mouseClick(iconLabel, Qt.MouseButton.LeftButton)
    assert mockWindowHandle.startSystemMove.call_count == 1


def test_mouse_press_on_center_interactive_widget_bypasses_system_move(qtbot, monkeypatch):
    """Verify left click on interactive center widget does not call startSystemMove.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest fixture for monkeypatching methods.
    """
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(600, 400)
    window.show()

    titleBar = TitleBar(window)
    titleBar.resize(600, 40)

    centerEditor = QLineEdit(titleBar)
    titleBar.setCenterWidget(centerEditor)
    titleBar.show()
    centerEditor.show()
    centerEditor.setGeometry(100, 5, 200, 30)

    mockWindowHandle = MagicMock()
    monkeypatch.setattr(window, "windowHandle", lambda: mockWindowHandle)

    # Click directly on TitleBar at coordinate where centerEditor resides
    editorCenter = centerEditor.geometry().center()
    pressEvent = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(editorCenter),
        QPointF(editorCenter),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    titleBar.mousePressEvent(pressEvent)
    assert mockWindowHandle.startSystemMove.call_count == 0


def test_mouse_press_disabled_when_press_to_move_false(qtbot, monkeypatch):
    """Verify system move is not initiated when pressToMove is disabled.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest fixture for monkeypatching methods.
    """
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(600, 400)
    window.show()

    titleBar = TitleBar(window)
    titleBar.setPressToMove(False)

    mockWindowHandle = MagicMock()
    monkeypatch.setattr(window, "windowHandle", lambda: mockWindowHandle)

    qtbot.mouseClick(titleBar, Qt.MouseButton.LeftButton, pos=titleBar.rect().center())
    assert mockWindowHandle.startSystemMove.call_count == 0


def test_mouse_double_click_on_center_interactive_widget_does_not_maximize(qtbot):
    """Verify double clicking an interactive center widget does not toggle maximize.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(600, 400)
    window.show()

    titleBar = TitleBar(window)
    titleBar.resize(600, 40)

    centerEditor = QLineEdit(titleBar)
    titleBar.setCenterWidget(centerEditor)
    titleBar.show()
    centerEditor.show()
    centerEditor.setGeometry(100, 5, 200, 30)

    assert not window.isMaximized()

    # Double click on TitleBar at coordinates of interactive QLineEdit
    editorCenter = centerEditor.geometry().center()
    dclickEvent = QMouseEvent(
        QEvent.Type.MouseButtonDblClick,
        QPointF(editorCenter),
        QPointF(editorCenter),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    titleBar.mouseDoubleClickEvent(dclickEvent)
    assert not window.isMaximized()

    # Double click on TitleBar title label DOES maximize
    titleLabelCenter = QPointF(titleBar.getTitle().geometry().center())
    titleDclickEvent = QMouseEvent(
        QEvent.Type.MouseButtonDblClick,
        titleLabelCenter,
        titleLabelCenter,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    titleBar.mouseDoubleClickEvent(titleDclickEvent)
    assert window.isMaximized()


def test_vector_button_set_dark_theme(qtbot):
    """Verify VectorButton setDarkTheme toggles stroke colors and targets.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    button = VectorButton()
    qtbot.addWidget(button)

    # Initial light mode state
    assert button.styleSheet() == ""
    assert button.getGlyphColor().name() == "#333333"
    assert button.getHoverColor() == QColor("#cfcfcf")

    # Switch to dark theme
    button.setDarkTheme(True)
    assert button.styleSheet() == ""
    assert button.getGlyphColor().name() == "#ffffff"
    assert button.getHoverColor() == QColor("#3f3f3f")

    # Switch back to light theme
    button.setDarkTheme(False)
    assert button.styleSheet() == ""
    assert button.getGlyphColor().name() == "#333333"
    assert button.getHoverColor() == QColor("#cfcfcf")


def test_titlebar_safe_initialization_without_dark_theme_signal(qtbot):
    """Verify TitleBar initializes safely with a parent lacking darkThemeChanged signal.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    plainParent = QWidget()
    qtbot.addWidget(plainParent)

    assert not hasattr(plainParent, "darkThemeChanged")
    titleBar = TitleBar(plainParent)
    assert titleBar.parent() is plainParent


def test_titlebar_handle_theme_changed_updates_labels_and_buttons(qtbot):
    """Verify _handleThemeChanged updates label palette colors and button stroke colors.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    # Transition to dark theme
    titleBar._handleThemeChanged(True)
    assert titleBar.getTitle().palette().color(QPalette.ColorRole.WindowText).name() == "#ffffff"
    assert titleBar.getTitle().styleSheet() == ""
    assert titleBar.getIcon().styleSheet() == ""
    for button in titleBar.getButtons().values():
        assert button.getGlyphColor().name() == "#ffffff"

    # Revert to light theme
    titleBar._handleThemeChanged(False)
    assert titleBar.getTitle().palette().color(QPalette.ColorRole.WindowText).name() == "#000000"
    assert titleBar.getTitle().styleSheet() == ""
    assert titleBar.getIcon().styleSheet() == ""
    for button in titleBar.getButtons().values():
        assert button.getGlyphColor().name() == "#333333"


def test_titlebar_observes_parent_dark_theme_changed_signal(qtbot):
    """Verify TitleBar automatically subscribes to parent darkThemeChanged signal.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """

    class MockThemedWindow(QWidget):
        darkThemeChanged = Signal(bool)

    window = MockThemedWindow()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    # Emitting darkThemeChanged on parent updates TitleBar
    window.darkThemeChanged.emit(True)
    assert titleBar.getTitle().palette().color(QPalette.ColorRole.WindowText).name() == "#ffffff"
    for button in titleBar.getButtons().values():
        assert button.getGlyphColor().name() == "#ffffff"

    window.darkThemeChanged.emit(False)
    assert titleBar.getTitle().palette().color(QPalette.ColorRole.WindowText).name() == "#000000"
    for button in titleBar.getButtons().values():
        assert button.getGlyphColor().name() == "#333333"


def test_frameless_window_set_dark_theme_updates_titlebar(qtbot):
    """Verify calling setDarkTheme on FramelessMainWindow dynamically updates title bar.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    from qtframeless import FramelessMainWindow

    window = FramelessMainWindow()
    qtbot.addWidget(window)
    titleBar = window.getTitleBar()
    assert titleBar is not None

    # Manually activate dark theme on window
    window.setDarkTheme(True)
    assert window.isDarkTheme()
    assert titleBar.isDarkTheme()
    assert titleBar.getTitle().palette().color(QPalette.ColorRole.WindowText).name() == "#ffffff"
    for button in titleBar.getButtons().values():
        assert button.getGlyphColor().name() == "#ffffff"

    # Manually activate light theme on window
    window.setDarkTheme(False)
    assert not window.isDarkTheme()
    assert not titleBar.isDarkTheme()
    assert titleBar.getTitle().palette().color(QPalette.ColorRole.WindowText).name() == "#000000"
    for button in titleBar.getButtons().values():
        assert button.getGlyphColor().name() == "#333333"


def test_titlebar_update_dpi_scaling_buttons(qtbot):
    """Verify updateDpiScaling scales vector control button dimensions proportionally.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    # Scale to 144 DPI (1.5x)
    titleBar.updateDpiScaling(144)
    buttons = titleBar.getButtons()
    for button in buttons.values():
        assert button.height() == 45
        assert button.width() == 63

    # Scale to 192 DPI (2.0x)
    titleBar.updateDpiScaling(192)
    for button in buttons.values():
        assert button.height() == 60
        assert button.width() == 84


def test_titlebar_update_dpi_scaling_icon_pixmap(qtbot):
    """Verify updateDpiScaling re-renders window icon pixmap at scaled dimensions.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    from qtpy.QtGui import QColor, QIcon, QPixmap

    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor("blue"))
    titleBar.setIcon(QIcon(pixmap))

    # Base size at 96 DPI is 18x18
    assert titleBar.getIcon().pixmap().width() == 18
    assert titleBar.getIcon().pixmap().height() == 18

    # Scale to 144 DPI (1.5x) -> 27x27
    titleBar.updateDpiScaling(144)
    assert titleBar.getIcon().pixmap().width() == 27
    assert titleBar.getIcon().pixmap().height() == 27

    # Scale to 192 DPI (2.0x) -> 36x36
    titleBar.updateDpiScaling(192)
    assert titleBar.getIcon().pixmap().width() == 36
    assert titleBar.getIcon().pixmap().height() == 36


def test_titlebar_update_dpi_scaling_margins_and_size_hint(qtbot):
    """Verify updateDpiScaling recomputes layout and label contentsMargins.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    layout = titleBar.layout()
    assert layout is not None
    assert layout.contentsMargins().left() == 8

    titleBar.updateDpiScaling(144)
    assert layout.contentsMargins().left() == 12
    margins = titleBar.getTitle().contentsMargins()
    assert margins.left() == 6
    assert margins.top() == 6
    assert margins.right() == 6
    assert margins.bottom() == 6

    iconMargins = titleBar.getIcon().contentsMargins()
    assert iconMargins.left() == 6
    assert iconMargins.top() == 6
    assert iconMargins.right() == 6
    assert iconMargins.bottom() == 6

    assert titleBar.getTitle().styleSheet() == ""
    assert titleBar.getIcon().styleSheet() == ""
    assert titleBar.maximumHeight() == titleBar.sizeHint().height()


def test_vector_button_glyph_scaling_factor(qtbot):
    """Verify VectorButton glyph scaling factor scales with button height.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    button = VectorButton()
    qtbot.addWidget(button)

    # Standard height 30px -> scale factor 1.0
    assert button.getGlyphScaleFactor() == 1.0

    # High DPI (150% -> height 45px, raw ratio 1.5 -> dampened: 1.0 + 0.5 * 0.25 = 1.125)
    button.updateButtonHeight(45)
    assert button.getGlyphScaleFactor() == 1.125

    # 200% scaling (height 60px, raw ratio 2.0 -> dampened: 1.0 + 1.0 * 0.25 = 1.25)
    button.updateButtonHeight(60)
    assert button.getGlyphScaleFactor() == 1.25


def test_titlebar_title_font_dpi_scaling(qtbot):
    """Verify TitleBar title label font scales with DPI updates.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    customFont = QFont("Segoe UI", 10)
    titleBar.setTitleBarFont(customFont)
    initialPointSize = titleBar.getTitle().font().pointSizeF()
    assert initialPointSize == 10.0

    # 150% DPI scaling -> 10pt * 1.5 = 15pt
    titleBar.updateDpiScaling(144)
    assert titleBar.getTitle().font().pointSizeF() == 15.0

    # 200% DPI scaling -> 10pt * 2.0 = 20pt
    titleBar.updateDpiScaling(192)
    assert titleBar.getTitle().font().pointSizeF() == 20.0


def test_buttons_module_direct_imports() -> None:
    """Verify all vector button classes are directly importable from buttons module."""
    import qtframeless.windows.buttons as buttonsModule
    import qtframeless.windows.title_bar as titleBarModule

    assert buttonsModule.VectorButton is titleBarModule.VectorButton
    assert buttonsModule.MinimizeButton is titleBarModule.MinimizeButton
    assert buttonsModule.MaximizeButton is titleBarModule.MaximizeButton
    assert buttonsModule.CloseButton is titleBarModule.CloseButton
    assert buttonsModule.FullScreenButton is titleBarModule.FullScreenButton


def test_titlebar_initial_menubar_is_none(qtbot):
    """Verify that a freshly initialized TitleBar has no menu bar installed.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    assert titleBar.getMenuBar() is None
    assert titleBar.getTitleAlignment() == Qt.AlignmentFlag.AlignLeft
    assert titleBar.isAutoStyleMenuBar() is True


def test_titlebar_set_and_get_menubar(qtbot):
    """Verify setMenuBar installs QMenuBar after icon with Maximum horizontal policy.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    menuBar = QMenuBar(titleBar)
    titleBar.setMenuBar(menuBar)

    assert titleBar.getMenuBar() is menuBar
    assert menuBar.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Maximum
    assert menuBar.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Preferred

    layout = titleBar.layout()
    assert layout is not None
    iconIndex = layout.indexOf(titleBar.getIcon())
    menuBarIndex = layout.indexOf(menuBar)
    assert menuBarIndex == iconIndex + 1
    layoutItem = layout.itemAt(menuBarIndex)
    assert layoutItem is not None
    assert bool(layoutItem.alignment() & Qt.AlignmentFlag.AlignVCenter)


def test_titlebar_set_menubar_replaces_existing(qtbot):
    """Verify setMenuBar replaces the existing menu bar and detaches the previous one.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    firstMenuBar = QMenuBar(titleBar)
    secondMenuBar = QMenuBar(titleBar)

    titleBar.setMenuBar(firstMenuBar)
    assert titleBar.getMenuBar() is firstMenuBar

    titleBar.setMenuBar(secondMenuBar)
    assert titleBar.getMenuBar() is secondMenuBar
    assert firstMenuBar.parent() is None


def test_titlebar_remove_menubar(qtbot):
    """Verify removeMenuBar detaches the menu bar, reparents to None, and returns it.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    menuBar = QMenuBar(titleBar)
    titleBar.setMenuBar(menuBar)

    removedMenuBar = titleBar.removeMenuBar()
    assert removedMenuBar is menuBar
    assert titleBar.getMenuBar() is None
    assert removedMenuBar.parent() is None

    # Removing again when empty returns None
    assert titleBar.removeMenuBar() is None


def test_titlebar_set_menubar_none_clears(qtbot):
    """Verify setMenuBar with None detaches and removes the active menu bar.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    menuBar = QMenuBar(titleBar)
    titleBar.setMenuBar(menuBar)
    assert titleBar.getMenuBar() is menuBar

    titleBar.setMenuBar(None)
    assert titleBar.getMenuBar() is None


def test_titlebar_title_alignment(qtbot):
    """Verify setTitleAlignment toggles horizontal alignment and expanding size policies.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    # Initial state is AlignLeft with Preferred policy
    assert titleBar.getTitleAlignment() == Qt.AlignmentFlag.AlignLeft
    assert bool(titleBar.getTitle().alignment() & Qt.AlignmentFlag.AlignLeft)
    assert titleBar.getTitle().sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Preferred

    # Switch to AlignCenter
    titleBar.setTitleAlignment(Qt.AlignmentFlag.AlignCenter)
    assert titleBar.getTitleAlignment() == Qt.AlignmentFlag.AlignCenter
    assert bool(titleBar.getTitle().alignment() & Qt.AlignmentFlag.AlignCenter)
    assert titleBar.getTitle().sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding

    # Switch back to AlignLeft
    titleBar.setTitleAlignment(Qt.AlignmentFlag.AlignLeft)
    assert titleBar.getTitleAlignment() == Qt.AlignmentFlag.AlignLeft
    assert bool(titleBar.getTitle().alignment() & Qt.AlignmentFlag.AlignLeft)
    assert titleBar.getTitle().sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Preferred


def test_titlebar_menubar_autostyle_theme_switching(qtbot):
    """Verify theme switching applies dark and light Fluent styling to QMenuBar.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    menuBar = QMenuBar(titleBar)
    titleBar.setMenuBar(menuBar)

    # Light theme stylesheet checks
    titleBar.setDarkTheme(False)
    assert "#000000" in menuBar.styleSheet()
    assert "#f9f9f9" in menuBar.styleSheet()
    assert "padding: 0px 0px 0px 8px;" in menuBar.styleSheet()
    assert "margin: 0px;" in menuBar.styleSheet()
    assert "max-height" not in menuBar.styleSheet()
    assert "font-size: 13px;" in menuBar.styleSheet()
    assert "padding: 5px 10px;" in menuBar.styleSheet()
    assert "border-radius: 8px;" in menuBar.styleSheet()
    assert "padding: 6px 28px 6px 14px;" in menuBar.styleSheet()
    assert "rgba(0, 0, 0, 0.08)" in menuBar.styleSheet()

    # Dark theme stylesheet checks
    titleBar.setDarkTheme(True)
    assert "#ffffff" in menuBar.styleSheet()
    assert "#2c2c2c" in menuBar.styleSheet()
    assert "padding: 0px 0px 0px 8px;" in menuBar.styleSheet()
    assert "margin: 0px;" in menuBar.styleSheet()
    assert "max-height" not in menuBar.styleSheet()
    assert "font-size: 13px;" in menuBar.styleSheet()
    assert "padding: 5px 10px;" in menuBar.styleSheet()
    assert "border-radius: 8px;" in menuBar.styleSheet()
    assert "padding: 6px 28px 6px 14px;" in menuBar.styleSheet()
    assert "rgba(255, 255, 255, 0.1)" in menuBar.styleSheet()


def test_titlebar_menubar_autostyle_disabled(qtbot):
    """Verify disabling autoStyleMenuBar preserves custom stylesheets across theme changes.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    menuBar = QMenuBar(titleBar)
    titleBar.setMenuBar(menuBar)

    titleBar.setAutoStyleMenuBar(False)
    assert titleBar.isAutoStyleMenuBar() is False

    customStyleSheet = "QMenuBar { background: red; }"
    menuBar.setStyleSheet(customStyleSheet)

    titleBar.setDarkTheme(True)
    assert menuBar.styleSheet() == customStyleSheet

    # Re-enabling autoStyleMenuBar immediately reapplies the active theme styles
    titleBar.setAutoStyleMenuBar(True)
    assert titleBar.isAutoStyleMenuBar() is True
    assert "#2c2c2c" in menuBar.styleSheet()


def test_titlebar_menubar_translucent_attributes(qtbot):
    """Verify setMenuBar configures WA_TranslucentBackground and disables autoFillBackground.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    menuBar = QMenuBar(titleBar)
    titleBar.setMenuBar(menuBar)

    assert menuBar.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is True
    assert menuBar.autoFillBackground() is False


def test_titlebar_menubar_pre_styled_preservation(qtbot):
    """Verify pre-styled menu bar is preserved on setMenuBar and across theme changes.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    menuBar = QMenuBar(titleBar)
    customStyleSheet = "QMenuBar { background-color: purple; color: white; }"
    menuBar.setStyleSheet(customStyleSheet)

    titleBar.setMenuBar(menuBar)

    assert titleBar.isAutoStyleMenuBar() is False
    assert menuBar.styleSheet() == customStyleSheet
    assert menuBar.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is True
    assert menuBar.autoFillBackground() is False

    titleBar.setDarkTheme(True)
    assert menuBar.styleSheet() == customStyleSheet

    titleBar.setDarkTheme(False)
    assert menuBar.styleSheet() == customStyleSheet

    # Whitespace-only stylesheet is treated as un-styled and permits auto-styling
    unStyledMenuBar = QMenuBar(titleBar)
    unStyledMenuBar.setStyleSheet("   \n\t  ")
    unStyledTitleBar = TitleBar(window)
    unStyledTitleBar.setMenuBar(unStyledMenuBar)
    assert unStyledTitleBar.isAutoStyleMenuBar() is True
    assert "#000000" in unStyledMenuBar.styleSheet()


def test_titlebar_apply_fluent_menu_style_standalone(qtbot):
    """Verify TitleBar.applyFluentMenuStyle applies styles with DPI scaling independently.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    menuBar = QMenuBar(window)

    # Light theme at 96 DPI
    TitleBar.applyFluentMenuStyle(menuBar, isDark=False, dpi=96)
    assert "#000000" in menuBar.styleSheet()
    assert "#f9f9f9" in menuBar.styleSheet()
    assert "padding: 0px 0px 0px 8px;" in menuBar.styleSheet()
    assert "margin: 0px;" in menuBar.styleSheet()
    assert "max-height" not in menuBar.styleSheet()

    # Dark theme at 144 DPI (1.5x scale -> 8 * 1.5 = 12px padding)
    TitleBar.applyFluentMenuStyle(menuBar, isDark=True, dpi=144)
    assert "#ffffff" in menuBar.styleSheet()
    assert "#2c2c2c" in menuBar.styleSheet()
    assert "padding: 0px 0px 0px 12px;" in menuBar.styleSheet()
    assert "margin: 0px;" in menuBar.styleSheet()
    assert "max-height" not in menuBar.styleSheet()

    # 192 DPI (2.0x scale -> 8 * 2.0 = 16px padding)
    TitleBar.applyFluentMenuStyle(menuBar, isDark=True, dpi=192)
    assert "padding: 0px 0px 0px 16px;" in menuBar.styleSheet()
    assert "margin: 0px;" in menuBar.styleSheet()
    assert "max-height" not in menuBar.styleSheet()

    # Fallback when DPI is non-positive defaults to 96 DPI
    TitleBar.applyFluentMenuStyle(menuBar, isDark=False, dpi=0)
    assert "padding: 0px 0px 0px 8px;" in menuBar.styleSheet()
    assert "margin: 0px;" in menuBar.styleSheet()
    assert "max-height" not in menuBar.styleSheet()


def test_mouse_press_on_menubar_bypasses_system_move(qtbot, monkeypatch):
    """Verify left click on integrated QMenuBar does not initiate window drag.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest fixture for monkeypatching methods.
    """
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(700, 400)
    window.show()

    titleBar = TitleBar(window)
    titleBar.setTitle("Test Window Title")
    titleBar.resize(700, 40)

    menuBar = QMenuBar(titleBar)
    menuBar.addMenu("File")
    titleBar.setMenuBar(menuBar)
    titleBar.show()
    titleBar.layout().activate()

    mockWindowHandle = MagicMock()
    monkeypatch.setattr(window, "windowHandle", lambda: mockWindowHandle)

    # Click directly on TitleBar at coordinate where menuBar resides
    menuBarCenter = menuBar.geometry().center()
    pressEvent = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(menuBarCenter),
        QPointF(menuBarCenter),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    titleBar.mousePressEvent(pressEvent)
    assert mockWindowHandle.startSystemMove.call_count == 0


def test_mouse_double_click_on_menubar_does_not_maximize(qtbot):
    """Verify double clicking the integrated QMenuBar does not toggle window maximize.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(700, 400)
    window.show()

    titleBar = TitleBar(window)
    titleBar.setTitle("Test Window Title")
    titleBar.resize(700, 40)

    menuBar = QMenuBar(titleBar)
    menuBar.addMenu("File")
    titleBar.setMenuBar(menuBar)
    titleBar.show()
    titleBar.layout().activate()

    assert not window.isMaximized()

    # Double click on TitleBar at coordinates of QMenuBar
    menuBarCenter = menuBar.geometry().center()
    doubleClickEvent = QMouseEvent(
        QEvent.Type.MouseButtonDblClick,
        QPointF(menuBarCenter),
        QPointF(menuBarCenter),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    titleBar.mouseDoubleClickEvent(doubleClickEvent)
    assert not window.isMaximized()

    # Double click on title label DOES maximize
    titleLabelCenter = QPointF(titleBar.getTitle().geometry().center())
    titleDoubleClickEvent = QMouseEvent(
        QEvent.Type.MouseButtonDblClick,
        titleLabelCenter,
        titleLabelCenter,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    titleBar.mouseDoubleClickEvent(titleDoubleClickEvent)
    assert window.isMaximized()


def test_frameless_mainwindow_menubar_integration(qtbot):
    """Verify FramelessMainWindow seamlessly integrates menuBar() and setMenuBar().

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    mainWindow = FramelessMainWindow()
    qtbot.addWidget(mainWindow)

    titleBar = mainWindow.getTitleBar()
    assert titleBar is not None
    assert titleBar.getMenuBar() is None

    # menuBar() automatically creates and integrates QMenuBar into TitleBar
    menuBar = mainWindow.menuBar()
    assert isinstance(menuBar, QMenuBar)
    assert titleBar.getMenuBar() is menuBar

    # Repeated calls return the same instance
    assert mainWindow.menuBar() is menuBar

    # setMenuBar() replaces the active menu bar on TitleBar
    customMenuBar = QMenuBar()
    mainWindow.setMenuBar(customMenuBar)
    assert titleBar.getMenuBar() is customMenuBar
    assert mainWindow.menuBar() is customMenuBar


def test_corner_buttons_align_to_top_edge(qtbot):
    """Verify that title bar corner buttons align flush to the window top edge without gap.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    mainWindow = FramelessMainWindow()
    qtbot.addWidget(mainWindow)
    menuBar = mainWindow.menuBar()
    menuBar.addMenu("File")
    menuBar.addMenu("Edit")
    mainWindow.resize(800, 600)
    mainWindow.show()
    qtbot.waitExposed(mainWindow)

    titleBar = mainWindow.getTitleBar()
    assert titleBar is not None
    closeButton = titleBar.getButtons()["close"]
    assert closeButton.mapTo(mainWindow, closeButton.rect().topLeft()).y() == 0


def test_menubar_actions_visible_without_overflow_button(qtbot):
    """Verify menu bar actions remain visible without triggering the overflow extension button.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    mainWindow = FramelessMainWindow()
    qtbot.addWidget(mainWindow)

    menuBar = mainWindow.menuBar()
    fileMenu = menuBar.addMenu("File")
    fileMenu.addAction("New")
    editMenu = menuBar.addMenu("Edit")
    editMenu.addAction("Undo")
    settingsMenu = menuBar.addMenu("Settings")
    settingsMenu.addAction("Preferences")

    mainWindow.resize(850, 520)
    mainWindow.show()
    qtbot.waitExposed(mainWindow)

    overflowButton = menuBar.findChild(QToolButton, "qt_menubar_ext_button")
    if overflowButton is not None:
        assert overflowButton.isVisible() is False

    menuActions = menuBar.actions()
    assert len(menuActions) == 3
    for action in menuActions:
        assert action.isVisible() is True
        actionGeometry = menuBar.actionGeometry(action)
        assert actionGeometry.width() > 0
        assert actionGeometry.height() > 0
