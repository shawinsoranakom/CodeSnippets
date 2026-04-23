async def test_xiaomi_lock(hass: HomeAssistant) -> None:
    """Make sure that lock events are correctly mapped."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="D7:1F:44:EB:8A:91",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0

    inject_bluetooth_service_info(
        hass,
        make_advertisement(
            "D7:1F:44:EB:8A:91",
            b"PD\x9e\x06C\x91\x8a\xebD\x1f\xd7\x0b\x00\t \x02\x00\x01\x80|D/a",
        ),
    )

    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 4

    event = hass.states.get("event.door_lock_8a91_lock")
    event_attr = event.attributes
    assert event_attr[ATTR_FRIENDLY_NAME] == "Door Lock 8A91 Lock"
    assert event_attr[ATTR_EVENT_TYPE] == "unlock_outside_the_door"

    sensor = hass.states.get("sensor.door_lock_8a91_lock_method")
    sensor_attr = sensor.attributes
    assert sensor.state == "biometrics"
    assert sensor_attr[ATTR_FRIENDLY_NAME] == "Door Lock 8A91 Lock method"

    sensor = hass.states.get("sensor.door_lock_8a91_key_id")
    sensor_attr = sensor.attributes
    assert sensor.state == "Fingerprint key id 2"
    assert sensor_attr[ATTR_FRIENDLY_NAME] == "Door Lock 8A91 Key id"

    binary_sensor = hass.states.get("binary_sensor.door_lock_8a91_lock")
    binary_sensor_attribtes = binary_sensor.attributes
    assert binary_sensor.state == STATE_ON
    assert binary_sensor_attribtes[ATTR_FRIENDLY_NAME] == "Door Lock 8A91 Lock"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()