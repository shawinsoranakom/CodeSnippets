async def test_xiaomi_formaldeyhde(hass: HomeAssistant) -> None:
    """Make sure that formldehyde sensors are correctly mapped."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="C4:7C:8D:6A:3E:7A",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0

    # WARNING: This test data is synthetic, rather than captured from a real device
    # obj type is 0x1010, payload len is 0x2 and payload is 0xf400
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "C4:7C:8D:6A:3E:7A", b"q \x5d\x01iz>j\x8d|\xc4\r\x10\x10\x02\xf4\x00"
        ),
    )

    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 1

    sensor = hass.states.get("sensor.smart_flower_pot_3e7a_formaldehyde")
    sensor_attr = sensor.attributes
    assert sensor.state == "2.44"
    assert sensor_attr[ATTR_FRIENDLY_NAME] == "Smart Flower Pot 3E7A Formaldehyde"
    assert sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "mg/m³"
    assert sensor_attr[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()