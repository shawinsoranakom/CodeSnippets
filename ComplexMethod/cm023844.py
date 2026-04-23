async def test_update(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    storage_setup,
) -> None:
    """Test updating options updates the state."""

    settings = {
        "name": "from storage",
        "options": ["yaml update 1", "yaml update 2"],
    }
    items = [{"id": "from_storage"} | settings]
    assert await storage_setup(items)

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    assert state.attributes[ATTR_OPTIONS] == ["yaml update 1", "yaml update 2"]
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id) is not None

    client = await hass_ws_client(hass)

    updated_settings = settings | {
        "options": ["new option", "newer option"],
        CONF_INITIAL: "newer option",
    }
    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            **updated_settings,
        }
    )
    resp = await client.receive_json()
    assert resp["success"]
    assert resp["result"] == {"id": "from_storage"} | updated_settings

    state = hass.states.get(input_entity_id)
    assert state.attributes[ATTR_OPTIONS] == ["new option", "newer option"]

    # Should fail because the initial state is now invalid
    updated_settings = settings | {
        "options": ["new option", "no newer option"],
        CONF_INITIAL: "newer option",
    }
    await client.send_json(
        {
            "id": 7,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            **updated_settings,
        }
    )
    resp = await client.receive_json()
    assert not resp["success"]