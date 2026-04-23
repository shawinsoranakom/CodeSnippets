async def test_stale_devices_cleanup(
    hass: HomeAssistant,
    device_registry: DeviceRegistry,
    mock_incomfort: MagicMock,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
    mock_heater_status: dict[str, Any],
) -> None:
    """Test the incomfort integration is cleaning up stale devices."""
    # Setup an old heater with serial_no c01d00c0ffee
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.LOADED
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    old_entries = device_registry.devices.get_devices_for_config_entry_id(
        mock_config_entry.entry_id
    )
    assert len(old_entries) == 3
    old_heater = device_registry.async_get_device({(DOMAIN, "c01d00c0ffee")})
    assert old_heater is not None
    assert old_heater.serial_number == "c01d00c0ffee"
    old_climate = device_registry.async_get_device({(DOMAIN, "c01d00c0ffee_1")})
    assert old_heater is not None
    old_climate = device_registry.async_get_device({(DOMAIN, "c01d00c0ffee_1")})
    assert old_climate is not None

    mock_heater_status["serial_no"] = "c0ffeec0ffee"
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.LOADED

    new_entries = device_registry.devices.get_devices_for_config_entry_id(
        mock_config_entry.entry_id
    )
    assert len(new_entries) == 3
    new_heater = device_registry.async_get_device({(DOMAIN, "c0ffeec0ffee")})
    assert new_heater is not None
    assert new_heater.serial_number == "c0ffeec0ffee"
    new_climate = device_registry.async_get_device({(DOMAIN, "c0ffeec0ffee_1")})
    assert new_climate is not None

    old_heater = device_registry.async_get_device({(DOMAIN, "c01d00c0ffee")})
    assert old_heater is None
    old_climate = device_registry.async_get_device({(DOMAIN, "c01d00c0ffee_1")})
    assert old_climate is None