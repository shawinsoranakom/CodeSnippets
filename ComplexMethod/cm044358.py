def test_system_properties(system_instance: System) -> None:
    """ Test :class:`lib.system.System` properties """
    assert hasattr(system_instance, "is_linux")
    assert isinstance(system_instance.is_linux, bool)
    if platform.system().lower() == "linux":
        assert system_instance.is_linux
        assert not system_instance.is_macos
        assert not system_instance.is_windows

    assert hasattr(system_instance, "is_macos")
    assert isinstance(system_instance.is_macos, bool)
    if platform.system().lower() == "darwin":
        assert system_instance.is_macos
        assert not system_instance.is_linux
        assert not system_instance.is_windows

    assert hasattr(system_instance, "is_windows")
    assert isinstance(system_instance.is_windows, bool)
    if platform.system().lower() == "windows":
        assert system_instance.is_windows
        assert not system_instance.is_linux
        assert not system_instance.is_macos