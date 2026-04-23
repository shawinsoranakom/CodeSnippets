async def test_discover_sensor(hass: HomeAssistant, rfxtrx_automatic) -> None:
    """Test with discovery of sensor."""
    rfxtrx = rfxtrx_automatic

    # 1
    await rfxtrx.signal("0a520801070100b81b0279")
    base_id = "sensor.wt260_wt260h_wt440h_wt450_wt450h_07_01"

    state = hass.states.get(f"{base_id}_humidity")
    assert state
    assert state.state == "27"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PERCENTAGE

    state = hass.states.get(f"{base_id}_humidity_status")
    assert state
    assert state.state == "normal"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None

    state = hass.states.get(f"{base_id}_signal_strength")
    assert state
    assert state.state == "-64"
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    )

    state = hass.states.get(f"{base_id}_temperature")
    assert state
    assert state.state == "18.4"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS

    state = hass.states.get(f"{base_id}_battery")
    assert state
    assert state.state == "100"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PERCENTAGE

    # 2
    await rfxtrx.signal("0a52080405020095240279")
    base_id = "sensor.wt260_wt260h_wt440h_wt450_wt450h_05_02"
    state = hass.states.get(f"{base_id}_humidity")

    assert state
    assert state.state == "36"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PERCENTAGE

    state = hass.states.get(f"{base_id}_humidity_status")
    assert state
    assert state.state == "normal"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None

    state = hass.states.get(f"{base_id}_signal_strength")
    assert state
    assert state.state == "-64"
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    )

    state = hass.states.get(f"{base_id}_temperature")
    assert state
    assert state.state == "14.9"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS

    state = hass.states.get(f"{base_id}_battery")
    assert state
    assert state.state == "100"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PERCENTAGE

    # 1 Update
    await rfxtrx.signal("0a52085e070100b31b0279")
    base_id = "sensor.wt260_wt260h_wt440h_wt450_wt450h_07_01"

    state = hass.states.get(f"{base_id}_humidity")
    assert state
    assert state.state == "27"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PERCENTAGE

    state = hass.states.get(f"{base_id}_humidity_status")
    assert state
    assert state.state == "normal"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None

    state = hass.states.get(f"{base_id}_signal_strength")
    assert state
    assert state.state == "-64"
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    )

    state = hass.states.get(f"{base_id}_temperature")
    assert state
    assert state.state == "17.9"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS

    state = hass.states.get(f"{base_id}_battery")
    assert state
    assert state.state == "100"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PERCENTAGE

    assert len(hass.states.async_all()) == 10