async def test_subscribe_entities_some_have_uom_multiple(
    recorder_mock: Recorder, hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test logbook stream with uom filtered entities and non-filtered entities."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )
    await async_wait_recording_done(hass)
    filtered_entity_ids = ("sensor.uom", "sensor.uom_two")
    non_filtered_entity_ids = ("sensor.keep", "sensor.keep_two")

    def _cycle_entities():
        for entity_id in filtered_entity_ids:
            for state in ("1", "2", "3"):
                hass.states.async_set(
                    entity_id, state, {ATTR_UNIT_OF_MEASUREMENT: "any"}
                )
        for entity_id in non_filtered_entity_ids:
            for state in (STATE_ON, STATE_OFF):
                hass.states.async_set(entity_id, state)

    # We will compare event subscriptions after closing the websocket connection,
    # count the listeners before setting it up
    init_listeners = hass.bus.async_listeners()
    _cycle_entities()

    await async_wait_recording_done(hass)
    websocket_client = await hass_ws_client()
    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logbook/event_stream",
            "start_time": now.isoformat(),
            "entity_ids": [*filtered_entity_ids, *non_filtered_entity_ids],
        }
    )

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    await get_instance(hass).async_block_till_done()
    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == [
        {"entity_id": "sensor.keep", "state": "off", "when": ANY},
        {"entity_id": "sensor.keep_two", "state": "off", "when": ANY},
    ]
    assert msg["event"]["partial"] is True

    await get_instance(hass).async_block_till_done()
    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert "partial" not in msg["event"]
    assert msg["event"]["events"] == []

    _cycle_entities()
    await get_instance(hass).async_block_till_done()
    await hass.async_block_till_done()
    _cycle_entities()
    await get_instance(hass).async_block_till_done()
    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == [
        {"entity_id": "sensor.keep", "state": "on", "when": ANY},
        {"entity_id": "sensor.keep", "state": "off", "when": ANY},
        {"entity_id": "sensor.keep_two", "state": "on", "when": ANY},
        {"entity_id": "sensor.keep_two", "state": "off", "when": ANY},
    ]
    assert "partial" not in msg["event"]

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == [
        {"entity_id": "sensor.keep", "state": "on", "when": ANY},
        {"entity_id": "sensor.keep", "state": "off", "when": ANY},
        {"entity_id": "sensor.keep_two", "state": "on", "when": ANY},
        {"entity_id": "sensor.keep_two", "state": "off", "when": ANY},
    ]

    assert "partial" not in msg["event"]

    await websocket_client.close()
    await hass.async_block_till_done()

    # Check our listener got unsubscribed
    assert listeners_without_writes(
        hass.bus.async_listeners()
    ) == listeners_without_writes(init_listeners)