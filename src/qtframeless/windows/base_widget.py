"""Base frameless window classes integrating FramelessWindowMixin with Qt widgets.

Provides BaseWidget, BaseDialog, and BaseMainWindow as concrete frameless window
implementations without duplicating logic across widget hierarchies.
"""

from qtpy.QtWidgets import QDialog, QMainWindow, QWidget

from qtframeless.core.frameless_mixin import FramelessWindowMixin


class BaseWidget(FramelessWindowMixin, QWidget):
    """Frameless QWidget base class with Win32 integration and custom title bar.

    Parameters
    ----------
    parent : QWidget, optional
        Parent widget.
    hint : list of str, optional
        Button hints for the title bar ('min', 'max', 'close', 'full_screen').
    flags : list, optional
        Additional Qt window flags.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        hint: list[str] | None = None,
        flags: list | None = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(parent, *args, **kwargs)
        self._initVal()
        self._initUi(hint, flags)


class BaseDialog(FramelessWindowMixin, QDialog):
    """Frameless QDialog base class with Win32 integration and custom title bar.

    Parameters
    ----------
    parent : QWidget, optional
        Parent widget.
    hint : list of str, optional
        Button hints for the title bar ('min', 'max', 'close', 'full_screen').
    flags : list, optional
        Additional Qt window flags.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        hint: list[str] | None = None,
        flags: list | None = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(parent, *args, **kwargs)
        self._initVal()
        self._initUi(hint, flags)


class BaseMainWindow(FramelessWindowMixin, QMainWindow):
    """Frameless QMainWindow base class with Win32 integration and custom title bar.

    Parameters
    ----------
    parent : QWidget, optional
        Parent widget.
    hint : list of str, optional
        Button hints for the title bar ('min', 'max', 'close', 'full_screen').
    flags : list, optional
        Additional Qt window flags.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        hint: list[str] | None = None,
        flags: list | None = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(parent, *args, **kwargs)
        self._initVal()
        self._initUi(hint, flags)


__all__ = [
    "BaseDialog",
    "BaseMainWindow",
    "BaseWidget",
]
