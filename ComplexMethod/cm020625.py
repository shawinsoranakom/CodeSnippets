async def test_xiaomi_cgdk2_bind_key(hass: HomeAssistant) -> None:
    """Test CGDK2 bind key.

    This device has encryption so we need to retrieve its bind key
    from the config entry.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="58:2D:34:12:20:89",
        data={"bindkey": "a3bfe9853dd85a620debe3620caaa351"},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "58:2D:34:12:20:89",
            b"XXo\x06\x07\x89 \x124-X_\x17m\xd5O\x02\x00\x00/\xa4S\xfa",
        ),
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 1

    temp_sensor = hass.states.get("sensor.temperature_humidity_sensor_2089_temperature")
    temp_sensor_attribtes = temp_sensor.attributes
    assert temp_sensor.state == "22.6"
    assert (
        temp_sensor_attribtes[ATTR_FRIENDLY_NAME]
        == "Temperature/Humidity Sensor 2089 Temperature"
    )
    assert temp_sensor_attribtes[ATTR_UNIT_OF_MEASUREMENT] == "°C"
    assert temp_sensor_attribtes[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()