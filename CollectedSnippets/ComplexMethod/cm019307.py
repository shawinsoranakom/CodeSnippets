async def test_state(hass: HomeAssistant) -> None:
    """Test handling of state.

    The group state is unknown if all group members are unknown or unavailable.
    Otherwise, the group state is opening if at least one group member is opening.
    Otherwise, the group state is closing if at least one group member is closing.
    Otherwise, the group state is open if at least one group member is open.
    Otherwise, the group state is closed.
    """
    state = hass.states.get(COVER_GROUP)
    # No entity has a valid state -> group state unavailable
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes[ATTR_FRIENDLY_NAME] == DEFAULT_NAME
    assert ATTR_ENTITY_ID not in state.attributes
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert ATTR_CURRENT_POSITION not in state.attributes
    assert ATTR_CURRENT_TILT_POSITION not in state.attributes

    # Test group members exposed as attribute
    hass.states.async_set(DEMO_COVER, STATE_UNKNOWN, {})
    await hass.async_block_till_done()
    state = hass.states.get(COVER_GROUP)
    assert state.attributes[ATTR_ENTITY_ID] == [
        DEMO_COVER,
        DEMO_COVER_POS,
        DEMO_COVER_TILT,
        DEMO_TILT,
    ]

    # The group state is unavailable if all group members are unavailable.
    hass.states.async_set(DEMO_COVER, STATE_UNAVAILABLE, {})
    hass.states.async_set(DEMO_COVER_POS, STATE_UNAVAILABLE, {})
    hass.states.async_set(DEMO_COVER_TILT, STATE_UNAVAILABLE, {})
    hass.states.async_set(DEMO_TILT, STATE_UNAVAILABLE, {})
    await hass.async_block_till_done()
    state = hass.states.get(COVER_GROUP)
    assert state.state == STATE_UNAVAILABLE

    # The group state is unknown if all group members are unknown or unavailable.
    for state_1 in (STATE_UNAVAILABLE, STATE_UNKNOWN):
        for state_2 in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            for state_3 in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                hass.states.async_set(DEMO_COVER, state_1, {})
                hass.states.async_set(DEMO_COVER_POS, state_2, {})
                hass.states.async_set(DEMO_COVER_TILT, state_3, {})
                hass.states.async_set(DEMO_TILT, STATE_UNKNOWN, {})
                await hass.async_block_till_done()
                state = hass.states.get(COVER_GROUP)
                assert state.state == STATE_UNKNOWN

    # At least one member opening -> group opening
    for state_1 in (
        CoverState.CLOSED,
        CoverState.CLOSING,
        CoverState.OPEN,
        CoverState.OPENING,
        STATE_UNAVAILABLE,
        STATE_UNKNOWN,
    ):
        for state_2 in (
            CoverState.CLOSED,
            CoverState.CLOSING,
            CoverState.OPEN,
            CoverState.OPENING,
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        ):
            for state_3 in (
                CoverState.CLOSED,
                CoverState.CLOSING,
                CoverState.OPEN,
                CoverState.OPENING,
                STATE_UNAVAILABLE,
                STATE_UNKNOWN,
            ):
                hass.states.async_set(DEMO_COVER, state_1, {})
                hass.states.async_set(DEMO_COVER_POS, state_2, {})
                hass.states.async_set(DEMO_COVER_TILT, state_3, {})
                hass.states.async_set(DEMO_TILT, CoverState.OPENING, {})
                await hass.async_block_till_done()
                state = hass.states.get(COVER_GROUP)
                assert state.state == CoverState.OPENING

    # At least one member closing -> group closing
    for state_1 in (
        CoverState.CLOSED,
        CoverState.CLOSING,
        CoverState.OPEN,
        STATE_UNAVAILABLE,
        STATE_UNKNOWN,
    ):
        for state_2 in (
            CoverState.CLOSED,
            CoverState.CLOSING,
            CoverState.OPEN,
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        ):
            for state_3 in (
                CoverState.CLOSED,
                CoverState.CLOSING,
                CoverState.OPEN,
                STATE_UNAVAILABLE,
                STATE_UNKNOWN,
            ):
                hass.states.async_set(DEMO_COVER, state_1, {})
                hass.states.async_set(DEMO_COVER_POS, state_2, {})
                hass.states.async_set(DEMO_COVER_TILT, state_3, {})
                hass.states.async_set(DEMO_TILT, CoverState.CLOSING, {})
                await hass.async_block_till_done()
                state = hass.states.get(COVER_GROUP)
                assert state.state == CoverState.CLOSING

    # At least one member open -> group open
    for state_1 in (
        CoverState.CLOSED,
        CoverState.OPEN,
        STATE_UNAVAILABLE,
        STATE_UNKNOWN,
    ):
        for state_2 in (
            CoverState.CLOSED,
            CoverState.OPEN,
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        ):
            for state_3 in (
                CoverState.CLOSED,
                CoverState.OPEN,
                STATE_UNAVAILABLE,
                STATE_UNKNOWN,
            ):
                hass.states.async_set(DEMO_COVER, state_1, {})
                hass.states.async_set(DEMO_COVER_POS, state_2, {})
                hass.states.async_set(DEMO_COVER_TILT, state_3, {})
                hass.states.async_set(DEMO_TILT, CoverState.OPEN, {})
                await hass.async_block_till_done()
                state = hass.states.get(COVER_GROUP)
                assert state.state == CoverState.OPEN

    # At least one member closed -> group closed
    for state_1 in (CoverState.CLOSED, STATE_UNAVAILABLE, STATE_UNKNOWN):
        for state_2 in (CoverState.CLOSED, STATE_UNAVAILABLE, STATE_UNKNOWN):
            for state_3 in (CoverState.CLOSED, STATE_UNAVAILABLE, STATE_UNKNOWN):
                hass.states.async_set(DEMO_COVER, state_1, {})
                hass.states.async_set(DEMO_COVER_POS, state_2, {})
                hass.states.async_set(DEMO_COVER_TILT, state_3, {})
                hass.states.async_set(DEMO_TILT, CoverState.CLOSED, {})
                await hass.async_block_till_done()
                state = hass.states.get(COVER_GROUP)
                assert state.state == CoverState.CLOSED

    # All group members removed from the state machine -> unavailable
    hass.states.async_remove(DEMO_COVER)
    hass.states.async_remove(DEMO_COVER_POS)
    hass.states.async_remove(DEMO_COVER_TILT)
    hass.states.async_remove(DEMO_TILT)
    await hass.async_block_till_done()
    state = hass.states.get(COVER_GROUP)
    assert state.state == STATE_UNAVAILABLE