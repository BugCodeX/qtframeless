"""Vector-rendered window control buttons for frameless windows.

Provides vector-drawn minimize, maximize/restore, close, and fullscreen toggle buttons
using QPainter, supporting dark/light theme switching, DPI scaling, and custom hover/pressed colors.
"""

import sys

from qtpy.QtCore import QEvent, QPointF, QRectF, Qt, QVariantAnimation
from qtpy.QtGui import QColor, QMouseEvent, QPaintEvent, QPen
from qtpy.QtGui import QPainter as _QtQPainter
from qtpy.QtWidgets import QPushButton, QWidget

__all__ = [
    "CloseButton",
    "FullScreenButton",
    "MaximizeButton",
    "MinimizeButton",
    "VectorButton",
]


def _getPainterClass() -> type:
    """Return active QPainter class, respecting title_bar module monkeypatching.

    Returns
    -------
    type
        The QPainter class or monkeypatched mock.
    """
    titleBarModule = sys.modules.get("qtframeless.windows.title_bar")
    if titleBarModule is not None and hasattr(titleBarModule, "QPainter"):
        return titleBarModule.QPainter
    return _QtQPainter


class VectorButton(QPushButton):
    """Base QPushButton subclass rendering crisp vector shapes via QPainter.

    Parameters
    ----------
    parent : QWidget, optional
        Parent widget holding this button.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._isDarkTheme = False
        self._isHovered = False
        self._isPressed = False
        self._glyphColor = QColor("#333333")
        self._hoverGlyphColor = QColor("#111111")
        self._customHoverColor: QColor | None = None
        self._customPressedColor: QColor | None = None
        self._currentBackgroundColor = self._getIdleColor()
        self._buttonWidth = 46
        self._buttonHeight = 30
        self.setFixedSize(self._buttonWidth, self._buttonHeight)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._colorAnimation = QVariantAnimation(self)
        self._colorAnimation.setDuration(120)
        self._colorAnimation.valueChanged.connect(self._onBackgroundColorChanged)

    def _onBackgroundColorChanged(self, color: QColor) -> None:
        """Update the active background color and request a widget repaint.

        Parameters
        ----------
        color : QColor
            Interpolated background color.
        """
        self._currentBackgroundColor = color
        self.update()

    def getCurrentBackgroundColor(self) -> QColor:
        """Return the current interpolated background color.

        Returns
        -------
        QColor
            Current background color.
        """
        return self._currentBackgroundColor

    def isHovered(self) -> bool:
        """Return whether the button is in a hovered visual state.

        Returns
        -------
        bool
            True if hovered directly or via non-client messages, False otherwise.
        """
        return self._isHovered or self.underMouse()

    def setHoverState(self, hovered: bool) -> None:
        """Set the hover visual state when handling non-client messages.

        Parameters
        ----------
        hovered : bool
            True to show hover styling, False to clear.
        """
        if self._isHovered != hovered:
            self._isHovered = hovered
            self._animateToTargetColor()

    def isPressedState(self) -> bool:
        """Return whether the button is in a pressed visual state.

        Returns
        -------
        bool
            True if pressed directly or via non-client messages, False otherwise.
        """
        return self._isPressed or self.isDown()

    def setPressedState(self, pressed: bool) -> None:
        """Set the pressed visual state when handling non-client mouse click messages.

        Parameters
        ----------
        pressed : bool
            True to show pressed styling, False to clear.
        """
        if self._isPressed != pressed or self.isDown() != pressed:
            self._isPressed = pressed
            self.setDown(pressed)
            self._animateToTargetColor()

    def enterEvent(self, event: QEvent) -> None:
        """Handle mouse enter event and trigger background hover transition.

        Parameters
        ----------
        event : QEvent
            Mouse enter event.
        """
        self._isHovered = True
        super().enterEvent(event)
        self._animateToTargetColor()

    def leaveEvent(self, event: QEvent) -> None:
        """Handle mouse leave event and trigger background restore transition.

        Parameters
        ----------
        event : QEvent
            Mouse leave event.
        """
        self._isHovered = False
        self._isPressed = False
        super().leaveEvent(event)
        self._animateToTargetColor()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press event and trigger background pressed transition.

        Parameters
        ----------
        event : QMouseEvent
            Mouse press event.
        """
        super().mousePressEvent(event)
        self._animateToTargetColor()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release event and transition to hover or idle color.

        Parameters
        ----------
        event : QMouseEvent
            Mouse release event.
        """
        super().mouseReleaseEvent(event)
        self._animateToTargetColor()

    def _getHoverColor(self) -> QColor:
        """Return target background color when button is hovered.

        Uses crisp Windows 11 contrasting tones (#cfcfcf light, #3f3f3f dark)
        so the button highlight remains distinct on both opaque windows and
        translucent backdrop materials like Mica Alt, Mica, and Acrylic.

        Returns
        -------
        QColor
            Hover target color according to current theme or custom override.
        """
        if self._customHoverColor is not None:
            return self._customHoverColor
        return QColor("#3f3f3f") if self._isDarkTheme else QColor("#cfcfcf")

    def _getPressedColor(self) -> QColor:
        """Return target background color when button is pressed down.

        Returns
        -------
        QColor
            Pressed target color according to current theme or custom override.
        """
        if self._customPressedColor is not None:
            return self._customPressedColor
        return QColor("#525252") if self._isDarkTheme else QColor("#b8b8b8")

    def getHoverColor(self) -> QColor:
        """Return the effective background color applied when hovered.

        Returns
        -------
        QColor
            Current hover color.
        """
        return self._getHoverColor()

    def setHoverColor(self, color: QColor | str | None) -> None:
        """Configure a custom hover background color.

        Parameters
        ----------
        color : QColor, str, or None
            Custom hover color, or None to revert to theme default.
        """
        if color is None:
            self._customHoverColor = None
        elif isinstance(color, QColor):
            self._customHoverColor = QColor(color)
        else:
            self._customHoverColor = QColor(color)
        self._animateToTargetColor()

    def getPressedColor(self) -> QColor:
        """Return the effective background color applied when pressed down.

        Returns
        -------
        QColor
            Current pressed color.
        """
        return self._getPressedColor()

    def setPressedColor(self, color: QColor | str | None) -> None:
        """Configure a custom pressed background color.

        Parameters
        ----------
        color : QColor, str, or None
            Custom pressed color, or None to revert to theme default.
        """
        if color is None:
            self._customPressedColor = None
        elif isinstance(color, QColor):
            self._customPressedColor = QColor(color)
        else:
            self._customPressedColor = QColor(color)
        self._animateToTargetColor()

    def _getIdleColor(self) -> QColor:
        """Return transparent base color aligned with hover RGB to avoid dark flash.

        Returns
        -------
        QColor
            Transparent idle color sharing the hover RGB components.
        """
        hover = self._getHoverColor()
        return QColor(hover.red(), hover.green(), hover.blue(), 0)

    def _getTargetColor(self) -> QColor:
        """Determine target background color based on hover and pressed states.

        Returns
        -------
        QColor
            Target color for the current state.
        """
        if self.isPressedState():
            return self._getPressedColor()
        if self.isHovered():
            return self._getHoverColor()
        return self._getIdleColor()

    def _animateToTargetColor(self) -> None:
        """Start or redirect background color interpolation toward current target."""
        targetColor = self._getTargetColor()
        if (
            self._currentBackgroundColor == targetColor
            and self._colorAnimation.state() == QVariantAnimation.State.Stopped
        ):
            return
        self._colorAnimation.stop()
        self._colorAnimation.setStartValue(self._currentBackgroundColor)
        self._colorAnimation.setEndValue(targetColor)
        self._colorAnimation.start()

    def setDarkTheme(self, isDark: bool) -> None:
        """Update button stroke and hover background styles for dark mode.

        Parameters
        ----------
        isDark : bool
            True to apply dark theme styles, False for light theme.
        """
        self._isDarkTheme = isDark
        if isDark:
            self._glyphColor = QColor("#ffffff")
            self._hoverGlyphColor = QColor("#ffffff")
        else:
            self._glyphColor = QColor("#333333")
            self._hoverGlyphColor = QColor("#111111")
        if not self.isHovered() and not self.isPressedState():
            self._currentBackgroundColor = self._getIdleColor()
            self.update()
        else:
            self._animateToTargetColor()

    def setGlyphColor(self, color: QColor) -> None:
        """Set the normal stroke color for the vector glyph.

        Parameters
        ----------
        color : QColor
            New stroke color for the glyph.
        """
        self._glyphColor = color
        self.update()

    def getGlyphColor(self) -> QColor:
        """Return the normal stroke color of the vector glyph.

        Returns
        -------
        QColor
            Current stroke color.
        """
        return self._glyphColor

    def updateButtonHeight(self, newHeight: int) -> None:
        """Update button height maintaining proportional width.

        Parameters
        ----------
        newHeight : int
            New button height in pixels.
        """
        self._buttonHeight = max(24, newHeight)
        self._buttonWidth = round(self._buttonHeight * 1.4)
        self.setFixedSize(self._buttonWidth, self._buttonHeight)

    def getGlyphScaleFactor(self) -> float:
        """Return a subtle scaling factor for vector glyphs relative to base height.

        Dampens scaling so glyph symbols only grow slightly at high DPI rather
        than scaling linearly with button height (e.g. 1.25x at 200% scaling).

        Returns
        -------
        float
            Dampened scale multiplier where 1.0 corresponds to standard 30px height.
        """
        rawRatio = self._buttonHeight / 30.0
        return max(0.85, 1.0 + (rawRatio - 1.0) * 0.25)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint button background directly using QPainter without native chrome.

        Leaves idle buttons completely transparent so parent window or title bar
        backgrounds show through cleanly, only rendering hover or pressed fill
        when the background color has positive alpha.

        Parameters
        ----------
        event : QPaintEvent
            The paint event.
        """
        if self._currentBackgroundColor.alpha() > 0:
            painter = _getPainterClass()(self)
            painter.fillRect(self.rect(), self._currentBackgroundColor)
            painter.end()


class MinimizeButton(VectorButton):
    """Window minimize button rendering a vector horizontal line glyph."""

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint vector minimize horizontal line.

        Parameters
        ----------
        event : QPaintEvent
            The paint event.
        """
        super().paintEvent(event)
        painterClass = _getPainterClass()
        painter = painterClass(self)
        painter.setRenderHint(painterClass.RenderHint.Antialiasing)

        scaleFactor = self.getGlyphScaleFactor()
        strokeColor = self._hoverGlyphColor if self.isHovered() else self._glyphColor
        pen = QPen(strokeColor, max(1.0, round(1.2 * scaleFactor, 1)))
        painter.setPen(pen)

        centerX = self.width() / 2.0
        centerY = self.height() / 2.0
        halfWidth = 5.0 * scaleFactor
        painter.drawLine(
            QPointF(centerX - halfWidth, centerY),
            QPointF(centerX + halfWidth, centerY),
        )
        painter.end()


class MaximizeButton(VectorButton):
    """Window maximize and restore button rendering vector rectangles."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._isMaximized = False

    def isMaximizedState(self) -> bool:
        """Return whether the button displays the restored or maximized glyph.

        Returns
        -------
        bool
            True if currently displaying restored glyph for a maximized window.
        """
        return self._isMaximized

    def setMaximizedState(self, isMaximized: bool) -> None:
        """Update button glyph state to reflect window maximize status.

        Parameters
        ----------
        isMaximized : bool
            True if the parent window is maximized.
        """
        if self._isMaximized != isMaximized:
            self._isMaximized = isMaximized
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint vector rectangle or overlapping restore rectangles.

        Parameters
        ----------
        event : QPaintEvent
            The paint event.
        """
        super().paintEvent(event)
        painterClass = _getPainterClass()
        painter = painterClass(self)
        painter.setRenderHint(painterClass.RenderHint.Antialiasing)

        isHovered = self.isHovered()

        scaleFactor = self.getGlyphScaleFactor()
        strokeColor = self._hoverGlyphColor if isHovered else self._glyphColor
        pen = QPen(strokeColor, max(1.0, round(1.2 * scaleFactor, 1)))
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        centerX = self.width() / 2.0
        centerY = self.height() / 2.0

        if self._isMaximized:
            # Draw background offset rectangle
            backRectPoints = [
                QPointF(centerX - 3.0 * scaleFactor, centerY - 3.0 * scaleFactor),
                QPointF(centerX - 3.0 * scaleFactor, centerY - 5.5 * scaleFactor),
                QPointF(centerX + 4.5 * scaleFactor, centerY - 5.5 * scaleFactor),
                QPointF(centerX + 4.5 * scaleFactor, centerY + 2.0 * scaleFactor),
                QPointF(centerX + 2.5 * scaleFactor, centerY + 2.0 * scaleFactor),
            ]
            painter.drawPolyline(backRectPoints)
            # Draw foreground rectangle
            frontRect = QRectF(
                centerX - 5.5 * scaleFactor,
                centerY - 3.0 * scaleFactor,
                8.0 * scaleFactor,
                8.0 * scaleFactor,
            )
            painter.drawRect(frontRect)
        else:
            # Draw single maximize square
            squareRect = QRectF(
                centerX - 4.5 * scaleFactor,
                centerY - 4.5 * scaleFactor,
                9.0 * scaleFactor,
                9.0 * scaleFactor,
            )
            painter.drawRect(squareRect)

        painter.end()


class CloseButton(VectorButton):
    """Window close button with diagonal cross vector glyph and red highlight."""

    def _getHoverColor(self) -> QColor:
        """Return target red hover background color.

        Returns
        -------
        QColor
            Red hover highlight color.
        """
        if self._customHoverColor is not None:
            return self._customHoverColor
        return QColor("#e81123")

    def _getPressedColor(self) -> QColor:
        """Return target light red pressed background color.

        Returns
        -------
        QColor
            Light red pressed highlight color.
        """
        if self._customPressedColor is not None:
            return self._customPressedColor
        return QColor("#f1707a")

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint vector diagonal cross glyph with white stroke on hover/press.

        Parameters
        ----------
        event : QPaintEvent
            The paint event.
        """
        super().paintEvent(event)
        painterClass = _getPainterClass()
        painter = painterClass(self)
        painter.setRenderHint(painterClass.RenderHint.Antialiasing)

        # White glyph on hover/pressed red background, normal color otherwise
        isHighlighted = self.isHovered() or self.isPressedState()
        strokeColor = QColor("#ffffff") if isHighlighted else self._glyphColor
        scaleFactor = self.getGlyphScaleFactor()
        pen = QPen(strokeColor, max(1.0, round(1.2 * scaleFactor, 1)))
        painter.setPen(pen)

        centerX = self.width() / 2.0
        centerY = self.height() / 2.0
        crossOffset = 4.5 * scaleFactor

        painter.drawLine(
            QPointF(centerX - crossOffset, centerY - crossOffset),
            QPointF(centerX + crossOffset, centerY + crossOffset),
        )
        painter.drawLine(
            QPointF(centerX - crossOffset, centerY + crossOffset),
            QPointF(centerX + crossOffset, centerY - crossOffset),
        )
        painter.end()


class FullScreenButton(VectorButton):
    """Window fullscreen toggle button rendering vector frame glyph."""

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint vector fullscreen glyph.

        Parameters
        ----------
        event : QPaintEvent
            The paint event.
        """
        super().paintEvent(event)
        painterClass = _getPainterClass()
        painter = painterClass(self)
        painter.setRenderHint(painterClass.RenderHint.Antialiasing)

        scaleFactor = self.getGlyphScaleFactor()
        strokeColor = self._hoverGlyphColor if self.isHovered() else self._glyphColor
        pen = QPen(strokeColor, max(1.0, round(1.2 * scaleFactor, 1)))
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        centerX = self.width() / 2.0
        centerY = self.height() / 2.0
        frameSize = 10.0 * scaleFactor
        frameRect = QRectF(
            centerX - (frameSize / 2.0), centerY - (frameSize / 2.0), frameSize, frameSize
        )
        painter.drawRect(frameRect)
        painter.end()
