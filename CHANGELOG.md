# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-21

### What's New

- **Native Windows Frameless Windows**: Pure Python implementation of modern frameless windows with native DWM drop shadows, smooth border resizing, and full Windows 11 Snap Layouts integration.
- **Fluent Materials Support**: Native backdrop composition for Windows 11 Mica, Mica Alt, and Windows 10/11 Acrylic blur-behind effects.
- **Modern Modular TitleBar**: Fully customizable title bar with vector-rendered control buttons (`MinimizeButton`, `MaximizeButton`, `CloseButton`, `FullScreenButton`), customizable center widget container, and flexible title alignment (`AlignLeft`, `AlignCenter`).
- **Integrated QMenuBar**: Native integration of `QMenuBar` directly into the title bar with custom spacing, non-invasive dragging, and Fluent UI dropdown styling.
- **Cross-Qt Runtime Compatibility**: Complete decoupling and support for both PySide6 and PyQt6 via `qtpy`, including SIP null-dereference protection on native event loops and IntEnum property support.
- **Dark/Light Theme Synchronization**: Automatic detection and synchronization of Windows system theme changes via registry events and `darkThemeChanged` signal.
- **Public Version Exposure**: Exposed `qtframelesskit.__version__` at the package root.

### Changes

- **Fluent UI Sample Suite**: Enriched examples (`sample_mainwindow.py`, `sample_dialog.py`, `sample_widget.py`, `sample_modular_titlebar.py`, `sample_menubar_titlebar.py`) featuring modern Fluent UI cards, badges, sliders, and controls.
- **TitleBar Spacing & Alignment**: Vertically centered integrated menu bars with dedicated left-margin offsets from window icons.
- **Package Metadata & Type Support**: Added PEP 561 `py.typed` marker for static type checker discovery and updated PyPI classifiers for Windows 10/11 Production/Stable status.

### Fixes

- **TitleBar Button Geometry**: Ensured the close button aligns flush with the top window border according to Windows UX standards while keeping menu bars non-invasive to window drag hit-testing.
- **Platform Guard Execution Order**: Reordered platform check in `qtframelesskit/__init__.py` to immediately raise `PlatformNotSupportedError` on non-Windows platforms before attempting native imports.

### Documentation

- **Comprehensive README & Docs**: Published detailed documentation with quickstart guides, architecture overviews, styling guides, and API references on Read the Docs.
- **Animated Showcases**: Added transparent animated showcase GIFs demonstrating Snap Layouts, materials, and DPI scaling across Windows 11 and Windows 10.
- **Inspiration & Acknowledgments**: Added architectural acknowledgments to `qwindowkit` for Win32 message handling insights.

### Verification

```bash
# Install with preferred binding
pip install qtframelesskit[pyside6]==0.1.0  # or qtframelesskit[pyqt6]==0.1.0
python -c "import qtframelesskit; print(qtframelesskit.__version__)"
```
