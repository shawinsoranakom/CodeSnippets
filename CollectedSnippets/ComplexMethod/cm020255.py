async def _test_sensor_value_template(hass: HomeAssistant) -> None:
    hass.states.async_set("sensor.test_monitored", "on")

    state = hass.states.get("binary_sensor.test_binary")

    assert state.attributes.get("occurred_observation_entities") == []
    assert abs(0.0769 - state.attributes.get("probability")) < 0.01
    # Calculated using bayes theorum where P(A) = 0.2, P(~B|A) = 0.2 (as negative observation), P(~B|notA) = 0.6

    assert state.state == "off"

    hass.states.async_set("sensor.test_monitored", "off")
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_binary")
    assert state.attributes.get("observations")[0]["prob_given_true"] == 0.8
    assert state.attributes.get("observations")[0]["prob_given_false"] == 0.4
    assert abs(0.33333 - state.attributes.get("probability")) < 0.01
    # Calculated using bayes theorum where P(A) = 0.2, P(B|A) = 0.8, P(B|notA) = 0.4

    assert state.state == "on"

    hass.states.async_set("sensor.test_monitored", "on")
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_binary")
    assert abs(0.076923 - state.attributes.get("probability")) < 0.01
    # Calculated using bayes theorum where P(A) = 0.2, P(~B|A) = 0.2 (as negative observation), P(~B|notA) = 0.6

    assert state.state == "off"