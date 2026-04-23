async def test_nested_sensor_attributes(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota
) -> None:
    """Test correct attributes for sensors."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    sensor_config = copy.deepcopy(DICT_SENSOR_CONFIG_1)
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

    state = hass.states.get("sensor.tasmota_tx23_speed_act")
    assert state.attributes.get("device_class") is None
    assert state.attributes.get("friendly_name") == "Tasmota TX23 Speed Act"
    assert state.attributes.get("icon") is None
    assert state.attributes.get("unit_of_measurement") == "km/h"

    state = hass.states.get("sensor.tasmota_tx23_dir_avg")
    assert state.attributes.get("device_class") is None
    assert state.attributes.get("friendly_name") == "Tasmota TX23 Dir Avg"
    assert state.attributes.get("icon") is None
    assert state.attributes.get("unit_of_measurement") is None