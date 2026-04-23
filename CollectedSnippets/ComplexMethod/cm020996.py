async def test_update_device_identifiers(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test being able to update device identifiers."""
    device_entry = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, "measure-id", "L1234")},
    )

    entries = dr.async_entries_for_config_entry(
        device_registry, mock_config_entry.entry_id
    )
    assert len(entries) == 1
    device_entry = entries[0]
    assert (DOMAIN, "measure-id", "L1234") in device_entry.identifiers
    assert (DOMAIN, "L1234") not in device_entry.identifiers

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.LOADED
    await hass.async_block_till_done()

    entries = dr.async_entries_for_config_entry(
        device_registry, mock_config_entry.entry_id
    )
    assert len(entries) == 1
    device_entry = entries[0]
    assert (DOMAIN, "measure-id", "L1234") not in device_entry.identifiers
    assert (DOMAIN, "L1234") in device_entry.identifiers