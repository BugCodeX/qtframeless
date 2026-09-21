"""Minimal example demonstrating a frameless QMainWindow with custom TitleBar."""

import sys
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QHBoxLayout, QPushButton, QVBoxLayout

from qtframeless import FramelessMainWindow, WindowCornerPreference


class Window(FramelessMainWindow):
    """Frameless QMainWindow window showcase."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._setupContent()

    def _setupContent(self) -> None:
        """Configure main window properties, title bar, and central content."""
        self.setWindowTitle("QtFrameless MainWindow")
        iconPath = Path(__file__).resolve().parent / "logo.png"
        if iconPath.exists():
            self.setWindowIcon(str(iconPath))

        # Modern Qt property usage
        self.darkTheme = False
        self.windowCornerPreference = WindowCornerPreference.ROUND
        self.borderColor = "#696969"

        titleBar = self.getTitleBar()
        if titleBar is not None:
            titleBar.setTitleBarFont(QFont("Segoe UI", 11))
            titleBar.setIconSize(20, 20)
            titleBar.setTitleBarHint(["min", "max", "close"])

        centralWidget = self.centralWidget()
        if centralWidget is not None:
            layout = centralWidget.layout()
            if layout is not None:
                contentLayout = QVBoxLayout()
                contentLayout.addStretch()

                buttonRowLayout = QHBoxLayout()
                buttonRowLayout.addStretch()

                themeToggleButton = QPushButton("Toggle Dark / Light Theme")
                themeToggleButton.setMinimumHeight(38)
                themeToggleButton.setMinimumWidth(220)
                themeToggleButton.clicked.connect(self._toggleTheme)
                buttonRowLayout.addWidget(themeToggleButton)

                buttonRowLayout.addStretch()
                contentLayout.addLayout(buttonRowLayout)
                contentLayout.addStretch()

                layout.addLayout(contentLayout)

    def _toggleTheme(self) -> None:
        """Toggle dark and light window themes dynamically."""
        self.darkTheme = not self.darkTheme


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.resize(800, 500)
    window.show()
    sys.exit(app.exec())
