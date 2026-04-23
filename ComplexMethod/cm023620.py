async def test_controlling_state_via_mqtt(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota
) -> None:
    """Test state update via MQTT."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["if"] = 1
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()

    state = hass.states.get("fan.tasmota")
    assert state.state == "unavailable"
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "Online")
    await hass.async_block_till_done()
    state = hass.states.get("fan.tasmota")
    assert state.state == STATE_OFF
    assert state.attributes["percentage"] is None
    assert (
        state.attributes["supported_features"]
        == fan.FanEntityFeature.SET_SPEED
        | fan.FanEntityFeature.TURN_OFF
        | fan.FanEntityFeature.TURN_ON
    )
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/STATE", '{"FanSpeed":1}')
    state = hass.states.get("fan.tasmota")
    assert state.state == STATE_ON
    assert state.attributes["percentage"] == 33

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/STATE", '{"FanSpeed":2}')
    state = hass.states.get("fan.tasmota")
    assert state.state == STATE_ON
    assert state.attributes["percentage"] == 66

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/STATE", '{"FanSpeed":3}')
    state = hass.states.get("fan.tasmota")
    assert state.state == STATE_ON
    assert state.attributes["percentage"] == 100

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/STATE", '{"FanSpeed":0}')
    state = hass.states.get("fan.tasmota")
    assert state.state == STATE_OFF
    assert state.attributes["percentage"] == 0

    async_fire_mqtt_message(hass, "tasmota_49A3BC/stat/RESULT", '{"FanSpeed":1}')
    state = hass.states.get("fan.tasmota")
    assert state.state == STATE_ON
    assert state.attributes["percentage"] == 33

    async_fire_mqtt_message(hass, "tasmota_49A3BC/stat/RESULT", '{"FanSpeed":0}')
    state = hass.states.get("fan.tasmota")
    assert state.state == STATE_OFF
    assert state.attributes["percentage"] == 0