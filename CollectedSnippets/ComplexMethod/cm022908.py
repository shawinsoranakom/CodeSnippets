async def test_device_capture(
    hass: HomeAssistant,
    init_components,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test audio capture from a satellite device."""
    entry = MockConfigEntry()
    entry.add_to_hass(hass)
    satellite_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("demo", "satellite-1234")},
    )

    audio_chunks = [
        make_10ms_chunk(b"chunk1"),
        make_10ms_chunk(b"chunk2"),
        make_10ms_chunk(b"chunk3"),
    ]

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

    for audio_chunk in audio_chunks:
        await client_pipeline.send_bytes(bytes([handler_id]) + audio_chunk)

    # End of audio stream
    await client_pipeline.send_bytes(bytes([handler_id]))

    msg = await client_pipeline.receive_json()
    assert msg["event"]["type"] == "stt-end"

    # run end
    msg = await client_pipeline.receive_json()
    assert msg["event"]["type"] == "run-end"
    assert msg["event"]["data"] == snapshot

    # Verify capture
    events = []
    async with asyncio.timeout(1):
        while True:
            msg = await client_capture.receive_json()
            assert msg["type"] == "event"
            event_data = msg["event"]
            events.append(event_data)
            if event_data["type"] == "end":
                break

    assert len(events) == len(audio_chunks) + 1

    # Verify audio chunks
    for i, audio_chunk in enumerate(audio_chunks):
        assert events[i]["type"] == "audio"
        assert events[i]["rate"] == SAMPLE_RATE
        assert events[i]["width"] == SAMPLE_WIDTH
        assert events[i]["channels"] == SAMPLE_CHANNELS

        # Audio is base64 encoded
        assert events[i]["audio"] == base64.b64encode(audio_chunk).decode("ascii")

    # Last event is the end
    assert events[-1]["type"] == "end"