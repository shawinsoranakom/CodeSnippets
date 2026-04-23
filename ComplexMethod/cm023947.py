async def test_script_mode(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    script_mode,
    max_runs,
    script_execution,
) -> None:
    """Test overlapping runs with max_runs > 1."""
    msg_id = 1

    def next_id():
        nonlocal msg_id
        msg_id += 1
        return msg_id

    flag = asyncio.Event()

    @callback
    def _handle_event(_):
        flag.set()

    event = "test_event"
    script_config = {
        "script1": {
            "sequence": [
                {"event": event, "event_data": {"value": 1}},
                {"wait_template": "{{ states.switch.test.state == 'off' }}"},
                {"event": event, "event_data": {"value": 2}},
            ],
            **script_mode,
        },
    }
    client = await hass_ws_client()
    hass.bus.async_listen(event, _handle_event)
    assert await async_setup_component(hass, "script", {"script": script_config})

    for _ in range(max_runs):
        hass.states.async_set("switch.test", "on")
        await hass.services.async_call("script", "script1")
        await asyncio.wait_for(flag.wait(), 1)

    # List traces
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": "script"})
    response = await client.receive_json()
    assert response["success"]
    traces = _find_traces(response["result"], "script", "script1")
    assert len(traces) == max_runs
    for trace in traces:
        assert trace["state"] == "running"

    # Start additional run of script while first runs are suspended in wait_template.

    flag.clear()
    await hass.services.async_call("script", "script1")

    # List traces
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": "script"})
    response = await client.receive_json()
    assert response["success"]
    traces = _find_traces(response["result"], "script", "script1")
    assert len(traces) == max_runs + 1
    assert traces[-1]["state"] == "stopped"
    assert traces[-1]["script_execution"] == script_execution