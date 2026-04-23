async def test_multilevel_switch_cover_v3_no_moving_state_supervised(
    hass: HomeAssistant,
    client: MagicMock,
    chain_actuator_zws12_state: dict[str, Any],
    integration: MockConfigEntry,
) -> None:
    """Test v3 Multilevel Switch cover never sets OPENING/CLOSING even with Supervision."""
    node_state = copy.deepcopy(chain_actuator_zws12_state)
    for value in node_state["values"]:
        if value["commandClass"] == CommandClass.SWITCH_MULTILEVEL:
            value["ccVersion"] = 3
    client.driver.controller.receive_event(
        Event(
            type="node added",
            data={
                "source": "controller",
                "event": "node added",
                "node": node_state,
                "result": {},
            },
        )
    )
    await hass.async_block_till_done()
    node = client.driver.controller.nodes[node_state["nodeId"]]

    state = hass.states.get(WINDOW_COVER_ENTITY)
    assert state
    assert state.state == CoverState.CLOSED

    # WORKING result (Supervision CC) must NOT optimistically set OPENING
    client.async_send_command.return_value = {
        "result": {"status": SetValueStatus.WORKING}
    }
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: WINDOW_COVER_ENTITY},
        blocking=True,
    )
    state = hass.states.get(WINDOW_COVER_ENTITY)
    assert state.state == CoverState.CLOSED

    # Position updates still work correctly.
    node.receive_event(
        Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Multilevel Switch",
                    "commandClass": CommandClass.SWITCH_MULTILEVEL,
                    "endpoint": 0,
                    "property": "currentValue",
                    "newValue": 99,
                    "prevValue": 0,
                    "propertyName": "currentValue",
                },
            },
        )
    )
    state = hass.states.get(WINDOW_COVER_ENTITY)
    assert state.state == CoverState.OPEN

    # WORKING result must NOT optimistically set CLOSING
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: WINDOW_COVER_ENTITY},
        blocking=True,
    )
    state = hass.states.get(WINDOW_COVER_ENTITY)
    assert state.state == CoverState.OPEN

    node.receive_event(
        Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Multilevel Switch",
                    "commandClass": CommandClass.SWITCH_MULTILEVEL,
                    "endpoint": 0,
                    "property": "currentValue",
                    "newValue": 0,
                    "prevValue": 99,
                    "propertyName": "currentValue",
                },
            },
        )
    )
    state = hass.states.get(WINDOW_COVER_ENTITY)
    assert state.state == CoverState.CLOSED

    # SUCCESS result must NOT set OPENING
    client.async_send_command.return_value = {
        "result": {"status": SetValueStatus.SUCCESS}
    }
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: WINDOW_COVER_ENTITY},
        blocking=True,
    )
    state = hass.states.get(WINDOW_COVER_ENTITY)
    assert state.state == CoverState.CLOSED