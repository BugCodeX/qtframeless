"""Theme management controller for qtframelesskit window components.

Encapsulates OS theme detection, dark mode toggling, title bar synchronization,
and QPalette generation for standard opaque and material transparent windows.
"""

from winreg import HKEY_CURRENT_USER, KEY_READ, OpenKey, QueryValueEx

from qtpy.QtCore import QObject, Qt, Signal
from qtpy.QtGui import QColor, QPalette
from qtpy.QtWidgets import QWidget

from qtframelesskit.native.window_effect import WindowsEffectHelper

__all__ = ["ThemeController"]


class ThemeController(QObject):
    """Manage application theme mode, system synchronization, and palette generation.

    Parameters
    ----------
    window : QWidget
        Target Qt widget window associated with this theme controller.
    isMaterial : bool, optional
        True if the window uses a translucent material backdrop (Acrylic or Mica).
        Defaults to False.
    parent : QObject, optional
        Parent QObject for lifecycle management. Defaults to None.

    Attributes
    ----------
    darkThemeChanged : Signal(bool)
        Emitted when the dark theme state changes.
    detectingThemeAllowedChanged : Signal(bool)
        Emitted when automatic system theme detection permission changes.
    """

    darkThemeChanged = Signal(bool)
    detectingThemeAllowedChanged = Signal(bool)

    def __init__(
        self,
        window: QWidget,
        isMaterial: bool = False,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent if parent is not None else window)
        self._window: QWidget = window
        self._isMaterial: bool = isMaterial
        self._isDarkTheme: bool = False
        self._detectThemeFlag: bool = True
        self._windowEffect: WindowsEffectHelper = WindowsEffectHelper()

    def isDarkTheme(self) -> bool:
        """Return whether dark theme is currently applied.

        Returns
        -------
        bool
            True if dark theme is active, False otherwise.
        """
        return self._isDarkTheme

    def setDarkTheme(self, isDark: bool, force: bool = False) -> None:
        """Apply dark theme mode to the window, title bar, and palette.

        Parameters
        ----------
        isDark : bool
            True to enable dark mode, False for light mode.
        force : bool, optional
            True to force re-applying theme even if state matches current theme.
            Defaults to False.
        """
        if not force and self._isDarkTheme == isDark:
            return
        self._isDarkTheme = isDark
        try:
            hWnd = int(self._window.winId())
        except (AttributeError, TypeError, ValueError):
            hWnd = 0
        if hWnd:
            self._windowEffect.setDarkTheme(hWnd, isDark)
        if hasattr(self._window, "_titleBar") and self._window._titleBar is not None:
            self._window._titleBar.setDarkTheme(isDark)
        self._window.setPalette(self.createThemePalette(isDark))
        self.darkThemeChanged.emit(isDark)

    def isDetectingThemeAllowed(self) -> bool:
        """Return whether automatic theme detection on setting changes is allowed.

        Returns
        -------
        bool
            True if automatic detection is active.
        """
        return self._detectThemeFlag

    def setDetectingThemeAllowed(self, allow: bool) -> None:
        """Enable or disable automatic theme detection on Windows setting changes.

        Parameters
        ----------
        allow : bool
            True to allow theme detection on setting changes.
        """
        if self._detectThemeFlag == allow:
            return
        self._detectThemeFlag = allow
        self.detectingThemeAllowedChanged.emit(allow)

    def detectSystemTheme(self) -> bool | None:
        """Query Windows registry for the system application theme setting.

        Returns
        -------
        bool or None
            True if system is in dark mode (AppsUseLightTheme == 0),
            False if system is in light mode (AppsUseLightTheme == 1),
            or None on OSError or invalid registry value.
        """
        try:
            rootKey = OpenKey(
                HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                0,
                KEY_READ,
            )
            lightThemeValue, _ = QueryValueEx(rootKey, "AppsUseLightTheme")
            if lightThemeValue == 0:
                return True
            if lightThemeValue == 1:
                return False
            return None
        except OSError:
            return None

    def syncWithSystemTheme(self, force: bool = False) -> None:
        """Synchronize window theme with the Windows system theme setting.

        Parameters
        ----------
        force : bool, optional
            True to force re-applying theme even if state matches current theme.
            Defaults to False.
        """
        systemDark = self.detectSystemTheme()
        if systemDark is not None:
            self.setDarkTheme(systemDark, force=force)

    def isMaterial(self) -> bool:
        """Return whether material transparent backdrop is enabled.

        Returns
        -------
        bool
            True if material backdrop is active.
        """
        return self._isMaterial

    def setIsMaterial(self, isMaterial: bool) -> None:
        """Set whether material transparent backdrop is enabled and update palette.

        Parameters
        ----------
        isMaterial : bool
            True to enable material palette transparency.
        """
        self._isMaterial = isMaterial
        self._window.setPalette(self.createThemePalette(self._isDarkTheme))

    def createThemePalette(self, isDark: bool) -> QPalette:
        """Generate a QPalette configured for dark or light theme mode.

        Parameters
        ----------
        isDark : bool
            True to generate a dark theme palette, False for light theme.

        Returns
        -------
        QPalette
            Configured window palette instance.
        """
        palette = QPalette()
        if isDark:
            palette.setColor(QPalette.ColorRole.Window, QColor("#202020"))
            palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#191919"))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#2d2d2d"))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#2b2b2b"))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.Button, QColor("#2d2d2d"))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.BrightText, QColor("#ff0000"))
            palette.setColor(QPalette.ColorRole.Link, QColor("#4cc2ff"))
            palette.setColor(QPalette.ColorRole.Highlight, QColor("#0078d4"))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#8a8a8a"))
        else:
            palette.setColor(QPalette.ColorRole.Window, QColor("#f3f3f3"))
            palette.setColor(QPalette.ColorRole.WindowText, QColor("#000000"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#e9e9e9"))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#000000"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#000000"))
            palette.setColor(QPalette.ColorRole.Button, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor("#000000"))
            palette.setColor(QPalette.ColorRole.BrightText, QColor("#ff0000"))
            palette.setColor(QPalette.ColorRole.Link, QColor("#0067c0"))
            palette.setColor(QPalette.ColorRole.Highlight, QColor("#0078d4"))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#767676"))

        if self._isMaterial:
            palette.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.transparent)
            palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.transparent)

        return palette
