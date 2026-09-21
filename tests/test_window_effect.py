"""Unit and integration tests for native window backdrop materials and effects."""

import ctypes
from ctypes import sizeof


def test_window_effect_enum():
    """Verify WindowEffect enum definition and member values."""
    from qtframeless.native.win32_types import WindowEffect

    assert WindowEffect.NONE.value == 0
    assert WindowEffect.MICA.value == 1
    assert WindowEffect.ACRYLIC.value == 2
    assert WindowEffect.MICA_ALT.value == 3


def test_dwm_system_backdrop_type_enum():
    """Verify DWM_SYSTEMBACKDROP_TYPE enum values match Windows SDK definitions."""
    from qtframeless.native.win32_types import DWM_SYSTEMBACKDROP_TYPE

    assert DWM_SYSTEMBACKDROP_TYPE.AUTO.value == 0
    assert DWM_SYSTEMBACKDROP_TYPE.NONE.value == 1
    assert DWM_SYSTEMBACKDROP_TYPE.MAINWINDOW.value == 2
    assert DWM_SYSTEMBACKDROP_TYPE.TRANSIENTWINDOW.value == 3
    assert DWM_SYSTEMBACKDROP_TYPE.TABBEDWINDOW.value == 4


def test_accent_structures_and_enums():
    """Verify ACCENT_STATE, ACCENT_POLICY, and WINDOWCOMPOSITIONATTRIBDATA ctypes layouts."""
    from qtframeless.native.win32_types import (
        ACCENT_POLICY,
        ACCENT_STATE,
        WINDOWCOMPOSITIONATTRIBDATA,
    )

    assert ACCENT_STATE.ACCENT_DISABLED.value == 0
    assert ACCENT_STATE.ACCENT_ENABLE_GRADIENT.value == 1
    assert ACCENT_STATE.ACCENT_ENABLE_TRANSPARENTGRADIENT.value == 2
    assert ACCENT_STATE.ACCENT_ENABLE_BLURBEHIND.value == 3
    assert ACCENT_STATE.ACCENT_ENABLE_ACRYLICBLURBEHIND.value == 4
    assert ACCENT_STATE.ACCENT_ENABLE_HOSTBACKDROP.value == 5
    assert ACCENT_STATE.ACCENT_INVALID_STATE.value == 6

    policy = ACCENT_POLICY()
    policy.AccentState = ACCENT_STATE.ACCENT_ENABLE_ACRYLICBLURBEHIND.value
    policy.AccentFlags = 2
    policy.GradientColor = 0x99222222
    policy.AnimationId = 0
    assert sizeof(ACCENT_POLICY) == 16

    attribData = WINDOWCOMPOSITIONATTRIBDATA()
    attribData.Attrib = 19
    attribData.pvData = ctypes.cast(ctypes.byref(policy), ctypes.c_void_p).value
    attribData.cbData = sizeof(policy)
    assert attribData.Attrib == 19
    assert attribData.cbData == 16


def test_dwm_blurbehind_structure_and_constants():
    """Verify DWM_BLURBEHIND ctypes structure and associated flags."""
    from qtframeless.native.win32_types import (
        ACCENT_FLAG_ACRYLIC,
        DWM_BB_BLURREGION,
        DWM_BB_ENABLE,
        DWM_BB_TRANSITIONONMAXIMIZED,
        DWM_BLURBEHIND,
    )

    assert DWM_BB_ENABLE == 0x00000001
    assert DWM_BB_BLURREGION == 0x00000002
    assert DWM_BB_TRANSITIONONMAXIMIZED == 0x00000004
    assert ACCENT_FLAG_ACRYLIC == 0x1E0

    blurBehind = DWM_BLURBEHIND()
    blurBehind.dwFlags = DWM_BB_ENABLE
    blurBehind.fEnable = True
    blurBehind.hRgnBlur = None
    blurBehind.fTransitionOnMaximized = False

    assert blurBehind.dwFlags == 0x00000001
    assert bool(blurBehind.fEnable) is True


def test_dwm_backdrop_constants_direct_export():
    """Verify backdrop constants exported from win32_types and window_effect."""
    from qtframeless.native.win32_types import (
        DWMSBT_AUTO,
        DWMSBT_MAINWINDOW,
        DWMSBT_NONE,
        DWMSBT_TABBEDWINDOW,
        DWMSBT_TRANSIENTWINDOW,
        DWMWA_MICA_EFFECT,
        DWMWA_SYSTEMBACKDROP_TYPE,
    )
    from qtframeless.native.window_effect import (
        DWMSBT_MAINWINDOW as EFFECT_MAINWINDOW,
    )
    from qtframeless.native.window_effect import (
        DWMSBT_TABBEDWINDOW as EFFECT_TABBEDWINDOW,
    )
    from qtframeless.native.window_effect import (
        DWMWA_MICA_EFFECT as EFFECT_MICA,
    )
    from qtframeless.native.window_effect import (
        DWMWA_SYSTEMBACKDROP_TYPE as EFFECT_BACKDROP,
    )

    assert DWMWA_SYSTEMBACKDROP_TYPE == 38
    assert DWMWA_MICA_EFFECT == 1029
    assert DWMSBT_AUTO == 0
    assert DWMSBT_NONE == 1
    assert DWMSBT_MAINWINDOW == 2
    assert DWMSBT_TRANSIENTWINDOW == 3
    assert DWMSBT_TABBEDWINDOW == 4

    assert EFFECT_BACKDROP == 38
    assert EFFECT_MICA == 1029
    assert EFFECT_MAINWINDOW == 2
    assert EFFECT_TABBEDWINDOW == 4


def test_enable_blur_behind_window(monkeypatch):
    """Verify enableBlurBehindWindow configures DWM_BLURBEHIND and calls native API.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from qtframeless.native.win32_types import DWM_BB_ENABLE, DWM_BLURBEHIND
    from qtframeless.native.window_effect import WindowsEffectHelper

    helper = WindowsEffectHelper()
    recordedCalls = []

    def fakeDwmEnableBlurBehindWindow(hWnd, blurBehindPointer):
        bb = ctypes.cast(blurBehindPointer, ctypes.POINTER(DWM_BLURBEHIND)).contents
        recordedCalls.append((hWnd, bb.dwFlags, bool(bb.fEnable)))
        return 0

    monkeypatch.setattr(
        helper,
        "_WindowsEffectHelper__dwmEnableBlurBehindWindow",
        fakeDwmEnableBlurBehindWindow,
    )

    assert helper.enableBlurBehindWindow(4001) is True
    assert recordedCalls[-1] == (4001, DWM_BB_ENABLE, True)


def test_refresh_background_blur_effect(monkeypatch):
    """Verify refreshBackgroundBlurEffect reapplies acrylic blur composition.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from qtframeless.native.window_effect import WindowsEffectHelper

    helper = WindowsEffectHelper()
    refreshedHandles = []

    monkeypatch.setattr(
        helper,
        "setAcrylicEffect",
        lambda hWnd, gradientColor=None: refreshedHandles.append((hWnd, gradientColor)) or True,
    )

    result = helper.refreshBackgroundBlurEffect(5001, 0x99AABBCC)
    assert result is True
    assert (5001, 0x99AABBCC) in refreshedHandles


def test_set_acrylic_effect_accent_flags_and_blur_behind(monkeypatch):
    """Verify setAcrylicEffect uses AccentFlags = 0x1E0 and enables blur behind.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from qtframeless.native.win32_types import (
        ACCENT_FLAG_ACRYLIC,
        ACCENT_POLICY,
        WINDOWCOMPOSITIONATTRIBDATA,
    )
    from qtframeless.native.window_effect import WindowsEffectHelper

    helper = WindowsEffectHelper()
    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin10_17063",
        lambda: True,
    )

    blurBehindCalled = []
    monkeypatch.setattr(
        helper,
        "enableBlurBehindWindow",
        lambda hWnd: blurBehindCalled.append(hWnd) or True,
    )

    recordedFlags = []

    def fakeWindowCompositionAttribute(hWnd, dataPointer):
        data = ctypes.cast(dataPointer, ctypes.POINTER(WINDOWCOMPOSITIONATTRIBDATA)).contents
        policy = ctypes.cast(data.pvData, ctypes.POINTER(ACCENT_POLICY)).contents
        recordedFlags.append((hWnd, policy.AccentFlags))
        return 1

    monkeypatch.setattr(
        helper,
        "_WindowsEffectHelper__windowCompositionAttribute",
        fakeWindowCompositionAttribute,
    )

    success = helper.setAcrylicEffect(6001)
    assert success is True
    assert 6001 in blurBehindCalled
    assert recordedFlags[-1] == (6001, ACCENT_FLAG_ACRYLIC)
    assert recordedFlags[-1][1] == 0x1E0


def test_dwm_window_attributes_extended():
    """Verify extended DWMWINDOWATTRIBUTE enum values for Mica and system backdrop."""
    from qtframeless.native.win32_types import (
        DWMWA_COLOR_DEFAULT,
        DWMWA_COLOR_NONE,
        DWMWINDOWATTRIBUTE,
    )

    assert DWMWINDOWATTRIBUTE.DWMWA_CAPTION_COLOR.value == 35
    assert DWMWINDOWATTRIBUTE.DWMWA_TEXT_COLOR.value == 36
    assert DWMWINDOWATTRIBUTE.DWMWA_SYSTEMBACKDROP_TYPE.value == 38
    assert DWMWINDOWATTRIBUTE.DWMWA_MICA_EFFECT.value == 1029
    assert DWMWA_COLOR_DEFAULT == 0xFFFFFFFF
    assert DWMWA_COLOR_NONE == 0xFFFFFFFE


def test_window_effect_root_export():
    """Verify WindowEffect is exported from the root qtframeless package and in __all__."""
    import qtframeless
    from qtframeless import WindowEffect

    assert WindowEffect.NONE.value == 0
    assert WindowEffect.MICA.value == 1
    assert WindowEffect.ACRYLIC.value == 2
    assert WindowEffect.MICA_ALT.value == 3
    assert "WindowEffect" in qtframeless.__all__


def test_set_mica_effect_win11_22621(monkeypatch):
    """Verify setMicaEffect applies attribute 38 on Windows 11 Build 22621 or newer.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from qtframeless.native.win32_types import (
        DWM_SYSTEMBACKDROP_TYPE,
        DWMWINDOWATTRIBUTE,
    )
    from qtframeless.native.window_effect import WindowsEffectHelper

    helper = WindowsEffectHelper()
    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin11_22H2",
        lambda: True,
    )

    recordedCalls = []

    def fakeDwmSetWindowAttribute(hWnd, attribute, valuePointer, valueSize):
        val = ctypes.cast(valuePointer, ctypes.POINTER(ctypes.c_int)).contents.value
        recordedCalls.append((hWnd, attribute, val))
        return 0

    monkeypatch.setattr(
        helper,
        "_WindowsEffectHelper__dwmSetWindowAttribute",
        fakeDwmSetWindowAttribute,
    )

    successMica = helper.setMicaEffect(1001, isAlt=False)
    assert successMica is True
    assert (
        1001,
        DWMWINDOWATTRIBUTE.DWMWA_SYSTEMBACKDROP_TYPE.value,
        DWM_SYSTEMBACKDROP_TYPE.MAINWINDOW.value,
    ) in recordedCalls
    assert (
        1001,
        DWMWINDOWATTRIBUTE.DWMWA_CAPTION_COLOR.value,
        -2,
    ) in recordedCalls

    successAlt = helper.setMicaEffect(1001, isAlt=True)
    assert successAlt is True
    assert (
        1001,
        DWMWINDOWATTRIBUTE.DWMWA_SYSTEMBACKDROP_TYPE.value,
        DWM_SYSTEMBACKDROP_TYPE.TABBEDWINDOW.value,
    ) in recordedCalls
    assert (
        1001,
        DWMWINDOWATTRIBUTE.DWMWA_CAPTION_COLOR.value,
        -2,
    ) in recordedCalls


def test_set_mica_effect_win11_22000(monkeypatch):
    """Verify setMicaEffect falls back to attribute 1029 on Windows 11 Build 22000.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from qtframeless.native.win32_types import DWMWINDOWATTRIBUTE
    from qtframeless.native.window_effect import WindowsEffectHelper

    helper = WindowsEffectHelper()
    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin11_22H2",
        lambda: False,
    )
    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin11",
        lambda: True,
    )

    recordedCalls = []

    def fakeDwmSetWindowAttribute(hWnd, attribute, valuePointer, valueSize):
        val = ctypes.cast(valuePointer, ctypes.POINTER(ctypes.c_int)).contents.value
        recordedCalls.append((hWnd, attribute, val))
        return 0

    monkeypatch.setattr(
        helper,
        "_WindowsEffectHelper__dwmSetWindowAttribute",
        fakeDwmSetWindowAttribute,
    )

    success = helper.setMicaEffect(1002, isAlt=False)
    assert success is True
    assert (
        1002,
        DWMWINDOWATTRIBUTE.DWMWA_MICA_EFFECT.value,
        1,
    ) in recordedCalls
    assert (
        1002,
        DWMWINDOWATTRIBUTE.DWMWA_CAPTION_COLOR.value,
        -2,
    ) in recordedCalls


def test_set_mica_effect_unsupported_platform(monkeypatch):
    """Verify setMicaEffect returns False on platforms older than Windows 11 without exception.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from qtframeless.native.window_effect import WindowsEffectHelper

    helper = WindowsEffectHelper()
    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin11_22H2",
        lambda: False,
    )
    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin11",
        lambda: False,
    )

    assert helper.setMicaEffect(1003) is False


def test_set_acrylic_effect_supported(monkeypatch):
    """Verify setAcrylicEffect applies ACCENT_ENABLE_ACRYLICBLURBEHIND on supported platforms.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from qtframeless.native.win32_types import (
        ACCENT_POLICY,
        ACCENT_STATE,
        WCA_ACCENT_POLICY,
        WINDOWCOMPOSITIONATTRIBDATA,
    )
    from qtframeless.native.window_effect import WindowsEffectHelper

    helper = WindowsEffectHelper()
    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin10_17063",
        lambda: True,
    )

    recordedCalls = []

    def fakeWindowCompositionAttribute(hWnd, dataPointer):
        data = ctypes.cast(dataPointer, ctypes.POINTER(WINDOWCOMPOSITIONATTRIBDATA)).contents
        policy = ctypes.cast(data.pvData, ctypes.POINTER(ACCENT_POLICY)).contents
        recordedCalls.append((hWnd, data.Attrib, policy.AccentState, policy.GradientColor))
        return 1

    monkeypatch.setattr(
        helper,
        "_WindowsEffectHelper__windowCompositionAttribute",
        fakeWindowCompositionAttribute,
    )

    success = helper.setAcrylicEffect(2001, gradientColor=0x99222222)
    assert success is True
    assert recordedCalls[-1] == (
        2001,
        WCA_ACCENT_POLICY,
        ACCENT_STATE.ACCENT_ENABLE_ACRYLICBLURBEHIND.value,
        0x99222222,
    )


def test_set_acrylic_effect_color_conversions(monkeypatch):
    """Verify setAcrylicEffect handles hex strings and None defaults for gradientColor.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from qtframeless.native.win32_types import (
        ACCENT_POLICY,
        WINDOWCOMPOSITIONATTRIBDATA,
    )
    from qtframeless.native.window_effect import WindowsEffectHelper

    helper = WindowsEffectHelper()
    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin10_17063",
        lambda: True,
    )

    recordedColors = []

    def fakeWindowCompositionAttribute(hWnd, dataPointer):
        data = ctypes.cast(dataPointer, ctypes.POINTER(WINDOWCOMPOSITIONATTRIBDATA)).contents
        policy = ctypes.cast(data.pvData, ctypes.POINTER(ACCENT_POLICY)).contents
        recordedColors.append(policy.GradientColor)
        return 1

    monkeypatch.setattr(
        helper,
        "_WindowsEffectHelper__windowCompositionAttribute",
        fakeWindowCompositionAttribute,
    )

    helper.setAcrylicEffect(2002, gradientColor=None)
    assert recordedColors[-1] == 0x99F2F2F2

    helper.setAcrylicEffect(2002, gradientColor="#99222222")
    assert recordedColors[-1] == 0x22222299


def test_set_acrylic_effect_unsupported_and_error_handling(monkeypatch):
    """Verify setAcrylicEffect returns False on unsupported platforms or when OSError occurs.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from qtframeless.native.window_effect import WindowsEffectHelper

    helper = WindowsEffectHelper()
    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin10_17063",
        lambda: False,
    )
    assert helper.setAcrylicEffect(2003) is False

    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin10_17063",
        lambda: True,
    )

    def fakeRaisingCompositionAttribute(hWnd, dataPointer):
        raise OSError("Invalid window handle")

    monkeypatch.setattr(
        helper,
        "_WindowsEffectHelper__windowCompositionAttribute",
        fakeRaisingCompositionAttribute,
    )
    assert helper.setAcrylicEffect(2003) is False


def test_remove_backdrop_effect(monkeypatch):
    """Verify removeBackdropEffect resets DWM system backdrop and clears Acrylic composition.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from qtframeless.native.win32_types import (
        ACCENT_POLICY,
        ACCENT_STATE,
        DWM_SYSTEMBACKDROP_TYPE,
        DWMWINDOWATTRIBUTE,
        WCA_ACCENT_POLICY,
        WINDOWCOMPOSITIONATTRIBDATA,
    )
    from qtframeless.native.window_effect import WindowsEffectHelper

    helper = WindowsEffectHelper()
    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin11_22H2",
        lambda: True,
    )
    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin10_17063",
        lambda: True,
    )

    dwmCalls = []
    wcaCalls = []

    def fakeDwmSetWindowAttribute(hWnd, attribute, valuePointer, valueSize):
        val = ctypes.cast(valuePointer, ctypes.POINTER(ctypes.c_int)).contents.value
        dwmCalls.append((hWnd, attribute, val))
        return 0

    def fakeWindowCompositionAttribute(hWnd, dataPointer):
        data = ctypes.cast(dataPointer, ctypes.POINTER(WINDOWCOMPOSITIONATTRIBDATA)).contents
        policy = ctypes.cast(data.pvData, ctypes.POINTER(ACCENT_POLICY)).contents
        wcaCalls.append((hWnd, data.Attrib, policy.AccentState))
        return 1

    monkeypatch.setattr(
        helper,
        "_WindowsEffectHelper__dwmSetWindowAttribute",
        fakeDwmSetWindowAttribute,
    )
    monkeypatch.setattr(
        helper,
        "_WindowsEffectHelper__windowCompositionAttribute",
        fakeWindowCompositionAttribute,
    )

    success = helper.removeBackdropEffect(3001)
    assert success is True
    assert (
        3001,
        DWMWINDOWATTRIBUTE.DWMWA_SYSTEMBACKDROP_TYPE.value,
        DWM_SYSTEMBACKDROP_TYPE.NONE.value,
    ) in dwmCalls
    assert (
        3001,
        DWMWINDOWATTRIBUTE.DWMWA_CAPTION_COLOR.value,
        -1,
    ) in dwmCalls
    assert (3001, WCA_ACCENT_POLICY, ACCENT_STATE.ACCENT_DISABLED.value) in wcaCalls


def test_remove_backdrop_effect_win11_22000(monkeypatch):
    """Verify removeBackdropEffect resets attribute 1029 on Windows 11 Build 22000.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from qtframeless.native.win32_types import DWMWINDOWATTRIBUTE
    from qtframeless.native.window_effect import WindowsEffectHelper

    helper = WindowsEffectHelper()
    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin11_22H2",
        lambda: False,
    )
    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin11",
        lambda: True,
    )
    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin10_17063",
        lambda: False,
    )

    dwmCalls = []

    def fakeDwmSetWindowAttribute(hWnd, attribute, valuePointer, valueSize):
        val = ctypes.cast(valuePointer, ctypes.POINTER(ctypes.c_int)).contents.value
        dwmCalls.append((hWnd, attribute, val))
        return 0

    monkeypatch.setattr(
        helper,
        "_WindowsEffectHelper__dwmSetWindowAttribute",
        fakeDwmSetWindowAttribute,
    )

    success = helper.removeBackdropEffect(3002)
    assert success is True
    assert (3002, DWMWINDOWATTRIBUTE.DWMWA_MICA_EFFECT.value, 0) in dwmCalls
    assert (3002, DWMWINDOWATTRIBUTE.DWMWA_CAPTION_COLOR.value, -1) in dwmCalls


def test_parse_gradient_color_variations():
    """Verify _parseGradientColor handles QColor, 6-char hex, 0x prefix, and invalid strings."""
    from qtpy.QtGui import QColor

    from qtframeless.native.window_effect import _parseGradientColor

    assert _parseGradientColor(None) == 0x99F2F2F2
    assert _parseGradientColor(0x11223344) == 0x11223344
    assert _parseGradientColor("0x11223344") == 0x11223344
    assert _parseGradientColor("invalid") == 0x99F2F2F2
    assert _parseGradientColor(12345.67) == 0x99F2F2F2

    # 6-char hex "#112233" -> 99 + 33 + 22 + 11 = 0x99332211
    assert _parseGradientColor("#112233") == 0x99332211

    # QColor
    qcolor = QColor(0x11, 0x22, 0x33, 0x88)
    expectedFromQColor = (0x88 << 24) | (0x33 << 16) | (0x22 << 8) | 0x11
    assert _parseGradientColor(qcolor) == expectedFromQColor


def test_set_caption_color(monkeypatch):
    """Verify setCaptionColor sets DWMWA_CAPTION_COLOR with expected values on Windows 11.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from qtframeless.native.win32_types import (
        DWMWA_COLOR_DEFAULT,
        DWMWA_COLOR_NONE,
        DWMWINDOWATTRIBUTE,
    )
    from qtframeless.native.window_effect import WindowsEffectHelper

    helper = WindowsEffectHelper()
    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin11",
        lambda: True,
    )

    recordedCalls = []

    def fakeDwmSetWindowAttribute(hWnd, attribute, valuePointer, valueSize):
        val = ctypes.cast(valuePointer, ctypes.POINTER(ctypes.c_uint)).contents.value
        recordedCalls.append((hWnd, attribute, val))
        return 0

    monkeypatch.setattr(
        helper,
        "_WindowsEffectHelper__dwmSetWindowAttribute",
        fakeDwmSetWindowAttribute,
    )

    # 1. DWMWA_COLOR_NONE
    assert helper.setCaptionColor(7001, DWMWA_COLOR_NONE) is True
    assert recordedCalls[-1] == (
        7001,
        DWMWINDOWATTRIBUTE.DWMWA_CAPTION_COLOR.value,
        DWMWA_COLOR_NONE,
    )

    # 2. None -> DWMWA_COLOR_NONE
    assert helper.setCaptionColor(7001, None) is True
    assert recordedCalls[-1] == (
        7001,
        DWMWINDOWATTRIBUTE.DWMWA_CAPTION_COLOR.value,
        DWMWA_COLOR_NONE,
    )

    # 3. DWMWA_COLOR_DEFAULT
    assert helper.setCaptionColor(7001, DWMWA_COLOR_DEFAULT) is True
    assert recordedCalls[-1] == (
        7001,
        DWMWINDOWATTRIBUTE.DWMWA_CAPTION_COLOR.value,
        DWMWA_COLOR_DEFAULT,
    )

    # 4. Hex color string
    assert helper.setCaptionColor(7001, "#FF0000") is True
    # #FF0000 is red: COLORREF = 0x000000FF = 255
    assert recordedCalls[-1] == (
        7001,
        DWMWINDOWATTRIBUTE.DWMWA_CAPTION_COLOR.value,
        255,
    )


def test_set_caption_color_unsupported(monkeypatch):
    """Verify setCaptionColor returns False on platforms older than Windows 11.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from qtframeless.native.window_effect import WindowsEffectHelper

    helper = WindowsEffectHelper()
    monkeypatch.setattr(
        "qtframeless.native.window_effect.isGreaterEqualWin11",
        lambda: False,
    )

    assert helper.setCaptionColor(7002, None) is False


def test_set_dark_theme_dwm_attribute(monkeypatch):
    """Verify setDarkTheme passes BOOL pointer, sizeof(BOOL), and correct boolean value.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    """
    from ctypes import POINTER, cast, sizeof
    from ctypes.wintypes import BOOL

    from qtframeless.native.win32_types import DWMWINDOWATTRIBUTE
    from qtframeless.native.window_effect import WindowsEffectHelper

    helper = WindowsEffectHelper()
    recordedCalls = []

    def fakeDwmSetWindowAttribute(hWnd, attribute, valuePointer, valueSize):
        assert valueSize == sizeof(BOOL)
        val = cast(valuePointer, POINTER(BOOL)).contents.value
        recordedCalls.append((hWnd, attribute, val))
        return 0

    monkeypatch.setattr(
        helper,
        "_WindowsEffectHelper__dwmSetWindowAttribute",
        fakeDwmSetWindowAttribute,
    )

    resultDark = helper.setDarkTheme(9001, True)
    assert resultDark is True
    assert (
        9001,
        DWMWINDOWATTRIBUTE.DWMWA_USE_IMMERSIVE_DARK_MODE.value,
        1,
    ) in recordedCalls

    resultLight = helper.setDarkTheme(9001, False)
    assert resultLight is True
    assert (
        9001,
        DWMWINDOWATTRIBUTE.DWMWA_USE_IMMERSIVE_DARK_MODE.value,
        0,
    ) in recordedCalls
