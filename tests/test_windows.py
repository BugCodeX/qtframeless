"""Tests for BaseWidget, BaseDialog, BaseMainWindow and Frameless variants."""

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QMainWindow, QWidget

from qtframelesskit.core.frameless_mixin import FramelessWindowMixin
from qtframelesskit.windows import FramelessDialog, FramelessMainWindow, FramelessWidget
from qtframelesskit.windows.base_widget import BaseDialog, BaseMainWindow, BaseWidget


def test_base_widget_inheritance_and_features(qtbot):
    """Verify BaseWidget inherits from QWidget and FramelessWindowMixin."""
    widget = BaseWidget()
    qtbot.addWidget(widget)

    assert isinstance(widget, QWidget)
    assert isinstance(widget, FramelessWindowMixin)
    assert bool(widget.windowFlags() & Qt.WindowType.FramelessWindowHint)


def test_base_dialog_inheritance_and_modality(qtbot):
    """Verify BaseDialog inherits from QDialog and FramelessWindowMixin."""
    dialog = BaseDialog()
    qtbot.addWidget(dialog)

    assert isinstance(dialog, QDialog)
    assert isinstance(dialog, FramelessWindowMixin)
    assert bool(dialog.windowFlags() & Qt.WindowType.FramelessWindowHint)


def test_base_main_window_inheritance(qtbot):
    """Verify BaseMainWindow inherits from QMainWindow and FramelessWindowMixin."""
    mainWindow = BaseMainWindow()
    qtbot.addWidget(mainWindow)

    assert isinstance(mainWindow, QMainWindow)
    assert isinstance(mainWindow, FramelessWindowMixin)
    assert bool(mainWindow.windowFlags() & Qt.WindowType.FramelessWindowHint)


def test_frameless_widget_layout_composition(qtbot):
    """Verify FramelessWidget composition integrates TitleBar in layout."""
    widget = FramelessWidget()
    qtbot.addWidget(widget)

    assert widget.layout() is not None
    assert widget.getTitleBar() is not None
    assert widget.getTitleBar().parent() == widget


def test_frameless_dialog_layout_composition(qtbot):
    """Verify FramelessDialog composition integrates TitleBar in layout."""
    dialog = FramelessDialog()
    qtbot.addWidget(dialog)

    assert dialog.layout() is not None
    assert dialog.getTitleBar() is not None


def test_frameless_main_window_central_widget(qtbot):
    """Verify FramelessMainWindow integrates TitleBar into central widget layout."""
    mainWindow = FramelessMainWindow()
    qtbot.addWidget(mainWindow)

    assert mainWindow.centralWidget() is not None
    assert mainWindow.centralWidget().layout() is not None
    assert mainWindow.getTitleBar() is not None


def test_windows_signal_compatibility(qtbot):
    """Verify darkThemeChanged and changedToDark signals on window classes."""
    widget = FramelessWidget()
    qtbot.addWidget(widget)

    assert hasattr(widget, "darkThemeChanged")
    assert hasattr(widget, "changedToDark")

    received = []
    widget.darkThemeChanged.connect(lambda dark: received.append(dark))
    widget.darkThemeChanged.emit(True)
    assert received == [True]


def test_frameless_widget_with_custom_hints(qtbot):
    """Verify FramelessWidget initializes with customized button hints."""
    widget = FramelessWidget(hint=["min", "close"])
    qtbot.addWidget(widget)

    buttons = widget.getTitleBar().getButtons()
    assert not buttons["min"].isHidden()
    assert not buttons["close"].isHidden()
    assert buttons["max"].isHidden()


def test_base_frameless_windows_pure_opaque_no_window_effect(qtbot):
    """Verify FramelessWindow, FramelessMainWindow, and FramelessDialog are pure opaque.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    from qtframelesskit import FramelessDialog, FramelessMainWindow, FramelessWindow

    window = FramelessWindow()
    mainWindow = FramelessMainWindow()
    dialog = FramelessDialog()

    qtbot.addWidget(window)
    qtbot.addWidget(mainWindow)
    qtbot.addWidget(dialog)

    for item in (window, mainWindow, dialog):
        assert item.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is False
        assert item._shouldExtendFrame() is True
        assert not hasattr(item, "setWindowEffect")
        assert not hasattr(item, "windowEffect")
        assert not hasattr(item, "windowEffectChanged")


def test_setup_frameless_layout_default_container(qtbot):
    """Verify _setupFramelessLayout configures zero-margin QVBoxLayout with title bar.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    from qtpy.QtWidgets import QVBoxLayout, QWidget

    from qtframelesskit.windows import _setupFramelessLayout
    from qtframelesskit.windows.title_bar import TitleBar

    containerWidget = QWidget()
    qtbot.addWidget(containerWidget)
    titleBar = TitleBar(containerWidget)

    _setupFramelessLayout(containerWidget, titleBar)

    layout = containerWidget.layout()
    assert isinstance(layout, QVBoxLayout)
    assert layout.count() >= 1
    assert layout.itemAt(0).widget() == titleBar
    margins = layout.contentsMargins()
    assert (margins.left(), margins.top(), margins.right(), margins.bottom()) == (0, 0, 0, 0)
    assert layout.spacing() == 0


def test_setup_frameless_layout_preserves_custom_layout(qtbot):
    """Verify _setupFramelessLayout preserves pre-configured custom layout.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    from qtpy.QtWidgets import QHBoxLayout, QWidget

    from qtframelesskit.windows import _setupFramelessLayout
    from qtframelesskit.windows.title_bar import TitleBar

    containerWidget = QWidget()
    qtbot.addWidget(containerWidget)
    customLayout = QHBoxLayout()
    containerWidget.setLayout(customLayout)
    titleBar = TitleBar(containerWidget)

    _setupFramelessLayout(containerWidget, titleBar)

    assert containerWidget.layout() is customLayout


def test_setup_frameless_layout_missing_title_bar(qtbot):
    """Verify _setupFramelessLayout does not assign layout when title bar is None.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    from qtpy.QtWidgets import QWidget

    from qtframelesskit.windows import _setupFramelessLayout

    containerWidget = QWidget()
    qtbot.addWidget(containerWidget)

    _setupFramelessLayout(containerWidget, None)

    assert containerWidget.layout() is None


def test_root_exports_for_dedicated_material_classes():
    """Verify all new material window classes and mixins are exported at root package level."""
    import qtframelesskit

    expectedExports = [
        "AcrylicWindowMixin",
        "FramelessAcrylicDialog",
        "FramelessAcrylicMainWindow",
        "FramelessAcrylicWindow",
        "FramelessDialog",
        "FramelessMainWindow",
        "FramelessMicaDialog",
        "FramelessMicaMainWindow",
        "FramelessMicaWindow",
        "FramelessWidget",
        "FramelessWindow",
        "MicaWindowMixin",
    ]

    for exportName in expectedExports:
        assert hasattr(qtframelesskit, exportName), f"Missing export: {exportName}"
        assert exportName in qtframelesskit.__all__, f"Missing in __all__: {exportName}"
