"""Showcase frameless dialog with modern Fluent preferences and dynamic theming.

Demonstrates:
1. Native Windows 11 preferences dialog pattern with ⚙️ header and subtitle.
2. Settings card containing active DWM feature toggles and status badges.
3. Action bar featuring theme toggle, cancel action, and primary accent button.
4. Smooth theme transition between light and dark visual palettes.
"""

import sys
from pathlib import Path

from qtpy.QtCore import Qt
from qtpy.QtGui import QFont, QIcon
from qtpy.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from qtframelesskit import FramelessDialog, WindowCornerPreference


class Window(FramelessDialog):
    """Modern frameless preferences dialog showcase."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._setupContent()

    def _setupContent(self) -> None:
        """Configure dialog properties, title bar, and preferences content."""
        self.setWindowTitle("QtFrameless Dialog")
        self.resize(540, 360)
        self.setMinimumSize(480, 320)

        iconPath = Path(__file__).resolve().parent / "logo.png"
        if iconPath.exists():
            self.setWindowIcon(QIcon(str(iconPath)))

        # Configure modern Windows 11 corner rounding and border accent
        self.darkTheme = False
        self.windowCornerPreference = WindowCornerPreference.ROUND
        self.borderColor = "#696969"

        # 1. Configure TitleBar with close hint only
        titleBar = self.getTitleBar()
        if titleBar is not None:
            titleBar.setTitleBarFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
            titleBar.setIconSize(18, 18)
            titleBar.setTitleBarHint(["close"])

        # 2. Build preferences body inside dialog layout
        layout = self.layout()
        if layout is not None:
            self._contentContainer = self._buildPreferencesArea()
            layout.addWidget(self._contentContainer)

        # 3. Apply initial light theme styling
        self._applyThemeStyles(self.darkTheme)

    def _buildPreferencesArea(self) -> QFrame:
        """Construct header, settings card, and action button bar.

        Returns
        -------
        QFrame
            Configured container frame holding preferences content.
        """
        container = QFrame()
        container.setObjectName("contentContainer")
        container.setFrameShape(QFrame.Shape.NoFrame)
        containerLayout = QVBoxLayout(container)
        containerLayout.setContentsMargins(28, 16, 28, 18)
        containerLayout.setSpacing(14)

        # Header section with icon, title, and subtitle
        headerLayout = QVBoxLayout()
        headerLayout.setSpacing(4)

        headerTitleRow = QHBoxLayout()
        headerTitleRow.setSpacing(8)

        iconLabel = QLabel("⚙️")
        iconLabel.setFont(QFont("Segoe UI Emoji", 16))
        headerTitleRow.addWidget(iconLabel)

        titleLabel = QLabel("Window Preferences")
        titleLabel.setObjectName("preferencesTitle")
        titleLabel.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        headerTitleRow.addWidget(titleLabel)
        headerTitleRow.addStretch()

        headerLayout.addLayout(headerTitleRow)

        subtitleLabel = QLabel("Customize native DWM composition and visual behaviors.")
        subtitleLabel.setObjectName("preferencesSubtitle")
        subtitleLabel.setFont(QFont("Segoe UI", 10))
        headerLayout.addWidget(subtitleLabel)

        containerLayout.addLayout(headerLayout)

        # Settings card with 3 styled options
        settingsCard = QFrame()
        settingsCard.setObjectName("settingsCard")
        cardLayout = QVBoxLayout(settingsCard)
        cardLayout.setContentsMargins(16, 12, 16, 12)
        cardLayout.setSpacing(10)

        options = [
            "Enable Windows 11 rounded corners",
            "Native DWM drop shadows",
            "Per-monitor dynamic DPI compensation",
        ]

        for index, optionText in enumerate(options):
            if index > 0:
                separator = QFrame()
                separator.setObjectName("cardSeparator")
                separator.setFixedHeight(1)
                separator.setFrameShape(QFrame.Shape.HLine)
                cardLayout.addWidget(separator)

            optionRow = self._createOptionRow(optionText)
            cardLayout.addLayout(optionRow)

        containerLayout.addWidget(settingsCard)
        containerLayout.addStretch()

        # Bottom action bar
        bottomBarLayout = QHBoxLayout()
        bottomBarLayout.setSpacing(10)

        self._themeToggleButton = QPushButton("🌙 Dark")
        self._themeToggleButton.setObjectName("secondaryButton")
        self._themeToggleButton.setFixedHeight(32)
        self._themeToggleButton.setMinimumWidth(80)
        self._themeToggleButton.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        self._themeToggleButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self._themeToggleButton.clicked.connect(self._toggleTheme)
        bottomBarLayout.addWidget(self._themeToggleButton)

        bottomBarLayout.addStretch()

        cancelButton = QPushButton("Cancel")
        cancelButton.setObjectName("secondaryButton")
        cancelButton.setFixedHeight(32)
        cancelButton.setMinimumWidth(80)
        cancelButton.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        cancelButton.setCursor(Qt.CursorShape.PointingHandCursor)
        cancelButton.clicked.connect(self.reject)
        bottomBarLayout.addWidget(cancelButton)

        saveButton = QPushButton("Save Changes")
        saveButton.setObjectName("primaryAccentButton")
        saveButton.setFixedHeight(32)
        saveButton.setMinimumWidth(110)
        saveButton.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        saveButton.setCursor(Qt.CursorShape.PointingHandCursor)
        saveButton.clicked.connect(self.accept)
        bottomBarLayout.addWidget(saveButton)

        containerLayout.addLayout(bottomBarLayout)
        return container

    def _createOptionRow(self, labelText: str) -> QHBoxLayout:
        """Create an option row with label and active status badge.

        Parameters
        ----------
        labelText : str
            Descriptive setting name.

        Returns
        -------
        QHBoxLayout
            Horizontal layout containing setting label and status badge.
        """
        rowLayout = QHBoxLayout()
        rowLayout.setContentsMargins(2, 4, 2, 4)
        rowLayout.setSpacing(12)

        optionLabel = QLabel(labelText)
        optionLabel.setObjectName("optionTitle")
        optionLabel.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        rowLayout.addWidget(optionLabel)

        rowLayout.addStretch()

        statusBadge = QLabel("ACTIVE")
        statusBadge.setObjectName("statusBadge")
        statusBadge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        statusBadge.setFixedHeight(22)
        statusBadge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rowLayout.addWidget(statusBadge)

        return rowLayout

    def _toggleTheme(self) -> None:
        """Toggle dark and light window themes dynamically."""
        self.darkTheme = not self.darkTheme
        self._applyThemeStyles(self.darkTheme)

    def _applyThemeStyles(self, isDarkTheme: bool) -> None:
        """Apply dynamic color palette and stylesheet matching active theme.

        Parameters
        ----------
        isDarkTheme : bool
            True for dark theme, False for light theme.
        """
        if hasattr(self, "_themeToggleButton"):
            if isDarkTheme:
                self._themeToggleButton.setText("☀️ Light")
            else:
                self._themeToggleButton.setText("🌙 Dark")

        if not hasattr(self, "_contentContainer"):
            return

        if isDarkTheme:
            self._contentContainer.setStyleSheet(
                """
                #contentContainer {
                    background-color: #202020;
                }
                #preferencesTitle {
                    color: #FFFFFF;
                }
                #preferencesSubtitle {
                    color: #9CA3AF;
                }
                #settingsCard {
                    background-color: #2B2B2B;
                    border: 1px solid #383838;
                    border-radius: 8px;
                }
                #cardSeparator {
                    background-color: #383838;
                    border: none;
                }
                #optionTitle {
                    color: #F3F4F6;
                }
                #statusBadge {
                    background-color: #1A381E;
                    color: #7EE787;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 10px;
                    font-weight: bold;
                    letter-spacing: 0.5px;
                }
                #secondaryButton {
                    background-color: #2D2D30;
                    color: #FFFFFF;
                    border: 1px solid #3E3E42;
                    border-radius: 6px;
                    padding: 4px 14px;
                }
                #secondaryButton:hover {
                    background-color: #38383C;
                    border-color: #0078D4;
                }
                #primaryAccentButton {
                    background-color: #0078D4;
                    color: #FFFFFF;
                    border: 1px solid #0078D4;
                    border-radius: 6px;
                    padding: 4px 16px;
                }
                #primaryAccentButton:hover {
                    background-color: #106EBE;
                    border-color: #106EBE;
                }
                """
            )
        else:
            self._contentContainer.setStyleSheet(
                """
                #contentContainer {
                    background-color: #F3F3F3;
                }
                #preferencesTitle {
                    color: #1A1A1A;
                }
                #preferencesSubtitle {
                    color: #6B7280;
                }
                #settingsCard {
                    background-color: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                }
                #cardSeparator {
                    background-color: #F3F4F6;
                    border: none;
                }
                #optionTitle {
                    color: #111827;
                }
                #statusBadge {
                    background-color: #DFF6DD;
                    color: #107C10;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 10px;
                    font-weight: bold;
                    letter-spacing: 0.5px;
                }
                #secondaryButton {
                    background-color: #FFFFFF;
                    color: #1A1A1A;
                    border: 1px solid #D1D5DB;
                    border-radius: 6px;
                    padding: 4px 14px;
                }
                #secondaryButton:hover {
                    background-color: #F3F4F6;
                    border-color: #9CA3AF;
                }
                #primaryAccentButton {
                    background-color: #0078D4;
                    color: #FFFFFF;
                    border: 1px solid #0078D4;
                    border-radius: 6px;
                    padding: 4px 16px;
                }
                #primaryAccentButton:hover {
                    background-color: #106EBE;
                    border-color: #106EBE;
                }
                """
            )


if __name__ == "__main__":
    application = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(application.exec())
