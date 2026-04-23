async def test_v1_sensors(
    hass: HomeAssistant,
    mac_address,
    advertisement,
    bind_key,
    result,
) -> None:
    """Test the different BTHome V1 sensors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=mac_address,
        data={"bindkey": bind_key},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0

    inject_bluetooth_service_info(
        hass,
        advertisement,
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == len(result)

    for meas in result:
        sensor = hass.states.get(meas["sensor_entity"])
        sensor_attr = sensor.attributes
        assert sensor.state == meas["expected_state"]
        assert sensor_attr[ATTR_FRIENDLY_NAME] == meas["friendly_name"]
        if ATTR_UNIT_OF_MEASUREMENT in sensor_attr:
            # Some sensors don't have a unit of measurement
            assert sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == meas["unit_of_measurement"]
        assert sensor_attr[ATTR_STATE_CLASS] == meas["state_class"]
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()