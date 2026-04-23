async def test_xiaomi_xmosb01xs(hass: HomeAssistant) -> None:
    """Test XMOSB01XS multiple advertisements.

    This device has multiple advertisements before all sensors are visible.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="DC:8E:95:23:07:B7",
        data={"bindkey": "272b1c920ef435417c49228b8ab9a563"},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "DC:8E:95:23:07:B7",
            (
                b"\x58\x59\x83\x46\x91\xb7\x07\x23\x95\x8e\xdc\xc7\x17\x61\xc1"
                b"\x24\x03\x00\x25\x44\xb0\x65"
            ),
            connectable=False,
        ),
    )
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "DC:8E:95:23:07:B7",
            b"\x10\x59\x83\x46\x90\xb7\x07\x23\x95\x8e\xdc",
            connectable=False,
        ),
    )
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "DC:8E:95:23:07:B7",
            b"\x48\x59\x83\x46\x9d\x34\x45\xec\xab\xda\x93\xf9\x24\x03\x00\x9e\x01\x6d\x3d",
            connectable=False,
        ),
    )
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "DC:8E:95:23:07:B7",
            (
                b"\x58\x59\x83\x46\xa9\xb7\x07\x23\x95\x8e\xdc\xc6\x59\xa2\xdc\xc5"
                b"\x24\x03\x00\xa0\x4d\x0d\x45"
            ),
            connectable=False,
        ),
    )
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "DC:8E:95:23:07:B7",
            (
                b"\x58\x59\x83\x46\xa4\xb7\x07\x23\x95\x8e\xdc\x77\x2a\xe2\x5c\x11"
                b"\x24\x03\x00\xab\x87\x7b\xd7"
            ),
            connectable=False,
        ),
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 4

    occupancy_sensor = hass.states.get("binary_sensor.occupancy_sensor_07b7_occupancy")
    occupancy_sensor_attribtes = occupancy_sensor.attributes
    assert occupancy_sensor.state == STATE_ON
    assert (
        occupancy_sensor_attribtes[ATTR_FRIENDLY_NAME]
        == "Occupancy Sensor 07B7 Occupancy"
    )

    illum_sensor = hass.states.get("sensor.occupancy_sensor_07b7_illuminance")
    illum_sensor_attr = illum_sensor.attributes
    assert illum_sensor.state == "111.0"
    assert illum_sensor_attr[ATTR_FRIENDLY_NAME] == "Occupancy Sensor 07B7 Illuminance"
    assert illum_sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "lx"
    assert illum_sensor_attr[ATTR_STATE_CLASS] == "measurement"

    illum_sensor = hass.states.get("sensor.occupancy_sensor_07b7_duration_detected")
    illum_sensor_attr = illum_sensor.attributes
    assert illum_sensor.state == "2"
    assert (
        illum_sensor_attr[ATTR_FRIENDLY_NAME]
        == "Occupancy Sensor 07B7 Duration detected"
    )
    assert illum_sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "min"
    assert illum_sensor_attr[ATTR_STATE_CLASS] == "measurement"

    illum_sensor = hass.states.get("sensor.occupancy_sensor_07b7_duration_cleared")
    illum_sensor_attr = illum_sensor.attributes
    assert illum_sensor.state == "2"
    assert (
        illum_sensor_attr[ATTR_FRIENDLY_NAME]
        == "Occupancy Sensor 07B7 Duration cleared"
    )
    assert illum_sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "min"
    assert illum_sensor_attr[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.data[CONF_SLEEPY_DEVICE] is True