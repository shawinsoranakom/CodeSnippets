async def test_logbook_stream_match_multiple_entities_one_with_broken_logbook_platform(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test logbook stream with a described integration that uses multiple entities.

    One of the entities has a broken logbook platform.
    """
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )
    entry = await _async_mock_entity_with_broken_logbook_platform(hass, entity_registry)
    entity_id = entry.entity_id
    hass.states.async_set(entity_id, STATE_ON)

    await hass.async_block_till_done()

    await async_wait_recording_done(hass)
    websocket_client = await hass_ws_client()
    init_listeners = hass.bus.async_listeners()
    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logbook/event_stream",
            "start_time": now.isoformat(),
            "entity_ids": [entity_id],
        }
    )

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    # There are no answers to our initial query
    # so we get an empty reply. This is to ensure
    # consumers of the api know there are no results
    # and its not a failure case. This is useful
    # in the frontend so we can tell the user there
    # are no results vs waiting for them to appear
    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == []
    assert "partial" in msg["event"]
    await async_wait_recording_done(hass)

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == []
    assert "partial" not in msg["event"]
    await async_wait_recording_done(hass)

    hass.states.async_set("binary_sensor.should_not_appear", STATE_ON)
    hass.states.async_set("binary_sensor.should_not_appear", STATE_OFF)
    context = core.Context(
        id="01GTDGKBCH00GW0X276W5TEDDD",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )
    hass.bus.async_fire(
        "mock_event", {"entity_id": ["sensor.any", entity_id]}, context=context
    )
    hass.bus.async_fire("mock_event", {"entity_id": [f"sensor.any,{entity_id}"]})
    hass.bus.async_fire("mock_event", {"entity_id": ["sensor.no_match", "light.off"]})
    hass.states.async_set(entity_id, STATE_OFF, context=context)
    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == [
        {
            "entity_id": "sensor.test",
            "context_domain": "test",
            "context_event_type": "mock_event",
            "context_user_id": "b400facee45711eaa9308bfd3d19e474",
            "state": "off",
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

    assert "Error with test describe event" in caplog.text