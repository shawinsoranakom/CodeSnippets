async def test_unavailable_sensor_recovery(hass: HomeAssistant, new_state: str) -> None:
    """Test recovery when sensor becomes unavailable/unknown and then available again."""
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

    # Set indoor temp to unavailable
    hass.states.async_set(
        "test.indoortemp",
        new_state,
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    await hass.async_block_till_done()
    moldind = hass.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == STATE_UNAVAILABLE
    assert moldind.attributes.get(ATTR_DEWPOINT) is None
    assert moldind.attributes.get(ATTR_CRITICAL_TEMP) is None

    # Recover by setting a valid value - should immediately work
    hass.states.async_set(
        "test.indoortemp", "20", {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    )
    await hass.async_block_till_done()
    moldind = hass.states.get("sensor.mold_indicator")
    assert moldind
    assert moldind.state == "68"
    assert moldind.attributes.get(ATTR_DEWPOINT) is not None
    assert moldind.attributes.get(ATTR_CRITICAL_TEMP) is not None