"""Tests verifying clean, canonical public API exports across qtframeless modules."""


def test_qtframeless_public_exports():
    """Verify clean canonical public classes and functions are exported at root."""
    import qtframeless

    expectedSymbols = [
        "FramelessDialog",
        "FramelessMainWindow",
        "FramelessWidget",
        "PlatformNotSupportedError",
        "TitleBar",
        "WindowCornerPreference",
    ]
    for symbol in expectedSymbols:
        assert hasattr(qtframeless, symbol), f"qtframeless missing export {symbol}"

    # Verify internal Base classes and lowercase aliases are not polluted in root __all__
    for internalSymbol in [
        "BaseDialog",
        "BaseMainWindow",
        "BaseWidget",
        "baseDialog",
        "baseMainWindow",
        "baseWidget",
    ]:
        assert internalSymbol not in qtframeless.__all__


def test_canonical_native_exports():
    """Verify qtframeless.native exports required structures and visual effect helpers."""
    import qtframeless.native as nativeModule

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
        assert hasattr(nativeModule, symbol), f"qtframeless.native missing export {symbol}"
        assert symbol in nativeModule.__all__, f"qtframeless.native.__all__ missing {symbol}"


def test_canonical_core_exports():
    """Verify qtframeless.core exports frame controller, theme, and mixin components."""
    import qtframeless.core as coreModule

    assert hasattr(coreModule, "FramelessWindowMixin")
    assert hasattr(coreModule, "WindowFrameController")
    assert hasattr(coreModule, "ThemeController")


def test_canonical_windows_exports():
    """Verify qtframeless.windows exports base window classes and title bar without lowercase aliases."""
    import qtframeless.windows as windowsModule

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
        assert hasattr(windowsModule, symbol), f"qtframeless.windows missing export {symbol}"
        assert symbol in windowsModule.__all__, f"qtframeless.windows.__all__ missing {symbol}"

    # Verify lowercase aliases are purged from __all__
    for legacyAlias in ["baseWidget", "baseDialog", "baseMainWindow", "titleBar"]:
        assert legacyAlias not in windowsModule.__all__
