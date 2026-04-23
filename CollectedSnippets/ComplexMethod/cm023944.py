async def test_nested_traces(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    domain,
    prefix,
    extra_trace_keys,
) -> None:
    """Test nested automation and script traces."""
    msg_id = 1

    def next_id():
        nonlocal msg_id
        msg_id += 1
        return msg_id

    sun_config = {
        "id": "sun",
        "triggers": {"platform": "event", "event_type": "test_event"},
        "actions": {"service": "script.moon"},
    }
    moon_config = {"moon": {"sequence": {"event": "another_event"}}}
    await _setup_automation_or_script(hass, domain, [sun_config], moon_config)

    client = await hass_ws_client()

    # Trigger "sun" automation / run "sun" script
    await _run_automation_or_script(hass, domain, sun_config, "test_event")
    await hass.async_block_till_done()

    # List traces
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": "script"})
    response = await client.receive_json()
    assert response["success"]
    assert len(_find_traces(response["result"], "script", "moon")) == 1
    moon_run_id = _find_run_id(response["result"], "script", "moon")
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": domain})
    response = await client.receive_json()
    assert response["success"]
    assert len(_find_traces(response["result"], domain, "sun")) == 1
    sun_run_id = _find_run_id(response["result"], domain, "sun")
    assert sun_run_id != moon_run_id

    # Get trace
    await client.send_json(
        {
            "id": next_id(),
            "type": "trace/get",
            "domain": domain,
            "item_id": "sun",
            "run_id": sun_run_id,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    trace = response["result"]
    assert set(trace["trace"]) == {f"{prefix}/0"} | extra_trace_keys
    assert len(trace["trace"][f"{prefix}/0"]) == 1
    child_id = trace["trace"][f"{prefix}/0"][0]["child_id"]
    assert child_id == {"domain": "script", "item_id": "moon", "run_id": moon_run_id}