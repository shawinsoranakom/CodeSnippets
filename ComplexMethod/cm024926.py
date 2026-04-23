async def test_async_handle_source_entity_new_entity_id(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    helper_config_entry: MockConfigEntry,
    helper_entity_entry: er.RegistryEntry,
    source_device: dr.DeviceEntry,
    source_entity_entry: er.RegistryEntry,
    async_remove_entry: AsyncMock,
    async_unload_entry: AsyncMock,
    set_source_entity_id_or_uuid: Mock,
    unload_calls: int,
    set_source_entity_id_calls: int,
) -> None:
    """Test the source entity's entity ID is changed."""
    # Add the helper config entry to the source device
    device_registry.async_update_device(
        source_device.id, add_config_entry_id=helper_config_entry.entry_id
    )

    assert await hass.config_entries.async_setup(helper_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check preconditions
    helper_entity_entry = entity_registry.async_get(helper_entity_entry.entity_id)
    assert helper_entity_entry.device_id == source_entity_entry.device_id

    source_device = device_registry.async_get(source_device.id)
    assert helper_config_entry.entry_id in source_device.config_entries

    events = track_entity_registry_actions(hass, helper_entity_entry.entity_id)

    # Change the source entity's entity ID
    entity_registry.async_update_entity(
        source_entity_entry.entity_id, new_entity_id="sensor.new_entity_id"
    )
    await hass.async_block_till_done()
    async_remove_entry.assert_not_called()
    assert len(async_unload_entry.mock_calls) == unload_calls
    assert len(set_source_entity_id_or_uuid.mock_calls) == set_source_entity_id_calls

    # Check that the helper config is still in the device
    source_device = device_registry.async_get(source_device.id)
    assert helper_config_entry.entry_id in source_device.config_entries

    # Check that the helper config entry is not removed
    assert helper_config_entry.entry_id in hass.config_entries.async_entry_ids()

    # Check we got the expected events
    assert events == []