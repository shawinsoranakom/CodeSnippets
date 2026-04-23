async def test_stt_cooldown_same_id(
    hass: HomeAssistant,
    init_components,
    mock_stt_provider,
    hass_ws_client: WebSocketGenerator,
    snapshot: SnapshotAssertion,
) -> None:
    """Test that two speech-to-text pipelines cannot run within the cooldown period if they have the same wake word."""
    client_1 = await hass_ws_client(hass)
    client_2 = await hass_ws_client(hass)

    await client_1.send_json_auto_id(
        {
            "type": "assist_pipeline/run",
            "start_stage": "stt",
            "end_stage": "tts",
            "input": {
                "sample_rate": SAMPLE_RATE,
                "wake_word_phrase": "ok_nabu",
            },
        }
    )

    await client_2.send_json_auto_id(
        {
            "type": "assist_pipeline/run",
            "start_stage": "stt",
            "end_stage": "tts",
            "input": {
                "sample_rate": SAMPLE_RATE,
                "wake_word_phrase": "ok_nabu",
            },
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
    assert msg["event"]["data"] == snapshot

    msg = await client_2.receive_json()
    assert msg["event"]["type"] == "run-start"
    msg["event"]["data"]["pipeline"] = ANY
    assert msg["event"]["data"] == snapshot

    # Get response events
    error_data: dict[str, Any] | None = None
    msg = await client_1.receive_json()
    event_type_1 = msg["event"]["type"]
    if event_type_1 == "error":
        error_data = msg["event"]["data"]

    msg = await client_2.receive_json()
    event_type_2 = msg["event"]["type"]
    if event_type_2 == "error":
        error_data = msg["event"]["data"]

    # One should be a stt start, one should be an error
    assert {event_type_1, event_type_2} == {"stt-start", "error"}
    assert error_data is not None
    assert error_data["code"] == "duplicate_wake_up_detected"