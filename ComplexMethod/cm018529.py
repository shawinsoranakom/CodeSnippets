async def test_block_device_rgbw_bulb(
    hass: HomeAssistant,
    mock_block_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test block device RGBW bulb."""
    monkeypatch.setitem(mock_block_device.shelly, "num_outputs", 1)
    entity_id = "light.test_name"
    await init_integration(hass, 1, model=MODEL_BULB)

    # Test initial
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_RGBW_COLOR] == (45, 55, 65, 70)
    assert state.attributes[ATTR_BRIGHTNESS] == 48
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [
        ColorMode.COLOR_TEMP,
        ColorMode.RGBW,
    ]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == LightEntityFeature.EFFECT
    assert len(state.attributes[ATTR_EFFECT_LIST]) == 7
    assert state.attributes[ATTR_EFFECT] == "Off"

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

    # Turn on, RGBW = [70, 80, 90, 20], brightness = 33, effect = Flash
    mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_RGBW_COLOR: [70, 80, 90, 30],
            ATTR_BRIGHTNESS: 33,
            ATTR_EFFECT: "Flash",
        },
        blocking=True,
    )
    mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
        turn="on", gain=13, brightness=13, red=70, green=80, blue=90, white=30, effect=3
    )
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.RGBW
    assert state.attributes[ATTR_RGBW_COLOR] == (70, 80, 90, 30)
    assert state.attributes[ATTR_BRIGHTNESS] == 33
    assert state.attributes[ATTR_EFFECT] == "Flash"

    # Turn on, COLOR_TEMP_KELVIN = 3500
    mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 3500},
        blocking=True,
    )
    mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
        turn="on", temp=3500, mode="white"
    )
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.COLOR_TEMP
    assert state.attributes[ATTR_COLOR_TEMP_KELVIN] == 3500

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-light_0"