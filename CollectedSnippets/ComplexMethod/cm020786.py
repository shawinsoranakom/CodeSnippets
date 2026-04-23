async def test_async_handle_source_entity_new_entity_id(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mold_indicator_config_entry: MockConfigEntry,
    indoor_humidity_entity_entry: er.RegistryEntry,
    source_entity_id: str,
    config_key: str,
) -> None:
    """Test the source entity's entity ID is changed."""
    source_entity_entry = entity_registry.async_get(source_entity_id)

    assert await hass.config_entries.async_setup(mold_indicator_config_entry.entry_id)
    await hass.async_block_till_done()

    mold_indicator_entity_entry = entity_registry.async_get("sensor.my_mold_indicator")
    assert (
        mold_indicator_entity_entry.device_id == indoor_humidity_entity_entry.device_id
    )

    source_device = device_registry.async_get(source_entity_entry.device_id)
    assert mold_indicator_config_entry.entry_id not in source_device.config_entries

    events = track_entity_registry_actions(hass, mold_indicator_entity_entry.entity_id)

    # Change the source entity's entity ID
    with patch(
        "homeassistant.components.mold_indicator.async_unload_entry",
        wraps=mold_indicator.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            source_entity_entry.entity_id, new_entity_id="sensor.new_entity_id"
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    # Check that the mold_indicator config entry is updated with the new entity ID
    assert mold_indicator_config_entry.options[config_key] == "sensor.new_entity_id"

    # Check that the helper config is not in the device
    source_device = device_registry.async_get(source_device.id)
    assert mold_indicator_config_entry.entry_id not in source_device.config_entries

    # Check that the mold_indicator config entry is not removed
    assert mold_indicator_config_entry.entry_id in hass.config_entries.async_entry_ids()

    # Check we got the expected events
    assert events == []