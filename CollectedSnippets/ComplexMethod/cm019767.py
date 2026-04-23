async def test_ws_create(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    storage_setup,
) -> None:
    """Test create WS."""
    assert await storage_setup(items=[])

    timer_id = "new_timer"
    timer_entity_id = f"{DOMAIN}.{timer_id}"

    state = hass.states.get(timer_entity_id)
    assert state is None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, timer_id) is None

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/create",
            CONF_NAME: "New Timer",
            CONF_DURATION: 42,
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = hass.states.get(timer_entity_id)
    assert state.state == STATUS_IDLE
    assert state.attributes == {
        ATTR_DURATION: "0:00:42",
        ATTR_EDITABLE: True,
        ATTR_FRIENDLY_NAME: "New Timer",
    }
    assert (
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, timer_id) == timer_entity_id
    )