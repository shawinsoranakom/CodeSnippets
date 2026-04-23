async def test_firmware_update_context_manager(hass: HomeAssistant) -> None:
    """Test firmware update progress context manager."""
    await async_setup_component(hass, DOMAIN, {})

    device_path = "/dev/ttyUSB0"

    # Initially no updates in progress
    assert not async_is_firmware_update_in_progress(hass, device_path)

    # Test successful completion
    async with async_firmware_update_context(hass, device_path, "zha"):
        assert async_is_firmware_update_in_progress(hass, device_path)

    # Should be cleaned up after context
    assert not async_is_firmware_update_in_progress(hass, device_path)

    # Test exception handling
    with pytest.raises(ValueError, match="test error"):  # noqa: PT012
        async with async_firmware_update_context(hass, device_path, "zha"):
            assert async_is_firmware_update_in_progress(hass, device_path)
            raise ValueError("test error")

    # Should still be cleaned up after exception
    assert not async_is_firmware_update_in_progress(hass, device_path)

    # Test concurrent context manager attempts should fail
    async with async_firmware_update_context(hass, device_path, "zha"):
        assert async_is_firmware_update_in_progress(hass, device_path)

        # Second context manager should fail to register
        with pytest.raises(ValueError, match="Firmware update already in progress"):
            async with async_firmware_update_context(hass, device_path, "skyconnect"):
                pytest.fail("We should not enter this context manager")

    # Should be cleaned up after first context
    assert not async_is_firmware_update_in_progress(hass, device_path)