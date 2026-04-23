async def test_dyad_device_fails_setup(
    hass: HomeAssistant,
    mock_roborock_entry: MockConfigEntry,
    device_registry: DeviceRegistry,
    entity_registry: EntityRegistry,
    fake_devices: list[FakeDevice],
) -> None:
    """Simulate an error while setting up a dyad device."""
    # We have a single dyad device in the test setup. Find it then set it to fail.
    dyad_device = next(
        (device for device in fake_devices if device.dyad is not None),
        None,
    )
    assert dyad_device is not None
    dyad_device.dyad.query_values.side_effect = RoborockException(
        "Simulated Dyad failure"
    )

    await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
    assert mock_roborock_entry.state is ConfigEntryState.LOADED

    # The Dyad device should be in the registry but have no entities
    # because its coordinator failed to set up.
    dyad_device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, dyad_device.duid)}
    )
    assert dyad_device_entry is not None
    dyad_entities = er.async_entries_for_device(
        entity_registry, dyad_device_entry.id, include_disabled_entities=True
    )
    assert len(dyad_entities) == 0

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
        # Dyad device is missing
        "Zeo One",
        "Roborock Q7",
        "Roborock Q10 S5+",
    }