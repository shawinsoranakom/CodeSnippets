async def test_async_handle_source_entity_changes_source_entity_moved_other_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    trend_config_entry: MockConfigEntry,
    sensor_config_entry: ConfigEntry,
    sensor_device: dr.DeviceEntry,
    sensor_entity_entry: er.RegistryEntry,
) -> None:
    """Test the source entity is moved to another device."""
    sensor_device_2 = device_registry.async_get_or_create(
        config_entry_id=sensor_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:FF")},
    )

    assert await hass.config_entries.async_setup(trend_config_entry.entry_id)
    await hass.async_block_till_done()

    trend_entity_entry = entity_registry.async_get("binary_sensor.my_trend")
    assert trend_entity_entry.device_id == sensor_entity_entry.device_id

    sensor_device = device_registry.async_get(sensor_device.id)
    assert trend_config_entry.entry_id not in sensor_device.config_entries
    sensor_device_2 = device_registry.async_get(sensor_device_2.id)
    assert trend_config_entry.entry_id not in sensor_device_2.config_entries

    events = track_entity_registry_actions(hass, trend_entity_entry.entity_id)

    # Move the source sensor to another device
    with patch(
        "homeassistant.components.trend.async_unload_entry",
        wraps=trend.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=sensor_device_2.id
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    # Check that the entity is linked to the other device
    trend_entity_entry = entity_registry.async_get("binary_sensor.my_trend")
    assert trend_entity_entry.device_id == sensor_device_2.id

    # Check that the trend config entry is not in any of the devices
    sensor_device = device_registry.async_get(sensor_device.id)
    assert trend_config_entry.entry_id not in sensor_device.config_entries
    sensor_device_2 = device_registry.async_get(sensor_device_2.id)
    assert trend_config_entry.entry_id not in sensor_device_2.config_entries

    # Check that the trend config entry is not removed
    assert trend_config_entry.entry_id in hass.config_entries.async_entry_ids()

    # Check we got the expected events
    assert events == ["update"]