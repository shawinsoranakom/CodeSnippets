async def test_recorder_is_far_behind(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    caplog: pytest.LogCaptureFixture,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test we still start live streaming if the recorder is far behind."""
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
    await async_wait_recording_done(hass)

    # Block the recorder queue
    await async_block_recorder(hass, 0.3)
    await hass.async_block_till_done()

    websocket_client = await hass_ws_client()
    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logbook/event_stream",
            "start_time": now.isoformat(),
            "device_ids": [device.id],
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
    await async_wait_recording_done(hass)

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == []

    hass.bus.async_fire("mock_event", {"device_id": device.id, "message": "1"})
    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == [
        {"domain": "test", "message": "1", "name": "device name", "when": ANY}
    ]

    hass.bus.async_fire("mock_event", {"device_id": device.id, "message": "2"})
    await hass.async_block_till_done()

    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["events"] == [
        {"domain": "test", "message": "2", "name": "device name", "when": ANY}
    ]

    await websocket_client.send_json(
        {"id": 8, "type": "unsubscribe_events", "subscription": 7}
    )
    msg = await asyncio.wait_for(websocket_client.receive_json(), 2)

    assert msg["id"] == 8
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]