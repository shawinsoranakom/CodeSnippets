async def test_pipeline_debug_get_run_wrong_pipeline_run(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    init_components,
) -> None:
    """Test debug listing events from a pipeline."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/run",
            "start_stage": "intent",
            "end_stage": "intent",
            "input": {"text": "Are the lights on?"},
        }
    )

    # result
    msg = await client.receive_json()
    assert msg["success"]

    # consume events
    msg = await client.receive_json()
    assert msg["event"]["type"] == "run-start"

    msg = await client.receive_json()
    assert msg["event"]["type"] == "intent-start"

    msg = await client.receive_json()
    assert msg["event"]["type"] == "intent-end"

    msg = await client.receive_json()
    assert msg["event"]["type"] == "run-end"

    # Get the id of the pipeline
    await client.send_json_auto_id({"type": "assist_pipeline/pipeline/list"})
    msg = await client.receive_json()
    assert msg["success"]
    assert len(msg["result"]["pipelines"]) == 1
    pipeline_id = msg["result"]["pipelines"][0]["id"]

    # get debug data for the wrong run
    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline_debug/get",
            "pipeline_id": pipeline_id,
            "pipeline_run_id": "blah",
        }
    )
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"] == {
        "code": "not_found",
        "message": "pipeline_run_id blah not found",
    }