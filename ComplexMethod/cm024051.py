async def test_methods(hass: HomeAssistant) -> None:
    """Test increment, decrement, set value, and reset methods."""
    config = {DOMAIN: {"test_1": {}}}

    assert await async_setup_component(hass, DOMAIN, config)

    entity_id = "counter.test_1"

    state = hass.states.get(entity_id)
    assert int(state.state) == 0

    async_increment(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert int(state.state) == 1

    async_increment(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert int(state.state) == 2

    async_decrement(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert int(state.state) == 1

    async_reset(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert int(state.state) == 0

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