"""Tests for FramelessMicaWindow, FramelessMicaMainWindow, and FramelessMicaDialog."""

from qtpy.QtCore import Qt
from qtpy.QtGui import QColor, QPalette
from qtpy.QtWidgets import QWidget

from qtframeless.windows.window import (
    FramelessMicaDialog,
    FramelessMicaMainWindow,
    FramelessMicaWindow,
    MicaWindowMixin,
    _configureTitleBarForMaterial,
)


def test_mica_window_initialization(qtbot, monkeypatch):
    """Verify FramelessMicaWindow initializes with standard Mica and class QSS.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    recordedCalls = []

    def fakeSetMica(self, hWnd, isAlt=False):
        recordedCalls.append((hWnd, isAlt))
        return True

    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setMicaEffect",
        fakeSetMica,
    )

    window = FramelessMicaWindow(isAlt=False)
    qtbot.addWidget(window)

    assert isinstance(window, MicaWindowMixin)
    assert isinstance(window, QWidget)
    assert window.isAlt() is False
    assert "FramelessMicaWindow" in window.styleSheet()
    assert window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is False
    assert window._shouldExtendFrame() is True
    assert len(recordedCalls) >= 1
    assert recordedCalls[-1][1] is False


def test_mica_alt_window_initialization(qtbot, monkeypatch):
    """Verify FramelessMicaWindow initializes with Mica Alt when isAlt is True.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    recordedCalls = []

    def fakeSetMica(self, hWnd, isAlt=False):
        recordedCalls.append((hWnd, isAlt))
        return True

    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setMicaEffect",
        fakeSetMica,
    )

    window = FramelessMicaWindow(isAlt=True)
    qtbot.addWidget(window)

    assert window.isAlt() is True
    assert recordedCalls[-1][1] is True


def test_mica_is_alt_toggle(qtbot, monkeypatch):
    """Verify setIsAlt updates isAlt state and re-invokes native helper.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    recordedCalls = []

    def fakeSetMica(self, hWnd, isAlt=False):
        recordedCalls.append(isAlt)
        return True

    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setMicaEffect",
        fakeSetMica,
    )

    window = FramelessMicaWindow()
    qtbot.addWidget(window)
    assert window.isAlt() is False

    window.setIsAlt(True)
    assert window.isAlt() is True
    assert recordedCalls[-1] is True

    window.setIsAlt(False)
    assert window.isAlt() is False
    assert recordedCalls[-1] is False


def test_mica_main_window_and_dialog(qtbot, monkeypatch):
    """Verify FramelessMicaMainWindow and FramelessMicaDialog composition.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setMicaEffect",
        lambda self, hWnd, isAlt=False: True,
    )

    mainWindow = FramelessMicaMainWindow(isAlt=True)
    qtbot.addWidget(mainWindow)
    assert isinstance(mainWindow, MicaWindowMixin)
    assert mainWindow.centralWidget() is not None
    assert mainWindow.isAlt() is True
    assert "FramelessMicaMainWindow" in mainWindow.styleSheet()

    dialog = FramelessMicaDialog(isAlt=False)
    qtbot.addWidget(dialog)
    assert isinstance(dialog, MicaWindowMixin)
    assert dialog.isAlt() is False
    assert "FramelessMicaDialog" in dialog.styleSheet()


def test_mica_dark_theme_synchronization(qtbot, monkeypatch):
    """Verify dark mode changes emit signal and update DWM dark theme on Mica window.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setMicaEffect",
        lambda self, hWnd, isAlt=False: True,
    )

    recordedThemes = []

    def fakeSetDarkTheme(self, hWnd, isDark):
        recordedThemes.append((hWnd, isDark))
        return True

    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setDarkTheme",
        fakeSetDarkTheme,
    )

    window = FramelessMicaWindow()
    qtbot.addWidget(window)

    with qtbot.waitSignal(window.darkThemeChanged, timeout=1000) as blocker:
        window.setDarkTheme(True)

    assert blocker.args == [True]
    assert window.isDarkTheme() is True
    assert (int(window.winId()), True) in recordedThemes


def test_mica_title_bar_transparency(qtbot, monkeypatch):
    """Verify TitleBar is completely transparent without background fill in Mica windows.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setMicaEffect",
        lambda self, hWnd, isAlt=False: True,
    )

    window = FramelessMicaWindow(isAlt=False)
    altMainWindow = FramelessMicaMainWindow(isAlt=True)
    qtbot.addWidget(window)
    qtbot.addWidget(altMainWindow)

    # Verify None safety on helper
    _configureTitleBarForMaterial(None)

    for currentWindow in (window, altMainWindow):
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


def test_mica_title_bar_buttons_idle_transparency(qtbot, monkeypatch):
    """Verify TitleBar control buttons have transparent idle background on Mica windows.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setMicaEffect",
        lambda self, hWnd, isAlt=False: True,
    )

    mainWindow = FramelessMicaMainWindow(isAlt=False)
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


def test_mica_theme_palette_transparency(qtbot, monkeypatch):
    """Verify theme palette keeps Window and Base color roles transparent for Mica.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        Pytest-qt fixture.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    monkeypatch.setattr(
        "qtframeless.native.window_effect.WindowsEffectHelper.setMicaEffect",
        lambda self, hWnd, isAlt=False: True,
    )

    window = FramelessMicaWindow()
    qtbot.addWidget(window)

    for isDark in (True, False):
        palette = window._createThemePalette(isDark)
        assert palette.color(QPalette.ColorRole.Window) == Qt.GlobalColor.transparent
        assert palette.color(QPalette.ColorRole.Base) == Qt.GlobalColor.transparent
