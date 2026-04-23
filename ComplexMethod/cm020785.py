async def test_async_handle_source_entity_changes_source_entity_moved_other_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mold_indicator_config_entry: MockConfigEntry,
    indoor_humidity_entity_entry: er.RegistryEntry,
    source_entity_id: str,
    unload_entry_calls: int,
    expected_events: list[str],
) -> None:
    """Test the source entity is moved to another device."""
    source_entity_entry = entity_registry.async_get(source_entity_id)

    source_device_2 = device_registry.async_get_or_create(
        config_entry_id=source_entity_entry.config_entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:FF")},
    )

    assert await hass.config_entries.async_setup(mold_indicator_config_entry.entry_id)
    await hass.async_block_till_done()

    mold_indicator_entity_entry = entity_registry.async_get("sensor.my_mold_indicator")
    assert (
        mold_indicator_entity_entry.device_id == indoor_humidity_entity_entry.device_id
    )

    source_device = device_registry.async_get(source_entity_entry.device_id)
    assert mold_indicator_config_entry.entry_id not in source_device.config_entries
    source_device_2 = device_registry.async_get(source_device_2.id)
    assert mold_indicator_config_entry.entry_id not in source_device_2.config_entries

    events = track_entity_registry_actions(hass, mold_indicator_entity_entry.entity_id)

    # Move the source entity to another device
    with patch(
        "homeassistant.components.mold_indicator.async_unload_entry",
        wraps=mold_indicator.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            source_entity_entry.entity_id, device_id=source_device_2.id
        )
        await hass.async_block_till_done()
    assert len(mock_unload_entry.mock_calls) == unload_entry_calls

    # Check that the helper entity is linked to the expected source device
    indoor_humidity_entity_entry = entity_registry.async_get(
        indoor_humidity_entity_entry.entity_id
    )
    mold_indicator_entity_entry = entity_registry.async_get("sensor.my_mold_indicator")
    assert (
        mold_indicator_entity_entry.device_id == indoor_humidity_entity_entry.device_id
    )

    # Check that the mold_indicator config entry is not in any of the devices
    source_device = device_registry.async_get(source_device.id)
    assert mold_indicator_config_entry.entry_id not in source_device.config_entries
    source_device_2 = device_registry.async_get(source_device_2.id)
    assert mold_indicator_config_entry.entry_id not in source_device_2.config_entries

    # Check that the mold_indicator config entry is not removed
    assert mold_indicator_config_entry.entry_id in hass.config_entries.async_entry_ids()

    # Check we got the expected events
    assert events == expected_events