async def test_zeo_device_fails_setup(
    hass: HomeAssistant,
    mock_roborock_entry: MockConfigEntry,
    device_registry: DeviceRegistry,
    entity_registry: EntityRegistry,
    fake_devices: list[FakeDevice],
) -> None:
    """Simulate an error while setting up a zeo device."""
    # We have a single zeo device in the test setup. Find it then set it to fail.
    zeo_device = next(
        (device for device in fake_devices if device.zeo is not None),
        None,
    )
    assert zeo_device is not None
    zeo_device.zeo.query_values.side_effect = RoborockException("Simulated Zeo failure")

    await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
    assert mock_roborock_entry.state is ConfigEntryState.LOADED

    # The Zeo device should be in the registry but have no entities
    # because its coordinator failed to set up.
    zeo_device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, zeo_device.duid)}
    )
    assert zeo_device_entry is not None
    zeo_entities = er.async_entries_for_device(
        entity_registry, zeo_device_entry.id, include_disabled_entities=True
    )
    assert len(zeo_entities) == 0

    # Other devices should have entities.
    all_entities = er.async_entries_for_config_entry(
        entity_registry, mock_roborock_entry.entry_id
    )
    devices_with_entities = {
        device_registry.async_get(entity.device_id).name
        for entity in all_entities
        if entity.device_id is not None
    }
    assert devices_with_entities == {
        "Roborock S7 MaxV",
        "Roborock S7 MaxV Dock",
        "Roborock S7 2",
        "Roborock S7 2 Dock",
        "Dyad Pro",
        "Roborock Q7",
        "Roborock Q10 S5+",
        # Zeo device is missing
    }