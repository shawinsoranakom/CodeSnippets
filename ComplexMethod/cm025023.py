async def test_disable_config_entry_disables_devices(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test that we disable entities tied to a config entry."""
    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to_hass(hass)

    entry1 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry2 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "34:56:AB:CD:EF:12")},
        disabled_by=dr.DeviceEntryDisabler.USER,
    )

    assert not entry1.disabled
    assert entry2.disabled

    await hass.config_entries.async_set_disabled_by(
        config_entry.entry_id, config_entries.ConfigEntryDisabler.USER
    )
    await hass.async_block_till_done()

    entry1 = device_registry.async_get(entry1.id)
    assert entry1.disabled
    assert entry1.disabled_by is dr.DeviceEntryDisabler.CONFIG_ENTRY
    entry2 = device_registry.async_get(entry2.id)
    assert entry2.disabled
    assert entry2.disabled_by is dr.DeviceEntryDisabler.USER

    await hass.config_entries.async_set_disabled_by(config_entry.entry_id, None)
    await hass.async_block_till_done()

    entry1 = device_registry.async_get(entry1.id)
    assert not entry1.disabled
    entry2 = device_registry.async_get(entry2.id)
    assert entry2.disabled
    assert entry2.disabled_by is dr.DeviceEntryDisabler.USER