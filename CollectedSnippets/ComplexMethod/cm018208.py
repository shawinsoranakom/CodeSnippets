async def test_subscribe_trigger(
    hass: HomeAssistant, websocket_client: MockHAClientWebSocket
) -> None:
    """Test subscribing to a trigger."""
    init_count = sum(hass.bus.async_listeners().values())

    await websocket_client.send_json_auto_id(
        {
            "type": "subscribe_trigger",
            "trigger": {"platform": "event", "event_type": "test_event"},
            "variables": {"hello": "world"},
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    # Verify we have a new listener
    assert sum(hass.bus.async_listeners().values()) == init_count + 1

    context = Context()

    hass.bus.async_fire("ignore_event")
    hass.bus.async_fire("test_event", {"hello": "world"}, context=context)
    hass.bus.async_fire("ignore_event")

    async with asyncio.timeout(3):
        msg = await websocket_client.receive_json()

    assert msg["type"] == "event"
    assert msg["event"]["context"]["id"] == context.id
    assert msg["event"]["variables"]["trigger"]["platform"] == "event"

    event = msg["event"]["variables"]["trigger"]["event"]

    assert event["event_type"] == "test_event"
    assert event["data"] == {"hello": "world"}
    assert event["origin"] == "LOCAL"

    await websocket_client.send_json_auto_id(
        {"type": "unsubscribe_events", "subscription": msg["id"]}
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    # Check our listener got unsubscribed
    assert sum(hass.bus.async_listeners().values()) == init_count