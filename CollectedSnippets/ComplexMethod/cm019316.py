async def test_direction_oscillating(hass: HomeAssistant) -> None:
    """Test handling of direction and oscillating attributes."""

    hass.states.async_set(
        LIVING_ROOM_FAN_ENTITY_ID,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FULL_SUPPORT_FEATURES,
            ATTR_OSCILLATING: True,
            ATTR_DIRECTION: DIRECTION_FORWARD,
            ATTR_PERCENTAGE: 50,
        },
    )
    hass.states.async_set(
        PERCENTAGE_FULL_FAN_ENTITY_ID,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FULL_SUPPORT_FEATURES,
            ATTR_OSCILLATING: True,
            ATTR_DIRECTION: DIRECTION_FORWARD,
            ATTR_PERCENTAGE: 50,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_FRIENDLY_NAME] == DEFAULT_NAME
    assert state.attributes[ATTR_ENTITY_ID] == [*FULL_FAN_ENTITY_IDS]
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == FULL_SUPPORT_FEATURES
    assert ATTR_PERCENTAGE in state.attributes
    assert state.attributes[ATTR_PERCENTAGE] == 50
    assert state.attributes[ATTR_OSCILLATING] is True
    assert state.attributes[ATTR_DIRECTION] == DIRECTION_FORWARD
    assert ATTR_ASSUMED_STATE not in state.attributes

    # Add Entity with a different direction should not set assumed state
    hass.states.async_set(
        PERCENTAGE_FULL_FAN_ENTITY_ID,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FULL_SUPPORT_FEATURES,
            ATTR_OSCILLATING: True,
            ATTR_DIRECTION: DIRECTION_REVERSE,
            ATTR_PERCENTAGE: 50,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_ON
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert ATTR_PERCENTAGE in state.attributes
    assert state.attributes[ATTR_PERCENTAGE] == 50
    assert state.attributes[ATTR_OSCILLATING] is True

    # Now that everything is the same, no longer assumed state

    hass.states.async_set(
        LIVING_ROOM_FAN_ENTITY_ID,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FULL_SUPPORT_FEATURES,
            ATTR_OSCILLATING: True,
            ATTR_DIRECTION: DIRECTION_REVERSE,
            ATTR_PERCENTAGE: 50,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_ON
    assert ATTR_PERCENTAGE in state.attributes
    assert state.attributes[ATTR_PERCENTAGE] == 50
    assert state.attributes[ATTR_OSCILLATING] is True
    assert state.attributes[ATTR_DIRECTION] == DIRECTION_REVERSE
    assert ATTR_ASSUMED_STATE not in state.attributes

    hass.states.async_set(
        LIVING_ROOM_FAN_ENTITY_ID,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FULL_SUPPORT_FEATURES,
            ATTR_OSCILLATING: False,
            ATTR_DIRECTION: DIRECTION_FORWARD,
            ATTR_PERCENTAGE: 50,
        },
    )
    hass.states.async_set(
        PERCENTAGE_FULL_FAN_ENTITY_ID,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FULL_SUPPORT_FEATURES,
            ATTR_OSCILLATING: False,
            ATTR_DIRECTION: DIRECTION_FORWARD,
            ATTR_PERCENTAGE: 50,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_ON
    assert ATTR_PERCENTAGE in state.attributes
    assert state.attributes[ATTR_PERCENTAGE] == 50
    assert state.attributes[ATTR_OSCILLATING] is False
    assert state.attributes[ATTR_DIRECTION] == DIRECTION_FORWARD
    assert ATTR_ASSUMED_STATE not in state.attributes