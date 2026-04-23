async def test_numeric_state_using_input_number(hass: HomeAssistant) -> None:
    """Test numeric_state conditions using input_number entities."""
    hass.states.async_set("number.low", 10)
    await async_setup_component(
        hass,
        "input_number",
        {
            "input_number": {
                "high": {"min": 0, "max": 255, "initial": 100},
            }
        },
    )

    config = {
        "condition": "and",
        "conditions": [
            {
                "condition": "numeric_state",
                "entity_id": "sensor.temperature",
                "below": "input_number.high",
                "above": "number.low",
            },
        ],
    }
    config = cv.CONDITION_SCHEMA(config)
    config = await condition.async_validate_condition_config(hass, config)
    test = await condition.async_from_config(hass, config)

    hass.states.async_set("sensor.temperature", 42)
    assert test(hass)

    hass.states.async_set("sensor.temperature", 10)
    assert not test(hass)

    hass.states.async_set("sensor.temperature", 100)
    assert not test(hass)

    hass.states.async_set("input_number.high", "unknown")
    assert not test(hass)

    hass.states.async_set("input_number.high", "unavailable")
    assert not test(hass)

    await hass.services.async_call(
        "input_number",
        "set_value",
        {
            "entity_id": "input_number.high",
            "value": 101,
        },
        blocking=True,
    )
    assert test(hass)

    hass.states.async_set("number.low", "unknown")
    assert not test(hass)

    hass.states.async_set("number.low", "unavailable")
    assert not test(hass)

    with pytest.raises(ConditionError):
        condition.async_numeric_state(
            hass, entity="sensor.temperature", below="input_number.not_exist"
        )
    with pytest.raises(ConditionError):
        condition.async_numeric_state(
            hass, entity="sensor.temperature", above="input_number.not_exist"
        )