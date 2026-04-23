async def test_async_handle_source_entity_changes_source_entity_moved_other_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    helper_config_entry: MockConfigEntry,
    helper_entity_entry: er.RegistryEntry,
    source_config_entry: ConfigEntry,
    source_device: dr.DeviceEntry,
    source_entity_entry: er.RegistryEntry,
    async_remove_entry: AsyncMock,
    async_unload_entry: AsyncMock,
    set_source_entity_id_or_uuid: Mock,
) -> None:
    """Test the source entity is moved to another device."""
    # Add the helper config entry to the source device
    device_registry.async_update_device(
        source_device.id, add_config_entry_id=helper_config_entry.entry_id
    )

    # Create another device to move the source entity to
    source_device_2 = device_registry.async_get_or_create(
        config_entry_id=source_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:FF")},
    )

    assert await hass.config_entries.async_setup(helper_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check preconditions
    helper_entity_entry = entity_registry.async_get(helper_entity_entry.entity_id)
    assert helper_entity_entry.device_id == source_entity_entry.device_id

    source_device = device_registry.async_get(source_device.id)
    assert helper_config_entry.entry_id in source_device.config_entries
    source_device_2 = device_registry.async_get(source_device_2.id)
    assert helper_config_entry.entry_id not in source_device_2.config_entries

    events = track_entity_registry_actions(hass, helper_entity_entry.entity_id)

    # Move the source entity to another device
    entity_registry.async_update_entity(
        source_entity_entry.entity_id, device_id=source_device_2.id
    )
    await hass.async_block_till_done()
    async_remove_entry.assert_not_called()
    async_unload_entry.assert_called_once()
    set_source_entity_id_or_uuid.assert_not_called()

    # Check that the helper config entry is moved to the other device
    source_device = device_registry.async_get(source_device.id)
    assert helper_config_entry.entry_id not in source_device.config_entries
    source_device_2 = device_registry.async_get(source_device_2.id)
    assert helper_config_entry.entry_id in source_device_2.config_entries

    # Check that the helper config entry is not removed
    assert helper_config_entry.entry_id in hass.config_entries.async_entry_ids()

    # Check we got the expected events
    assert events == ["update"]