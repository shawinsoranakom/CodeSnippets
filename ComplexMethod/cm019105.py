async def test_websocket_subscribe_debounces_rapid_updates(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    test_entities: list[MockCalendarEntity],
) -> None:
    """Test that rapid state writes are debounced for event listeners."""
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

    entity = test_entities[0]
    entity.async_get_events.reset_mock()

    # Rapidly write state multiple times
    for i in range(5):
        entity.create_event(
            start=start + timedelta(hours=i + 2),
            end=start + timedelta(hours=i + 3),
            summary=f"Rapid Event {i}",
        )
        entity.async_write_ha_state()

    await hass.async_block_till_done()

    # The debouncer with immediate=True fires the first call immediately
    # and coalesces the rest into one call after the cooldown.
    # Without debouncing this would be 5 calls.
    assert entity.async_get_events.call_count == 1

    # Advance time past the debounce cooldown to fire the trailing call
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=2))
    await hass.async_block_till_done()

    # Should be exactly 2 total: immediate + one coalesced trailing call
    assert entity.async_get_events.call_count == 2

    # Drain messages: immediate update + trailing debounced update
    messages: list[dict] = []
    for _ in range(10):
        msg = await client.receive_json()
        assert msg["id"] == subscription_id
        assert msg["type"] == "event"
        messages.append(msg)
        if len(msg["event"]["events"]) == 6:  # 1 original + 5 rapid
            break
    else:
        pytest.fail("Did not receive expected calendar event list with 6 events")

    # The final message has all events
    assert len(messages[-1]["event"]["events"]) == 6