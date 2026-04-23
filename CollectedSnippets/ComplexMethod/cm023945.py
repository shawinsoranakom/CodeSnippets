async def test_breakpoints(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, domain, prefix
) -> None:
    """Test script and automation breakpoints."""
    msg_id = 1

    def next_id():
        nonlocal msg_id
        msg_id += 1
        return msg_id

    async def assert_last_step(item_id, expected_action, expected_state):
        await client.send_json(
            {"id": next_id(), "type": "trace/list", "domain": domain}
        )
        response = await client.receive_json()
        assert response["success"]
        trace = _find_traces(response["result"], domain, item_id)[-1]
        assert trace["last_step"] == expected_action
        assert trace["state"] == expected_state
        return trace["run_id"]

    sun_config = {
        "id": "sun",
        "triggers": {"platform": "event", "event_type": "test_event"},
        "actions": [
            {"event": "event0"},
            {"event": "event1"},
            {"event": "event2"},
            {"event": "event3"},
            {"event": "event4"},
            {"event": "event5"},
            {"event": "event6"},
            {"event": "event7"},
            {"event": "event8"},
        ],
    }
    await _setup_automation_or_script(hass, domain, [sun_config])

    client = await hass_ws_client()

    await client.send_json(
        {
            "id": next_id(),
            "type": "trace/debug/breakpoint/set",
            "domain": domain,
            "item_id": "sun",
            "node": "1",
        }
    )
    response = await client.receive_json()
    assert not response["success"]

    await client.send_json({"id": next_id(), "type": "trace/debug/breakpoint/list"})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == []

    subscription_id = next_id()
    await client.send_json(
        {"id": subscription_id, "type": "trace/debug/breakpoint/subscribe"}
    )
    response = await client.receive_json()
    assert response["success"]

    await client.send_json(
        {
            "id": next_id(),
            "type": "trace/debug/breakpoint/set",
            "domain": domain,
            "item_id": "sun",
            "node": f"{prefix}/1",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    await client.send_json(
        {
            "id": next_id(),
            "type": "trace/debug/breakpoint/set",
            "domain": domain,
            "item_id": "sun",
            "node": f"{prefix}/5",
        }
    )
    response = await client.receive_json()
    assert response["success"]

    await client.send_json({"id": next_id(), "type": "trace/debug/breakpoint/list"})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == unordered(
        [
            {"node": f"{prefix}/1", "run_id": "*", "domain": domain, "item_id": "sun"},
            {"node": f"{prefix}/5", "run_id": "*", "domain": domain, "item_id": "sun"},
        ],
    )

    # Trigger "sun" automation / run "sun" script
    await _run_automation_or_script(hass, domain, sun_config, "test_event")

    response = await client.receive_json()
    run_id = await assert_last_step("sun", f"{prefix}/1", "running")
    assert response["event"] == {
        "domain": domain,
        "item_id": "sun",
        "node": f"{prefix}/1",
        "run_id": run_id,
    }

    await client.send_json(
        {
            "id": next_id(),
            "type": "trace/debug/step",
            "domain": domain,
            "item_id": "sun",
            "run_id": run_id,
        }
    )
    response = await client.receive_json()
    assert response["success"]

    response = await client.receive_json()
    run_id = await assert_last_step("sun", f"{prefix}/2", "running")
    assert response["event"] == {
        "domain": domain,
        "item_id": "sun",
        "node": f"{prefix}/2",
        "run_id": run_id,
    }

    await client.send_json(
        {
            "id": next_id(),
            "type": "trace/debug/continue",
            "domain": domain,
            "item_id": "sun",
            "run_id": run_id,
        }
    )
    response = await client.receive_json()
    assert response["success"]

    response = await client.receive_json()
    run_id = await assert_last_step("sun", f"{prefix}/5", "running")
    assert response["event"] == {
        "domain": domain,
        "item_id": "sun",
        "node": f"{prefix}/5",
        "run_id": run_id,
    }

    await client.send_json(
        {
            "id": next_id(),
            "type": "trace/debug/stop",
            "domain": domain,
            "item_id": "sun",
            "run_id": run_id,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    await hass.async_block_till_done()
    await assert_last_step("sun", f"{prefix}/5", "stopped")