async def test_subscribe_entities_chained_state_change(
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
    hass_admin_user: MockUser,
) -> None:
    """Test chaining state changed events.

    Ensure the websocket sends the off state after
    the on state.
    """

    @callback
    def auto_off_listener(event):
        hass.states.async_set("light.permitted", "off")

    async_track_state_change_event(hass, ["light.permitted"], auto_off_listener)

    await websocket_client.send_json_auto_id({"type": "subscribe_entities"})

    data = await websocket_client.receive_str()
    msg = json_loads(data)
    subscription = msg["id"]
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    data = await websocket_client.receive_str()
    msg = json_loads(data)
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    assert msg["event"] == {"a": {}}

    hass.states.async_set("light.permitted", "on")
    data = await websocket_client.receive_str()
    msg = json_loads(data)
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    assert msg["event"] == {
        "a": {"light.permitted": {"a": {}, "c": ANY, "lc": ANY, "s": "on"}}
    }
    data = await websocket_client.receive_str()
    msg = json_loads(data)
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    assert msg["event"] == {
        "c": {"light.permitted": {"+": {"c": ANY, "lc": ANY, "s": "off"}}}
    }

    await websocket_client.close()
    await hass.async_block_till_done()