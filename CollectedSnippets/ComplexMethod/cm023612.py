async def test_controlling_state_via_mqtt_ct(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota
) -> None:
    """Test state update via MQTT."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["rl"][0] = 2
    config["lt_st"] = 2  # 2 channel light (CT)
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
        hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON","CT":300}'
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("color_temp_kelvin") == 3333
    assert state.attributes.get("color_mode") == "color_temp"

    # Tasmota will send "Color" also for CT light, this should be ignored
    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON","Color":"255,128"}'
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("color_temp_kelvin") == 3333
    assert state.attributes.get("brightness") == 128
    assert state.attributes.get("color_mode") == "color_temp"