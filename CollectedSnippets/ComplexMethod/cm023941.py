async def test_restore_traces_overflow(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
    domain: str,
    num_restored_moon_traces: int,
) -> None:
    """Test restored traces are evicted first."""
    hass.set_state(CoreState.not_running)
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

    saved_traces = json.loads(
        await async_load_fixture(hass, f"{domain}_saved_traces.json", "trace")
    )
    hass_storage["trace.saved_traces"] = saved_traces
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
    await _setup_automation_or_script(hass, domain, [sun_config, moon_config])
    await hass.async_start()
    await hass.async_block_till_done()

    client = await hass_ws_client()

    # Traces should not yet be restored
    assert "trace_traces_restored" not in hass.data

    # List traces
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": domain})
    response = await client.receive_json()
    assert response["success"]
    restored_moon_traces = _find_traces(response["result"], domain, "moon")
    assert len(restored_moon_traces) == num_restored_moon_traces
    assert len(_find_traces(response["result"], domain, "sun")) == 1

    # Traces should be restored
    assert "trace_traces_restored" in hass.data

    # Trigger "moon" enough times to overflow the max number of stored traces
    with patch(
        "homeassistant.components.trace.models.uuid_util.random_uuid_hex",
        wraps=mock_random_uuid_hex,
    ):
        for _ in range(DEFAULT_STORED_TRACES - num_restored_moon_traces + 1):
            await _run_automation_or_script(hass, domain, moon_config, "test_event2")
            await hass.async_block_till_done()

    await client.send_json({"id": next_id(), "type": "trace/list", "domain": domain})
    response = await client.receive_json()
    assert response["success"]
    moon_traces = _find_traces(response["result"], domain, "moon")
    assert len(moon_traces) == DEFAULT_STORED_TRACES
    if num_restored_moon_traces > 1:
        assert moon_traces[0]["run_id"] == restored_moon_traces[1]["run_id"]
    assert moon_traces[num_restored_moon_traces - 1]["run_id"] == trace_uuids[0]
    assert moon_traces[-1]["run_id"] == trace_uuids[-1]
    assert len(_find_traces(response["result"], domain, "sun")) == 1