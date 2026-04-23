async def test_subscribe_unsubscribe_events(
    hass: HomeAssistant, websocket_client
) -> None:
    """Test subscribe/unsubscribe events command."""
    init_count = sum(hass.bus.async_listeners().values())

    await websocket_client.send_json_auto_id(
        {"type": "subscribe_events", "event_type": "test_event"}
    )

    msg = await websocket_client.receive_json()
    subscription = msg["id"]
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    # Verify we have a new listener
    assert sum(hass.bus.async_listeners().values()) == init_count + 1

    hass.bus.async_fire("ignore_event")
    hass.bus.async_fire("test_event", {"hello": "world"})
    hass.bus.async_fire("ignore_event")

    async with asyncio.timeout(3):
        msg = await websocket_client.receive_json()

    assert msg["id"] == subscription
    assert msg["type"] == "event"
    event = msg["event"]

    assert event["event_type"] == "test_event"
    assert event["data"] == {"hello": "world"}
    assert event["origin"] == "LOCAL"

    await websocket_client.send_json_auto_id(
        {"type": "unsubscribe_events", "subscription": subscription}
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    # Check our listener got unsubscribed
    assert sum(hass.bus.async_listeners().values()) == init_count