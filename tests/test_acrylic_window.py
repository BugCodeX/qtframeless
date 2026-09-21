"""Tests for FramelessAcrylicWindow, FramelessAcrylicMainWindow, and FramelessAcrylicDialog."""

from qtpy.QtCore import QEvent, Qt
from qtpy.QtGui import QColor, QPalette
from qtpy.QtWidgets import QWidget

from qtframeless.native.win32_utils import isGreaterEqualWin11
from qtframeless.windows.window import (
    AcrylicWindowMixin,
    FramelessAcrylicDialog,
    FramelessAcrylicMainWindow,
    FramelessAcrylicWindow,
    _configureTitleBarForMaterial,
)


def test_acrylic_window_initialization(qtbot, monkeypatch):
    """Verify FramelessAcrylicWindow initializes with class QSS and without translucent attribute.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    recordedEffects = []

    def fakeSetAcrylic(self, hWnd, gradientColor=None):
        recordedEffects.append((hWnd, gradientColor))
        return True

    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setAcrylicEffect",
        fakeSetAcrylic,
    )

    window = FramelessAcrylicWindow()
    qtbot.addWidget(window)

    # Must be instance of AcrylicWindowMixin and QWidget
    assert isinstance(window, AcrylicWindowMixin)
    assert isinstance(window, QWidget)

    # Class-specific QSS must set transparent background
    assert "FramelessAcrylicWindow" in window.styleSheet()
    assert "background: transparent;" in window.styleSheet()

    # Must NOT set WA_TranslucentBackground
    assert window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is False

    # Should match platform DWM frame extension capability
    assert window._shouldExtendFrame() is isGreaterEqualWin11()

    # Title bar hint if Qt >= 6.10
    if hasattr(Qt.WindowType, "NoTitleBarBackgroundHint"):
        assert bool(window.windowFlags() & Qt.WindowType.NoTitleBarBackgroundHint)

    # Helper should have been called
    assert len(recordedEffects) >= 1


def test_acrylic_main_window_initialization(qtbot, monkeypatch):
    """Verify FramelessAcrylicMainWindow integrates central widget and QSS.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setAcrylicEffect",
        lambda self, hWnd, gradientColor=None: True,
    )

    mainWindow = FramelessAcrylicMainWindow()
    qtbot.addWidget(mainWindow)

    assert isinstance(mainWindow, AcrylicWindowMixin)
    assert mainWindow.centralWidget() is not None
    assert "FramelessAcrylicMainWindow" in mainWindow.styleSheet()
    assert mainWindow.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is False
    assert mainWindow._shouldExtendFrame() is isGreaterEqualWin11()


def test_acrylic_dialog_initialization(qtbot, monkeypatch):
    """Verify FramelessAcrylicDialog initializes with Acrylic mixin and QSS.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setAcrylicEffect",
        lambda self, hWnd, gradientColor=None: True,
    )

    dialog = FramelessAcrylicDialog()
    qtbot.addWidget(dialog)

    assert isinstance(dialog, AcrylicWindowMixin)
    assert "FramelessAcrylicDialog" in dialog.styleSheet()
    assert dialog.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is False
    assert dialog._shouldExtendFrame() is isGreaterEqualWin11()


def test_acrylic_gradient_color_getter_and_setter(qtbot, monkeypatch):
    """Verify getGradientColor and setGradientColor reapply native Acrylic effect.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    appliedColors = []

    def fakeSetAcrylic(self, hWnd, gradientColor=None):
        appliedColors.append(gradientColor)
        return True

    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setAcrylicEffect",
        fakeSetAcrylic,
    )

    window = FramelessAcrylicWindow(gradientColor=0x99112233)
    qtbot.addWidget(window)

    assert window.getGradientColor() == 0x99112233
    assert 0x99112233 in appliedColors

    window.setGradientColor(0x99445566)
    assert window.getGradientColor() == 0x99445566
    assert appliedColors[-1] == 0x99445566


def test_acrylic_window_state_change_refreshes_blur(qtbot, monkeypatch):
    """Verify window state change event triggers refreshBackgroundBlurEffect.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setAcrylicEffect",
        lambda self, hWnd, gradientColor=None: True,
    )

    window = FramelessAcrylicWindow()
    qtbot.addWidget(window)

    refreshCallCount = 0

    def fakeRefresh():
        nonlocal refreshCallCount
        refreshCallCount += 1

    monkeypatch.setattr(window, "refreshBackgroundBlurEffect", fakeRefresh)

    # Deliver WindowStateChange event
    stateChangeEvent = QEvent(QEvent.Type.WindowStateChange)
    window.changeEvent(stateChangeEvent)

    assert refreshCallCount == 1


def test_acrylic_title_bar_transparency(qtbot, monkeypatch):
    """Verify TitleBar is completely transparent without background fill in Acrylic windows.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setAcrylicEffect",
        lambda self, hWnd, gradientColor=None: True,
    )

    window = FramelessAcrylicWindow()
    mainWindow = FramelessAcrylicMainWindow()
    qtbot.addWidget(window)
    qtbot.addWidget(mainWindow)

    # Verify None safety on helper
    _configureTitleBarForMaterial(None)

    for currentWindow in (window, mainWindow):
        titleBar = currentWindow.getTitleBar()
        assert titleBar is not None
        assert titleBar.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is True
        assert titleBar.autoFillBackground() is False
        paletteColor = titleBar.palette().color(QPalette.ColorRole.Window)
        assert paletteColor == Qt.GlobalColor.transparent
        assert titleBar.getBackgroundColor() == QColor(0, 0, 0, 0)
        assert titleBar.styleSheet() == ""

        currentWindow.show()
        qtbot.waitExposed(currentWindow)
        grabbedImage = titleBar.grab().toImage()
        assert grabbedImage.pixelColor(10, 10).alpha() == 0


def test_acrylic_title_bar_buttons_idle_transparency(qtbot, monkeypatch):
    """Verify TitleBar control buttons have transparent idle background on Acrylic windows.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setAcrylicEffect",
        lambda self, hWnd, gradientColor=None: True,
    )

    mainWindow = FramelessAcrylicMainWindow()
    qtbot.addWidget(mainWindow)
    mainWindow.show()
    qtbot.waitExposed(mainWindow)

    titleBar = mainWindow.getTitleBar()
    assert titleBar is not None
    buttons = titleBar.getButtons()

    for buttonKey in ("min", "max", "close"):
        button = buttons[buttonKey]
        buttonImage = button.grab().toImage()
        # Idle background must be transparent (alpha == 0)
        assert buttonImage.pixelColor(5, 5).alpha() == 0


def test_acrylic_theme_palette_transparency(qtbot, monkeypatch):
    """Verify theme palette keeps Window and Base color roles transparent for Acrylic.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setAcrylicEffect",
        lambda self, hWnd, gradientColor=None: True,
    )

    window = FramelessAcrylicWindow()
    qtbot.addWidget(window)

    for isDark in (True, False):
        palette = window._createThemePalette(isDark)
        assert palette.color(QPalette.ColorRole.Window) == Qt.GlobalColor.transparent
        assert palette.color(QPalette.ColorRole.Base) == Qt.GlobalColor.transparent
