async def test_device_capture_queue_full(
    hass: HomeAssistant,
    init_components,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test audio capture from a satellite device when the recording queue fills up."""
    entry = MockConfigEntry()
    entry.add_to_hass(hass)
    satellite_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("demo", "satellite-1234")},
    )

    class FakeQueue(asyncio.Queue):
        """Queue that reports full for anything but None."""

        def put_nowait(self, item):
            if item is not None:
                raise asyncio.QueueFull

            super().put_nowait(item)

    with patch(
        "homeassistant.components.assist_pipeline.websocket_api.DeviceAudioQueue"
    ) as mock:
        mock.return_value = DeviceAudioQueue(queue=FakeQueue())

        # Start capture
        client_capture = await hass_ws_client(hass)
        await client_capture.send_json_auto_id(
            {
                "type": "assist_pipeline/device/capture",
                "timeout": 30,
                "device_id": satellite_device.id,
            }
        )

        # result
        msg = await client_capture.receive_json()
        assert msg["success"]

    # Run pipeline
    client_pipeline = await hass_ws_client(hass)
    await client_pipeline.send_json_auto_id(
        {
            "type": "assist_pipeline/run",
            "start_stage": "stt",
            "end_stage": "stt",
            "input": {"sample_rate": SAMPLE_RATE, "no_vad": True},
            "device_id": satellite_device.id,
        }
    )

    # result
    msg = await client_pipeline.receive_json()
    assert msg["success"]

    # run start
    msg = await client_pipeline.receive_json()
    assert msg["event"]["type"] == "run-start"
    msg["event"]["data"]["pipeline"] = ANY
    assert msg["event"]["data"] == snapshot
    handler_id = msg["event"]["data"]["runner_data"]["stt_binary_handler_id"]

    # stt
    msg = await client_pipeline.receive_json()
    assert msg["event"]["type"] == "stt-start"
    assert msg["event"]["data"] == snapshot

    # Single chunk will "overflow" the queue
    await client_pipeline.send_bytes(bytes([handler_id]) + bytes(BYTES_PER_CHUNK))

    # End of audio stream
    await client_pipeline.send_bytes(bytes([handler_id]))

    msg = await client_pipeline.receive_json()
    assert msg["event"]["type"] == "stt-end"
    assert msg["event"]["data"] == snapshot

    msg = await client_pipeline.receive_json()
    assert msg["event"]["type"] == "run-end"
    assert msg["event"]["data"] == snapshot

    # Queue should have been overflowed
    async with asyncio.timeout(1):
        msg = await client_capture.receive_json()
        assert msg["type"] == "event"
        assert msg["event"] == snapshot
        assert msg["event"]["type"] == "end"
        assert msg["event"]["overflow"]