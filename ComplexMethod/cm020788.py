async def test_calculation(hass: HomeAssistant) -> None:
    """Test the mold indicator internal calculations."""
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

    # assert dewpoint
    dewpoint = moldind.attributes.get(ATTR_DEWPOINT)
    assert dewpoint
    assert dewpoint > 9.2
    assert dewpoint < 9.3

    # assert temperature estimation
    esttemp = moldind.attributes.get(ATTR_CRITICAL_TEMP)
    assert esttemp
    assert esttemp > 14.9
    assert esttemp < 15.1

    # assert mold indicator value
    state = moldind.state
    assert state
    assert state == "68"