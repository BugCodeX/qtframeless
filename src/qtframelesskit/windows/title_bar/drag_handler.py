"""Mouse interaction and window drag handler for frameless title bars.

Coordinates native system window drag initiation and maximize/restore toggling
upon double click while respecting interactive child widgets and menu bars.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import QPoint, Qt
from qtpy.QtGui import QMouseEvent
from qtpy.QtWidgets import QWidget

if TYPE_CHECKING:
    from .title_bar import TitleBar

__all__ = ["TitleBarDragHandler"]


class TitleBarDragHandler:
    """Handles native window dragging and maximize toggling via mouse interactions."""

    def __init__(self, titleBar: TitleBar) -> None:
        """Initialize drag handler associated with a title bar instance.

        Parameters
        ----------
        titleBar : TitleBar
            The parent TitleBar instance to manage mouse dragging and double clicks for.
        """
        self._titleBar = titleBar

    def isMenuBarClick(self, clickPosition: QPoint, targetChild: QWidget | None) -> bool:
        """Determine whether a click position or child widget belongs to the integrated menu bar.

        Parameters
        ----------
        clickPosition : QPoint
            The position of the mouse click in title bar coordinates.
        targetChild : QWidget or None
            The child widget located at the click position, or None if none.

        Returns
        -------
        bool
            True if the click targets the menu bar or one of its child widgets, False otherwise.
        """
        menuBar = self._titleBar.getMenuBar()
        if menuBar is None:
            return False
        isChildOfMenuBar = targetChild is not None and (
            targetChild is menuBar or menuBar.isAncestorOf(targetChild)
        )
        resolvedPoint = (
            clickPosition.toPoint() if hasattr(clickPosition, "toPoint") else clickPosition
        )
        return isChildOfMenuBar or menuBar.geometry().contains(resolvedPoint)

    def isInteractiveChild(self, childWidget: QWidget | None, clickPosition: QPoint) -> bool:
        """Determine whether a child widget or click position represents an interactive element.

        Parameters
        ----------
        childWidget : QWidget or None
            The child widget at the interaction position.
        clickPosition : QPoint
            The position of the mouse interaction in title bar coordinates.

        Returns
        -------
        bool
            True if the child widget is an interactive center widget or menu bar, False otherwise.
        """
        centerWidget = self._titleBar.getCenterWidget()
        isCenterInteractive = (
            centerWidget is not None
            and childWidget is not None
            and (childWidget is centerWidget or centerWidget.isAncestorOf(childWidget))
        )
        isMenuBarInteractive = self.isMenuBarClick(clickPosition, childWidget)
        return isCenterInteractive or isMenuBarInteractive

    def handleMousePress(self, event: QMouseEvent) -> bool:
        """Handle mouse press event on title bar to initiate system window drag.

        Parameters
        ----------
        event : QMouseEvent
            The mouse press event.

        Returns
        -------
        bool
            True if system move was initiated and the event accepted, False otherwise.
        """
        if event.button() == Qt.MouseButton.LeftButton and self._titleBar.isPressToMove():
            clickPosition = (
                event.position().toPoint() if hasattr(event, "position") else event.pos()
            )
            targetChild = self._titleBar.childAt(clickPosition)
            isMenuBar = self.isMenuBarClick(clickPosition, targetChild)
            isDraggableWidget = not isMenuBar and targetChild in (
                None,
                self._titleBar.getTitle(),
                self._titleBar.getIcon(),
                self._titleBar._centerContainer,
                self._titleBar._cornerWidget,
            )
            if isDraggableWidget:
                targetWindow = self._titleBar.window()
                if targetWindow:
                    windowHandle = targetWindow.windowHandle()
                    if windowHandle:
                        windowHandle.startSystemMove()
                        event.accept()
                        return True
        return False

    def handleMouseDoubleClick(self, event: QMouseEvent) -> bool:
        """Handle mouse double-click event to toggle window maximized state.

        Parameters
        ----------
        event : QMouseEvent
            The mouse double-click event.

        Returns
        -------
        bool
            True if double click was handled and window maximized or restored, False otherwise.
        """
        if getattr(self._titleBar, "_baseWindowResizable", True) and (
            event.button() == Qt.MouseButton.LeftButton
        ):
            clickPosition = (
                event.position().toPoint() if hasattr(event, "position") else event.pos()
            )
            targetChild = self._titleBar.childAt(clickPosition)
            if not self.isInteractiveChild(targetChild, clickPosition):
                self._titleBar._handleMaximizeClicked()
                event.accept()
                return True
        return False
