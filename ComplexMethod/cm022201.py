async def device_source_mock(
    hass: HomeAssistant,
    config_entry_mock: MockConfigEntry,
    ssdp_scanner_mock: Mock,
    dms_device_mock: Mock,
) -> AsyncGenerator[None]:
    """Fixture to set up a DmsDeviceSource in a connected state and cleanup at completion."""
    config_entry_mock.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry_mock.entry_id)
    await hass.async_block_till_done()

    # Check the DmsDeviceSource has registered all needed listeners
    assert len(config_entry_mock.update_listeners) == 0
    assert ssdp_scanner_mock.async_register_callback.await_count == 2
    assert ssdp_scanner_mock.async_register_callback.return_value.call_count == 0

    # Run the test
    yield None

    # Unload config entry to clean up
    assert await hass.config_entries.async_remove(config_entry_mock.entry_id) == {
        "require_restart": False
    }

    # Check DmsDeviceSource has cleaned up its resources
    assert not config_entry_mock.update_listeners
    assert (
        ssdp_scanner_mock.async_register_callback.await_count
        == ssdp_scanner_mock.async_register_callback.return_value.call_count
    )

    domain_data = cast(DlnaDmsData, hass.data[DOMAIN])
    assert MOCK_DEVICE_USN not in domain_data.devices
    assert MOCK_SOURCE_ID not in domain_data.sources