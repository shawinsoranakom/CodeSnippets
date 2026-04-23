async def test_async_handle_source_entity_changes_source_entity_removed(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    statistics_config_entry: MockConfigEntry,
    sensor_config_entry: ConfigEntry,
    sensor_device: dr.DeviceEntry,
    sensor_entity_entry: er.RegistryEntry,
) -> None:
    """Test the statistics config entry is removed when the source entity is removed."""
    assert await hass.config_entries.async_setup(statistics_config_entry.entry_id)
    await hass.async_block_till_done()

    statistics_entity_entry = entity_registry.async_get("sensor.my_statistics")
    assert statistics_entity_entry.device_id == sensor_entity_entry.device_id

    sensor_device = device_registry.async_get(sensor_device.id)
    assert statistics_config_entry.entry_id not in sensor_device.config_entries

    events = track_entity_registry_actions(hass, statistics_entity_entry.entity_id)

    # Remove the source sensor's config entry from the device, this removes the
    # source sensor
    with patch(
        "homeassistant.components.statistics.async_unload_entry",
        wraps=statistics.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            sensor_device.id, remove_config_entry_id=sensor_config_entry.entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    # Check that the helper entity is removed
    assert not entity_registry.async_get("sensor.my_statistics")

    # Check that the device is removed
    assert not device_registry.async_get(sensor_device.id)

    # Check that the statistics config entry is removed
    assert statistics_config_entry.entry_id not in hass.config_entries.async_entry_ids()

    # Check we got the expected events
    assert events == ["remove"]