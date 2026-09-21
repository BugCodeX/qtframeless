"""Modern, modular frameless window showcase.

Demonstrates:
1. Modular TitleBar with custom center widgets (navigation buttons, search bar, theme toggle).
2. TitleBar fixed at the top (y=0) with clean window layout hierarchy.
3. Intelligent drag hit-testing (clicking/typing in inputs does not drag the window).
4. Windows 11 native styling: rounded corners, border accent, and fluid light/dark theming.
"""

import sys

from qtpy.QtCore import Qt
from qtpy.QtGui import QFont
from qtpy.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from qtframeless import FramelessMainWindow, WindowCornerPreference


class ModularTitleBarWindow(FramelessMainWindow):
    """Modern frameless window demonstrating modular title bar integration."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._isDarkMode = True
        self._setupWindow()

    def _setupWindow(self) -> None:
        """Configure native window effects, modular title bar, and central content."""
        self.setWindowTitle("QtFrameless Studio")
        self.setWindowIcon(r"examples\Stark-icon.png")
        self.resize(960, 620)
        self.setMinimumSize(700, 450)

        # Windows 11 native corner rounding and border accent
        self.setWindowCornerPreference(WindowCornerPreference.ROUND)
        self.setBorderColor("#696969")

        # 1. Configure TitleBar strictly at the top
        titleBar = self.getTitleBar()
        if titleBar is not None:
            titleBar.setTitleBarFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
            titleBar.setIconSize(20, 20)
            titleBar.setTitleBarHint(["min", "max", "close"])

            # Build modular center area
            centerWidget = self._buildCenterWidget()
            titleBar.setCenterWidget(centerWidget)

        # 2. Attach content below the title bar using the existing centralWidget layout
        centralWidget = self.centralWidget()
        if centralWidget is not None:
            layout = centralWidget.layout()
            if layout is not None:
                contentArea = self._buildContentArea()
                layout.addWidget(contentArea)

        # 3. Apply initial theme
        self._applyThemeStyles(self._isDarkMode)

    def _buildCenterWidget(self) -> QWidget:
        """Create interactive center widget with navigation, search, and theme toggle.

        Returns
        -------
        QWidget
            Modular container for title bar center area.
        """
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 2, 12, 2)
        layout.setSpacing(6)

        # Navigation buttons
        self._backButton = QPushButton("‹")
        self._backButton.setObjectName("navButton")
        self._backButton.setFixedSize(28, 24)
        self._backButton.setCursor(Qt.CursorShape.PointingHandCursor)

        self._forwardButton = QPushButton("›")
        self._forwardButton.setObjectName("navButton")
        self._forwardButton.setFixedSize(28, 24)
        self._forwardButton.setCursor(Qt.CursorShape.PointingHandCursor)

        # Search bar
        self._searchBar = QLineEdit()
        self._searchBar.setObjectName("searchBar")
        self._searchBar.setPlaceholderText("Search or jump to... (Ctrl+K)")
        self._searchBar.setClearButtonEnabled(True)
        self._searchBar.setFixedWidth(280)
        self._searchBar.setFixedHeight(26)

        # Theme toggle button
        self._themeButton = QPushButton("🌙 Dark")
        self._themeButton.setObjectName("themeToggle")
        self._themeButton.setFixedHeight(26)
        self._themeButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self._themeButton.clicked.connect(self._handleThemeToggle)

        layout.addStretch()
        layout.addWidget(self._backButton)
        layout.addWidget(self._forwardButton)
        layout.addWidget(self._searchBar)
        layout.addWidget(self._themeButton)
        layout.addStretch()

        return container

    def _buildContentArea(self) -> QWidget:
        """Build main content area placed below the title bar.

        Returns
        -------
        QWidget
            Main window content container.
        """
        contentWidget = QWidget()
        contentWidget.setObjectName("contentArea")
        mainLayout = QHBoxLayout(contentWidget)
        mainLayout.setContentsMargins(16, 16, 16, 16)
        mainLayout.setSpacing(16)

        # Sidebar navigation
        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        sidebar.setFixedWidth(200)
        sidebarLayout = QVBoxLayout(sidebar)
        sidebarLayout.setContentsMargins(8, 12, 8, 12)
        sidebarLayout.setSpacing(6)

        sidebarTitle = QLabel("NAVIGATION")
        sidebarTitle.setObjectName("sectionTitle")
        sidebarLayout.addWidget(sidebarTitle)

        navList = QListWidget()
        navList.setObjectName("navList")
        navList.addItems(
            [
                "🏠 Overview",
                "🔍 Search & Inputs",
                "🎨 Theme & DWM",
                "⚙️ Settings",
            ]
        )
        navList.setCurrentRow(0)
        sidebarLayout.addWidget(navList)

        mainLayout.addWidget(sidebar)

        # Main dashboard / interactive area
        dashboard = QWidget()
        dashboardLayout = QVBoxLayout(dashboard)
        dashboardLayout.setContentsMargins(0, 0, 0, 0)
        dashboardLayout.setSpacing(14)

        # Feature highlights card
        card = QFrame()
        card.setObjectName("featureCard")
        cardLayout = QVBoxLayout(card)
        cardLayout.setContentsMargins(16, 14, 16, 14)
        cardLayout.setSpacing(8)

        cardTitle = QLabel("<h3>Modern Modular TitleBar Features</h3>")
        cardTitle.setTextFormat(Qt.TextFormat.RichText)
        cardLayout.addWidget(cardTitle)

        cardDescription = QLabel(
            "• <b>TitleBar at Top:</b> Sits cleanly at the top of the window with native zero margins.<br>"
            "• <b>Modular Center:</b> The search input and navigation buttons above are inside <code>TitleBar.setCenterWidget()</code>.<br>"
            "• <b>Intelligent Drag:</b> Dragging empty space or the title moves the window. Clicking or selecting text in the search input does <i>not</i> trigger drag.<br>"
            "• <b>Fluid Theming:</b> Toggle between Light and Dark mode to see title bar text, vector buttons, and window chrome adapt automatically."
        )
        cardDescription.setTextFormat(Qt.TextFormat.RichText)
        cardDescription.setWordWrap(True)
        cardLayout.addWidget(cardDescription)
        dashboardLayout.addWidget(card)

        # Interactive controls grid (proves child input interaction)
        controlsFrame = QFrame()
        controlsFrame.setObjectName("controlsFrame")
        controlsLayout = QGridLayout(controlsFrame)
        controlsLayout.setContentsMargins(16, 14, 16, 14)
        controlsLayout.setHorizontalSpacing(14)
        controlsLayout.setVerticalSpacing(10)

        controlsLayout.addWidget(QLabel("Interactive input:"), 0, 0)
        sampleInput = QLineEdit()
        sampleInput.setPlaceholderText("Try typing or selecting text here...")
        controlsLayout.addWidget(sampleInput, 0, 1)

        controlsLayout.addWidget(QLabel("Slider adjustment:"), 1, 0)
        sampleSlider = QSlider(Qt.Orientation.Horizontal)
        sampleSlider.setRange(0, 100)
        sampleSlider.setValue(65)
        controlsLayout.addWidget(sampleSlider, 1, 1)

        dashboardLayout.addWidget(controlsFrame)

        # Text editor
        self._editor = QTextEdit()
        self._editor.setObjectName("editorArea")
        self._editor.setPlaceholderText(
            "Write notes or code here...\n\n"
            "Notice how the entire window chrome matches native Windows 11 styling."
        )
        dashboardLayout.addWidget(self._editor)

        mainLayout.addWidget(dashboard)
        return contentWidget

    def _handleThemeToggle(self) -> None:
        """Toggle between dark and light themes."""
        self._isDarkMode = not self._isDarkMode
        self._applyThemeStyles(self._isDarkMode)

    def _applyThemeStyles(self, isDark: bool) -> None:
        """Apply dark or light theme styling across the window.

        Parameters
        ----------
        isDark : bool
            True for dark mode, False for light mode.
        """
        # 1. Update native Windows 11 DWM chrome and titlebar
        self.setDarkTheme(isDark)

        # 2. Update toggle button label
        if hasattr(self, "_themeButton"):
            self._themeButton.setText("🌙 Dark" if isDark else "☀️ Light")

        # 3. Apply polished stylesheet
        if isDark:
            self.setStyleSheet(
                """
                QMainWindow, #contentArea {
                    background-color: #1E1E1E;
                    color: #FFFFFF;
                }
                #sidebarFrame, #featureCard, #controlsFrame {
                    background-color: #252526;
                    border: 1px solid #333333;
                    border-radius: 8px;
                }
                #sectionTitle {
                    color: #888888;
                    font-size: 11px;
                    font-weight: bold;
                    letter-spacing: 1px;
                }
                #navList {
                    background: transparent;
                    border: none;
                    color: #CCCCCC;
                    font-size: 13px;
                }
                #navList::item {
                    padding: 8px 10px;
                    border-radius: 6px;
                }
                #navList::item:selected {
                    background-color: #37373D;
                    color: #FFFFFF;
                }
                #navButton {
                    background-color: transparent;
                    color: #CCCCCC;
                    border: 1px solid #3E3E42;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                }
                #navButton:hover {
                    background-color: #333337;
                    color: #FFFFFF;
                }
                #searchBar {
                    background-color: #2D2D30;
                    color: #FFFFFF;
                    border: 1px solid #3E3E42;
                    border-radius: 6px;
                    padding: 2px 10px;
                    font-size: 12px;
                }
                #searchBar:focus {
                    border: 1px solid #0078D4;
                }
                #themeToggle {
                    background-color: #2D2D30;
                    color: #E0E0E0;
                    border: 1px solid #3E3E42;
                    border-radius: 6px;
                    padding: 2px 10px;
                    font-size: 12px;
                }
                #themeToggle:hover {
                    background-color: #38383C;
                }
                QLineEdit, QTextEdit {
                    background-color: #252526;
                    color: #FFFFFF;
                    border: 1px solid #3E3E42;
                    border-radius: 6px;
                    padding: 6px 10px;
                }
                QLineEdit:focus, QTextEdit:focus {
                    border: 1px solid #0078D4;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                QMainWindow, #contentArea {
                    background-color: #F8F9FA;
                    color: #1A1A1A;
                }
                #sidebarFrame, #featureCard, #controlsFrame {
                    background-color: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                }
                #sectionTitle {
                    color: #6B7280;
                    font-size: 11px;
                    font-weight: bold;
                    letter-spacing: 1px;
                }
                #navList {
                    background: transparent;
                    border: none;
                    color: #374151;
                    font-size: 13px;
                }
                #navList::item {
                    padding: 8px 10px;
                    border-radius: 6px;
                }
                #navList::item:selected {
                    background-color: #E0E7FF;
                    color: #1E40AF;
                }
                #navButton {
                    background-color: transparent;
                    color: #374151;
                    border: 1px solid #D1D5DB;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                }
                #navButton:hover {
                    background-color: #E5E7EB;
                }
                #searchBar {
                    background-color: #FFFFFF;
                    color: #1A1A1A;
                    border: 1px solid #D1D5DB;
                    border-radius: 6px;
                    padding: 2px 10px;
                    font-size: 12px;
                }
                #searchBar:focus {
                    border: 1px solid #0078D4;
                }
                #themeToggle {
                    background-color: #FFFFFF;
                    color: #374151;
                    border: 1px solid #D1D5DB;
                    border-radius: 6px;
                    padding: 2px 10px;
                    font-size: 12px;
                }
                #themeToggle:hover {
                    background-color: #F3F4F6;
                }
                QLineEdit, QTextEdit {
                    background-color: #FFFFFF;
                    color: #1A1A1A;
                    border: 1px solid #D1D5DB;
                    border-radius: 6px;
                    padding: 6px 10px;
                }
                QLineEdit:focus, QTextEdit:focus {
                    border: 1px solid #0078D4;
                }
                """
            )


if __name__ == "__main__":
    application = QApplication(sys.argv)
    window = ModularTitleBarWindow()
    window.show()
    sys.exit(application.exec())
