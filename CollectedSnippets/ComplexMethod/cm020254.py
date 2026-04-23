async def _test_sensor_state(hass: HomeAssistant, prior: float) -> None:
    """Common test code for state-based observations."""
    hass.states.async_set("sensor.test_monitored", "on")
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.test_binary")

    assert state.attributes.get("occurred_observation_entities") == [
        "sensor.test_monitored"
    ]
    assert state.attributes.get("observations")[0]["prob_given_true"] == 0.8
    assert state.attributes.get("observations")[0]["prob_given_false"] == 0.4
    assert abs(0.0769 - state.attributes.get("probability")) < 0.01
    # Calculated using bayes theorum where P(A) = 0.2, P(~B|A) = 0.2 (as negative observation), P(~B|notA) = 0.6
    assert state.state == "off"

    hass.states.async_set("sensor.test_monitored", "off")
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.test_binary")

    assert state.attributes.get("occurred_observation_entities") == [
        "sensor.test_monitored"
    ]
    assert abs(0.33 - state.attributes.get("probability")) < 0.01
    # Calculated using bayes theorum where P(A) = 0.2, P(~B|A) = 0.8 (as negative observation), P(~B|notA) = 0.4
    assert state.state == "on"

    hass.states.async_remove("sensor.test_monitored")
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.test_binary")

    assert state.attributes.get("occurred_observation_entities") == []
    assert abs(prior - state.attributes.get("probability")) < 0.01
    assert state.state == "off"

    hass.states.async_set("sensor.test_monitored", STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.test_binary")

    assert state.attributes.get("occurred_observation_entities") == []
    assert abs(prior - state.attributes.get("probability")) < 0.01
    assert state.state == "off"

    hass.states.async_set("sensor.test_monitored", STATE_UNKNOWN)
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.test_binary")

    assert state.attributes.get("occurred_observation_entities") == []
    assert abs(prior - state.attributes.get("probability")) < 0.01
    assert state.state == "off"