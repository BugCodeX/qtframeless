"""Custom title bar widget and vector-rendered control buttons for frameless windows.

Provides vector-drawn minimize, maximize/restore, and close buttons using QPainter,
integrated title and icon displays, and event filtering using official Qt enums.
"""

from qtpy.QtCore import QEvent, Qt
from qtpy.QtGui import (
    QColor,
    QFont,
    QIcon,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPalette,
)
from qtpy.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from .buttons import (
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
    "TitleBar",
    "VectorButton",
]


class TitleBar(QWidget):
    """Custom title bar widget with vector control buttons and event filtering.

    Parameters
    ----------
    parentWidget : QWidget, optional
        Parent window owning this title bar.
    hint : list of str, optional
        Button hints controlling which control buttons to display.
    base_widget : QWidget, optional
        Legacy alias for parentWidget.
    """

    def __init__(
        self,
        parentWidget: QWidget | None = None,
        hint: list[str] | None = None,
        base_widget: QWidget | None = None,
    ) -> None:
        resolvedParent = parentWidget if parentWidget is not None else base_widget
        super().__init__(resolvedParent)
        self._isDarkTheme = False
        self._pressToMove = True
        self._baseWindowResizable = True
        self._currentDpi = 96
        self._baseIconWidth = 18
        self._baseIconHeight = 18
        self._baseButtonHeight = 30
        self._backgroundColor: QColor | None = None

        self._iconLabel = QLabel()
        self._titleLabel = QLabel()
        self._baseFont = QFont(self._titleLabel.font())
        self._centerContainer = QWidget(self)
        centerLayout = QHBoxLayout()
        centerLayout.setContentsMargins(0, 0, 0, 0)
        centerLayout.setSpacing(0)
        self._centerContainer.setLayout(centerLayout)
        self._centerContainer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self._centerWidget: QWidget | None = None
        self._cornerWidget = QWidget(self)
        self._cornerWidget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._fullScreenButton = FullScreenButton(self)
        self._minimizeButton = MinimizeButton(self)
        self._maximizeButton = MaximizeButton(self)
        self._closeButton = CloseButton(self)

        self._fullScreenButton.setCheckable(True)
        self._buttonDict = {
            "full_screen": self._fullScreenButton,
            "min": self._minimizeButton,
            "max": self._maximizeButton,
            "close": self._closeButton,
        }

        self._connectButtonSignals()
        self._initUi(hint)

        targetWindow = self.window()
        if targetWindow and targetWindow is not self:
            targetWindow.installEventFilter(self)

        for candidate in (resolvedParent, targetWindow):
            if candidate is not None and candidate is not self:
                try:
                    themeSignal = getattr(candidate, "darkThemeChanged", None)
                    if themeSignal is not None and hasattr(themeSignal, "connect"):
                        themeSignal.connect(self._handleThemeChanged)
                        if hasattr(candidate, "isDarkTheme") and callable(candidate.isDarkTheme):
                            if candidate.isDarkTheme():
                                self.setDarkTheme(True)
                        break
                except Exception:
                    pass

    def _connectButtonSignals(self) -> None:
        """Connect button click signals to parent window action slots."""
        self._fullScreenButton.clicked.connect(self._handleFullScreenClicked)
        self._minimizeButton.clicked.connect(self._handleMinimizeClicked)
        self._maximizeButton.clicked.connect(self._handleMaximizeClicked)
        self._closeButton.clicked.connect(self._handleCloseClicked)

    def _initUi(self, hint: list[str] | None) -> None:
        """Build title bar layout, setting icon, title, and button controls."""
        mainLayout = QHBoxLayout()
        mainLayout.setContentsMargins(8, 0, 0, 0)
        mainLayout.setSpacing(0)
        mainLayout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self._iconLabel.setContentsMargins(4, 4, 4, 4)
        self._titleLabel.setContentsMargins(4, 4, 4, 4)
        textColor = "#ffffff" if self._isDarkTheme else "#000000"
        titlePalette = self._titleLabel.palette()
        titlePalette.setColor(QPalette.ColorRole.WindowText, QColor(textColor))
        self._titleLabel.setPalette(titlePalette)

        mainLayout.addWidget(self._iconLabel)
        mainLayout.addWidget(self._titleLabel)
        mainLayout.addWidget(self._centerContainer)

        cornerLayout = QHBoxLayout()
        cornerLayout.setContentsMargins(0, 0, 0, 0)
        cornerLayout.setSpacing(0)
        for button in self._buttonDict.values():
            cornerLayout.addWidget(button)
        self._cornerWidget.setLayout(cornerLayout)

        self.setTitleBarHint(hint)
        mainLayout.addWidget(self._cornerWidget)
        self.setLayout(mainLayout)

    def _handleMinimizeClicked(self) -> None:
        """Minimize the top-level parent window."""
        targetWindow = self.window()
        if targetWindow:
            targetWindow.showMinimized()

    def _handleMaximizeClicked(self) -> None:
        """Toggle normal and maximized state of the parent window."""
        targetWindow = self.window()
        if not targetWindow:
            return
        if targetWindow.isMaximized():
            targetWindow.showNormal()
        else:
            targetWindow.showMaximized()

    def _handleFullScreenClicked(self) -> None:
        """Toggle fullscreen state of the parent window."""
        targetWindow = self.window()
        if not targetWindow:
            return
        if targetWindow.isFullScreen():
            targetWindow.showNormal()
        else:
            targetWindow.showFullScreen()

    def _handleCloseClicked(self) -> None:
        """Close the parent window."""
        targetWindow = self.window()
        if targetWindow:
            targetWindow.close()

    def _handleThemeChanged(self, isDark: bool) -> None:
        """Update label text colors and vector button themes for dark mode.

        Parameters
        ----------
        isDark : bool
            True if dark mode is active, False for light mode.
        """
        self._isDarkTheme = isDark
        textColor = "#ffffff" if isDark else "#000000"
        titlePalette = self._titleLabel.palette()
        titlePalette.setColor(QPalette.ColorRole.WindowText, QColor(textColor))
        self._titleLabel.setPalette(titlePalette)

        for button in self._buttonDict.values():
            if isinstance(button, VectorButton):
                button.setDarkTheme(isDark)

    def setDarkTheme(self, isDark: bool) -> None:
        """Configure dark or light theme styling on labels and vector buttons.

        Parameters
        ----------
        isDark : bool
            True to apply dark theme styles, False for light theme.
        """
        self._handleThemeChanged(isDark)

    def isDarkTheme(self) -> bool:
        """Return whether the title bar is currently configured with dark theme.

        Returns
        -------
        bool
            True if dark theme is active, False otherwise.
        """
        return self._isDarkTheme

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Toggle maximize state upon double-clicking the title bar.

        Parameters
        ----------
        event : QMouseEvent
            Mouse double-click event.
        """
        if self._baseWindowResizable and event.button() == Qt.MouseButton.LeftButton:
            clickPosition = (
                event.position().toPoint() if hasattr(event, "position") else event.pos()
            )
            targetChild = self.childAt(clickPosition)
            isInteractiveChild = (
                self._centerWidget is not None
                and targetChild is not None
                and (
                    targetChild is self._centerWidget
                    or self._centerWidget.isAncestorOf(targetChild)
                )
            )
            if not isInteractiveChild:
                self._handleMaximizeClicked()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start native system window drag when left clicking the title bar.

        Parameters
        ----------
        event : QMouseEvent
            Mouse press event.
        """
        if event.button() == Qt.MouseButton.LeftButton and self._pressToMove:
            clickPosition = (
                event.position().toPoint() if hasattr(event, "position") else event.pos()
            )
            targetChild = self.childAt(clickPosition)
            isDraggableWidget = targetChild in (
                None,
                self._titleLabel,
                self._iconLabel,
                self._centerContainer,
                self._cornerWidget,
            )
            if isDraggableWidget:
                targetWindow = self.window()
                if targetWindow:
                    windowHandle = targetWindow.windowHandle()
                    if windowHandle:
                        windowHandle.startSystemMove()
                        event.accept()
                        return
        super().mousePressEvent(event)

    def eventFilter(self, watchedObject: object, event: QEvent) -> bool:
        """Filter parent window state change and layout request events.

        Parameters
        ----------
        watchedObject : object
            The watched Qt object.
        event : QEvent
            The incoming Qt event.

        Returns
        -------
        bool
            True if event was handled, False to pass along.
        """
        if watchedObject is self.window():
            eventType = event.type()
            if eventType == QEvent.Type.WindowStateChange:
                targetWindow = self.window()
                isFullScreen = targetWindow.isFullScreen()
                isMaximized = targetWindow.isMaximized()

                self._fullScreenButton.setChecked(isFullScreen)
                self._maximizeButton.setChecked(isMaximized)
                self._maximizeButton.setMaximizedState(isMaximized)

                if isFullScreen:
                    self.hide()
                else:
                    self.show()
            elif eventType == QEvent.Type.LayoutRequest:
                self.setMaximumHeight(self.sizeHint().height())

        return super().eventFilter(watchedObject, event)

    def setIcon(self, icon: QIcon) -> None:
        """Set the window icon on the title bar with default 18x18 size.

        Parameters
        ----------
        icon : QIcon
            Icon to display.
        """
        self._windowIcon = icon
        self.setIconSize(18, 18)

    def setIconSize(self, width: int, height: int) -> None:
        """Set the icon pixel dimensions and adjust button heights.

        Parameters
        ----------
        width : int
            Target icon width in pixels.
        height : int
            Target icon height in pixels.
        """
        self._baseIconWidth = width
        self._baseIconHeight = height
        self._baseButtonHeight = height * 2
        scaledWidth = round(width * getattr(self, "_currentDpi", 96) / 96)
        scaledHeight = round(height * getattr(self, "_currentDpi", 96) / 96)
        if hasattr(self, "_windowIcon") and not self._windowIcon.isNull():
            self._iconLabel.setPixmap(self._windowIcon.pixmap(scaledWidth, scaledHeight))
        scaledButtonHeight = round(self._baseButtonHeight * getattr(self, "_currentDpi", 96) / 96)
        for button in self._buttonDict.values():
            if isinstance(button, VectorButton):
                button.updateButtonHeight(scaledButtonHeight)

    def setTitle(self, title: str) -> None:
        """Set the window title text.

        Parameters
        ----------
        title : str
            Title string to display.
        """
        self._titleLabel.setText(title)

    def setTitleBarFont(self, font: QFont) -> None:
        """Set the title label font and scale button heights proportionally.

        Parameters
        ----------
        font : QFont
            Font to apply to the title text.
        """
        self._baseFont = QFont(font)
        currentDpi = getattr(self, "_currentDpi", 96)
        scaleFactor = currentDpi / 96.0

        scaledFont = QFont(self._baseFont)
        basePoints = self._baseFont.pointSizeF()
        if basePoints > 0:
            scaledFont.setPointSizeF(basePoints * scaleFactor)
        else:
            basePixels = self._baseFont.pixelSize()
            if basePixels > 0:
                scaledFont.setPixelSize(round(basePixels * scaleFactor))
        self._titleLabel.setFont(scaledFont)

        self._baseButtonHeight = font.pointSize() * 2
        newButtonHeight = round(self._baseButtonHeight * scaleFactor)
        for button in self._buttonDict.values():
            if isinstance(button, VectorButton):
                button.updateButtonHeight(newButtonHeight)

    def updateDpiScaling(self, dpi: int) -> None:
        """Recalculate layout margins, button bounds, icon, and title font for new DPI.

        Parameters
        ----------
        dpi : int
            Active dots-per-inch scaling factor (e.g. 96 for 100%, 144 for 150%).
        """
        if dpi <= 0:
            dpi = 96
        self._currentDpi = dpi
        scaleFactor = dpi / 96.0

        if hasattr(self, "_baseFont"):
            scaledFont = QFont(self._baseFont)
            basePoints = self._baseFont.pointSizeF()
            if basePoints > 0:
                scaledFont.setPointSizeF(basePoints * scaleFactor)
            else:
                basePixels = self._baseFont.pixelSize()
                if basePixels > 0:
                    scaledFont.setPixelSize(round(basePixels * scaleFactor))
            self._titleLabel.setFont(scaledFont)

        scaledButtonHeight = max(24, round(self._baseButtonHeight * scaleFactor))
        for button in self._buttonDict.values():
            if isinstance(button, VectorButton):
                button.updateButtonHeight(scaledButtonHeight)

        if hasattr(self, "_windowIcon") and not self._windowIcon.isNull():
            scaledWidth = round(self._baseIconWidth * scaleFactor)
            scaledHeight = round(self._baseIconHeight * scaleFactor)
            self._iconLabel.setPixmap(self._windowIcon.pixmap(scaledWidth, scaledHeight))

        scaledMargin = max(2, round(4 * scaleFactor))
        self._iconLabel.setContentsMargins(scaledMargin, scaledMargin, scaledMargin, scaledMargin)
        self._titleLabel.setContentsMargins(scaledMargin, scaledMargin, scaledMargin, scaledMargin)

        scaledLayoutLeft = max(4, round(8 * scaleFactor))
        if self.layout() is not None:
            self.layout().setContentsMargins(scaledLayoutLeft, 0, 0, 0)

        self.updateGeometry()
        self.setMaximumHeight(self.sizeHint().height())

    def getCurrentDpi(self) -> int:
        """Return the active DPI scaling factor configured for the title bar.

        Returns
        -------
        int
            Active DPI value (e.g. 96 for 100%, 144 for 150%).
        """
        return getattr(self, "_currentDpi", 96)

    def setTitleBarHint(self, hint: list[str] | None) -> None:
        """Show only the control buttons specified in hint list.

        Parameters
        ----------
        hint : list of str or None
            Button keys to display ('min', 'max', 'close', 'full_screen').
            Defaults to standard set ('min', 'max', 'close') when None.
        """
        if hint is None:
            hint = ["min", "max", "close"]

        visibleSet = set(hint)
        for key, button in self._buttonDict.items():
            button.setVisible(key in visibleSet)

    def setPressToMove(self, enabled: bool) -> None:
        """Enable or disable dragging window from title bar.

        Parameters
        ----------
        enabled : bool
            True to enable press-to-move dragging.
        """
        self._pressToMove = enabled

    def isPressToMove(self) -> bool:
        """Return whether pressing title bar initiates window movement.

        Returns
        -------
        bool
            True if press to move is enabled.
        """
        return self._pressToMove

    def setBaseWindowResizable(self, resizable: bool) -> None:
        """Configure whether maximize button is enabled based on resizability.

        Parameters
        ----------
        resizable : bool
            True if the base window can be resized/maximized.
        """
        self._baseWindowResizable = resizable
        self._maximizeButton.setVisible(resizable)

    def getTitle(self) -> QLabel:
        """Return the QLabel widget displaying window title.

        Returns
        -------
        QLabel
            The title label widget.
        """
        return self._titleLabel

    def getIcon(self) -> QLabel:
        """Return the QLabel widget displaying window icon.

        Returns
        -------
        QLabel
            The icon label widget.
        """
        return self._iconLabel

    def getButtons(self) -> dict[str, QPushButton]:
        """Return mapping of button keys to QPushButton instances.

        Returns
        -------
        dict of str to QPushButton
            Dictionary of control buttons.
        """
        return self._buttonDict

    def getMaximizeButton(self) -> MaximizeButton | None:
        """Return the maximize button instance if present and not hidden.

        Returns
        -------
        MaximizeButton or None
            The maximize button instance, or None if omitted or hidden.
        """
        button = getattr(self, "_maximizeButton", None)
        if button is not None and not button.isHidden():
            return button
        return None

    def setCenterWidget(self, widget: QWidget | None) -> None:
        """Install or replace the custom widget hosted in the center area.

        Parameters
        ----------
        widget : QWidget or None
            Custom widget to place inside the center area, or None to clear.
        """
        if self._centerWidget is not None:
            self.removeCenterWidget()

        if widget is not None:
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            containerLayout = self._centerContainer.layout()
            if containerLayout is not None:
                containerLayout.addWidget(widget)
            self._centerWidget = widget

    def getCenterWidget(self) -> QWidget | None:
        """Return the custom widget currently hosted in the center area.

        Returns
        -------
        QWidget or None
            The installed center widget, or None if no widget is installed.
        """
        return self._centerWidget

    def removeCenterWidget(self) -> QWidget | None:
        """Remove and return the hosted center widget without destroying it.

        Returns
        -------
        QWidget or None
            The removed widget, or None if no center widget was installed.
        """
        if self._centerWidget is not None:
            detachedWidget = self._centerWidget
            containerLayout = self._centerContainer.layout()
            if containerLayout is not None:
                containerLayout.removeWidget(detachedWidget)
            detachedWidget.setParent(None)
            self._centerWidget = None
            return detachedWidget
        return None

    def getBackgroundColor(self) -> QColor | None:
        """Return the current background color of the title bar.

        Returns
        -------
        QColor or None
            Current background color, or None if using default window background.
        """
        return self._backgroundColor

    def setBackgroundColor(self, color: QColor | str | None) -> None:
        """Set the background color of the title bar and request a repaint.

        Parameters
        ----------
        color : QColor, str, or None
            New background color representation, or None to use default window background.
        """
        if color is None:
            self._backgroundColor = None
        elif isinstance(color, QColor):
            self._backgroundColor = QColor(color)
        else:
            self._backgroundColor = QColor(color)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint title bar background directly using QPainter without stylesheets.

        Uses CompositionMode_Source so transparent or custom background
        colors overwrite the backing store buffer cleanly without alpha-blending
        over previous frames.

        Parameters
        ----------
        event : QPaintEvent
            The paint event.
        """
        super().paintEvent(event)
        if self._backgroundColor is not None:
            painter = QPainter(self)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            painter.fillRect(self.rect(), self._backgroundColor)
            painter.end()
