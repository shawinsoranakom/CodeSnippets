async def test_subscribe_unsubscribe_logbook_stream_device(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test subscribe/unsubscribe logbook stream with a device."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )
    devices = await _async_mock_devices_with_logbook_platform(hass, device_registry)
    device = devices[0]
    device2 = devices[1]

    await hass.async_block_till_done()

    await async_wait_recording_done(hass)
    websocket_client = await hass_ws_client()
    init_listeners = hass.bus.async_listeners()
    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logbook/event_stream",
            "start_time": now.isoformat(),
            "device_ids": [device.id, device2.id],
        }
    )

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    await async_wait_recording_done(hass)

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
    hass.bus.async_fire("mock_event", {"device_id": device.id})
    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == [
        {"domain": "test", "message": "is on fire", "name": "device name", "when": ANY}
    ]

    for _ in range(3):
        hass.bus.async_fire("mock_event", {"device_id": device.id})
        hass.bus.async_fire("mock_event", {"device_id": device2.id})
        await hass.async_block_till_done()

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