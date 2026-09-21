"""Showcase window with native Fluent Acrylic blur-behind backdrop material."""

import sys
from pathlib import Path

from qtpy.QtGui import QFont
from qtpy.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
)

from qtframelesskit import FramelessAcrylicMainWindow, WindowCornerPreference


class AcrylicWindow(FramelessAcrylicMainWindow):
    """Frameless window with Windows Acrylic blur-behind backdrop."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, gradientColor="F2F2F299", **kwargs)
        self._setupContent()

    def _setupContent(self) -> None:
        """Configure Acrylic backdrop, title bar, and content widgets."""
        self.setWindowTitle("Windows Acrylic Material")
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
        """Toggle dark/light theme dynamically and update Acrylic gradient color."""
        self.darkTheme = not self.darkTheme
        self.setGradientColor("20202099" if self.darkTheme else "F2F2F299")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AcrylicWindow()
    window.show()
    sys.exit(app.exec())
