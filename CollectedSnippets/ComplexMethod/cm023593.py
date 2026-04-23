async def test_controlling_state_via_mqtt(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota
) -> None:
    """Test state update via MQTT."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["swc"][0] = 1
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.tasmota_binary_sensor_1")
    assert state.state == "unavailable"
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "Online")
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.tasmota_binary_sensor_1")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    # Test normal state update
    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"ON"}}'
    )
    state = hass.states.get("binary_sensor.tasmota_binary_sensor_1")
    assert state.state == STATE_ON

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"OFF"}}'
    )
    state = hass.states.get("binary_sensor.tasmota_binary_sensor_1")
    assert state.state == STATE_OFF

    # Test periodic state update
    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/SENSOR", '{"Switch1":"ON"}')
    state = hass.states.get("binary_sensor.tasmota_binary_sensor_1")
    assert state.state == STATE_ON

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/SENSOR", '{"Switch1":"OFF"}')
    state = hass.states.get("binary_sensor.tasmota_binary_sensor_1")
    assert state.state == STATE_OFF

    # Test polled state update
    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/STATUS10", '{"StatusSNS":{"Switch1":"ON"}}'
    )
    state = hass.states.get("binary_sensor.tasmota_binary_sensor_1")
    assert state.state == STATE_ON

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/STATUS10", '{"StatusSNS":{"Switch1":"OFF"}}'
    )
    state = hass.states.get("binary_sensor.tasmota_binary_sensor_1")
    assert state.state == STATE_OFF

    # Test force update flag
    entity = hass.data["entity_components"]["binary_sensor"].get_entity(
        "binary_sensor.tasmota_binary_sensor_1"
    )
    assert not entity.force_update