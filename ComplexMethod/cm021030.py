async def test_entities_for_entire_platform_removed(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_client: APIClient,
    hass_storage: dict[str, Any],
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test removing all entities for a specific platform when static info changes."""
    entity_info = [
        BinarySensorInfo(
            object_id="mybinary_sensor_to_be_removed",
            key=1,
            name="my binary_sensor to be removed",
        ),
    ]
    states = [
        BinarySensorState(key=1, state=True, missing_state=False),
    ]
    mock_device = await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
    )
    entry = mock_device.entry
    entry_id = entry.entry_id
    storage_key = f"esphome.{entry_id}"
    state = hass.states.get("binary_sensor.test_my_binary_sensor_to_be_removed")
    assert state is not None
    assert state.state == STATE_ON

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass_storage[storage_key]["data"]["binary_sensor"]) == 1

    state = hass.states.get("binary_sensor.test_my_binary_sensor_to_be_removed")
    assert state is not None
    reg_entry = entity_registry.async_get(
        "binary_sensor.test_my_binary_sensor_to_be_removed"
    )
    assert reg_entry is not None
    assert state.attributes[ATTR_RESTORED] is True

    mock_device = await mock_esphome_device(
        mock_client=mock_client,
        entry=entry,
    )
    assert mock_device.entry.entry_id == entry_id
    state = hass.states.get("binary_sensor.test_my_binary_sensor_to_be_removed")
    assert state is None
    reg_entry = entity_registry.async_get(
        "binary_sensor.test_my_binary_sensor_to_be_removed"
    )
    assert reg_entry is None
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert len(hass_storage[storage_key]["data"]["binary_sensor"]) == 0