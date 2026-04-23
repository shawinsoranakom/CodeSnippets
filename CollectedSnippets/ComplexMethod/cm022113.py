async def test_subscribe_all_entities_are_continuous_with_device(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test subscribe/unsubscribe logbook stream with entities that are always filtered and a device."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )
    await async_wait_recording_done(hass)
    devices = await _async_mock_devices_with_logbook_platform(hass, device_registry)
    device = devices[0]
    device2 = devices[1]

    entity_ids = ("sensor.uom", "sensor.uom_two")

    def _create_events():
        for entity_id in entity_ids:
            for state in ("1", "2", "3"):
                hass.states.async_set(
                    entity_id, state, {ATTR_UNIT_OF_MEASUREMENT: "any"}
                )
                hass.states.async_set("counter.any", state)
                hass.states.async_set("proximity.any", state)
        hass.bus.async_fire("mock_event", {"device_id": device.id})
        hass.bus.async_fire("mock_event", {"device_id": device2.id})

    # We will compare event subscriptions after closing the websocket connection,
    # count the listeners before setting it up
    init_listeners = hass.bus.async_listeners()
    _create_events()

    await async_wait_recording_done(hass)
    websocket_client = await hass_ws_client()
    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logbook/event_stream",
            "start_time": now.isoformat(),
            "entity_ids": ["sensor.uom", "counter.any", "proximity.any"],
            "device_ids": [device.id, device2.id],
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
        {"domain": "test", "message": "is on fire", "name": "device name", "when": ANY},
        {"domain": "test", "message": "is on fire", "name": "device name", "when": ANY},
    ]
    assert msg["event"]["partial"] is True

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == []
    assert "partial" not in msg["event"]

    for _ in range(2):
        _create_events()
        msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
        assert msg["id"] == 7
        assert msg["type"] == "event"
        assert msg["event"]["events"] == [
            {
                "domain": "test",
                "message": "is on fire",
                "name": "device name",
                "when": ANY,
            },
            {
                "domain": "test",
                "message": "is on fire",
                "name": "device name",
                "when": ANY,
            },
        ]
        assert "partial" not in msg["event"]

    await websocket_client.close()
    await hass.async_block_till_done()

    # Check our listener got unsubscribed
    assert listeners_without_writes(
        hass.bus.async_listeners()
    ) == listeners_without_writes(init_listeners)