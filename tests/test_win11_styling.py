"""Tests for Windows 11 native corner preferences and border coloring."""

from qtpy.QtGui import QColor
from qtpy.QtWidgets import QWidget

from qtframelesskit import WindowCornerPreference
from qtframelesskit.core.frameless_mixin import FramelessWindowMixin
from qtframelesskit.native.win32_types import colorToColorRef


class ConcreteWindow(FramelessWindowMixin, QWidget):
    """Concrete test window combining FramelessWindowMixin with QWidget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._initVal()
        self._initUi()


def test_color_to_color_ref_conversions():
    """Verify QColor and hex string conversions to Win32 COLORREF format."""
    assert colorToColorRef("#FF0000") == 0x000000FF  # Red
    assert colorToColorRef(QColor(0, 255, 0)) == 0x0000FF00  # Green
    assert colorToColorRef("#0000FF") == 0x00FF0000  # Blue
    assert colorToColorRef("invalid") == 0xFFFFFFFE
    assert colorToColorRef(None) == 0xFFFFFFFE


def test_window_corner_preference_state(qtbot):
    """Verify setting and getting window corner preferences."""
    window = ConcreteWindow()
    qtbot.addWidget(window)

    assert window.getWindowCornerPreference() == WindowCornerPreference.DEFAULT

    # Setting valid preference
    window.setWindowCornerPreference(WindowCornerPreference.ROUND)
    assert window.getWindowCornerPreference() == WindowCornerPreference.ROUND

    # Setting integer enum value
    window.setWindowCornerPreference(1)
    assert window.getWindowCornerPreference() == WindowCornerPreference.DO_NOT_ROUND

    # Setting invalid int
    assert not window.setWindowCornerPreference(999)


def test_window_border_color_state(qtbot):
    """Verify setting and getting customized border color."""
    window = ConcreteWindow()
    qtbot.addWidget(window)

    assert window.getBorderColor() is None

    # Setting via hex string
    window.setBorderColor("#0078D4")
    assert window.getBorderColor() is not None
    assert window.getBorderColor().name().lower() == "#0078d4"

    # Setting via QColor
    window.setBorderColor(QColor(255, 0, 0))
    assert window.getBorderColor() == QColor(255, 0, 0)


def test_window_caption_color_state(qtbot):
    """Verify setting and getting customized caption color."""
    from qtframelesskit.native.win32_types import DWMWA_COLOR_NONE

    window = ConcreteWindow()
    qtbot.addWidget(window)

    assert window.getCaptionColor() is None

    # Setting DWMWA_COLOR_NONE
    window.setCaptionColor(DWMWA_COLOR_NONE)
    assert window.getCaptionColor() == DWMWA_COLOR_NONE

    # Setting via hex string
    window.setCaptionColor("#0078D4")
    assert window.getCaptionColor() is not None
    assert window.getCaptionColor().name().lower() == "#0078d4"

    # Setting via QColor
    window.setCaptionColor(QColor(255, 0, 0))
    assert window.getCaptionColor() == QColor(255, 0, 0)
