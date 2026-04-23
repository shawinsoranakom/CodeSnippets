async def test_state(hass: HomeAssistant, entity_registry: er.EntityRegistry) -> None:
    """Test handling of state.

    The group state is on if at least one group member is on.
    Otherwise, the group state is off.
    """
    state = hass.states.get(FAN_GROUP)
    # No entity has a valid state -> group state unavailable
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes[ATTR_FRIENDLY_NAME] == DEFAULT_NAME
    assert ATTR_ENTITY_ID not in state.attributes
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    # Test group members exposed as attribute
    hass.states.async_set(CEILING_FAN_ENTITY_ID, STATE_UNKNOWN, {})
    await hass.async_block_till_done()
    state = hass.states.get(FAN_GROUP)
    assert state.attributes[ATTR_ENTITY_ID] == [
        *FULL_FAN_ENTITY_IDS,
        *LIMITED_FAN_ENTITY_IDS,
    ]

    # All group members unavailable -> unavailable
    hass.states.async_set(CEILING_FAN_ENTITY_ID, STATE_UNAVAILABLE)
    hass.states.async_set(LIVING_ROOM_FAN_ENTITY_ID, STATE_UNAVAILABLE)
    hass.states.async_set(PERCENTAGE_FULL_FAN_ENTITY_ID, STATE_UNAVAILABLE)
    hass.states.async_set(PERCENTAGE_LIMITED_FAN_ENTITY_ID, STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_UNAVAILABLE

    # The group state is unknown if all group members are unknown or unavailable.
    for state_1 in (STATE_UNAVAILABLE, STATE_UNKNOWN):
        for state_2 in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            for state_3 in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                hass.states.async_set(CEILING_FAN_ENTITY_ID, state_1, {})
                hass.states.async_set(LIVING_ROOM_FAN_ENTITY_ID, state_2, {})
                hass.states.async_set(PERCENTAGE_FULL_FAN_ENTITY_ID, state_3, {})
                hass.states.async_set(
                    PERCENTAGE_LIMITED_FAN_ENTITY_ID, STATE_UNKNOWN, {}
                )
                await hass.async_block_till_done()
                state = hass.states.get(FAN_GROUP)
                assert state.state == STATE_UNKNOWN

    # The group state is off if all group members are off, unknown or unavailable.
    for state_1 in (STATE_OFF, STATE_UNAVAILABLE, STATE_UNKNOWN):
        for state_2 in (STATE_OFF, STATE_UNAVAILABLE, STATE_UNKNOWN):
            for state_3 in (STATE_OFF, STATE_UNAVAILABLE, STATE_UNKNOWN):
                hass.states.async_set(CEILING_FAN_ENTITY_ID, state_1, {})
                hass.states.async_set(LIVING_ROOM_FAN_ENTITY_ID, state_2, {})
                hass.states.async_set(PERCENTAGE_FULL_FAN_ENTITY_ID, state_3, {})
                hass.states.async_set(PERCENTAGE_LIMITED_FAN_ENTITY_ID, STATE_OFF, {})
                await hass.async_block_till_done()
                state = hass.states.get(FAN_GROUP)
                assert state.state == STATE_OFF

    # At least one member on -> group on
    for state_1 in (STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN):
        for state_2 in (STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN):
            for state_3 in (STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN):
                hass.states.async_set(CEILING_FAN_ENTITY_ID, state_1, {})
                hass.states.async_set(LIVING_ROOM_FAN_ENTITY_ID, state_2, {})
                hass.states.async_set(PERCENTAGE_FULL_FAN_ENTITY_ID, state_3, {})
                hass.states.async_set(PERCENTAGE_LIMITED_FAN_ENTITY_ID, STATE_ON, {})
                await hass.async_block_till_done()
                state = hass.states.get(FAN_GROUP)
                assert state.state == STATE_ON

    # now remove an entity
    hass.states.async_remove(PERCENTAGE_LIMITED_FAN_ENTITY_ID)
    await hass.async_block_till_done()
    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_UNKNOWN
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    # now remove all entities
    hass.states.async_remove(CEILING_FAN_ENTITY_ID)
    hass.states.async_remove(LIVING_ROOM_FAN_ENTITY_ID)
    hass.states.async_remove(PERCENTAGE_FULL_FAN_ENTITY_ID)
    await hass.async_block_till_done()
    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_UNAVAILABLE
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    # Test entity registry integration
    entry = entity_registry.async_get(FAN_GROUP)
    assert entry
    assert entry.unique_id == "unique_identifier"