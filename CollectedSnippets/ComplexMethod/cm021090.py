async def test_gv5140(hass: HomeAssistant) -> None:
    """Test CO2, temperature and humidity sensors for a GV5140 device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AA:BB:CC:DD:EE:FF",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0
    inject_bluetooth_service_info(hass, GV5140_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 3

    temp_sensor = hass.states.get("sensor.5140eeff_temperature")
    temp_sensor_attributes = temp_sensor.attributes
    assert temp_sensor.state == "21.6"
    assert temp_sensor_attributes[ATTR_FRIENDLY_NAME] == "5140EEFF Temperature"
    assert temp_sensor_attributes[ATTR_UNIT_OF_MEASUREMENT] == "°C"
    assert temp_sensor_attributes[ATTR_STATE_CLASS] == "measurement"

    humidity_sensor = hass.states.get("sensor.5140eeff_humidity")
    humidity_sensor_attributes = humidity_sensor.attributes
    assert humidity_sensor.state == "67.8"
    assert humidity_sensor_attributes[ATTR_FRIENDLY_NAME] == "5140EEFF Humidity"
    assert humidity_sensor_attributes[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert humidity_sensor_attributes[ATTR_STATE_CLASS] == "measurement"

    co2_sensor = hass.states.get("sensor.5140eeff_carbon_dioxide")
    co2_sensor_attributes = co2_sensor.attributes
    assert co2_sensor.state == "531"
    assert co2_sensor_attributes[ATTR_FRIENDLY_NAME] == "5140EEFF Carbon Dioxide"
    assert co2_sensor_attributes[ATTR_UNIT_OF_MEASUREMENT] == "ppm"
    assert co2_sensor_attributes[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()