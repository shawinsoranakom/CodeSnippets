async def test_controlling_state_via_mqtt(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota
) -> None:
    """Test state update via MQTT."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["rl"][0] = 1
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()

    state = hass.states.get("switch.tasmota_test")
    assert state.state == "unavailable"
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "Online")
    await hass.async_block_till_done()
    state = hass.states.get("switch.tasmota_test")
    assert state.state == STATE_OFF
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON"}')

    state = hass.states.get("switch.tasmota_test")
    assert state.state == STATE_ON

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"OFF"}')

    state = hass.states.get("switch.tasmota_test")
    assert state.state == STATE_OFF

    async_fire_mqtt_message(hass, "tasmota_49A3BC/stat/RESULT", '{"POWER":"ON"}')

    state = hass.states.get("switch.tasmota_test")
    assert state.state == STATE_ON

    async_fire_mqtt_message(hass, "tasmota_49A3BC/stat/RESULT", '{"POWER":"OFF"}')

    state = hass.states.get("switch.tasmota_test")
    assert state.state == STATE_OFF