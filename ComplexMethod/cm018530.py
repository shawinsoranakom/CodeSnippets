async def test_block_device_rgb_bulb(
    hass: HomeAssistant,
    mock_block_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    entity_registry: EntityRegistry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test block device RGB bulb."""
    monkeypatch.setitem(mock_block_device.shelly, "num_outputs", 1)
    entity_id = "light.test_name"
    monkeypatch.delattr(mock_block_device.blocks[LIGHT_BLOCK_ID], "mode")
    monkeypatch.setattr(
        mock_block_device.blocks[LIGHT_BLOCK_ID], "description", "light_1"
    )
    await init_integration(hass, 1, model=MODEL_BULB_RGBW)

    # Test initial
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_RGB_COLOR] == (45, 55, 65)
    assert state.attributes[ATTR_BRIGHTNESS] == 48
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [
        ColorMode.COLOR_TEMP,
        ColorMode.RGB,
    ]
    assert (
        state.attributes[ATTR_SUPPORTED_FEATURES]
        == LightEntityFeature.EFFECT | LightEntityFeature.TRANSITION
    )
    assert len(state.attributes[ATTR_EFFECT_LIST]) == 4
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

    # Turn on, RGB = [70, 80, 90], brightness = 33, effect = Flash
    mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_RGB_COLOR: [70, 80, 90],
            ATTR_BRIGHTNESS: 33,
            ATTR_EFFECT: "Flash",
        },
        blocking=True,
    )
    mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
        turn="on", gain=13, brightness=13, red=70, green=80, blue=90, effect=3
    )
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.RGB
    assert state.attributes[ATTR_RGB_COLOR] == (70, 80, 90)
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

    # Turn on with unsupported effect
    mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "Breath"},
        blocking=True,
    )
    mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
        turn="on", mode="color"
    )

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_EFFECT] == "Off"
    assert "Effect 'Breath' not supported" in caplog.text

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-light_1"