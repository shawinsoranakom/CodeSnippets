async def test_indexed_sensor_attributes(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota
) -> None:
    """Test correct attributes for sensors."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    sensor_config = {
        "sn": {
            "Dummy1": {"Temperature": [None, None]},
            "Dummy2": {"CarbonDioxide": [None, None]},
            "TempUnit": "C",
        }
    }
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

    state = hass.states.get("sensor.tasmota_dummy1_temperature_0")
    assert state.attributes.get("device_class") == "temperature"
    assert state.attributes.get("friendly_name") == "Tasmota Dummy1 Temperature 0"
    assert state.attributes.get("icon") is None
    assert state.attributes.get("unit_of_measurement") == "°C"

    state = hass.states.get("sensor.tasmota_dummy2_carbondioxide_1")
    assert state.attributes.get("device_class") == "carbon_dioxide"
    assert state.attributes.get("friendly_name") == "Tasmota Dummy2 CarbonDioxide 1"
    assert state.attributes.get("icon") is None
    assert state.attributes.get("unit_of_measurement") == "ppm"