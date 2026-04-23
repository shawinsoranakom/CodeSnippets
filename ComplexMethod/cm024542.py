async def test_update_min_max(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    storage_setup,
) -> None:
    """Test updating min/max updates the state."""

    settings = {
        "name": "from storage",
        "max": 100,
        "min": 0,
        "step": 1,
        "mode": "slider",
    }
    items = [{"id": "from_storage"} | settings]
    assert await storage_setup(items)

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    assert state is not None
    assert state.state
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id) is not None

    client = await hass_ws_client(hass)

    updated_settings = settings | {"min": 9}
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
    assert float(state.state) == 9

    updated_settings = settings | {"max": 5}
    await client.send_json(
        {
            "id": 7,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            **updated_settings,
        }
    )
    resp = await client.receive_json()
    assert resp["success"]
    assert resp["result"] == {"id": "from_storage"} | updated_settings

    state = hass.states.get(input_entity_id)
    assert float(state.state) == 5