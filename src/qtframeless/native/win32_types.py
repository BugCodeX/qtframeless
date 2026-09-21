"""ctypes mirrors of Win32 structures used by the frameless window machinery.

All types here map 1-to-1 to their C counterparts in the Windows SDK.
They are consumed by ``WM_NCCALCSIZE`` and DWM attribute handlers in
the frameless window implementation.
"""

from ctypes import POINTER, Structure, c_int, c_size_t, c_void_p
from ctypes.wintypes import BOOL, DWORD, HWND, RECT, UINT
from enum import Enum


class MARGINS(Structure):
    """ctypes mirror of the Win32 ``MARGINS`` structure.

    Passed to ``DwmExtendFrameIntoClientArea`` to control the DWM glass
    frame extension on each edge of the window.
    """

    _fields_ = [
        ("cxLeftWidth", c_int),
        ("cxRightWidth", c_int),
        ("cyTopHeight", c_int),
        ("cyBottomHeight", c_int),
    ]


class DWM_BLURBEHIND(Structure):
    """ctypes mirror of the Win32 ``DWM_BLURBEHIND`` structure.

    Passed to ``DwmEnableBlurBehindWindow`` to enable desktop window manager blur-behind.
    """

    _fields_ = [
        ("dwFlags", DWORD),
        ("fEnable", BOOL),
        ("hRgnBlur", c_void_p),
        ("fTransitionOnMaximized", BOOL),
    ]


DWM_BB_ENABLE = 0x00000001
DWM_BB_BLURREGION = 0x00000002
DWM_BB_TRANSITIONONMAXIMIZED = 0x00000004

ACCENT_FLAG_ACRYLIC = 0x1E0

DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMWA_MICA_EFFECT = 1029

DWMSBT_AUTO = 0
DWMSBT_NONE = 1
DWMSBT_MAINWINDOW = 2
DWMSBT_TRANSIENTWINDOW = 3
DWMSBT_TABBEDWINDOW = 4


class PWINDOWPOS(Structure):
    """ctypes mirror of the Win32 ``WINDOWPOS`` structure.

    Embedded inside :class:`NCCALCSIZE_PARAMS` and passed to
    ``WM_NCCALCSIZE`` to describe the new window position and size.
    """

    _fields_ = [
        ("hWnd", HWND),
        ("hwndInsertAfter", HWND),
        ("x", c_int),
        ("y", c_int),
        ("cx", c_int),
        ("cy", c_int),
        ("flags", UINT),
    ]


class NCCALCSIZE_PARAMS(Structure):
    """ctypes mirror of the Win32 ``NCCALCSIZE_PARAMS`` structure.

    Passed via ``lParam`` in ``WM_NCCALCSIZE`` when ``wParam`` is non-zero.
    ``rgrc[0]`` holds the proposed new client rect that we adjust to remove
    the native title bar from the non-client area calculation.
    """

    _fields_ = [
        ("rgrc", RECT * 3),
        ("lppos", POINTER(PWINDOWPOS)),
    ]


class DWMWINDOWATTRIBUTE(Enum):
    """Subset of the Win32 ``DWMWINDOWATTRIBUTE`` enum used by this library.

    Passed to ``DwmSetWindowAttribute`` to toggle immersive dark mode, corner
    rounding preference, border color, and system backdrop materials.
    """

    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    DWMWA_WINDOW_CORNER_PREFERENCE = 33
    DWMWA_BORDER_COLOR = 34
    DWMWA_CAPTION_COLOR = 35
    DWMWA_TEXT_COLOR = 36
    DWMWA_SYSTEMBACKDROP_TYPE = 38
    DWMWA_MICA_EFFECT = 1029


#: Special DWM window attribute color constants
DWMWA_COLOR_DEFAULT = 0xFFFFFFFF
DWMWA_COLOR_NONE = 0xFFFFFFFE


class WindowCornerPreference(Enum):
    """Windows 11 window corner rounding preferences.

    Values correspond directly to ``DWM_WINDOW_CORNER_PREFERENCE`` constants.
    """

    DEFAULT = 0
    DO_NOT_ROUND = 1
    ROUND = 2
    ROUND_SMALL = 3


class WindowEffect(Enum):
    """Supported native Windows backdrop materials and effects.

    Attributes
    ----------
    NONE : int
        Default solid window background with no backdrop material.
    MICA : int
        Windows 11 Mica material matching system theme and desktop wallpaper.
    ACRYLIC : int
        Windows 10/11 Acrylic blur-behind material with custom tint.
    MICA_ALT : int
        Windows 11 Mica Alt (tabbed) material for secondary surfaces.
    """

    NONE = 0
    MICA = 1
    ACRYLIC = 2
    MICA_ALT = 3


class DWM_SYSTEMBACKDROP_TYPE(Enum):
    """Win32 DWM_SYSTEMBACKDROP_TYPE enum values for Windows 11 Build 22621+.

    Attributes
    ----------
    AUTO : int
        System determines backdrop type automatically.
    NONE : int
        No backdrop material.
    MAINWINDOW : int
        Mica material for main application window.
    TRANSIENTWINDOW : int
        Acrylic backdrop material.
    TABBEDWINDOW : int
        Mica Alt material for tabbed windows.
    """

    AUTO = 0
    NONE = 1
    MAINWINDOW = 2
    TRANSIENTWINDOW = 3
    TABBEDWINDOW = 4


class ACCENT_STATE(Enum):
    """Win32 SetWindowCompositionAttribute accent policy states.

    Attributes
    ----------
    ACCENT_DISABLED : int
        Disables composition accent policy.
    ACCENT_ENABLE_GRADIENT : int
        Enables solid gradient fill.
    ACCENT_ENABLE_TRANSPARENTGRADIENT : int
        Enables translucent gradient fill.
    ACCENT_ENABLE_BLURBEHIND : int
        Enables classic Aero blur behind.
    ACCENT_ENABLE_ACRYLICBLURBEHIND : int
        Enables modern Fluent Acrylic blur behind.
    ACCENT_ENABLE_HOSTBACKDROP : int
        Enables host backdrop blur.
    ACCENT_INVALID_STATE : int
        Invalid accent state boundary.
    """

    ACCENT_DISABLED = 0
    ACCENT_ENABLE_GRADIENT = 1
    ACCENT_ENABLE_TRANSPARENTGRADIENT = 2
    ACCENT_ENABLE_BLURBEHIND = 3
    ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
    ACCENT_ENABLE_HOSTBACKDROP = 5
    ACCENT_INVALID_STATE = 6


class ACCENT_POLICY(Structure):
    """ctypes mirror of the Win32 ``ACCENT_POLICY`` structure.

    Configures window accent attributes such as Acrylic blur behind and tint.
    """

    _fields_ = [
        ("AccentState", DWORD),
        ("AccentFlags", DWORD),
        ("GradientColor", DWORD),
        ("AnimationId", DWORD),
    ]


class WINDOWCOMPOSITIONATTRIBDATA(Structure):
    """ctypes mirror of the Win32 ``WINDOWCOMPOSITIONATTRIBDATA`` structure.

    Passed to ``SetWindowCompositionAttribute`` to apply accent policies.
    """

    _fields_ = [
        ("Attrib", DWORD),
        ("pvData", c_void_p),
        ("cbData", c_size_t),
    ]


WCA_ACCENT_POLICY = 19


def colorToColorRef(color: object) -> int:
    """Convert a QColor or hex string into a Win32 COLORREF integer (0x00BBGGRR).

    Parameters
    ----------
    color : QColor or str
        Color representation to convert.

    Returns
    -------
    int
        Win32 COLORREF representation (0x00BBGGRR), or 0xFFFFFFFE (default) if invalid.
    """
    from qtpy.QtGui import QColor

    qcolor: QColor
    if isinstance(color, str):
        qcolor = QColor(color)
    elif isinstance(color, QColor):
        qcolor = color
    else:
        return 0xFFFFFFFE

    if not qcolor.isValid():
        return 0xFFFFFFFE

    return (qcolor.blue() << 16) | (qcolor.green() << 8) | qcolor.red()


#: Pointer type for :class:`NCCALCSIZE_PARAMS`, used to cast ``lParam``
#: in ``WM_NCCALCSIZE`` when ``wParam`` is non-zero.
LPNCCALCSIZE_PARAMS = POINTER(NCCALCSIZE_PARAMS)


class TRACKMOUSEEVENT(Structure):
    """ctypes mirror of the Win32 ``TRACKMOUSEEVENT`` structure.

    Passed to ``TrackMouseEvent`` to request non-client mouse leave notifications.
    """

    _fields_ = [
        ("cbSize", DWORD),
        ("dwFlags", DWORD),
        ("hwndTrack", HWND),
        ("dwHoverTime", DWORD),
    ]


TME_HOVER = 0x00000001
TME_LEAVE = 0x00000002
TME_NONCLIENT = 0x00000010
WM_NCMOUSELEAVE = 0x02A2
WM_DPICHANGED = 0x02E0
