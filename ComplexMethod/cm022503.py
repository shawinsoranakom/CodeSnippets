async def test_ws_create_update(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    storage_setup,
) -> None:
    """Test creating and updating via WS."""
    assert await storage_setup(config={DOMAIN: {}})

    client = await hass_ws_client(hass)

    await client.send_json({"id": 7, "type": f"{DOMAIN}/create", "name": "new"})
    resp = await client.receive_json()
    assert resp["success"]

    state = hass.states.get(f"{DOMAIN}.new")
    assert state is not None
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "new"

    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "new") is not None

    await client.send_json(
        {"id": 8, "type": f"{DOMAIN}/update", f"{DOMAIN}_id": "new", "name": "newer"}
    )
    resp = await client.receive_json()
    assert resp["success"]
    assert resp["result"] == {"id": "new", "name": "newer"}

    state = hass.states.get(f"{DOMAIN}.new")
    assert state is not None
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "newer"

    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "new") is not None