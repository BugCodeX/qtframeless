"""Tests for platform restrictions and platform-specific exceptions."""

import importlib
import sys

import pytest


def test_platform_not_supported_error_inheritance():
    """Verify that PlatformNotSupportedError inherits from Exception."""
    from qtframelesskit.exceptions import PlatformNotSupportedError

    error = PlatformNotSupportedError("Only Windows is supported.")
    assert isinstance(error, Exception)
    assert str(error) == "Only Windows is supported."


@pytest.mark.parametrize("mocked_platform", ["linux", "darwin", "freebsd", "java"])
def test_import_raises_on_non_windows(monkeypatch, mocked_platform):
    """Verify PlatformNotSupportedError is raised when imported on non-Windows OS."""
    from qtframelesskit.exceptions import PlatformNotSupportedError

    monkeypatch.setattr(sys, "platform", mocked_platform)

    # Force re-importing qtframelesskit under mocked non-Windows platform
    if "qtframelesskit" in sys.modules:
        monkeypatch.delitem(sys.modules, "qtframelesskit")

    with pytest.raises(PlatformNotSupportedError) as exc_info:
        importlib.import_module("qtframelesskit")

    assert str(exc_info.value) == "qtframelesskit only supports Windows platforms."


def test_import_succeeds_on_win32(monkeypatch):
    """Verify import succeeds without error when platform is win32."""
    monkeypatch.setattr(sys, "platform", "win32")

    if "qtframelesskit" in sys.modules:
        monkeypatch.delitem(sys.modules, "qtframelesskit")

    module = importlib.import_module("qtframelesskit")
    assert module is not None


def test_version():
    """Verify that qtframelesskit defines the expected package version."""
    import qtframelesskit

    assert qtframelesskit.__version__ == "0.2.0"
