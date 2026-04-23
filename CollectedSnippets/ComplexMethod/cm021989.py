async def test_dynamic_and_stale_devices(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_opower_api: AsyncMock,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the dynamic addition and removal of Opower devices."""
    original_accounts = mock_opower_api.async_get_accounts.return_value
    original_forecasts = mock_opower_api.async_get_forecast.return_value

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    devices = dr.async_entries_for_config_entry(
        device_registry, mock_config_entry.entry_id
    )
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    initial_device_ids = {device.id for device in devices}
    initial_entity_ids = {entity.entity_id for entity in entities}
    # Ensure we actually created some devices and entities for this entry
    assert initial_device_ids
    assert initial_entity_ids

    # Remove the second account and update data
    mock_opower_api.async_get_accounts.return_value = [original_accounts[0]]
    mock_opower_api.async_get_forecast.return_value = [original_forecasts[0]]

    coordinator = mock_config_entry.runtime_data
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    devices = dr.async_entries_for_config_entry(
        device_registry, mock_config_entry.entry_id
    )
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    device_ids_after_removal = {device.id for device in devices}
    entity_ids_after_removal = {entity.entity_id for entity in entities}
    # After removing one account, we should have removed some devices/entities
    # but not added any new ones.
    assert device_ids_after_removal <= initial_device_ids
    assert entity_ids_after_removal <= initial_entity_ids
    assert device_ids_after_removal != initial_device_ids
    assert entity_ids_after_removal != initial_entity_ids

    # Add back the second account
    mock_opower_api.async_get_accounts.return_value = original_accounts
    mock_opower_api.async_get_forecast.return_value = original_forecasts

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    devices = dr.async_entries_for_config_entry(
        device_registry, mock_config_entry.entry_id
    )
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    device_ids_after_restore = {device.id for device in devices}
    entity_ids_after_restore = {entity.entity_id for entity in entities}
    # After restoring the second account, we should be back to the original
    # number of devices and entities (IDs themselves may change on re-create).
    assert len(device_ids_after_restore) == len(initial_device_ids)
    assert len(entity_ids_after_restore) == len(initial_entity_ids)