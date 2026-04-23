async def test_audio_pipeline_with_wake_word_timeout(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    init_components,
    snapshot: SnapshotAssertion,
) -> None:
    """Test timeout from a pipeline run with audio input/output + wake word."""
    events = []
    client = await hass_ws_client(hass)

    with patch(
        "homeassistant.components.tts.secrets.token_urlsafe", return_value="test_token"
    ):
        await client.send_json_auto_id(
            {
                "type": "assist_pipeline/run",
                "start_stage": "wake_word",
                "end_stage": "tts",
                "input": {
                    "sample_rate": SAMPLE_RATE,
                    "timeout": 1,
                },
            }
        )

        # result
        msg = await client.receive_json()
        assert msg["success"], msg

        # run start
        msg = await client.receive_json()
        assert msg["event"]["type"] == "run-start"
        msg["event"]["data"]["pipeline"] = ANY
        assert msg["event"]["data"] == snapshot
        events.append(msg["event"])

        # wake_word
        msg = await client.receive_json()
        assert msg["event"]["type"] == "wake_word-start"
        assert msg["event"]["data"] == snapshot
        events.append(msg["event"])

        # 2 seconds of silence
        await client.send_bytes(bytes([1]) + bytes(2 * BYTES_ONE_SECOND))

        # Time out error
        msg = await client.receive_json()
        assert msg["event"]["type"] == "error"
        assert msg["event"]["data"] == snapshot
        events.append(msg["event"])

        # run end
        msg = await client.receive_json()
        assert msg["event"]["type"] == "run-end"
        assert msg["event"]["data"] == snapshot
        events.append(msg["event"])