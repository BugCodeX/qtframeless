"""Showcase frameless QWidget component with interactive controls and dynamic theming.

Demonstrates:
1. Reusable borderless QWidget component with integrated custom TitleBar.
2. Intelligent drag hit-testing with interactive text inputs and slider controls.
3. Windows 11 rounded corners, native drop shadow, and border styling.
4. Dynamic light and dark theme adaptation across controls and typography.
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from qtframeless import FramelessWidget, WindowCornerPreference


class Window(FramelessWidget):
    """Modern frameless widget component showcase."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._setupContent()

    def _setupContent(self) -> None:
        """Configure widget properties, title bar, and interactive content."""
        self.setWindowTitle("QtFrameless Widget")
        self.resize(680, 420)
        self.setMinimumSize(540, 360)

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
            titleBar.setIconSize(18, 18)
            titleBar.setTitleBarHint(["min", "max", "close"])

        # 2. Build content inside widget layout
        layout = self.layout()
        if layout is not None:
            self._contentContainer = self._buildContentArea()
            layout.addWidget(self._contentContainer)

        # 3. Apply initial light theme styling
        self._applyThemeStyles(self.darkTheme)

    def _buildContentArea(self) -> QFrame:
        """Construct header, interactive card, and bottom action bar.

        Returns
        -------
        QFrame
            Configured container frame holding widget content.
        """
        container = QFrame()
        container.setObjectName("contentContainer")
        container.setFrameShape(QFrame.Shape.NoFrame)
        containerLayout = QVBoxLayout(container)
        containerLayout.setContentsMargins(32, 20, 32, 22)
        containerLayout.setSpacing(18)

        # Header section with title and subtitle
        headerLayout = QVBoxLayout()
        headerLayout.setSpacing(6)

        titleLabel = QLabel("Frameless QWidget Component")
        titleLabel.setObjectName("widgetTitleLabel")
        titleLabel.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        headerLayout.addWidget(titleLabel)

        subtitleLabel = QLabel(
            "Reusable borderless widget with integrated TitleBar, "
            "native drag, and edge hit-testing."
        )
        subtitleLabel.setObjectName("widgetSubtitleLabel")
        subtitleLabel.setFont(QFont("Segoe UI", 11))
        subtitleLabel.setWordWrap(True)
        headerLayout.addWidget(subtitleLabel)

        containerLayout.addLayout(headerLayout)

        # Interactive card demonstrating input and slider hit-testing
        interactiveCard = QFrame()
        interactiveCard.setObjectName("interactiveCard")
        cardLayout = QVBoxLayout(interactiveCard)
        cardLayout.setContentsMargins(20, 18, 20, 18)
        cardLayout.setSpacing(14)

        cardCategoryBadge = QLabel("INTERACTIVE CONTROLS")
        cardCategoryBadge.setObjectName("cardCategoryBadge")
        cardCategoryBadge.setFixedHeight(20)
        cardCategoryBadge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        cardLayout.addWidget(cardCategoryBadge, alignment=Qt.AlignmentFlag.AlignLeft)

        # Text input row
        inputLayout = QVBoxLayout()
        inputLayout.setSpacing(6)

        inputLabel = QLabel("Interactive Text Input:")
        inputLabel.setObjectName("controlLabel")
        inputLabel.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        inputLayout.addWidget(inputLabel)

        self._textInput = QLineEdit()
        self._textInput.setObjectName("interactiveInput")
        self._textInput.setPlaceholderText("Try typing or selecting text here...")
        self._textInput.setFixedHeight(34)
        self._textInput.setClearButtonEnabled(True)
        inputLayout.addWidget(self._textInput)

        cardLayout.addLayout(inputLayout)

        # Slider adjustment row with value badge
        sliderLayout = QVBoxLayout()
        sliderLayout.setSpacing(6)

        sliderHeaderRow = QHBoxLayout()
        sliderLabel = QLabel("Slider Adjustment:")
        sliderLabel.setObjectName("controlLabel")
        sliderLabel.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        sliderHeaderRow.addWidget(sliderLabel)

        sliderHeaderRow.addStretch()

        self._valueBadge = QLabel("65%")
        self._valueBadge.setObjectName("valueBadge")
        self._valueBadge.setFixedHeight(22)
        self._valueBadge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._valueBadge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sliderHeaderRow.addWidget(self._valueBadge)

        sliderLayout.addLayout(sliderHeaderRow)

        self._sampleSlider = QSlider(Qt.Orientation.Horizontal)
        self._sampleSlider.setObjectName("interactiveSlider")
        self._sampleSlider.setRange(0, 100)
        self._sampleSlider.setValue(65)
        self._sampleSlider.valueChanged.connect(self._handleSliderValueChanged)
        sliderLayout.addWidget(self._sampleSlider)

        cardLayout.addLayout(sliderLayout)
        containerLayout.addWidget(interactiveCard)
        containerLayout.addStretch()

        # Bottom action bar with theme switch button
        actionBarLayout = QHBoxLayout()
        self._themeToggleButton = QPushButton("🌙 Switch to Dark Theme")
        self._themeToggleButton.setObjectName("widgetThemeButton")
        self._themeToggleButton.setFixedHeight(38)
        self._themeToggleButton.setMinimumWidth(220)
        self._themeToggleButton.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        self._themeToggleButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self._themeToggleButton.clicked.connect(self._toggleTheme)
        actionBarLayout.addWidget(self._themeToggleButton)
        actionBarLayout.addStretch()

        containerLayout.addLayout(actionBarLayout)
        return container

    def _handleSliderValueChanged(self, value: int) -> None:
        """Update value badge text to reflect active slider position.

        Parameters
        ----------
        value : int
            Current slider integer value from 0 to 100.
        """
        self._valueBadge.setText(f"{value}%")

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

        if not hasattr(self, "_contentContainer"):
            return

        if isDarkTheme:
            self._contentContainer.setStyleSheet(
                """
                #contentContainer {
                    background-color: #202020;
                }
                #widgetTitleLabel {
                    color: #FFFFFF;
                }
                #widgetSubtitleLabel {
                    color: #9CA3AF;
                }
                #interactiveCard {
                    background-color: #2B2B2B;
                    border: 1px solid #383838;
                    border-radius: 10px;
                }
                #cardCategoryBadge {
                    background-color: #1E3A5F;
                    color: #93C5FD;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 10px;
                    font-weight: bold;
                    letter-spacing: 0.5px;
                }
                #controlLabel {
                    color: #F3F4F6;
                }
                #valueBadge {
                    background-color: #1E293B;
                    color: #60A5FA;
                    border-radius: 4px;
                    padding: 2px 10px;
                }
                #interactiveInput {
                    background-color: #1E1E1E;
                    color: #FFFFFF;
                    border: 1px solid #3E3E42;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 12px;
                }
                #interactiveInput:focus {
                    border-color: #0078D4;
                }
                #widgetThemeButton {
                    background-color: #2D2D30;
                    color: #FFFFFF;
                    border: 1px solid #3E3E42;
                    border-radius: 6px;
                    padding: 6px 18px;
                }
                #widgetThemeButton:hover {
                    background-color: #38383C;
                    border-color: #0078D4;
                }
                """
            )
        else:
            self._contentContainer.setStyleSheet(
                """
                #contentContainer {
                    background-color: #F3F3F3;
                }
                #widgetTitleLabel {
                    color: #1A1A1A;
                }
                #widgetSubtitleLabel {
                    color: #6B7280;
                }
                #interactiveCard {
                    background-color: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 10px;
                }
                #cardCategoryBadge {
                    background-color: #E0E7FF;
                    color: #0078D4;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 10px;
                    font-weight: bold;
                    letter-spacing: 0.5px;
                }
                #controlLabel {
                    color: #111827;
                }
                #valueBadge {
                    background-color: #E0E7FF;
                    color: #0078D4;
                    border-radius: 4px;
                    padding: 2px 10px;
                }
                #interactiveInput {
                    background-color: #FFFFFF;
                    color: #1A1A1A;
                    border: 1px solid #D1D5DB;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 12px;
                }
                #interactiveInput:focus {
                    border-color: #0078D4;
                }
                #widgetThemeButton {
                    background-color: #FFFFFF;
                    color: #1A1A1A;
                    border: 1px solid #D1D5DB;
                    border-radius: 6px;
                    padding: 6px 18px;
                }
                #widgetThemeButton:hover {
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
