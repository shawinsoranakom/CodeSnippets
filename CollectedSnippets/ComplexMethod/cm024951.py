async def test_disable_device_disables_entities(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that we disable entities tied to a device."""
    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to_hass(hass)

    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )

    entry1 = entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry,
        device_id=device_entry.id,
    )
    entry2 = entity_registry.async_get_or_create(
        "light",
        "hue",
        "ABCD",
        config_entry=config_entry,
        device_id=device_entry.id,
        disabled_by=er.RegistryEntryDisabler.USER,
    )
    entry3 = entity_registry.async_get_or_create(
        "light",
        "hue",
        "EFGH",
        config_entry=config_entry,
        device_id=device_entry.id,
        disabled_by=er.RegistryEntryDisabler.CONFIG_ENTRY,
    )

    assert not entry1.disabled
    assert entry2.disabled
    assert entry3.disabled

    device_registry.async_update_device(
        device_entry.id, disabled_by=dr.DeviceEntryDisabler.USER
    )
    await hass.async_block_till_done()

    entry1 = entity_registry.async_get(entry1.entity_id)
    assert entry1.disabled
    assert entry1.disabled_by is er.RegistryEntryDisabler.DEVICE
    entry2 = entity_registry.async_get(entry2.entity_id)
    assert entry2.disabled
    assert entry2.disabled_by is er.RegistryEntryDisabler.USER
    entry3 = entity_registry.async_get(entry3.entity_id)
    assert entry3.disabled
    assert entry3.disabled_by is er.RegistryEntryDisabler.CONFIG_ENTRY

    device_registry.async_update_device(device_entry.id, disabled_by=None)
    await hass.async_block_till_done()

    entry1 = entity_registry.async_get(entry1.entity_id)
    assert not entry1.disabled
    entry2 = entity_registry.async_get(entry2.entity_id)
    assert entry2.disabled
    assert entry2.disabled_by is er.RegistryEntryDisabler.USER
    entry3 = entity_registry.async_get(entry3.entity_id)
    assert entry3.disabled
    assert entry3.disabled_by is er.RegistryEntryDisabler.CONFIG_ENTRY