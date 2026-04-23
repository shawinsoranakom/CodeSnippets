async def test_presence_sensor(hass: HomeAssistant) -> None:
    """Test setting up creates the sensors for Presence Sensor."""
    await async_setup_component(hass, DOMAIN, {})
    inject_bluetooth_service_info(hass, PRESENCE_SENSOR_SERVICE_INFO)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
            CONF_NAME: "test-name",
            CONF_SENSOR_TYPE: "presence_sensor",
        },
        unique_id="aabbccddeeff",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 4
    assert len(hass.states.async_all("binary_sensor")) == 1

    battery_sensor = hass.states.get("sensor.test_name_battery")
    battery_sensor_attrs = battery_sensor.attributes
    assert battery_sensor
    assert battery_sensor.state == "100"
    assert battery_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Battery"
    assert battery_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    battery_range_sensor = hass.states.get("sensor.test_name_battery_range")
    assert battery_range_sensor is not None
    assert battery_range_sensor.state == "high"
    assert (
        battery_range_sensor.attributes[ATTR_FRIENDLY_NAME] == "test-name Battery range"
    )

    light_level_sensor = hass.states.get("sensor.test_name_light_level")
    light_level_sensor_attrs = light_level_sensor.attributes
    assert light_level_sensor
    assert light_level_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Light level"

    rssi_sensor = hass.states.get("sensor.test_name_bluetooth_signal")
    rssi_sensor_attrs = rssi_sensor.attributes
    assert rssi_sensor
    assert rssi_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Bluetooth signal"
    assert rssi_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "dBm"

    occupancy_sensor = hass.states.get("binary_sensor.test_name_occupancy")
    occupancy_sensor_attrs = occupancy_sensor.attributes
    assert occupancy_sensor
    assert occupancy_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Occupancy"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()