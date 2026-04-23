async def test_stt_stream_failed(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    init_components,
    snapshot: SnapshotAssertion,
) -> None:
    """Test events from a pipeline run with a non-existent STT provider."""
    events = []
    client = await hass_ws_client(hass)

    with patch(
        "tests.components.assist_pipeline.conftest.MockSTTProviderEntity.async_process_audio_stream",
        side_effect=RuntimeError,
    ):
        await client.send_json_auto_id(
            {
                "type": "assist_pipeline/run",
                "start_stage": "stt",
                "end_stage": "tts",
                "input": {
                    "sample_rate": 44100,
                },
            }
        )

        # result
        msg = await client.receive_json()
        assert msg["success"]

        # run start
        msg = await client.receive_json()
        assert msg["event"]["type"] == "run-start"
        msg["event"]["data"]["pipeline"] = ANY
        assert msg["event"]["data"] == snapshot
        handler_id = msg["event"]["data"]["runner_data"]["stt_binary_handler_id"]
        events.append(msg["event"])

        # stt
        msg = await client.receive_json()
        assert msg["event"]["type"] == "stt-start"
        assert msg["event"]["data"] == snapshot
        events.append(msg["event"])

        # End of audio stream (handler id + empty payload)
        await client.send_bytes(bytes([handler_id]))

        # stt error
        msg = await client.receive_json()
        assert msg["event"]["type"] == "error"
        assert msg["event"]["data"]["code"] == "stt-stream-failed"
        events.append(msg["event"])

        # run end
        msg = await client.receive_json()
        assert msg["event"]["type"] == "run-end"
        assert msg["event"]["data"] == snapshot
        events.append(msg["event"])

    pipeline_data: PipelineData = hass.data[DOMAIN]
    pipeline_id = list(pipeline_data.pipeline_debug)[0]
    pipeline_run_id = list(pipeline_data.pipeline_debug[pipeline_id])[0]

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline_debug/get",
            "pipeline_id": pipeline_id,
            "pipeline_run_id": pipeline_run_id,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {"events": events}