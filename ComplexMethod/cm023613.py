async def test_controlling_state_via_mqtt_rgbw(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota
) -> None:
    """Test state update via MQTT."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["rl"][0] = 2
    config["lt_st"] = 4  # 4 channel light (RGBW)
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
    assert state.attributes.get("color_mode") == "hs"

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"OFF"}')
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_OFF
    assert not state.attributes["color_mode"]

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON","Dimmer":50,"White":0}'
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 128
    assert state.attributes.get("color_mode") == "hs"

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON","Dimmer":75,"White":75}'
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 191
    assert state.attributes.get("color_mode") == "white"

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/tele/STATE",
        '{"POWER":"ON","Dimmer":50,"HSBColor":"30,100,50","White":0}',
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 128
    assert state.attributes.get("hs_color") == (30, 100)
    assert state.attributes.get("color_mode") == "hs"

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON","White":50}'
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 128
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("color_mode") == "white"

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON","Dimmer":0}'
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 0
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("color_mode") == "white"

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON","Scheme":3}'
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("effect") == "Cycle down"

    async_fire_mqtt_message(hass, "tasmota_49A3BC/stat/RESULT", '{"POWER":"ON"}')

    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON

    async_fire_mqtt_message(hass, "tasmota_49A3BC/stat/RESULT", '{"POWER":"OFF"}')

    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_OFF