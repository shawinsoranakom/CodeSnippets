async def test_async_handle_source_entity_new_entity_id(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    integration_config_entry: MockConfigEntry,
    sensor_device: dr.DeviceEntry,
    sensor_entity_entry: er.RegistryEntry,
) -> None:
    """Test the source entity's entity ID is changed."""
    assert await hass.config_entries.async_setup(integration_config_entry.entry_id)
    await hass.async_block_till_done()

    integration_entity_entry = entity_registry.async_get("sensor.my_integration")
    assert integration_entity_entry.device_id == sensor_entity_entry.device_id

    sensor_device = device_registry.async_get(sensor_device.id)
    assert integration_config_entry.entry_id not in sensor_device.config_entries

    events = track_entity_registry_actions(hass, integration_entity_entry.entity_id)

    # Change the source entity's entity ID
    with patch(
        "homeassistant.components.integration.async_unload_entry",
        wraps=integration.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, new_entity_id="sensor.new_entity_id"
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    # Check that the integration config entry is updated with the new entity ID
    assert integration_config_entry.options["source"] == "sensor.new_entity_id"

    # Check that the helper config is not in the device
    sensor_device = device_registry.async_get(sensor_device.id)
    assert integration_config_entry.entry_id not in sensor_device.config_entries

    # Check that the integration config entry is not removed
    assert integration_config_entry.entry_id in hass.config_entries.async_entry_ids()

    # Check we got the expected events
    assert events == []