async def test_get_agent_list(
    hass: HomeAssistant,
    init_components,
    mock_conversation_agent: MockAgent,
    mock_agent_support_all: MockAgent,
    hass_ws_client: WebSocketGenerator,
    snapshot: SnapshotAssertion,
) -> None:
    """Test getting agent info."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "conversation/agent/list"})
    msg = await client.receive_json()
    assert msg["type"] == "result"
    assert msg["success"]
    assert msg["result"] == snapshot

    await client.send_json_auto_id(
        {"type": "conversation/agent/list", "language": "smurfish"}
    )
    msg = await client.receive_json()
    assert msg["type"] == "result"
    assert msg["success"]
    assert msg["result"] == snapshot

    await client.send_json_auto_id(
        {"type": "conversation/agent/list", "language": "en"}
    )
    msg = await client.receive_json()
    assert msg["type"] == "result"
    assert msg["success"]
    assert msg["result"] == snapshot

    await client.send_json_auto_id(
        {"type": "conversation/agent/list", "language": "en-UK"}
    )
    msg = await client.receive_json()
    assert msg["type"] == "result"
    assert msg["success"]
    assert msg["result"] == snapshot

    await client.send_json_auto_id(
        {"type": "conversation/agent/list", "language": "de"}
    )
    msg = await client.receive_json()
    assert msg["type"] == "result"
    assert msg["success"]
    assert msg["result"] == snapshot

    await client.send_json_auto_id(
        {"type": "conversation/agent/list", "language": "de", "country": "ch"}
    )
    msg = await client.receive_json()
    assert msg["type"] == "result"
    assert msg["success"]
    assert msg["result"] == snapshot