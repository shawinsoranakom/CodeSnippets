async def test_xiaomi_hhccjcy01_not_connectable(hass: HomeAssistant) -> None:
    """Test HHCCJCY01 when sensors are not connectable.

    This device has multiple advertisements before all sensors are visible but not connectable.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="C4:7C:8D:6A:3E:7A",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "C4:7C:8D:6A:3E:7A",
            b"q \x98\x00fz>j\x8d|\xc4\r\x07\x10\x03\x00\x00\x00",
            connectable=False,
        ),
    )
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "C4:7C:8D:6A:3E:7A",
            b"q \x98\x00hz>j\x8d|\xc4\r\t\x10\x02W\x02",
            connectable=False,
        ),
    )
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "C4:7C:8D:6A:3E:7A",
            b"q \x98\x00Gz>j\x8d|\xc4\r\x08\x10\x01@",
            connectable=False,
        ),
    )
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "C4:7C:8D:6A:3E:7A",
            b"q \x98\x00iz>j\x8d|\xc4\r\x04\x10\x02\xf4\x00",
            connectable=False,
        ),
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 4

    illum_sensor = hass.states.get("sensor.plant_sensor_3e7a_illuminance")
    illum_sensor_attr = illum_sensor.attributes
    assert illum_sensor.state == "0"
    assert illum_sensor_attr[ATTR_FRIENDLY_NAME] == "Plant Sensor 3E7A Illuminance"
    assert illum_sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "lx"
    assert illum_sensor_attr[ATTR_STATE_CLASS] == "measurement"

    cond_sensor = hass.states.get("sensor.plant_sensor_3e7a_conductivity")
    cond_sensor_attribtes = cond_sensor.attributes
    assert cond_sensor.state == "599"
    assert cond_sensor_attribtes[ATTR_FRIENDLY_NAME] == "Plant Sensor 3E7A Conductivity"
    assert cond_sensor_attribtes[ATTR_UNIT_OF_MEASUREMENT] == "μS/cm"
    assert cond_sensor_attribtes[ATTR_STATE_CLASS] == "measurement"

    moist_sensor = hass.states.get("sensor.plant_sensor_3e7a_moisture")
    moist_sensor_attribtes = moist_sensor.attributes
    assert moist_sensor.state == "64"
    assert moist_sensor_attribtes[ATTR_FRIENDLY_NAME] == "Plant Sensor 3E7A Moisture"
    assert moist_sensor_attribtes[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert moist_sensor_attribtes[ATTR_STATE_CLASS] == "measurement"

    temp_sensor = hass.states.get("sensor.plant_sensor_3e7a_temperature")
    temp_sensor_attribtes = temp_sensor.attributes
    assert temp_sensor.state == "24.4"
    assert temp_sensor_attribtes[ATTR_FRIENDLY_NAME] == "Plant Sensor 3E7A Temperature"
    assert temp_sensor_attribtes[ATTR_UNIT_OF_MEASUREMENT] == "°C"
    assert temp_sensor_attribtes[ATTR_STATE_CLASS] == "measurement"

    # No battery sensor since its not connectable

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()