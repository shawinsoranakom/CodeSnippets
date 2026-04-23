async def test_list_traces(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    domain,
    prefix,
    trigger,
    last_step,
    script_execution,
) -> None:
    """Test listing script and automation traces."""
    await async_setup_component(hass, "homeassistant", {})
    msg_id = 1

    def next_id():
        nonlocal msg_id
        msg_id += 1
        return msg_id

    sun_config = {
        "id": "sun",
        "triggers": {"platform": "event", "event_type": "test_event"},
        "actions": {"service": "test.automation"},
    }
    moon_config = {
        "id": "moon",
        "triggers": [
            {"platform": "event", "event_type": "test_event2"},
            {"platform": "event", "event_type": "test_event3"},
        ],
        "conditions": {
            "condition": "template",
            "value_template": "{{ trigger.event.event_type=='test_event2' }}",
        },
        "actions": {"event": "another_event"},
    }
    await _setup_automation_or_script(hass, domain, [sun_config, moon_config])

    client = await hass_ws_client()

    await client.send_json({"id": next_id(), "type": "trace/list", "domain": domain})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == []

    await client.send_json(
        {"id": next_id(), "type": "trace/list", "domain": domain, "item_id": "sun"}
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == []

    # Trigger "sun" automation / run "sun" script
    await _run_automation_or_script(hass, domain, sun_config, "test_event")
    await hass.async_block_till_done()

    # List traces
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": domain})
    response = await client.receive_json()
    assert response["success"]
    assert len(response["result"]) == 1
    assert len(_find_traces(response["result"], domain, "sun")) == 1

    await client.send_json(
        {"id": next_id(), "type": "trace/list", "domain": domain, "item_id": "sun"}
    )
    response = await client.receive_json()
    assert response["success"]
    assert len(response["result"]) == 1
    assert len(_find_traces(response["result"], domain, "sun")) == 1

    await client.send_json(
        {"id": next_id(), "type": "trace/list", "domain": domain, "item_id": "moon"}
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == []

    # Trigger "moon" automation, with passing condition / run "moon" script
    await _run_automation_or_script(hass, domain, moon_config, "test_event2")
    await hass.async_block_till_done()

    # Trigger "moon" automation, with failing condition / run "moon" script
    await _run_automation_or_script(hass, domain, moon_config, "test_event3")
    await hass.async_block_till_done()

    # Trigger "moon" automation, with passing condition / run "moon" script
    await _run_automation_or_script(hass, domain, moon_config, "test_event2")
    await hass.async_block_till_done()

    # List traces
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": domain})
    response = await client.receive_json()
    assert response["success"]
    assert len(_find_traces(response["result"], domain, "moon")) == 3
    assert len(_find_traces(response["result"], domain, "sun")) == 1
    trace = _find_traces(response["result"], domain, "sun")[0]
    assert trace["last_step"] == last_step[0].format(prefix=prefix)
    assert trace["error"] == "Action test.automation not found"
    assert trace["state"] == "stopped"
    assert trace["script_execution"] == script_execution[0]
    assert trace["timestamp"]
    assert trace["item_id"] == "sun"
    assert trace.get("trigger", UNDEFINED) == trigger[0]

    trace = _find_traces(response["result"], domain, "moon")[0]
    assert trace["last_step"] == last_step[1].format(prefix=prefix)
    assert "error" not in trace
    assert trace["state"] == "stopped"
    assert trace["script_execution"] == script_execution[1]
    assert trace["timestamp"]
    assert trace["item_id"] == "moon"
    assert trace.get("trigger", UNDEFINED) == trigger[1]

    trace = _find_traces(response["result"], domain, "moon")[1]
    assert trace["last_step"] == last_step[2].format(prefix=prefix)
    assert "error" not in trace
    assert trace["state"] == "stopped"
    assert trace["script_execution"] == script_execution[2]
    assert trace["timestamp"]
    assert trace["item_id"] == "moon"
    assert trace.get("trigger", UNDEFINED) == trigger[2]

    trace = _find_traces(response["result"], domain, "moon")[2]
    assert trace["last_step"] == last_step[3].format(prefix=prefix)
    assert "error" not in trace
    assert trace["state"] == "stopped"
    assert trace["script_execution"] == script_execution[3]
    assert trace["timestamp"]
    assert trace["item_id"] == "moon"
    assert trace.get("trigger", UNDEFINED) == trigger[3]