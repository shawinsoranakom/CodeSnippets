async def test_climate_panel_sensor(hass: HomeAssistant) -> None:
    """Test setting up creates the sensor for Climate Panel."""
    await async_setup_component(hass, DOMAIN, {})
    inject_bluetooth_service_info(hass, CLIMATE_PANEL_SERVICE_INFO)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
            CONF_NAME: "test-name",
            CONF_SENSOR_TYPE: "climate_panel",
        },
        unique_id="aabbccddeeff",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 4
    assert len(hass.states.async_all("binary_sensor")) == 2

    temperature_sensor = hass.states.get("sensor.test_name_temperature")
    temperature_sensor_attrs = temperature_sensor.attributes
    assert temperature_sensor.state == "26.6"
    assert temperature_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Temperature"
    assert temperature_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "°C"
    assert temperature_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    humidity_sensor = hass.states.get("sensor.test_name_humidity")
    humidity_sensor_attrs = humidity_sensor.attributes
    assert humidity_sensor.state == "44"
    assert humidity_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Humidity"
    assert humidity_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert humidity_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    rssi_sensor = hass.states.get("sensor.test_name_bluetooth_signal")
    rssi_sensor_attrs = rssi_sensor.attributes
    assert rssi_sensor.state == "-60"
    assert rssi_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Bluetooth signal"
    assert rssi_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "dBm"

    battery_sensor = hass.states.get("sensor.test_name_battery")
    battery_sensor_attrs = battery_sensor.attributes
    assert battery_sensor.state == "95"
    assert battery_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Battery"
    assert battery_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    light_sensor = hass.states.get("binary_sensor.test_name_light")
    light_sensor_attrs = light_sensor.attributes
    assert light_sensor.state == STATE_ON
    assert light_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Light"

    motion_sensor = hass.states.get("binary_sensor.test_name_motion")
    motion_sensor_attrs = motion_sensor.attributes
    assert motion_sensor.state == STATE_ON
    assert motion_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Motion"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()