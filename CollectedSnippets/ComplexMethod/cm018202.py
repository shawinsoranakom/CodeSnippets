async def test_subscribe_unsubscribe_entities_with_filter(
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
    hass_admin_user: MockUser,
    unserializable_states: list[str],
) -> None:
    """Test subscribe/unsubscribe entities with an entity filter."""

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

    hass.states.async_set("switch.not_included", "off")
    hass.states.async_set("light.include", "off")
    await websocket_client.send_json_auto_id(
        {"type": "subscribe_entities", "include": {"domains": ["light"]}}
    )

    msg = await websocket_client.receive_json()
    subscription = msg["id"]
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    assert msg["event"] == {
        "a": {
            "light.include": {
                "a": {},
                "c": ANY,
                "lc": ANY,
                "s": "off",
            }
        }
    }
    hass.states.async_set("switch.not_included", "on")
    hass.states.async_set("light.include", "on")
    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    assert msg["event"] == {
        "c": {
            "light.include": {
                "+": {
                    "c": ANY,
                    "lc": ANY,
                    "s": "on",
                }
            }
        }
    }