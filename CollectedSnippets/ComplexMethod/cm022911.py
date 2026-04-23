async def test_pipeline_empty_tts_output(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    init_components,
    snapshot: SnapshotAssertion,
) -> None:
    """Test events from a pipeline run with a empty text-to-speech text."""
    events = []
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/run",
            "start_stage": "intent",
            "end_stage": "tts",
            "input": {
                "text": "never mind",
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