async def test_message_coalescing_not_supported_by_websocket_client(
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
    hass_admin_user: MockUser,
) -> None:
    """Test enabling message coalescing not supported by websocket client."""
    await websocket_client.send_json({"id": 7, "type": "subscribe_entities"})

    data = await websocket_client.receive_str()
    msg = json_loads(data)
    assert msg["id"] == 7
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    hass.states.async_set("light.permitted", "on", {"color": "red"})
    hass.states.async_set("light.permitted", "on", {"color": "blue"})

    data = await websocket_client.receive_str()
    msg = json_loads(data)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"] == {"a": {}}

    data = await websocket_client.receive_str()
    msg = json_loads(data)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"] == {
        "a": {
            "light.permitted": {"a": {"color": "red"}, "c": ANY, "lc": ANY, "s": "on"}
        }
    }

    data = await websocket_client.receive_str()
    msg = json_loads(data)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"] == {
        "c": {"light.permitted": {"+": {"a": {"color": "blue"}, "c": ANY, "lu": ANY}}}
    }
    await websocket_client.close()
    await hass.async_block_till_done()