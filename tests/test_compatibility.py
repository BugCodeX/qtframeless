"""Tests verifying clean, canonical public API exports across qtframelesskit modules."""


def test_qtframelesskit_public_exports():
    """Verify clean canonical public classes and functions are exported at root."""
    import qtframelesskit

    expectedSymbols = [
        "FramelessDialog",
        "FramelessMainWindow",
        "FramelessWidget",
        "PlatformNotSupportedError",
        "TitleBar",
        "WindowCornerPreference",
    ]
    for symbol in expectedSymbols:
        assert hasattr(qtframelesskit, symbol), f"qtframelesskit missing export {symbol}"

    # Verify internal Base classes and lowercase aliases are not polluted in root __all__
    for internalSymbol in [
        "BaseDialog",
        "BaseMainWindow",
        "BaseWidget",
        "baseDialog",
        "baseMainWindow",
        "baseWidget",
    ]:
        assert internalSymbol not in qtframelesskit.__all__


def test_canonical_native_exports():
    """Verify qtframelesskit.native exports required structures and visual effect helpers."""
    import qtframelesskit.native as nativeModule

    expectedNativeSymbols = [
        "DWMWA_COLOR_DEFAULT",
        "DWMWA_COLOR_NONE",
        "DWMWINDOWATTRIBUTE",
        "WindowCornerPreference",
        "WindowEffect",
        "WindowsEffectHelper",
        "colorToColorRef",
        "win32_types",
        "win32_utils",
        "window_effect",
    ]
    for symbol in expectedNativeSymbols:
        assert hasattr(nativeModule, symbol), f"qtframelesskit.native missing export {symbol}"
        assert symbol in nativeModule.__all__, f"qtframelesskit.native.__all__ missing {symbol}"


def test_canonical_core_exports():
    """Verify qtframelesskit.core exports frame controller, theme, and mixin components."""
    import qtframelesskit.core as coreModule

    assert hasattr(coreModule, "FramelessWindowMixin")
    assert hasattr(coreModule, "WindowFrameController")
    assert hasattr(coreModule, "ThemeController")


def test_canonical_windows_exports():
    """Verify qtframelesskit.windows exports base window classes and title bar without lowercase aliases."""
    import qtframelesskit.windows as windowsModule

    expectedWindowsSymbols = [
        "AcrylicWindowMixin",
        "BaseDialog",
        "BaseMainWindow",
        "BaseWidget",
        "CloseButton",
        "FramelessAcrylicDialog",
        "FramelessAcrylicMainWindow",
        "FramelessAcrylicWindow",
        "FramelessDialog",
        "FramelessMainWindow",
        "FramelessMicaDialog",
        "FramelessMicaMainWindow",
        "FramelessMicaWindow",
        "FramelessWidget",
        "FramelessWindow",
        "FullScreenButton",
        "MaximizeButton",
        "MinimizeButton",
        "MicaWindowMixin",
        "TitleBar",
        "VectorButton",
    ]
    for symbol in expectedWindowsSymbols:
        assert hasattr(windowsModule, symbol), f"qtframelesskit.windows missing export {symbol}"
        assert symbol in windowsModule.__all__, f"qtframelesskit.windows.__all__ missing {symbol}"

    # Verify lowercase aliases are purged from __all__
    for legacyAlias in ["baseWidget", "baseDialog", "baseMainWindow", "titleBar"]:
        assert legacyAlias not in windowsModule.__all__
