async def test_subscribe_disconnected(
    recorder_mock: Recorder, hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test subscribe/unsubscribe logbook stream gets disconnected."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )
    await async_wait_recording_done(hass)

    hass.states.async_set("light.small", STATE_ON)
    hass.states.async_set("binary_sensor.is_light", STATE_ON)
    hass.states.async_set("binary_sensor.is_light", STATE_OFF)
    state: State = hass.states.get("binary_sensor.is_light")
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)
    # We will compare event subscriptions after closing the websocket connection,
    # count the listeners before setting it up
    init_listeners = hass.bus.async_listeners()
    websocket_client = await hass_ws_client()
    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logbook/event_stream",
            "start_time": now.isoformat(),
            "entity_ids": ["light.small", "binary_sensor.is_light"],
        }
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

    await websocket_client.close()
    await hass.async_block_till_done()

    # Check our listener got unsubscribed
    assert listeners_without_writes(
        hass.bus.async_listeners()
    ) == listeners_without_writes(init_listeners)