async def test_xiaomi_battery_voltage(hass: HomeAssistant) -> None:
    """Make sure that battery voltage sensors are correctly mapped."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="C4:7C:8D:6A:3E:7A",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # WARNING: This test data is synthetic, rather than captured from a real device
    # obj type is 0x0a10, payload len is 0x2 and payload is 0x6400
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "C4:7C:8D:6A:3E:7A", b"q \x5d\x01iz>j\x8d|\xc4\r\x0a\x10\x02\x64\x00"
        ),
    )

    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 2

    volt_sensor = hass.states.get("sensor.smart_flower_pot_3e7a_voltage")
    volt_sensor_attr = volt_sensor.attributes
    assert volt_sensor.state == "3.1"
    assert volt_sensor_attr[ATTR_FRIENDLY_NAME] == "Smart Flower Pot 3E7A Voltage"
    assert volt_sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "V"
    assert volt_sensor_attr[ATTR_STATE_CLASS] == "measurement"

    bat_sensor = hass.states.get("sensor.smart_flower_pot_3e7a_battery")
    bat_sensor_attr = bat_sensor.attributes
    assert bat_sensor.state == "100"
    assert bat_sensor_attr[ATTR_FRIENDLY_NAME] == "Smart Flower Pot 3E7A Battery"
    assert bat_sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert bat_sensor_attr[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()