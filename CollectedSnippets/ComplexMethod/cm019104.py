async def test_websocket_subscribe_updates_on_state_change(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    test_entities: list[MockCalendarEntity],
) -> None:
    """Test that subscribers receive updates when calendar state changes."""
    client = await hass_ws_client(hass)

    start = dt_util.now()
    end = start + timedelta(days=1)

    await client.send_json_auto_id(
        {
            "type": "calendar/event/subscribe",
            "entity_id": "calendar.calendar_1",
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    subscription_id = msg["id"]

    # Receive initial event list
    msg = await client.receive_json()
    assert msg["id"] == subscription_id

    # Add a new event and trigger state update
    entity = test_entities[0]
    entity.create_event(
        start=start + timedelta(hours=2),
        end=start + timedelta(hours=3),
        summary="New Event",
    )
    entity.async_write_ha_state()
    await hass.async_block_till_done()

    # Should receive updated event list
    msg = await client.receive_json()
    assert msg["id"] == subscription_id
    assert msg["type"] == "event"
    events = msg["event"]["events"]
    assert len(events) == 2
    summaries = {event["summary"] for event in events}
    assert "Future Event" in summaries
    assert "New Event" in summaries