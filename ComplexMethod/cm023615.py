async def test_controlling_state_via_mqtt_rgbww_tuya(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota
) -> None:
    """Test state update via MQTT."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["rl"][0] = 2
    config["lt_st"] = 5  # 5 channel light (RGBCW)
    config["ty"] = 1  # Tuya device
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
    assert state.attributes.get("color_mode") == "color_temp"

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"OFF"}')
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_OFF
    assert not state.attributes["color_mode"]

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON","Dimmer":50}'
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 128
    assert state.attributes.get("color_mode") == "color_temp"

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/tele/STATE",
        '{"POWER":"ON","HSBColor":"30,100,0","White":0}',
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("hs_color") == (30, 100)
    assert state.attributes.get("color_mode") == "hs"

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/tele/STATE",
        '{"POWER":"ON","Dimmer":0}',
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("hs_color") == (30, 100)
    assert state.attributes.get("color_mode") == "hs"

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON","Dimmer":50,"White":50}'
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    # Setting white > 0 should clear the color
    assert not state.attributes.get("hs_color")
    assert state.attributes.get("color_mode") == "color_temp"

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON","CT":300}'
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("color_temp_kelvin") == 3333
    assert state.attributes.get("color_mode") == "color_temp"

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON","White":0}'
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    # Setting white to 0 should clear the color_temp
    assert not state.attributes.get("color_temp_kelvin")
    assert state.attributes.get("color_mode") == "hs"

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