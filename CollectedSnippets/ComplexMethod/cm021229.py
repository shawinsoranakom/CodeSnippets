async def test_ws_create(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    storage_setup,
) -> None:
    """Test create WS."""
    assert await storage_setup(items=[])

    input_id = "new_datetime"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    assert state is None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id) is None

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/create",
            CONF_NAME: "New DateTime",
            CONF_INITIAL: "1991-01-02 01:02:03",
            CONF_HAS_DATE: True,
            CONF_HAS_TIME: True,
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = hass.states.get(input_entity_id)
    assert state.state == "1991-01-02 01:02:03"
    assert state.attributes[ATTR_FRIENDLY_NAME] == "New DateTime"
    assert state.attributes[ATTR_EDITABLE]