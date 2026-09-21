"""Backward-compatible alias module re-exporting vector control buttons.

Re-exports vector buttons from :mod:`qtframelesskit.windows.title_bar.buttons`
for backward compatibility with existing imports.
"""

import sys

from .title_bar import buttons as _buttons_module
from .title_bar.buttons import (
    CloseButton,
    FullScreenButton,
    MaximizeButton,
    MinimizeButton,
    VectorButton,
)

__all__ = [
    "CloseButton",
    "FullScreenButton",
    "MaximizeButton",
    "MinimizeButton",
    "VectorButton",
]

sys.modules[__name__] = _buttons_module
