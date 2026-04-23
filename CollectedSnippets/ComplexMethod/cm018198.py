async def test_subscribe_unsubscribe_events_whitelist(
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
    hass_admin_user: MockUser,
) -> None:
    """Test subscribe/unsubscribe events on whitelist."""
    hass_admin_user.groups = []

    await websocket_client.send_json_auto_id(
        {"type": "subscribe_events", "event_type": "not-in-whitelist"}
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == "unauthorized"

    await websocket_client.send_json_auto_id(
        {"type": "subscribe_events", "event_type": "themes_updated"}
    )

    msg = await websocket_client.receive_json()
    themes_updated_subscription = msg["id"]
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    hass.bus.async_fire("themes_updated")

    async with asyncio.timeout(3):
        msg = await websocket_client.receive_json()

    assert msg["id"] == themes_updated_subscription
    assert msg["type"] == "event"
    event = msg["event"]
    assert event["event_type"] == "themes_updated"
    assert event["origin"] == "LOCAL"