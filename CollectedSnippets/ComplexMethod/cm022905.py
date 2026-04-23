async def test_wake_word_cooldown_same_id(
    hass: HomeAssistant,
    init_components,
    mock_wake_word_provider_entity: MockWakeWordEntity,
    hass_ws_client: WebSocketGenerator,
    snapshot: SnapshotAssertion,
) -> None:
    """Test that duplicate wake word detections with the same id are blocked during the cooldown period."""
    client_1 = await hass_ws_client(hass)
    client_2 = await hass_ws_client(hass)

    await client_1.send_json_auto_id(
        {
            "type": "assist_pipeline/run",
            "start_stage": "wake_word",
            "end_stage": "tts",
            "input": {"sample_rate": SAMPLE_RATE, "no_vad": True},
        }
    )

    await client_2.send_json_auto_id(
        {
            "type": "assist_pipeline/run",
            "start_stage": "wake_word",
            "end_stage": "tts",
            "input": {"sample_rate": SAMPLE_RATE, "no_vad": True},
        }
    )

    # result
    msg = await client_1.receive_json()
    assert msg["success"], msg

    msg = await client_2.receive_json()
    assert msg["success"], msg

    # run start
    msg = await client_1.receive_json()
    assert msg["event"]["type"] == "run-start"
    msg["event"]["data"]["pipeline"] = ANY
    handler_id_1 = msg["event"]["data"]["runner_data"]["stt_binary_handler_id"]
    assert msg["event"]["data"] == snapshot

    msg = await client_2.receive_json()
    assert msg["event"]["type"] == "run-start"
    msg["event"]["data"]["pipeline"] = ANY
    handler_id_2 = msg["event"]["data"]["runner_data"]["stt_binary_handler_id"]
    assert msg["event"]["data"] == snapshot

    # wake_word
    msg = await client_1.receive_json()
    assert msg["event"]["type"] == "wake_word-start"
    assert msg["event"]["data"] == snapshot

    msg = await client_2.receive_json()
    assert msg["event"]["type"] == "wake_word-start"
    assert msg["event"]["data"] == snapshot

    # Wake both up at the same time
    await client_1.send_bytes(bytes([handler_id_1]) + make_10ms_chunk(b"wake word"))
    await client_2.send_bytes(bytes([handler_id_2]) + make_10ms_chunk(b"wake word"))

    # Get response events
    error_data: dict[str, Any] | None = None
    msg = await client_1.receive_json()
    event_type_1 = msg["event"]["type"]
    assert msg["event"]["data"] == snapshot
    if event_type_1 == "error":
        error_data = msg["event"]["data"]

    msg = await client_2.receive_json()
    event_type_2 = msg["event"]["type"]
    assert msg["event"]["data"] == snapshot
    if event_type_2 == "error":
        error_data = msg["event"]["data"]

    # One should be a wake up, one should be an error
    assert {event_type_1, event_type_2} == {"wake_word-end", "error"}
    assert error_data is not None
    assert error_data["code"] == "duplicate_wake_up_detected"