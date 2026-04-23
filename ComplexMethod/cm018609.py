async def test_block_event(
    hass: HomeAssistant,
    monkeypatch: pytest.MonkeyPatch,
    mock_block_device: Mock,
    entity_registry: EntityRegistry,
) -> None:
    """Test block device event."""
    await init_integration(hass, 1)
    # num_outputs is 2, device name and channel name is used
    entity_id = "event.test_name_channel_1_input"

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(ATTR_EVENT_TYPES) == unordered(["single", "long"])
    assert state.attributes.get(ATTR_EVENT_TYPE) is None
    assert state.attributes.get(ATTR_DEVICE_CLASS) == EventDeviceClass.BUTTON

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-relay_0-1"

    monkeypatch.setattr(
        mock_block_device.blocks[DEVICE_BLOCK_ID],
        "sensor_ids",
        {"inputEvent": "L", "inputEventCnt": 0},
    )
    monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "inputEvent", "L")
    mock_block_device.mock_update()
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id))
    assert state.attributes.get(ATTR_EVENT_TYPE) == "long"