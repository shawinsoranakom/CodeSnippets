async def test_update(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    storage_setup,
) -> None:
    """Test updating min/max updates the state."""

    assert await storage_setup()

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.datetime_from_storage"

    state = hass.states.get(input_entity_id)
    assert state.attributes[ATTR_FRIENDLY_NAME] == "datetime from storage"
    assert state.state == INITIAL_DATETIME
    assert (
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id) == input_entity_id
    )

    client = await hass_ws_client(hass)

    updated_settings = {
        CONF_NAME: "even newer name",
        CONF_HAS_DATE: False,
        CONF_HAS_TIME: True,
        CONF_INITIAL: INITIAL_DATETIME,
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
    assert state.state == INITIAL_TIME
    assert state.attributes[ATTR_FRIENDLY_NAME] == "even newer name"