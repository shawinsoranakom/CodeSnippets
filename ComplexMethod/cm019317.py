async def test_service_calls(hass: HomeAssistant) -> None:
    """Test calling services."""
    await hass.services.async_call(
        FAN_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: FAN_GROUP}, blocking=True
    )
    assert hass.states.get(LIVING_ROOM_FAN_ENTITY_ID).state == STATE_ON
    assert hass.states.get(PERCENTAGE_FULL_FAN_ENTITY_ID).state == STATE_ON
    assert hass.states.get(FAN_GROUP).state == STATE_ON

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: FAN_GROUP, ATTR_PERCENTAGE: 66},
        blocking=True,
    )
    living_room_fan_state = hass.states.get(LIVING_ROOM_FAN_ENTITY_ID)
    assert living_room_fan_state.attributes[ATTR_PERCENTAGE] == 66
    percentage_full_fan_state = hass.states.get(PERCENTAGE_FULL_FAN_ENTITY_ID)
    assert percentage_full_fan_state.attributes[ATTR_PERCENTAGE] == 66
    fan_group_state = hass.states.get(FAN_GROUP)
    assert fan_group_state.attributes[ATTR_PERCENTAGE] == 66
    assert fan_group_state.attributes[ATTR_PERCENTAGE_STEP] == 100 / 3

    await hass.services.async_call(
        FAN_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: FAN_GROUP}, blocking=True
    )
    assert hass.states.get(LIVING_ROOM_FAN_ENTITY_ID).state == STATE_OFF
    assert hass.states.get(PERCENTAGE_FULL_FAN_ENTITY_ID).state == STATE_OFF
    assert hass.states.get(FAN_GROUP).state == STATE_OFF

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: FAN_GROUP, ATTR_PERCENTAGE: 100},
        blocking=True,
    )
    living_room_fan_state = hass.states.get(LIVING_ROOM_FAN_ENTITY_ID)
    assert living_room_fan_state.attributes[ATTR_PERCENTAGE] == 100
    percentage_full_fan_state = hass.states.get(PERCENTAGE_FULL_FAN_ENTITY_ID)
    assert percentage_full_fan_state.attributes[ATTR_PERCENTAGE] == 100
    fan_group_state = hass.states.get(FAN_GROUP)
    assert fan_group_state.attributes[ATTR_PERCENTAGE] == 100

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: FAN_GROUP, ATTR_PERCENTAGE: 0},
        blocking=True,
    )
    assert hass.states.get(LIVING_ROOM_FAN_ENTITY_ID).state == STATE_OFF
    assert hass.states.get(PERCENTAGE_FULL_FAN_ENTITY_ID).state == STATE_OFF
    assert hass.states.get(FAN_GROUP).state == STATE_OFF

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_OSCILLATE,
        {ATTR_ENTITY_ID: FAN_GROUP, ATTR_OSCILLATING: True},
        blocking=True,
    )
    living_room_fan_state = hass.states.get(LIVING_ROOM_FAN_ENTITY_ID)
    assert living_room_fan_state.attributes[ATTR_OSCILLATING] is True
    percentage_full_fan_state = hass.states.get(PERCENTAGE_FULL_FAN_ENTITY_ID)
    assert percentage_full_fan_state.attributes[ATTR_OSCILLATING] is True
    fan_group_state = hass.states.get(FAN_GROUP)
    assert fan_group_state.attributes[ATTR_OSCILLATING] is True

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_OSCILLATE,
        {ATTR_ENTITY_ID: FAN_GROUP, ATTR_OSCILLATING: False},
        blocking=True,
    )
    living_room_fan_state = hass.states.get(LIVING_ROOM_FAN_ENTITY_ID)
    assert living_room_fan_state.attributes[ATTR_OSCILLATING] is False
    percentage_full_fan_state = hass.states.get(PERCENTAGE_FULL_FAN_ENTITY_ID)
    assert percentage_full_fan_state.attributes[ATTR_OSCILLATING] is False
    fan_group_state = hass.states.get(FAN_GROUP)
    assert fan_group_state.attributes[ATTR_OSCILLATING] is False

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_DIRECTION,
        {ATTR_ENTITY_ID: FAN_GROUP, ATTR_DIRECTION: DIRECTION_FORWARD},
        blocking=True,
    )
    living_room_fan_state = hass.states.get(LIVING_ROOM_FAN_ENTITY_ID)
    assert living_room_fan_state.attributes[ATTR_DIRECTION] == DIRECTION_FORWARD
    percentage_full_fan_state = hass.states.get(PERCENTAGE_FULL_FAN_ENTITY_ID)
    assert percentage_full_fan_state.attributes[ATTR_DIRECTION] == DIRECTION_FORWARD
    fan_group_state = hass.states.get(FAN_GROUP)
    assert fan_group_state.attributes[ATTR_DIRECTION] == DIRECTION_FORWARD

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_DIRECTION,
        {ATTR_ENTITY_ID: FAN_GROUP, ATTR_DIRECTION: DIRECTION_REVERSE},
        blocking=True,
    )
    living_room_fan_state = hass.states.get(LIVING_ROOM_FAN_ENTITY_ID)
    assert living_room_fan_state.attributes[ATTR_DIRECTION] == DIRECTION_REVERSE
    percentage_full_fan_state = hass.states.get(PERCENTAGE_FULL_FAN_ENTITY_ID)
    assert percentage_full_fan_state.attributes[ATTR_DIRECTION] == DIRECTION_REVERSE
    fan_group_state = hass.states.get(FAN_GROUP)
    assert fan_group_state.attributes[ATTR_DIRECTION] == DIRECTION_REVERSE