async def test_async_handle_source_entity_changes_source_entity_removed(
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
    """Test the helper config entry is removed when the source entity is removed."""
    # Add the helper config entry to the source device
    device_registry.async_update_device(
        source_device.id, add_config_entry_id=helper_config_entry.entry_id
    )
    # Add another config entry to the source device
    other_config_entry = MockConfigEntry()
    other_config_entry.add_to_hass(hass)
    device_registry.async_update_device(
        source_device.id, add_config_entry_id=other_config_entry.entry_id
    )

    assert await hass.config_entries.async_setup(helper_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check preconditions
    helper_entity_entry = entity_registry.async_get(helper_entity_entry.entity_id)
    assert helper_entity_entry.device_id == source_entity_entry.device_id
    source_device = device_registry.async_get(source_device.id)
    assert helper_config_entry.entry_id in source_device.config_entries

    events = track_entity_registry_actions(hass, helper_entity_entry.entity_id)

    # Remove the source entitys's config entry from the device, this removes the
    # source entity
    device_registry.async_update_device(
        source_device.id, remove_config_entry_id=source_config_entry.entry_id
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # Check that the helper entity is not linked to the source device anymore
    helper_entity_entry = entity_registry.async_get(helper_entity_entry.entity_id)
    assert helper_entity_entry.device_id is None
    async_unload_entry.assert_not_called()
    async_remove_entry.assert_not_called()
    set_source_entity_id_or_uuid.assert_not_called()

    # Check that the helper config entry is not removed from the device
    source_device = device_registry.async_get(source_device.id)
    assert helper_config_entry.entry_id in source_device.config_entries

    # Check that the helper config entry is not removed
    assert helper_config_entry.entry_id in hass.config_entries.async_entry_ids()

    # Check we got the expected events
    assert events == ["update"]