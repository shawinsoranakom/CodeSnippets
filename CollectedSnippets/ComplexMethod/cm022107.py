async def test_stream_consumer_stop_processing(
    recorder_mock: Recorder, hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test we unsubscribe if the stream consumer fails or is canceled."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )
    await async_wait_recording_done(hass)
    init_listeners = hass.bus.async_listeners()
    hass.states.async_set("light.small", STATE_ON)
    hass.states.async_set("binary_sensor.is_light", STATE_ON)
    hass.states.async_set("binary_sensor.is_light", STATE_OFF)
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)
    websocket_client = await hass_ws_client()

    after_ws_created_listeners = hass.bus.async_listeners()

    with (
        patch.object(websocket_api, "MAX_PENDING_LOGBOOK_EVENTS", 5),
        patch.object(websocket_api, "_async_events_consumer"),
    ):
        await websocket_client.send_json(
            {
                "id": 7,
                "type": "logbook/event_stream",
                "start_time": now.isoformat(),
                "entity_ids": ["light.small", "binary_sensor.is_light"],
            }
        )
        await async_wait_recording_done(hass)

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    assert listeners_without_writes(
        hass.bus.async_listeners()
    ) != listeners_without_writes(init_listeners)
    for _ in range(5):
        hass.states.async_set("binary_sensor.is_light", STATE_ON)
        hass.states.async_set("binary_sensor.is_light", STATE_OFF)
    await async_wait_recording_done(hass)

    # Check our listener got unsubscribed because
    # the queue got full and the overload safety tripped
    assert listeners_without_writes(
        hass.bus.async_listeners()
    ) == listeners_without_writes(after_ws_created_listeners)
    await websocket_client.close()
    assert listeners_without_writes(
        hass.bus.async_listeners()
    ) == listeners_without_writes(init_listeners)