async def test_restore_traces(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
    domain: str,
) -> None:
    """Test restored traces."""
    hass.set_state(CoreState.not_running)
    msg_id = 1

    def next_id():
        nonlocal msg_id
        msg_id += 1
        return msg_id

    saved_traces = json.loads(
        await async_load_fixture(hass, f"{domain}_saved_traces.json", "trace")
    )
    hass_storage["trace.saved_traces"] = saved_traces
    await _setup_automation_or_script(hass, domain, [])
    await hass.async_start()
    await hass.async_block_till_done()

    client = await hass_ws_client()

    # List traces
    await client.send_json({"id": next_id(), "type": "trace/list", "domain": domain})
    response = await client.receive_json()
    assert response["success"]
    trace_list = response["result"]

    # Get all traces and generate expected stored traces
    traces = defaultdict(list)
    contexts = {}
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
        contexts[response["result"]["context"]["id"]] = {
            "run_id": trace["run_id"],
            "domain": domain,
            "item_id": trace["item_id"],
        }

    # Check that loaded data is same as the serialized traces
    assert hass_storage["trace.saved_traces"]["data"] == traces

    # Check restored contexts
    await _assert_contexts(client, next_id, contexts)

    # Fake stop
    hass_storage.pop("trace.saved_traces")
    assert "trace.saved_traces" not in hass_storage
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()

    # Check that saved data is same as the serialized traces
    assert "trace.saved_traces" in hass_storage
    assert hass_storage["trace.saved_traces"] == saved_traces