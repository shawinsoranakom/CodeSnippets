async def test_client_message_coalescing(
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
    hass_admin_user: MockUser,
) -> None:
    """Test client message coalescing."""
    await websocket_client.send_json(
        [
            {
                "id": 1,
                "type": "supported_features",
                "features": {FEATURE_COALESCE_MESSAGES: 1},
            },
            {"id": 7, "type": "subscribe_entities"},
        ]
    )
    hass.states.async_set("light.permitted", "on", {"color": "red"})

    data = await websocket_client.receive_str()
    msgs = json_loads(data)

    msg = msgs.pop(0)
    assert msg["id"] == 1
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    msg = msgs.pop(0)
    assert msg["id"] == 7
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    msg = msgs.pop(0)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"] == {
        "a": {
            "light.permitted": {"a": {"color": "red"}, "c": ANY, "lc": ANY, "s": "on"}
        }
    }

    hass.states.async_set("light.permitted", "on", {"color": "yellow"})
    hass.states.async_set("light.permitted", "on", {"color": "green"})
    hass.states.async_set("light.permitted", "on", {"color": "blue"})

    data = await websocket_client.receive_str()
    msgs = json_loads(data)

    msg = msgs.pop(0)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"] == {
        "c": {"light.permitted": {"+": {"a": {"color": "yellow"}, "c": ANY, "lu": ANY}}}
    }

    msg = msgs.pop(0)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"] == {
        "c": {"light.permitted": {"+": {"a": {"color": "green"}, "c": ANY, "lu": ANY}}}
    }

    msg = msgs.pop(0)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"] == {
        "c": {"light.permitted": {"+": {"a": {"color": "blue"}, "c": ANY, "lu": ANY}}}
    }

    hass.states.async_set("light.permitted", "on", {"color": "yellow"})
    hass.states.async_set("light.permitted", "on", {"color": "green"})
    hass.states.async_set("light.permitted", "on", {"color": "blue"})
    await websocket_client.close()
    await hass.async_block_till_done()