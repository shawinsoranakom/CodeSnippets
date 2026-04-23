async def test_all_sensors_unavailable_recovery(hass: HomeAssistant) -> None:
    """Test recovery when all sensors become unavailable and then available again."""
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

    # Initial state should be valid
    moldind = hass.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == "68"

    # Set all sensors to unavailable
    hass.states.async_set(
        "test.indoortemp",
        STATE_UNAVAILABLE,
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    hass.states.async_set(
        "test.outdoortemp",
        STATE_UNAVAILABLE,
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    hass.states.async_set(
        "test.indoorhumidity",
        STATE_UNAVAILABLE,
        {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE},
    )
    await hass.async_block_till_done()
    moldind = hass.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == STATE_UNAVAILABLE

    # Recover all sensors one by one
    hass.states.async_set(
        "test.indoortemp", "20", {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    )
    await hass.async_block_till_done()
    moldind = hass.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == STATE_UNAVAILABLE  # Still unavailable, needs all sensors

    hass.states.async_set(
        "test.outdoortemp", "10", {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    )
    await hass.async_block_till_done()
    moldind = hass.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == STATE_UNAVAILABLE  # Still unavailable, needs humidity

    hass.states.async_set(
        "test.indoorhumidity", "50", {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )
    await hass.async_block_till_done()
    moldind = hass.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == "68"  # Now should recover fully
    assert moldind.attributes.get(ATTR_DEWPOINT) is not None
    assert moldind.attributes.get(ATTR_CRITICAL_TEMP) is not None