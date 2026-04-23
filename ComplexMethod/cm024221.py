async def test_received_rgbx_values_set_state_optimistic(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the state is set correctly when an rgbx update is received."""
    await mqtt_mock_entry()
    state = hass.states.get("light.test")
    assert state and state.state is not None
    async_fire_mqtt_message(hass, "test-topic", "ON")
    ## Test rgb processing
    async_fire_mqtt_message(hass, "rgb-state-topic", "255,255,255")
    await hass.async_block_till_done()
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_mode"] == "rgb"
    assert state.attributes["rgb_color"] == (255, 255, 255)

    # Only update color mode
    async_fire_mqtt_message(hass, "color-mode-state-topic", "rgbww")
    await hass.async_block_till_done()
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_mode"] == "rgbww"

    # Resending same rgb value should restore color mode
    async_fire_mqtt_message(hass, "rgb-state-topic", "255,255,255")
    await hass.async_block_till_done()
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_mode"] == "rgb"
    assert state.attributes["rgb_color"] == (255, 255, 255)

    # Only update brightness
    await common.async_turn_on(hass, "light.test", brightness=128)
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 128
    assert state.attributes["color_mode"] == "rgb"
    assert state.attributes["rgb_color"] == (255, 255, 255)

    # Resending same rgb value should restore brightness
    async_fire_mqtt_message(hass, "rgb-state-topic", "255,255,255")
    await hass.async_block_till_done()
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_mode"] == "rgb"
    assert state.attributes["rgb_color"] == (255, 255, 255)

    # Only change rgb value
    async_fire_mqtt_message(hass, "rgb-state-topic", "255,255,0")
    await hass.async_block_till_done()
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_mode"] == "rgb"
    assert state.attributes["rgb_color"] == (255, 255, 0)

    ## Test rgbw processing
    async_fire_mqtt_message(hass, "rgbw-state-topic", "255,255,255,255")
    await hass.async_block_till_done()
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_mode"] == "rgbw"
    assert state.attributes["rgbw_color"] == (255, 255, 255, 255)

    # Only update color mode
    async_fire_mqtt_message(hass, "color-mode-state-topic", "rgb")
    await hass.async_block_till_done()
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_mode"] == "rgb"

    # Resending same rgbw value should restore color mode
    async_fire_mqtt_message(hass, "rgbw-state-topic", "255,255,255,255")
    await hass.async_block_till_done()
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_mode"] == "rgbw"
    assert state.attributes["rgbw_color"] == (255, 255, 255, 255)

    # Only update brightness
    await common.async_turn_on(hass, "light.test", brightness=128)
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 128
    assert state.attributes["color_mode"] == "rgbw"
    assert state.attributes["rgbw_color"] == (255, 255, 255, 255)

    # Resending same rgbw value should restore brightness
    async_fire_mqtt_message(hass, "rgbw-state-topic", "255,255,255,255")
    await hass.async_block_till_done()
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_mode"] == "rgbw"
    assert state.attributes["rgbw_color"] == (255, 255, 255, 255)

    # Only change rgbw value
    async_fire_mqtt_message(hass, "rgbw-state-topic", "255,255,128,255")
    await hass.async_block_till_done()
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_mode"] == "rgbw"
    assert state.attributes["rgbw_color"] == (255, 255, 128, 255)

    ## Test rgbww processing
    async_fire_mqtt_message(hass, "rgbww-state-topic", "255,255,255,32,255")
    await hass.async_block_till_done()
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_mode"] == "rgbww"
    assert state.attributes["rgbww_color"] == (255, 255, 255, 32, 255)

    # Only update color mode
    async_fire_mqtt_message(hass, "color-mode-state-topic", "rgb")
    await hass.async_block_till_done()
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_mode"] == "rgb"

    # Resending same rgbw value should restore color mode
    async_fire_mqtt_message(hass, "rgbww-state-topic", "255,255,255,32,255")
    await hass.async_block_till_done()
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_mode"] == "rgbww"
    assert state.attributes["rgbww_color"] == (255, 255, 255, 32, 255)

    # Only update brightness
    await common.async_turn_on(hass, "light.test", brightness=128)
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 128
    assert state.attributes["color_mode"] == "rgbww"
    assert state.attributes["rgbww_color"] == (255, 255, 255, 32, 255)

    # Resending same rgbww value should restore brightness
    async_fire_mqtt_message(hass, "rgbww-state-topic", "255,255,255,32,255")
    await hass.async_block_till_done()
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_mode"] == "rgbww"
    assert state.attributes["rgbww_color"] == (255, 255, 255, 32, 255)

    # Only change rgbww value
    async_fire_mqtt_message(hass, "rgbww-state-topic", "255,255,128,32,255")
    await hass.async_block_till_done()
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_mode"] == "rgbww"
    assert state.attributes["rgbww_color"] == (255, 255, 128, 32, 255)