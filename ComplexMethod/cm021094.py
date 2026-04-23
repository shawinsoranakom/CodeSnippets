async def test_vibration_sensor(hass: HomeAssistant) -> None:
    """Test setting up creates the vibration sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=GVH5124_SERVICE_INFO.address,
        data={CONF_DEVICE_TYPE: "H5124"},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 1
    inject_bluetooth_service_info(hass, GVH5124_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 2

    motion_sensor = hass.states.get("event.h5124_vibration")
    first_time = motion_sensor.state
    assert motion_sensor.state != STATE_UNKNOWN

    inject_bluetooth_service_info(hass, GVH5124_2_SERVICE_INFO)
    await hass.async_block_till_done()

    motion_sensor = hass.states.get("event.h5124_vibration")
    assert motion_sensor.state != first_time
    assert motion_sensor.state != STATE_UNKNOWN
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()