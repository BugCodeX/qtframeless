"""Modern, cross-Qt frameless window framework for Windows in pure Python."""

import contextlib
import sys

from qtframeless.exceptions import PlatformNotSupportedError

__version__ = "0.1.0"

if sys.platform != "win32":
    raise PlatformNotSupportedError("qtframeless only supports Windows platforms.")

from qtframeless.native.win32_types import WindowCornerPreference, WindowEffect

with contextlib.suppress(ImportError):
    from qtframeless.windows import (
        AcrylicWindowMixin,  # noqa: F401
        FramelessAcrylicDialog,  # noqa: F401
        FramelessAcrylicMainWindow,  # noqa: F401
        FramelessAcrylicWindow,  # noqa: F401
        FramelessDialog,  # noqa: F401
        FramelessMainWindow,  # noqa: F401
        FramelessMicaDialog,  # noqa: F401
        FramelessMicaMainWindow,  # noqa: F401
        FramelessMicaWindow,  # noqa: F401
        FramelessWidget,  # noqa: F401
        FramelessWindow,  # noqa: F401
        MicaWindowMixin,  # noqa: F401
        TitleBar,  # noqa: F401
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
    "PlatformNotSupportedError",
    "TitleBar",
    "WindowCornerPreference",
    "WindowEffect",
    "__version__",
]
