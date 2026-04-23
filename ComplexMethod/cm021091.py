async def test_gvh5106(hass: HomeAssistant) -> None:
    """Test setting up creates the sensors for a device with PM25."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="CC:32:37:35:4E:05",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0
    inject_bluetooth_service_info(hass, GVH5106_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 3

    pm25_sensor = hass.states.get("sensor.h5106_4e05_pm25")
    pm25_sensor_attributes = pm25_sensor.attributes
    assert pm25_sensor.state == "0"
    assert pm25_sensor_attributes[ATTR_FRIENDLY_NAME] == "H5106 4E05 Pm25"
    assert pm25_sensor_attributes[ATTR_UNIT_OF_MEASUREMENT] == "μg/m³"
    assert pm25_sensor_attributes[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()