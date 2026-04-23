async def test_trace_overflow(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, domain, stored_traces
) -> None:
    """Test the number of stored traces per script or automation is limited."""
    msg_id = 1

    trace_uuids = []

    def mock_random_uuid_hex():
        nonlocal trace_uuids
        trace_uuids.append(random_uuid_hex())
        return trace_uuids[-1]

    def next_id():
        nonlocal msg_id
        msg_id += 1
        return msg_id

    sun_config = {
        "id": "sun",
        "triggers": {"platform": "event", "event_type": "test_event"},
        "actions": {"event": "some_event"},
    }
    moon_config = {
        "id": "moon",
        "triggers": {"platform": "event", "event_type": "test_event2"},
        "actions": {"event": "another_event"},
    }
    await _setup_automation_or_script(
        hass, domain, [sun_config, moon_config], stored_traces=stored_traces
    )

    client = await hass_ws_client()

    await client.send_json({"id": next_id(), "type": "trace/list", "domain": domain})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == []

    # Trigger "sun" and "moon" automation / script once
    await _run_automation_or_script(hass, domain, sun_config, "test_event")
    await _run_automation_or_script(hass, domain, moon_config, "test_event2")
    await hass.async_block_till_done()

    # List traces
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": domain})
    response = await client.receive_json()
    assert response["success"]
    assert len(_find_traces(response["result"], domain, "moon")) == 1
    assert len(_find_traces(response["result"], domain, "sun")) == 1

    # Trigger "moon" enough times to overflow the max number of stored traces
    with patch(
        "homeassistant.components.trace.models.uuid_util.random_uuid_hex",
        wraps=mock_random_uuid_hex,
    ):
        for _ in range(stored_traces or DEFAULT_STORED_TRACES):
            await _run_automation_or_script(hass, domain, moon_config, "test_event2")
            await hass.async_block_till_done()

    await client.send_json({"id": next_id(), "type": "trace/list", "domain": domain})
    response = await client.receive_json()
    assert response["success"]
    moon_traces = _find_traces(response["result"], domain, "moon")
    assert len(moon_traces) == stored_traces or DEFAULT_STORED_TRACES
    assert moon_traces[0]
    assert moon_traces[0]["run_id"] == trace_uuids[0]
    assert moon_traces[-1]["run_id"] == trace_uuids[-1]
    assert len(_find_traces(response["result"], domain, "sun")) == 1