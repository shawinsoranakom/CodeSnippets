async def test_fix_duplicate_device_ids(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
    entry1_updates: dict[str, Any],
    entry2_updates: dict[str, Any],
    expected_device_name: str | None,
    expected_disabled_by: dr.DeviceEntryDisabler | None,
) -> None:
    """Test fixing duplicate device ids."""

    entry1 = device_registry.async_get_or_create(
        identifiers={(DOMAIN, str(SERIAL_NUMBER))},
        config_entry_id=config_entry.entry_id,
        serial_number=config_entry.data["serial_number"],
    )
    device_registry.async_update_device(entry1.id, **entry1_updates)

    entry2 = device_registry.async_get_or_create(
        identifiers={(DOMAIN, MAC_ADDRESS_UNIQUE_ID)},
        config_entry_id=config_entry.entry_id,
        serial_number=config_entry.data["serial_number"],
    )
    device_registry.async_update_device(entry2.id, **entry2_updates)

    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )
    assert len(device_entries) == 2

    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.LOADED

    # Only the device with the new format exists
    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )
    assert len(device_entries) == 1

    device_entry = device_registry.async_get_device({(DOMAIN, MAC_ADDRESS_UNIQUE_ID)})
    assert device_entry
    assert device_entry.identifiers == {(DOMAIN, MAC_ADDRESS_UNIQUE_ID)}
    assert device_entry.name_by_user == expected_device_name
    assert device_entry.disabled_by == expected_disabled_by