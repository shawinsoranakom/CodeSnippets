async def test_co2_sensor(hass: HomeAssistant) -> None:
    """Test setting up creates the co2 sensor for a WoTHPc."""
    await async_setup_component(hass, DOMAIN, {})
    inject_bluetooth_service_info(hass, WOMETERTHPC_SERVICE_INFO)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
            CONF_NAME: "test-name",
            CONF_PASSWORD: "test-password",
            CONF_SENSOR_TYPE: "hygrometer_co2",
        },
        unique_id="aabbccddeeaa",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 5

    battery_sensor = hass.states.get("sensor.test_name_battery")
    battery_sensor_attrs = battery_sensor.attributes
    assert battery_sensor.state == "100"
    assert battery_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Battery"
    assert battery_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert battery_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    rssi_sensor = hass.states.get("sensor.test_name_bluetooth_signal")
    rssi_sensor_attrs = rssi_sensor.attributes
    assert rssi_sensor.state == "-60"
    assert rssi_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Bluetooth signal"
    assert rssi_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "dBm"

    co2_sensor = hass.states.get("sensor.test_name_carbon_dioxide")
    co2_sensor_attrs = co2_sensor.attributes
    assert co2_sensor.state == "725"
    assert co2_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Carbon dioxide"
    assert co2_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "ppm"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()