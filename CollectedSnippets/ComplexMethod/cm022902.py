async def test_audio_pipeline_debug(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    init_components,
    snapshot: SnapshotAssertion,
) -> None:
    """Test debug listing events from a pipeline run with audio input/output."""
    events = []
    client = await hass_ws_client(hass)

    with patch(
        "homeassistant.components.tts.secrets.token_urlsafe", return_value="test_token"
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

        msg = await client.receive_json()
        assert msg["event"]["type"] == "stt-end"
        assert msg["event"]["data"] == snapshot
        events.append(msg["event"])

        # intent
        msg = await client.receive_json()
        assert msg["event"]["type"] == "intent-start"
        assert msg["event"]["data"] == snapshot
        events.append(msg["event"])

        msg = await client.receive_json()
        assert msg["event"]["type"] == "intent-end"
        assert msg["event"]["data"] == snapshot
        events.append(msg["event"])

        # text-to-speech
        msg = await client.receive_json()
        assert msg["event"]["type"] == "tts-start"
        assert msg["event"]["data"] == snapshot
        events.append(msg["event"])

        msg = await client.receive_json()
        assert msg["event"]["type"] == "tts-end"
        assert msg["event"]["data"] == snapshot
        events.append(msg["event"])

        # run end
        msg = await client.receive_json()
        assert msg["event"]["type"] == "run-end"
        assert msg["event"]["data"] == snapshot
        events.append(msg["event"])

        # Get the id of the pipeline
        await client.send_json_auto_id({"type": "assist_pipeline/pipeline/list"})
        msg = await client.receive_json()
        assert msg["success"]
        assert len(msg["result"]["pipelines"]) == 1

        pipeline_id = msg["result"]["pipelines"][0]["id"]

        # Get the id for the run
        await client.send_json_auto_id(
            {"type": "assist_pipeline/pipeline_debug/list", "pipeline_id": pipeline_id}
        )
        msg = await client.receive_json()
        assert msg["success"]
        assert msg["result"] == {"pipeline_runs": [ANY]}

        pipeline_run_id = msg["result"]["pipeline_runs"][0]["pipeline_run_id"]

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