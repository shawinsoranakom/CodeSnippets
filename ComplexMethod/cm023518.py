async def test_hubmini_matter_sensor(hass: HomeAssistant) -> None:
    """Test setting up creates the sensor for HubMini Matter."""
    await async_setup_component(hass, DOMAIN, {})
    inject_bluetooth_service_info(hass, HUBMINI_MATTER_SERVICE_INFO)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
            CONF_NAME: "test-name",
            CONF_SENSOR_TYPE: "hubmini_matter",
        },
        unique_id="aabbccddeeff",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 3

    temperature_sensor = hass.states.get("sensor.test_name_temperature")
    temperature_sensor_attrs = temperature_sensor.attributes
    assert temperature_sensor.state == "24.1"
    assert temperature_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Temperature"
    assert temperature_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "°C"
    assert temperature_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    humidity_sensor = hass.states.get("sensor.test_name_humidity")
    humidity_sensor_attrs = humidity_sensor.attributes
    assert humidity_sensor.state == "53"
    assert humidity_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Humidity"
    assert humidity_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert humidity_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    rssi_sensor = hass.states.get("sensor.test_name_bluetooth_signal")
    rssi_sensor_attrs = rssi_sensor.attributes
    assert rssi_sensor.state == "-60"
    assert rssi_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Bluetooth signal"
    assert rssi_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "dBm"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()