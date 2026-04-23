async def test_window_covering_cover_moving_state_position_support(
    hass: HomeAssistant,
    client: MagicMock,
    window_covering_outbound_bottom: Node,
    integration: MockConfigEntry,
) -> None:
    """Test moving state is only set when not already at the target endpoint."""
    node = window_covering_outbound_bottom
    entity_id = "cover.node_2_outbound_bottom"

    # Initial currentValue is 52 (mid-position). open_cover SHOULD set OPENING.
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.state == CoverState.OPENING

    # Clear moving state before next scenario.
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    # Simulate device reaching fully open (raw Z-Wave value 99 → HA position 100%).
    node.receive_event(
        Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Window Covering",
                    "commandClass": 106,
                    "endpoint": 0,
                    "property": "targetValue",
                    "propertyKey": 13,
                    "newValue": 99,
                    "prevValue": 52,
                    "propertyName": "targetValue",
                },
            },
        )
    )
    node.receive_event(
        Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Window Covering",
                    "commandClass": 106,
                    "endpoint": 0,
                    "property": "currentValue",
                    "propertyKey": 13,
                    "newValue": 99,
                    "prevValue": 52,
                    "propertyName": "currentValue",
                },
            },
        )
    )
    state = hass.states.get(entity_id)
    assert state.state == CoverState.OPEN

    # Already fully open — open_cover must NOT set OPENING.
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.state not in (CoverState.OPENING, CoverState.CLOSING)

    # Fully open but not fully closed — close_cover SHOULD set CLOSING.
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.state == CoverState.CLOSING

    # Clear moving state before next scenario.
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    # Simulate device reaching fully closed (raw Z-Wave value 0 → HA position 0%).
    node.receive_event(
        Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Window Covering",
                    "commandClass": 106,
                    "endpoint": 0,
                    "property": "targetValue",
                    "propertyKey": 13,
                    "newValue": 0,
                    "prevValue": 99,
                    "propertyName": "targetValue",
                },
            },
        )
    )
    node.receive_event(
        Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Window Covering",
                    "commandClass": 106,
                    "endpoint": 0,
                    "property": "currentValue",
                    "propertyKey": 13,
                    "newValue": 0,
                    "prevValue": 99,
                    "propertyName": "currentValue",
                },
            },
        )
    )
    state = hass.states.get(entity_id)
    assert state.state == CoverState.CLOSED

    # Already fully closed — close_cover must NOT set CLOSING.
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.state not in (CoverState.OPENING, CoverState.CLOSING)

    # From fully closed, open_cover SHOULD set OPENING (not at fully open endpoint).
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.state == CoverState.OPENING

    # Simulate the device moving: targetValue arrives first (early report), then
    # currentValue catches up to halfway. Moving state must stay OPENING throughout.
    node.receive_event(
        Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Window Covering",
                    "commandClass": 106,
                    "endpoint": 0,
                    "property": "targetValue",
                    "propertyKey": 13,
                    "newValue": 99,
                    "prevValue": 0,
                    "propertyName": "targetValue",
                },
            },
        )
    )
    node.receive_event(
        Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Window Covering",
                    "commandClass": 106,
                    "endpoint": 0,
                    "property": "currentValue",
                    "propertyKey": 13,
                    "newValue": 52,
                    "prevValue": 0,
                    "propertyName": "currentValue",
                },
            },
        )
    )
    state = hass.states.get(entity_id)
    assert state.state == CoverState.OPENING

    # Reverse halfway: close_cover while mid-travel MUST set CLOSING (not at endpoint).
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.state == CoverState.CLOSING

    # Simulate the device moving back down: targetValue=0 arrives first (early report),
    # then currentValue reaches halfway. Moving state must stay CLOSING throughout.
    node.receive_event(
        Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Window Covering",
                    "commandClass": 106,
                    "endpoint": 0,
                    "property": "targetValue",
                    "propertyKey": 13,
                    "newValue": 0,
                    "prevValue": 99,
                    "propertyName": "targetValue",
                },
            },
        )
    )
    node.receive_event(
        Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Window Covering",
                    "commandClass": 106,
                    "endpoint": 0,
                    "property": "currentValue",
                    "propertyKey": 13,
                    "newValue": 52,
                    "prevValue": 99,
                    "propertyName": "currentValue",
                },
            },
        )
    )
    state = hass.states.get(entity_id)
    assert state.state == CoverState.CLOSING

    # Reverse halfway: open_cover while mid-travel MUST set OPENING (not at endpoint).
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.state == CoverState.OPENING