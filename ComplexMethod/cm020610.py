async def test_door_problem_sensors(hass: HomeAssistant) -> None:
    """Test setting up a door binary sensor with additional problem sensors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="EE:89:73:44:BE:98",
        data={"bindkey": "2c3795afa33019a8afdc17ba99e6f217"},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "EE:89:73:44:BE:98",
            b"HU9\x0e3\x9cq\xc0$\x1f\xff\xee\x80S\x00\x00\x02\xb4\xc59",
        ),
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 3

    door_sensor = hass.states.get("binary_sensor.door_lock_be98_door")
    door_sensor_attribtes = door_sensor.attributes
    assert door_sensor.state == STATE_OFF
    assert door_sensor_attribtes[ATTR_FRIENDLY_NAME] == "Door Lock BE98 Door"

    door_left_open = hass.states.get("binary_sensor.door_lock_be98_door_left_open")
    door_left_open_attribtes = door_left_open.attributes
    assert door_left_open.state == STATE_OFF
    assert (
        door_left_open_attribtes[ATTR_FRIENDLY_NAME] == "Door Lock BE98 Door left open"
    )

    pry_the_door = hass.states.get("binary_sensor.door_lock_be98_pry_the_door")
    pry_the_door_attribtes = pry_the_door.attributes
    assert pry_the_door.state == STATE_OFF
    assert pry_the_door_attribtes[ATTR_FRIENDLY_NAME] == "Door Lock BE98 Pry the door"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()