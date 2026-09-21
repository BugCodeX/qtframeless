"""Fluent menu styler for title bar integrated menu bars and popup menus.

Provides styling logic applying Windows 11 Fluent design QSS stylesheets
to QMenuBar and nested QMenu popups with DPI-aware padding and theme support.
"""

from qtpy.QtWidgets import QMenuBar

__all__ = ["MenuStyler"]


class MenuStyler:
    """Styler utility providing Windows 11 Fluent QSS themes for menu bars and popup menus."""

    @staticmethod
    def applyFluentMenuStyle(menuBar: QMenuBar, isDark: bool = False, dpi: int = 96) -> None:
        """Apply Fluent design transparent styles and popup menu styling to a menu bar.

        Parameters
        ----------
        menuBar : QMenuBar
            Target menu bar instance to style.
        isDark : bool, optional
            True for dark theme palette, False for light theme. Defaults to False.
        dpi : int, optional
            Screen dots-per-inch used to scale layout padding. Defaults to 96.
        """
        if dpi <= 0:
            dpi = 96
        scaleFactor = dpi / 96.0
        scaledPaddingLeft = max(4, round(8 * scaleFactor))

        menuBarRule = (
            f"QMenuBar {{\n"
            f"    background: transparent;\n"
            f"    border: none;\n"
            f"    padding: 0px 0px 0px {scaledPaddingLeft}px;\n"
            f"    margin: 0px;\n"
            f"    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;\n"
            f"    font-size: 13px;\n"
            f"}}\n"
        )

        if isDark:
            styleSheet = (
                menuBarRule
                + """QMenuBar::item {
    background: transparent;
    color: #ffffff;
    padding: 5px 10px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: rgba(255, 255, 255, 0.1);
}
QMenuBar::item:pressed {
    background-color: rgba(255, 255, 255, 0.15);
}
QMenu {
    background-color: #2c2c2c;
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    padding: 6px;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-size: 13px;
}
QMenu::item {
    background: transparent;
    color: #ffffff;
    padding: 6px 28px 6px 14px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}
QMenu::item:disabled {
    color: rgba(255, 255, 255, 0.4);
}
QMenu::separator {
    height: 1px;
    background: rgba(255, 255, 255, 0.12);
    margin: 4px 8px;
}
"""
            )
        else:
            styleSheet = (
                menuBarRule
                + """QMenuBar::item {
    background: transparent;
    color: #000000;
    padding: 5px 10px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: rgba(0, 0, 0, 0.08);
}
QMenuBar::item:pressed {
    background-color: rgba(0, 0, 0, 0.12);
}
QMenu {
    background-color: #f9f9f9;
    color: #000000;
    border: 1px solid rgba(0, 0, 0, 0.12);
    border-radius: 8px;
    padding: 6px;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-size: 13px;
}
QMenu::item {
    background: transparent;
    color: #000000;
    padding: 6px 28px 6px 14px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: rgba(0, 0, 0, 0.08);
    color: #000000;
}
QMenu::item:disabled {
    color: rgba(0, 0, 0, 0.35);
}
QMenu::separator {
    height: 1px;
    background: rgba(0, 0, 0, 0.1);
    margin: 4px 8px;
}
"""
            )
        menuBar.setStyleSheet(styleSheet)
