async def test_multilevel_switch_select(
    hass: HomeAssistant, client, fortrezz_ssa1_siren, integration
) -> None:
    """Test Multilevel Switch CC based select entity."""
    node = fortrezz_ssa1_siren
    state = hass.states.get(MULTILEVEL_SWITCH_SELECT_ENTITY)

    assert state
    assert state.state == "Off"
    attr = state.attributes
    assert attr["options"] == [
        "Off",
        "Strobe ONLY",
        "Siren ONLY",
        "Siren & Strobe FULL Alarm",
    ]

    # Test select option with string value
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": MULTILEVEL_SWITCH_SELECT_ENTITY, "option": "Strobe ONLY"},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "endpoint": 0,
        "commandClass": 38,
        "property": "targetValue",
    }
    assert args["value"] == 33

    client.async_send_command.reset_mock()

    # Test value update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": node.node_id,
            "args": {
                "commandClassName": "Multilevel Switch",
                "commandClass": 38,
                "endpoint": 0,
                "property": "currentValue",
                "newValue": 33,
                "prevValue": 0,
                "propertyName": "currentValue",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(MULTILEVEL_SWITCH_SELECT_ENTITY)
    assert state.state == "Strobe ONLY"