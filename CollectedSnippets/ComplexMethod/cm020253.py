async def _test_sensor_numeric_state(
    hass: HomeAssistant, issue_registry: ir.IssueRegistry
) -> None:
    hass.states.async_set("sensor.test_monitored", 6)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_binary")

    assert state.attributes.get("occurred_observation_entities") == [
        "sensor.test_monitored"
    ]
    assert abs(state.attributes.get("probability") - 0.304) < 0.01
    # A = sensor.test_binary being ON
    # B = sensor.test_monitored in the range [5, 10]
    # Bayes theorum  is P(A|B) = P(B|A) * P(A) / P(B|A)*P(A) + P(B|~A)*P(~A).
    # Where P(B|A) is prob_given_true and P(B|~A) is prob_given_false
    # Calculated using P(A) = 0.2, P(B|A) = 0.7, P(B|~A) = 0.4 -> 0.30

    hass.states.async_set("sensor.test_monitored", 4)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_binary")

    assert state.attributes.get("occurred_observation_entities") == [
        "sensor.test_monitored"
    ]
    assert abs(state.attributes.get("probability") - 0.111) < 0.01
    # As abve but since the value is equal to 4 then this is a negative observation (~B) where P(~B) == 1 - P(B) because B is binary
    # We therefore want to calculate P(A|~B) so we use P(~B|A) (1-0.7) and P(~B|~A) (1-0.4)
    # Calculated using bayes theorum where P(A) = 0.2, P(~B|A) = 1-0.7 (as negative observation), P(~B|notA) = 1-0.4 -> 0.11

    assert state.state == "off"

    hass.states.async_set("sensor.test_monitored", 6)
    await hass.async_block_till_done()
    hass.states.async_set("sensor.test_monitored1", 6)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_binary")
    assert state.attributes.get("observations")[0]["prob_given_true"] == 0.7
    assert state.attributes.get("observations")[1]["prob_given_true"] == 0.9
    assert state.attributes.get("observations")[1]["prob_given_false"] == 0.2
    assert abs(state.attributes.get("probability") - 0.663) < 0.01
    # Here we have two positive observations as both are in range. We do a 2-step bayes. The output of the first is used as the (updated) prior in the second.
    # 1st step P(A) = 0.2, P(B|A) = 0.7, P(B|notA) = 0.4 -> 0.304
    # 2nd update: P(A) = 0.304, P(B|A) = 0.9, P(B|notA) = 0.2 -> 0.663

    assert state.state == "on"

    hass.states.async_set("sensor.test_monitored1", 0)
    await hass.async_block_till_done()
    hass.states.async_set("sensor.test_monitored", 4)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_binary")
    assert abs(state.attributes.get("probability") - 0.0153) < 0.01
    # Calculated using bayes theorum where P(A) = 0.2, P(~B|A) = 0.3, P(~B|notA) = 0.6 -> 0.11
    # 2nd update: P(A) = 0.111, P(~B|A) = 0.1, P(~B|notA) = 0.8

    assert state.state == "off"

    hass.states.async_set("sensor.test_monitored", 15)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_binary")

    assert state.state == "off"

    assert len(issue_registry.issues) == 0