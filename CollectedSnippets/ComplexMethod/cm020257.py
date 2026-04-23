async def _test_multiple_numeric_observations(
    hass: HomeAssistant, issue_registry: ir.IssueRegistry
) -> None:
    """Common test code for multiple numeric state observations."""
    hass.states.async_set("sensor.test_temp", -5)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.nice_day")

    for attrs in state.attributes.values():
        json.dumps(attrs)
    assert state.attributes.get("occurred_observation_entities") == ["sensor.test_temp"]
    assert state.attributes.get("probability") == 0.1

    # No observations made so probability should be the prior
    assert state.attributes.get("occurred_observation_entities") == ["sensor.test_temp"]
    assert abs(state.attributes.get("probability") - 0.09677) < 0.01
    # A = binary_sensor.nice_day being TRUE
    # B = sensor.test_temp in the range (, 0]
    # Bayes theorum  is P(A|B) = P(B|A) * P(A) / ( P(B|A)*P(A) + P(B|~A)*P(~A) ).
    # Where P(B|A) is prob_given_true and P(B|~A) is prob_given_false
    # Calculated using P(A) = 0.3, P(B|A) = 0.05, P(B|~A) = 0.2 -> 0.09677
    # Because >1 range is defined for sensor.test_temp we should not infer anything from the
    # ranges not observed
    assert state.state == "off"

    hass.states.async_set("sensor.test_temp", 5)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.nice_day")

    assert state.attributes.get("occurred_observation_entities") == ["sensor.test_temp"]
    assert abs(state.attributes.get("probability") - 0.14634146) < 0.01
    # A = binary_sensor.nice_day being TRUE
    # B = sensor.test_temp in the range (0, 10]
    # Bayes theorum  is P(A|B) = P(B|A) * P(A) / ( P(B|A)*P(A) + P(B|~A)*P(~A) ).
    # Where P(B|A) is prob_given_true and P(B|~A) is prob_given_false
    # Calculated using P(A) = 0.3, P(B|A) = 0.1, P(B|~A) = 0.25 -> 0.14634146
    # Because >1 range is defined for sensor.test_temp we should not infer anything from the
    # ranges not observed

    assert state.state == "off"

    hass.states.async_set("sensor.test_temp", 12)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.nice_day")
    assert abs(state.attributes.get("probability") - 0.19672131) < 0.01
    # A = binary_sensor.nice_day being TRUE
    # B = sensor.test_temp in the range (10, 15]
    # Bayes theorum  is P(A|B) = P(B|A) * P(A) / ( P(B|A)*P(A) + P(B|~A)*P(~A) ).
    # Where P(B|A) is prob_given_true and P(B|~A) is prob_given_false
    # Calculated using P(A) = 0.3, P(B|A) = 0.2, P(B|~A) = 0.35 -> 0.19672131
    # Because >1 range is defined for sensor.test_temp we should not infer anything from the
    # ranges not observed

    assert state.state == "off"

    hass.states.async_set("sensor.test_temp", 22)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.nice_day")
    assert abs(state.attributes.get("probability") - 0.58823529) < 0.01
    # A = binary_sensor.nice_day being TRUE
    # B = sensor.test_temp in the range (15, 25]
    # Bayes theorum  is P(A|B) = P(B|A) * P(A) / ( P(B|A)*P(A) + P(B|~A)*P(~A) ).
    # Where P(B|A) is prob_given_true and P(B|~A) is prob_given_false
    # Calculated using P(A) = 0.3, P(B|A) = 0.5, P(B|~A) = 0.15 -> 0.58823529
    # Because >1 range is defined for sensor.test_temp we should not infer anything from the
    # ranges not observed

    assert state.state == "on"

    hass.states.async_set("sensor.test_temp", 30)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.nice_day")
    assert abs(state.attributes.get("probability") - 0.562500) < 0.01
    # A = binary_sensor.nice_day being TRUE
    # B = sensor.test_temp in the range (25, ]
    # Bayes theorum  is P(A|B) = P(B|A) * P(A) / ( P(B|A)*P(A) + P(B|~A)*P(~A) ).
    # Where P(B|A) is prob_given_true and P(B|~A) is prob_given_false
    # Calculated using P(A) = 0.3, P(B|A) = 0.15, P(B|~A) = 0.05 -> 0.562500
    # Because >1 range is defined for sensor.test_temp we should not infer anything from the
    # ranges not observed

    assert state.state == "on"

    # Edge cases
    # if on a threshold only one observation should be included and not both
    hass.states.async_set("sensor.test_temp", 15)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.nice_day")

    assert state.attributes.get("occurred_observation_entities") == ["sensor.test_temp"]

    assert abs(state.attributes.get("probability") - 0.19672131) < 0.01
    # Where there are multi numeric ranges when on the threshold, use below
    # A = binary_sensor.nice_day being TRUE
    # B = sensor.test_temp in the range (10, 15]
    # Bayes theorum  is P(A|B) = P(B|A) * P(A) / ( P(B|A)*P(A) + P(B|~A)*P(~A) ).
    # Where P(B|A) is prob_given_true and P(B|~A) is prob_given_false
    # Calculated using P(A) = 0.3, P(B|A) = 0.2, P(B|~A) = 0.35 -> 0.19672131
    # Because >1 range is defined for sensor.test_temp we should not infer anything from the
    # ranges not observed

    assert state.state == "off"

    assert len(issue_registry.issues) == 0
    assert state.attributes.get("observations")[0]["platform"] == "numeric_state"

    hass.states.async_set("sensor.test_temp", "badstate")
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.nice_day")

    assert state.attributes.get("occurred_observation_entities") == []
    assert state.state == "off"

    hass.states.async_set("sensor.test_temp", STATE_UNAVAILABLE)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.nice_day")

    assert state.attributes.get("occurred_observation_entities") == []
    assert state.state == "off"

    hass.states.async_set("sensor.test_temp", STATE_UNKNOWN)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.nice_day")

    assert state.attributes.get("occurred_observation_entities") == []
    assert state.state == "off"