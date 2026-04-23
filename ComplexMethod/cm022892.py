async def test_text_only_pipeline(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    init_components,
    snapshot: SnapshotAssertion,
    extra_msg: dict[str, Any],
) -> None:
    """Test events from a pipeline run with text input (no STT/TTS)."""
    events = []
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/run",
            "start_stage": "intent",
            "end_stage": "intent",
            "input": {"text": "Are the lights on?"},
            "conversation_id": "mock-conversation-id",
            "device_id": "mock-device-id",
        }
        | extra_msg
    )

    # result
    msg = await client.receive_json()
    assert msg["success"]

    # run start
    msg = await client.receive_json()
    assert msg["event"]["type"] == "run-start"
    msg["event"]["data"]["pipeline"] = ANY
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