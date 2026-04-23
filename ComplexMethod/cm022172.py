async def test_async_handle_source_entity_changes_source_entity_removed(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    trend_config_entry: MockConfigEntry,
    sensor_config_entry: ConfigEntry,
    sensor_device: dr.DeviceEntry,
    sensor_entity_entry: er.RegistryEntry,
) -> None:
    """Test the trend config entry is removed when the source entity is removed."""
    assert await hass.config_entries.async_setup(trend_config_entry.entry_id)
    await hass.async_block_till_done()

    trend_entity_entry = entity_registry.async_get("binary_sensor.my_trend")
    assert trend_entity_entry.device_id == sensor_entity_entry.device_id

    sensor_device = device_registry.async_get(sensor_device.id)
    assert trend_config_entry.entry_id not in sensor_device.config_entries

    events = track_entity_registry_actions(hass, trend_entity_entry.entity_id)

    # Remove the source sensor's config entry from the device, this removes the
    # source sensor
    with patch(
        "homeassistant.components.trend.async_unload_entry",
        wraps=trend.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            sensor_device.id, remove_config_entry_id=sensor_config_entry.entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    # Check that the helper entity is removed
    assert not entity_registry.async_get("binary_sensor.my_trend")

    # Check that the device is removed
    assert not device_registry.async_get(sensor_device.id)

    # Check that the trend config entry is removed
    assert trend_config_entry.entry_id not in hass.config_entries.async_entry_ids()

    # Check we got the expected events
    assert events == ["remove"]