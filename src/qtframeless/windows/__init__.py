"""Public entry point for frameless window variants and native material subclasses.

Exposes base frameless window classes (:class:`FramelessWidget`, :class:`FramelessWindow`,
:class:`FramelessDialog`, :class:`FramelessMainWindow`) and dedicated native Windows backdrop
subclasses for Acrylic and Mica.
"""

from .base_widget import (
    BaseDialog,
    BaseMainWindow,
    BaseWidget,
)
from .buttons import (
    CloseButton,
    FullScreenButton,
    MaximizeButton,
    MinimizeButton,
    VectorButton,
)
from .title_bar import TitleBar
from .window import (
    AcrylicWindowMixin,
    FramelessAcrylicDialog,
    FramelessAcrylicMainWindow,
    FramelessAcrylicWindow,
    FramelessDialog,
    FramelessMainWindow,
    FramelessMicaDialog,
    FramelessMicaMainWindow,
    FramelessMicaWindow,
    FramelessWidget,
    FramelessWindow,
    MicaWindowMixin,
    _configureTitleBarForMaterial,
    _setupFramelessLayout,
)

__all__ = [
    "AcrylicWindowMixin",
    "BaseDialog",
    "BaseMainWindow",
    "BaseWidget",
    "CloseButton",
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
    "FullScreenButton",
    "MaximizeButton",
    "MinimizeButton",
    "MicaWindowMixin",
    "TitleBar",
    "VectorButton",
    "_configureTitleBarForMaterial",
    "_setupFramelessLayout",
]
