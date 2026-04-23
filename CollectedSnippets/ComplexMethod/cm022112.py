async def test_logbook_stream_ignores_forced_updates(
    recorder_mock: Recorder, hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test logbook live stream ignores forced updates."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )

    await hass.async_block_till_done()

    hass.states.async_set("binary_sensor.is_light", STATE_ON)
    hass.states.async_set("binary_sensor.is_light", STATE_OFF)
    state: State = hass.states.get("binary_sensor.is_light")
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)
    websocket_client = await hass_ws_client()
    init_listeners = hass.bus.async_listeners()
    await websocket_client.send_json(
        {"id": 7, "type": "logbook/event_stream", "start_time": now.isoformat()}
    )

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == [
        {
            "entity_id": "binary_sensor.is_light",
            "state": "off",
            "when": state.last_updated_timestamp,
        }
    ]
    assert msg["event"]["start_time"] == now.timestamp()
    assert msg["event"]["end_time"] > msg["event"]["start_time"]
    assert msg["event"]["partial"] is True

    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert "partial" not in msg["event"]["events"]
    assert msg["event"]["events"] == []

    hass.states.async_set("binary_sensor.is_light", STATE_ON)
    hass.states.async_set("binary_sensor.is_light", STATE_OFF)

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert "partial" not in msg["event"]["events"]
    assert msg["event"]["events"] == [
        {
            "entity_id": "binary_sensor.is_light",
            "state": STATE_ON,
            "when": ANY,
        },
        {
            "entity_id": "binary_sensor.is_light",
            "state": STATE_OFF,
            "when": ANY,
        },
    ]

    # Now we force an update to make sure we ignore
    # forced updates when the state has not actually changed

    hass.states.async_set("binary_sensor.is_light", STATE_ON)
    for _ in range(3):
        hass.states.async_set("binary_sensor.is_light", STATE_OFF, force_update=True)

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert "partial" not in msg["event"]["events"]
    assert msg["event"]["events"] == [
        {
            "entity_id": "binary_sensor.is_light",
            "state": STATE_ON,
            "when": ANY,
        },
        # We should only get the first one and ignore
        # the other forced updates since the state
        # has not actually changed
        {
            "entity_id": "binary_sensor.is_light",
            "state": STATE_OFF,
            "when": ANY,
        },
    ]

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