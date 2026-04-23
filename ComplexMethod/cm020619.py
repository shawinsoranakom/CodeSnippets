async def test_xiaomi_score(hass: HomeAssistant) -> None:
    """Make sure that score sensors are correctly mapped."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="ED:DE:34:3F:48:0C",
        data={"bindkey": "1330b99cded13258acc391627e9771f7"},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "ED:DE:34:3F:48:0C",
            b"\x48\x58\x06\x08\xc9H\x0e\xf1\x12\x81\x07\x973\xfc\x14\x00\x00VD\xdbA",
        ),
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 2

    sensor = hass.states.get("sensor.smart_toothbrush_480c_score")

    sensor_attr = sensor.attributes
    assert sensor.state == "83"
    assert sensor_attr[ATTR_FRIENDLY_NAME] == "Smart Toothbrush 480C Score"
    assert sensor_attr[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()