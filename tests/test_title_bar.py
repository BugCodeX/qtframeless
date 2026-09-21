"""Unit and integration tests for TitleBar features and vector button controls.

Covers vector button rendering, painting, event filtering, modular center container hosting,
intelligent drag hit-testing, menu bar integration, and dynamic theme adaptation.
"""

from unittest.mock import MagicMock

from qtpy.QtCore import QEvent, QPoint, QPointF, Qt, Signal
from qtpy.QtGui import (
    QColor,
    QFont,
    QIcon,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPalette,
    QPixmap,
)
from qtpy.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QMenuBar,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from qtframelesskit.windows.title_bar import (
    CloseButton,
    FullScreenButton,
    MaximizeButton,
    MenuStyler,
    MinimizeButton,
    TitleBar,
    TitleBarDragHandler,
    VectorButton,
)
from qtframelesskit.windows.window import FramelessMainWindow


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
    import qtframelesskit.windows.buttons as buttonsModule
    import qtframelesskit.windows.title_bar as titleBarModule

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


def test_vector_buttons_creation_and_paint(qtbot):
    """Verify vector buttons instantiate and render non-empty glyphs without error.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    parent = QWidget()
    qtbot.addWidget(parent)

    minButton = MinimizeButton(parent)
    maxButton = MaximizeButton(parent)
    closeButton = CloseButton(parent)

    for button in (minButton, maxButton, closeButton):
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
    """Verify MaximizeButton toggles maximized glyph state.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    parent = QWidget()
    qtbot.addWidget(parent)

    maxButton = MaximizeButton(parent)
    assert not maxButton.isMaximizedState()

    maxButton.setMaximizedState(True)
    assert maxButton.isMaximizedState()

    maxButton.setMaximizedState(False)
    assert not maxButton.isMaximizedState()


def test_titlebar_title_and_font(qtbot):
    """Verify TitleBar title text and font updates.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    titleBar.setTitle("Test Title")
    assert titleBar.getTitle().text() == "Test Title"

    customFont = QFont("Arial", 14)
    titleBar.setTitleBarFont(customFont)
    assert titleBar.getTitle().font().pointSize() == 14


def test_titlebar_icon_and_size(qtbot):
    """Verify TitleBar icon and size updates.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    # Create dummy icon pixmap
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor("blue"))
    icon = QIcon(pixmap)

    titleBar.setIcon(icon)
    titleBar.setIconSize(24, 24)

    iconPixmap = titleBar.getIcon().pixmap()
    assert not iconPixmap.isNull()
    assert iconPixmap.width() == 24
    assert iconPixmap.height() == 24


def test_titlebar_hints_configuration(qtbot):
    """Verify TitleBar hint controls button visibility.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)

    titleBar = TitleBar(window, hint=["min", "close"])
    buttons = titleBar.getButtons()

    assert not buttons["min"].isHidden()
    assert not buttons["close"].isHidden()
    assert buttons["max"].isHidden()

    # Default hint shows standard buttons
    defaultTitleBar = TitleBar(window, hint=None)
    defaultButtons = defaultTitleBar.getButtons()
    assert not defaultButtons["min"].isHidden()
    assert not defaultButtons["max"].isHidden()
    assert not defaultButtons["close"].isHidden()


def test_titlebar_event_filter_window_state_change(qtbot):
    """Verify TitleBar eventFilter reacts to QEvent.Type.WindowStateChange.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    # Simulate maximized state change event
    window.setWindowState(Qt.WindowState.WindowMaximized)
    event = QEvent(QEvent.Type.WindowStateChange)
    titleBar.eventFilter(window, event)

    maxButton = titleBar.getButtons()["max"]
    assert isinstance(maxButton, MaximizeButton)
    assert maxButton.isMaximizedState()


def test_titlebar_event_filter_layout_request(qtbot):
    """Verify TitleBar eventFilter clamps maximum height on QEvent.Type.LayoutRequest.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    event = QEvent(QEvent.Type.LayoutRequest)
    titleBar.eventFilter(window, event)
    assert titleBar.maximumHeight() == titleBar.sizeHint().height()


def test_fullscreen_button_and_event_filter(qtbot):
    """Verify FullScreenButton toggles and eventFilter hides/shows title bar.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window, hint=["full_screen", "min", "max", "close"])

    fullscreenButton = titleBar.getButtons()["full_screen"]
    pixmap = QPixmap(fullscreenButton.size())
    pixmap.fill(Qt.GlobalColor.transparent)
    fullscreenButton.render(pixmap)
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
    titleBar.eventFilter(window, event)
    assert fullscreenButton.isChecked()
    assert titleBar.isHidden()

    # Trigger normal state event
    window.setWindowState(Qt.WindowState.WindowNoState)
    titleBar.eventFilter(window, event)
    assert not fullscreenButton.isChecked()
    assert not titleBar.isHidden()


def test_titlebar_base_widget_kwarg(qtbot):
    """Verify legacy base_widget keyword argument works.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(base_widget=window)
    assert titleBar.parent() == window


def test_titlebar_resizable_toggle(qtbot):
    """Verify setBaseWindowResizable toggles maximize button visibility.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    titleBar = TitleBar(window)

    maxButton = titleBar.getButtons()["max"]
    assert not maxButton.isHidden()

    titleBar.setBaseWindowResizable(False)
    assert maxButton.isHidden()

    titleBar.setBaseWindowResizable(True)
    assert not maxButton.isHidden()


def test_titlebar_double_click_maximize(qtbot):
    """Verify double clicking TitleBar triggers maximize/restore on window.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(300, 200)
    window.show()
    titleBar = TitleBar(window)

    # Double click with left button
    qtbot.mouseDClick(titleBar, Qt.MouseButton.LeftButton)
    assert window.isMaximized()

    qtbot.mouseDClick(titleBar, Qt.MouseButton.LeftButton)
    assert not window.isMaximized()


def test_maximize_button_vector_painting_normal_and_restore(qtbot, monkeypatch):
    """Verify MaximizeButton paints single rectangle when normal and dual rectangles when maximized.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    monkeypatch : pytest.MonkeyPatch
        Pytest fixture for monkeypatching methods.
    """
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
        "qtframelesskit.windows.buttons.QPainter",
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
        "qtframelesskit.windows.buttons.QPainter",
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

    # 4. MinimizeButton glyph color in normal vs hover state
    mockPainterMinNormal = MagicMock()
    mockClassMin = MagicMock(return_value=mockPainterMinNormal)
    mockClassMin.RenderHint = QPainter.RenderHint
    monkeypatch.setattr(
        "qtframelesskit.windows.buttons.QPainter",
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

    # 5. CloseButton glyph color in normal, hover, and pressed states
    mockPainterCloseNormal = MagicMock()
    mockClassClose = MagicMock(return_value=mockPainterCloseNormal)
    mockClassClose.RenderHint = QPainter.RenderHint
    monkeypatch.setattr(
        "qtframelesskit.windows.buttons.QPainter",
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


def test_titlebar_subpackage_direct_exports() -> None:
    """Verify MenuStyler and TitleBarDragHandler are exported and listed in __all__.

    Ensures both MenuStyler and TitleBarDragHandler are available directly from
    the title_bar subpackage and match their internal module definitions.
    """
    import qtframelesskit.windows.title_bar as titleBarModule
    from qtframelesskit.windows.title_bar.drag_handler import (
        TitleBarDragHandler as ModularTitleBarDragHandler,
    )
    from qtframelesskit.windows.title_bar.menu_styler import (
        MenuStyler as ModularMenuStyler,
    )

    assert hasattr(titleBarModule, "MenuStyler")
    assert titleBarModule.MenuStyler is ModularMenuStyler
    assert "MenuStyler" in titleBarModule.__all__

    assert hasattr(titleBarModule, "TitleBarDragHandler")
    assert titleBarModule.TitleBarDragHandler is ModularTitleBarDragHandler
    assert "TitleBarDragHandler" in titleBarModule.__all__


def test_menu_styler_isolated_styling(qtbot):
    """Verify MenuStyler applies Fluent styles to standalone QMenuBar with DPI scaling.

    Tests both light and dark theme palettes along with standard, high, and fallback
    dots-per-inch scaling factors to ensure correct QSS padding and colors are set.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    menuBar = QMenuBar()
    qtbot.addWidget(menuBar)

    # 1. Light theme with standard 96 DPI
    MenuStyler.applyFluentMenuStyle(menuBar, isDark=False, dpi=96)
    lightStyleSheet = menuBar.styleSheet()
    assert "padding: 0px 0px 0px 8px;" in lightStyleSheet
    assert "background: transparent;" in lightStyleSheet
    assert "color: #000000;" in lightStyleSheet
    assert "background-color: #f9f9f9;" in lightStyleSheet
    assert "border: 1px solid rgba(0, 0, 0, 0.12);" in lightStyleSheet

    # 2. Dark theme with standard 96 DPI
    MenuStyler.applyFluentMenuStyle(menuBar, isDark=True, dpi=96)
    darkStyleSheet = menuBar.styleSheet()
    assert "padding: 0px 0px 0px 8px;" in darkStyleSheet
    assert "background: transparent;" in darkStyleSheet
    assert "color: #ffffff;" in darkStyleSheet
    assert "background-color: #2c2c2c;" in darkStyleSheet
    assert "background-color: #0078d4;" in darkStyleSheet
    assert "border: 1px solid rgba(255, 255, 255, 0.15);" in darkStyleSheet

    # 3. DPI scaling at 144 DPI (1.5x scale -> 12px left padding)
    MenuStyler.applyFluentMenuStyle(menuBar, isDark=False, dpi=144)
    assert "padding: 0px 0px 0px 12px;" in menuBar.styleSheet()

    # 4. DPI scaling at 192 DPI (2.0x scale -> 16px left padding)
    MenuStyler.applyFluentMenuStyle(menuBar, isDark=True, dpi=192)
    assert "padding: 0px 0px 0px 16px;" in menuBar.styleSheet()

    # 5. Non-positive DPI fallback defaults to 96 DPI (8px left padding)
    MenuStyler.applyFluentMenuStyle(menuBar, isDark=False, dpi=0)
    assert "padding: 0px 0px 0px 8px;" in menuBar.styleSheet()

    MenuStyler.applyFluentMenuStyle(menuBar, isDark=False, dpi=-10)
    assert "padding: 0px 0px 0px 8px;" in menuBar.styleSheet()


def test_drag_handler_isolated_hit_testing(qtbot):
    """Verify TitleBarDragHandler hit-testing detects interactive child widgets and menus.

    Tests center widget, nested child, and menu bar identification as interactive
    elements while treating non-interactive labels and background areas as draggable.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(800, 400)
    window.show()

    titleBar = TitleBar(window)
    titleBar.resize(800, 40)
    titleBar.show()

    dragHandler = TitleBarDragHandler(titleBar)

    # 1. Background areas and non-interactive title labels return False
    backgroundPosition = QPoint(60, 20)
    assert dragHandler.isInteractiveChild(None, backgroundPosition) is False

    titleLabel = titleBar.getTitle()
    assert dragHandler.isInteractiveChild(titleLabel, backgroundPosition) is False

    iconLabel = titleBar.getIcon()
    assert dragHandler.isInteractiveChild(iconLabel, backgroundPosition) is False

    # 2. Center widget installed: center widget and its nested children return True
    centerContainer = QWidget(titleBar)
    centerContainer.setGeometry(200, 5, 300, 30)
    nestedEditor = QLineEdit(centerContainer)
    nestedEditor.setGeometry(10, 5, 200, 20)
    titleBar.setCenterWidget(centerContainer)

    centerPosition = QPoint(250, 20)
    assert dragHandler.isInteractiveChild(centerContainer, centerPosition) is True
    assert dragHandler.isInteractiveChild(nestedEditor, centerPosition) is True

    # Interaction outside center widget remains non-interactive
    assert dragHandler.isInteractiveChild(None, backgroundPosition) is False
    assert dragHandler.isInteractiveChild(titleLabel, backgroundPosition) is False

    # 3. Menu bar installed: menu bar widget, nested child, and contained point return True
    menuBar = QMenuBar(titleBar)
    menuBar.addMenu("File")
    titleBar.setMenuBar(menuBar)
    titleBar.layout().activate()

    menuBarCenter = menuBar.geometry().center()
    assert dragHandler.isInteractiveChild(menuBar, menuBarCenter) is True
    assert dragHandler.isInteractiveChild(None, menuBarCenter) is True

    nestedMenuWidget = QWidget(menuBar)
    assert dragHandler.isInteractiveChild(nestedMenuWidget, menuBarCenter) is True

    # 4. Detaching center widget and menu bar restores non-interactive state
    titleBar.removeCenterWidget()
    titleBar.removeMenuBar()

    assert dragHandler.isInteractiveChild(centerContainer, centerPosition) is False
    assert dragHandler.isInteractiveChild(nestedEditor, centerPosition) is False
    assert dragHandler.isInteractiveChild(menuBar, menuBarCenter) is False
    assert dragHandler.isInteractiveChild(None, menuBarCenter) is False
