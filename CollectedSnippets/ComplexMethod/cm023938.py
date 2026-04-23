async def test_get_trace(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
    domain,
    prefix,
    extra_trace_keys,
    trigger,
    context_key,
    condition_results,
) -> None:
    """Test tracing a script or automation."""
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

    sun_action = {
        "params": {
            "domain": "test",
            "service": "automation",
            "service_data": {},
            "target": {},
        },
        "running_script": False,
    }
    moon_action = {"event": "another_event", "event_data": {}}

    await _setup_automation_or_script(hass, domain, [sun_config, moon_config])

    client = await hass_ws_client()
    contexts = {}
    contexts_sun = {}
    contexts_moon = {}

    # Trigger "sun" automation / run "sun" script
    context = Context()
    await _run_automation_or_script(hass, domain, sun_config, "test_event", context)
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
    assert set(trace["trace"]) == {f"{prefix}/0"} | extra_trace_keys[0]
    assert len(trace["trace"][f"{prefix}/0"]) == 1
    assert trace["trace"][f"{prefix}/0"][0]["error"]
    assert trace["trace"][f"{prefix}/0"][0]["result"] == sun_action
    _assert_raw_config(domain, sun_config, trace)
    assert trace["blueprint_inputs"] is None
    assert trace["context"]
    assert trace["error"] == "Action test.automation not found"
    assert trace["state"] == "stopped"
    assert trace["script_execution"] == "error"
    assert trace["item_id"] == "sun"
    assert trace["context"][context_key] == context.id
    assert trace.get("trigger", UNDEFINED) == trigger[0]
    contexts[trace["context"]["id"]] = {
        "run_id": trace["run_id"],
        "domain": domain,
        "item_id": trace["item_id"],
    }
    contexts_sun[trace["context"]["id"]] = {
        "run_id": trace["run_id"],
        "domain": domain,
        "item_id": trace["item_id"],
    }

    # Trigger "moon" automation, with passing condition / run "moon" script
    await _run_automation_or_script(hass, domain, moon_config, "test_event2", context)
    await hass.async_block_till_done()

    # List traces
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": domain})
    response = await client.receive_json()
    assert response["success"]
    run_id = _find_run_id(response["result"], domain, "moon")

    # Get trace
    await client.send_json(
        {
            "id": next_id(),
            "type": "trace/get",
            "domain": domain,
            "item_id": "moon",
            "run_id": run_id,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    trace = response["result"]
    assert set(trace["trace"]) == {f"{prefix}/0"} | extra_trace_keys[1]
    assert len(trace["trace"][f"{prefix}/0"]) == 1
    assert "error" not in trace["trace"][f"{prefix}/0"][0]
    assert trace["trace"][f"{prefix}/0"][0]["result"] == moon_action
    _assert_raw_config(domain, moon_config, trace)
    assert trace["blueprint_inputs"] is None
    assert trace["context"]
    assert "error" not in trace
    assert trace["state"] == "stopped"
    assert trace["script_execution"] == "finished"
    assert trace["item_id"] == "moon"

    assert trace.get("trigger", UNDEFINED) == trigger[1]

    assert len(trace["trace"].get("condition/0", [])) == len(condition_results)
    for idx, condition_result in enumerate(condition_results):
        assert trace["trace"]["condition/0"][idx]["result"] == {
            "result": condition_result,
            "entities": [],
        }
    contexts[trace["context"]["id"]] = {
        "run_id": trace["run_id"],
        "domain": domain,
        "item_id": trace["item_id"],
    }
    contexts_moon[trace["context"]["id"]] = {
        "run_id": trace["run_id"],
        "domain": domain,
        "item_id": trace["item_id"],
    }

    if len(extra_trace_keys) <= 2:
        # Check contexts
        await _assert_contexts(client, next_id, contexts)
        await _assert_contexts(client, next_id, contexts_moon, domain, "moon")
        await _assert_contexts(client, next_id, contexts_sun, domain, "sun")
        return

    # Trigger "moon" automation with failing condition
    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()

    # List traces
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": domain})
    response = await client.receive_json()
    assert response["success"]
    run_id = _find_run_id(response["result"], "automation", "moon")

    # Get trace
    await client.send_json(
        {
            "id": next_id(),
            "type": "trace/get",
            "domain": domain,
            "item_id": "moon",
            "run_id": run_id,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    trace = response["result"]
    assert set(trace["trace"]) == extra_trace_keys[2]
    assert len(trace["trace"]["condition/0"]) == 1
    assert trace["trace"]["condition/0"][0]["result"] == {
        "result": False,
        "entities": [],
    }
    assert trace["config"] == moon_config
    assert trace["context"]
    assert "error" not in trace
    assert trace["state"] == "stopped"
    assert trace["script_execution"] == "failed_conditions"
    assert trace["trigger"] == "event 'test_event3'"
    assert trace["item_id"] == "moon"
    contexts[trace["context"]["id"]] = {
        "run_id": trace["run_id"],
        "domain": domain,
        "item_id": trace["item_id"],
    }
    contexts_moon[trace["context"]["id"]] = {
        "run_id": trace["run_id"],
        "domain": domain,
        "item_id": trace["item_id"],
    }

    # Trigger "moon" automation with passing condition
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()

    # List traces
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": domain})
    response = await client.receive_json()
    assert response["success"]
    run_id = _find_run_id(response["result"], "automation", "moon")

    # Get trace
    await client.send_json(
        {
            "id": next_id(),
            "type": "trace/get",
            "domain": domain,
            "item_id": "moon",
            "run_id": run_id,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    trace = response["result"]
    assert set(trace["trace"]) == {f"{prefix}/0"} | extra_trace_keys[3]
    assert len(trace["trace"][f"{prefix}/0"]) == 1
    assert "error" not in trace["trace"][f"{prefix}/0"][0]
    assert trace["trace"][f"{prefix}/0"][0]["result"] == moon_action
    assert len(trace["trace"]["condition/0"]) == 1
    assert trace["trace"]["condition/0"][0]["result"] == {
        "result": True,
        "entities": [],
    }
    assert trace["config"] == moon_config
    assert trace["context"]
    assert "error" not in trace
    assert trace["state"] == "stopped"
    assert trace["script_execution"] == "finished"
    assert trace["trigger"] == "event 'test_event2'"
    assert trace["item_id"] == "moon"
    contexts[trace["context"]["id"]] = {
        "run_id": trace["run_id"],
        "domain": domain,
        "item_id": trace["item_id"],
    }
    contexts_moon[trace["context"]["id"]] = {
        "run_id": trace["run_id"],
        "domain": domain,
        "item_id": trace["item_id"],
    }

    # Check contexts
    await _assert_contexts(client, next_id, contexts)
    await _assert_contexts(client, next_id, contexts_moon, domain, "moon")
    await _assert_contexts(client, next_id, contexts_sun, domain, "sun")

    # List traces
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": domain})
    response = await client.receive_json()
    assert response["success"]
    trace_list = response["result"]

    # Get all traces and generate expected stored traces
    traces = defaultdict(list)
    for trace in trace_list:
        item_id = trace["item_id"]
        run_id = trace["run_id"]
        await client.send_json(
            {
                "id": next_id(),
                "type": "trace/get",
                "domain": domain,
                "item_id": item_id,
                "run_id": run_id,
            }
        )
        response = await client.receive_json()
        assert response["success"]
        traces[f"{domain}.{item_id}"].append(
            {"short_dict": trace, "extended_dict": response["result"]}
        )

    # Fake stop
    assert "trace.saved_traces" not in hass_storage
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()

    # Check that saved data is same as the serialized traces
    assert "trace.saved_traces" in hass_storage
    assert hass_storage["trace.saved_traces"]["data"] == traces