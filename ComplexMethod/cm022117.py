async def test_logbook_stream_user_id_from_parent_context_filtered(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test user attribution from parent context in filtered live event stream.

    Same scenario as test_logbook_stream_user_id_from_parent_context but
    with entity_ids in the subscription, matching what the frontend does.
    This exercises the filtered event subscription path where
    EVENT_CALL_SERVICE must be explicitly included and matched via
    service_data.
    """
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )
    await hass.async_block_till_done()

    setup_thermostat_context_test_entities(hass)
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)
    now = dt_util.utcnow()
    websocket_client = await hass_ws_client()
    # Subscribe with entity_ids, matching what the frontend logbook card does
    end_time = now + timedelta(hours=3)
    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logbook/event_stream",
            "start_time": now.isoformat(),
            "end_time": end_time.isoformat(),
            "entity_ids": ["climate.living_room", "switch.heater"],
        }
    )

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    # Receive historical events (partial) and sync message
    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["event"]["partial"] is True

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["event"]["events"] == []

    # Simulate the full chain as live events
    parent_context, _ = simulate_thermostat_context_chain(hass)
    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"

    assert_thermostat_context_chain_events(msg["event"]["events"], parent_context)