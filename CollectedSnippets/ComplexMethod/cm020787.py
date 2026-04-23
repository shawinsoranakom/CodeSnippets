async def test_invalidhum(hass: HomeAssistant) -> None:
    """Test invalid sensor values."""
    hass.states.async_set(
        "test.indoortemp", "10", {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    )
    hass.states.async_set(
        "test.outdoortemp", "10", {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    )
    hass.states.async_set(
        "test.indoorhumidity", "-1", {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )

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
    moldind = hass.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == STATE_UNAVAILABLE
    assert moldind.attributes.get(ATTR_DEWPOINT) is None
    assert moldind.attributes.get(ATTR_CRITICAL_TEMP) is None

    hass.states.async_set(
        "test.indoorhumidity", "A", {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )
    await hass.async_block_till_done()
    moldind = hass.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == STATE_UNAVAILABLE
    assert moldind.attributes.get(ATTR_DEWPOINT) is None
    assert moldind.attributes.get(ATTR_CRITICAL_TEMP) is None

    hass.states.async_set(
        "test.indoorhumidity",
        "10",
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    await hass.async_block_till_done()
    moldind = hass.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == STATE_UNAVAILABLE
    assert moldind.attributes.get(ATTR_DEWPOINT) is None
    assert moldind.attributes.get(ATTR_CRITICAL_TEMP) is None