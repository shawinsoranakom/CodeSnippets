async def test_subscribe_unsubscribe_entities_specific_entities(
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
    hass_admin_user: MockUser,
    unserializable_states: list[str],
) -> None:
    """Test subscribe/unsubscribe entities with a list of entity ids."""

    class CannotSerializeMe:
        """Cannot serialize this."""

        def __init__(self) -> None:
            """Init cannot serialize this."""

    for entity_id in unserializable_states:
        hass.states.async_set(
            entity_id,
            "off",
            {"color": "red", "cannot_serialize": CannotSerializeMe()},
        )

    hass.states.async_set("light.permitted", "off", {"color": "red"})
    hass.states.async_set("light.not_interested", "off", {"color": "blue"})
    original_state = hass.states.get("light.permitted")
    assert isinstance(original_state, State)
    hass_admin_user.groups = []
    hass_admin_user.mock_policy(
        {
            "entities": {
                "entity_ids": {
                    "light.permitted": True,
                    "light.not_interested": True,
                    "light.cannot_serialize": True,
                }
            }
        }
    )

    await websocket_client.send_json_auto_id(
        {
            "type": "subscribe_entities",
            "entity_ids": ["light.permitted", "light.cannot_serialize"],
        }
    )

    msg = await websocket_client.receive_json()
    subscription = msg["id"]
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    assert isinstance(msg["event"]["a"]["light.permitted"]["c"], str)
    assert msg["event"] == {
        "a": {
            "light.permitted": {
                "a": {"color": "red"},
                "c": ANY,
                "lc": ANY,
                "s": "off",
            }
        }
    }
    hass.states.async_set("light.not_interested", "on", {"effect": "help"})
    hass.states.async_set("light.not_permitted", "on")
    hass.states.async_set("light.permitted", "on", {"color": "blue"})

    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    assert msg["event"] == {
        "c": {
            "light.permitted": {
                "+": {
                    "a": {"color": "blue"},
                    "c": ANY,
                    "lc": ANY,
                    "s": "on",
                }
            }
        }
    }