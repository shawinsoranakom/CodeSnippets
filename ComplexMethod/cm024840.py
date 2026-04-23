async def test_state_using_input_entities(hass: HomeAssistant) -> None:
    """Test state conditions using input_* entities."""
    await async_setup_component(
        hass,
        "input_text",
        {
            "input_text": {
                "hello": {"initial": "goodbye"},
            }
        },
    )

    await async_setup_component(
        hass,
        "input_select",
        {
            "input_select": {
                "hello": {"options": ["cya", "goodbye", "welcome"], "initial": "cya"},
            }
        },
    )

    config = {
        "condition": "and",
        "conditions": [
            {
                "condition": "state",
                "entity_id": "sensor.salut",
                "state": [
                    "input_text.hello",
                    "input_select.hello",
                    "salut",
                ],
            },
        ],
    }
    config = cv.CONDITION_SCHEMA(config)
    config = await condition.async_validate_condition_config(hass, config)
    test = await condition.async_from_config(hass, config)

    hass.states.async_set("sensor.salut", "goodbye")
    assert test(hass)

    hass.states.async_set("sensor.salut", "salut")
    assert test(hass)

    hass.states.async_set("sensor.salut", "hello")
    assert not test(hass)

    await hass.services.async_call(
        "input_text",
        "set_value",
        {
            "entity_id": "input_text.hello",
            "value": "hi",
        },
        blocking=True,
    )
    assert not test(hass)

    hass.states.async_set("sensor.salut", "hi")
    assert test(hass)

    hass.states.async_set("sensor.salut", "cya")
    assert test(hass)

    await hass.services.async_call(
        "input_select",
        "select_option",
        {
            "entity_id": "input_select.hello",
            "option": "welcome",
        },
        blocking=True,
    )
    assert not test(hass)

    hass.states.async_set("sensor.salut", "welcome")
    assert test(hass)