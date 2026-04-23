async def test_async_handle_source_entity_changes_source_entity_removed_from_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    utility_meter_config_entry: MockConfigEntry,
    sensor_device: dr.DeviceEntry,
    sensor_entity_entry: er.RegistryEntry,
    expected_entities: set[str],
) -> None:
    """Test the source entity removed from the source device."""
    assert await hass.config_entries.async_setup(utility_meter_config_entry.entry_id)
    await hass.async_block_till_done()

    events = {}
    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        assert utility_meter_entity.device_id == sensor_entity_entry.device_id
        events[utility_meter_entity.entity_id] = track_entity_registry_actions(
            hass, utility_meter_entity.entity_id
        )
    assert set(events) == expected_entities

    sensor_device = device_registry.async_get(sensor_device.id)
    assert utility_meter_config_entry.entry_id not in sensor_device.config_entries

    # Remove the source sensor from the device
    with patch(
        "homeassistant.components.utility_meter.async_unload_entry",
        wraps=utility_meter.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=None
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    # Check that the entities are no longer linked to the source device
    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        assert utility_meter_entity.device_id is None

    # Check that the utility_meter config entry is not in the device
    sensor_device = device_registry.async_get(sensor_device.id)
    assert utility_meter_config_entry.entry_id not in sensor_device.config_entries

    # Check that the utility_meter config entry is not removed
    assert utility_meter_config_entry.entry_id in hass.config_entries.async_entry_ids()

    # Check we got the expected events
    for entity_events in events.values():
        assert entity_events == ["update"]