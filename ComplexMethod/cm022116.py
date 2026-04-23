async def test_logbook_stream_user_id_from_parent_context(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test user attribution from parent context in live event stream.

    Simulates the generic_thermostat pattern where a child context
    (no user_id) is created for the heater service call, while the
    parent context (from the user's set_hvac_mode call) has the user_id.

    The live stream uses memoize_new_contexts=False, so context_lookup
    is empty. User_id must be resolved via the context_user_ids map.
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
    await websocket_client.send_json(
        {"id": 7, "type": "logbook/event_stream", "start_time": now.isoformat()}
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

    # Simulate the full generic_thermostat chain as live events
    parent_context, _ = simulate_thermostat_context_chain(hass)
    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"

    assert_thermostat_context_chain_events(msg["event"]["events"], parent_context)