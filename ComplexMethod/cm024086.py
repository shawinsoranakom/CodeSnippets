async def test_ibs_p02b_sensors(hass: HomeAssistant) -> None:
    """Test setting up creates the sensors for an IBS-P02B."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="49:24:11:18:00:65",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0
    inject_bluetooth_service_info(hass, IBS_P02B_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 2

    temp_sensor = hass.states.get("sensor.ibs_p02b_0065_battery")
    temp_sensor_attribtes = temp_sensor.attributes
    assert temp_sensor.state == "95"
    assert temp_sensor_attribtes[ATTR_FRIENDLY_NAME] == "IBS-P02B 0065 Battery"
    assert temp_sensor_attribtes[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert temp_sensor_attribtes[ATTR_STATE_CLASS] == "measurement"

    temp_sensor = hass.states.get("sensor.ibs_p02b_0065_temperature")
    temp_sensor_attribtes = temp_sensor.attributes
    assert temp_sensor.state == "36.6"
    assert temp_sensor_attribtes[ATTR_FRIENDLY_NAME] == "IBS-P02B 0065 Temperature"
    assert temp_sensor_attribtes[ATTR_UNIT_OF_MEASUREMENT] == "°C"
    assert temp_sensor_attribtes[ATTR_STATE_CLASS] == "measurement"

    # Make sure we remember the device type
    # in case the name is corrupted later
    assert entry.data[CONF_DEVICE_TYPE] == "IBS-P02B"
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()