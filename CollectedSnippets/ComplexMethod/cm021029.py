async def test_entities_removed_after_reload(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_client: APIClient,
    hass_storage: dict[str, Any],
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test entities and their registry entry are removed when static info changes after a reload."""
    entity_info = [
        BinarySensorInfo(
            object_id="mybinary_sensor",
            key=1,
            name="my binary_sensor",
        ),
        BinarySensorInfo(
            object_id="mybinary_sensor_to_be_removed",
            key=2,
            name="my binary_sensor to be removed",
        ),
    ]
    states = [
        BinarySensorState(key=1, state=True, missing_state=False),
        BinarySensorState(key=2, state=True, missing_state=False),
    ]
    mock_device: MockESPHomeDevice = await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
    )
    entry = mock_device.entry
    entry_id = entry.entry_id
    storage_key = f"esphome.{entry_id}"
    state = hass.states.get("binary_sensor.test_my_binary_sensor")
    assert state is not None
    assert state.state == STATE_ON
    state = hass.states.get("binary_sensor.test_my_binary_sensor_to_be_removed")
    assert state is not None
    assert state.state == STATE_ON

    reg_entry = entity_registry.async_get(
        "binary_sensor.test_my_binary_sensor_to_be_removed"
    )
    assert reg_entry is not None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass_storage[storage_key]["data"]["binary_sensor"]) == 2

    state = hass.states.get("binary_sensor.test_my_binary_sensor")
    assert state is not None
    assert state.attributes[ATTR_RESTORED] is True
    state = hass.states.get("binary_sensor.test_my_binary_sensor_to_be_removed")
    assert state is not None
    assert state.attributes[ATTR_RESTORED] is True

    reg_entry = entity_registry.async_get(
        "binary_sensor.test_my_binary_sensor_to_be_removed"
    )
    assert reg_entry is not None

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass_storage[storage_key]["data"]["binary_sensor"]) == 2

    state = hass.states.get("binary_sensor.test_my_binary_sensor")
    assert state is not None
    assert ATTR_RESTORED not in state.attributes
    state = hass.states.get("binary_sensor.test_my_binary_sensor_to_be_removed")
    assert state is not None
    assert ATTR_RESTORED not in state.attributes
    reg_entry = entity_registry.async_get(
        "binary_sensor.test_my_binary_sensor_to_be_removed"
    )
    assert reg_entry is not None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    entity_info = [
        BinarySensorInfo(
            object_id="mybinary_sensor",
            key=1,
            name="my binary_sensor",
        ),
    ]
    mock_device.client.list_entities_services = AsyncMock(
        return_value=(entity_info, [])
    )
    mock_device.client.device_info_and_list_entities = AsyncMock(
        return_value=(mock_device.device_info, entity_info, [])
    )

    assert await hass.config_entries.async_setup(entry.entry_id)
    on_future = hass.loop.create_future()

    @callback
    def _async_wait_for_on(event: Event[EventStateChangedData]) -> None:
        if event.data["new_state"].state == STATE_ON:
            on_future.set_result(None)

    async_track_state_change_event(
        hass, ["binary_sensor.test_my_binary_sensor"], _async_wait_for_on
    )
    await hass.async_block_till_done()
    async with asyncio.timeout(2):
        await on_future

    assert mock_device.entry.entry_id == entry_id
    state = hass.states.get("binary_sensor.test_my_binary_sensor")
    assert state is not None
    assert state.state == STATE_ON
    state = hass.states.get("binary_sensor.test_my_binary_sensor_to_be_removed")
    assert state is None

    await hass.async_block_till_done()

    reg_entry = entity_registry.async_get(
        "binary_sensor.test_my_binary_sensor_to_be_removed"
    )
    assert reg_entry is None
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert len(hass_storage[storage_key]["data"]["binary_sensor"]) == 1