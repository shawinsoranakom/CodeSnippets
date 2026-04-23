async def test_methods_with_config(hass: HomeAssistant) -> None:
    """Test increment, decrement, and reset methods with configuration."""
    config = {
        DOMAIN: {
            "test": {
                CONF_NAME: "Hello World",
                CONF_INITIAL: 10,
                CONF_STEP: 5,
                CONF_MINIMUM: 5,
                CONF_MAXIMUM: 20,
            }
        }
    }

    assert await async_setup_component(hass, DOMAIN, config)

    entity_id = "counter.test"

    state = hass.states.get(entity_id)
    assert int(state.state) == 10

    async_increment(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert int(state.state) == 15

    async_increment(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert int(state.state) == 20

    async_decrement(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert int(state.state) == 15

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: entity_id,
            VALUE: 5,
        },
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.state == "5"

    with pytest.raises(
        ValueError, match=r"Value 25 for counter.test exceeding the maximum value of 20"
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_ENTITY_ID: entity_id,
                VALUE: 25,
            },
            blocking=True,
        )

    state = hass.states.get(entity_id)
    assert state.state == "5"

    with pytest.raises(
        ValueError, match=r"Value 0 for counter.test exceeding the minimum value of 5"
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_ENTITY_ID: entity_id,
                VALUE: 0,
            },
            blocking=True,
        )

    state = hass.states.get(entity_id)
    assert state.state == "5"

    with pytest.raises(
        ValueError,
        match=r"Value 6 for counter.test is not a multiple of the step size 5",
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_ENTITY_ID: entity_id,
                VALUE: 6,
            },
            blocking=True,
        )

    state = hass.states.get(entity_id)
    assert state.state == "5"