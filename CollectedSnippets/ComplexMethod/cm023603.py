async def test_bad_indexed_sensor_state_via_mqtt(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota
) -> None:
    """Test state update via MQTT where sensor is not matching configuration."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    sensor_config = copy.deepcopy(BAD_LIST_SENSOR_CONFIG_3)
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()
    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/sensors",
        json.dumps(sensor_config),
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.tasmota_energy_apparentpower_0")
    assert state.state == "unavailable"
    assert not state.attributes.get(ATTR_ASSUMED_STATE)
    state = hass.states.get("sensor.tasmota_energy_apparentpower_1")
    assert state.state == "unavailable"
    assert not state.attributes.get(ATTR_ASSUMED_STATE)
    state = hass.states.get("sensor.tasmota_energy_apparentpower_2")
    assert state.state == "unavailable"
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "Online")
    await hass.async_block_till_done()
    state = hass.states.get("sensor.tasmota_energy_apparentpower_0")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)
    state = hass.states.get("sensor.tasmota_energy_apparentpower_1")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)
    state = hass.states.get("sensor.tasmota_energy_apparentpower_2")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    # Test periodic state update
    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/SENSOR", '{"ENERGY":{"ApparentPower":[1.2,3.4,5.6]}}'
    )
    state = hass.states.get("sensor.tasmota_energy_apparentpower_0")
    assert state.state == "1.2"
    state = hass.states.get("sensor.tasmota_energy_apparentpower_1")
    assert state.state == "3.4"
    state = hass.states.get("sensor.tasmota_energy_apparentpower_2")
    assert state.state == "5.6"

    # Test periodic state update with too few values
    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/SENSOR", '{"ENERGY":{"ApparentPower":[7.8,9.0]}}'
    )
    state = hass.states.get("sensor.tasmota_energy_apparentpower_0")
    assert state.state == "7.8"
    state = hass.states.get("sensor.tasmota_energy_apparentpower_1")
    assert state.state == "9.0"
    state = hass.states.get("sensor.tasmota_energy_apparentpower_2")
    assert state.state == "5.6"

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/SENSOR", '{"ENERGY":{"ApparentPower":2.3}}'
    )
    state = hass.states.get("sensor.tasmota_energy_apparentpower_0")
    assert state.state == "2.3"
    state = hass.states.get("sensor.tasmota_energy_apparentpower_1")
    assert state.state == "9.0"
    state = hass.states.get("sensor.tasmota_energy_apparentpower_2")
    assert state.state == "5.6"

    # Test polled state update
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS10",
        '{"StatusSNS":{"ENERGY":{"ApparentPower":[1.2,3.4,5.6]}}}',
    )
    state = hass.states.get("sensor.tasmota_energy_apparentpower_0")
    assert state.state == "1.2"
    state = hass.states.get("sensor.tasmota_energy_apparentpower_1")
    assert state.state == "3.4"
    state = hass.states.get("sensor.tasmota_energy_apparentpower_2")
    assert state.state == "5.6"

    # Test polled state update with too few values
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS10",
        '{"StatusSNS":{"ENERGY":{"ApparentPower":[7.8,9.0]}}}',
    )
    state = hass.states.get("sensor.tasmota_energy_apparentpower_0")
    assert state.state == "7.8"
    state = hass.states.get("sensor.tasmota_energy_apparentpower_1")
    assert state.state == "9.0"
    state = hass.states.get("sensor.tasmota_energy_apparentpower_2")
    assert state.state == "5.6"

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS10",
        '{"StatusSNS":{"ENERGY":{"ApparentPower":2.3}}}',
    )
    state = hass.states.get("sensor.tasmota_energy_apparentpower_0")
    assert state.state == "2.3"
    state = hass.states.get("sensor.tasmota_energy_apparentpower_1")
    assert state.state == "9.0"
    state = hass.states.get("sensor.tasmota_energy_apparentpower_2")
    assert state.state == "5.6"