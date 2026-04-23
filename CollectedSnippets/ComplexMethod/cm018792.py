async def test_async_handle_source_entity_changes_source_entity_removed_from_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    statistics_config_entry: MockConfigEntry,
    sensor_device: dr.DeviceEntry,
    sensor_entity_entry: er.RegistryEntry,
) -> None:
    """Test the source entity removed from the source device."""
    assert await hass.config_entries.async_setup(statistics_config_entry.entry_id)
    await hass.async_block_till_done()

    statistics_entity_entry = entity_registry.async_get("sensor.my_statistics")
    assert statistics_entity_entry.device_id == sensor_entity_entry.device_id

    sensor_device = device_registry.async_get(sensor_device.id)
    assert statistics_config_entry.entry_id not in sensor_device.config_entries

    events = track_entity_registry_actions(hass, statistics_entity_entry.entity_id)

    # Remove the source sensor from the device
    with patch(
        "homeassistant.components.statistics.async_unload_entry",
        wraps=statistics.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=None
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    # Check that the entity is no longer linked to the source device
    statistics_entity_entry = entity_registry.async_get("sensor.my_statistics")
    assert statistics_entity_entry.device_id is None

    # Check that the statistics config entry is not in the device
    sensor_device = device_registry.async_get(sensor_device.id)
    assert statistics_config_entry.entry_id not in sensor_device.config_entries

    # Check that the statistics config entry is not removed
    assert statistics_config_entry.entry_id in hass.config_entries.async_entry_ids()

    # Check we got the expected events
    assert events == ["update"]