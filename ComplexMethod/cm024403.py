async def test_update(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
    storage_setup,
) -> None:
    """Test updating min/max updates the state."""

    items = [
        {
            "id": "from_storage",
            "name": "from storage",
            "latitude": 1,
            "longitude": 2,
            "radius": 3,
            "passive": False,
        }
    ]
    assert await storage_setup(items)

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    assert state.attributes["latitude"] == 1
    assert state.attributes["longitude"] == 2
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id) is not None

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            "latitude": 3,
            "longitude": 4,
            "passive": True,
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    state = hass.states.get(input_entity_id)
    assert state.attributes["latitude"] == 3
    assert state.attributes["longitude"] == 4
    assert state.attributes["passive"] is True