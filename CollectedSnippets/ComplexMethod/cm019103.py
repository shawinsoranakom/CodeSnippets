async def test_websocket_handle_subscribe_calendar_events(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    test_entities: list[MockCalendarEntity],
) -> None:
    """Test subscribing to calendar event updates via websocket."""
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

    # Should receive initial event list
    msg = await client.receive_json()
    assert msg["id"] == subscription_id
    assert msg["type"] == "event"
    assert "events" in msg["event"]
    events = msg["event"]["events"]
    assert len(events) == 1
    assert events[0]["summary"] == "Future Event"
    assert events[0]["uid"] == "calendar-event-uid-1"
    assert events[0]["rrule"] == "FREQ=WEEKLY;COUNT=3"
    assert events[0]["recurrence_id"] == "20260415"