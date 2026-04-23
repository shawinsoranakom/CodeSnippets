async def test_subscribe_all_entities_have_uom_multiple(
    recorder_mock: Recorder, hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test logbook stream with specific request for multiple entities that are always filtered."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )
    await async_wait_recording_done(hass)
    entity_ids = ("sensor.uom", "sensor.uom_two")

    def _cycle_entities():
        for entity_id in entity_ids:
            for state in ("1", "2", "3"):
                hass.states.async_set(
                    entity_id, state, {ATTR_UNIT_OF_MEASUREMENT: "any"}
                )

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
            "entity_ids": [*entity_ids],
        }
    )

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    _cycle_entities()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == []

    await websocket_client.close()
    await hass.async_block_till_done()

    # Check our listener got unsubscribed
    assert listeners_without_writes(
        hass.bus.async_listeners()
    ) == listeners_without_writes(init_listeners)