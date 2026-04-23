async def test_block_device_white_bulb(
    hass: HomeAssistant,
    mock_block_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test block device white bulb."""
    monkeypatch.setitem(mock_block_device.shelly, "num_outputs", 1)
    entity_id = "light.test_name"
    monkeypatch.delattr(mock_block_device.blocks[LIGHT_BLOCK_ID], "red")
    monkeypatch.delattr(mock_block_device.blocks[LIGHT_BLOCK_ID], "green")
    monkeypatch.delattr(mock_block_device.blocks[LIGHT_BLOCK_ID], "blue")
    monkeypatch.delattr(mock_block_device.blocks[LIGHT_BLOCK_ID], "mode")
    monkeypatch.delattr(mock_block_device.blocks[LIGHT_BLOCK_ID], "colorTemp")
    monkeypatch.delattr(mock_block_device.blocks[LIGHT_BLOCK_ID], "effect")
    monkeypatch.setattr(
        mock_block_device.blocks[LIGHT_BLOCK_ID], "description", "light_1"
    )
    monkeypatch.setattr(
        mock_block_device.blocks[LIGHT_BLOCK_ID],
        "set_state",
        AsyncMock(side_effect=mock_white_light_set_state),
    )
    await init_integration(hass, 1, model=MODEL_VINTAGE_V2)

    # Test initial
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 128
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.BRIGHTNESS]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == LightEntityFeature.TRANSITION

    # Turn off
    mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
        turn="off"
    )
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF

    # Turn on, brightness = 33
    mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 33},
        blocking=True,
    )
    mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
        turn="on", gain=13, brightness=13
    )
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 33

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-light_1"