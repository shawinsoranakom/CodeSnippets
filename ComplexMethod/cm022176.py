async def test_async_handle_source_entity_new_entity_id(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    trend_config_entry: MockConfigEntry,
    sensor_device: dr.DeviceEntry,
    sensor_entity_entry: er.RegistryEntry,
) -> None:
    """Test the source entity's entity ID is changed."""
    assert await hass.config_entries.async_setup(trend_config_entry.entry_id)
    await hass.async_block_till_done()

    trend_entity_entry = entity_registry.async_get("binary_sensor.my_trend")
    assert trend_entity_entry.device_id == sensor_entity_entry.device_id

    sensor_device = device_registry.async_get(sensor_device.id)
    assert trend_config_entry.entry_id not in sensor_device.config_entries

    events = track_entity_registry_actions(hass, trend_entity_entry.entity_id)

    # Change the source entity's entity ID
    with patch(
        "homeassistant.components.trend.async_unload_entry",
        wraps=trend.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, new_entity_id="sensor.new_entity_id"
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    # Check that the trend config entry is updated with the new entity ID
    assert trend_config_entry.options["entity_id"] == "sensor.new_entity_id"

    # Check that the helper config is not in the device
    sensor_device = device_registry.async_get(sensor_device.id)
    assert trend_config_entry.entry_id not in sensor_device.config_entries

    # Check that the trend config entry is not removed
    assert trend_config_entry.entry_id in hass.config_entries.async_entry_ids()

    # Check we got the expected events
    assert events == []