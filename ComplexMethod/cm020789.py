async def test_unknown_sensor(hass: HomeAssistant) -> None:
    """Test the sensor_changed function."""
    assert await async_setup_component(
        hass,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "mold_indicator",
                "indoor_temp_sensor": "test.indoortemp",
                "outdoor_temp_sensor": "test.outdoortemp",
                "indoor_humidity_sensor": "test.indoorhumidity",
                "calibration_factor": 2.0,
            }
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    hass.states.async_set(
        "test.indoortemp",
        STATE_UNKNOWN,
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    await hass.async_block_till_done()
    moldind = hass.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == STATE_UNAVAILABLE
    assert moldind.attributes.get(ATTR_DEWPOINT) is None
    assert moldind.attributes.get(ATTR_CRITICAL_TEMP) is None

    hass.states.async_set(
        "test.indoortemp", "30", {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    )
    hass.states.async_set(
        "test.outdoortemp",
        STATE_UNKNOWN,
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    await hass.async_block_till_done()
    moldind = hass.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == STATE_UNAVAILABLE
    assert moldind.attributes.get(ATTR_DEWPOINT) is None
    assert moldind.attributes.get(ATTR_CRITICAL_TEMP) is None

    hass.states.async_set(
        "test.outdoortemp", "25", {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    )
    hass.states.async_set(
        "test.indoorhumidity",
        STATE_UNKNOWN,
        {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE},
    )
    await hass.async_block_till_done()
    moldind = hass.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == STATE_UNAVAILABLE
    assert moldind.attributes.get(ATTR_DEWPOINT) is None
    assert moldind.attributes.get(ATTR_CRITICAL_TEMP) is None

    hass.states.async_set(
        "test.indoorhumidity", "20", {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )
    await hass.async_block_till_done()
    moldind = hass.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == "23"

    dewpoint = moldind.attributes.get(ATTR_DEWPOINT)
    assert dewpoint
    assert dewpoint > 4.5
    assert dewpoint < 4.6

    esttemp = moldind.attributes.get(ATTR_CRITICAL_TEMP)
    assert esttemp
    assert esttemp == 27.5