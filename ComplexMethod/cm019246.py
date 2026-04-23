async def test_attributes(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test handling of state attributes."""
    state = hass.states.get(VALVE_GROUP)
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes[ATTR_FRIENDLY_NAME] == DEFAULT_NAME
    assert ATTR_ENTITY_ID not in state.attributes
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert ATTR_CURRENT_POSITION not in state.attributes

    # Set entity as closed
    hass.states.async_set(DEMO_VALVE1, ValveState.CLOSED, {})
    await hass.async_block_till_done()

    state = hass.states.get(VALVE_GROUP)
    assert state.state == ValveState.CLOSED
    assert state.attributes[ATTR_ENTITY_ID] == [
        DEMO_VALVE1,
        DEMO_VALVE2,
        DEMO_VALVE_POS1,
        DEMO_VALVE_POS2,
    ]

    # Set entity as opening
    hass.states.async_set(DEMO_VALVE1, ValveState.OPENING, {})
    await hass.async_block_till_done()

    state = hass.states.get(VALVE_GROUP)
    assert state.state == ValveState.OPENING

    # Set entity as closing
    hass.states.async_set(DEMO_VALVE1, ValveState.CLOSING, {})
    await hass.async_block_till_done()

    state = hass.states.get(VALVE_GROUP)
    assert state.state == ValveState.CLOSING

    # Set entity as unknown again
    hass.states.async_set(DEMO_VALVE1, STATE_UNKNOWN, {})
    await hass.async_block_till_done()

    state = hass.states.get(VALVE_GROUP)
    assert state.state == STATE_UNKNOWN

    # Add Entity that supports open / close / stop
    hass.states.async_set(DEMO_VALVE1, ValveState.OPEN, {ATTR_SUPPORTED_FEATURES: 11})
    await hass.async_block_till_done()

    state = hass.states.get(VALVE_GROUP)
    assert state.state == ValveState.OPEN
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 11
    assert ATTR_CURRENT_POSITION not in state.attributes

    # Add Entity that supports set_valve_position
    hass.states.async_set(
        DEMO_VALVE_POS1,
        ValveState.OPEN,
        {ATTR_SUPPORTED_FEATURES: 4, ATTR_CURRENT_POSITION: 70},
    )
    await hass.async_block_till_done()

    state = hass.states.get(VALVE_GROUP)
    assert state.state == ValveState.OPEN
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 15
    assert state.attributes[ATTR_CURRENT_POSITION] == 70

    ### Test state when group members have different states ###

    # Valves
    hass.states.async_remove(DEMO_VALVE_POS1)
    hass.states.async_remove(DEMO_VALVE_POS2)
    await hass.async_block_till_done()

    state = hass.states.get(VALVE_GROUP)
    assert state.state == ValveState.OPEN
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 11
    assert ATTR_CURRENT_POSITION not in state.attributes

    # Test entity registry integration
    entry = entity_registry.async_get(VALVE_GROUP)
    assert entry
    assert entry.unique_id == "unique_identifier"