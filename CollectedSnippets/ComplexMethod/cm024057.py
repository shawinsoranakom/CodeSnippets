async def test_create(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
    storage_setup,
) -> None:
    """Test creating counter using WS."""

    items = []

    assert await storage_setup(items)

    counter_id = "new_counter"
    input_entity_id = f"{DOMAIN}.{counter_id}"

    state = hass.states.get(input_entity_id)
    assert state is None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, counter_id) is None

    client = await hass_ws_client(hass)

    await client.send_json({"id": 6, "type": f"{DOMAIN}/create", "name": "new counter"})
    resp = await client.receive_json()
    assert resp["success"]

    state = hass.states.get(input_entity_id)
    assert int(state.state) == 0
    assert ATTR_MINIMUM not in state.attributes
    assert ATTR_MAXIMUM not in state.attributes
    assert state.attributes[ATTR_STEP] == 1