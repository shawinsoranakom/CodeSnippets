async def test_motion_sensor(hass: HomeAssistant) -> None:
    """Test setting up creates the motion sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=GV5121_MOTION_SERVICE_INFO.address,
        data={CONF_DEVICE_TYPE: "H5121"},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 1
    inject_bluetooth_service_info(hass, GV5121_MOTION_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 2

    motion_sensor = hass.states.get("event.h5121_motion")
    first_time = motion_sensor.state
    assert motion_sensor.state != STATE_UNKNOWN

    inject_bluetooth_service_info(hass, GV5121_MOTION_SERVICE_INFO_2)
    await hass.async_block_till_done()

    motion_sensor = hass.states.get("event.h5121_motion")
    assert motion_sensor.state != first_time
    assert motion_sensor.state != STATE_UNKNOWN
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()