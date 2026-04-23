async def test_controlling_state_via_mqtt_on_off(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota
) -> None:
    """Test state update via MQTT."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["rl"][0] = 1
    config["so"]["30"] = 1  # Enforce Home Assistant auto-discovery as light
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()

    state = hass.states.get("light.tasmota_test")
    assert state.state == "unavailable"
    assert not state.attributes.get(ATTR_ASSUMED_STATE)
    assert "color_mode" not in state.attributes

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "Online")
    await hass.async_block_till_done()
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_OFF
    assert not state.attributes.get(ATTR_ASSUMED_STATE)
    assert not state.attributes["color_mode"]

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON"}')
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("color_mode") == "onoff"

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"OFF"}')
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_OFF
    assert not state.attributes["color_mode"]

    async_fire_mqtt_message(hass, "tasmota_49A3BC/stat/RESULT", '{"POWER":"ON"}')

    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("color_mode") == "onoff"

    async_fire_mqtt_message(hass, "tasmota_49A3BC/stat/RESULT", '{"POWER":"OFF"}')

    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_OFF
    assert not state.attributes["color_mode"]