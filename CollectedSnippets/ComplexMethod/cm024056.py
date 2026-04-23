async def test_update_min_max(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
    storage_setup,
) -> None:
    """Test updating min/max updates the state."""

    settings = {
        "initial": 15,
        "name": "from storage",
        "maximum": 100,
        "minimum": 10,
        "step": 3,
        "restore": True,
    }
    items = [{"id": "from_storage"} | settings]
    assert await storage_setup(items)

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    assert state is not None
    assert int(state.state) == 15
    assert state.attributes[ATTR_MAXIMUM] == 100
    assert state.attributes[ATTR_MINIMUM] == 10
    assert state.attributes[ATTR_STEP] == 3
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id) is not None

    client = await hass_ws_client(hass)

    updated_settings = settings | {"minimum": 19}
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
    assert int(state.state) == 19
    assert state.attributes[ATTR_MINIMUM] == 19
    assert state.attributes[ATTR_MAXIMUM] == 100
    assert state.attributes[ATTR_STEP] == 3

    updated_settings = settings | {"maximum": 5, "minimum": 2, "step": 5}
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
    assert int(state.state) == 5
    assert state.attributes[ATTR_MINIMUM] == 2
    assert state.attributes[ATTR_MAXIMUM] == 5
    assert state.attributes[ATTR_STEP] == 5

    updated_settings = settings | {"maximum": None, "minimum": None, "step": 6}
    await client.send_json(
        {
            "id": 8,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            **updated_settings,
        }
    )
    resp = await client.receive_json()
    assert resp["success"]
    assert resp["result"] == {"id": "from_storage"} | updated_settings

    state = hass.states.get(input_entity_id)
    assert int(state.state) == 5
    assert ATTR_MINIMUM not in state.attributes
    assert ATTR_MAXIMUM not in state.attributes
    assert state.attributes[ATTR_STEP] == 6