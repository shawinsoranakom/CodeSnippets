async def test_coordinator_automatic_registry_cleanup(
    hass: HomeAssistant,
    mock_automower_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    values: dict[str, MowerAttributes],
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test automatic registry cleanup."""
    await setup_integration(hass, mock_config_entry)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    await hass.async_block_till_done()

    # Count current entitties and devices
    current_entites = len(
        er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    )
    current_devices = len(
        dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    )
    # Remove mower 2 and check if it worked
    values_copy = deepcopy(values)
    mower2 = values_copy.pop("1234")
    mock_automower_client.get_status.return_value = values_copy
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (
        len(er.async_entries_for_config_entry(entity_registry, entry.entry_id))
        == current_entites - NUMBER_OF_ENTITIES_MOWER_2
    )
    assert (
        len(dr.async_entries_for_config_entry(device_registry, entry.entry_id))
        == current_devices - 1
    )
    # Add mower 2 and check if it worked
    values_copy = deepcopy(values)
    values_copy["1234"] = mower2
    mock_automower_client.get_status.return_value = values_copy
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert (
        len(er.async_entries_for_config_entry(entity_registry, entry.entry_id))
        == current_entites
    )
    assert (
        len(dr.async_entries_for_config_entry(device_registry, entry.entry_id))
        == current_devices
    )

    # Remove mower 1 and check if it worked
    values_copy = deepcopy(values)
    mower1 = values_copy.pop(TEST_MOWER_ID)
    mock_automower_client.get_status.return_value = values_copy
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (
        len(er.async_entries_for_config_entry(entity_registry, entry.entry_id))
        == NUMBER_OF_ENTITIES_MOWER_2
    )
    assert (
        len(dr.async_entries_for_config_entry(device_registry, entry.entry_id))
        == current_devices - 1
    )
    # Add mower 1 and check if it worked
    values_copy = deepcopy(values)
    values_copy[TEST_MOWER_ID] = mower1
    mock_automower_client.get_status.return_value = values_copy
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert (
        len(dr.async_entries_for_config_entry(device_registry, entry.entry_id))
        == current_devices
    )
    assert (
        len(er.async_entries_for_config_entry(entity_registry, entry.entry_id))
        == current_entites
    )