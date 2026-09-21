"""Showcase frameless main window with modern dashboard and dynamic theming.

Demonstrates:
1. Prominent header typography and subtitle.
2. Three feature highlight cards with rounded borders and responsive layouts.
3. Windows 11 Snap Layouts, DWM shadow integration, and smooth edge resizing.
4. Dynamic light and dark theme adaptation across controls and typography.
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

from qtframelesskit import FramelessMainWindow, WindowCornerPreference


class Window(FramelessMainWindow):
    """Modern frameless main window dashboard showcase."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._setupContent()

    def _setupContent(self) -> None:
        """Configure main window properties, title bar, and dashboard content."""
        self.setWindowTitle("QtFrameless MainWindow")
        self.resize(800, 500)
        self.setMinimumSize(640, 420)

        iconPath = Path(__file__).resolve().parent / "logo.png"
        if iconPath.exists():
            self.setWindowIcon(QIcon(str(iconPath)))

        # Configure modern Windows 11 corner rounding and border accent
        self.darkTheme = False
        self.windowCornerPreference = WindowCornerPreference.ROUND
        self.borderColor = "#696969"

        # 1. Configure TitleBar
        titleBar = self.getTitleBar()
        if titleBar is not None:
            titleBar.setTitleBarFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
            titleBar.setIconSize(20, 20)
            titleBar.setTitleBarHint(["min", "max", "close"])

        # 2. Build dashboard inside central widget
        centralWidget = self.centralWidget()
        if centralWidget is not None:
            layout = centralWidget.layout()
            if layout is not None:
                self._dashboardWidget = self._buildDashboardArea()
                layout.addWidget(self._dashboardWidget)

        # 3. Apply initial light theme styling
        self._applyThemeStyles(self.darkTheme)

    def _buildDashboardArea(self) -> QFrame:
        """Construct the dashboard header, feature cards, and action row.

        Returns
        -------
        QFrame
            Configured dashboard content container.
        """
        dashboardWidget = QFrame()
        dashboardWidget.setObjectName("dashboardWidget")
        dashboardWidget.setFrameShape(QFrame.Shape.NoFrame)
        dashboardLayout = QVBoxLayout(dashboardWidget)
        dashboardLayout.setContentsMargins(36, 28, 36, 28)
        dashboardLayout.setSpacing(22)

        # Header section with large title and subtitle
        headerLayout = QVBoxLayout()
        headerLayout.setSpacing(6)

        mainTitleLabel = QLabel("Modern Frameless Desktop")
        mainTitleLabel.setObjectName("mainTitleLabel")
        mainTitleLabel.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        headerLayout.addWidget(mainTitleLabel)

        subtitleLabel = QLabel(
            "Pure Python Win32 integration with Snap Layouts, DWM shadows, "
            "and smooth edge resizing."
        )
        subtitleLabel.setObjectName("subtitleLabel")
        subtitleLabel.setFont(QFont("Segoe UI", 11))
        subtitleLabel.setWordWrap(True)
        headerLayout.addWidget(subtitleLabel)

        dashboardLayout.addLayout(headerLayout)

        # Three feature cards in a horizontal row
        featureCardsLayout = QHBoxLayout()
        featureCardsLayout.setSpacing(14)

        cardData = [
            (
                "🪟 Snap Layouts",
                "Hover maximize button for Windows 11 snap layouts.",
            ),
            (
                "🎨 Dynamic Theme",
                "Auto-syncs with Windows dark and light system themes.",
            ),
            (
                "⚡ Pure Python",
                "Zero C++ binaries. Pure ctypes and Win32 APIs.",
            ),
        ]

        for cardTitle, cardDescription in cardData:
            cardFrame = self._createFeatureCard(cardTitle, cardDescription)
            featureCardsLayout.addWidget(cardFrame)

        dashboardLayout.addLayout(featureCardsLayout)
        dashboardLayout.addStretch()

        # Action row with modern theme switch button
        actionRowLayout = QHBoxLayout()
        self._themeToggleButton = QPushButton("🌙 Switch to Dark Theme")
        self._themeToggleButton.setObjectName("themeToggleButton")
        self._themeToggleButton.setFixedHeight(40)
        self._themeToggleButton.setMinimumWidth(240)
        self._themeToggleButton.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        self._themeToggleButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self._themeToggleButton.clicked.connect(self._toggleTheme)
        actionRowLayout.addWidget(self._themeToggleButton)
        actionRowLayout.addStretch()

        dashboardLayout.addLayout(actionRowLayout)
        return dashboardWidget

    def _createFeatureCard(self, title: str, description: str) -> QFrame:
        """Create a styled feature card with title and descriptive text.

        Parameters
        ----------
        title : str
            Card title with emoji icon.
        description : str
            Detailed explanation of the feature.

        Returns
        -------
        QFrame
            Configured feature card frame widget.
        """
        cardFrame = QFrame()
        cardFrame.setObjectName("featureCard")
        cardLayout = QVBoxLayout(cardFrame)
        cardLayout.setContentsMargins(18, 16, 18, 16)
        cardLayout.setSpacing(8)

        cardTitleLabel = QLabel(title)
        cardTitleLabel.setObjectName("cardTitleLabel")
        cardTitleLabel.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))

        cardDescriptionLabel = QLabel(description)
        cardDescriptionLabel.setObjectName("cardDescriptionLabel")
        cardDescriptionLabel.setFont(QFont("Segoe UI", 10))
        cardDescriptionLabel.setWordWrap(True)

        cardLayout.addWidget(cardTitleLabel)
        cardLayout.addWidget(cardDescriptionLabel)
        cardLayout.addStretch()
        return cardFrame

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
                self._themeToggleButton.setText("☀️ Switch to Light Theme")
            else:
                self._themeToggleButton.setText("🌙 Switch to Dark Theme")

        if not hasattr(self, "_dashboardWidget"):
            return

        if isDarkTheme:
            self._dashboardWidget.setStyleSheet(
                """
                #dashboardWidget {
                    background-color: #202020;
                }
                #mainTitleLabel {
                    color: #FFFFFF;
                }
                #subtitleLabel {
                    color: #9CA3AF;
                }
                #featureCard {
                    background-color: #2B2B2B;
                    border: 1px solid #383838;
                    border-radius: 10px;
                }
                #cardTitleLabel {
                    color: #F3F4F6;
                }
                #cardDescriptionLabel {
                    color: #9CA3AF;
                    line-height: 140%;
                }
                #themeToggleButton {
                    background-color: #2D2D30;
                    color: #FFFFFF;
                    border: 1px solid #3E3E42;
                    border-radius: 6px;
                    padding: 6px 18px;
                }
                #themeToggleButton:hover {
                    background-color: #38383C;
                    border-color: #0078D4;
                }
                """
            )
        else:
            self._dashboardWidget.setStyleSheet(
                """
                #dashboardWidget {
                    background-color: #F3F3F3;
                }
                #mainTitleLabel {
                    color: #1A1A1A;
                }
                #subtitleLabel {
                    color: #6B7280;
                }
                #featureCard {
                    background-color: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 10px;
                }
                #cardTitleLabel {
                    color: #111827;
                }
                #cardDescriptionLabel {
                    color: #4B5563;
                    line-height: 140%;
                }
                #themeToggleButton {
                    background-color: #FFFFFF;
                    color: #1A1A1A;
                    border: 1px solid #D1D5DB;
                    border-radius: 6px;
                    padding: 6px 18px;
                }
                #themeToggleButton:hover {
                    background-color: #F3F4F6;
                    border-color: #9CA3AF;
                }
                """
            )


if __name__ == "__main__":
    application = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(application.exec())
