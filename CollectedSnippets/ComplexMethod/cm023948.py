async def test_script_mode_2(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    script_mode,
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
            "mode": script_mode,
        }
    }
    client = await hass_ws_client()
    hass.bus.async_listen(event, _handle_event)
    assert await async_setup_component(hass, "script", {"script": script_config})

    hass.states.async_set("switch.test", "on")
    await hass.services.async_call("script", "script1")
    await asyncio.wait_for(flag.wait(), 1)

    # List traces
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": "script"})
    response = await client.receive_json()
    assert response["success"]
    trace = _find_traces(response["result"], "script", "script1")[0]
    assert trace["state"] == "running"

    # Start second run of script while first run is suspended in wait_template.

    flag.clear()
    await hass.services.async_call("script", "script1")
    await asyncio.wait_for(flag.wait(), 1)

    # List traces
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": "script"})
    response = await client.receive_json()
    assert response["success"]
    trace = _find_traces(response["result"], "script", "script1")[1]
    assert trace["state"] == "running"

    # Let both scripts finish
    hass.states.async_set("switch.test", "off")
    await hass.async_block_till_done()

    # List traces
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": "script"})
    response = await client.receive_json()
    assert response["success"]
    trace = _find_traces(response["result"], "script", "script1")[0]
    assert trace["state"] == "stopped"
    assert trace["script_execution"] == script_execution
    trace = _find_traces(response["result"], "script", "script1")[1]
    assert trace["state"] == "stopped"
    assert trace["script_execution"] == "finished"