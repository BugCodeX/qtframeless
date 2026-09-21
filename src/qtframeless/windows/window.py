"""Concrete frameless window implementations for base opaque, Acrylic, and Mica backdrops.

Provides dedicated subclass families for standard opaque windows, Windows 10/11 Fluent
Acrylic blur-behind material, and Windows 11 native Mica and Mica Alt materials.
"""

from qtpy.QtCore import QEvent, Qt
from qtpy.QtGui import QColor, QPalette
from qtpy.QtWidgets import QVBoxLayout, QWidget

from qtframeless.native.win32_types import DWMWA_COLOR_NONE
from qtframeless.native.win32_utils import isGreaterEqualWin11
from qtframeless.native.window_effect import WindowsEffectHelper
from qtframeless.windows.base_widget import BaseDialog, BaseMainWindow, BaseWidget
from qtframeless.windows.title_bar import TitleBar


def _configureTitleBarForMaterial(titleBar: TitleBar | None) -> None:
    """Configure a TitleBar instance to be fully transparent for material backdrops.

    Enables translucent background attributes, disables default palette window autofill,
    and assigns a transparent QPainter background color so the title bar seamlessly blends
    into native Windows 11 Acrylic, Mica, and Mica Alt materials without stylesheets.

    Parameters
    ----------
    titleBar : TitleBar or None
        Custom title bar widget to configure for material backdrop composition.
    """
    if titleBar is None:
        return
    titleBar.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    titleBar.setAutoFillBackground(False)
    palette = titleBar.palette()
    palette.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.transparent)
    palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.transparent)
    titleBar.setPalette(palette)
    titleBar.setBackgroundColor(QColor(0, 0, 0, 0))


def _setupFramelessLayout(widget: QWidget, titleBar: TitleBar | None) -> None:
    """Configure a zero-margin vertical layout hosting the title bar on a frameless container.

    Parameters
    ----------
    widget : QWidget
        Target frameless container widget to configure.
    titleBar : TitleBar or None
        Custom title bar widget to position as the topmost element in the layout.
    """
    if widget.layout() is None and titleBar is not None:
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(titleBar)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        widget.setLayout(mainLayout)


class FramelessWidget(BaseWidget):
    """Frameless :class:`QWidget` with an integrated custom title bar.

    Parameters
    ----------
    hint : list of str, optional
        Title-bar button keys to display (e.g. ``["min", "max", "close"]``).
        Defaults to all buttons when None.
    flags : list, optional
        Extra Qt window flags to apply. Defaults to an empty list.
    """

    def __init__(
        self,
        hint: list[str] | None = None,
        flags: list | None = None,
        *args,
        **kwargs,
    ) -> None:
        if flags is None:
            flags = []
        super().__init__(*args, hint=hint, flags=flags, **kwargs)

    def _initUi(self, hint: list[str] | None = None, flags: list | None = None) -> None:
        """Build the layout, placing the title bar above the content area."""
        super()._initUi(hint, flags)
        _setupFramelessLayout(self, self._titleBar)


class FramelessWindow(FramelessWidget):
    """Frameless top-level window widget with integrated custom title bar.

    Alias and standard widget subclass equivalent to :class:`FramelessWidget`.
    """


class FramelessDialog(BaseDialog):
    """Frameless :class:`QDialog` with an integrated custom title bar.

    Parameters
    ----------
    hint : list of str, optional
        Title-bar button keys to display. Defaults to all buttons when None.
    flags : list, optional
        Extra Qt window flags to apply. Defaults to an empty list.
    """

    def __init__(
        self,
        hint: list[str] | None = None,
        flags: list | None = None,
        *args,
        **kwargs,
    ) -> None:
        if flags is None:
            flags = []
        super().__init__(*args, hint=hint, flags=flags, **kwargs)

    def _initUi(self, hint: list[str] | None = None, flags: list | None = None) -> None:
        """Build the layout, placing the title bar above the content area."""
        super()._initUi(hint, flags)
        _setupFramelessLayout(self, self._titleBar)


class FramelessMainWindow(BaseMainWindow):
    """Frameless :class:`QMainWindow` with an integrated custom title bar.

    Wraps the title bar and content inside a central widget so that
    dock and toolbar mechanisms operate normally.

    Parameters
    ----------
    hint : list of str, optional
        Title-bar button keys to display. Defaults to all buttons when None.
    flags : list, optional
        Extra Qt window flags to apply. Defaults to an empty list.
    """

    def __init__(
        self,
        hint: list[str] | None = None,
        flags: list | None = None,
        *args,
        **kwargs,
    ) -> None:
        if flags is None:
            flags = []
        super().__init__(*args, hint=hint, flags=flags, **kwargs)

    def _initUi(self, hint: list[str] | None = None, flags: list | None = None) -> None:
        """Build the layout and set it as the central widget."""
        super()._initUi(hint, flags)
        if self.centralWidget() is None and self._titleBar is not None:
            mainLayout = QVBoxLayout()
            mainLayout.addWidget(self._titleBar)
            mainLayout.setContentsMargins(0, 0, 0, 0)
            mainLayout.setSpacing(0)

            mainContentWidget = QWidget()
            mainContentWidget.setLayout(mainLayout)
            self.setCentralWidget(mainContentWidget)


class AcrylicWindowMixin:
    """Mixin providing native Windows Fluent Acrylic blur-behind material integration."""

    def __init__(
        self,
        *args,
        gradientColor: str | int | None = None,
        **kwargs,
    ) -> None:
        self._gradientColor: str | int | None = gradientColor
        super().__init__(*args, **kwargs)

    def _isMaterialBackdrop(self) -> bool:
        """Return whether the window uses a material backdrop effect.

        Returns
        -------
        bool
            True for material backdrop windows.
        """
        return True

    def _shouldExtendFrame(self) -> bool:
        """Determine whether DWM frame extension should be enabled for Acrylic windows.

        On Windows 11, extending the frame removes the native Win32 caption bar
        so the custom TitleBar seamlessly matches the Acrylic blur backdrop.
        On Windows 10, frame extension is omitted to prevent blur boundary collision.

        Returns
        -------
        bool
            True if running on Windows 11 or higher, False on Windows 10.
        """
        return isGreaterEqualWin11()

    def _createThemePalette(self, isDark: bool) -> QPalette:
        """Create a theme palette with transparent background roles for Acrylic backdrop.

        Parameters
        ----------
        isDark : bool
            True to generate a dark theme palette, False for light theme.

        Returns
        -------
        QPalette
            Theme palette with Window and Base color roles set to transparent.
        """
        return super()._createThemePalette(isDark)

    def _initUi(self, hint: list[str] | None = None, flags: list | None = None) -> None:
        """Configure Acrylic window flags, QSS transparency, and native blur.

        Parameters
        ----------
        hint : list of str, optional
            Control button hints to display on the title bar.
        flags : list, optional
            Additional Qt window flags to apply.
        """
        if hasattr(self, "_themeController"):
            self._themeController.setIsMaterial(True)

        combinedFlags = list(flags) if flags is not None else []
        if hasattr(Qt.WindowType, "NoTitleBarBackgroundHint"):
            combinedFlags.append(Qt.WindowType.NoTitleBarBackgroundHint)

        super()._initUi(hint=hint, flags=combinedFlags)

        className = self.__class__.__name__
        self.setStyleSheet(f"{className}, {className} > QWidget {{ background: transparent; }}")
        _configureTitleBarForMaterial(getattr(self, "_titleBar", None))

        if not hasattr(self, "_windowEffect"):
            self._windowEffect = WindowsEffectHelper()
        self._windowEffect.setAcrylicEffect(
            int(self.winId()), getattr(self, "_gradientColor", None)
        )
        self._windowEffect.setCaptionColor(int(self.winId()), DWMWA_COLOR_NONE)

    def changeEvent(self, event: QEvent) -> None:
        """Handle window state change events, refreshing Acrylic blur when maximized or restored.

        Parameters
        ----------
        event : QEvent
            State change event.
        """
        if event.type() == QEvent.Type.WindowStateChange:
            self.refreshBackgroundBlurEffect()
        super().changeEvent(event)

    def refreshBackgroundBlurEffect(self) -> None:
        """Reapply native Acrylic blur effect to prevent visual loss after state transitions."""
        if hasattr(self, "_windowEffect"):
            self._windowEffect.refreshBackgroundBlurEffect(
                int(self.winId()), getattr(self, "_gradientColor", None)
            )

    def getGradientColor(self) -> str | int | None:
        """Return the active Acrylic gradient tint color.

        Returns
        -------
        str, int, or None
            Current tint color representation.
        """
        return getattr(self, "_gradientColor", None)

    def setGradientColor(self, color: str | int | None) -> None:
        """Apply a new Acrylic gradient tint color and refresh DWM composition.

        Parameters
        ----------
        color : str, int, or None
            Gradient tint color representation.
        """
        self._gradientColor = color
        if hasattr(self, "_windowEffect"):
            self._windowEffect.setAcrylicEffect(int(self.winId()), color)


class FramelessAcrylicWindow(AcrylicWindowMixin, FramelessWindow):
    """Frameless :class:`QWidget` with native Fluent Acrylic blur-behind material.

    Parameters
    ----------
    hint : list of str, optional
        Control button hints to display on the title bar.
    flags : list, optional
        Additional Qt window flags to apply.
    gradientColor : str, int, or None, optional
        Custom gradient tint color for the Acrylic effect.
    """

    def __init__(
        self,
        hint: list[str] | None = None,
        flags: list | None = None,
        gradientColor: str | int | None = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(
            *args,
            hint=hint,
            flags=flags,
            gradientColor=gradientColor,
            **kwargs,
        )


class FramelessAcrylicMainWindow(AcrylicWindowMixin, FramelessMainWindow):
    """Frameless :class:`QMainWindow` with native Fluent Acrylic blur-behind material.

    Parameters
    ----------
    hint : list of str, optional
        Control button hints to display on the title bar.
    flags : list, optional
        Additional Qt window flags to apply.
    gradientColor : str, int, or None, optional
        Custom gradient tint color for the Acrylic effect.
    """

    def __init__(
        self,
        hint: list[str] | None = None,
        flags: list | None = None,
        gradientColor: str | int | None = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(
            *args,
            hint=hint,
            flags=flags,
            gradientColor=gradientColor,
            **kwargs,
        )


class FramelessAcrylicDialog(AcrylicWindowMixin, FramelessDialog):
    """Frameless :class:`QDialog` with native Fluent Acrylic blur-behind material.

    Parameters
    ----------
    hint : list of str, optional
        Control button hints to display on the title bar.
    flags : list, optional
        Additional Qt window flags to apply.
    gradientColor : str, int, or None, optional
        Custom gradient tint color for the Acrylic effect.
    """

    def __init__(
        self,
        hint: list[str] | None = None,
        flags: list | None = None,
        gradientColor: str | int | None = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(
            *args,
            hint=hint,
            flags=flags,
            gradientColor=gradientColor,
            **kwargs,
        )


class MicaWindowMixin:
    """Mixin providing native Windows 11 Mica and Mica Alt backdrop material integration."""

    def __init__(
        self,
        *args,
        isAlt: bool = False,
        **kwargs,
    ) -> None:
        self._isAlt: bool = isAlt
        super().__init__(*args, **kwargs)

    def _isMaterialBackdrop(self) -> bool:
        """Return whether the window uses a material backdrop effect.

        Returns
        -------
        bool
            True for material backdrop windows.
        """
        return True

    def _initUi(self, hint: list[str] | None = None, flags: list | None = None) -> None:
        """Configure Mica window flags, QSS transparency, and native backdrop.

        Parameters
        ----------
        hint : list of str, optional
            Control button hints to display on the title bar.
        flags : list, optional
            Additional Qt window flags to apply.
        """
        if hasattr(self, "_themeController"):
            self._themeController.setIsMaterial(True)

        combinedFlags = list(flags) if flags is not None else []
        if hasattr(Qt.WindowType, "NoTitleBarBackgroundHint"):
            combinedFlags.append(Qt.WindowType.NoTitleBarBackgroundHint)

        super()._initUi(hint=hint, flags=combinedFlags)

        className = self.__class__.__name__
        self.setStyleSheet(f"{className}, {className} > QWidget {{ background: transparent; }}")
        _configureTitleBarForMaterial(getattr(self, "_titleBar", None))

        if not hasattr(self, "_windowEffect"):
            self._windowEffect = WindowsEffectHelper()
        self._windowEffect.setMicaEffect(int(self.winId()), isAlt=getattr(self, "_isAlt", False))
        self._windowEffect.setCaptionColor(int(self.winId()), DWMWA_COLOR_NONE)

    def _createThemePalette(self, isDark: bool) -> QPalette:
        """Create a theme palette with transparent background roles for Mica backdrop.

        Parameters
        ----------
        isDark : bool
            True to generate a dark theme palette, False for light theme.

        Returns
        -------
        QPalette
            Theme palette with Window and Base color roles set to transparent.
        """
        palette = super()._createThemePalette(isDark)
        palette.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.transparent)
        palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.transparent)
        return palette

    def isAlt(self) -> bool:
        """Return whether Mica Alt (tabbed window backdrop) is active.

        Returns
        -------
        bool
            True if Mica Alt is enabled, False for standard Mica.
        """
        return getattr(self, "_isAlt", False)

    def setIsAlt(self, isAlt: bool) -> None:
        """Configure Mica backdrop variant and reapply DWM attributes.

        Parameters
        ----------
        isAlt : bool
            True to apply Mica Alt, False for standard Mica.
        """
        self._isAlt = isAlt
        if hasattr(self, "_windowEffect"):
            self._windowEffect.setMicaEffect(int(self.winId()), isAlt=isAlt)


class FramelessMicaWindow(MicaWindowMixin, FramelessWindow):
    """Frameless :class:`QWidget` with native Windows 11 Mica or Mica Alt backdrop.

    Parameters
    ----------
    hint : list of str, optional
        Control button hints to display on the title bar.
    flags : list, optional
        Additional Qt window flags to apply.
    isAlt : bool, optional
        True to apply Mica Alt material, False for standard Mica. Defaults to False.
    """

    def __init__(
        self,
        hint: list[str] | None = None,
        flags: list | None = None,
        isAlt: bool = False,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(
            *args,
            hint=hint,
            flags=flags,
            isAlt=isAlt,
            **kwargs,
        )


class FramelessMicaMainWindow(MicaWindowMixin, FramelessMainWindow):
    """Frameless :class:`QMainWindow` with native Windows 11 Mica or Mica Alt backdrop.

    Parameters
    ----------
    hint : list of str, optional
        Control button hints to display on the title bar.
    flags : list, optional
        Additional Qt window flags to apply.
    isAlt : bool, optional
        True to apply Mica Alt material, False for standard Mica. Defaults to False.
    """

    def __init__(
        self,
        hint: list[str] | None = None,
        flags: list | None = None,
        isAlt: bool = False,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(
            *args,
            hint=hint,
            flags=flags,
            isAlt=isAlt,
            **kwargs,
        )


class FramelessMicaDialog(MicaWindowMixin, FramelessDialog):
    """Frameless :class:`QDialog` with native Windows 11 Mica or Mica Alt backdrop.

    Parameters
    ----------
    hint : list of str, optional
        Control button hints to display on the title bar.
    flags : list, optional
        Additional Qt window flags to apply.
    isAlt : bool, optional
        True to apply Mica Alt material, False for standard Mica. Defaults to False.
    """

    def __init__(
        self,
        hint: list[str] | None = None,
        flags: list | None = None,
        isAlt: bool = False,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(
            *args,
            hint=hint,
            flags=flags,
            isAlt=isAlt,
            **kwargs,
        )


__all__ = [
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
    "_configureTitleBarForMaterial",
    "_setupFramelessLayout",
]
