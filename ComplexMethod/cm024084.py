async def test_polling_sensor(hass: HomeAssistant) -> None:
    """Test setting up a device that needs polling."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AA:BB:CC:DD:EE:FF",
        data={CONF_DEVICE_TYPE: "IBS-TH"},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0

    with patch(
        "homeassistant.components.inkbird.coordinator.INKBIRDBluetoothDeviceData.async_poll",
        return_value=_make_sensor_update("IBS-TH", 10.24),
    ):
        inject_bluetooth_service_info(hass, SPS_PASSIVE_SERVICE_INFO)
        await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 1

    temp_sensor = hass.states.get("sensor.ibs_th_eeff_humidity")
    temp_sensor_attribtes = temp_sensor.attributes
    assert temp_sensor.state == "10.24"
    assert temp_sensor_attribtes[ATTR_FRIENDLY_NAME] == "IBS-TH EEFF Humidity"
    assert temp_sensor_attribtes[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert temp_sensor_attribtes[ATTR_STATE_CLASS] == "measurement"

    assert entry.data[CONF_DEVICE_TYPE] == "IBS-TH"

    with patch(
        "homeassistant.components.inkbird.coordinator.INKBIRDBluetoothDeviceData.async_poll",
        return_value=_make_sensor_update("IBS-TH", 20.24),
    ):
        async_fire_time_changed(hass, dt_util.utcnow() + FALLBACK_POLL_INTERVAL)
        inject_bluetooth_service_info(hass, SPS_PASSIVE_SERVICE_INFO)
        await hass.async_block_till_done()

    temp_sensor = hass.states.get("sensor.ibs_th_eeff_humidity")
    temp_sensor_attribtes = temp_sensor.attributes
    assert temp_sensor.state == "20.24"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()