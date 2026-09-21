"""Showcase window with native Windows 11 Mica Alt (Tabbed) backdrop material."""

import sys
from pathlib import Path

from qtpy.QtGui import QFont
from qtpy.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
)

from qtframeless import FramelessMicaMainWindow, WindowCornerPreference


class MicaAltWindow(FramelessMicaMainWindow):
    """Frameless window with Windows 11 native Mica Alt backdrop."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, isAlt=True, **kwargs)
        self._setupContent()

    def _setupContent(self) -> None:
        """Configure Mica Alt backdrop, title bar, and content widgets."""
        self.setWindowTitle("Windows 11 Mica Alt Material")
        self.resize(760, 480)
        self.setMinimumSize(560, 360)
        self.windowCornerPreference = WindowCornerPreference.ROUND
        self.borderColor = None

        iconPath = Path(__file__).resolve().parent.parent / "logo.png"
        if iconPath.exists():
            self.setWindowIcon(str(iconPath))

        # Configure TitleBar
        titleBar = self.getTitleBar()
        if titleBar is not None:
            titleBar.setTitleBarFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
            titleBar.setIconSize(18, 18)
            titleBar.setTitleBarHint(["min", "max", "close"])

        # Build minimal content with centered Toggle Theme button
        centralWidget = self.centralWidget()
        if centralWidget is not None:
            layout = centralWidget.layout()
            if layout is not None:
                contentLayout = QVBoxLayout()
                contentLayout.addStretch()

                buttonRow = QHBoxLayout()
                buttonRow.addStretch()

                themeToggleButton = QPushButton("Toggle Dark / Light Theme")
                themeToggleButton.setMinimumHeight(38)
                themeToggleButton.setMinimumWidth(220)
                themeToggleButton.clicked.connect(self._toggleTheme)
                buttonRow.addWidget(themeToggleButton)

                buttonRow.addStretch()
                contentLayout.addLayout(buttonRow)
                contentLayout.addStretch()

                layout.addLayout(contentLayout)

    def _toggleTheme(self) -> None:
        """Toggle dark/light theme dynamically."""
        self.darkTheme = not self.darkTheme


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MicaAltWindow()
    window.show()
    sys.exit(app.exec())
