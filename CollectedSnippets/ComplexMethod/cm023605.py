async def test_battery_sensor_state_via_mqtt(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota
) -> None:
    """Test state update via MQTT."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["bat"] = 1  # BatteryPercentage feature enabled
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.tasmota_battery_level")
    assert state.state == "unavailable"
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "Online")
    await hass.async_block_till_done()
    state = hass.states.get("sensor.tasmota_battery_level")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    # Test pushed state update
    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/STATE", '{"BatteryPercentage":55}'
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.tasmota_battery_level")
    assert state.state == "55"
    assert state.attributes == {
        "device_class": "battery",
        "friendly_name": "Tasmota Battery Level",
        "state_class": "measurement",
        "unit_of_measurement": "%",
    }

    # Test polled state update
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS11",
        '{"StatusSTS":{"BatteryPercentage":50}}',
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.tasmota_battery_level")
    assert state.state == "50"