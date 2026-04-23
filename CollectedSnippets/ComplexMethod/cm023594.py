async def test_controlling_state_via_mqtt_switchname(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota
) -> None:
    """Test state update via MQTT."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["swc"][0] = 1
    config["swn"][0] = "Custom Name"
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.tasmota_custom_name")
    assert state.state == "unavailable"
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "Online")
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.tasmota_custom_name")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    # Test normal state update
    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Custom Name":{"Action":"ON"}}'
    )
    state = hass.states.get("binary_sensor.tasmota_custom_name")
    assert state.state == STATE_ON

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Custom Name":{"Action":"OFF"}}'
    )
    state = hass.states.get("binary_sensor.tasmota_custom_name")
    assert state.state == STATE_OFF

    # Test periodic state update
    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/SENSOR", '{"Custom Name":"ON"}')
    state = hass.states.get("binary_sensor.tasmota_custom_name")
    assert state.state == STATE_ON

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/SENSOR", '{"Custom Name":"OFF"}')
    state = hass.states.get("binary_sensor.tasmota_custom_name")
    assert state.state == STATE_OFF

    # Test polled state update
    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/STATUS10", '{"StatusSNS":{"Custom Name":"ON"}}'
    )
    state = hass.states.get("binary_sensor.tasmota_custom_name")
    assert state.state == STATE_ON

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/STATUS10", '{"StatusSNS":{"Custom Name":"OFF"}}'
    )
    state = hass.states.get("binary_sensor.tasmota_custom_name")
    assert state.state == STATE_OFF