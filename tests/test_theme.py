"""Unit tests for ThemeController theme management, palette generation, and system sync."""

from unittest.mock import MagicMock

from qtpy.QtCore import Qt
from qtpy.QtGui import QColor, QPalette
from qtpy.QtWidgets import QWidget

from qtframelesskit.core.theme import ThemeController


def test_theme_controller_initialization(qapp) -> None:
    """Verify ThemeController default attributes and initial state."""
    window = QWidget()
    controller = ThemeController(window)

    assert controller.isDarkTheme() is False
    assert controller.isDetectingThemeAllowed() is True
    assert controller.isMaterial() is False


def test_theme_controller_material_initialization(qapp) -> None:
    """Verify ThemeController initialization with material transparency enabled."""
    window = QWidget()
    controller = ThemeController(window, isMaterial=True)

    assert controller.isMaterial() is True


def test_set_dark_theme_toggle_and_signals(qtbot) -> None:
    """Verify setDarkTheme toggles state, emits darkThemeChanged signal, and handles force."""
    window = QWidget()
    qtbot.addWidget(window)
    controller = ThemeController(window)

    emittedValues: list[bool] = []
    controller.darkThemeChanged.connect(emittedValues.append)

    controller.setDarkTheme(True)
    assert controller.isDarkTheme() is True
    assert emittedValues == [True]

    controller.setDarkTheme(True)
    assert emittedValues == [True]

    controller.setDarkTheme(True, force=True)
    assert emittedValues == [True, True]

    controller.setDarkTheme(False)
    assert controller.isDarkTheme() is False
    assert emittedValues == [True, True, False]


def test_set_dark_theme_updates_title_bar(qtbot) -> None:
    """Verify setDarkTheme calls setDarkTheme on window title bar if present."""
    window = QWidget()
    qtbot.addWidget(window)

    mockTitleBar = MagicMock()
    window._titleBar = mockTitleBar

    controller = ThemeController(window)
    controller.setDarkTheme(True)

    mockTitleBar.setDarkTheme.assert_called_once_with(True)


def test_set_detecting_theme_allowed(qtbot) -> None:
    """Verify setDetectingThemeAllowed toggles flag and emits signal with suppression."""
    window = QWidget()
    qtbot.addWidget(window)
    controller = ThemeController(window)

    emittedValues: list[bool] = []
    controller.detectingThemeAllowedChanged.connect(emittedValues.append)

    controller.setDetectingThemeAllowed(False)
    assert controller.isDetectingThemeAllowed() is False
    assert emittedValues == [False]

    controller.setDetectingThemeAllowed(False)
    assert emittedValues == [False]

    controller.setDetectingThemeAllowed(True)
    assert controller.isDetectingThemeAllowed() is True
    assert emittedValues == [False, True]


def test_create_theme_palette_opaque_window(qapp) -> None:
    """Verify createThemePalette returns opaque colors for standard windows."""
    window = QWidget()
    controller = ThemeController(window, isMaterial=False)

    darkPalette = controller.createThemePalette(isDark=True)
    assert darkPalette.color(QPalette.ColorRole.Window) == QColor("#202020")
    assert darkPalette.color(QPalette.ColorRole.Base) == QColor("#191919")

    lightPalette = controller.createThemePalette(isDark=False)
    assert lightPalette.color(QPalette.ColorRole.Window) == QColor("#f3f3f3")
    assert lightPalette.color(QPalette.ColorRole.Base) == QColor("#ffffff")


def test_create_theme_palette_material_window(qapp) -> None:
    """Verify createThemePalette returns transparent background roles for material windows."""
    window = QWidget()
    controller = ThemeController(window, isMaterial=True)

    darkPalette = controller.createThemePalette(isDark=True)
    assert darkPalette.color(QPalette.ColorRole.Window) == Qt.GlobalColor.transparent
    assert darkPalette.color(QPalette.ColorRole.Base) == Qt.GlobalColor.transparent

    lightPalette = controller.createThemePalette(isDark=False)
    assert lightPalette.color(QPalette.ColorRole.Window) == Qt.GlobalColor.transparent
    assert lightPalette.color(QPalette.ColorRole.Base) == Qt.GlobalColor.transparent


def test_set_is_material_updates_palette(qapp) -> None:
    """Verify setIsMaterial toggles state and immediately applies updated palette to window."""
    window = QWidget()
    controller = ThemeController(window, isMaterial=False)

    assert controller.isMaterial() is False
    assert window.palette().color(QPalette.ColorRole.Window) != Qt.GlobalColor.transparent

    controller.setIsMaterial(True)
    assert controller.isMaterial() is True
    assert window.palette().color(QPalette.ColorRole.Window) == Qt.GlobalColor.transparent


def test_detect_system_theme_dark(monkeypatch, qapp) -> None:
    """Verify detectSystemTheme returns True when Windows registry AppsUseLightTheme is 0."""
    window = QWidget()
    controller = ThemeController(window)

    monkeypatch.setattr(
        "qtframelesskit.core.theme.OpenKey",
        lambda *args, **kwargs: MagicMock(),
    )
    monkeypatch.setattr(
        "qtframelesskit.core.theme.QueryValueEx",
        lambda *args, **kwargs: (0, 4),
    )

    assert controller.detectSystemTheme() is True


def test_detect_system_theme_light(monkeypatch, qapp) -> None:
    """Verify detectSystemTheme returns False when Windows registry AppsUseLightTheme is 1."""
    window = QWidget()
    controller = ThemeController(window)

    monkeypatch.setattr(
        "qtframelesskit.core.theme.OpenKey",
        lambda *args, **kwargs: MagicMock(),
    )
    monkeypatch.setattr(
        "qtframelesskit.core.theme.QueryValueEx",
        lambda *args, **kwargs: (1, 4),
    )

    assert controller.detectSystemTheme() is False


def test_detect_system_theme_os_error(monkeypatch, qapp) -> None:
    """Verify detectSystemTheme returns None when registry query raises OSError."""
    window = QWidget()
    controller = ThemeController(window)

    def raiseOsError(*args, **kwargs):
        raise OSError("Registry key not found")

    monkeypatch.setattr("qtframelesskit.core.theme.OpenKey", raiseOsError)

    assert controller.detectSystemTheme() is None


def test_sync_with_system_theme_integration(monkeypatch, qtbot) -> None:
    """Verify syncWithSystemTheme queries system theme and updates dark theme state."""
    window = QWidget()
    qtbot.addWidget(window)
    controller = ThemeController(window)

    monkeypatch.setattr(controller, "detectSystemTheme", lambda: True)
    controller.syncWithSystemTheme()
    assert controller.isDarkTheme() is True

    monkeypatch.setattr(controller, "detectSystemTheme", lambda: False)
    controller.syncWithSystemTheme()
    assert controller.isDarkTheme() is False

    monkeypatch.setattr(controller, "detectSystemTheme", lambda: None)
    controller.syncWithSystemTheme()
    assert controller.isDarkTheme() is False
