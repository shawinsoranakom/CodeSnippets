async def test_sensors(hass: HomeAssistant) -> None:
    """Test setting up creates the sensors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="00:81:F9:DD:6F:C1",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0
    inject_bluetooth_service_info_bleak(hass, MMC_T201_1_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 2

    temp_sensor = hass.states.get("sensor.baby_thermometer_6fc1_temperature")
    temp_sensor_attribtes = temp_sensor.attributes
    assert temp_sensor.state == "36.8719980616822"
    assert (
        temp_sensor_attribtes[ATTR_FRIENDLY_NAME] == "Baby Thermometer 6FC1 Temperature"
    )
    assert temp_sensor_attribtes[ATTR_UNIT_OF_MEASUREMENT] == "°C"
    assert temp_sensor_attribtes[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()