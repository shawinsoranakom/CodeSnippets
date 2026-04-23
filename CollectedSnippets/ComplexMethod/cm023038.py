async def test_ws_hass_agent_debug_out_of_range(
    hass: HomeAssistant,
    init_components,
    hass_ws_client: WebSocketGenerator,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test homeassistant agent debug websocket command with an out of range entity."""
    test_light = entity_registry.async_get_or_create(
        "light", "demo", "1234", original_name="test light"
    )
    hass.states.async_set(
        test_light.entity_id, "off", attributes={ATTR_FRIENDLY_NAME: "test light"}
    )

    client = await hass_ws_client(hass)

    # Brightness is in range (0-100)
    await client.send_json_auto_id(
        {
            "type": "conversation/agent/homeassistant/debug",
            "sentences": [
                "set test light brightness to 100%",
            ],
        }
    )

    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == snapshot

    results = msg["result"]["results"]
    assert len(results) == 1
    assert results[0]["match"]

    # Brightness is out of range
    await client.send_json_auto_id(
        {
            "type": "conversation/agent/homeassistant/debug",
            "sentences": [
                "set test light brightness to 1001%",
            ],
        }
    )

    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == snapshot

    results = msg["result"]["results"]
    assert len(results) == 1
    assert not results[0]["match"]

    # Name matched, but brightness didn't
    assert results[0]["slots"] == {"name": "test light"}
    assert results[0]["unmatched_slots"] == {"brightness": 1001}