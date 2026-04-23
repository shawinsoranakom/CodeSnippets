async def test_device_with_corrupt_name(hass: HomeAssistant) -> None:
    """Test setting up a known device type with a corrupt name."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AA:BB:CC:DD:EE:FF",
        data={CONF_DEVICE_TYPE: "IBS-TH"},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0
    inject_bluetooth_service_info(hass, SPS_WITH_CORRUPT_NAME_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 3

    temp_sensor = hass.states.get("sensor.ibs_th_eeff_battery")
    temp_sensor_attribtes = temp_sensor.attributes
    assert temp_sensor.state == "87"
    assert temp_sensor_attribtes[ATTR_FRIENDLY_NAME] == "IBS-TH EEFF Battery"
    assert temp_sensor_attribtes[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert temp_sensor_attribtes[ATTR_STATE_CLASS] == "measurement"

    assert entry.data[CONF_DEVICE_TYPE] == "IBS-TH"
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()