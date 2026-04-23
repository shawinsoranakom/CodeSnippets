async def test_subscribe_unsubscribe_logbook_stream_entities_with_end_time(
    recorder_mock: Recorder, hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test subscribe/unsubscribe logbook stream with specific entities and an end_time."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )

    await hass.async_block_till_done()
    hass.states.async_set("light.small", STATE_ON)
    hass.states.async_set("binary_sensor.is_light", STATE_ON)
    hass.states.async_set("binary_sensor.is_light", STATE_OFF)
    state: State = hass.states.get("binary_sensor.is_light")
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)
    websocket_client = await hass_ws_client()
    init_listeners = hass.bus.async_listeners()
    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logbook/event_stream",
            "start_time": now.isoformat(),
            "end_time": (now + timedelta(minutes=10)).isoformat(),
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
    assert msg["event"]["partial"] is True
    assert msg["event"]["events"] == [
        {
            "entity_id": "binary_sensor.is_light",
            "state": "off",
            "when": state.last_updated_timestamp,
        }
    ]

    await get_instance(hass).async_block_till_done()
    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert "partial" not in msg["event"]
    assert msg["event"]["events"] == []

    hass.states.async_set("light.alpha", STATE_ON)
    hass.states.async_set("light.alpha", STATE_OFF)
    hass.states.async_set("light.small", STATE_OFF, {"effect": "help", "color": "blue"})

    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert "partial" not in msg["event"]
    assert msg["event"]["events"] == [
        {
            "entity_id": "light.small",
            "state": "off",
            "when": ANY,
        },
    ]

    hass.states.async_remove("light.alpha")
    hass.states.async_remove("light.small")
    await hass.async_block_till_done()

    async_fire_time_changed(hass, now + timedelta(minutes=11))
    await hass.async_block_till_done()

    # These states should not be sent since we should be unsubscribed
    hass.states.async_set("light.small", STATE_ON)
    hass.states.async_set("light.small", STATE_OFF)
    await hass.async_block_till_done()

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