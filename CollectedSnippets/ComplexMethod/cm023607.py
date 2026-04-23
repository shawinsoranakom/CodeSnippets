async def test_attributes(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota
) -> None:
    """Test correct attributes for sensors."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    sensor_config = {
        "sn": {
            "DHT11": {"Temperature": None},
            "Beer": {"CarbonDioxide": None},
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

    state = hass.states.get("sensor.tasmota_dht11_temperature")
    assert state.attributes.get("device_class") == "temperature"
    assert state.attributes.get("friendly_name") == "Tasmota DHT11 Temperature"
    assert state.attributes.get("icon") is None
    assert state.attributes.get("unit_of_measurement") == "°C"

    state = hass.states.get("sensor.tasmota_beer_CarbonDioxide")
    assert state.attributes.get("device_class") == "carbon_dioxide"
    assert state.attributes.get("friendly_name") == "Tasmota Beer CarbonDioxide"
    assert state.attributes.get("icon") is None
    assert state.attributes.get("unit_of_measurement") == "ppm"