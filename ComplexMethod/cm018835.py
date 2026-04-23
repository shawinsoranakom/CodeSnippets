async def test_device_retention_during_reload(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mock_products: AsyncMock,
) -> None:
    """Test that valid devices are retained during a config entry reload."""
    # Setup entry with normal devices
    entry = await setup_platform(hass)

    # Get initial device count and identifiers
    pre_devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    pre_count = len(pre_devices)
    pre_identifiers = {
        identifier for device in pre_devices for identifier in device.identifiers
    }

    # Make sure we have some devices
    assert pre_count > 0

    # Save the original identifiers to compare after reload
    original_identifiers = pre_identifiers.copy()

    # Reload the config entry with the same products data
    # The mock_products fixture will return the same data as during setup
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    # Verify device count and identifiers after reload match pre-reload
    post_devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    post_count = len(post_devices)
    post_identifiers = {
        identifier for device in post_devices for identifier in device.identifiers
    }

    # Since the products data didn't change, we should have the same devices
    assert post_count == pre_count
    assert post_identifiers == original_identifiers