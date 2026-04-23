async def test_light_motion(hass: HomeAssistant) -> None:
    """Test setting up a light and motion binary sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="58:2D:34:35:93:21",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "58:2D:34:35:93:21",
            b"P \xf6\x07\xda!\x9354-X\x0f\x00\x03\x01\x00\x00",
        ),
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 2

    motion_sensor = hass.states.get("binary_sensor.nightlight_9321_motion")
    motion_sensor_attribtes = motion_sensor.attributes
    assert motion_sensor.state == STATE_ON
    assert motion_sensor_attribtes[ATTR_FRIENDLY_NAME] == "Nightlight 9321 Motion"

    light_sensor = hass.states.get("binary_sensor.nightlight_9321_light")
    light_sensor_attribtes = light_sensor.attributes
    assert light_sensor.state == STATE_OFF
    assert light_sensor_attribtes[ATTR_FRIENDLY_NAME] == "Nightlight 9321 Light"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()