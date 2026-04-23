async def test_opening_problem_sensors(hass: HomeAssistant) -> None:
    """Test setting up a opening binary sensor with additional problem sensors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="A4:C1:38:66:E5:67",
        data={"bindkey": "0fdcc30fe9289254876b5ef7c11ef1f0"},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "A4:C1:38:66:E5:67",
            b"XY\x89\x18ug\xe5f8\xc1\xa4i\xdd\xf3\xa1&\x00\x00\xa2J\x1bE",
        ),
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 3

    opening_sensor = hass.states.get("binary_sensor.door_window_sensor_e567_opening")
    opening_sensor_attribtes = opening_sensor.attributes
    assert opening_sensor.state == STATE_OFF
    assert (
        opening_sensor_attribtes[ATTR_FRIENDLY_NAME]
        == "Door/Window Sensor E567 Opening"
    )

    door_left_open = hass.states.get(
        "binary_sensor.door_window_sensor_e567_door_left_open"
    )
    door_left_open_attribtes = door_left_open.attributes
    assert door_left_open.state == STATE_OFF
    assert (
        door_left_open_attribtes[ATTR_FRIENDLY_NAME]
        == "Door/Window Sensor E567 Door left open"
    )

    device_forcibly_removed = hass.states.get(
        "binary_sensor.door_window_sensor_e567_device_forcibly_removed"
    )
    device_forcibly_removed_attribtes = device_forcibly_removed.attributes
    assert device_forcibly_removed.state == STATE_OFF
    assert (
        device_forcibly_removed_attribtes[ATTR_FRIENDLY_NAME]
        == "Door/Window Sensor E567 Device forcibly removed"
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()