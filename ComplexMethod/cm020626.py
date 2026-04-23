async def test_hhccjcy10_uuid(hass: HomeAssistant) -> None:
    """Test HHCCJCY10 UUID.

    This device uses a different UUID compared to the other Xiaomi sensors.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="DC:23:4D:E5:5B:FC",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    inject_bluetooth_service_info_bleak(hass, HHCCJCY10_SERVICE_INFO)

    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 5

    temp_sensor = hass.states.get("sensor.plant_sensor_5bfc_temperature")
    temp_sensor_attr = temp_sensor.attributes
    assert temp_sensor.state == "11.0"
    assert temp_sensor_attr[ATTR_FRIENDLY_NAME] == "Plant Sensor 5BFC Temperature"
    assert temp_sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "°C"
    assert temp_sensor_attr[ATTR_STATE_CLASS] == "measurement"

    illu_sensor = hass.states.get("sensor.plant_sensor_5bfc_illuminance")
    illu_sensor_attr = illu_sensor.attributes
    assert illu_sensor.state == "79012"
    assert illu_sensor_attr[ATTR_FRIENDLY_NAME] == "Plant Sensor 5BFC Illuminance"
    assert illu_sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "lx"
    assert illu_sensor_attr[ATTR_STATE_CLASS] == "measurement"

    cond_sensor = hass.states.get("sensor.plant_sensor_5bfc_conductivity")
    cond_sensor_attr = cond_sensor.attributes
    assert cond_sensor.state == "91"
    assert cond_sensor_attr[ATTR_FRIENDLY_NAME] == "Plant Sensor 5BFC Conductivity"
    assert cond_sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "μS/cm"
    assert cond_sensor_attr[ATTR_STATE_CLASS] == "measurement"

    moist_sensor = hass.states.get("sensor.plant_sensor_5bfc_moisture")
    moist_sensor_attr = moist_sensor.attributes
    assert moist_sensor.state == "14"
    assert moist_sensor_attr[ATTR_FRIENDLY_NAME] == "Plant Sensor 5BFC Moisture"
    assert moist_sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert moist_sensor_attr[ATTR_STATE_CLASS] == "measurement"

    bat_sensor = hass.states.get("sensor.plant_sensor_5bfc_battery")
    bat_sensor_attr = bat_sensor.attributes
    assert bat_sensor.state == "40"
    assert bat_sensor_attr[ATTR_FRIENDLY_NAME] == "Plant Sensor 5BFC Battery"
    assert bat_sensor_attr[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert bat_sensor_attr[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()