"""Automated screenshot capture and animated GIF showcase generator.

Captures sample windows demonstrating qtframelesskit capabilities:
modular title bar studio, integrated menu bar with centered title,
standard frameless main window, per-monitor DPI scaling, and frameless dialogs.
Supports Windows 11 (rounded corners, DWM border, and drop shadow) and Windows 10
(classic square borders) with automatic OS detection and dedicated directories.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

# Ensure repository root is on sys.path so examples package can be imported.
_repositoryRoot = Path(__file__).resolve().parent.parent
if str(_repositoryRoot) not in sys.path:
    sys.path.insert(0, str(_repositoryRoot))

from PIL import Image, ImageDraw
from qtpy.QtWidgets import QApplication, QWidget

from examples.sample_dialog import Window as DialogWindow
from examples.sample_dpi_scaling import DpiScalingDemoWindow
from examples.sample_mainwindow import Window as StandardMainWindow
from examples.sample_menubar_titlebar import Window as MenuBarTitleBarWindow
from examples.sample_modular_titlebar import ModularTitleBarWindow
from examples.sample_widget import Window as WidgetWindow

if TYPE_CHECKING:
    from collections.abc import Sequence


def detectWindowsVersion() -> str:
    """Detect whether the current host environment is Windows 11 or Windows 10.

    Windows 11 builds start at 22000. Any earlier Windows NT build is treated
    as Windows 10. Non-Windows platforms default to Windows 11 styling.

    Returns
    -------
    str
        Either ``"win11"`` or ``"win10"``.
    """
    if sys.platform == "win32":
        windowsVersion = sys.getwindowsversion()
        return "win11" if windowsVersion.build >= 22000 else "win10"
    return "win11"


def renderWindowFrame(
    rawWindowImage: Image.Image,
    isDarkTheme: bool,
    cornerRadius: int = 12,
) -> Image.Image:
    """Mask a window capture with native DWM borders and transparent rounded corners.

    On Windows 11 (cornerRadius > 0), applies the signature 12px corner rounding
    and a 1px subtle DWM border with a transparent background outside the corners.
    On Windows 10 (cornerRadius = 0), applies classic sharp square borders.

    Parameters
    ----------
    rawWindowImage : Image.Image
        Raw RGB/RGBA window capture from Qt.
    isDarkTheme : bool
        Whether the captured window is rendered in dark theme.
    cornerRadius : int, default 12
        Corner radius in pixels (12 for Windows 11, 0 for Windows 10).

    Returns
    -------
    Image.Image
        RGBA image of the window with transparent outer corners and 1px DWM border.
    """
    windowWidth, windowHeight = rawWindowImage.size

    # 1. Apply corner rounding mask to the window
    windowMask = Image.new("L", (windowWidth, windowHeight), 0)
    windowDraw = ImageDraw.Draw(windowMask)
    if cornerRadius > 0:
        windowDraw.rounded_rectangle(
            [(0, 0), (windowWidth - 1, windowHeight - 1)],
            radius=cornerRadius,
            fill=255,
        )
    else:
        windowDraw.rectangle(
            [(0, 0), (windowWidth - 1, windowHeight - 1)],
            fill=255,
        )

    windowLayer = Image.new("RGBA", (windowWidth, windowHeight), (0, 0, 0, 0))
    windowLayer.paste(rawWindowImage.convert("RGBA"), (0, 0), mask=windowMask)

    # 2. Draw 1px subtle DWM border
    borderDraw = ImageDraw.Draw(windowLayer)
    borderColor = (110, 110, 110, 255) if isDarkTheme else (190, 190, 190, 255)
    if cornerRadius > 0:
        borderDraw.rounded_rectangle(
            [(0, 0), (windowWidth - 1, windowHeight - 1)],
            radius=cornerRadius,
            outline=borderColor,
            width=1,
        )
    else:
        borderDraw.rectangle(
            [(0, 0), (windowWidth - 1, windowHeight - 1)],
            outline=borderColor,
            width=1,
        )

    return windowLayer


def captureWindow(
    window: QWidget,
    outputPath: Path,
    application: QApplication,
    isDarkTheme: bool,
    cornerRadius: int = 12,
    targetWidth: int = 800,
    targetHeight: int = 500,
) -> Path:
    """Resize, display, capture, and frame a window screenshot to disk.

    Parameters
    ----------
    window : QWidget
        The Qt window instance to display and capture.
    outputPath : Path
        Destination file path where the framed PNG image is written.
    application : QApplication
        Active Qt application instance processing window events.
    isDarkTheme : bool
        Whether the window is rendered in dark theme.
    cornerRadius : int, default 12
        Corner radius in pixels (12 for Windows 11, 0 for Windows 10).
    targetWidth : int, default 800
        Target window width in logical pixels.
    targetHeight : int, default 500
        Target window height in logical pixels.

    Returns
    -------
    Path
        Path to the saved PNG screenshot.
    """
    window.resize(targetWidth, targetHeight)
    window.show()
    application.processEvents()

    tempRawPath = outputPath.parent / f"_raw_{outputPath.name}"
    outputPath.parent.mkdir(parents=True, exist_ok=True)
    pixmap = window.grab()
    pixmap.save(str(tempRawPath), "PNG")

    with Image.open(tempRawPath) as rawImage:
        framedImage = renderWindowFrame(
            rawImage,
            isDarkTheme=isDarkTheme,
            cornerRadius=cornerRadius,
        )
        framedImage.save(outputPath, "PNG")

    tempRawPath.unlink(missing_ok=True)
    return outputPath


def captureAllScreenshots(
    outputDirectory: Path,
    application: QApplication,
    cornerRadius: int = 12,
    targetWidth: int = 800,
    targetHeight: int = 500,
) -> list[Path]:
    """Instantiate, configure, and capture showcase window states.

    Excludes backdrop material experiments and captures core widget and
    window examples in both light and dark themes.

    Parameters
    ----------
    outputDirectory : Path
        Directory where individual PNG screenshots will be stored.
    application : QApplication
        Active Qt application instance.
    cornerRadius : int, default 12
        Corner radius in pixels (12 for Windows 11, 0 for Windows 10).
    targetWidth : int, default 800
        Target window width in logical pixels.
    targetHeight : int, default 500
        Target window height in logical pixels.

    Returns
    -------
    list of Path
        Ordered list of paths to captured screenshot PNG files.
    """
    capturedPaths: list[Path] = []

    # 1 & 2: Modular TitleBar Studio (Dark & Light)
    modularStudioWindow = ModularTitleBarWindow()
    capturedPaths.append(
        captureWindow(
            modularStudioWindow,
            outputDirectory / "01_modular_studio_dark.png",
            application,
            isDarkTheme=True,
            cornerRadius=cornerRadius,
            targetWidth=targetWidth,
            targetHeight=targetHeight,
        )
    )
    modularStudioWindow._handleThemeToggle()
    capturedPaths.append(
        captureWindow(
            modularStudioWindow,
            outputDirectory / "02_modular_studio_light.png",
            application,
            isDarkTheme=False,
            cornerRadius=cornerRadius,
            targetWidth=targetWidth,
            targetHeight=targetHeight,
        )
    )
    modularStudioWindow.close()
    application.processEvents()

    # 3 & 4: MenuBar & Centered Title (Light & Dark)
    menuBarWindow = MenuBarTitleBarWindow()
    capturedPaths.append(
        captureWindow(
            menuBarWindow,
            outputDirectory / "03_menubar_centered_light.png",
            application,
            isDarkTheme=False,
            cornerRadius=cornerRadius,
            targetWidth=targetWidth,
            targetHeight=targetHeight,
        )
    )
    menuBarWindow._toggleTheme()
    capturedPaths.append(
        captureWindow(
            menuBarWindow,
            outputDirectory / "04_menubar_centered_dark.png",
            application,
            isDarkTheme=True,
            cornerRadius=cornerRadius,
            targetWidth=targetWidth,
            targetHeight=targetHeight,
        )
    )
    menuBarWindow.close()
    application.processEvents()

    # 5 & 6: Standard Frameless MainWindow (Light & Dark)
    standardMainWindow = StandardMainWindow()
    capturedPaths.append(
        captureWindow(
            standardMainWindow,
            outputDirectory / "05_standard_mainwindow_light.png",
            application,
            isDarkTheme=False,
            cornerRadius=cornerRadius,
            targetWidth=targetWidth,
            targetHeight=targetHeight,
        )
    )
    standardMainWindow._toggleTheme()
    capturedPaths.append(
        captureWindow(
            standardMainWindow,
            outputDirectory / "06_standard_mainwindow_dark.png",
            application,
            isDarkTheme=True,
            cornerRadius=cornerRadius,
            targetWidth=targetWidth,
            targetHeight=targetHeight,
        )
    )
    standardMainWindow.close()
    application.processEvents()

    # 7: Frameless Widget Component (Dark)
    widgetWindow = WidgetWindow()
    if not widgetWindow.darkTheme:
        widgetWindow._toggleTheme()
    capturedPaths.append(
        captureWindow(
            widgetWindow,
            outputDirectory / "07_frameless_widget_dark.png",
            application,
            isDarkTheme=True,
            cornerRadius=cornerRadius,
            targetWidth=targetWidth,
            targetHeight=targetHeight,
        )
    )
    widgetWindow.close()
    application.processEvents()

    # 8: Frameless Dialog Window (Light)
    dialogWindow = DialogWindow()
    if dialogWindow.darkTheme:
        dialogWindow._toggleTheme()
    capturedPaths.append(
        captureWindow(
            dialogWindow,
            outputDirectory / "08_dialog_window_light.png",
            application,
            isDarkTheme=False,
            cornerRadius=cornerRadius,
            targetWidth=targetWidth,
            targetHeight=targetHeight,
        )
    )
    dialogWindow.close()
    application.processEvents()

    # 9: DPI Scaling Demo (Dark)
    dpiScalingWindow = DpiScalingDemoWindow()
    capturedPaths.append(
        captureWindow(
            dpiScalingWindow,
            outputDirectory / "09_dpi_scaling_demo.png",
            application,
            isDarkTheme=True,
            cornerRadius=cornerRadius,
            targetWidth=targetWidth,
            targetHeight=targetHeight,
        )
    )
    dpiScalingWindow.close()
    application.processEvents()

    return capturedPaths


def assembleShowcaseGif(
    imagePaths: Sequence[Path],
    outputGifPath: Path,
    frameDurationMilliseconds: int = 1500,
    loopCount: int = 0,
) -> Path:
    """Assemble a sequence of PNG images into an animated GIF with transparent corners.

    Converts each frame to a 256-color adaptive palette with transparent outer corners
    and disposal=2 so frames do not bleed into each other.

    Parameters
    ----------
    imagePaths : sequence of Path
        Ordered paths of source PNG images to include in the animated GIF.
    outputGifPath : Path
        Destination path where the animated GIF will be written.
    frameDurationMilliseconds : int, default 1500
        Display duration for each frame in milliseconds.
    loopCount : int, default 0
        Number of loops (0 indicates infinite looping).

    Returns
    -------
    Path
        Path to the generated animated GIF file.

    Raises
    ------
    ValueError
        If imagePaths is empty.
    """
    if not imagePaths:
        raise ValueError("Cannot assemble GIF from empty image sequence.")

    convertedFrames: list[Image.Image] = []
    for imagePath in imagePaths:
        with Image.open(imagePath) as sourceImage:
            rgbaImage = sourceImage.convert("RGBA")
            alphaChannel = rgbaImage.split()[-1]
            rgbImage = rgbaImage.convert("RGB")

            # 255 adaptive colors, reserving index 255 for transparency
            pFrame = rgbImage.convert(
                "P",
                palette=Image.Palette.ADAPTIVE,
                colors=255,
                dither=Image.Dither.NONE,
            )

            # Map fully transparent pixels (alpha == 0) to index 255
            transparentMask = Image.eval(alphaChannel, lambda a: 255 if a == 0 else 0)
            pFrame.paste(255, transparentMask)
            pFrame.info["transparency"] = 255
            convertedFrames.append(pFrame)

    outputGifPath.parent.mkdir(parents=True, exist_ok=True)
    convertedFrames[0].save(
        outputGifPath,
        save_all=True,
        append_images=convertedFrames[1:],
        duration=frameDurationMilliseconds,
        loop=loopCount,
        transparency=255,
        disposal=2,
        optimize=False,
    )
    return outputGifPath


def generateShowcase(
    targetOs: str = "auto",
    frameDurationMilliseconds: int = 1500,
) -> None:
    """Orchestrate screenshot capture, GIF assembly, and docs synchronization.

    Parameters
    ----------
    targetOs : str, default "auto"
        Target OS flavor: ``"auto"`` (auto-detect), ``"win11"``, or ``"win10"``.
    frameDurationMilliseconds : int, default 1500
        Display duration for each frame in milliseconds.
    """
    if targetOs == "auto":
        targetOs = detectWindowsVersion()

    isWindows11 = targetOs == "win11"
    cornerRadius = 12 if isWindows11 else 0
    osSubdirName = "windows_11" if isWindows11 else "windows_10"
    gifFileName = "windows11_showcase.gif" if isWindows11 else "windows10_showcase.gif"

    repositoryRoot = Path(__file__).resolve().parent.parent
    screenshotDirectory = repositoryRoot / "screenshot" / osSubdirName
    docsImagesDirectory = repositoryRoot / "docs" / "images"

    application = QApplication.instance()
    if application is None:
        application = QApplication(sys.argv)

    # Clean up obsolete screenshot files if present
    for obsoleteFileName in ["07_dpi_scaling_demo.png", "08_dialog_window.png"]:
        (screenshotDirectory / obsoleteFileName).unlink(missing_ok=True)

    print(f"Target OS: {targetOs.upper()} (Corner radius: {cornerRadius}px)")
    print(f"Capturing showcase window screenshots into {screenshotDirectory}...")
    capturedImages = captureAllScreenshots(
        screenshotDirectory,
        application,
        cornerRadius=cornerRadius,
    )
    print(f"Captured {len(capturedImages)} screenshots.")

    targetGifPath = screenshotDirectory / gifFileName
    print(f"Assembling animated GIF showcase: {targetGifPath}")
    assembleShowcaseGif(
        capturedImages,
        targetGifPath,
        frameDurationMilliseconds=frameDurationMilliseconds,
        loopCount=0,
    )

    docsImagesDirectory.mkdir(parents=True, exist_ok=True)
    docsGifPath = docsImagesDirectory / gifFileName
    shutil.copy2(targetGifPath, docsGifPath)
    print(f"Showcase GIF successfully copied to {docsGifPath}")


def main() -> int:
    """Run the automated screenshot showcase generation CLI.

    Returns
    -------
    int
        Exit code (0 for success).
    """
    parser = argparse.ArgumentParser(
        description="Generate qtframelesskit window screenshots and showcase GIF."
    )
    parser.add_argument(
        "--os",
        choices=["auto", "win11", "win10"],
        default="auto",
        help="Target OS styling: auto (detect), win11 (rounded corners), or win10 (square corners).",
    )
    args = parser.parse_args()
    generateShowcase(targetOs=args.os)
    return 0


if __name__ == "__main__":
    sys.exit(main())
