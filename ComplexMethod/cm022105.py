async def test_live_stream_with_one_second_commit_interval(
    async_setup_recorder_instance: RecorderInstanceGenerator,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test the recorder with a 1s commit interval."""
    config = {recorder.CONF_COMMIT_INTERVAL: 0.5}
    await async_setup_recorder_instance(hass, config)
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )
    devices = await _async_mock_devices_with_logbook_platform(hass, device_registry)
    device = devices[0]

    await hass.async_block_till_done()

    hass.bus.async_fire("mock_event", {"device_id": device.id, "message": "1"})

    await async_wait_recording_done(hass)

    hass.bus.async_fire("mock_event", {"device_id": device.id, "message": "2"})

    await hass.async_block_till_done()

    hass.bus.async_fire("mock_event", {"device_id": device.id, "message": "3"})

    websocket_client = await hass_ws_client()
    init_listeners = hass.bus.async_listeners()
    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logbook/event_stream",
            "start_time": now.isoformat(),
            "device_ids": [device.id],
        }
    )
    hass.bus.async_fire("mock_event", {"device_id": device.id, "message": "4"})

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    hass.bus.async_fire("mock_event", {"device_id": device.id, "message": "5"})

    received_rows = []
    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    received_rows.extend(msg["event"]["events"])

    hass.bus.async_fire("mock_event", {"device_id": device.id, "message": "6"})

    await hass.async_block_till_done()

    hass.bus.async_fire("mock_event", {"device_id": device.id, "message": "7"})

    while len(received_rows) < 7:
        msg = await asyncio.wait_for(websocket_client.receive_json(), 2.5)
        assert msg["id"] == 7
        assert msg["type"] == "event"
        received_rows.extend(msg["event"]["events"])

    # Make sure we get rows back in order
    assert received_rows == [
        {"domain": "test", "message": "1", "name": "device name", "when": ANY},
        {"domain": "test", "message": "2", "name": "device name", "when": ANY},
        {"domain": "test", "message": "3", "name": "device name", "when": ANY},
        {"domain": "test", "message": "4", "name": "device name", "when": ANY},
        {"domain": "test", "message": "5", "name": "device name", "when": ANY},
        {"domain": "test", "message": "6", "name": "device name", "when": ANY},
        {"domain": "test", "message": "7", "name": "device name", "when": ANY},
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