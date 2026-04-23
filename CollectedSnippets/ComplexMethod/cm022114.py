async def test_live_stream_with_changed_state_change(
    async_setup_recorder_instance: RecorderInstanceGenerator,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    params: dict[str, Any],
) -> None:
    """Test the live logbook stream with chained events."""
    config = {recorder.CONF_COMMIT_INTERVAL: 0.5}
    await async_setup_recorder_instance(hass, config)
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )

    hass.states.async_set("binary_sensor.is_light", "unavailable")
    hass.states.async_set("binary_sensor.is_light", "unknown")
    await async_wait_recording_done(hass)

    @callback
    def auto_off_listener(event):
        hass.states.async_set("binary_sensor.is_light", STATE_OFF)

    async_track_state_change_event(hass, ["binary_sensor.is_light"], auto_off_listener)

    websocket_client = await hass_ws_client()
    init_listeners = hass.bus.async_listeners()
    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logbook/event_stream",
            "start_time": now.isoformat(),
            **params,
        }
    )

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    await hass.async_block_till_done()
    hass.states.async_set("binary_sensor.is_light", STATE_ON)

    received_rows = []
    while len(received_rows) < 3:
        msg = await asyncio.wait_for(websocket_client.receive_json(), 2.5)
        assert msg["id"] == 7
        assert msg["type"] == "event"
        received_rows.extend(msg["event"]["events"])

    # Make sure we get rows back in order
    assert received_rows == [
        {"entity_id": "binary_sensor.is_light", "state": "unknown", "when": ANY},
        {"entity_id": "binary_sensor.is_light", "state": "on", "when": ANY},
        {"entity_id": "binary_sensor.is_light", "state": "off", "when": ANY},
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