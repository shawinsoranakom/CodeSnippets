async def _test_multiple_observations(hass: HomeAssistant, prior: float) -> None:
    """Common test code for multiple observations."""
    hass.states.async_set("sensor.test_monitored", "off")
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_binary")

    for attrs in state.attributes.values():
        json.dumps(attrs)
    assert state.attributes.get("occurred_observation_entities") == []
    assert state.attributes.get("probability") == prior
    # probability should be the same as the prior as negative observations are ignored in multi-state

    assert state.state == "off"

    hass.states.async_set("sensor.test_monitored", "blue")
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_binary")

    assert state.attributes.get("occurred_observation_entities") == [
        "sensor.test_monitored"
    ]
    assert state.attributes.get("observations")[0]["prob_given_true"] == 0.8
    assert state.attributes.get("observations")[0]["prob_given_false"] == 0.4
    assert round(abs(0.33 - state.attributes.get("probability")), 7) == 0
    # Calculated using bayes theorum where P(A) = 0.2, P(B|A) = 0.8, P(B|notA) = 0.4

    assert state.state == "on"

    hass.states.async_set("sensor.test_monitored", "red")
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_binary")
    assert abs(0.076923 - state.attributes.get("probability")) < 0.01
    # Calculated using bayes theorum where P(A) = 0.2, P(B|A) = 0.2, P(B|notA) = 0.6

    assert state.state == "off"
    assert state.attributes.get("observations")[0]["platform"] == "state"
    assert state.attributes.get("observations")[1]["platform"] == "state"