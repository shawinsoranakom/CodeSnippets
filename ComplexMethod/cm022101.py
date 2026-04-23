async def test_subscribe_unsubscribe_logbook_stream_big_query(
    recorder_mock: Recorder, hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test subscribe/unsubscribe logbook stream and ask for a large time frame.

    We should get the data for the first 24 hours in the first message, and
    anything older will come in a followup message.
    """
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )

    await hass.async_block_till_done()
    four_days_ago = now - timedelta(days=4)
    five_days_ago = now - timedelta(days=5)

    with freeze_time(four_days_ago):
        hass.states.async_set("binary_sensor.four_days_ago", STATE_ON)
        hass.states.async_set("binary_sensor.four_days_ago", STATE_OFF)
        four_day_old_state: State = hass.states.get("binary_sensor.four_days_ago")
        await hass.async_block_till_done()

    await async_wait_recording_done(hass)
    # Verify our state was recorded in the past
    assert (now - four_day_old_state.last_updated).total_seconds() > 86400 * 3

    hass.states.async_set("binary_sensor.is_light", STATE_OFF)
    hass.states.async_set("binary_sensor.is_light", STATE_ON)
    current_state: State = hass.states.get("binary_sensor.is_light")

    # Verify our new state was recorded in the recent timeframe
    assert (now - current_state.last_updated).total_seconds() < 2

    await async_wait_recording_done(hass)

    websocket_client = await hass_ws_client()
    init_listeners = hass.bus.async_listeners()
    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logbook/event_stream",
            "start_time": five_days_ago.isoformat(),
        }
    )

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    # With a big query we get the current state first
    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == [
        {
            "entity_id": "binary_sensor.is_light",
            "state": "on",
            "when": current_state.last_updated_timestamp,
        }
    ]

    # With a big query we get the old states second
    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["partial"] is True
    assert msg["event"]["events"] == [
        {
            "entity_id": "binary_sensor.four_days_ago",
            "state": "off",
            "when": four_day_old_state.last_updated_timestamp,
        }
    ]

    # And finally a response without partial set to indicate no more
    # historical data is coming
    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == []

    await websocket_client.send_json(
        {"id": 8, "type": "unsubscribe_events", "subscription": 7}
    )
    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)

    assert msg["id"] == 8
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    # Check our listener got unsubscribed
    assert listeners_without_writes(
        hass.bus.async_listeners()
    ) == listeners_without_writes(init_listeners)