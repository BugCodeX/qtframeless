"""Native Win32 and DWM integration submodules and visual effect helpers for Windows."""

from . import win32_types, win32_utils, window_effect
from .win32_types import (
    DWMWA_COLOR_DEFAULT,
    DWMWA_COLOR_NONE,
    DWMWINDOWATTRIBUTE,
    WindowCornerPreference,
    WindowEffect,
    colorToColorRef,
)
from .window_effect import WindowsEffectHelper

__all__ = [
    "DWMWA_COLOR_DEFAULT",
    "DWMWA_COLOR_NONE",
    "DWMWINDOWATTRIBUTE",
    "WindowCornerPreference",
    "WindowEffect",
    "WindowsEffectHelper",
    "colorToColorRef",
    "win32_types",
    "win32_utils",
    "window_effect",
]
