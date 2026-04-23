async def test_v2_binary_sensors(
    hass: HomeAssistant,
    mac_address,
    advertisement,
    bind_key,
    result,
) -> None:
    """Test the different BTHome v2 binary sensors."""
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
        binary_sensor = hass.states.get(meas["binary_sensor_entity"])
        binary_sensor_attr = binary_sensor.attributes
        assert binary_sensor.state == meas["expected_state"]
        assert binary_sensor_attr[ATTR_FRIENDLY_NAME] == meas["friendly_name"]
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()