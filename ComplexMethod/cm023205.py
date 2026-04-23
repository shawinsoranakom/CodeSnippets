async def test_protection_select(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client: MagicMock,
    inovelli_lzw36: Node,
    integration: ConfigEntry,
) -> None:
    """Test the default tone select entity."""
    node = inovelli_lzw36
    state = hass.states.get(PROTECTION_SELECT_ENTITY)

    assert state
    assert state.state == "Unprotected"
    attr = state.attributes
    assert attr["options"] == [
        "Unprotected",
        "ProtectedBySequence",
        "NoOperationPossible",
    ]

    entity_entry = entity_registry.async_get(PROTECTION_SELECT_ENTITY)

    assert entity_entry
    assert entity_entry.entity_category is EntityCategory.CONFIG

    # Test select option with string value
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": PROTECTION_SELECT_ENTITY, "option": "ProtectedBySequence"},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "endpoint": 0,
        "commandClass": 117,
        "property": "local",
    }
    assert args["value"] == 1

    client.async_send_command.reset_mock()

    # Test value update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": node.node_id,
            "args": {
                "commandClassName": "Protection",
                "commandClass": 117,
                "endpoint": 0,
                "property": "local",
                "newValue": 1,
                "prevValue": 0,
                "propertyName": "local",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(PROTECTION_SELECT_ENTITY)
    assert state
    assert state.state == "ProtectedBySequence"

    # Test null value
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": node.node_id,
            "args": {
                "commandClassName": "Protection",
                "commandClass": 117,
                "endpoint": 0,
                "property": "local",
                "newValue": None,
                "prevValue": 1,
                "propertyName": "local",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(PROTECTION_SELECT_ENTITY)
    assert state
    assert state.state == STATE_UNKNOWN