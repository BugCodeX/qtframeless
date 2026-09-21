"""Showcase frameless main window with integrated QMenuBar and centered title.

Demonstrates:
1. Integrated QMenuBar inside TitleBar with keyboard mnemonics (File, Edit, Settings).
2. Centered window title using TitleBar title alignment.
3. Centered clock display and dynamic light/dark theme toggle.
4. Windows 11 rounded corners and border styling.
"""

import sys
from pathlib import Path

from qtpy.QtCore import Qt, QTime, QTimer
from qtpy.QtGui import QAction, QFont, QIcon
from qtpy.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMenuBar,
    QPushButton,
    QVBoxLayout,
)

from qtframelesskit import FramelessMainWindow, WindowCornerPreference


class Window(FramelessMainWindow):
    """Frameless main window showcasing integrated QMenuBar and centered title."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._setupWindow()

    def _setupWindow(self) -> None:
        """Configure main window properties, title bar, menu bar, and central content."""
        self.setWindowTitle("Example MainWindow")
        self.resize(850, 520)
        self.setMinimumSize(600, 380)

        iconPath = Path(__file__).resolve().parent / "logo.png"
        if iconPath.exists():
            self.setWindowIcon(QIcon(str(iconPath)))

        # Configure modern Windows 11 corner rounding and border accent
        self.darkTheme = False
        self.windowCornerPreference = WindowCornerPreference.ROUND
        self.borderColor = "#696969"

        # 1. Configure TitleBar with centered title alignment
        titleBar = self.getTitleBar()
        if titleBar is not None:
            titleBar.setTitleAlignment(Qt.AlignmentFlag.AlignCenter)
            titleBar.setTitleBarFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
            titleBar.setIconSize(18, 18)
            titleBar.setTitleBarHint(["min", "max", "close"])

        # 2. Integrate QMenuBar into the TitleBar
        menuBar = self.menuBar()
        self._setupMenuBar(menuBar)

        # 3. Build central content with clock display and theme toggle
        self._setupCentralContent()

    def _setupMenuBar(self, menuBar: QMenuBar) -> None:
        """Populate the integrated QMenuBar with File, Edit, and Settings menus.

        Parameters
        ----------
        menuBar : QMenuBar
            The menu bar instance attached to the title bar.
        """
        # File Menu
        fileMenu = menuBar.addMenu("File(&F)")
        newAction = QAction("New(&N)", self)
        newAction.setShortcut("Ctrl+N")
        fileMenu.addAction(newAction)

        openAction = QAction("Open(&O)...", self)
        openAction.setShortcut("Ctrl+O")
        fileMenu.addAction(openAction)

        saveAction = QAction("Save(&S)", self)
        saveAction.setShortcut("Ctrl+S")
        fileMenu.addAction(saveAction)

        fileMenu.addSeparator()

        exitAction = QAction("Exit(&X)", self)
        exitAction.setShortcut("Alt+F4")
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

        # Edit Menu
        editMenu = menuBar.addMenu("Edit(&E)")
        undoAction = QAction("Undo(&U)", self)
        undoAction.setShortcut("Ctrl+Z")
        editMenu.addAction(undoAction)

        redoAction = QAction("Redo(&R)", self)
        redoAction.setShortcut("Ctrl+Y")
        editMenu.addAction(redoAction)

        editMenu.addSeparator()

        cutAction = QAction("Cut(&T)", self)
        cutAction.setShortcut("Ctrl+X")
        editMenu.addAction(cutAction)

        copyAction = QAction("Copy(&C)", self)
        copyAction.setShortcut("Ctrl+C")
        editMenu.addAction(copyAction)

        pasteAction = QAction("Paste(&P)", self)
        pasteAction.setShortcut("Ctrl+V")
        editMenu.addAction(pasteAction)

        # Settings Menu
        settingsMenu = menuBar.addMenu("Settings(&S)")
        themeAction = QAction("Toggle Theme(&T)", self)
        themeAction.setShortcut("Ctrl+T")
        themeAction.triggered.connect(self._toggleTheme)
        settingsMenu.addAction(themeAction)

        preferencesAction = QAction("Preferences(&P)...", self)
        preferencesAction.setShortcut("Ctrl+,")
        settingsMenu.addAction(preferencesAction)

    def _setupCentralContent(self) -> None:
        """Create and embed the clock display and theme switcher inside the central widget."""
        centralWidget = self.centralWidget()
        if centralWidget is None:
            return

        layout = centralWidget.layout()
        if layout is None:
            return

        contentLayout = QVBoxLayout()
        contentLayout.addStretch()

        # Digital clock display
        self._clockLabel = QLabel()
        self._clockLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._clockLabel.setFont(QFont("Segoe UI", 38, QFont.Weight.Bold))
        self._updateClock()
        contentLayout.addWidget(self._clockLabel)

        # Descriptive subtitle
        subtitleLabel = QLabel("Centered Title & Integrated QMenuBar Showcase")
        subtitleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitleLabel.setFont(QFont("Segoe UI", 12))
        contentLayout.addWidget(subtitleLabel)

        contentLayout.addSpacing(24)

        # Centered theme toggle button
        buttonRowLayout = QHBoxLayout()
        buttonRowLayout.addStretch()

        self._themeToggleButton = QPushButton("🌙 Switch to Dark Theme")
        self._themeToggleButton.setMinimumHeight(40)
        self._themeToggleButton.setMinimumWidth(240)
        self._themeToggleButton.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        self._themeToggleButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self._themeToggleButton.clicked.connect(self._toggleTheme)
        buttonRowLayout.addWidget(self._themeToggleButton)

        buttonRowLayout.addStretch()
        contentLayout.addLayout(buttonRowLayout)
        contentLayout.addStretch()

        layout.addLayout(contentLayout)

        # Periodic timer updating clock display
        self._clockTimer = QTimer(self)
        self._clockTimer.setInterval(1000)
        self._clockTimer.timeout.connect(self._updateClock)
        self._clockTimer.start()

    def _updateClock(self) -> None:
        """Update clock display label text with the current local time."""
        self._clockLabel.setText(QTime.currentTime().toString("hh:mm:ss AP"))

    def _toggleTheme(self) -> None:
        """Toggle dark and light window themes dynamically."""
        self.darkTheme = not self.darkTheme
        if self.darkTheme:
            self._themeToggleButton.setText("☀️ Switch to Light Theme")
        else:
            self._themeToggleButton.setText("🌙 Switch to Dark Theme")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
