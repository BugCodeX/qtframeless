"""Custom exceptions for the qtframeless framework."""


class PlatformNotSupportedError(Exception):
    """Exception raised when qtframeless is used on an unsupported platform.

    Only Windows (win32) is supported because the framework relies on native
    Windows DWM and Win32 event filtering APIs.
    """
