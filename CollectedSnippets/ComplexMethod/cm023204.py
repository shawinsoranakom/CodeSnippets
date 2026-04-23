async def test_default_tone_select(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client: MagicMock,
    aeotec_zw164_siren: Node,
    integration: ConfigEntry,
) -> None:
    """Test the default tone select entity."""
    node = aeotec_zw164_siren
    state = hass.states.get(DEFAULT_TONE_SELECT_ENTITY)

    assert state
    assert state.state == "17ALAR~1 (35 sec)"
    attr = state.attributes
    assert attr["options"] == [
        "01DING~1 (5 sec)",
        "02DING~1 (9 sec)",
        "03TRAD~1 (11 sec)",
        "04ELEC~1 (2 sec)",
        "05WEST~1 (13 sec)",
        "06CHIM~1 (7 sec)",
        "07CUCK~1 (31 sec)",
        "08TRAD~1 (6 sec)",
        "09SMOK~1 (11 sec)",
        "10SMOK~1 (6 sec)",
        "11FIRE~1 (35 sec)",
        "12COSE~1 (5 sec)",
        "13KLAX~1 (38 sec)",
        "14DEEP~1 (41 sec)",
        "15WARN~1 (37 sec)",
        "16TORN~1 (46 sec)",
        "17ALAR~1 (35 sec)",
        "18DEEP~1 (62 sec)",
        "19ALAR~1 (15 sec)",
        "20ALAR~1 (7 sec)",
        "21DIGI~1 (8 sec)",
        "22ALER~1 (64 sec)",
        "23SHIP~1 (4 sec)",
        "25CHRI~1 (4 sec)",
        "26GONG~1 (12 sec)",
        "27SING~1 (1 sec)",
        "28TONA~1 (5 sec)",
        "29UPWA~1 (2 sec)",
        "30DOOR~1 (27 sec)",
    ]

    entity_entry = entity_registry.async_get(DEFAULT_TONE_SELECT_ENTITY)

    assert entity_entry
    assert entity_entry.entity_category is EntityCategory.CONFIG

    # Test select option with string value
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": DEFAULT_TONE_SELECT_ENTITY, "option": "30DOOR~1 (27 sec)"},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "endpoint": 2,
        "commandClass": 121,
        "property": "defaultToneId",
    }
    assert args["value"] == 30

    client.async_send_command.reset_mock()

    # Test value update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": node.node_id,
            "args": {
                "commandClassName": "Sound Switch",
                "commandClass": 121,
                "endpoint": 2,
                "property": "defaultToneId",
                "newValue": 30,
                "prevValue": 17,
                "propertyName": "defaultToneId",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(DEFAULT_TONE_SELECT_ENTITY)
    assert state
    assert state.state == "30DOOR~1 (27 sec)"