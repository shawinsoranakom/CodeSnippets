async def test_ws_hass_agent_debug_sentence_trigger(
    hass: HomeAssistant,
    init_components,
    hass_ws_client: WebSocketGenerator,
    snapshot: SnapshotAssertion,
) -> None:
    """Test homeassistant agent debug websocket command with a sentence trigger."""
    calls = async_mock_service(hass, "test", "automation")
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "trigger": {
                    "platform": "conversation",
                    "command": ["hello", "hello[ world]"],
                },
                "action": {
                    "service": "test.automation",
                    "data_template": {"data": "{{ trigger }}"},
                },
            }
        },
    )

    client = await hass_ws_client(hass)

    # List sentence
    await client.send_json_auto_id(
        {
            "type": "conversation/sentences/list",
        }
    )
    await hass.async_block_till_done()

    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == snapshot

    # Use trigger sentence
    await client.send_json_auto_id(
        {
            "type": "conversation/agent/homeassistant/debug",
            "sentences": ["hello world"],
        }
    )
    await hass.async_block_till_done()

    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == snapshot

    debug_results = msg["result"].get("results", [])
    assert len(debug_results) == 1
    assert debug_results[0].get("match")
    assert debug_results[0].get("source") == "trigger"
    assert debug_results[0].get("sentence_template") == "hello[ world]"

    # Trigger should not have been executed
    assert len(calls) == 0