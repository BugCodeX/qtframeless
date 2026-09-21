"""Tests verifying sample example windows run cleanly."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def test_example_widget_instantiation(qtbot):
    """Verify sample_widget pattern instantiates without errors."""
    from examples.sample_widget import Window

    window = Window()
    qtbot.addWidget(window)
    assert window.windowTitle() == "QtFrameless Widget"
    assert window.getTitleBar() is not None


def test_example_dialog_instantiation(qtbot):
    """Verify sample_dialog pattern instantiates without errors."""
    from examples.sample_dialog import Window

    window = Window()
    qtbot.addWidget(window)
    assert window.windowTitle() == "QtFrameless Dialog"


def test_example_mainwindow_instantiation(qtbot):
    """Verify sample_mainwindow pattern instantiates without errors."""
    from examples.sample_mainwindow import Window

    window = Window()
    qtbot.addWidget(window)
    assert window.windowTitle() == "QtFrameless MainWindow"
    assert window.centralWidget() is not None


def test_example_mainwindow_toggle_theme(qtbot):
    """Verify toggling dark theme in sample_mainwindow updates darkTheme and palette cleanly.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    from qtpy.QtGui import QPalette

    from examples.sample_mainwindow import Window

    window = Window()
    qtbot.addWidget(window)
    assert window.darkTheme is False
    assert window.palette().color(QPalette.ColorRole.Window).name().lower() == "#f3f3f3"
    titleBar = window.getTitleBar()
    assert titleBar is not None
    assert (
        titleBar.getTitle().palette().color(QPalette.ColorRole.WindowText).name().lower()
        == "#000000"
    )

    window._toggleTheme()
    assert window.darkTheme is True
    assert window.palette().color(QPalette.ColorRole.Window).name().lower() == "#202020"
    assert (
        titleBar.getTitle().palette().color(QPalette.ColorRole.WindowText).name().lower()
        == "#ffffff"
    )

    window._toggleTheme()
    assert window.darkTheme is False
    assert window.palette().color(QPalette.ColorRole.Window).name().lower() == "#f3f3f3"
    assert (
        titleBar.getTitle().palette().color(QPalette.ColorRole.WindowText).name().lower()
        == "#000000"
    )


def test_example_widget_toggle_theme(qtbot):
    """Verify toggling dark theme in sample_widget updates darkTheme and palette cleanly.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    from qtpy.QtGui import QPalette

    from examples.sample_widget import Window

    window = Window()
    qtbot.addWidget(window)
    assert window.darkTheme is False
    assert window.palette().color(QPalette.ColorRole.Window).name().lower() == "#f3f3f3"

    window._toggleTheme()
    assert window.darkTheme is True
    assert window.palette().color(QPalette.ColorRole.Window).name().lower() == "#202020"

    window._toggleTheme()
    assert window.darkTheme is False
    assert window.palette().color(QPalette.ColorRole.Window).name().lower() == "#f3f3f3"


def test_example_dialog_toggle_theme(qtbot):
    """Verify toggling dark theme in sample_dialog updates darkTheme and palette cleanly.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    from qtpy.QtGui import QPalette

    from examples.sample_dialog import Window

    window = Window()
    qtbot.addWidget(window)
    assert window.darkTheme is False
    assert window.palette().color(QPalette.ColorRole.Window).name().lower() == "#f3f3f3"

    window._toggleTheme()
    assert window.darkTheme is True
    assert window.palette().color(QPalette.ColorRole.Window).name().lower() == "#202020"

    window._toggleTheme()
    assert window.darkTheme is False
    assert window.palette().color(QPalette.ColorRole.Window).name().lower() == "#f3f3f3"


def test_example_modular_titlebar_instantiation(qtbot):
    """Verify sample_modular_titlebar pattern instantiates and configures center widget."""
    from examples.sample_modular_titlebar import ModularTitleBarWindow

    window = ModularTitleBarWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "QtFrameless Studio"
    titleBar = window.getTitleBar()
    assert titleBar is not None
    assert titleBar.getCenterWidget() is not None


def test_example_dpi_scaling_instantiation(qtbot):
    """Verify sample_dpi_scaling pattern instantiates and simulates DPI updates cleanly."""
    from examples.sample_dpi_scaling import DpiScalingDemoWindow

    window = DpiScalingDemoWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "Per-Monitor DPI Scaling Demo"
    titleBar = window.getTitleBar()
    assert titleBar is not None

    # Test interactive DPI scaling simulation
    window._simulateDpiChange(144)
    assert "144 DPI" in window._currentDpiLabel.text()


def test_example_materials_instantiation(qtbot):
    """Verify materials example windows (Mica, Mica Alt, Acrylic) instantiate cleanly."""
    from qtpy.QtCore import Qt

    from examples.materials.sample_acrylic import AcrylicWindow
    from examples.materials.sample_mica import MicaWindow
    from examples.materials.sample_mica_alt import MicaAltWindow
    from qtframelesskit import (
        FramelessAcrylicMainWindow,
        FramelessMicaMainWindow,
    )

    micaWindow = MicaWindow()
    qtbot.addWidget(micaWindow)
    assert isinstance(micaWindow, FramelessMicaMainWindow)
    assert micaWindow.windowTitle() == "Windows 11 Mica Material"
    assert micaWindow.isAlt() is False
    assert micaWindow.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is False

    micaAltWindow = MicaAltWindow()
    qtbot.addWidget(micaAltWindow)
    assert isinstance(micaAltWindow, FramelessMicaMainWindow)
    assert micaAltWindow.windowTitle() == "Windows 11 Mica Alt Material"
    assert micaAltWindow.isAlt() is True
    assert micaAltWindow.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is False

    acrylicWindow = AcrylicWindow()
    qtbot.addWidget(acrylicWindow)
    assert isinstance(acrylicWindow, FramelessAcrylicMainWindow)
    assert acrylicWindow.windowTitle() == "Windows Acrylic Material"
    assert acrylicWindow.getGradientColor() == "F2F2F299"
    assert acrylicWindow.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is False


def test_example_menubar_titlebar_instantiation_and_theme(qtbot):
    """Verify sample_menubar_titlebar pattern instantiates, configures menu bar, and toggles theme.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture for widget lifecycle management.
    """
    from qtpy.QtCore import Qt

    from examples.sample_menubar_titlebar import Window

    window = Window()
    qtbot.addWidget(window)
    assert window.windowTitle() == "Example MainWindow"

    titleBar = window.getTitleBar()
    assert titleBar is not None
    assert titleBar.getTitleAlignment() == Qt.AlignmentFlag.AlignCenter

    menuBar = titleBar.getMenuBar()
    assert menuBar is not None
    assert menuBar is window.menuBar()

    menuTitles = [action.text() for action in menuBar.actions()]
    assert "File(&F)" in menuTitles
    assert "Edit(&E)" in menuTitles
    assert "Settings(&S)" in menuTitles

    assert window.darkTheme is False
    assert titleBar.isDarkTheme() is False
    assert "#000000" in menuBar.styleSheet()

    window._toggleTheme()
    assert window.darkTheme is True
    assert titleBar.isDarkTheme() is True
    assert "#ffffff" in menuBar.styleSheet()
    assert "Switch to Light Theme" in window._themeToggleButton.text()

    window._toggleTheme()
    assert window.darkTheme is False
    assert titleBar.isDarkTheme() is False
    assert "#000000" in menuBar.styleSheet()
    assert "Switch to Dark Theme" in window._themeToggleButton.text()
