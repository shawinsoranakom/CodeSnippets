async def test_consistent_stream_and_recorder_filtering(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_id: str,
    attributes: dict,
    result_count: int,
) -> None:
    """Test that the logbook live stream and get_events apis use consistent filtering rules."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )
    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)

    hass.states.async_set(entity_id, "1.0", attributes)
    hass.states.async_set("binary_sensor.other_entity", "off")

    await hass.async_block_till_done()

    await async_wait_recording_done(hass)

    websocket_client = await hass_ws_client()
    await websocket_client.send_json(
        {
            "id": 1,
            "type": "logbook/event_stream",
            "start_time": now.isoformat(),
            "entity_ids": [entity_id, "binary_sensor.other_entity"],
        }
    )

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 1
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 1
    assert msg["type"] == "event"
    assert msg["event"]["events"] == []
    assert "partial" in msg["event"]
    await async_wait_recording_done(hass)

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 1
    assert msg["type"] == "event"
    assert msg["event"]["events"] == []
    assert "partial" not in msg["event"]
    await async_wait_recording_done(hass)

    hass.states.async_set(
        entity_id,
        "2.0",
        attributes,
    )
    hass.states.async_set("binary_sensor.other_entity", "on")
    await get_instance(hass).async_block_till_done()
    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 1
    assert msg["type"] == "event"
    assert "partial" not in msg["event"]
    assert len(msg["event"]["events"]) == 1 + result_count

    await hass.async_block_till_done()

    await async_wait_recording_done(hass)

    await websocket_client.send_json(
        {
            "id": 2,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
            "entity_ids": [entity_id],
        }
    )
    response = await websocket_client.receive_json()
    assert response["success"]
    assert response["id"] == 2

    results = response["result"]
    assert len(results) == result_count