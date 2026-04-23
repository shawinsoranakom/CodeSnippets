async def test_attributes(hass: HomeAssistant) -> None:
    """Test handling of state attributes."""
    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes[ATTR_FRIENDLY_NAME] == DEFAULT_NAME
    assert ATTR_ENTITY_ID not in state.attributes
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    hass.states.async_set(CEILING_FAN_ENTITY_ID, STATE_ON, {})
    hass.states.async_set(LIVING_ROOM_FAN_ENTITY_ID, STATE_ON, {})
    hass.states.async_set(PERCENTAGE_FULL_FAN_ENTITY_ID, STATE_ON, {})
    hass.states.async_set(PERCENTAGE_LIMITED_FAN_ENTITY_ID, STATE_ON, {})
    await hass.async_block_till_done()
    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_ENTITY_ID] == [
        *FULL_FAN_ENTITY_IDS,
        *LIMITED_FAN_ENTITY_IDS,
    ]

    # Add Entity that supports speed
    hass.states.async_set(
        CEILING_FAN_ENTITY_ID,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.SET_SPEED,
            ATTR_PERCENTAGE: 50,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_ON
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == FanEntityFeature.SET_SPEED
    assert ATTR_PERCENTAGE in state.attributes
    assert state.attributes[ATTR_PERCENTAGE] == 50
    assert ATTR_ASSUMED_STATE not in state.attributes

    # Add Entity with a different speed should not set assumed state
    hass.states.async_set(
        PERCENTAGE_LIMITED_FAN_ENTITY_ID,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.SET_SPEED,
            ATTR_PERCENTAGE: 75,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_ON
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_PERCENTAGE] == int((50 + 75) / 2)