async def test_attributes(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test handling of state attributes."""
    state = hass.states.get(COVER_GROUP)
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes[ATTR_FRIENDLY_NAME] == DEFAULT_NAME
    assert ATTR_ENTITY_ID not in state.attributes
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert ATTR_CURRENT_POSITION not in state.attributes
    assert ATTR_CURRENT_TILT_POSITION not in state.attributes

    # Set entity as closed
    hass.states.async_set(DEMO_COVER, CoverState.CLOSED, {})
    await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.CLOSED
    assert state.attributes[ATTR_ENTITY_ID] == [
        DEMO_COVER,
        DEMO_COVER_POS,
        DEMO_COVER_TILT,
        DEMO_TILT,
    ]

    # Set entity as opening
    hass.states.async_set(DEMO_COVER, CoverState.OPENING, {})
    await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.OPENING

    # Set entity as closing
    hass.states.async_set(DEMO_COVER, CoverState.CLOSING, {})
    await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.CLOSING

    # Set entity as unknown again
    hass.states.async_set(DEMO_COVER, STATE_UNKNOWN, {})
    await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == STATE_UNKNOWN

    # Add Entity that supports open / close / stop
    hass.states.async_set(DEMO_COVER, CoverState.OPEN, {ATTR_SUPPORTED_FEATURES: 11})
    await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.OPEN
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 11
    assert ATTR_CURRENT_POSITION not in state.attributes
    assert ATTR_CURRENT_TILT_POSITION not in state.attributes

    # Add Entity that supports set_cover_position
    hass.states.async_set(
        DEMO_COVER_POS,
        CoverState.OPEN,
        {ATTR_SUPPORTED_FEATURES: 4, ATTR_CURRENT_POSITION: 70},
    )
    await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.OPEN
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 15
    assert state.attributes[ATTR_CURRENT_POSITION] == 70
    assert ATTR_CURRENT_TILT_POSITION not in state.attributes

    # Add Entity that supports open tilt / close tilt / stop tilt
    hass.states.async_set(DEMO_TILT, CoverState.OPEN, {ATTR_SUPPORTED_FEATURES: 112})
    await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.OPEN
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 127
    assert state.attributes[ATTR_CURRENT_POSITION] == 70
    assert ATTR_CURRENT_TILT_POSITION not in state.attributes

    # Add Entity that supports set_tilt_position
    hass.states.async_set(
        DEMO_COVER_TILT,
        CoverState.OPEN,
        {ATTR_SUPPORTED_FEATURES: 128, ATTR_CURRENT_TILT_POSITION: 60},
    )
    await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.OPEN
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 255
    assert state.attributes[ATTR_CURRENT_POSITION] == 70
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 60

    # ### Test state when group members have different states ###
    # ##########################

    # Covers
    hass.states.async_set(
        DEMO_COVER,
        CoverState.OPEN,
        {ATTR_SUPPORTED_FEATURES: 4, ATTR_CURRENT_POSITION: 100},
    )
    await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.OPEN
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 244
    assert state.attributes[ATTR_CURRENT_POSITION] == 85  # (70 + 100) / 2
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 60

    hass.states.async_remove(DEMO_COVER)
    hass.states.async_remove(DEMO_COVER_POS)
    await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.OPEN
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 240
    assert ATTR_CURRENT_POSITION not in state.attributes
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 60

    # Tilts
    hass.states.async_set(
        DEMO_TILT,
        CoverState.OPEN,
        {ATTR_SUPPORTED_FEATURES: 128, ATTR_CURRENT_TILT_POSITION: 100},
    )
    await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.OPEN
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 128
    assert ATTR_CURRENT_POSITION not in state.attributes
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 80  # (60 + 100) / 2

    hass.states.async_remove(DEMO_COVER_TILT)
    hass.states.async_set(DEMO_TILT, CoverState.CLOSED)
    await hass.async_block_till_done()

    state = hass.states.get(COVER_GROUP)
    assert state.state == CoverState.CLOSED
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert ATTR_CURRENT_POSITION not in state.attributes
    assert ATTR_CURRENT_TILT_POSITION not in state.attributes

    # Test entity registry integration
    entry = entity_registry.async_get(COVER_GROUP)
    assert entry
    assert entry.unique_id == "unique_identifier"