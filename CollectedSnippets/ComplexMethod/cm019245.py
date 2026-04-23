async def test_state(hass: HomeAssistant) -> None:
    """Test handling of state.

    The group state is unknown if all group members are unknown or unavailable.
    Otherwise, the group state is opening if at least one group member is opening.
    Otherwise, the group state is closing if at least one group member is closing.
    Otherwise, the group state is open if at least one group member is open.
    Otherwise, the group state is closed.
    """
    state = hass.states.get(VALVE_GROUP)
    # No entity has a valid state -> group state unavailable
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes[ATTR_FRIENDLY_NAME] == DEFAULT_NAME
    assert ATTR_ENTITY_ID not in state.attributes
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert ATTR_CURRENT_POSITION not in state.attributes

    # Test group members exposed as attribute
    hass.states.async_set(DEMO_VALVE1, STATE_UNKNOWN, {})
    await hass.async_block_till_done()
    state = hass.states.get(VALVE_GROUP)
    assert state.attributes[ATTR_ENTITY_ID] == [
        DEMO_VALVE1,
        DEMO_VALVE2,
        DEMO_VALVE_POS1,
        DEMO_VALVE_POS2,
    ]

    # The group state is unavailable if all group members are unavailable.
    hass.states.async_set(DEMO_VALVE1, STATE_UNAVAILABLE, {})
    hass.states.async_set(DEMO_VALVE_POS1, STATE_UNAVAILABLE, {})
    hass.states.async_set(DEMO_VALVE_POS2, STATE_UNAVAILABLE, {})
    hass.states.async_set(DEMO_VALVE2, STATE_UNAVAILABLE, {})
    await hass.async_block_till_done()
    state = hass.states.get(VALVE_GROUP)
    assert state.state == STATE_UNAVAILABLE

    # The group state is unknown if all group members are unknown or unavailable.
    for state_1 in (STATE_UNAVAILABLE, STATE_UNKNOWN):
        for state_2 in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            for state_3 in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                hass.states.async_set(DEMO_VALVE1, state_1, {})
                hass.states.async_set(DEMO_VALVE_POS1, state_2, {})
                hass.states.async_set(DEMO_VALVE_POS2, state_3, {})
                hass.states.async_set(DEMO_VALVE2, STATE_UNKNOWN, {})
                await hass.async_block_till_done()
                state = hass.states.get(VALVE_GROUP)
                assert state.state == STATE_UNKNOWN

    # At least one member opening -> group opening
    for state_1 in (
        ValveState.CLOSED,
        ValveState.CLOSING,
        ValveState.OPEN,
        ValveState.OPENING,
        STATE_UNAVAILABLE,
        STATE_UNKNOWN,
    ):
        for state_2 in (
            ValveState.CLOSED,
            ValveState.CLOSING,
            ValveState.OPEN,
            ValveState.OPENING,
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        ):
            for state_3 in (
                ValveState.CLOSED,
                ValveState.CLOSING,
                ValveState.OPEN,
                ValveState.OPENING,
                STATE_UNAVAILABLE,
                STATE_UNKNOWN,
            ):
                hass.states.async_set(DEMO_VALVE1, state_1, {})
                hass.states.async_set(DEMO_VALVE_POS1, state_2, {})
                hass.states.async_set(DEMO_VALVE_POS2, state_3, {})
                hass.states.async_set(DEMO_VALVE2, ValveState.OPENING, {})
                await hass.async_block_till_done()
                state = hass.states.get(VALVE_GROUP)
                assert state.state == ValveState.OPENING

    # At least one member closing -> group closing
    for state_1 in (
        ValveState.CLOSED,
        ValveState.CLOSING,
        ValveState.OPEN,
        STATE_UNAVAILABLE,
        STATE_UNKNOWN,
    ):
        for state_2 in (
            ValveState.CLOSED,
            ValveState.CLOSING,
            ValveState.OPEN,
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        ):
            for state_3 in (
                ValveState.CLOSED,
                ValveState.CLOSING,
                ValveState.OPEN,
                STATE_UNAVAILABLE,
                STATE_UNKNOWN,
            ):
                hass.states.async_set(DEMO_VALVE1, state_1, {})
                hass.states.async_set(DEMO_VALVE_POS1, state_2, {})
                hass.states.async_set(DEMO_VALVE_POS2, state_3, {})
                hass.states.async_set(DEMO_VALVE2, ValveState.CLOSING, {})
                await hass.async_block_till_done()
                state = hass.states.get(VALVE_GROUP)
                assert state.state == ValveState.CLOSING

    # At least one member open -> group open
    for state_1 in (
        ValveState.CLOSED,
        ValveState.OPEN,
        STATE_UNAVAILABLE,
        STATE_UNKNOWN,
    ):
        for state_2 in (
            ValveState.CLOSED,
            ValveState.OPEN,
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        ):
            for state_3 in (
                ValveState.CLOSED,
                ValveState.OPEN,
                STATE_UNAVAILABLE,
                STATE_UNKNOWN,
            ):
                hass.states.async_set(DEMO_VALVE1, state_1, {})
                hass.states.async_set(DEMO_VALVE_POS1, state_2, {})
                hass.states.async_set(DEMO_VALVE_POS2, state_3, {})
                hass.states.async_set(DEMO_VALVE2, ValveState.OPEN, {})
                await hass.async_block_till_done()
                state = hass.states.get(VALVE_GROUP)
                assert state.state == ValveState.OPEN

    # At least one member closed -> group closed
    for state_1 in (ValveState.CLOSED, STATE_UNAVAILABLE, STATE_UNKNOWN):
        for state_2 in (ValveState.CLOSED, STATE_UNAVAILABLE, STATE_UNKNOWN):
            for state_3 in (ValveState.CLOSED, STATE_UNAVAILABLE, STATE_UNKNOWN):
                hass.states.async_set(DEMO_VALVE1, state_1, {})
                hass.states.async_set(DEMO_VALVE_POS1, state_2, {})
                hass.states.async_set(DEMO_VALVE_POS2, state_3, {})
                hass.states.async_set(DEMO_VALVE2, ValveState.CLOSED, {})
                await hass.async_block_till_done()
                state = hass.states.get(VALVE_GROUP)
                assert state.state == ValveState.CLOSED

    # All group members removed from the state machine -> unavailable
    hass.states.async_remove(DEMO_VALVE1)
    hass.states.async_remove(DEMO_VALVE_POS1)
    hass.states.async_remove(DEMO_VALVE_POS2)
    hass.states.async_remove(DEMO_VALVE2)
    await hass.async_block_till_done()
    state = hass.states.get(VALVE_GROUP)
    assert state.state == STATE_UNAVAILABLE