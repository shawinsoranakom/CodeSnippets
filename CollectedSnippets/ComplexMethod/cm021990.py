async def test_stale_device_removed_on_load(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_opower_api: AsyncMock,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test that a stale device present before setup is removed on first load."""
    # Simulate a device that was created by a previous version / old account
    # and is already registered before the integration sets up.
    stale_device = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, "pge_stale_account_99999")},
    )
    assert device_registry.async_get(stale_device.id) is not None

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Stale device should have been removed on first coordinator update
    assert device_registry.async_get(stale_device.id) is None

    # Active devices for known accounts should still be present,
    # and the stale identifier should no longer be registered.
    active_devices = dr.async_entries_for_config_entry(
        device_registry, mock_config_entry.entry_id
    )
    active_identifiers = {
        identifier
        for device in active_devices
        for (_domain, identifier) in device.identifiers
    }
    assert "pge_111111" in active_identifiers
    assert "pge_222222" in active_identifiers
    assert "pge_stale_account_99999" not in active_identifiers