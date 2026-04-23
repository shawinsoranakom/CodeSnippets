async def test_trace_blueprint_automation(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test trace of blueprint automation."""
    await async_setup_component(hass, "homeassistant", {})
    msg_id = 1

    def next_id():
        nonlocal msg_id
        msg_id += 1
        return msg_id

    domain = "automation"
    sun_config = {
        "id": "sun",
        "use_blueprint": {
            "path": "test_event_service.yaml",
            "input": {
                "trigger_event": "blueprint_event",
                "service_to_call": "test.automation",
                "a_number": 5,
            },
        },
    }
    sun_action = {
        "params": {
            "domain": "test",
            "service": "automation",
            "service_data": {},
            "target": {"entity_id": ["light.kitchen"]},
        },
        "running_script": False,
    }
    assert await async_setup_component(hass, "automation", {"automation": sun_config})
    client = await hass_ws_client()
    hass.bus.async_fire("blueprint_event")
    await hass.async_block_till_done()

    # List traces
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": domain})
    response = await client.receive_json()
    assert response["success"]
    run_id = _find_run_id(response["result"], domain, "sun")

    # Get trace
    await client.send_json(
        {
            "id": next_id(),
            "type": "trace/get",
            "domain": domain,
            "item_id": "sun",
            "run_id": run_id,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    trace = response["result"]
    assert set(trace["trace"]) == {"trigger/0", "action/0"}
    assert len(trace["trace"]["action/0"]) == 1
    assert trace["trace"]["action/0"][0]["error"]
    assert trace["trace"]["action/0"][0]["result"] == sun_action
    assert trace["config"]["id"] == "sun"
    assert trace["blueprint_inputs"] == sun_config
    assert trace["context"]
    assert trace["error"] == "Action test.automation not found"
    assert trace["state"] == "stopped"
    assert trace["script_execution"] == "error"
    assert trace["item_id"] == "sun"
    assert trace.get("trigger", UNDEFINED) == "event 'blueprint_event'"