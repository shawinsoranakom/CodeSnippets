async def test_multiple_config_entries(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Make sure we do not get duplicate entries."""
    config_entry_1 = MockConfigEntry()
    config_entry_1.add_to_hass(hass)
    config_entry_2 = MockConfigEntry()
    config_entry_2.add_to_hass(hass)

    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    entry2 = device_registry.async_get_or_create(
        config_entry_id=config_entry_2.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    entry3 = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )

    assert len(device_registry.devices) == 1
    assert entry.id == entry2.id
    assert entry.id == entry3.id
    assert entry2.config_entries == {config_entry_1.entry_id, config_entry_2.entry_id}
    assert entry2.primary_config_entry == config_entry_1.entry_id
    assert entry3.config_entries == {config_entry_1.entry_id, config_entry_2.entry_id}
    assert entry3.primary_config_entry == config_entry_1.entry_id