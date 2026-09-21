"""Per-monitor DPI scaling showcase for frameless windows.

Demonstrates:
1. Automatic per-monitor DPI detection and dynamic title bar rescaling.
2. Dynamic hit-testing resize border margin scaling based on DPI.
3. Native border compensation in WM_NCCALCSIZE avoiding pixel misalignment.
4. Interactive DPI simulator to test 100%, 125%, 150%, 175%, and 200% scaling live.
"""

import sys
from pathlib import Path

from qtpy.QtGui import QFont
from qtpy.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from qtframeless import FramelessMainWindow, WindowCornerPreference
from qtframeless.native.win32_utils import getDpiForWindow, getResizeBorderThickness


class DpiScalingDemoWindow(FramelessMainWindow):
    """Showcase window for per-monitor DPI scaling in frameless windows."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._setupWindow()

    def _setupWindow(self) -> None:
        """Configure frameless window properties, title bar, and DPI inspector."""
        self.setWindowTitle("Per-Monitor DPI Scaling Demo")
        self.resize(880, 560)
        self.setMinimumSize(640, 400)
        self.setWindowCornerPreference(WindowCornerPreference.ROUND)
        self.setBorderColor("#696969")

        iconPath = Path(__file__).resolve().parent / "logo.png"
        if iconPath.exists():
            self.setWindowIcon(str(iconPath))

        titleBar = self.getTitleBar()
        if titleBar is not None:
            titleBar.setTitleBarFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
            titleBar.setIconSize(18, 18)
            titleBar.setTitleBarHint(["min", "max", "close"])

        centralWidget = self.centralWidget()
        if centralWidget is not None:
            layout = centralWidget.layout()
            if layout is not None:
                contentWidget = self._buildContentWidget()
                layout.addWidget(contentWidget)

        # Connect screen changed signal to refresh display info
        windowHandle = self.windowHandle()
        if windowHandle is not None:
            windowHandle.screenChanged.connect(self._refreshDpiMetrics)

        self._refreshDpiMetrics()

    def _buildContentWidget(self) -> QWidget:
        """Build the main content widget with DPI info and interactive simulator.

        Returns
        -------
        QWidget
            Configured content widget.
        """
        container = QWidget()
        mainLayout = QVBoxLayout(container)
        mainLayout.setContentsMargins(24, 20, 24, 24)
        mainLayout.setSpacing(16)

        # Header description
        headerLabel = QLabel(
            "<h2>Per-Monitor DPI & Multi-Screen Scaling</h2>"
            "<p style='color: #888888; font-size: 13px;'>"
            "Drag this window across monitors with different DPI scalings (e.g. 100% vs 150%) "
            "to observe seamless border compensation, proportional button sizing, and crisp icons."
            "</p>"
        )
        headerLabel.setWordWrap(True)
        mainLayout.addWidget(headerLabel)

        # Grid of current metrics
        metricsBox = QGroupBox("Active Display & Win32 DPI Metrics")
        boxLayout = QGridLayout(metricsBox)
        boxLayout.setSpacing(12)

        self._screenNameLabel = QLabel("Unknown")
        self._currentDpiLabel = QLabel("96 DPI (100%)")
        self._devicePixelRatioLabel = QLabel("1.0")
        self._borderThicknessLabel = QLabel("8 px")
        self._hitboxMarginLabel = QLabel("5 px")
        self._titleBarHeightLabel = QLabel("30 px")

        labelStyle = "font-weight: bold; color: #0078D4; font-size: 13px;"
        self._currentDpiLabel.setStyleSheet(labelStyle)
        self._borderThicknessLabel.setStyleSheet(labelStyle)
        self._hitboxMarginLabel.setStyleSheet(labelStyle)

        boxLayout.addWidget(QLabel("Current Screen:"), 0, 0)
        boxLayout.addWidget(self._screenNameLabel, 0, 1)
        boxLayout.addWidget(QLabel("Active Window DPI:"), 0, 2)
        boxLayout.addWidget(self._currentDpiLabel, 0, 3)

        boxLayout.addWidget(QLabel("Device Pixel Ratio:"), 1, 0)
        boxLayout.addWidget(self._devicePixelRatioLabel, 1, 1)
        boxLayout.addWidget(QLabel("Resize Border Thickness:"), 1, 2)
        boxLayout.addWidget(self._borderThicknessLabel, 1, 3)

        boxLayout.addWidget(QLabel("Hitbox Margin (WM_NCHITTEST):"), 2, 0)
        boxLayout.addWidget(self._hitboxMarginLabel, 2, 1)
        boxLayout.addWidget(QLabel("TitleBar Height:"), 2, 2)
        boxLayout.addWidget(self._titleBarHeightLabel, 2, 3)

        mainLayout.addWidget(metricsBox)

        # Interactive DPI simulation bar
        simBox = QGroupBox("Interactive DPI Scaling Simulator")
        simLayout = QVBoxLayout(simBox)

        description = QLabel(
            "Test how the title bar, vector control buttons, and hitboxes adapt to target DPI scaling:"
        )
        description.setStyleSheet("color: #888888; font-size: 12px;")
        simLayout.addWidget(description)

        buttonRow = QHBoxLayout()
        buttonRow.setSpacing(8)

        scaleOptions = [
            ("100% (96 DPI)", 96),
            ("125% (120 DPI)", 120),
            ("150% (144 DPI)", 144),
            ("175% (168 DPI)", 168),
            ("200% (192 DPI)", 192),
        ]

        for labelText, dpiValue in scaleOptions:
            button = QPushButton(labelText)
            button.setMinimumHeight(32)
            button.clicked.connect(lambda _, d=dpiValue: self._simulateDpiChange(d))
            buttonRow.addWidget(button)

        self._toggleDpiButton = QPushButton("Disable DPI Scaling")
        self._toggleDpiButton.setMinimumHeight(32)
        self._toggleDpiButton.clicked.connect(self._toggleDpiScaling)
        buttonRow.addWidget(self._toggleDpiButton)

        simLayout.addLayout(buttonRow)
        mainLayout.addWidget(simBox)

        # Key technical points frame
        notesFrame = QFrame()
        notesFrame.setStyleSheet(
            "QFrame { background-color: rgba(128, 128, 128, 0.08); border-radius: 6px; padding: 8px; }"
        )
        notesLayout = QVBoxLayout(notesFrame)
        notesText = QLabel(
            "<b>Technical Features Verified:</b><br>"
            "• <b>WM_NCCALCSIZE:</b> Compensates border dimensions using native per-monitor metrics "
            "(<code>GetSystemMetricsForDpi</code>) to prevent 1-2px clipping on secondary screens.<br>"
            "• <b>WM_NCHITTEST:</b> Dynamically scales resizing border margins (<code>round(5 * dpi / 96)</code>) "
            "for effortless edge dragging on 4K displays.<br>"
            "• <b>WM_DPICHANGED:</b> Intercepts system DPI changes, delegating geometry bounds to Qt while "
            "re-rendering high-resolution icons and vector buttons."
        )
        notesText.setWordWrap(True)
        notesLayout.addWidget(notesText)
        mainLayout.addWidget(notesFrame)

        mainLayout.addStretch()
        return container

    def _refreshDpiMetrics(self) -> None:
        """Query and display live Win32 and Qt DPI metrics."""
        hWnd = int(self.winId())
        currentDpi = getDpiForWindow(hWnd)
        scalePercent = round((currentDpi / 96.0) * 100)

        self._currentDpiLabel.setText(f"{currentDpi} DPI ({scalePercent}%)")

        windowHandle = self.windowHandle()
        if windowHandle is not None:
            screen = windowHandle.screen()
            if screen is not None:
                self._screenNameLabel.setText(screen.name())
            self._devicePixelRatioLabel.setText(f"{windowHandle.devicePixelRatio():.2f}")

        borderThickness = getResizeBorderThickness(hWnd)
        self._borderThicknessLabel.setText(f"{borderThickness} px")

        scaledHitbox = round(getattr(self, "_borderWidth", 5) * currentDpi / 96)
        self._hitboxMarginLabel.setText(f"{scaledHitbox} px")

        titleBar = self.getTitleBar()
        if titleBar is not None:
            self._titleBarHeightLabel.setText(f"{titleBar.height()} px")

    def _simulateDpiChange(self, targetDpi: int) -> None:
        """Simulate a DPI change by updating the TitleBar and metric labels.

        Parameters
        ----------
        targetDpi : int
            Target DPI value to simulate (e.g. 96, 120, 144, 192).
        """
        titleBar = self.getTitleBar()
        if titleBar is not None:
            titleBar.updateDpiScaling(targetDpi)

        scalePercent = round((targetDpi / 96.0) * 100)
        self._currentDpiLabel.setText(f"{targetDpi} DPI ({scalePercent}%) [Simulated]")

        scaledHitbox = round(getattr(self, "_borderWidth", 5) * targetDpi / 96)
        self._hitboxMarginLabel.setText(f"{scaledHitbox} px")

        if titleBar is not None:
            self._titleBarHeightLabel.setText(f"{titleBar.sizeHint().height()} px")

    def _toggleDpiScaling(self) -> None:
        """Toggle automatic TitleBar DPI scaling on and off."""
        isCurrentlyAllowed = self.isDpiScalingAllowed()
        newAllowed = not isCurrentlyAllowed
        self.allowDpiScaling(newAllowed)

        if newAllowed:
            self._toggleDpiButton.setText("Disable DPI Scaling")
            self._refreshDpiMetrics()
        else:
            self._toggleDpiButton.setText("Enable DPI Scaling")
            self._refreshDpiMetrics()
            self._currentDpiLabel.setText("96 DPI (DPI Scaling Disabled)")


if __name__ == "__main__":
    application = QApplication(sys.argv)
    window = DpiScalingDemoWindow()
    window.show()
    sys.exit(application.exec())
